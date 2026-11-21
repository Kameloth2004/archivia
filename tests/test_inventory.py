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

            self.assertEqual(len(result["files"]), 2)
            self.assertEqual(result["files"][0]["path"], "fotos/imagem.JPG")
            self.assertEqual(result["files"][0]["category"], "imagem")
            self.assertEqual(result["files"][0]["size_bytes"], 3)
            self.assertEqual(result["summary"]["other_files"], 1)
            self.assertEqual(result["summary"]["indexed_files"], 2)
            self.assertEqual(result["summary"]["by_category"]["documento"], 1)
            self.assertEqual(result["errors"], [])
            self.assertEqual(image.read_bytes(), before)

    def test_universal_categories_and_archives_not_opened(self):
        # TEST-ONLY: bytes falsos apenas para verificar reconhecimento por extensão.
        with temporary_test_directory() as tmp:
            root = tmp / "biblioteca"
            root.mkdir()
            fixtures = {
                "manual.PDF": "documento",
                "dados.xlsx": "planilha",
                "slides.pptx": "apresentacao",
                "arquivo.zip": "compactado",
                "script.py": "codigo",
                "desconhecido.xyz": "outro",
                "imagem.jpg": "imagem",
            }
            for name in fixtures:
                (root / name).write_bytes(b"mock")
            output = inventory(root)
            mapping = {item["path"]: item["category"] for item in output["files"]}
            self.assertEqual(mapping, fixtures)
            self.assertEqual(output["summary"]["indexed_files"], 7)
            self.assertEqual(output["summary"]["media_files"], 1)
            self.assertEqual(output["summary"]["other_files"], 6)
            self.assertEqual(output["summary"]["bytes_indexed"], 28)
            self.assertEqual(output["summary"]["bytes_media"], 4)
            self.assertEqual(output["errors"], [])

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
