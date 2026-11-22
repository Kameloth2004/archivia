"""TEST-ONLY: SHA-256 progressivo em memória, sem escrever na biblioteca."""
from __future__ import annotations

from pathlib import Path
import unittest

from support import temporary_test_directory
from generate_sha256_paged_demo import generate_fixture
from archivia.catalog import store_inventory
from archivia.duplicate_sessions import ProgressiveDuplicateSession
from archivia.inventory import inventory


class ProgressiveDuplicateSessionTests(unittest.TestCase):
    def _make(self, temp_root):
        source = temp_root / "origem"
        generate_fixture(source)
        db = temp_root / "catalogo.sqlite3"
        result = store_inventory(inventory(source), db)
        session = ProgressiveDuplicateSession(
            db, category="imagem", scan_id=result["scan_id"]
        )
        return source, db, session

    def test_progressive_matches_hashes_across_six_batches(self):
        with temporary_test_directory() as temp:
            source, db, session = self._make(temp)
            self.assertEqual(session.total_files, 134)
            self.assertEqual(session.total_candidates, 134)
            events = []
            reports = []
            while not session.done:
                reports.append(session.next_batch(batch_size=25, progress=events.append))
            last = reports[-1]
            self.assertEqual(len(reports), 6)
            self.assertEqual(last["selected"], 134)
            self.assertEqual(last["hashed_files"], 134)
            self.assertEqual(last["confirmed_groups"], 3)
            self.assertEqual(last["confirmed_files"], 7)
            self.assertEqual(sorted(group["count"] for group in last["groups"]), [2, 2, 3])
            self.assertEqual(last["remaining_candidates"], 0)
            self.assertTrue(last["done"])
            self.assertTrue(last["complete"])
            self.assertEqual(last["skipped"], [])
            self.assertTrue(events)
            self.assertEqual(events[-1]["total"], 134)
            self.assertEqual(session.next_batch()["batch_selected"], 0)
            self.assertEqual(len(list(source.rglob("*.jpg"))), 134)
            self.assertFalse(last["files_modified"])
            self.assertFalse(last["executable"])
            self.assertEqual(last["state_storage"], "memory_only")

    def test_per_batch_limits_mark_skipped_without_false_completeness(self):
        with temporary_test_directory() as temp:
            source, _, session = self._make(temp)
            initial = (source / "A" / "000_foto_original.jpg").read_bytes()
            last = None
            while not session.done:
                last = session.next_batch(batch_size=30, max_file_bytes=1)
            self.assertIsNotNone(last)
            self.assertTrue(last["done"])
            self.assertFalse(last["complete"])
            self.assertGreater(len(last["skipped"]), 0)
            self.assertEqual(last["remaining_candidates"], 0)
            self.assertEqual((source / "A" / "000_foto_original.jpg").read_bytes(), initial)

    def test_session_stays_on_selected_snapshot_after_new_catalog(self):
        with temporary_test_directory() as temp:
            source, db, session = self._make(temp)
            session.next_batch(batch_size=20)
            # O novo snapshot é diferente; sessão segue fixada no anterior.
            store_inventory(inventory(source), db)
            last = None
            while not session.done:
                last = session.next_batch(batch_size=40)
            self.assertEqual(last["scan_id"], 1)
            self.assertEqual(last["selected"], 134)
            self.assertEqual(last["confirmed_files"], 7)

    def test_modified_file_is_skipped_in_next_batch(self):
        with temporary_test_directory() as temp:
            source, _, session = self._make(temp)
            target = source / "Z" / "999_foto_copia.jpg"
            target.write_bytes(b"MODIFICADO")
            last = None
            while not session.done:
                last = session.next_batch(batch_size=25)
            self.assertFalse(last["complete"])
            self.assertIn("Z/999_foto_copia.jpg", {row["file"] for row in last["skipped"]})

    def test_invalid_limits_and_missing_catalog(self):
        with temporary_test_directory() as temp:
            nonexistent = temp / "nao-existe.sqlite3"
            with self.assertRaises(ValueError):
                ProgressiveDuplicateSession(nonexistent)
            _, _, session = self._make(temp)
            for arguments in (
                {"batch_size": 0}, {"batch_size": 201},
                {"batch_size": True}, {"max_file_bytes": 0},
                {"max_total_bytes": 0}, {"progress": "not_callable"},
            ):
                with self.subTest(arguments=arguments):
                    with self.assertRaises(ValueError):
                        session.next_batch(**arguments)
            self.assertEqual(session.summary()["selected"], 0)
            self.assertEqual(session.summary()["remaining_candidates"], 134)


if __name__ == "__main__":
    unittest.main()
