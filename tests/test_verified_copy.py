"""TEST-ONLY: cópia verificada de um arquivo fictício, nunca arquivos pessoais."""
import unittest
from unittest.mock import patch

from support import temporary_test_directory
from archivia.catalog import store_inventory
from archivia.inventory import inventory
from archivia.planner import propose_moves
from archivia.verified_copy import copy_verified_test_file


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
