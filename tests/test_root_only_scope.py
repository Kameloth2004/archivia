"""Escopo opcional: processar apenas arquivos órfãos da pasta selecionada."""
import unittest

from support import temporary_test_directory
from archivia.agent import FolderCatalogSession
from archivia.inventory import inventory
from archivia.move_executor import APPROVAL_PHRASE, move_one_approved
from archivia.queue_move import move_queue_approved


class RootOnlyScopeTests(unittest.TestCase):
    def setUp(self):
        self.context = temporary_test_directory()
        self.tmp = self.context.__enter__()
        self.root = self.tmp / "origem"
        self.dest = self.root / "Imagens"
        self.other = self.root / "outras"
        self.dest.mkdir(parents=True)
        self.other.mkdir()
        (self.root / "solta1.jpg").write_bytes(b"imagem 1")
        (self.root / "solta2.png").write_bytes(b"imagem 2")
        (self.root / "manual.txt").write_bytes(b"documento na raiz")
        (self.dest / "catalogada.jpg").write_bytes(b"imagem ja organizada")
        (self.other / "outra.jpg").write_bytes(b"imagem de subpasta")
        self.session = FolderCatalogSession(self.root)

    def tearDown(self):
        self.session.close()
        self.context.__exit__(None, None, None)

    def test_inventory_only_root_files_without_visiting_subdirectories(self):
        report = inventory(self.root, recursive=False)
        self.assertEqual({f["path"] for f in report["files"]},
                         {"solta1.jpg", "solta2.png", "manual.txt"})
        self.assertEqual(report["summary"]["indexed_files"], 3)
        self.assertEqual(report["summary"]["by_category"]["imagem"], 2)
        self.assertEqual(report["errors"], [])

    def test_root_only_analysis_and_plan_ignore_subfolders(self):
        analysis = self.session.analyze_source(recursive=False)
        self.assertFalse(analysis["recursive"])
        self.assertEqual(analysis["summary"]["indexed_files"], 3)
        plan = self.session.prepare_recursive_plan(
            self.dest, "imagem", recursive=False,
        )
        self.assertFalse(plan["recursive"])
        self.assertTrue(plan["complete"])
        self.assertEqual(plan["total_matches"], 2)
        self.assertEqual(plan["proposed"], 2)
        self.assertEqual(plan["blocked"], 0)
        self.assertEqual({a["file"] for a in plan["actions"]},
                         {"solta1.jpg", "solta2.png"})
        self.assertTrue((self.dest / "catalogada.jpg").exists())
        self.assertTrue((self.other / "outra.jpg").exists())

    def test_real_move_only_root_and_preserves_subfolder_contents(self):
        plan = self.session.prepare_recursive_plan(
            self.dest, "imagem", recursive=False,
        )
        report = move_queue_approved(
            plan, ["solta1.jpg", "solta2.png"],
            db_path=self.session._db, scan_id=self.session._scan_id,
            approval=APPROVAL_PHRASE,
        )
        self.assertEqual(report["moved"], 2)
        self.assertFalse((self.root / "solta1.jpg").exists())
        self.assertFalse((self.root / "solta2.png").exists())
        self.assertEqual((self.dest / "solta1.jpg").read_bytes(), b"imagem 1")
        self.assertEqual((self.dest / "solta2.png").read_bytes(), b"imagem 2")
        self.assertEqual((self.dest / "catalogada.jpg").read_bytes(),
                         b"imagem ja organizada")
        self.assertEqual((self.other / "outra.jpg").read_bytes(),
                         b"imagem de subpasta")
        self.assertEqual((self.root / "manual.txt").read_bytes(),
                         b"documento na raiz")

    def test_recursive_default_still_sees_nested_images(self):
        analysis = self.session.analyze_source()
        self.assertTrue(analysis["recursive"])
        self.assertEqual(analysis["summary"]["by_category"]["imagem"], 4)
        plan = self.session.prepare_recursive_plan(self.dest, "imagem")
        self.assertTrue(plan["recursive"])
        self.assertEqual(plan["total_matches"], 4)
        self.assertEqual(plan["blocked_by_reason"]["ja_no_destino"], 1)

    def test_executor_enforces_declared_root_only_scope(self):
        plan = self.session.prepare_recursive_plan(
            self.dest, "imagem", recursive=False,
        )
        with self.assertRaisesRegex(ValueError, "subpasta fora do escopo"):
            move_one_approved(
                plan, "outras/outra.jpg",
                db_path=self.session._db, scan_id=self.session._scan_id,
                approval=APPROVAL_PHRASE,
            )
        self.assertTrue((self.other / "outra.jpg").exists())

    def test_only_subfolders_results_in_empty_valid_plan(self):
        (self.root / "solta1.jpg").unlink()
        (self.root / "solta2.png").unlink()
        plan = self.session.prepare_recursive_plan(
            self.dest, "imagem", recursive=False,
        )
        self.assertEqual(plan["total_matches"], 0)
        self.assertEqual(plan["proposed"], 0)
        self.assertTrue(plan["complete"])
        self.assertEqual(plan["pending"], 0)
        self.assertTrue((self.dest / "catalogada.jpg").exists())


if __name__ == "__main__":
    unittest.main()
