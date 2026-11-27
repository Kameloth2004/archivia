"""Regressões da decodificação de prévias, sem arquivos pessoais."""
from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from support import temporary_test_directory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtGui import QImage
    from PySide6.QtWidgets import QApplication
    from archivia.image_decode import decode_preview
except ImportError:
    QApplication = None


@unittest.skipIf(QApplication is None, "PySide6 opcional não instalado")
class ImageDecodeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_png_qt_original_dimensions_and_small_preview(self):
        with temporary_test_directory() as root:
            path = root / "valid.png"
            image = QImage(320, 160, QImage.Format.Format_RGB32)
            image.fill(0xff204060)
            self.assertTrue(image.save(str(path), "PNG"))
            preview, original = decode_preview(
                path, max_side=96, max_source_pixels=1_000_000,
            )
            self.assertEqual(original, (320, 160))
            self.assertFalse(preview.isNull())
            self.assertLessEqual(max(preview.width(), preview.height()), 96)

    def test_png_too_many_pixels_fails_before_decode(self):
        with temporary_test_directory() as root:
            path = root / "valid.png"
            image = QImage(30, 20, QImage.Format.Format_RGB32)
            self.assertTrue(image.save(str(path), "PNG"))
            with self.assertRaisesRegex(ValueError, "30 × 20"):
                decode_preview(path, max_side=96, max_source_pixels=500)

    def test_unknown_file_explains_missing_pillow_or_invalid_file(self):
        with temporary_test_directory() as root:
            path = root / "invalid.avif"
            path.write_bytes(b"not an image")
            with self.assertRaisesRegex(ValueError, "decodific|Pillow|imagem"):
                decode_preview(path, max_side=96, max_source_pixels=1_000_000)

    def test_valid_avif_decodes_with_pillow_when_available(self):
        try:
            from PIL import Image, features
        except ImportError:
            self.skipTest("Pillow não instalado")
        if not features.check("avif"):
            self.skipTest("Pillow sem suporte AVIF nesta plataforma")
        with temporary_test_directory() as root:
            path = root / "real.avif"
            Image.new("RGB", (96, 64), (8, 100, 150)).save(path, format="AVIF")
            preview, original = decode_preview(
                path, max_side=48, max_source_pixels=1_000_000,
            )
            self.assertEqual(original, (96, 64))
            self.assertFalse(preview.isNull())
            self.assertLessEqual(max(preview.width(), preview.height()), 48)

    def test_pillow_fallback_when_qt_reader_rejects_valid_png(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow não instalado")
        with temporary_test_directory() as root:
            path = root / "valid.png"
            Image.new("RGB", (64, 32), (5, 90, 25)).save(path)
            with patch("archivia.image_decode.QImageReader") as qt_reader:
                qt_reader.return_value.size.return_value.isValid.return_value = False
                qt_reader.return_value.errorString.return_value = "Unsupported image"
                preview, original = decode_preview(
                    path, max_side=32, max_source_pixels=1_000_000,
                )
            self.assertEqual(original, (64, 32))
            self.assertFalse(preview.isNull())


if __name__ == "__main__":
    unittest.main()
