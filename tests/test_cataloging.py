"""TEST-ONLY: catalogação por confirmação lógica, sem GUI e sem dados pessoais."""
import unittest

from support import temporary_test_directory
from archivia.catalog import catalog_summary
from archivia.cataloging import catalog_verified_preview
from archivia.inventory import inventory


class CatalogingTests(unittest.TestCase):
    def test_valid_preview_creates_snapshot_only_in_sqlite(self):
        with temporary_test_directory() as tmp:
            root = tmp / "midias"
            root.mkdir()
            original = root / "arquivo.pdf"
            original.write_bytes(b"documento")
            before = original.read_bytes()
            preview = inventory(root)
            db = tmp / "data" / "catalogo.sqlite3"
            saved = catalog_verified_preview(preview, db)
            self.assertEqual(saved["scan_id"], 1)
            self.assertEqual(catalog_summary(db)["indexed_files"], 1)
            self.assertEqual(original.read_bytes(), before)

    def test_modified_file_rejects_without_creating_db(self):
        with temporary_test_directory() as tmp:
            root = tmp / "midias"
            root.mkdir()
            sample = root / "foto.jpg"
            sample.write_bytes(b"a")
            preview = inventory(root)
            sample.write_bytes(b"mudou")
            db = tmp / "data" / "catalogo.sqlite3"
            with self.assertRaisesRegex(ValueError, "mudaram"):
                catalog_verified_preview(preview, db)
            self.assertFalse(db.exists())

    def test_added_file_rejects_without_creating_db(self):
        with temporary_test_directory() as tmp:
            root = tmp / "midias"
            root.mkdir()
            (root / "foto.jpg").write_bytes(b"a")
            preview = inventory(root)
            (root / "novo.pdf").write_bytes(b"novo")
            db = tmp / "data" / "catalogo.sqlite3"
            with self.assertRaises(ValueError):
                catalog_verified_preview(preview, db)
            self.assertFalse(db.exists())

    def test_incomplete_or_invalid_preview_rejected(self):
        with temporary_test_directory() as tmp:
            root = tmp / "midias"
            root.mkdir()
            preview = inventory(root)
            db = tmp / "data" / "catalogo.sqlite3"
            incomplete = {**preview, "errors": [{"error": "acesso negado"}]}
            with self.assertRaises(ValueError):
                catalog_verified_preview(incomplete, db)
            with self.assertRaises(ValueError):
                catalog_verified_preview({}, db)
            self.assertFalse(db.exists())


if __name__ == "__main__":
    unittest.main()
