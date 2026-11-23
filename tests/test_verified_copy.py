"""TEST-ONLY: cópia verificada de um arquivo fictício, nunca arquivos pessoais."""
import unittest
from unittest.mock import patch

from support import temporary_test_directory
from archivia.catalog import store_inventory
from archivia.inventory import inventory
from archivia.planner import propose_moves
from archivia.verified_copy import copy_verified_test_file, inspect_verified_copy_test, reconcile_published_test_copy


class VerifiedCopyTests(unittest.TestCase):
    def _setup(self, tmp):
        source = tmp / "origem"
        destination = tmp / "destino"
        source.mkdir()
        destination.mkdir()
        image = source / "foto.jpg"
        image.write_bytes(b"ARCHIVIA-FIXTURE-VERIFICADA")
        db = tmp / "catalogo.sqlite3"
        saved = store_inventory(inventory(source), db)
        plan = propose_moves(destination, "imagem", db_path=db, scan_id=saved["scan_id"])
        return image, destination / "foto.jpg", db, plan

    def test_copy_preserves_source_and_checks_sha256(self):
        import hashlib
        with temporary_test_directory() as tmp:
            source, destination, db, plan = self._setup(tmp)
            result = copy_verified_test_file(
                plan, db, approval="CONFIRMO TESTE ARCHIVIA",
            )
            self.assertEqual(result["status"], "copiado_verificado")
            self.assertEqual(source.read_bytes(), destination.read_bytes())
            self.assertEqual(result["sha256"], hashlib.sha256(source.read_bytes()).hexdigest())
            self.assertTrue(result["source_preserved"])
            self.assertTrue((tmp / "archivia-copy-journal.jsonl").is_file())
            journal = (tmp / "archivia-copy-journal.jsonl").read_text(encoding="utf-8")
            self.assertIn("HASH_VERIFICADO", journal)
            self.assertIn("PUBLICADO", journal)
            self.assertEqual(list(destination.parent.glob(".archivia-copy-*.tmp")), [])

    def test_inspect_published_copy_is_read_only(self):
        with temporary_test_directory() as tmp:
            source, destination, db, plan = self._setup(tmp)
            copy_verified_test_file(plan, db, approval="CONFIRMO TESTE ARCHIVIA")
            before = (source.read_bytes(), destination.read_bytes())
            report = inspect_verified_copy_test(tmp)
            self.assertEqual(report["status"], "publicacao_registrada_inspecionada")
            self.assertEqual(report["last_event"], "PUBLICADO")
            self.assertTrue(report["source_exists"])
            self.assertTrue(report["destination_exists"])
            self.assertTrue(report["current_sha256_equal"])
            self.assertEqual(report["temporary_count"], 0)
            self.assertTrue(report["read_only"])
            self.assertFalse(report["automatic_recovery"])
            self.assertEqual(
                (source.read_bytes(), destination.read_bytes()), before,
            )

    def test_inspect_failure_after_publication_preserves_both_files(self):
        from archivia import verified_copy
        with temporary_test_directory() as tmp:
            source, destination, db, plan = self._setup(tmp)
            original_journal = verified_copy._journal

            def fail_publication_log(journal, event, src, dst):
                if event == "PUBLICADO":
                    raise OSError("falha de journal pós-publicação")
                return original_journal(journal, event, src, dst)

            with patch("archivia.verified_copy._journal", side_effect=fail_publication_log):
                with self.assertRaisesRegex(OSError, "pós-publicação"):
                    copy_verified_test_file(
                        plan, db, approval="CONFIRMO TESTE ARCHIVIA",
                    )
            report = inspect_verified_copy_test(tmp)
            self.assertEqual(report["status"], "interrompido_revisao_manual")
            self.assertEqual(report["last_event"], "INTERROMPIDO")
            self.assertTrue(report["source_exists"])
            self.assertTrue(report["destination_exists"])
            self.assertTrue(report["current_sha256_equal"])
            self.assertEqual(source.read_bytes(), destination.read_bytes())

    def test_inspect_partial_copy_and_leftover_temp_without_cleanup(self):
        from archivia import verified_copy
        with temporary_test_directory() as tmp:
            source, destination, db, plan = self._setup(tmp)
            with patch("archivia.verified_copy._fingerprint",
                       side_effect=OSError("falha antes da publicação")):
                with self.assertRaisesRegex(OSError, "falha antes"):
                    copy_verified_test_file(
                        plan, db, approval="CONFIRMO TESTE ARCHIVIA",
                    )
            temp = destination.parent / ".archivia-copy-teste.tmp"
            temp.write_bytes(b"TEMPORARIO-NAO-APAGAR")
            report = inspect_verified_copy_test(tmp)
            self.assertEqual(report["status"], "interrompido_revisao_manual")
            self.assertFalse(report["destination_exists"])
            self.assertEqual(report["temporary_count"], 1)
            self.assertEqual(report["temporary_files"], [str(temp)])
            self.assertEqual(temp.read_bytes(), b"TEMPORARIO-NAO-APAGAR")
            self.assertTrue(source.exists())

    def test_inspect_refuses_invalid_journal_and_outside_runtime(self):
        with temporary_test_directory() as tmp:
            source, destination, db, plan = self._setup(tmp)
            with self.assertRaisesRegex(ValueError, "Journal"):
                inspect_verified_copy_test(tmp)
            (tmp / "archivia-copy-journal.jsonl").write_text(
                "isto-nao-e-json\\n", encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "inválido|incompleta"):
                inspect_verified_copy_test(tmp)
            with self.assertRaisesRegex(ValueError, "tests/.runtime|restrita"):
                inspect_verified_copy_test(tmp.parent.parent)
            self.assertTrue(source.exists())
            self.assertFalse(destination.exists())

    def _interrupted_published_fixture(self, plan, db):
        from archivia import verified_copy
        original_journal = verified_copy._journal

        def fail_published(journal, event, src, dst):
            if event == "PUBLICADO":
                raise OSError("falha pós-publicação simulada")
            return original_journal(journal, event, src, dst)

        with patch("archivia.verified_copy._journal", side_effect=fail_published):
            with self.assertRaisesRegex(OSError, "pós-publicação"):
                copy_verified_test_file(
                    plan, db, approval="CONFIRMO TESTE ARCHIVIA",
                )

    def test_reconcile_published_interrupted_journal_without_deleting(self):
        with temporary_test_directory() as tmp:
            source, destination, db, plan = self._setup(tmp)
            self._interrupted_published_fixture(plan, db)
            before = (source.read_bytes(), destination.read_bytes())
            result = reconcile_published_test_copy(
                tmp, approval="CONFIRMO TESTE ARCHIVIA",
            )
            self.assertEqual(result["status"], "copia_reconciliada_registrada")
            self.assertTrue(result["source_preserved"])
            self.assertTrue(result["destination_preserved"])
            self.assertFalse(result["automatic_cleanup"])
            self.assertEqual(
                (source.read_bytes(), destination.read_bytes()), before,
            )
            self.assertEqual(
                inspect_verified_copy_test(tmp)["status"],
                "copia_reconciliada_registrada",
            )
            with self.assertRaisesRegex(ValueError, "Journal não permite"):
                reconcile_published_test_copy(
                    tmp, approval="CONFIRMO TESTE ARCHIVIA",
                )

    def test_reconcile_refuses_changed_destination_and_no_approval(self):
        with temporary_test_directory() as tmp:
            source, destination, db, plan = self._setup(tmp)
            self._interrupted_published_fixture(plan, db)
            with self.assertRaisesRegex(ValueError, "Confirmação"):
                reconcile_published_test_copy(tmp, approval="")
            destination.write_bytes(b"ALTERADO")
            with self.assertRaisesRegex(ValueError, "revisão manual"):
                reconcile_published_test_copy(
                    tmp, approval="CONFIRMO TESTE ARCHIVIA",
                )
            self.assertEqual(destination.read_bytes(), b"ALTERADO")
            self.assertTrue(source.exists())

    def test_reconcile_refuses_leftover_temporary_without_removing_it(self):
        with temporary_test_directory() as tmp:
            source, destination, db, plan = self._setup(tmp)
            self._interrupted_published_fixture(plan, db)
            temporary = destination.parent / ".archivia-copy-sobra.tmp"
            temporary.write_bytes(b"NAO-APAGAR")
            with self.assertRaisesRegex(ValueError, "temporários"):
                reconcile_published_test_copy(
                    tmp, approval="CONFIRMO TESTE ARCHIVIA",
                )
            self.assertEqual(temporary.read_bytes(), b"NAO-APAGAR")
            self.assertTrue(source.exists())
            self.assertTrue(destination.exists())

    def test_reconcile_refuses_prepublication_interruption(self):
        with temporary_test_directory() as tmp:
            source, destination, db, plan = self._setup(tmp)
            with patch("archivia.verified_copy._fingerprint",
                       side_effect=OSError("falha antes de publicar")):
                with self.assertRaisesRegex(OSError, "antes de publicar"):
                    copy_verified_test_file(
                        plan, db, approval="CONFIRMO TESTE ARCHIVIA",
                    )
            with self.assertRaisesRegex(ValueError, "Journal não permite"):
                reconcile_published_test_copy(
                    tmp, approval="CONFIRMO TESTE ARCHIVIA",
                )
            self.assertTrue(source.exists())
            self.assertFalse(destination.exists())

    def test_copy_denies_without_explicit_approval(self):
        with temporary_test_directory() as tmp:
            source, destination, db, plan = self._setup(tmp)
            with self.assertRaisesRegex(ValueError, "Confirmação"):
                copy_verified_test_file(plan, db, approval="")
            self.assertTrue(source.exists())
            self.assertFalse(destination.exists())

    def test_copy_refuses_existing_destination(self):
        with temporary_test_directory() as tmp:
            source, destination, db, plan = self._setup(tmp)
            destination.write_bytes(b"NAO-SOBRESCREVER")
            with self.assertRaisesRegex(ValueError, "ocupado"):
                copy_verified_test_file(plan, db, approval="CONFIRMO TESTE ARCHIVIA")
            self.assertEqual(destination.read_bytes(), b"NAO-SOBRESCREVER")
            self.assertTrue(source.exists())

    def test_copy_refuses_partial_or_tampered_plan(self):
        with temporary_test_directory() as tmp:
            source, destination, db, plan = self._setup(tmp)
            for modifications in ({"truncated": True}, {"total_matches": 2},
                                  {"blocked": 1}, {"category": "codigo"}):
                with self.subTest(modifications=modifications):
                    with self.assertRaises(ValueError):
                        copy_verified_test_file(
                            dict(plan, **modifications), db,
                            approval="CONFIRMO TESTE ARCHIVIA",
                        )
            self.assertTrue(source.exists())
            self.assertFalse(destination.exists())

    def test_copy_rejects_lock_from_concurrent_fixture(self):
        with temporary_test_directory() as tmp:
            source, destination, db, plan = self._setup(tmp)
            lock = tmp / ".archivia-operation.lock"
            lock.mkdir()
            try:
                with self.assertRaisesRegex(ValueError, "lock presente"):
                    copy_verified_test_file(
                        plan, db, approval="CONFIRMO TESTE ARCHIVIA",
                    )
                self.assertTrue(source.exists())
                self.assertFalse(destination.exists())
            finally:
                lock.rmdir()

    def test_copy_failure_preserves_original_and_destination(self):
        with temporary_test_directory() as tmp:
            source, destination, db, plan = self._setup(tmp)
            with patch("archivia.verified_copy._fingerprint",
                       side_effect=OSError("falha simulada na cópia")):
                with self.assertRaisesRegex(OSError, "falha simulada"):
                    copy_verified_test_file(
                        plan, db, approval="CONFIRMO TESTE ARCHIVIA",
                    )
            self.assertTrue(source.exists())
            self.assertFalse(destination.exists())
            self.assertEqual(list(destination.parent.glob(".archivia-copy-*.tmp")), [])
            self.assertIn(
                "INTERROMPIDO",
                (tmp / "archivia-copy-journal.jsonl").read_text(encoding="utf-8"),
            )

    def test_copy_refuses_reusing_journal(self):
        with temporary_test_directory() as tmp:
            source, destination, db, plan = self._setup(tmp)
            (tmp / "archivia-copy-journal.jsonl").write_text(
                "teste-anterior\n", encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "journal"):
                copy_verified_test_file(
                    plan, db, approval="CONFIRMO TESTE ARCHIVIA",
                )
            self.assertTrue(source.exists())
            self.assertFalse(destination.exists())
