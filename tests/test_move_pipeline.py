"""TEST-ONLY: movimentação de fixtures descartáveis por cópia + SHA-256."""
import unittest
from unittest.mock import patch

from support import temporary_test_directory
from archivia.catalog import store_inventory
from archivia.inventory import inventory
from archivia.planner import propose_moves
from archivia.move_pipeline import move_verified_test_file


_APPROVAL = "CONFIRMO MOVIMENTO DE TESTE"


class MovePipelineTests(unittest.TestCase):
    def _setup(self, tmp):
        source_dir = tmp / "origem"
        target_dir = tmp / "destino"
        source_dir.mkdir()
        target_dir.mkdir()
        source = source_dir / "foto.jpg"
        source.write_bytes(b"ARCHIVIA-FIXTURE-MOVE-V2")
        database = tmp / "catalogo.sqlite3"
        record = store_inventory(inventory(source_dir), database)
        plan = propose_moves(target_dir, "imagem", db_path=database,
                             scan_id=record["scan_id"])
        return source, target_dir / "foto.jpg", database, plan

    def test_verified_move_after_hash_preserves_content(self):
        import hashlib
        with temporary_test_directory() as tmp:
            source, target, database, plan = self._setup(tmp)
            content = source.read_bytes()
            report = move_verified_test_file(plan, database, approval=_APPROVAL)
            self.assertEqual(report["status"], "movido")
            self.assertEqual(report["files_moved"], 1)
            self.assertTrue(report["test_only"])
            self.assertFalse(source.exists())
            self.assertEqual(target.read_bytes(), content)
            self.assertEqual(report["sha256"], hashlib.sha256(content).hexdigest())
            journal = (tmp / "archivia-move-v2.jsonl").read_text(encoding="utf-8")
            self.assertIn("HASH_VERIFICADO", journal)
            self.assertIn("REMOCAO_AUTORIZADA", journal)
            self.assertIn("CONCLUIDO", journal)
            self.assertEqual(list(target.parent.glob(".archivia-move-*.tmp")), [])

    def test_requires_distinct_explicit_approval(self):
        with temporary_test_directory() as tmp:
            source, target, database, plan = self._setup(tmp)
            for approval in ("", "CONFIRMO TESTE ARCHIVIA"):
                with self.subTest(approval=approval):
                    with self.assertRaisesRegex(ValueError, "Confirmação"):
                        move_verified_test_file(plan, database, approval=approval)
            self.assertTrue(source.exists())
            self.assertFalse(target.exists())

    def test_never_overwrites_occupied_destination(self):
        with temporary_test_directory() as tmp:
            source, target, database, plan = self._setup(tmp)
            target.write_bytes(b"ORIGINAL-DESTINO")
            with self.assertRaisesRegex(ValueError, "ocupado"):
                move_verified_test_file(plan, database, approval=_APPROVAL)
            self.assertEqual(target.read_bytes(), b"ORIGINAL-DESTINO")
            self.assertTrue(source.exists())

    def test_rejects_partial_and_tampered_plan(self):
        with temporary_test_directory() as tmp:
            source, target, database, plan = self._setup(tmp)
            for changes in ({"blocked": 1}, {"truncated": True}, {"selected": 2},
                            {"category": "codigo"}, {"summary_only": True}):
                with self.subTest(changes=changes):
                    with self.assertRaises(ValueError):
                        move_verified_test_file(
                            dict(plan, **changes), database, approval=_APPROVAL,
                        )
            self.assertTrue(source.exists())
            self.assertFalse(target.exists())

    def test_failed_copy_preserves_original(self):
        with temporary_test_directory() as tmp:
            source, target, database, plan = self._setup(tmp)
            from archivia import move_pipeline
            original_digest = move_pipeline._digest

            def interrupted_hash(path):
                if path.name.endswith(".tmp"):
                    raise ValueError("hash temporário falhou")
                return original_digest(path)

            with patch("archivia.move_pipeline._digest", side_effect=interrupted_hash):
                with self.assertRaisesRegex(ValueError, "hash temporário"):
                    move_verified_test_file(plan, database, approval=_APPROVAL)
            self.assertEqual(source.read_bytes(), b"ARCHIVIA-FIXTURE-MOVE-V2")
            self.assertFalse(target.exists())
            self.assertIn("INTERROMPIDO", (tmp / "archivia-move-v2.jsonl").read_text(encoding="utf-8"))

    def test_failed_unlink_leaves_source_and_verified_destination(self):
        with temporary_test_directory() as tmp:
            source, target, database, plan = self._setup(tmp)
            with patch("archivia.move_pipeline.os.unlink", side_effect=OSError("unlink negado")):
                with self.assertRaisesRegex(OSError, "unlink negado"):
                    move_verified_test_file(plan, database, approval=_APPROVAL)
            self.assertTrue(source.exists())
            self.assertEqual(target.read_bytes(), source.read_bytes())
            self.assertIn("INTERROMPIDO", (tmp / "archivia-move-v2.jsonl").read_text(encoding="utf-8"))

    def test_rejects_existing_operation_journal(self):
        with temporary_test_directory() as tmp:
            source, target, database, plan = self._setup(tmp)
            (tmp / "archivia-move-v2.jsonl").write_text("operação anterior\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Journal"):
                move_verified_test_file(plan, database, approval=_APPROVAL)
            self.assertTrue(source.exists())
            self.assertFalse(target.exists())

    def test_rejects_concurrent_lock(self):
        with temporary_test_directory() as tmp:
            source, target, database, plan = self._setup(tmp)
            lock = tmp / ".archivia-operation.lock"
            lock.mkdir()
            try:
                with self.assertRaisesRegex(ValueError, "lock presente"):
                    move_verified_test_file(plan, database, approval=_APPROVAL)
                self.assertTrue(source.exists())
                self.assertFalse(target.exists())
            finally:
                lock.rmdir()
