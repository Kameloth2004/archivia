"""Testes isolados do executor real: exclusivamente tests/.runtime."""
import unittest
from unittest.mock import patch

from support import temporary_test_directory
from archivia.agent import FolderCatalogSession, dispatch_tool, TOOLS
from archivia.move_executor import move_one_approved, APPROVAL_PHRASE


class ApprovedMoveTests(unittest.TestCase):
    def setUp(self):
        self.context = temporary_test_directory()
        self.tmp = self.context.__enter__()
        self.origin = self.tmp / "origem"
        self.dest = self.tmp / "destino"
        self.origin.mkdir()
        self.dest.mkdir()
        self.source = self.origin / "foto.jpg"
        self.target = self.dest / "foto.jpg"
        self.source.write_bytes(b"conteudo-validado-por-hash")
        self.session = FolderCatalogSession(self.origin)
        self.session.refresh()
        self.plan = self.new_plan()

    def tearDown(self):
        self.session.close()
        self.context.__exit__(None, None, None)

    def new_plan(self):
        return dispatch_tool(
            "planejar_consolidacao_recursiva",
            {"categoria": "imagem", "destino": str(self.dest)},
            db_path=self.session._db,
            context_scan_id=self.session._scan_id,
        )

    def move(self, approval=APPROVAL_PHRASE, name="foto.jpg", plan=None):
        return move_one_approved(
            self.plan if plan is None else plan, name,
            db_path=self.session._db,
            scan_id=self.session._scan_id,
            approval=approval,
        )

    def test_real_move_requires_approval_and_checks_hash(self):
        with self.assertRaises(ValueError):
            self.move(approval="")
        self.assertTrue(self.source.exists())
        self.assertFalse(self.target.exists())
        outcome = self.move()
        self.assertEqual(outcome["status"], "movido")
        self.assertFalse(self.source.exists())
        self.assertEqual(self.target.read_bytes(), b"conteudo-validado-por-hash")
        self.assertEqual(outcome["bytes"], len(b"conteudo-validado-por-hash"))
        self.assertFalse(list(self.dest.glob(".archivia-stage-*")))

    def test_destination_collision_never_overwrites(self):
        self.target.write_bytes(b"NAO-SOBRESCREVER")
        with self.assertRaises(ValueError):
            self.move()
        self.assertEqual(self.target.read_bytes(), b"NAO-SOBRESCREVER")
        self.assertTrue(self.source.exists())

    def test_modified_source_keeps_original_and_no_target(self):
        self.source.write_bytes(b"alterado desde inventario")
        with self.assertRaises(ValueError):
            self.move()
        self.assertFalse(self.target.exists())
        self.assertTrue(self.source.exists())

    def test_reject_blocked_and_ambiguous_files(self):
        sub = self.origin / "sub"
        sub.mkdir()
        (sub / "foto.jpg").write_bytes(b"outro")
        self.session.refresh()
        plan = self.new_plan()
        with self.assertRaises(ValueError):
            self.move(plan=plan)
        self.assertTrue(self.source.exists())
        self.assertFalse(self.target.exists())

    def test_wrong_snapshot_or_unknown_file_rejected(self):
        with self.assertRaises(ValueError):
            self.move(name="nao-existe.jpg")
        self.plan["scan_id"] += 1
        with self.assertRaises(ValueError):
            self.move()
        self.assertTrue(self.source.exists())

    def test_simulation_tool_registry_does_not_expose_executor(self):
        names = {t["function"]["name"] for t in TOOLS}
        self.assertNotIn("move_one_approved", names)
        self.assertNotIn("mover_arquivo", names)
        with self.assertRaises(ValueError):
            dispatch_tool("move_one_approved", {"arquivo": "foto.jpg"},
                          db_path=self.session._db,
                          context_scan_id=self.session._scan_id)


if __name__ == "__main__":
    unittest.main()
