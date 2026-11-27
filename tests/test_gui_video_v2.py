"""TEST-ONLY: integração do player local e navegação do visualizador V2.

Não contém arquivos de vídeo reais; testa somente fonte, estado e controles.
"""
from __future__ import annotations

import os
import unittest
from pathlib import Path
from unittest.mock import patch

from support import temporary_test_directory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import QUrl
    from PySide6.QtMultimedia import QMediaPlayer
    from PySide6.QtWidgets import QApplication
    from archivia.gui_video import LocalVideoPlayer, VIDEO_EXTENSIONS, format_media_time
    from archivia.gui_viewer import FilePreviewDialog
except ImportError:
    QApplication = None


@unittest.skipIf(QApplication is None, "Qt Multimedia/PySide6 indisponível")
class VideoPlayerV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.context = temporary_test_directory()
        self.root = self.context.__enter__()
        self.video = self.root / "clip.mp4"
        self.video.write_bytes(b"TEST-ONLY NOT A REAL VIDEO")
        self.photo = self.root / "foto.jpg"
        self.photo.write_bytes(b"TEST-ONLY")
        self.player = LocalVideoPlayer()

    def tearDown(self):
        self.player.release()
        self.player.close()
        self.context.__exit__(None, None, None)

    def _expected(self, path):
        info = path.stat()
        return info.st_size, info.st_mtime_ns

    def test_extensions_and_time_format(self):
        self.assertIn(".mp4", VIDEO_EXTENSIONS)
        self.assertIn(".webm", VIDEO_EXTENSIONS)
        self.assertEqual(format_media_time(0), "00:00")
        self.assertEqual(format_media_time(61_000), "01:01")
        self.assertEqual(format_media_time(3_661_000), "01:01:01")

    def test_open_does_not_autoplay_and_release_clears_source(self):
        with patch.object(self.player.player, "play") as play:
            self.player.open_local(self.video)
            play.assert_not_called()
        self.assertEqual(self.player.player.source(), QUrl.fromLocalFile(str(self.video)))
        self.player.release()
        self.assertTrue(self.player.player.source().isEmpty())

    def test_seek_clamps_to_duration_and_requires_seekable(self):
        self.player._duration = 20_000
        with patch.object(self.player.player, "isSeekable", return_value=True), \
             patch.object(self.player.player, "position", return_value=15_000), \
             patch.object(self.player.player, "setPosition") as seek:
            self.player.seek_relative(10_000)
            seek.assert_called_once_with(20_000)
        with patch.object(self.player.player, "isSeekable", return_value=False), \
             patch.object(self.player.player, "setPosition") as seek:
            self.player.seek_relative(-10_000)
            seek.assert_not_called()

    def test_video_dialog_does_not_submit_image_or_autoplay(self):
        with patch.object(FilePreviewDialog, "_submit_image") as image_submit, \
             patch.object(LocalVideoPlayer, "open_local") as open_video, \
             patch.object(LocalVideoPlayer, "release"):
            dialog = FilePreviewDialog(self.root, self.video, self._expected(self.video))
            try:
                image_submit.assert_not_called()
                open_video.assert_called_once_with(self.video)
                self.assertIs(dialog.display.currentWidget(), dialog.video_player)
            finally:
                dialog.reject()

    def test_navigation_out_of_video_releases_player(self):
        with patch.object(FilePreviewDialog, "_submit_image"), \
             patch.object(LocalVideoPlayer, "open_local"), \
             patch.object(LocalVideoPlayer, "release") as release:
            dialog = FilePreviewDialog(
                self.root, self.video, self._expected(self.video),
                sequence=[
                    (self.video, self._expected(self.video)),
                    (self.photo, self._expected(self.photo)),
                ],
            )
            try:
                dialog._next_file()
                self.assertEqual(dialog.file, self.photo)
                self.assertGreaterEqual(release.call_count, 1)
            finally:
                dialog.reject()


if __name__ == "__main__":
    unittest.main()
