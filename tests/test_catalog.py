"""Testes SQLite em diretórios temporários, sem acessar mídias pessoais."""

import sqlite3
import unittest
from pathlib import Path

from support import temporary_test_directory

from archivia.catalog import store_inventory
from archivia.inventory import inventory


class CatalogTests(unittest.TestCase):
    def test_persists_snapshot_without_changing_media(self):
        with temporary_test_directory() as tmp:
            base = tmp
            media_dir = base / "midias"
            media_dir.mkdir()
            media = media_dir / "foto.png"
            media.write_bytes(b"conteudo")
            before = media.read_bytes()
            database = base / "data" / "catalogo.sqlite3"

            first = store_inventory(inventory(media_dir), database)
            second = store_inventory(inventory(media_dir), database)

            with sqlite3.connect(database) as conn:
                scans = conn.execute("SELECT COUNT(*) FROM scans").fetchone()[0]
                rows = conn.execute(
                    "SELECT relative_path, category, size_bytes FROM media WHERE scan_id=?",
                    (second["scan_id"],),
                ).fetchall()

            self.assertEqual(scans, 2)
            self.assertEqual(rows, [("foto.png", "imagem", len(before))])
            self.assertNotEqual(first["scan_id"], second["scan_id"])
            self.assertEqual(media.read_bytes(), before)

    def test_rejects_incomplete_inventory(self):
        with temporary_test_directory() as tmp:
            db = tmp / "data" / "catalogo.sqlite3"
            result = {
                "root": tmp,
                "files": [],
                "summary": {"media_files": 0, "other_files": 0,
                            "symlinks_skipped": 0, "bytes_media": 0},
                "errors": [{"path": tmp, "error": "Acesso negado"}],
            }
            with self.assertRaises(ValueError):
                store_inventory(result, db)
            self.assertFalse(db.exists())


if __name__ == "__main__":
    unittest.main()
