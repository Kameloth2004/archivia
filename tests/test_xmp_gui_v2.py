"""TEST-ONLY: XML original é opcional e acompanha a seleção ativa."""
from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from support import temporary_test_directory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication
    from archivia.gui_explorer import ExplorerPanel
    from archivia.gui_viewer import FilePreviewDialog
    from archivia.gui_metadata_raw import RawMetadataDialog
except ImportError:
    QApplication = None


@unittest.skipIf(QApplication is None, "PySide6 opcional não instalado")
class XmpGuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.context = temporary_test_directory()
        self.root = self.context.__enter__()
        self.file = self.root / "xmp.png"
        self.file.write_bytes(b"test-only fixture")
        self.raw = [{"name": "XMP — XML original", "text": "<root>Completo</root>"}]
        self.data = {
            "groups": [{"name": "XMP", "fields": [("Software", "ArchivIA teste")]}],
            "source": "Pillow", "raw_sections": self.raw,
        }

    def tearDown(self):
        self.context.__exit__(None, None, None)

    def test_explorer_button_appears_only_after_explicit_metadata_result(self):
        explorer = ExplorerPanel()
        try:
            explorer.set_active_folder(self.root)
            item = explorer.files.item(0)
            explorer.files.setCurrentItem(item)
            self.assertFalse(explorer.raw_metadata_button.isVisible())
            path = item.data(256)
            meta = item.data(257)
            explorer._apply_metadata(
                path, meta[1], meta[2], explorer._metadata_generation, self.data
            )
            self.assertTrue(explorer.raw_metadata_button.isEnabled())
            self.assertIn("ArchivIA teste", explorer.metadata_details.text())
            with patch("archivia.gui_explorer.RawMetadataDialog") as viewer:
                explorer.raw_metadata_button.click()
            viewer.assert_called_once()
            explorer.files.clearSelection()
            self.assertFalse(explorer.raw_metadata_button.isEnabled())
            self.assertFalse(explorer._raw_metadata_sections)
        finally:
            explorer.close()

    def test_fullscreen_viewer_resets_raw_on_next_file(self):
        second = self.root / "novo.png"
        second.write_bytes(b"test-only fixture 2")
        st1, st2 = self.file.stat(), second.stat()
        with patch.object(FilePreviewDialog, "_submit_image"):
            viewer = FilePreviewDialog(
                self.root, self.file, (st1.st_size, st1.st_mtime_ns),
                sequence=[
                    (self.file, (st1.st_size, st1.st_mtime_ns)),
                    (second, (st2.st_size, st2.st_mtime_ns)),
                ],
            )
        try:
            viewer._metadata_loaded_result(viewer._generation, self.data)
            self.assertTrue(viewer.raw_metadata_button.isEnabled())
            self.assertIn("ArchivIA teste", viewer.metadata_text.toPlainText())
            viewer._next_file()
            self.assertFalse(viewer.raw_metadata_button.isEnabled())
            self.assertEqual(viewer._raw_metadata_sections, [])
        finally:
            viewer.reject()

    def test_raw_dialog_displays_complete_exif_bytes_instead_of_hex_preview(self):
        from archivia.gui_metadata_raw import _raw_section_text
        raw_bytes = b"Exif" + bytes(range(256)) * 4
        section = {"name": "EXIF original", "data": raw_bytes}
        rendered = _raw_section_text(section)
        self.assertIn("00000000: 45 78 69 66", rendered)
        self.assertIn("Tamanho original: 1,028 bytes", rendered)
        self.assertNotIn("truncado", rendered)
        self.assertIn("\n00000010:", rendered)
        dialog = RawMetadataDialog([section])
        try:
            self.assertIn("EXIF original", dialog.content.toPlainText())
            self.assertIn("Tamanho original", dialog.content.toPlainText())
        finally:
            dialog.accept()

    def test_raw_dialog_shows_full_text_without_modifying_source_file(self):
        before = self.file.read_bytes()
        dialog = RawMetadataDialog(self.raw)
        self.assertIn("<root>Completo</root>", dialog.content.toPlainText())
        self.assertTrue(dialog.content.isReadOnly())
        dialog.close_button.click()
        self.assertEqual(self.file.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
