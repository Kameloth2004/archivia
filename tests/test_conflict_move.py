"""Fluxo real de conflitos: nomes iguais, bytes diferentes e preservação."""
import unittest

from support import temporary_test_directory
from archivia.agent import FolderCatalogSession, dispatch_tool
from archivia.move_executor import (
    APPROVAL_PHRASE, move_one_approved, preview_conflict_move,
)


class ConflictMoveTests(unittest.TestCase):
    def setUp(self):
        self.context = temporary_test_directory()
        self.tmp = self.context.__enter__()
        self.origin = self.tmp / "origem"
        self.dest = self.tmp / "destino"
        self.origin.mkdir()
        self.dest.mkdir()
        self.source = self.origin / "teste.jpg"
        self.existing = self.dest / "teste.jpg"
        self.source.write_bytes(b"imagem-origem-distinta")
        self.existing.write_bytes(b"imagem-ja-existente")
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
            db_path=self.session._db, context_scan_id=self.session._scan_id,
        )

    def preview(self):
        return preview_conflict_move(
            self.plan, "teste.jpg",
            db_path=self.session._db, scan_id=self.session._scan_id,
        )

    def move(self, name=None, approval=APPROVAL_PHRASE):
        return move_one_approved(
            self.plan, "teste.jpg", db_path=self.session._db,
            scan_id=self.session._scan_id, approval=approval,
            resolve_conflict=True, approved_target_name=name,
        )

    def test_different_content_preserves_original_destination_and_moves_renamed(self):
        preview = self.preview()
        self.assertEqual(preview["suggested_filename"], "teste_archivia_1.jpg")
        self.assertFalse(preview["files_modified"])
        response = self.move(preview["suggested_filename"])
        self.assertEqual(response["status"], "movido")
        self.assertEqual(response["destination"], str(self.dest / "teste_archivia_1.jpg"))
        self.assertEqual(self.existing.read_bytes(), b"imagem-ja-existente")
        self.assertEqual((self.dest / "teste_archivia_1.jpg").read_bytes(),
                         b"imagem-origem-distinta")
        self.assertFalse(self.source.exists())
        self.assertFalse(list(self.dest.glob(".archivia-stage-*")))

    def test_existing_alternative_generates_next_free_name(self):
        (self.dest / "teste_archivia_1.jpg").write_bytes(b"ocupado")
        preview = self.preview()
        self.assertEqual(preview["suggested_filename"], "teste_archivia_2.jpg")
        result = self.move(preview["suggested_filename"])
        self.assertEqual(result["status"], "movido")
        self.assertEqual((self.dest / "teste_archivia_1.jpg").read_bytes(), b"ocupado")

    def test_alternative_changed_after_confirmation_is_rejected(self):
        first = self.preview()
        (self.dest / first["suggested_filename"]).write_bytes(b"novo-conflito")
        with self.assertRaises(ValueError):
            self.move(first["suggested_filename"])
        self.assertTrue(self.source.exists())
        self.assertEqual(self.existing.read_bytes(), b"imagem-ja-existente")

    def test_identical_content_never_executes_conflict_move(self):
        self.existing.write_bytes(self.source.read_bytes())
        with self.assertRaises(ValueError):
            self.preview()
        with self.assertRaises(ValueError):
            self.move("teste_archivia_1.jpg")
        self.assertTrue(self.source.exists())
        self.assertFalse((self.dest / "teste_archivia_1.jpg").exists())

    def test_wrong_approval_or_unconfirmed_name_cannot_move(self):
        with self.assertRaises(ValueError):
            self.move("teste_archivia_1.jpg", approval="")
        with self.assertRaises(ValueError):
            self.move(None)
        with self.assertRaises(ValueError):
            self.move("qualquer-outro.jpg")
        self.assertTrue(self.source.exists())
        self.assertFalse((self.dest / "teste_archivia_1.jpg").exists())

    def test_changed_source_blocks_rename(self):
        preview = self.preview()
        self.source.write_bytes(b"origem-alterada-depois-do-inventario")
        with self.assertRaises(ValueError):
            self.move(preview["suggested_filename"])
        self.assertTrue(self.source.exists())
        self.assertFalse((self.dest / preview["suggested_filename"]).exists())

    def test_ambiguous_sources_are_not_automatically_resolved(self):
        sub = self.origin / "sub"
        sub.mkdir()
        (sub / "teste.jpg").write_bytes(b"terceira-versao")
        self.session.refresh()
        self.plan = self.new_plan()
        with self.assertRaises(ValueError):
            self.preview()
        self.assertEqual(self.existing.read_bytes(), b"imagem-ja-existente")
        self.assertTrue(self.source.exists())


if __name__ == "__main__":
    unittest.main()
