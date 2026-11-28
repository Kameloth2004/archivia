"""TEST-ONLY: fila, descarte e sinal de miniatura de vídeo sem exigir codecs."""
from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from support import temporary_test_directory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    from PySide6.QtGui import QImage
    from PySide6.QtCore import Qt, QUrl
    from PySide6.QtWidgets import QApplication
    from archivia.video_thumbnails import VideoThumbnailService
    from archivia.gui_explorer import ExplorerPanel
except ImportError:
    QApplication = None


@unittest.skipIf(QApplication is None, "Qt Multimedia não disponível")
class VideoThumbnailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.context = temporary_test_directory()
        self.root = self.context.__enter__()
        self.video = self.root / "teste.mp4"
        self.video.write_bytes(b"fixture de video nao decodificavel")
        self.info = self.video.stat()
        self.service = VideoThumbnailService()
        self.service.reset(1)

    def tearDown(self):
        self.service.close()
        self.context.__exit__(None, None, None)

    def test_rejects_old_generation_and_nonvideo(self):
        with patch.object(self.service._player, "setSource") as set_source:
            self.service.request(str(self.video), self.info.st_size, self.info.st_mtime_ns, 0)
            self.service.request(str(self.video.with_suffix(".txt")), self.info.st_size, self.info.st_mtime_ns, 1)
            set_source.assert_not_called()

    def test_capture_emits_image_then_releases_source(self):
        key = (str(self.video), self.info.st_size, self.info.st_mtime_ns, 1)
        self.service._current = key
        self.service._seen.add(key)
        result = []
        self.service.ready.connect(lambda *values: result.append(values))
        image = QImage(80, 50, QImage.Format.Format_RGB32)
        image.fill(Qt.GlobalColor.blue)
        class Frame:
            def isValid(self):
                return True
            def toImage(self):
                return image
        with patch.object(self.service._player, "stop"), \
             patch.object(self.service._player, "setSource"):
            self.service._frame_ready(Frame())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][:4], key)
        self.assertFalse(result[0][4].isNull())
        self.assertIsNone(self.service._current)
        self.assertIn(key[:3], self.service._cache)

    def test_reset_discards_pending_and_active_work(self):
        key = (str(self.video), self.info.st_size, self.info.st_mtime_ns, 1)
        self.service._current = key
        self.service._queue.append(key)
        self.service._seen.add(key)
        self.service.reset(2)
        self.assertFalse(self.service._queue)
        self.assertFalse(self.service._seen)
        self.assertIsNone(self.service._current)
        self.assertTrue(self.service._player.source().isEmpty())

    def test_cache_hit_returns_without_decoding(self):
        key = (str(self.video), self.info.st_size, self.info.st_mtime_ns)
        picture = QImage(24, 24, QImage.Format.Format_RGB32)
        self.service._cache[key] = picture
        received = []
        self.service.ready.connect(lambda *args: received.append(args))
        with patch.object(self.service._player, "setSource") as set_source:
            self.service.request(*key, 1)
            set_source.assert_not_called()
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0][:4], (*key, 1))

    def test_explorer_can_apply_video_overlay_to_matching_item(self):
        panel = ExplorerPanel()
        try:
            panel.set_active_folder(self.root)
            item = next(
                panel.files.item(i) for i in range(panel.files.count())
                if panel.files.item(i).text() == "teste.mp4"
            )
            before = item.icon().cacheKey()
            picture = QImage(128, 104, QImage.Format.Format_RGB32)
            picture.fill(Qt.GlobalColor.darkGray)
            panel._apply_video_thumbnail(
                str(self.video), self.info.st_size, self.info.st_mtime_ns,
                panel._generation, picture,
            )
            self.assertNotEqual(item.icon().cacheKey(), before)
        finally:
            panel.set_active_folder(None)
            panel.close()
            self.assertTrue(panel._pool.waitForDone(10000))


if __name__ == "__main__":
    unittest.main()
