"""Homologação da organização de mídias da pasta principal em subpastas internas."""
import unittest

from support import temporary_test_directory
from archivia.agent import FolderCatalogSession
from archivia.move_executor import APPROVAL_PHRASE, move_one_approved, MoveSkippedError
from archivia.queue_move import move_queue_approved


class NestedDestinationTests(unittest.TestCase):
    def setUp(self):
        self.context = temporary_test_directory()
        self.tmp = self.context.__enter__()
        self.root = self.tmp / "origem"
        self.dest = self.root / "Imagens"
        self.deep_dest = self.dest / "Album"
        self.deep_dest.mkdir(parents=True)
        (self.root / "nova.jpg").write_bytes(b"nova imagem")
        (self.root / "segunda.png").write_bytes(b"segunda imagem")
        (self.dest / "existente.jpg").write_bytes(b"ja organizado")
        (self.deep_dest / "antiga.jpg").write_bytes(b"ja organizado em subpasta")
        self.session = FolderCatalogSession(self.root)
        self.session.refresh()

    def tearDown(self):
        self.session.close()
        self.context.__exit__(None, None, None)

    def test_moves_from_root_into_internal_directory(self):
        plan = self.session.prepare_recursive_plan(self.dest, "imagem")
        self.assertTrue(plan["complete"])
        self.assertEqual(plan["proposed"], 2)
        self.assertEqual(plan["blocked_by_reason"].get("ja_no_destino"), 2)
        self.assertEqual(plan["pending"], 0)
        self.assertFalse(plan["files_modified"])
        result = move_queue_approved(
            plan, ["nova.jpg", "segunda.png"],
            db_path=self.session._db, scan_id=self.session._scan_id,
            approval=APPROVAL_PHRASE,
        )
        self.assertEqual(result["moved"], 2)
        self.assertEqual(result["errors"], 0)
        self.assertEqual((self.dest / "nova.jpg").read_bytes(), b"nova imagem")
        self.assertEqual((self.dest / "segunda.png").read_bytes(), b"segunda imagem")
        self.assertFalse((self.root / "nova.jpg").exists())
        self.assertFalse((self.root / "segunda.png").exists())
        self.assertEqual((self.dest / "existente.jpg").read_bytes(), b"ja organizado")
        self.assertEqual((self.deep_dest / "antiga.jpg").read_bytes(),
                         b"ja organizado em subpasta")

    def test_never_moves_items_already_within_destination(self):
        plan = self.session.prepare_recursive_plan(self.dest, "imagem")
        for file in ("Imagens/existente.jpg", "Imagens/Album/antiga.jpg"):
            with self.subTest(file=file), self.assertRaises(ValueError):
                move_one_approved(
                    plan, file, db_path=self.session._db, scan_id=self.session._scan_id,
                    approval=APPROVAL_PHRASE,
                )
        # Mesmo se alguém alterar manualmente a ação, o executor revalida.
        action = next(a for a in plan["actions"]
                      if a["file"] == "Imagens/existente.jpg")
        action["status"] = "proposto"
        action["reason"] = None
        with self.assertRaises(MoveSkippedError):
            move_one_approved(
                plan, "Imagens/existente.jpg",
                db_path=self.session._db, scan_id=self.session._scan_id,
                approval=APPROVAL_PHRASE,
            )
        self.assertEqual((self.dest / "existente.jpg").read_bytes(), b"ja organizado")

    def test_existing_name_collision_is_not_overwritten(self):
        (self.dest / "nova.jpg").write_bytes(b"nao sobrescrever")
        plan = self.session.prepare_recursive_plan(self.dest, "imagem")
        self.assertEqual(plan["blocked_by_reason"].get("destino_ja_existe"), 1)
        self.assertTrue((self.root / "nova.jpg").exists())
        self.assertEqual((self.dest / "nova.jpg").read_bytes(), b"nao sobrescrever")

    def test_identical_root_destination_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "mesma pasta"):
            self.session.prepare_recursive_plan(self.root, "imagem")


if __name__ == "__main__":
    unittest.main()
