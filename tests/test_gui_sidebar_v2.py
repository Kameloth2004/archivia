"""Regressões da navegação lateral da V2; sem tocar em arquivos pessoais."""
from __future__ import annotations

import ast
import os
from pathlib import Path
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

GUI = Path(__file__).resolve().parents[1] / "src" / "archivia" / "gui.py"


class SidebarStructureTests(unittest.TestCase):
    def test_maximizes_on_start_not_exclusive_fullscreen(self):
        tree = ast.parse(GUI.read_text(encoding="utf-8"))
        main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
        body = ast.unparse(main)
        self.assertIn("window.showMaximized()", body)
        self.assertNotIn("showFullScreen()", body)

    def test_sidebar_uses_same_tab_widget_and_horizontal_splitter(self):
        tree = ast.parse(GUI.read_text(encoding="utf-8"))
        window = next(n for n in tree.body if isinstance(n, ast.ClassDef)
                      and n.name == "ArchivIAWindow")
        init = ast.unparse(next(n for n in window.body if isinstance(n, ast.FunctionDef)
                                and n.name == "__init__"))
        for fragment in (
            "self.workspace_splitter = QSplitter(Qt.Orientation.Horizontal)",
            "self.sidebar = NavigationSidebar(self.tabs)",
            "self.tabs.tabBar().hide()",
            "self.workspace_splitter.addWidget(self.sidebar)",
            "self.workspace_splitter.addWidget(self.tabs)",
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, init)
        self.assertNotIn("self.tabs = QStackedWidget(", init)


try:
    from PySide6.QtWidgets import QApplication
    from archivia.gui import ArchivIAWindow
except ImportError:
    QApplication = None


@unittest.skipIf(QApplication is None, "PySide6 opcional não instalado")
class SidebarInteractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = ArchivIAWindow()

    def tearDown(self):
        self.window.close()

    def test_six_navigation_buttons_and_highlight_follow_each_tab(self):
        w = self.window
        self.assertEqual(w.tabs.count(), 6)
        self.assertTrue(w.tabs.tabBar().isHidden())
        self.assertEqual(
            [button.text() for button in w.sidebar.buttons],
            ["Início", "Biblioteca", "Documentos", "Organizar",
             "Agente IA", "Configurações"],
        )
        for index, button in enumerate(w.sidebar.buttons):
            with self.subTest(index=index):
                button.click()
                self.assertEqual(w.tabs.currentIndex(), index)
                self.assertTrue(button.isChecked())
                self.assertEqual(
                    sum(item.isChecked() for item in w.sidebar.buttons), 1
                )

    def test_existing_programmatic_navigation_updates_sidebar(self):
        w = self.window
        w.tabs.setCurrentWidget(w.library_workspace)
        self.assertTrue(w.sidebar.buttons[1].isChecked())
        w.tabs.setCurrentIndex(3)
        self.assertTrue(w.sidebar.buttons[3].isChecked())
        self.assertFalse(w.sidebar.buttons[1].isChecked())

    def test_sidebar_never_initiates_moves_or_scans(self):
        w = self.window
        self.assertIsNone(w._worker)
        self.assertIsNone(w._folder_session)
        for button in w.sidebar.buttons:
            button.click()
        self.assertIsNone(w._worker)
        self.assertIsNone(w._folder_session)


if __name__ == "__main__":
    unittest.main()
