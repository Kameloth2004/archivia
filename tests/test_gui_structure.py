"""TEST-ONLY: regressões estruturais da GUI sem abrir janelas Qt.

A suíte roda mesmo quando PySide6 não está instalado (aplicação opcional).
"""
from __future__ import annotations

import ast
from pathlib import Path
import unittest


GUI_FILE = Path(__file__).resolve().parents[1] / "src" / "archivia" / "gui.py"


class GUIStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tree = ast.parse(GUI_FILE.read_text(encoding="utf-8"))
        cls.window = next(
            node for node in cls.tree.body
            if isinstance(node, ast.ClassDef) and node.name == "ArchivIAWindow"
        )

    @classmethod
    def method(cls, name):
        return next(
            node for node in cls.window.body
            if isinstance(node, ast.FunctionDef) and node.name == name
        )

    def test_busy_guards_run_before_widget_mutations(self):
        for name in (
            "_run_inventory_preview", "_run_summary",
            "_run_date_plan", "_run_duplicate_hash",
        ):
            with self.subTest(name=name):
                method = self.method(name)
                first = method.body[0]
                self.assertIsInstance(first, ast.If)
                self.assertIn("self._worker is not None", ast.unparse(first.test))
                self.assertIsInstance(first.body[0], ast.Return)

    def test_timestamp_cell_keeps_raw_iso_in_user_role(self):
        method = self.method("_render_result")
        body = ast.unparse(method)
        self.assertIn('setData(Qt.ItemDataRole.UserRole, item["modified_utc"])', body.replace("\'", '"\'))

    def test_date_format_uses_saved_iso_not_previous_display(self):
        method = self.method("_change_date_format")
        body = ast.unparse(method)
        self.assertIn("cell.data(Qt.ItemDataRole.UserRole)", body)
        self.assertNotIn("datetime.strptime(cell.text()", body)
        self.assertIn("display_timestamp(iso, next_format)", body)

    def test_worker_moved_out_of_main_window_module(self):
        top_classes = [
            node.name for node in self.tree.body if isinstance(node, ast.ClassDef)
        ]
        self.assertNotIn("QueryWorker", top_classes)
        self.assertIn("ArchivIAWindow", top_classes)
        imports = ast.unparse(self.tree)
        self.assertIn("from .gui_worker import QueryWorker", imports)

    def test_result_contract_is_checked_before_render(self):
        body = ast.unparse(self.method("_show_result"))
        self.assertLess(body.index("validate_gui_result("), body.index("self._render_result("))


if __name__ == "__main__":
    unittest.main()
