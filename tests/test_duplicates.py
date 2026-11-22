"""TEST-ONLY: SHA-256 em fixtures sintéticos, sem mídia real ou escrita no SQLite."""
from __future__ import annotations

import hashlib
from pathlib import Path
import shutil
import unittest

from support import temporary_test_directory
from archivia.catalog import store_inventory
from archivia.duplicates import verify_duplicate_hashes
from archivia.inventory import inventory

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "sha256_demo"


class DuplicateHashTests(unittest.TestCase):
    def _catalog_fixture(self, tmp):
        root = tmp / "origem"
        shutil.copytree(FIXTURES, root)
        db = tmp / "catalogo.sqlite3"
        snapshot = store_inventory(inventory(root), db)
        return root, db, snapshot["scan_id"]

    def test_identifies_same_bytes_across_names_and_zero_byte_files(self):
        # TEST-ONLY: três arquivos iguais, dois vazios e falsos positivos de tamanho/nome.
        with temporary_test_directory() as tmp:
            root, db, scan_id = self._catalog_fixture(tmp)
            before = {str(p.relative_to(root)): p.read_bytes()
                      for p in root.rglob("*") if p.is_file()}
            result = verify_duplicate_hashes(db, category="imagem", scan_id=scan_id)
            self.assertEqual(result["confirmed_groups_in_sample"], 2)
            self.assertEqual(result["confirmed_files_in_sample"], 5)
            self.assertEqual(result["selected"], 8)
            self.assertFalse(result["truncated"])
            self.assertFalse(result["files_modified"])
            self.assertFalse(result["executable"])
            groups = [set(g["files"]) for g in result["groups"]]
            self.assertIn({
                "A/foto_igual.jpg", "B/foto_igual.jpg", "B/alias_nome_diferente.jpg"
            }, groups)
            self.assertIn({"A/vazio.jpg", "B/vazio_copia.jpg"}, groups)
            self.assertFalse(any("C/foto_igual.jpg" in group for group in groups))
            self.assertFalse(any("mesmo_tamanho.jpg" in filename
                                 for group in groups for filename in group))
            empty_group = next(g for g in result["groups"] if g["size_bytes"] == 0)
            self.assertEqual(empty_group["sha256"], hashlib.sha256(b"").hexdigest())
            self.assertEqual(before, {str(p.relative_to(root)): p.read_bytes()
                                      for p in root.rglob("*") if p.is_file()})

    def test_limits_skip_large_files_and_incomplete_sample(self):
        # TEST-ONLY: amostra de 2 registros, sem afirmar ausência no resto da origem.
        with temporary_test_directory() as tmp:
            root, db, scan_id = self._catalog_fixture(tmp)
            small_sample = verify_duplicate_hashes(db, category="imagem", limit=2)
            self.assertEqual(small_sample["selected"], 2)
            self.assertTrue(small_sample["truncated"])
            capped = verify_duplicate_hashes(db, category="imagem", max_file_bytes=1)
            self.assertTrue(any(s["reason"] == "arquivo_acima_do_limite"
                                for s in capped["skipped"]))
            self.assertEqual(capped["confirmed_groups_in_sample"], 1)  # dois vazios
            self.assertEqual(capped["hashed_files"], 2)
            self.assertEqual(capped["bytes_read"], 0)
            self.assertTrue((root / "A" / "foto_igual.jpg").exists())

    def test_rejects_invalid_limits_and_unavailable_catalog(self):
        with temporary_test_directory() as tmp:
            db = tmp / "nao_existe.sqlite3"
            for kwargs in (
                {"limit": 0}, {"limit": 101}, {"limit": True},
                {"max_file_bytes": 0}, {"max_file_bytes": 16 * 1024 * 1024 + 1},
                {"max_total_bytes": 0}, {"max_total_bytes": True},
            ):
                with self.subTest(kwargs=kwargs):
                    with self.assertRaises(ValueError):
                        verify_duplicate_hashes(db, **kwargs)
            with self.assertRaises(ValueError):
                verify_duplicate_hashes(db)
            self.assertFalse(db.exists())

    def test_changed_or_missing_sources_are_not_reported_equal(self):
        with temporary_test_directory() as tmp:
            root, db, _ = self._catalog_fixture(tmp)
            (root / "A" / "foto_igual.jpg").write_bytes(b"MUDOU")
            (root / "B" / "alias_nome_diferente.jpg").unlink()
            result = verify_duplicate_hashes(db, category="imagem")
            failures = {s["file"]: s["reason"] for s in result["skipped"]}
            self.assertEqual(failures["A/foto_igual.jpg"], "arquivo_alterado_desde_inventario")
            self.assertEqual(failures["B/alias_nome_diferente.jpg"], "arquivo_ausente")
            self.assertFalse(any("A/foto_igual.jpg" in g["files"] for g in result["groups"]))

    def test_paged_scan_detects_equal_content_across_pages(self):
        # TEST-ONLY: dois conteúdos iguais separados por mais de 100 nomes.
        with temporary_test_directory() as tmp:
            root = tmp / "origem"
            root.mkdir()
            for number in range(125):
                (root / f"m{number:03d}.jpg").write_bytes(
                    f"conteudo-{number:03d}".encode("ascii")
                )
            (root / "a_primeiro.jpg").write_bytes(b"mesmos-bytes-entre-paginas")
            (root / "z_ultimo.jpg").write_bytes(b"mesmos-bytes-entre-paginas")
            db = tmp / "catalogo.sqlite3"
            store_inventory(inventory(root), db)
            events = []
            result = verify_duplicate_hashes(
                db, category="imagem", limit=150, progress=events.append
            )
            self.assertEqual(result["selected"], 127)
            self.assertEqual(result["pages_scanned"], 2)
            self.assertFalse(result["truncated"])
            self.assertEqual(result["confirmed_groups_in_sample"], 1)
            self.assertEqual(result["groups"][0]["files"], [
                "a_primeiro.jpg", "z_ultimo.jpg",
            ])
            self.assertTrue(any(e["phase"] == "catalog" for e in events))
            self.assertTrue(any(e["phase"] == "hash" for e in events))
            self.assertEqual(events[-1]["phase"], "done")
            self.assertFalse(result["files_modified"])

    def test_page_limit_prevents_false_global_completeness(self):
        # TEST-ONLY: um par de duplicatas atravessa o limite da amostra.
        with temporary_test_directory() as tmp:
            root = tmp / "origem"
            root.mkdir()
            for number in range(110):
                (root / f"b{number:03d}.jpg").write_bytes(
                    f"unico-{number:03d}".encode("ascii")
                )
            (root / "a_inicio.jpg").write_bytes(b"PAR_EM_PAGINAS")
            (root / "z_final.jpg").write_bytes(b"PAR_EM_PAGINAS")
            db = tmp / "catalogo.sqlite3"
            store_inventory(inventory(root), db)
            first = verify_duplicate_hashes(db, category="imagem", limit=100)
            complete = verify_duplicate_hashes(db, category="imagem", limit=200)
            self.assertTrue(first["truncated"])
            self.assertEqual(first["confirmed_groups_in_sample"], 0)
            self.assertFalse(complete["truncated"])
            self.assertEqual(complete["confirmed_groups_in_sample"], 1)
            self.assertEqual(complete["selected"], 112)

    def test_progress_input_validation_and_budget_maximum(self):
        with temporary_test_directory() as tmp:
            root, db, _ = self._catalog_fixture(tmp)
            for kwargs in (
                {"limit": 1001}, {"max_total_bytes": 256 * 1024 * 1024 + 1},
                {"progress": "não é callback"},
            ):
                with self.subTest(kwargs=kwargs):
                    with self.assertRaises(ValueError):
                        verify_duplicate_hashes(db, category="imagem", **kwargs)
            progress = []
            verified = verify_duplicate_hashes(
                db, category="imagem", limit=1000, progress=progress.append
            )
            self.assertEqual(verified["selected"], 8)
            self.assertTrue(progress)
            self.assertEqual(progress[-1], {"phase": "done", "processed": 8, "total": 8})
            self.assertTrue((root / "A" / "foto_igual.jpg").exists())

    def test_total_read_budget_is_respected(self):
        with temporary_test_directory() as tmp:
            _, db, _ = self._catalog_fixture(tmp)
            result = verify_duplicate_hashes(db, category="imagem", max_total_bytes=1)
            self.assertLessEqual(result["bytes_read"], 1)
            self.assertTrue(any(s["reason"] == "limite_total_de_leitura"
                                for s in result["skipped"]))


if __name__ == "__main__":
    unittest.main()
