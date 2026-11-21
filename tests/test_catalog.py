"""Testes SQLite em diretórios temporários, sem acessar mídias pessoais."""

from contextlib import closing
import sqlite3
import unittest
from pathlib import Path

from support import temporary_test_directory

from archivia.catalog import query_catalog, store_inventory
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

            with closing(sqlite3.connect(database)) as conn:
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


    def test_query_latest_snapshot_and_category_filter(self):
        # TEST-ONLY: arquivos sintéticos e SQLite restritos a tests/.runtime.
        with temporary_test_directory() as tmp:
            media_dir = tmp / "midias"
            media_dir.mkdir()
            (media_dir / "foto.jpg").write_bytes(b"a")
            db = tmp / "data" / "catalogo.sqlite3"
            first = store_inventory(inventory(media_dir), db)
            (media_dir / "audio.mp3").write_bytes(b"bc")
            second = store_inventory(inventory(media_dir), db)

            all_files = query_catalog(db)
            images = query_catalog(db, "imagem")
            audios = query_catalog(db, "audio")

            self.assertNotEqual(first["scan_id"], second["scan_id"])
            self.assertEqual(all_files["scan_id"], second["scan_id"])
            self.assertEqual(all_files["count"], 2)
            self.assertEqual(images["count"], 1)
            self.assertEqual(images["files"][0]["relative_path"], "foto.jpg")
            self.assertEqual(audios["files"][0]["relative_path"], "audio.mp3")

    def test_query_missing_database_does_not_create_it(self):
        with temporary_test_directory() as tmp:
            db = tmp / "ausente.sqlite3"
            with self.assertRaises(ValueError):
                query_catalog(db)
            self.assertFalse(db.exists())


if __name__ == "__main__":
    unittest.main()
