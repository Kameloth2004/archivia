"""TEST-ONLY: visualizador ampliado, zoom, segurança e metadados opt-in."""
from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from support import temporary_test_directory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QImage
    from PySide6.QtWidgets import QApplication
    from archivia.gui_viewer import (
        FilePreviewDialog, ZoomImageView, verified_file, _ImageLoad, _MetadataLoad,
    )
    from archivia.gui_explorer import ExplorerPanel
except ImportError:
    QApplication = None


@unittest.skipIf(QApplication is None, "PySide6 opcional não instalado")
class FullscreenViewerV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.context = temporary_test_directory()
        self.base = self.context.__enter__()
        self.root = self.base / "origem"
        self.root.mkdir()
        self.image = self.root / "imagem.png"
        picture = QImage(120, 80, QImage.Format.Format_RGB32)
        picture.fill(Qt.GlobalColor.cyan)
        self.assertTrue(picture.save(str(self.image), "PNG"))
        self.other = self.root / "codigo.py"
        self.other.write_text("print('teste')", encoding="utf-8")

    def tearDown(self):
        self.context.__exit__(None, None, None)

    def _expected(self, path):
        st = path.stat()
        return st.st_size, st.st_mtime_ns

    def test_real_image_preview_and_zoom(self):
        with patch.object(FilePreviewDialog, "_submit_image"):
            dialog = FilePreviewDialog(self.root, self.image, self._expected(self.image))
        try:
            self.assertFalse(dialog._image_loaded)
            picture = QImage(120, 80, QImage.Format.Format_RGB32)
            picture.fill(Qt.GlobalColor.cyan)
            dialog._image_loaded_result(
                dialog._generation, {"image": picture, "original": (120, 80)},
            )
            self.assertTrue(dialog._image_loaded)
            self.assertTrue(dialog.zoom_in_button.isEnabled())
            dialog.zoom_view.actual_size()
            self.assertAlmostEqual(dialog.zoom_view.transform().m11(), 1.0)
            dialog.zoom_in_button.click()
            self.assertAlmostEqual(dialog.zoom_view.transform().m11(), 1.25)
            dialog.zoom_out_button.click()
            self.assertAlmostEqual(dialog.zoom_view.transform().m11(), 1.0)
            dialog.fit_button.click()
            self.assertTrue(dialog.zoom_view._fit_mode)
            self.assertTrue(dialog.edit_button.isEnabled() is False)
        finally:
            dialog.reject()

    def test_real_decoder_task_works_without_modifying_fixture(self):
        from archivia.gui_viewer import _ViewerEvents
        events = _ViewerEvents()
        payloads = []
        events.image_ready.connect(lambda *_args: payloads.append(_args))
        before = self.image.read_bytes()
        task = _ImageLoad(self.root, self.image, self._expected(self.image), 1, events)
        task.run()
        self.app.processEvents()
        self.assertEqual(len(payloads), 1)
        self.assertIn("image", payloads[0][1])
        self.assertFalse(payloads[0][1]["image"].isNull())
        self.assertEqual(self.image.read_bytes(), before)

    def test_non_image_shows_readonly_placeholder_and_requires_metadata_click(self):
        dialog = FilePreviewDialog(self.root, self.other, self._expected(self.other))
        try:
            self.assertIn("ainda não disponível", dialog.placeholder.text())
            self.assertFalse(dialog.zoom_in_button.isEnabled())
            self.assertIn("ainda não consultados", dialog.metadata_status.text())
            with patch.object(dialog, "_submit_metadata") as submit:
                dialog.verify_button.click()
            self.assertEqual(submit.call_count, 1)
            self.assertIsInstance(submit.call_args.args[0], _MetadataLoad)
            self.assertFalse(dialog.verify_button.isEnabled())
            dialog._metadata_loaded_result(
                dialog._generation,
                {"fields": [("Formato", "Texto")],
                 "source": "Sistema de arquivos", "note": "Sem leitor interno."},
            )
            self.assertIn("Formato: Texto", dialog.metadata_text.toPlainText())
        finally:
            dialog.reject()

    def test_stale_metadata_and_image_after_close_are_ignored(self):
        dialog = FilePreviewDialog(self.root, self.other, self._expected(self.other))
        dialog.reject()
        dialog._metadata_loaded_result(
            1, {"fields": [("Autor", "NAO_EXIBIR")]},
        )
        self.assertNotIn("NAO_EXIBIR", dialog.metadata_text.toPlainText())

    def test_reject_outside_folder_or_modified_file(self):
        from pathlib import Path
        with self.assertRaises(ValueError):
            verified_file(self.root, self.base / "fora.txt", (1, 1))
        with self.assertRaises(ValueError):
            verified_file(self.root, self.image, (0, 0))
        self.assertEqual(
            verified_file(self.root, self.image, self._expected(self.image)).st_size,
            self.image.stat().st_size,
        )

    def test_explorer_doubleclick_opens_preview_only_for_files(self):
        explorer = ExplorerPanel()
        try:
            explorer.set_active_folder(self.root)
            image_item = next(
                explorer.files.item(i) for i in range(explorer.files.count())
                if explorer.files.item(i).text() == "imagem.png"
            )
            with patch("archivia.gui_explorer.FilePreviewDialog") as viewer:
                explorer._open_item(image_item)
            self.assertEqual(viewer.call_count, 1)
            self.assertTrue(viewer.return_value.showFullScreen.called)
            self.assertTrue(viewer.return_value.exec.called)
            self.assertEqual(explorer.current_directory, self.root.resolve())
            self.assertTrue(self.image.is_file())
        finally:
            explorer.close()


if __name__ == "__main__":
    unittest.main()
