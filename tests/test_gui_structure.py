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
        self.assertIn("catalog_rows(items, self._date_format)", body)
        self.assertIn("fill_table(self.catalog_table, rows, roles=roles)", body)
        helper = (GUI_FILE.parent / "gui_tables.py").read_text(encoding="utf-8")
        self.assertIn("cell.setData(Qt.ItemDataRole.UserRole, raw)", helper)
        row_helper = (GUI_FILE.parent / "table_rows.py").read_text(encoding="utf-8")
        self.assertIn('item["modified_utc"]', row_helper)

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

    def test_catalog_filters_and_pagination_use_shared_helpers(self):
        catalog = ast.unparse(self.method("_load_catalog_page"))
        self.assertIn("catalog_filters(", catalog)
        self.assertIn("**filters", catalog)
        self.assertIn("previous_page(", ast.unparse(self.method("_previous_page")))
        self.assertIn("next_page(", ast.unparse(self.method("_next_page")))
        self.assertIn("previous_page(", ast.unparse(self.method("_previous_preview_page")))
        self.assertIn("next_page(", ast.unparse(self.method("_next_preview_page")))

    def test_reports_are_delegated_to_presentation_module(self):
        rendered = ast.unparse(self.method("_render_result"))
        self.assertIn("summary_report(result)", rendered)
        self.assertIn("inventory_report(result)", rendered)
        self.assertIn("agent_report(result)", rendered)
        self.assertNotIn("json.dumps(", rendered)

    def test_saved_snapshot_navigation_waits_for_worker_finish(self):
        body = ast.unparse(self.method("_worker_done")).replace(chr(39), chr(34))
        self.assertIn('completed_mode == "catalog_verified_preview"', body)
        self.assertIn('self._start_worker("history", Path(navigation["database"]))', body)
        self.assertIn('completed_mode == "history"', body)
        self.assertIn('navigation["stage"] == "await_listing"', body)
        self.assertIn("self._load_catalog_page()", body)

    def test_saved_snapshot_selection_uses_id_and_clears_old_filters(self):
        body = ast.unparse(self.method("_render_result")).replace(chr(39), chr(34))
        self.assertIn("find_saved_snapshot(result, saved_id)", body)
        self.assertIn("self.history_select.findData(saved_id)", body)
        self.assertIn("self._clear_catalog_search()", body)
        self.assertIn("self.category_filter.setCurrentIndex(0)", body)
        self.assertIn("self.tabs.setCurrentIndex(1)", body)

    def test_home_catalog_buttons_reuse_existing_handlers(self):
        constructor = ast.unparse(self.method("__init__"))
        self.assertIn("self.home_inventory_button.clicked.connect(self._run_inventory_preview)", constructor)
        self.assertIn("self.home_catalog_button.clicked.connect(self._confirm_catalog_preview)", constructor)
        self.assertIn("self.home_preview_button.clicked.connect(self._home_view_preview)", constructor)
        self.assertNotIn("copy_verified_test_file", constructor)
        self.assertNotIn("execute_test_move", constructor)

    def test_home_preview_opens_existing_advanced_inventory(self):
        body = ast.unparse(self.method("_home_view_preview"))
        self.assertIn("can_save_inventory_preview(", body)
        self.assertIn("self.advanced_button.setChecked(True)", body)
        self.assertIn("self.advanced_tabs.setCurrentIndex(1)", body)

    def test_busy_and_saved_preview_control_all_catalog_buttons(self):
        busy = ast.unparse(self.method("_set_busy"))
        self.assertIn("can_save_inventory_preview(", busy)
        for name in ("catalog_preview_button", "home_preview_button", "home_catalog_button"):
            self.assertIn(f"self.{name}.setEnabled(ready)", busy)
        cleared = ast.unparse(self.method("_clear_preview"))
        for name in ("home_preview_button", "home_catalog_button"):
            self.assertIn(f"self.{name}.setEnabled(False)", cleared)
        result = ast.unparse(self.method("_render_result"))
        self.assertIn("preview_report = inventory_report(result)", result)
        confirm = ast.unparse(self.method("_confirm_catalog_preview"))
        self.assertIn("can_save_inventory_preview(", confirm)

    def test_manual_copy_is_opt_in_only_from_gui(self):
        init = ast.unparse(self.method("__init__"))
        self.assertIn("self.manual_copy_button.clicked.connect(self._manual_copy_image)", init)
        handler = ast.unparse(self.method("_manual_copy_image"))
        self.assertIn("QFileDialog.getOpenFileName", handler)
        self.assertIn("QFileDialog.getExistingDirectory", handler)
        self.assertIn("QMessageBox.question", handler)
        self.assertIn("preview_manual_image_copy", handler)
        self.assertIn('self._start_worker(', handler)
        self.assertNotIn("os.unlink", handler)

    def test_manual_copy_uses_existing_worker_and_disables_button(self):
        busy = ast.unparse(self.method("_set_busy"))
        self.assertIn("self.manual_copy_button.setEnabled(not busy)", busy)
        result = ast.unparse(self.method("_render_result"))
        self.assertIn('mode == "manual_copy"', result.replace(chr(39), chr(34)))
        self.assertIn("A imagem original NÃO foi removida", result)

    def test_home_direct_organization_is_independent_of_ollama(self):
        init = ast.unparse(self.method("__init__"))
        preparation = ast.unparse(self.method("_prepare_home_organization"))
        invalidation = ast.unparse(self.method("_invalidate_home_organization"))
        busy = ast.unparse(self.method("_set_busy"))
        self.assertIn("self.home_prepare_button.clicked.connect(self._prepare_home_organization)", init)
        self.assertIn("self.home_organize_category.addItem('Vídeos', 'video')", init)
        self.assertIn("self.home_organize_category.addItem('Áudios', 'audio')", init)
        self.assertIn("self.home_folder.textChanged.connect(self._invalidate_home_organization)", init)
        self.assertIn("self.home_destination.textChanged.connect(self._invalidate_home_organization)", init)
        self.assertIn("self.home_organize_category.currentIndexChanged.connect(self._invalidate_home_organization)", init)
        self.assertIn("self._start_worker(", preparation)
        self.assertIn("self.home_organize_category.currentData()", preparation)
        self.assertNotIn("self._run_agent(", preparation)
        self.assertIn("session._last_recursive_plan = None", invalidation)
        self.assertIn("plan.get('complete') is True", busy)
        self.assertIn("self.home_prepare_button.setEnabled(not busy)", busy)

    def test_home_understands_mova_and_renders_recursive_plan(self):
        handler = ast.unparse(self.method("_home_ask"))
        self.assertIn("'mova'", handler)
        self.assertIn("'mover'", handler)
        rendered = ast.unparse(self.method("_render_result"))
        self.assertIn("recursive_plan_report(result)", rendered)

    def test_result_contract_is_checked_before_render(self):
        body = ast.unparse(self.method("_show_result"))
        self.assertLess(body.index("validate_gui_result("), body.index("self._render_result("))


if __name__ == "__main__":
    unittest.main()
