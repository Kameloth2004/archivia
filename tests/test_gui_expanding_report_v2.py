"""TEST-ONLY: relatórios da aba Início sem rolagem interna."""
from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication
    from archivia.gui_expanding_report import ExpandingReport
    from archivia.gui import ArchivIAWindow
except ImportError:
    QApplication = None


@unittest.skipIf(QApplication is None, "PySide6 não instalado")
class ExpandingReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_readonly_and_no_internal_scrollbar(self):
        report = ExpandingReport()
        self.assertTrue(report.isReadOnly())
        self.assertEqual(
            report.verticalScrollBarPolicy(),
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )
        self.assertEqual(
            report.horizontalScrollBarPolicy(),
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )
        report.close()

    def test_height_grows_to_fit_full_report(self):
        report = ExpandingReport()
        report.resize(500, 50)
        report.show()
        self.app.processEvents()
        report.setPlainText("\n".join(f"Arquivo {i}" for i in range(25)))
        self.app.processEvents()
        self.assertGreater(report.height(), 105)
        self.assertEqual(report.verticalScrollBar().maximum(), 0)
        report.close()

    def test_report_recalculates_after_text_and_width_change(self):
        report = ExpandingReport()
        report.resize(520, 50)
        report.show()
        self.app.processEvents()
        report.setPlainText("Linha curta")
        short_height = report.height()
        report.setPlainText("\n".join("Arquivo " + str(i) for i in range(40)))
        long_height = report.height()
        self.assertGreater(long_height, short_height)
        self.assertGreater(long_height, 105)
        report.setPlainText("Texto " * 200)
        report.resize(240, report.height())
        self.app.processEvents()
        narrow_height = report.height()
        report.resize(600, report.height())
        self.app.processEvents()
        self.assertGreaterEqual(narrow_height, report.height())
        self.assertEqual(
            report.verticalScrollBarPolicy(),
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )
        report.close()

    def test_home_report_stays_collapsible_and_external_scroll_exists(self):
        window = ArchivIAWindow()
        self.assertIsInstance(window.home_result, ExpandingReport)
        self.assertTrue(window.home_result.isHidden())
        window.home_result.setPlainText("\n".join("Linha do relatório" for _ in range(30)))
        window.home_analysis_toggle.click()
        self.app.processEvents()
        self.assertFalse(window.home_result.isHidden())
        self.assertGreater(window.home_result.height(), 105)
        window.home_analysis_toggle.click()
        self.assertTrue(window.home_result.isHidden())
        self.assertEqual(window.home_result.document().blockCount(), 30)
        window.close()


if __name__ == "__main__":
    unittest.main()
