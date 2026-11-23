"""Testes de formatação de tabelas, sem dependência de PySide6."""
import unittest

from archivia.table_rows import (
    inventory_preview_rows, origin_rows, duplicate_rows,
    date_plan_rows, catalog_rows,
)


class TableRowsTests(unittest.TestCase):
    def test_inventory_rows_are_immutable_presentations(self):
        files = [{"path": "a/foto.jpg", "category": "imagem",
                  "extension": ".jpg", "size_bytes": 123}]
        self.assertEqual(
            inventory_preview_rows(files),
            [("a/foto.jpg", "imagem", ".jpg", "123")],
        )
        self.assertEqual(files[0]["size_bytes"], 123)

    def test_origin_rows(self):
        origins = [{"root": "C:/teste", "scan_id": 3,
                    "indexed_files": 10, "media_files": 8}]
        self.assertEqual(origin_rows(origins), [("C:/teste", "3", "10", "8")])

    def test_duplicate_rows_repeat_original_tooltips(self):
        rows, tips = duplicate_rows([{
            "size_bytes": 9, "sha256": "abcdef",
            "files": ["a.jpg", "b.jpg"],
        }])
        self.assertEqual(rows, [("1", "a.jpg", "9"), ("1", "b.jpg", "9")])
        self.assertEqual(tips[0], ("a.jpg\nSHA-256: abcdef\nGrupo: 1",) * 3)
        self.assertEqual(tips[1], ("b.jpg\nSHA-256: abcdef\nGrupo: 1",) * 3)

    def test_date_plan_rows_preserve_reason_and_warning(self):
        rows, tips = date_plan_rows([{
            "file": "f.jpg", "status": "bloqueado",
            "destination": None, "reason": "conflito",
            "possible_duplicate_by_metadata": True,
        }])
        self.assertEqual(rows, [("f.jpg", "—", "bloqueado", "conflito · Suspeita")])
        self.assertEqual(tips, rows)

    def test_date_plan_rows_show_future_subfolder(self):
        rows, _ = date_plan_rows([{
            "file": "f.jpg", "status": "proposto",
            "directory_would_need_creation": True, "destination": "D:/f.jpg",
        }])
        self.assertEqual(rows[0][3], "Subpasta futura")

    def test_catalog_rows_keep_iso_original_for_date_toggle(self):
        source = [{
            "relative_path": "foto.jpg", "category": "imagem",
            "extension": ".jpg", "size_bytes": 14,
            "modified_utc": "2026-11-23T12:34:56+00:00",
        }]
        br_rows, br_roles = catalog_rows(source, "br")
        iso_rows, iso_roles = catalog_rows(source, "iso")
        self.assertEqual(br_rows[0][4], "23/11/2026 12:34:56 UTC")
        self.assertEqual(iso_rows[0][4], "2026-11-23 12:34:56 UTC")
        self.assertEqual(br_roles, iso_roles)
        self.assertEqual(br_roles[0], (None, None, None, None, source[0]["modified_utc"]))
        self.assertEqual(source[0]["modified_utc"], "2026-11-23T12:34:56+00:00")

    def test_empty_tables(self):
        self.assertEqual(inventory_preview_rows([]), [])
        self.assertEqual(origin_rows([]), [])
        self.assertEqual(duplicate_rows([]), ([], []))
        self.assertEqual(date_plan_rows([]), ([], []))
        self.assertEqual(catalog_rows([], "br"), ([], []))
