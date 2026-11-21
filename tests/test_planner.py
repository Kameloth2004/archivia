"""TEST-ONLY: plano de movimentações sem executar nenhuma ação sobre arquivos."""
import unittest

from support import temporary_test_directory
from archivia.catalog import store_inventory
from archivia.inventory import inventory
from archivia.planner import propose_moves


class PlannerTests(unittest.TestCase):
    def test_proposes_without_moving_or_modifying(self):
        with temporary_test_directory() as tmp:
            source = tmp / "midias"
            target = tmp / "destino"
            source.mkdir()
            target.mkdir()
            image = source / "foto.jpg"
            image.write_bytes(b"synthetic")
            db = tmp / "data" / "catalogo.sqlite3"
            store_inventory(inventory(source), db)
            plan = propose_moves(target, "imagem", db_path=db)
            self.assertFalse(plan["executable"])
            self.assertEqual(plan["mode"], "simulation")
            self.assertEqual(plan["selected"], 1)
            self.assertEqual(plan["blocked"], 0)
            self.assertEqual(plan["actions"][0]["status"], "proposto")
            self.assertTrue(image.exists())
            self.assertFalse((target / "foto.jpg").exists())

    def test_blocks_existing_destination(self):
        with temporary_test_directory() as tmp:
            source = tmp / "midias"
            target = tmp / "destino"
            source.mkdir()
            target.mkdir()
            (source / "foto.jpg").write_bytes(b"source")
            existing = target / "foto.jpg"
            existing.write_bytes(b"existing")
            db = tmp / "data" / "catalogo.sqlite3"
            store_inventory(inventory(source), db)
            plan = propose_moves(target, "imagem", db_path=db)
            self.assertEqual(plan["blocked"], 1)
            self.assertEqual(plan["actions"][0]["reason"], "destino_ja_existe_ou_link")
            self.assertEqual(existing.read_bytes(), b"existing")

    def test_blocks_duplicate_target_names_from_different_folders(self):
        # TEST-ONLY: nomes iguais em pastas distintas não devem competir pelo destino.
        with temporary_test_directory() as tmp:
            source = tmp / "midias"
            target = tmp / "destino"
            (source / "a").mkdir(parents=True)
            (source / "b").mkdir()
            target.mkdir()
            (source / "a" / "foto.jpg").write_bytes(b"um")
            (source / "b" / "foto.jpg").write_bytes(b"dois")
            db = tmp / "data" / "catalogo.sqlite3"
            store_inventory(inventory(source), db)
            plan = propose_moves(target, "imagem", db_path=db)
            self.assertEqual(plan["selected"], 2)
            self.assertEqual(plan["blocked"], 1)
            self.assertEqual(sum(a["status"] == "proposto" for a in plan["actions"]), 1)
            self.assertEqual(plan["actions"][1]["reason"], "destino_duplicado_no_plano")

    def test_blocks_changed_file(self):
        with temporary_test_directory() as tmp:
            source = tmp / "midias"
            target = tmp / "destino"
            source.mkdir()
            target.mkdir()
            image = source / "foto.jpg"
            image.write_bytes(b"a")
            db = tmp / "data" / "catalogo.sqlite3"
            store_inventory(inventory(source), db)
            image.write_bytes(b"alterado")
            plan = propose_moves(target, "imagem", db_path=db)
            self.assertEqual(plan["blocked"], 1)
            self.assertEqual(plan["actions"][0]["reason"], "origem_alterada_desde_inventario")

    def test_invalid_limit_or_destination(self):
        with temporary_test_directory() as tmp:
            source = tmp / "midias"
            source.mkdir()
            (source / "a.jpg").write_bytes(b"a")
            db = tmp / "data" / "catalogo.sqlite3"
            store_inventory(inventory(source), db)
            with self.assertRaises(ValueError):
                propose_moves(tmp / "inexistente", "imagem", db_path=db)
            with self.assertRaises(ValueError):
                propose_moves(tmp, "imagem", db_path=db, limit=0)

    def test_plan_never_creates_destination(self):
        with temporary_test_directory() as tmp:
            source = tmp / "midias"
            source.mkdir()
            (source / "a.jpg").write_bytes(b"a")
            db = tmp / "data" / "catalogo.sqlite3"
            store_inventory(inventory(source), db)
            newdir = tmp / "nao_criar"
            with self.assertRaises(ValueError):
                propose_moves(newdir, "imagem", db_path=db)
            self.assertFalse(newdir.exists())


if __name__ == "__main__":
    unittest.main()
