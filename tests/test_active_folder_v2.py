"""TEST-ONLY: pasta ativa isolada do SQLite persistente e das operações reais."""
from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from support import temporary_test_directory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication
    from archivia.gui import ArchivIAWindow
except ImportError:
    QApplication = None


@unittest.skipIf(QApplication is None, "PySide6 opcional não instalado")
class ActiveFolderV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.context = temporary_test_directory()
        self.tmp = self.context.__enter__()
        self.first = self.tmp / "origem_a"
        self.second = self.tmp / "origem_b"
        self.first.mkdir()
        self.second.mkdir()
        (self.first / "relatorio.pdf").write_bytes(b"pdf A")
        (self.second / "relatorio.pdf").write_bytes(b"pdf B")
        self.window = ArchivIAWindow()

    def tearDown(self):
        self.window.close()
        self.context.__exit__(None, None, None)

    def test_selected_folder_is_shared_and_is_not_saved_to_settings(self):
        w = self.window
        w.folder.setText(str(self.first))
        self.assertEqual(w.active_folder_display.text(), str(self.first))
        self.assertEqual(w.home_folder.text(), str(self.first))
        self.assertEqual(w.organize_source.text(), str(self.first))
        self.assertIn(str(self.first), w.documents_active_folder.text())
        self.assertEqual(w._active_folder, self.first)
        self.assertIsNone(w._folder_session)
        self.assertNotIn("session/active_folder", w._settings.allKeys())

    def test_home_source_is_the_same_widget_as_inventory_folder(self):
        w = self.window
        self.assertIs(w.home_folder, w.folder)
        w.folder.setText(str(self.first))
        self.assertEqual(w.home_folder.text(), str(self.first))
        self.assertEqual(w.active_folder_display.text(), str(self.first))
        self.assertEqual(w.organize_source.text(), str(self.first))
        self.assertEqual(w._active_folder, self.first)

    def test_global_actions_keep_source_and_navigation(self):
        w = self.window
        w.folder.setText(str(self.first))
        self.assertIs(w.home_folder, w.folder)
        self.assertEqual(w.active_folder_display.text(), str(self.first))
        self.assertIsNone(w._worker)
        w.open_organize_button.click()
        self.assertEqual(w.tabs.currentIndex(), 3)
        self.assertTrue(w.sidebar.buttons[3].isChecked())
        self.assertEqual(w.active_folder_display.text(), str(self.first))
        self.assertIsNone(w._worker)

    def test_analysis_details_start_closed_and_toggle_without_losing_text(self):
        w = self.window
        self.assertFalse(w.home_analysis_toggle.isChecked())
        self.assertTrue(w.home_result.isHidden())
        report = "Análise concluída — nenhum arquivo foi alterado."
        w.home_result.setPlainText(report)
        self.assertIn("Análise concluída", w.home_analysis_toggle.text())
        w.home_analysis_toggle.click()
        self.assertTrue(w.home_analysis_toggle.isChecked())
        self.assertFalse(w.home_result.isHidden())
        self.assertEqual(w.home_result.toPlainText(), report)
        w.home_analysis_toggle.click()
        self.assertFalse(w.home_analysis_toggle.isChecked())
        self.assertTrue(w.home_result.isHidden())
        self.assertEqual(w.home_result.toPlainText(), report)

    def test_switch_folder_discards_previous_temporary_catalog_and_plan(self):
        w = self.window
        w.folder.setText(str(self.first))
        session = w._session_for_folder()
        plan_dest = self.tmp / "dest"
        plan_dest.mkdir()
        plan = session.prepare_recursive_plan(plan_dest, "documento")
        self.assertEqual(plan["proposed"], 1)
        self.assertTrue(session.ready)
        w.catalog_source.setCurrentIndex(w.catalog_source.findData("active"))
        w.folder.setText(str(self.second))
        self.assertIsNone(w._folder_session)
        self.assertFalse(session.ready)
        self.assertEqual(w.catalog_table.rowCount(), 0)
        self.assertEqual(w._active_folder, self.second)
        self.assertEqual(w.move_choice.count(), 1)
        self.assertTrue((self.first / "relatorio.pdf").is_file())

    def test_clear_keeps_saved_catalog_configuration(self):
        w = self.window
        existing_database_value = w.database.text()
        w.folder.setText(str(self.first))
        w._clear_active_folder()
        self.assertIsNone(w._active_folder)
        self.assertEqual(w.folder.text(), "")
        self.assertEqual(w.home_folder.text(), "")
        self.assertEqual(w.organize_source.text(), "")
        self.assertEqual(w.database.text(), existing_database_value)
        self.assertFalse(w.active_folder_clear.isEnabled())

    def test_active_catalog_uses_session_not_saved_database(self):
        w = self.window
        w.folder.setText(str(self.first))
        w.catalog_source.setCurrentIndex(w.catalog_source.findData("active"))
        w.category_filter.blockSignals(True)
        w.category_filter.setCurrentIndex(w.category_filter.findData("documento"))
        w.category_filter.blockSignals(False)
        with patch.object(w, "_start_worker") as start:
            w._load_catalog_page()
        self.assertEqual(start.call_args.args[0], "catalog_page")
        session = start.call_args.kwargs["folder_session"]
        self.assertEqual(session.source, self.first)
        self.assertIsNone(start.call_args.kwargs["scan_id"])
        self.assertFalse(session.ready)
        # O worker usa apenas SQLite descartável da pasta ativa.
        session.refresh()
        from archivia.catalog import query_catalog_page
        result = query_catalog_page(
            session._db, "documento", scan_id=session._scan_id,
            page=1, page_size=10,
        )
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["files"][0]["relative_path"], "relatorio.pdf")
        self.assertTrue((self.first / "relatorio.pdf").is_file())

    def test_while_busy_selection_controls_are_disabled(self):
        w = self.window
        w.folder.setText(str(self.first))
        w._set_busy(True)
        self.assertFalse(w.active_folder_choose.isEnabled())
        self.assertFalse(w.active_folder_clear.isEnabled())
        self.assertFalse(w.catalog_source.isEnabled())
        w._set_busy(False)
        self.assertTrue(w.active_folder_choose.isEnabled())


if __name__ == "__main__":
    unittest.main()
