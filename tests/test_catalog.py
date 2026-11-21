"""Testes SQLite em diretórios temporários, sem acessar mídias pessoais."""

from contextlib import closing
from datetime import datetime, timezone
import os
import sqlite3
import unittest
from pathlib import Path

from support import temporary_test_directory

from archivia.catalog import catalog_summary, query_catalog, query_catalog_page, list_catalog_scans, catalog_origins_summary, store_inventory
from archivia.inventory import CATEGORIES, inventory


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

    def test_summary_uses_latest_snapshot_without_listing_files(self):
        # TEST-ONLY: nunca acessa o banco real nem mídias pessoais.
        with temporary_test_directory() as tmp:
            root = tmp / "midias"
            root.mkdir()
            (root / "foto.jpg").write_bytes(b"abc")
            db = tmp / "data" / "catalogo.sqlite3"
            store_inventory(inventory(root), db)
            (root / "musica.mp3").write_bytes(b"de")
            latest = store_inventory(inventory(root), db)

            result = catalog_summary(db)
            self.assertEqual(result["scan_id"], latest["scan_id"])
            self.assertEqual(result["media_files"], 2)
            self.assertEqual(result["bytes_media"], 5)
            self.assertEqual(result["by_category"], {**{category: 0 for category in CATEGORIES}, "imagem": 1, "audio": 1})
            self.assertNotIn("files", result)

    def test_universal_catalog_persists_and_filters_without_migration(self):
        # TEST-ONLY: valida que o schema anterior suporta categorias novas.
        with temporary_test_directory() as tmp:
            root = tmp / "arquivos"
            root.mkdir()
            (root / "foto.jpg").write_bytes(b"abc")
            (root / "texto.pdf").write_bytes(b"pdf")
            (root / "backup.zip").write_bytes(b"zip")
            (root / "arquivo.unknown").write_bytes(b"otro")
            db = tmp / "catalogo.sqlite3"
            store_inventory(inventory(root), db)
            result = catalog_summary(db)
            docs = query_catalog_page(db, category="documento")
            archives = query_catalog(db, category="compactado")
            unknown = query_catalog_page(db, category="outro")
            self.assertEqual(result["indexed_files"], 4)
            self.assertEqual(result["media_files"], 1)
            self.assertEqual(result["other_files"], 3)
            self.assertEqual(result["by_category"]["documento"], 1)
            self.assertEqual(result["by_category"]["compactado"], 1)
            self.assertEqual(result["by_category"]["outro"], 1)
            self.assertEqual(docs["files"][0]["relative_path"], "texto.pdf")
            self.assertEqual(archives["files"][0]["relative_path"], "backup.zip")
            self.assertEqual(unknown["count"], 1)

    def test_summary_missing_database_never_creates_file(self):
        with temporary_test_directory() as tmp:
            db = tmp / "inexistente.sqlite3"
            with self.assertRaises(ValueError):
                catalog_summary(db)
            self.assertFalse(db.exists())

    def test_pagination_and_category_filters_are_read_only(self):
        # TEST-ONLY: banco de dados e mídias sintéticos ficam em tests/.runtime.
        with temporary_test_directory() as tmp:
            root = tmp / "midias"
            root.mkdir()
            for i in range(7):
                (root / f"foto{i:02d}.jpg").write_bytes(b"abc")
            (root / "trilha.mp3").write_bytes(b"som")
            db = tmp / "data" / "catalogo.sqlite3"
            store_inventory(inventory(root), db)
            first = query_catalog_page(db, page=1, page_size=3)
            second = query_catalog_page(db, page=2, page_size=3)
            last = query_catalog_page(db, page=3, page_size=3)
            filtered = query_catalog_page(db, category="audio", page_size=3)
            beyond = query_catalog_page(db, page=4, page_size=3)
            self.assertEqual(first["count"], 8)
            self.assertEqual(first["pages"], 3)
            self.assertEqual([len(p["files"]) for p in (first, second, last)], [3, 3, 2])
            self.assertEqual(len({
                f["relative_path"] for p in (first, second, last) for f in p["files"]
            }), 8)
            self.assertEqual(filtered["count"], 1)
            self.assertEqual(filtered["files"][0]["relative_path"], "trilha.mp3")
            self.assertEqual(beyond["files"], [])
            self.assertTrue((root / "foto00.jpg").exists())

    def test_pagination_rejects_bad_limits_and_missing_database(self):
        with temporary_test_directory() as tmp:
            db = tmp / "nao_existe.sqlite3"
            with self.assertRaises(ValueError):
                query_catalog_page(db)
            self.assertFalse(db.exists())
            root = tmp / "midias"
            root.mkdir()
            store_inventory(inventory(root), tmp / "catalogo.sqlite3")
            db = tmp / "catalogo.sqlite3"
            for invalid_page in (0, -1, True):
                with self.assertRaises(ValueError):
                    query_catalog_page(db, page=invalid_page)
            for invalid_size in (0, 101, True):
                with self.assertRaises(ValueError):
                    query_catalog_page(db, page_size=invalid_size)

    def test_history_lists_snapshots_and_selects_previous_scan(self):
        # TEST-ONLY: histórico isolado em tests/.runtime, nunca banco do usuário.
        with temporary_test_directory() as tmp:
            root_a = tmp / "origem_a"
            root_b = tmp / "origem_b"
            root_a.mkdir()
            root_b.mkdir()
            (root_a / "foto.jpg").write_bytes(b"a")
            (root_b / "manual.pdf").write_bytes(b"bb")
            database = tmp / "data" / "catalogo.sqlite3"
            first = store_inventory(inventory(root_a), database)
            second = store_inventory(inventory(root_b), database)
            scans = list_catalog_scans(database)
            self.assertEqual([s["id"] for s in scans], [second["scan_id"], first["scan_id"]])
            self.assertEqual([s["indexed_files"] for s in scans], [1, 1])
            older = query_catalog_page(database, scan_id=first["scan_id"])
            current = query_catalog_page(database)
            self.assertEqual(older["root"], str(root_a))
            self.assertEqual(older["files"][0]["relative_path"], "foto.jpg")
            self.assertEqual(current["root"], str(root_b))
            self.assertEqual(current["files"][0]["relative_path"], "manual.pdf")
            self.assertEqual(list_catalog_scans(database, limit=1)[0]["id"], second["scan_id"])

    def test_history_rejects_invalid_ids_and_missing_database(self):
        with temporary_test_directory() as tmp:
            database = tmp / "data" / "catalogo.sqlite3"
            with self.assertRaises(ValueError):
                list_catalog_scans(database)
            self.assertFalse(database.exists())
            root = tmp / "origem"
            root.mkdir()
            store_inventory(inventory(root), database)
            with self.assertRaises(ValueError):
                query_catalog_page(database, scan_id=9999)
            for invalid in (0, -1, True):
                with self.assertRaises(ValueError):
                    query_catalog_page(database, scan_id=invalid)
            for invalid in (0, 1001, True):
                with self.assertRaises(ValueError):
                    list_catalog_scans(database, limit=invalid)

    def test_origins_summary_uses_only_latest_snapshot_for_each_root(self):
        # TEST-ONLY: múltiplos diretórios sintéticos, sem banco pessoal.
        with temporary_test_directory() as tmp:
            first_root = tmp / "origem_a"
            second_root = tmp / "origem_b"
            first_root.mkdir()
            second_root.mkdir()
            (first_root / "a.jpg").write_bytes(b"a")
            (second_root / "b.pdf").write_bytes(b"bb")
            db = tmp / "data" / "catalogo.sqlite3"
            old = store_inventory(inventory(first_root), db)
            (first_root / "novo.mp4").write_bytes(b"ccc")
            latest = store_inventory(inventory(first_root), db)
            other = store_inventory(inventory(second_root), db)
            summary = catalog_origins_summary(db)
            self.assertEqual(summary["origins_count"], 2)
            self.assertEqual(summary["indexed_files"], 3)
            self.assertEqual(summary["bytes_indexed"], 6)
            self.assertEqual(summary["media_files"], 2)
            self.assertEqual(summary["by_category"]["imagem"], 1)
            self.assertEqual(summary["by_category"]["video"], 1)
            self.assertEqual(summary["by_category"]["documento"], 1)
            self.assertEqual(
                {origin["scan_id"] for origin in summary["origins"]},
                {latest["scan_id"], other["scan_id"]},
            )
            self.assertNotIn(old["scan_id"], {
                origin["scan_id"] for origin in summary["origins"]
            })

    def test_origins_summary_missing_database_and_empty_catalog(self):
        with temporary_test_directory() as tmp:
            db = tmp / "data" / "catalogo.sqlite3"
            with self.assertRaises(ValueError):
                catalog_origins_summary(db)
            self.assertFalse(db.exists())
            root = tmp / "vazia"
            root.mkdir()
            store_inventory(inventory(root), db)
            result = catalog_origins_summary(db)
            self.assertEqual(result["origins_count"], 1)
            self.assertEqual(result["indexed_files"], 0)
            self.assertEqual(result["bytes_indexed"], 0)

    def test_search_name_extension_history_and_literal_wildcards(self):
        # TEST-ONLY: busca SQL em arquivos sintéticos e banco descartável.
        with temporary_test_directory() as tmp:
            root = tmp / "arquivos"
            root.mkdir()
            (root / "ventilador_manual.PDF").write_bytes(b"a")
            (root / "ventilador_foto.jpg").write_bytes(b"bc")
            (root / "100%_real.txt").write_bytes(b"d")
            (root / "outro.txt").write_bytes(b"e")
            db = tmp / "data" / "catalogo.sqlite3"
            first = store_inventory(inventory(root), db)
            (root / "ventilador_novo.pdf").write_bytes(b"f")
            second = store_inventory(inventory(root), db)

            named = query_catalog_page(db, name_contains="ventilador", page_size=2)
            self.assertEqual(named["count"], 3)
            self.assertEqual(named["pages"], 2)
            self.assertEqual(len(named["files"]), 2)
            pdfs = query_catalog_page(db, name_contains="ventilador", extension="PDF")
            self.assertEqual(pdfs["count"], 2)
            self.assertTrue(all(f["extension"] == ".pdf" for f in pdfs["files"]))
            old = query_catalog_page(db, scan_id=first["scan_id"], extension=".pdf")
            self.assertEqual(old["count"], 1)
            self.assertEqual(query_catalog_page(db, scan_id=second["scan_id"])["count"], 5)
            literal = query_catalog_page(db, name_contains="%_")
            self.assertEqual(literal["count"], 1)
            self.assertEqual(literal["files"][0]["relative_path"], "100%_real.txt")
            self.assertEqual(query_catalog_page(db, extension="unknown")["count"], 0)

    def test_search_filters_reject_invalid_inputs(self):
        with temporary_test_directory() as tmp:
            root = tmp / "files"
            root.mkdir()
            db = tmp / "catalogo.sqlite3"
            store_inventory(inventory(root), db)
            for field in ({"name_contains": "a" * 201}, {"extension": "x" * 31},
                          {"name_contains": 1}, {"extension": 2}):
                with self.assertRaises(ValueError):
                    query_catalog_page(db, **field)

    def test_filename_scope_excludes_directory_matches(self):
        # TEST-ONLY: nomes de pastas não devem contaminar busca por nome-base.
        with temporary_test_directory() as tmp:
            root = tmp / "origem"
            folder = root / "BACKUPS"
            folder.mkdir(parents=True)
            (folder / "documento.pdf").write_bytes(b"doc")
            (root / "backup_relatorio.pdf").write_bytes(b"relatorio")
            db = tmp / "data" / "catalogo.sqlite3"
            store_inventory(inventory(root), db)
            by_path = query_catalog_page(db, name_contains="backup", search_scope="path")
            by_name = query_catalog_page(db, name_contains="backup", search_scope="filename")
            self.assertEqual(by_path["count"], 2)
            self.assertEqual(by_name["count"], 1)
            self.assertEqual(by_name["files"][0]["relative_path"], "backup_relatorio.pdf")
            self.assertEqual(by_name["search_scope"], "filename")

    def test_modified_date_range_and_sorting(self):
        # TEST-ONLY: timestamps sintéticos em UTC no diretório de testes.
        with temporary_test_directory() as tmp:
            root = tmp / "origem"
            root.mkdir()
            timestamps = {
                "antigo.jpg": "2024-02-10",
                "medio.pdf": "2025-04-20",
                "novo.zip": "2026-08-08",
            }
            for name, day in timestamps.items():
                file = root / name
                file.write_bytes(b"x")
                instant = datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp()
                os.utime(file, (instant, instant))
            db = tmp / "data" / "catalogo.sqlite3"
            store_inventory(inventory(root), db)
            newest = query_catalog_page(db, sort_by="newest")
            oldest = query_catalog_page(db, sort_by="oldest")
            filtered = query_catalog_page(db, date_from="2025-01-01", date_to="2025-12-31")
            through = query_catalog_page(db, date_to="2024-12-31")
            self.assertEqual(
                [f["relative_path"] for f in newest["files"]],
                ["novo.zip", "medio.pdf", "antigo.jpg"],
            )
            self.assertEqual(
                [f["relative_path"] for f in oldest["files"]],
                ["antigo.jpg", "medio.pdf", "novo.zip"],
            )
            self.assertEqual(filtered["count"], 1)
            self.assertEqual(filtered["files"][0]["relative_path"], "medio.pdf")
            self.assertEqual(through["count"], 1)

    def test_search_scope_and_date_validations(self):
        with temporary_test_directory() as tmp:
            root = tmp / "origem"
            root.mkdir()
            db = tmp / "data" / "catalogo.sqlite3"
            store_inventory(inventory(root), db)
            for arguments in (
                {"search_scope": "invalid"},
                {"sort_by": "invalid"},
                {"date_from": "2025-02-30"},
                {"date_from": "2025-1-01"},
                {"date_to": "2025-00-10"},
                {"date_from": "2026-01-01", "date_to": "2025-12-31"},
                {"date_from": 42},
            ):
                with self.subTest(arguments=arguments):
                    with self.assertRaises(ValueError):
                        query_catalog_page(db, **arguments)

    def test_query_missing_database_does_not_create_it(self):
        with temporary_test_directory() as tmp:
            db = tmp / "ausente.sqlite3"
            with self.assertRaises(ValueError):
                query_catalog(db)
            self.assertFalse(db.exists())


if __name__ == "__main__":
    unittest.main()
