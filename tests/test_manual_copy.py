"""Teste do piloto manual: cópias reais apenas em pastas temporárias descartáveis."""
import hashlib
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from archivia.manual_copy import (
    preview_manual_image_copy, copy_manual_image_verified,
)


class ManualCopyTests(unittest.TestCase):
    def fixture(self, root):
        original = root / "origem"
        target = root / "destino"
        original.mkdir()
        target.mkdir()
        file = original / "imagem.jpg"
        file.write_bytes(b"IMAGEM DE TESTE ARCHIVIA")
        return file, target

    def approve(self, file, folder):
        p = preview_manual_image_copy(file, folder)
        return {
            "approved_source": p["source"],
            "approved_destination": p["destination"],
        }

    def test_copies_one_image_with_hash_and_preserves_original(self):
        with tempfile.TemporaryDirectory() as temp:
            file, folder = self.fixture(Path(temp))
            kwargs = self.approve(file, folder)
            result = copy_manual_image_verified(file, folder, **kwargs)
            destination = folder / file.name
            self.assertEqual(result["status"], "copia_verificada")
            self.assertTrue(result["source_preserved"])
            self.assertTrue(file.exists())
            self.assertEqual(file.read_bytes(), destination.read_bytes())
            self.assertEqual(result["sha256"], hashlib.sha256(file.read_bytes()).hexdigest())
            self.assertTrue(Path(result["journal"]).exists())
            self.assertEqual(list(folder.glob(".archivia-manual-*.tmp")), [])

    def test_requires_exact_approved_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            file, folder = self.fixture(Path(temp))
            with self.assertRaisesRegex(ValueError, "diferentes"):
                copy_manual_image_verified(
                    file, folder, approved_source=str(file),
                    approved_destination=str(folder / "nao-aprovado.jpg"),
                )
            self.assertTrue(file.exists())
            self.assertFalse((folder / file.name).exists())

    def test_refuses_existing_target_without_replacing(self):
        with tempfile.TemporaryDirectory() as temp:
            file, folder = self.fixture(Path(temp))
            target = folder / file.name
            target.write_bytes(b"OUTRA IMAGEM")
            with self.assertRaisesRegex(ValueError, "existe|sobrescrita"):
                preview_manual_image_copy(file, folder)
            self.assertEqual(target.read_bytes(), b"OUTRA IMAGEM")
            self.assertTrue(file.exists())

    def test_rejects_unsupported_extension(self):
        with tempfile.TemporaryDirectory() as temp:
            file, folder = self.fixture(Path(temp))
            file.rename(file.with_suffix(".exe"))
            with self.assertRaisesRegex(ValueError, "apenas"):
                preview_manual_image_copy(file.with_suffix(".exe"), folder)

    def test_rejects_same_source_destination_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            file, folder = self.fixture(Path(temp))
            with self.assertRaisesRegex(ValueError, "diferente"):
                preview_manual_image_copy(file, file.parent)

    def test_copy_failure_does_not_delete_source(self):
        with tempfile.TemporaryDirectory() as temp:
            file, folder = self.fixture(Path(temp))
            kwargs = self.approve(file, folder)
            from archivia import manual_copy
            original_digest = manual_copy._digest

            def fail_temp_digest(path):
                if Path(path).suffix == ".tmp":
                    raise OSError("falha simulada SHA")
                return original_digest(path)

            with patch("archivia.manual_copy._digest", side_effect=fail_temp_digest):
                with self.assertRaisesRegex(OSError, "falha simulada"):
                    copy_manual_image_verified(file, folder, **kwargs)
            self.assertTrue(file.exists())
            self.assertFalse((folder / file.name).exists())

    def test_collision_case_insensitive_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            file, folder = self.fixture(Path(temp))
            (folder / "IMAGEM.JPG").write_bytes(b"EXISTENTE")
            with self.assertRaisesRegex(ValueError, "existe|sobrescrita"):
                preview_manual_image_copy(file, folder)
            self.assertEqual((folder / "IMAGEM.JPG").read_bytes(), b"EXISTENTE")
