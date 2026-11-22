"""TEST-ONLY: executor experimental, nunca utiliza pastas pessoais ou reais."""
import unittest
from unittest.mock import patch

from support import temporary_test_directory
from archivia.catalog import store_inventory
from archivia.inventory import inventory
from archivia.planner import propose_moves
from archivia.executor import execute_test_move, inspect_test_journal, rollback_interrupted_test_move


class ExecutorTests(unittest.TestCase):
    def _setup(self, tmp):
        source = tmp / "origem"
        dest = tmp / "destino"
        source.mkdir()
        dest.mkdir()
        image = source / "foto.jpg"
        image.write_bytes(b"TEST-ONLY")
        db = tmp / "catalogo.sqlite3"
        stored = store_inventory(inventory(source), db)
        proposal = propose_moves(dest, "imagem", db, scan_id=stored["scan_id"])
        return source, dest, image, db, proposal

    def test_moves_one_fixture_with_explicit_approval_and_journal(self):
        with temporary_test_directory() as tmp:
            source, dest, image, db, plan = self._setup(tmp)
            result = execute_test_move(
                plan, db, approval="CONFIRMO TESTE ARCHIVIA",
            )
            self.assertEqual(result["files_moved"], 1)
            self.assertTrue(result["test_only"])
            self.assertFalse(image.exists())
            self.assertEqual((dest / "foto.jpg").read_bytes(), b"TEST-ONLY")
            journal = tmp / "archivia-executor-journal.jsonl"
            self.assertTrue(journal.exists())
            data = journal.read_text(encoding="utf-8")
            self.assertIn("PREPARADO", data)
            self.assertIn("CONCLUIDO", data)

    def test_inspect_completed_move_without_recovery(self):
        with temporary_test_directory() as tmp:
            source, dest, image, db, plan = self._setup(tmp)
            execute_test_move(plan, db, approval="CONFIRMO TESTE ARCHIVIA")
            report = inspect_test_journal(tmp)
            self.assertEqual(report["status"], "concluido_registrado")
            self.assertEqual(report["last_event"], "CONCLUIDO")
            self.assertFalse(report["source_exists"])
            self.assertTrue(report["destination_exists"])
            self.assertFalse(report["automatic_recovery"])

    def test_inspect_interrupted_move_leaves_files_untouched(self):
        # TEST-ONLY: falha controlada depois do hardlink e antes de apagar origem.
        with temporary_test_directory() as tmp:
            source, dest, image, db, plan = self._setup(tmp)
            with patch("archivia.executor.os.unlink", side_effect=OSError("falha simulada")):
                with self.assertRaisesRegex(ValueError, "origem preservada"):
                    execute_test_move(
                        plan, db, approval="CONFIRMO TESTE ARCHIVIA",
                    )
            before = (image.read_bytes(), (dest / "foto.jpg").read_bytes())
            report = inspect_test_journal(tmp)
            self.assertEqual(report["status"], "revisao_manual_obrigatoria")
            self.assertEqual(report["last_event"], "INTERROMPIDO_REMOCAO")
            self.assertTrue(report["source_exists"])
            self.assertTrue(report["destination_exists"])
            self.assertFalse(report["automatic_recovery"])
            self.assertEqual(
                (image.read_bytes(), (dest / "foto.jpg").read_bytes()), before,
            )

    def test_recover_interrupted_fixture_with_verified_hardlink(self):
        with temporary_test_directory() as tmp:
            source, dest, image, db, plan = self._setup(tmp)
            with patch("archivia.executor.os.unlink", side_effect=OSError("falha simulada")):
                with self.assertRaisesRegex(ValueError, "origem preservada"):
                    execute_test_move(plan, db, approval="CONFIRMO TESTE ARCHIVIA")
            self.assertTrue(image.exists())
            self.assertTrue((dest / "foto.jpg").exists())
            result = rollback_interrupted_test_move(
                tmp, approval="CONFIRMO TESTE ARCHIVIA",
            )
            self.assertEqual(result["status"], "recuperado")
            self.assertEqual(image.read_bytes(), b"TEST-ONLY")
            self.assertFalse((dest / "foto.jpg").exists())
            self.assertEqual(
                inspect_test_journal(tmp)["status"], "recuperado_registrado",
            )
            with self.assertRaisesRegex(ValueError, "Estado do journal"):
                rollback_interrupted_test_move(
                    tmp, approval="CONFIRMO TESTE ARCHIVIA",
                )

    def test_recovery_rejects_wrong_identity_and_missing_confirmation(self):
        with temporary_test_directory() as tmp:
            source, dest, image, db, plan = self._setup(tmp)
            with patch("archivia.executor.os.unlink", side_effect=OSError("falha simulada")):
                with self.assertRaises(ValueError):
                    execute_test_move(plan, db, approval="CONFIRMO TESTE ARCHIVIA")
            with self.assertRaisesRegex(ValueError, "Confirmação"):
                rollback_interrupted_test_move(tmp, approval="")
            target = dest / "foto.jpg"
            target.unlink()
            target.write_bytes(b"ARQUIVO-DIFERENTE")
            with self.assertRaisesRegex(ValueError, "Identidade física"):
                rollback_interrupted_test_move(
                    tmp, approval="CONFIRMO TESTE ARCHIVIA",
                )
            self.assertEqual(image.read_bytes(), b"TEST-ONLY")
            self.assertEqual(target.read_bytes(), b"ARQUIVO-DIFERENTE")

    def test_recovery_rejects_completed_operation_and_does_not_delete(self):
        with temporary_test_directory() as tmp:
            source, dest, image, db, plan = self._setup(tmp)
            execute_test_move(plan, db, approval="CONFIRMO TESTE ARCHIVIA")
            with self.assertRaisesRegex(ValueError, "Estado do journal"):
                rollback_interrupted_test_move(
                    tmp, approval="CONFIRMO TESTE ARCHIVIA",
                )
            self.assertEqual((dest / "foto.jpg").read_bytes(), b"TEST-ONLY")

    def test_inspection_rejects_corrupt_journal_and_outside_runtime(self):
        with temporary_test_directory() as tmp:
            source, dest, image, db, plan = self._setup(tmp)
            with self.assertRaisesRegex(ValueError, "Journal"):
                inspect_test_journal(tmp)
            (tmp / "archivia-executor-journal.jsonl").write_text(
                "registro-invalido\\n", encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "incompleto|JSON inválido"):
                inspect_test_journal(tmp)
            with self.assertRaisesRegex(ValueError, "tests/.runtime"):
                inspect_test_journal(tmp.parent.parent)
            self.assertTrue(image.exists())
            self.assertEqual(list(dest.iterdir()), [])

    def test_move_refuses_concurrent_fixture_lock(self):
        with temporary_test_directory() as tmp:
            source, dest, image, db, plan = self._setup(tmp)
            lock = tmp / ".archivia-operation.lock"
            lock.mkdir()
            try:
                with self.assertRaisesRegex(ValueError, "lock presente"):
                    execute_test_move(
                        plan, db, approval="CONFIRMO TESTE ARCHIVIA",
                    )
                self.assertTrue(image.exists())
                self.assertFalse((dest / "foto.jpg").exists())
            finally:
                lock.rmdir()

    def test_recovery_refuses_concurrent_fixture_lock(self):
        with temporary_test_directory() as tmp:
            source, dest, image, db, plan = self._setup(tmp)
            with patch("archivia.executor.os.unlink", side_effect=OSError("falha simulada")):
                with self.assertRaises(ValueError):
                    execute_test_move(plan, db, approval="CONFIRMO TESTE ARCHIVIA")
            lock = tmp / ".archivia-operation.lock"
            lock.mkdir()
            try:
                with self.assertRaisesRegex(ValueError, "lock presente"):
                    rollback_interrupted_test_move(
                        tmp, approval="CONFIRMO TESTE ARCHIVIA",
                    )
                self.assertTrue(image.exists())
                self.assertTrue((dest / "foto.jpg").exists())
            finally:
                lock.rmdir()

    def test_move_rechecks_source_after_destination_logged(self):
        with temporary_test_directory() as tmp:
            source, dest, image, db, plan = self._setup(tmp)
            from archivia import executor
            real_record = executor._record

            def mutate_after_record(journal, event, original, target):
                real_record(journal, event, original, target)
                if event == "DESTINO_CRIADO":
                    image.write_bytes(b"MODIFICADO-DURANTE-O-JOURNAL")

            with patch("archivia.executor._record", side_effect=mutate_after_record):
                with self.assertRaisesRegex(ValueError, "revisão manual"):
                    execute_test_move(
                        plan, db, approval="CONFIRMO TESTE ARCHIVIA",
                    )
            self.assertTrue(image.exists())
            self.assertTrue((dest / "foto.jpg").exists())
            self.assertEqual(
                inspect_test_journal(tmp)["last_event"],
                "INTERROMPIDO_VERIFICACAO",
            )

    def test_rejects_missing_approval_and_preserves_fixture(self):
        with temporary_test_directory() as tmp:
            source, dest, image, db, plan = self._setup(tmp)
            with self.assertRaisesRegex(ValueError, "Confirmação"):
                execute_test_move(plan, db, approval="")
            self.assertTrue(image.exists())
            self.assertFalse((dest / "foto.jpg").exists())

    def test_rejects_occupied_target_and_changed_source(self):
        with temporary_test_directory() as tmp:
            source, dest, image, db, plan = self._setup(tmp)
            (dest / "foto.jpg").write_bytes(b"ORIGINAL-DESTINO")
            with self.assertRaises(ValueError):
                execute_test_move(plan, db, approval="CONFIRMO TESTE ARCHIVIA")
            self.assertTrue(image.exists())
            self.assertEqual((dest / "foto.jpg").read_bytes(), b"ORIGINAL-DESTINO")
            (dest / "foto.jpg").unlink()
            image.write_bytes(b"MODIFICADO")
            with self.assertRaisesRegex(ValueError, "Plano não corresponde"):
                execute_test_move(plan, db, approval="CONFIRMO TESTE ARCHIVIA")
            self.assertTrue(image.exists())
            self.assertFalse((dest / "foto.jpg").exists())

    def test_rejects_tampered_and_partial_plans(self):
        with temporary_test_directory() as tmp:
            source, dest, image, db, plan = self._setup(tmp)
            for changes in (
                {"truncated": True}, {"summary_only": True},
                {"blocked": 1}, {"selected": 2}, {"total_matches": 2},
                {"category": "codigo"},
            ):
                with self.subTest(changes=changes):
                    with self.assertRaises(ValueError):
                        execute_test_move(
                            dict(plan, **changes), db,
                            approval="CONFIRMO TESTE ARCHIVIA",
                        )
            self.assertTrue(image.exists())
            self.assertFalse((dest / "foto.jpg").exists())

    def test_rejects_destination_outside_test_runtime(self):
        with temporary_test_directory() as tmp:
            source, dest, image, db, plan = self._setup(tmp)
            altered = dict(plan, actions=[dict(plan["actions"][0],
                destination=str(tmp.parent.parent / "nao-permitido.jpg"))])
            with self.assertRaisesRegex(ValueError, "tests/.runtime"):
                execute_test_move(altered, db, approval="CONFIRMO TESTE ARCHIVIA")
            self.assertTrue(image.exists())
