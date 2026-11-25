"""Regressão V2: nomes-base ambíguos não podem interromper a fila segura."""
import unittest

from support import temporary_test_directory
from archivia.agent import FolderCatalogSession
from archivia.move_executor import APPROVAL_PHRASE
from archivia.queue_move import move_queue_approved
from archivia.batch_move import move_batch_approved


class AmbiguousBasenameQueueTests(unittest.TestCase):
    def setUp(self):
        self.context = temporary_test_directory()
        self.tmp = self.context.__enter__()
        self.root = self.tmp / "origem"
        self.dest = self.tmp / "destino"
        self.dest.mkdir()
        (self.root / "a").mkdir(parents=True)
        (self.root / "b").mkdir()
        (self.root / "c").mkdir()
        (self.root / "a" / "README.md").write_bytes(b"README do A")
        (self.root / "b" / "README.md").write_bytes(b"README do B")
        (self.root / "c" / "README.MD").write_bytes(b"README do C")
        (self.root / "a" / "primeiro.pdf").write_bytes(b"PDF primeiro")
        (self.root / "b" / "ultimo.pdf").write_bytes(b"PDF ultimo")
        self.session = FolderCatalogSession(self.root)

    def tearDown(self):
        self.session.close()
        self.context.__exit__(None, None, None)

    def test_plan_blocks_all_ambiguous_sources_and_moves_remaining(self):
        plan = self.session.prepare_recursive_plan(self.dest, "documento")
        ambiguous = [a for a in plan["actions"]
                     if a["file"].casefold().endswith("readme.md")]
        self.assertEqual(len(ambiguous), 3)
        self.assertTrue(all(a["status"] == "bloqueado" for a in ambiguous))
        self.assertEqual(plan["blocked_by_reason"]["nome_repetido_entre_subpastas"], 3)
        self.assertEqual(plan["proposed"], 2)
        files = [a["file"] for a in plan["actions"] if a["status"] == "proposto"]
        report = move_queue_approved(
            plan, files, db_path=self.session._db,
            scan_id=self.session._scan_id, approval=APPROVAL_PHRASE,
        )
        self.assertEqual(report["moved"], 2)
        self.assertEqual(report["errors"], 0)
        self.assertEqual(report["pending"], 0)
        self.assertFalse(report["stopped"])
        self.assertEqual((self.dest / "primeiro.pdf").read_bytes(), b"PDF primeiro")
        self.assertEqual((self.dest / "ultimo.pdf").read_bytes(), b"PDF ultimo")
        self.assertFalse((self.dest / "README.md").exists())
        self.assertTrue((self.root / "a" / "README.md").exists())
        self.assertTrue((self.root / "b" / "README.md").exists())
        self.assertTrue((self.root / "c" / "README.MD").exists())

    def test_legacy_plan_ambiguous_item_is_safe_block_not_fatal_error(self):
        # Representa a prévia anterior da V2, em que a primeira ocorrência
        # era proposta e somente as posteriores eram marcadas bloqueadas.
        plan = self.session.prepare_recursive_plan(self.dest, "documento")
        first = next(a for a in plan["actions"] if a["file"] == "a/README.md")
        first["status"] = "proposto"
        first["reason"] = None
        files = ["a/primeiro.pdf", "a/README.md", "b/ultimo.pdf"]
        report = move_queue_approved(
            plan, files, db_path=self.session._db,
            scan_id=self.session._scan_id, approval=APPROVAL_PHRASE,
        )
        self.assertEqual(report["moved"], 2)
        self.assertEqual(report["blocked"], 1)
        self.assertEqual(report["errors"], 0)
        self.assertEqual(report["processed"], 3)
        self.assertEqual(report["pending"], 0)
        self.assertFalse(report["stopped"])
        self.assertEqual(report["results"][1]["status"], "bloqueado")
        self.assertIn("ambíguo", report["results"][1]["detail"])
        self.assertTrue((self.root / "a" / "README.md").exists())
        self.assertTrue((self.root / "b" / "README.md").exists())

    def test_batch_also_continues_after_safe_ambiguity(self):
        plan = self.session.prepare_recursive_plan(self.dest, "documento")
        first = next(a for a in plan["actions"] if a["file"] == "a/README.md")
        first["status"] = "proposto"
        first["reason"] = None
        report = move_batch_approved(
            plan, ["a/README.md", "b/ultimo.pdf"],
            db_path=self.session._db, scan_id=self.session._scan_id,
            approval=APPROVAL_PHRASE,
        )
        self.assertEqual(report["moved"], 1)
        self.assertEqual(report["blocked"], 1)
        self.assertEqual(report["errors"], 0)
        self.assertFalse(report["stopped"])
        self.assertTrue((self.root / "a" / "README.md").exists())
        self.assertEqual((self.dest / "ultimo.pdf").read_bytes(), b"PDF ultimo")


if __name__ == "__main__":
    unittest.main()
