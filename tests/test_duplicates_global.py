"""TEST-ONLY: análise de candidatos do snapshot completo, sem tocar em mídia real."""
from __future__ import annotations

from pathlib import Path
import shutil
import unittest

from support import temporary_test_directory
from archivia.catalog import store_inventory
from archivia.duplicates import verify_snapshot_duplicate_candidates
from archivia.inventory import inventory

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "sha256_demo"


class GlobalCandidatesTests(unittest.TestCase):
    def test_global_scope_uses_all_eight_fixture_files(self):
        with temporary_test_directory() as tmp:
            root = tmp / "origem"
            shutil.copytree(FIXTURES, root)
            db = tmp / "db.sqlite3"
            stored = store_inventory(inventory(root), db)
            events = []
            result = verify_snapshot_duplicate_candidates(
                db, category="imagem", scan_id=stored["scan_id"],
                max_candidates=50, progress=events.append,
            )
            self.assertEqual(result["total_matches"], 8)
            self.assertEqual(result["candidate_files_total"], 8)
            self.assertEqual(result["confirmed_groups_in_sample"], 2)
            self.assertEqual(result["confirmed_files_in_sample"], 5)
            self.assertEqual(result["unprocessed_candidate_files"], 0)
            self.assertTrue(result["complete"])
            self.assertFalse(result["executable"])
            self.assertFalse(result["files_modified"])
            self.assertEqual(events[-1]["phase"], "done")

    def test_group_not_sliced_even_when_larger_than_candidate_limit(self):
        # TEST-ONLY: grupo grande com nomes/tamanhos iguais, um par menor separado.
        with temporary_test_directory() as tmp:
            root = tmp / "origem"
            root.mkdir()
            for i in range(115):
                (root / f"m{i:03d}.jpg").write_bytes(f"PAYLOAD-{i:03d}".encode())
            (root / "a_primeiro.jpg").write_bytes(b"PAR-REPETIDO-COM-OUTRO-TAMANHO")
            (root / "z_ultimo.jpg").write_bytes(b"PAR-REPETIDO-COM-OUTRO-TAMANHO")
            db = tmp / "catalogo.sqlite3"
            store_inventory(inventory(root), db)
            result = verify_snapshot_duplicate_candidates(
                db, category="imagem", max_candidates=5,
            )
            self.assertEqual(result["total_matches"], 117)
            self.assertEqual(result["candidate_files_total"], 117)
            self.assertEqual(result["selected"], 2)
            self.assertEqual(result["unprocessed_candidate_files"], 115)
            self.assertEqual(result["size_groups_omitted"], 1)
            self.assertFalse(result["complete"])
            self.assertTrue(result["truncated"])
            self.assertEqual(result["confirmed_groups_in_sample"], 1)
            self.assertEqual(result["groups"][0]["files"],
                             ["a_primeiro.jpg", "z_ultimo.jpg"])

    def test_global_detects_distant_pair_in_snapshot_above_one_thousand(self):
        with temporary_test_directory() as tmp:
            root = tmp / "origem"
            root.mkdir()
            for i in range(1010):
                (root / f"m{i:04d}.jpg").write_bytes(f"CONT-{i:04d}".encode())
            (root / "a_copia.jpg").write_bytes(b"IDENTICOS-FORA-DA-PRIMEIRA-AMOSTRA")
            (root / "z_copia.jpg").write_bytes(b"IDENTICOS-FORA-DA-PRIMEIRA-AMOSTRA")
            db = tmp / "catalogo.sqlite3"
            store_inventory(inventory(root), db)
            result = verify_snapshot_duplicate_candidates(
                db, category="imagem", max_candidates=3,
            )
            self.assertEqual(result["total_matches"], 1012)
            self.assertEqual(result["selected"], 2)
            self.assertEqual(result["confirmed_groups_in_sample"], 1)
            self.assertEqual(result["groups"][0]["files"],
                             ["a_copia.jpg", "z_copia.jpg"])
            self.assertGreater(result["unprocessed_candidate_files"], 1000)

    def test_global_rejects_invalid_args_and_preserves_originals(self):
        with temporary_test_directory() as tmp:
            root = tmp / "origem"
            shutil.copytree(FIXTURES, root)
            db = tmp / "db.sqlite3"
            store_inventory(inventory(root), db)
            for arguments in (
                {"max_candidates": 0}, {"max_candidates": 5001},
                {"max_candidates": True}, {"scan_id": True},
                {"category": "invalida"}, {"max_total_bytes": 0},
                {"progress": "invalid"},
            ):
                with self.subTest(arguments=arguments):
                    with self.assertRaises(ValueError):
                        verify_snapshot_duplicate_candidates(db, **arguments)
            result = verify_snapshot_duplicate_candidates(
                db, category="imagem", max_candidates=50, max_file_bytes=1
            )
            self.assertFalse(result["complete"])
            self.assertGreater(len(result["skipped"]), 0)
            self.assertEqual((root / "A" / "foto_igual.jpg").read_bytes(),
                             b"TEST-ONLY: IMAGEM SINTETICA 0001\n")


if __name__ == "__main__":
    unittest.main()
