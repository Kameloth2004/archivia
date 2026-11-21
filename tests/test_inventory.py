"""Testes de inventário sem arquivos pessoais."""

import unittest
from pathlib import Path

from support import temporary_test_directory

from archivia.inventory import inventory


class InventoryTests(unittest.TestCase):
    def test_inventory_only_reads_and_classifies_extensions(self):
        with temporary_test_directory() as tmp:
            root = tmp
            sub = root / "fotos"
            sub.mkdir()
            image = sub / "imagem.JPG"
            image.write_bytes(b"abc")
            (root / "nota.txt").write_text("texto", encoding="utf-8")
            before = image.read_bytes()

            result = inventory(root)

            self.assertEqual(len(result["files"]), 1)
            self.assertEqual(result["files"][0]["path"], "fotos/imagem.JPG")
            self.assertEqual(result["files"][0]["category"], "imagem")
            self.assertEqual(result["files"][0]["size_bytes"], 3)
            self.assertEqual(result["summary"]["other_files"], 1)
            self.assertEqual(result["errors"], [])
            self.assertEqual(image.read_bytes(), before)

    def test_nonexistent_directory_is_rejected(self):
        with temporary_test_directory() as tmp:
            with self.assertRaises(ValueError):
                inventory(tmp / "inexistente")

    def test_symlink_not_followed(self):
        with temporary_test_directory() as tmp:
            root = tmp
            target = root / "foto.png"
            target.write_bytes(b"a")
            link = root / "link.png"
            try:
                link.symlink_to(target)
            except (OSError, NotImplementedError):
                self.skipTest("Sistema não permite criação de links simbólicos")
            result = inventory(root)
            self.assertEqual(result["summary"]["media_files"], 1)
            self.assertEqual(result["summary"]["symlinks_skipped"], 1)


if __name__ == "__main__":
    unittest.main()
