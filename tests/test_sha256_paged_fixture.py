"""TEST-ONLY: cenário completo de 134 arquivos, SHA-256 entre páginas SQL."""
from __future__ import annotations

from pathlib import Path
import unittest

from support import temporary_test_directory
from generate_sha256_paged_demo import generate_fixture, fixture_payloads, TOTAL_FILES
from archivia.catalog import store_inventory
from archivia.duplicates import verify_duplicate_hashes
from archivia.inventory import inventory


class PagedFixtureTests(unittest.TestCase):
    def test_generator_produces_expected_groups_between_pages_without_changes(self):
        # TEST-ONLY: usa exclusivamente tests/.runtime; não cria arquivos pessoais.
        with temporary_test_directory() as tmp:
            root = tmp / "cenario"
            fixture = generate_fixture(root)
            self.assertEqual(fixture["files"], 134)
            self.assertEqual(len(list(root.rglob("*.jpg"))), 134)
            db = tmp / "catalogo.sqlite3"
            saved = store_inventory(inventory(root), db)
            events = []
            result = verify_duplicate_hashes(
                db, category="imagem", scan_id=saved["scan_id"],
                limit=200, progress=events.append,
            )
            self.assertEqual(result["selected"], 134)
            self.assertEqual(result["total_matches"], 134)
            self.assertEqual(result["pages_scanned"], 2)
            self.assertFalse(result["truncated"])
            self.assertEqual(result["confirmed_groups_in_sample"], 3)
            self.assertEqual(result["confirmed_files_in_sample"], 7)
            self.assertEqual(sorted(g["count"] for g in result["groups"]), [2, 2, 3])
            self.assertFalse(result["skipped"])
            groups = [set(g["files"]) for g in result["groups"]]
            self.assertIn({
                "A/000_foto_original.jpg", "L/050_alias_nome.jpg",
                "Z/999_foto_copia.jpg",
            }, groups)
            self.assertIn({"B/010_relatorio.jpg", "Y/990_outro_nome.jpg"}, groups)
            self.assertIn({"C/020_vazio.jpg", "X/980_vazio_copia.jpg"}, groups)
            self.assertFalse(any("mesmo_nome" in name for group in groups for name in group))
            self.assertTrue(any(event["phase"] == "catalog" and event["processed"] >= 100
                                for event in events))
            self.assertEqual(events[-1]["phase"], "done")
            self.assertEqual(len(list(root.rglob("*.jpg"))), 134)
            self.assertFalse(result["files_modified"])

    def test_sample_of_100_is_partial_and_cross_page_pairs_can_be_missed(self):
        with temporary_test_directory() as tmp:
            root = tmp / "cenario"
            generate_fixture(root)
            db = tmp / "catalogo.sqlite3"
            store_inventory(inventory(root), db)
            partial = verify_duplicate_hashes(db, category="imagem", limit=100)
            full = verify_duplicate_hashes(db, category="imagem", limit=200)
            self.assertTrue(partial["truncated"])
            self.assertEqual(partial["pages_scanned"], 1)
            self.assertEqual(full["pages_scanned"], 2)
            self.assertEqual(partial["selected"], 100)
            self.assertEqual(full["selected"], 134)
            self.assertEqual(full["confirmed_groups_in_sample"], 3)
            self.assertGreater(full["confirmed_files_in_sample"],
                               partial["confirmed_files_in_sample"])

    def test_generator_rejects_existing_content_and_paths_outside_tests(self):
        with temporary_test_directory() as tmp:
            root = tmp / "cenario"
            root.mkdir()
            marker = root / "nao_apagar.txt"
            marker.write_text("preservar", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                generate_fixture(root)
            self.assertEqual(marker.read_text(encoding="utf-8"), "preservar")
            with self.assertRaises(ValueError):
                generate_fixture(Path.home() / "archivia-forbidden-fixture")
            self.assertEqual(len(fixture_payloads()), TOTAL_FILES)


if __name__ == "__main__":
    unittest.main()
