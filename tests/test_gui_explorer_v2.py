"""TEST-ONLY: explorador da Biblioteca não modifica arquivos nem snapshots."""
from __future__ import annotations

import os
import unittest

from support import temporary_test_directory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QImage
    from PySide6.QtWidgets import QApplication
    from archivia.gui_explorer import ExplorerPanel, safe_directory, _BATCH_SIZE
    from archivia.gui import ArchivIAWindow
except ImportError:
    QApplication = None


@unittest.skipIf(QApplication is None, "PySide6 opcional não instalado")
class ExplorerV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.context = temporary_test_directory()
        self.tmp = self.context.__enter__()
        self.root = self.tmp / "origem"
        self.root.mkdir()
        self.child = self.root / "subpasta"
        self.child.mkdir()
        (self.root / "imagem.jpg").write_bytes(b"IMAGEM_FICTICIA")
        (self.root / "documento.pdf").write_bytes(b"PDF_FICTICIO")
        (self.child / "nota.txt").write_text("fixture", encoding="utf-8")
        self.panel = ExplorerPanel()

    def tearDown(self):
        self.panel.set_active_folder(None)
        self.panel.close()
        self.context.__exit__(None, None, None)

    def test_directory_guard_denies_outside_and_symlinks(self):
        self.assertEqual(safe_directory(self.root, self.root), self.root.resolve())
        self.assertEqual(safe_directory(self.root, self.child), self.child.resolve())
        self.assertIsNone(safe_directory(self.root, self.tmp))
        self.assertIsNone(safe_directory(self.root, self.root / ".."))
        alias = self.root / "atalho"
        try:
            alias.symlink_to(self.child, target_is_directory=True)
        except (OSError, NotImplementedError):
            return  # Windows sem permissão para criar symlink
        self.assertIsNone(safe_directory(self.root, alias))
        self.assertIsNone(safe_directory(self.root, alias / "nota.txt"))

    def test_root_lists_only_direct_children_and_navigation(self):
        self.panel.set_active_folder(self.root)
        self.assertEqual(self.panel.current_directory, self.root.resolve())
        self.assertEqual(self.panel.files.count(), 3)
        labels = {self.panel.files.item(i).text() for i in range(3)}
        self.assertEqual(labels, {"subpasta", "imagem.jpg", "documento.pdf"})
        folder_item = next(self.panel.files.item(i) for i in range(3)
                           if self.panel.files.item(i).text() == "subpasta")
        self.panel._open_item(folder_item)
        self.assertEqual(self.panel.current_directory, self.child.resolve())
        self.assertEqual(self.panel.files.count(), 1)
        self.panel._go_up()
        self.assertEqual(self.panel.current_directory, self.root.resolve())
        self.assertTrue((self.root / "imagem.jpg").is_file())

    def test_selection_properties_and_safe_double_click(self):
        self.panel.set_active_folder(self.root)
        item = next(self.panel.files.item(i) for i in range(self.panel.files.count())
                    if self.panel.files.item(i).text() == "documento.pdf")
        self.panel.files.setCurrentItem(item)
        self.panel._show_properties()
        self.assertIn("documento.pdf", self.panel.properties_text.text())
        self.assertIn("Modificado:", self.panel.properties_text.text())
        self.panel._open_item(item)
        self.assertEqual(self.panel.current_directory, self.root.resolve())
        self.assertTrue((self.root / "documento.pdf").is_file())

    def test_thumbnail_result_updates_only_current_file_generation(self):
        self.panel.set_active_folder(self.root)
        item = next(self.panel.files.item(i) for i in range(self.panel.files.count())
                    if self.panel.files.item(i).text() == "imagem.jpg")
        path = item.data(Qt.ItemDataRole.UserRole)
        meta = item.data(Qt.ItemDataRole.UserRole + 1)
        picture = QImage(24, 24, QImage.Format.Format_RGB32)
        picture.fill(Qt.GlobalColor.red)
        original_key = item.icon().cacheKey()
        self.panel._apply_thumbnail(
            path, meta[1], meta[2], self.panel._generation, picture
        )
        self.assertNotEqual(item.icon().cacheKey(), original_key)
        updated_key = item.icon().cacheKey()
        self.panel._apply_thumbnail(
            path, meta[1], meta[2], self.panel._generation - 1, picture
        )
        self.assertEqual(item.icon().cacheKey(), updated_key)

    def test_navigation_denies_leaving_active_folder(self):
        self.panel.set_active_folder(self.root)
        self.panel._open_directory(self.tmp)
        self.assertEqual(self.panel.current_directory, self.root.resolve())
        self.panel._go_up()
        self.assertEqual(self.panel.current_directory, self.root.resolve())

    def test_listing_is_batched_and_refresh_is_readonly(self):
        for index in range(_BATCH_SIZE + 6):
            (self.root / f"arquivo_{index:04d}.txt").write_bytes(b"TESTE")
        self.panel.set_active_folder(self.root)
        self.assertEqual(self.panel.files.count(), _BATCH_SIZE)
        self.assertTrue(self.panel.more_button.isVisible() or self.panel._cursor is not None)
        self.panel._append_batch()
        self.assertEqual(self.panel.files.count(), _BATCH_SIZE + 9)
        self.panel.refresh()
        self.assertEqual(self.panel.files.count(), _BATCH_SIZE)
        self.assertTrue((self.root / "arquivo_0000.txt").is_file())

    def test_folder_switch_clears_previous_items_and_thumbnail_cache(self):
        other = self.tmp / "outra"
        other.mkdir()
        (other / "arquivo.csv").write_bytes(b"coluna")
        self.panel.set_active_folder(self.root)
        self.panel._open_directory(self.child)
        self.panel.set_active_folder(other)
        self.assertEqual(self.panel.current_directory, other.resolve())
        self.assertEqual(self.panel.files.count(), 1)
        self.assertEqual(self.panel.files.item(0).text(), "arquivo.csv")
        self.panel.set_active_folder(None)
        self.assertIsNone(self.panel.current_directory)
        self.assertEqual(self.panel.files.count(), 0)

    def test_gui_explorer_tracks_active_folder_without_sqlite_writes(self):
        window = ArchivIAWindow()
        try:
            self.assertEqual(window.library_sections.tabText(0), "Explorador")
            self.assertEqual(window.library_sections.tabText(1), "Acervo")
            self.assertEqual(window.library_sections.tabText(2), "Inventário")
            window.folder.setText(str(self.root))
            self.assertEqual(window.explorer.active_root, self.root.resolve())
            self.assertEqual(window.explorer.files.count(), 3)
            window._clear_active_folder()
            self.assertIsNone(window.explorer.active_root)
            self.assertEqual(window.explorer.files.count(), 0)
            self.assertIsNone(window._worker)
        finally:
            window.close()


if __name__ == "__main__":
    unittest.main()
