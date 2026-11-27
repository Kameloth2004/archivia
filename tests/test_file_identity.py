"""Caracterização da identidade compartilhada e escopo recursivo de inventário.

Somente arquivos temporários de testes; não altera arquivos pessoais.
"""
import os
from pathlib import Path
import tempfile
import unittest

from archivia.file_identity import file_identity
from archivia.inventory import inventory


class FileIdentityAndRecursionTests(unittest.TestCase):
    def test_identity_matches_previous_contract(self):
        with tempfile.TemporaryDirectory() as name:
            source = Path(name) / "arquivo.jpg"
            source.write_bytes(b"conteudo")
            st = source.stat(follow_symlinks=False)
            self.assertEqual(
                file_identity(st),
                (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns),
            )
            self.assertEqual(file_identity(st), file_identity(st))

    def test_recursive_inventory_includes_nested_files_with_relative_path(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            nested = root / "nivel1" / "nivel2"
            nested.mkdir(parents=True)
            (root / "raiz.jpg").write_bytes(b"r")
            (nested / "profunda.png").write_bytes(b"n")
            all_files = inventory(root, recursive=True)
            root_only = inventory(root, recursive=False)
            self.assertEqual(
                {f["path"] for f in all_files["files"]},
                {"raiz.jpg", "nivel1/nivel2/profunda.png"},
            )
            self.assertEqual(
                {f["path"] for f in root_only["files"]},
                {"raiz.jpg"},
            )

    @unittest.skipUnless(hasattr(os, "symlink"), "Symlink indisponível")
    def test_symlink_directory_not_followed(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            nested = root / "pasta"
            nested.mkdir()
            (nested / "arquivo.jpg").write_bytes(b"x")
            link = root / "atalho"
            try:
                link.symlink_to(nested, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("Symlink sem permissão neste sistema")
            result = inventory(root, recursive=True)
            self.assertEqual([f["path"] for f in result["files"]], ["pasta/arquivo.jpg"])
            self.assertEqual(result["summary"]["symlinks_skipped"], 1)


if __name__ == "__main__":
    unittest.main()
