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

    def test_arrows_navigate_and_reset_zoom_and_metadata_without_auto_read(self):
        second = self.root / "imagem_02.png"
        image = QImage(60, 40, QImage.Format.Format_RGB32)
        image.fill(Qt.GlobalColor.blue)
        self.assertTrue(image.save(str(second), "PNG"))
        sequence = [
            (self.image, self._expected(self.image)),
            (self.other, self._expected(self.other)),
            (second, self._expected(second)),
        ]
        with patch.object(FilePreviewDialog, "_submit_image") as start_image:
            dialog = FilePreviewDialog(
                self.root, self.image, self._expected(self.image),
                sequence=sequence,
            )
            try:
                self.assertFalse(dialog.prev_button.isEnabled())
                self.assertTrue(dialog.next_button.isEnabled())
                self.assertEqual(dialog.position_label.text(), "1 / 3")
                picture = QImage(120, 80, QImage.Format.Format_RGB32)
                picture.fill(Qt.GlobalColor.cyan)
                dialog._image_loaded_result(
                    dialog._generation,
                    {"image": picture, "original": (120, 80)},
                )
                dialog.zoom_view.actual_size()
                dialog.zoom_in_button.click()
                self.assertGreater(dialog.zoom_view.transform().m11(), 1)
                dialog.metadata_text.setPlainText("Metadados anteriores")
                with patch.object(dialog, "_submit_metadata") as get_metadata:
                    dialog.next_button.click()
                    self.assertEqual(dialog.file, self.other)
                    self.assertEqual(dialog.position_label.text(), "2 / 3")
                    self.assertFalse(dialog.zoom_in_button.isEnabled())
                    self.assertFalse(dialog.zoom_view._has_image)
                    self.assertEqual(dialog.metadata_text.toPlainText(), "")
                    self.assertIn("ainda não consultados", dialog.metadata_status.text())
                    self.assertIn("ainda não disponível", dialog.placeholder.text())
                    self.assertIn("codigo.py", dialog.properties_text.text())
                    dialog.next_button.click()
                    self.assertEqual(dialog.file, second)
                    self.assertEqual(dialog.position_label.text(), "3 / 3")
                    self.assertFalse(dialog.next_button.isEnabled())
                    self.assertTrue(dialog.prev_button.isEnabled())
                    dialog._next_file()
                    self.assertEqual(dialog.file, second)
                    dialog.prev_button.click()
                    self.assertEqual(dialog.file, self.other)
                    get_metadata.assert_not_called()
            finally:
                dialog.reject()
        self.assertEqual(start_image.call_count, 2)
        self.assertTrue(self.image.exists())
        self.assertTrue(second.exists())

    def test_old_async_image_is_ignored_after_navigating(self):
        second = self.root / "segunda.png"
        image = QImage(50, 50, QImage.Format.Format_RGB32)
        image.fill(Qt.GlobalColor.red)
        self.assertTrue(image.save(str(second), "PNG"))
        # Manter o mock durante a navegação: voltar ao submit real aqui
        # iniciaria leitura concorrente e bloquearia exclusão da fixture
        # no Windows (WinError 32).
        with patch.object(FilePreviewDialog, "_submit_image"):
            dialog = FilePreviewDialog(
                self.root, self.image, self._expected(self.image),
                sequence=[
                    (self.image, self._expected(self.image)),
                    (second, self._expected(second)),
                ],
            )
            try:
                old_generation = dialog._generation
                dialog._next_file()
                stale = QImage(10, 10, QImage.Format.Format_RGB32)
                stale.fill(Qt.GlobalColor.green)
                dialog._image_loaded_result(
                    old_generation, {"image": stale, "original": (10, 10)}
                )
                self.assertFalse(dialog._image_loaded)
                self.assertEqual(dialog.display.currentWidget(), dialog.placeholder)
                self.assertIn("segunda.png", dialog.title_label.text())
            finally:
                dialog.reject()
                self.assertTrue(dialog._pool.waitForDone(10000))

    def test_next_file_can_load_one_more_batch(self):
        second = self.root / "segunda.png"
        QImage(30, 30, QImage.Format.Format_RGB32).save(str(second), "PNG")
        extended = [
            (self.image, self._expected(self.image)),
            (second, self._expected(second)),
        ]
        more = [True]
        calls = []
        def load_one():
            calls.append(True)
            more[0] = False
            return extended

        with patch.object(FilePreviewDialog, "_submit_image"):
            dialog = FilePreviewDialog(
                self.root, self.image, self._expected(self.image),
                sequence=extended[:1], load_more=load_one,
                has_more=lambda: more[0],
            )
            try:
                self.assertTrue(dialog.next_button.isEnabled())
                self.assertEqual(dialog.position_label.text(), "1 / 1+")
                dialog._next_file()
                self.assertEqual(dialog.file, second)
                self.assertEqual(dialog.position_label.text(), "2 / 2")
                self.assertEqual(len(calls), 1)
                self.assertFalse(dialog.next_button.isEnabled())
            finally:
                dialog.reject()
                self.assertTrue(dialog._pool.waitForDone(10000))

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

    def test_close_button_marks_dialog_closed_and_returns_to_explorer(self):
        dialog = FilePreviewDialog(self.root, self.other, self._expected(self.other))
        self.assertEqual(dialog.close_button.accessibleName(), "Fechar visualização")
        self.assertFalse(dialog._closed)
        dialog.close_button.click()
        self.assertTrue(dialog._closed)

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
