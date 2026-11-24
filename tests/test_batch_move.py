"""Testes do lote supervisionado usando somente diretórios temporários."""
import unittest
from unittest.mock import patch

from support import temporary_test_directory
from archivia.agent import FolderCatalogSession, dispatch_tool
from archivia.batch_move import move_batch_approved, MAX_BATCH_FILES
from archivia.move_executor import APPROVAL_PHRASE


class SupervisedBatchTests(unittest.TestCase):
    def setUp(self):
        self.folder = temporary_test_directory()
        self.tmp = self.folder.__enter__()
        self.origin = self.tmp / "origem"
        self.dest = self.tmp / "destino"
        self.origin.mkdir()
        self.dest.mkdir()
        for index in range(3):
            (self.origin / f"foto{index}.jpg").write_bytes(f"imagem{index}".encode())
        self.session = FolderCatalogSession(self.origin)
        self.session.refresh()
        self.plan = self.plan_now()

    def tearDown(self):
        self.session.close()
        self.folder.__exit__(None, None, None)

    def plan_now(self):
        return dispatch_tool(
            "planejar_consolidacao_recursiva",
            {"categoria": "imagem", "destino": str(self.dest)},
            db_path=self.session._db,
            context_scan_id=self.session._scan_id,
        )

    def run_batch(self, files, approval=APPROVAL_PHRASE, plan=None, progress=None):
        return move_batch_approved(
            self.plan if plan is None else plan, files,
            db_path=self.session._db, scan_id=self.session._scan_id,
            approval=approval, progress=progress,
        )

    def test_batch_moves_all_three_and_reports_progress(self):
        events = []
        names = [f"foto{i}.jpg" for i in range(3)]
        result = self.run_batch(names, progress=events.append)
        self.assertEqual(result["moved"], 3)
        self.assertEqual(result["processed"], 3)
        self.assertEqual(result["pending"], 0)
        self.assertFalse(result["stopped"])
        self.assertEqual([e["processed"] for e in events], [1, 2, 3])
        for index in range(3):
            name = f"foto{index}.jpg"
            self.assertFalse((self.origin / name).exists())
            self.assertEqual((self.dest / name).read_bytes(), f"imagem{index}".encode())

    def test_batch_skips_collision_and_moves_remaining_files(self):
        (self.dest / "foto1.jpg").write_bytes(b"nao sobrescrever")
        result = self.run_batch(["foto0.jpg", "foto1.jpg", "foto2.jpg"])
        self.assertEqual(result["moved"], 2)
        self.assertEqual(result["processed"], 3)
        self.assertEqual(result["pending"], 0)
        self.assertFalse(result["stopped"])
        self.assertEqual(result["blocked"], 1)
        self.assertEqual(result["results"][1]["status"], "bloqueado")
        self.assertFalse((self.origin / "foto0.jpg").exists())
        self.assertTrue((self.origin / "foto1.jpg").exists())
        self.assertFalse((self.origin / "foto2.jpg").exists())
        self.assertEqual((self.dest / "foto1.jpg").read_bytes(), b"nao sobrescrever")

    def test_missing_approval_rejects_before_writing(self):
        with self.assertRaises(ValueError):
            self.run_batch(["foto0.jpg"], approval="")
        self.assertFalse((self.dest / "foto0.jpg").exists())

    def test_reject_unplanned_or_duplicate_names(self):
        for selection in ([], ["foto0.jpg", "foto0.jpg"],
                          ["../foto0.jpg"], ["foto0.jpg", "naoexiste.jpg"],
                          ["foto0.jpg"] * (MAX_BATCH_FILES + 1)):
            with self.subTest(selection=selection), self.assertRaises(ValueError):
                self.run_batch(selection)
        self.assertTrue((self.origin / "foto0.jpg").exists())

    def test_reject_incomplete_or_different_snapshot(self):
        partial = self.plan_now()
        partial["complete"] = False
        partial["pending"] = 1
        with self.assertRaises(ValueError):
            self.run_batch(["foto0.jpg"], plan=partial)
        other = self.plan_now()
        other["scan_id"] += 1
        with self.assertRaises(ValueError):
            self.run_batch(["foto0.jpg"], plan=other)

    def test_copy_preserved_stops_batch_without_removing_other_files(self):
        fake = {"status": "copiado_origem_preservada",
                "source": str(self.origin / "foto0.jpg"),
                "destination": str(self.dest / "foto0.jpg"),
                "sha256": "abc"}
        with patch("archivia.batch_move.move_one_approved", return_value=fake):
            result = self.run_batch(["foto0.jpg", "foto1.jpg"])
        self.assertTrue(result["stopped"])
        self.assertEqual(result["moved"], 0)
        self.assertEqual(result["pending"], 1)
        self.assertTrue(result["files_modified"])
        self.assertTrue((self.origin / "foto1.jpg").exists())


if __name__ == "__main__":
    unittest.main()
