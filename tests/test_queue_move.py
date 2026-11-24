"""Fila de movimentos homologada somente em diretórios temporários."""
import unittest
from unittest.mock import patch

from support import temporary_test_directory
from archivia.agent import FolderCatalogSession, dispatch_tool
from archivia.move_executor import APPROVAL_PHRASE
from archivia.queue_move import move_queue_approved


class QueueMoveTests(unittest.TestCase):
    def setUp(self):
        self.context = temporary_test_directory()
        self.tmp = self.context.__enter__()
        self.source = self.tmp / "origem"
        self.dest = self.tmp / "destino"
        self.source.mkdir()
        self.dest.mkdir()
        for i in range(4):
            (self.source / f"img{i}.jpg").write_bytes(f"dado-{i}".encode())
        self.session = FolderCatalogSession(self.source)
        self.session.refresh()
        self.plan = dispatch_tool(
            "planejar_consolidacao_recursiva",
            {"categoria": "imagem", "destino": str(self.dest)},
            db_path=self.session._db, context_scan_id=self.session._scan_id,
        )

    def tearDown(self):
        self.session.close()
        self.context.__exit__(None, None, None)

    def run_queue(self, files=None, approval=APPROVAL_PHRASE, **kw):
        return move_queue_approved(
            self.plan, [f"img{i}.jpg" for i in range(4)] if files is None else files,
            db_path=self.session._db, scan_id=self.session._scan_id,
            approval=approval, **kw,
        )

    def test_moves_all_approved_without_touching_other_files(self):
        events = []
        result = self.run_queue(progress=events.append)
        self.assertEqual(result["moved"], 4)
        self.assertEqual(result["pending"], 0)
        self.assertFalse(result["stopped"])
        self.assertEqual(len(events), 4)
        for i in range(4):
            self.assertFalse((self.source / f"img{i}.jpg").exists())
            self.assertEqual((self.dest / f"img{i}.jpg").read_bytes(), f"dado-{i}".encode())

    def test_interrupt_between_files_preserves_remaining_origins(self):
        ticks = []
        result = self.run_queue(
            interrupted=lambda: len(ticks) >= 1,
            progress=ticks.append,
        )
        self.assertEqual(result["moved"], 1)
        self.assertEqual(result["pending"], 3)
        self.assertEqual(result["stopped_reason"], "interrompido_pelo_usuario")
        self.assertFalse((self.source / "img0.jpg").exists())
        for i in range(1, 4):
            self.assertTrue((self.source / f"img{i}.jpg").exists())

    def test_safe_collision_is_reported_and_remaining_files_are_moved(self):
        (self.dest / "img1.jpg").write_bytes(b"ocupado")
        result = self.run_queue()
        self.assertEqual(result["moved"], 3)
        self.assertEqual(result["processed"], 4)
        self.assertEqual(result["pending"], 0)
        self.assertFalse(result["stopped"])
        self.assertEqual(result["blocked"], 1)
        self.assertEqual(result["errors"], 0)
        self.assertEqual((self.dest / "img1.jpg").read_bytes(), b"ocupado")
        self.assertTrue((self.source / "img1.jpg").exists())
        self.assertFalse((self.source / "img2.jpg").exists())

    def test_reject_bad_authorization_or_unplanned_files(self):
        for selection in (["img0.jpg", "img0.jpg"], ["../img0.jpg"],
                          ["nao-existe.jpg"], []):
            with self.subTest(selection=selection), self.assertRaises(ValueError):
                self.run_queue(files=selection)
        with self.assertRaises(ValueError):
            self.run_queue(approval="")
        self.assertTrue((self.source / "img0.jpg").exists())

    def test_inconclusive_copy_stops_queue(self):
        fake = {
            "status": "copiado_origem_preservada",
            "sha256": "fake", "source": str(self.source / "img0.jpg"),
            "destination": str(self.dest / "img0.jpg"),
        }
        with patch("archivia.queue_move.move_one_approved", return_value=fake):
            report = self.run_queue()
        self.assertEqual(report["processed"], 1)
        self.assertTrue(report["stopped"])
        self.assertTrue(report["files_modified"])
        self.assertTrue((self.source / "img1.jpg").exists())


if __name__ == "__main__":
    unittest.main()
