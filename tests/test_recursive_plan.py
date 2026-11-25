"""Simulação recursiva de consolidação solicitada por linguagem natural."""
import unittest
from unittest.mock import patch

from support import temporary_test_directory
from archivia.catalog import store_inventory
from archivia.inventory import inventory
from archivia.recursive_plan import propose_recursive_consolidation
from archivia.agent import ask_agent, dispatch_tool, TOOLS


class RecursivePlanningTests(unittest.TestCase):
    def setup_case(self, tmp):
        root = tmp / "origem"
        dest = tmp / "destino"
        (root / "sub1").mkdir(parents=True)
        (root / "sub2").mkdir(parents=True)
        dest.mkdir()
        (root / "sub1" / "foto.jpg").write_bytes(b"a")
        (root / "sub2" / "foto.jpg").write_bytes(b"b")
        (root / "sub2" / "extra.png").write_bytes(b"c")
        (root / "documento.pdf").write_bytes(b"pdf")
        db = tmp / "catalogo.sqlite3"
        scan = store_inventory(inventory(root), db)["scan_id"]
        return root, dest, db, scan

    def test_recursion_and_name_conflicts_do_not_move_anything(self):
        with temporary_test_directory() as tmp:
            root, dest, db, scan = self.setup_case(tmp)
            result = propose_recursive_consolidation(dest, "imagem", db, scan_id=scan)
            self.assertEqual(result["total_matches"], 3)
            self.assertEqual(result["examined"], 3)
            self.assertEqual(result["blocked"], 1)
            self.assertEqual(result["proposed"], 2)
            self.assertTrue(result["complete"])
            self.assertFalse(result["truncated"])
            self.assertFalse(result["executable"])
            self.assertTrue(result["recursive"])
            self.assertEqual(result["pending"], 0)
            self.assertIn("nome_repetido_entre_subpastas", result["blocked_by_reason"])
            self.assertEqual(len(list(root.rglob("*.jpg"))), 2)
            self.assertEqual(list(dest.iterdir()), [])

    def test_partial_plan_is_explicit(self):
        with temporary_test_directory() as tmp:
            root, dest, db, scan = self.setup_case(tmp)
            result = propose_recursive_consolidation(dest, "imagem", db, scan_id=scan, limit=2)
            self.assertEqual(result["examined"], 2)
            self.assertEqual(result["pending"], 1)
            self.assertFalse(result["complete"])
            self.assertTrue(result["truncated"])
            self.assertFalse(result["executable"])

    def test_existing_destination_blocks_without_replacement(self):
        with temporary_test_directory() as tmp:
            root, dest, db, scan = self.setup_case(tmp)
            (dest / "extra.png").write_bytes(b"NAO-SOBRESCREVER")
            result = propose_recursive_consolidation(dest, "imagem", db, scan_id=scan)
            self.assertIn("destino_ja_existe", result["blocked_by_reason"])
            self.assertEqual((dest / "extra.png").read_bytes(), b"NAO-SOBRESCREVER")

    def test_nested_destination_skips_files_already_inside(self):
        with temporary_test_directory() as tmp:
            root, dest, db, scan = self.setup_case(tmp)
            # sub1 contém foto.jpg e será o destino de sub2/extra.png.
            result = propose_recursive_consolidation(root / "sub1", "imagem", db, scan_id=scan)
            self.assertTrue(result["destination_inside_root"])
            self.assertEqual(result["total_matches"], 3)
            self.assertEqual(result["pending"], 0)
            self.assertTrue(result["complete"])
            self.assertEqual(result["blocked_by_reason"]["ja_no_destino"], 1)
            self.assertEqual(result["proposed"], 1)
            self.assertEqual(result["blocked_by_reason"]["destino_ja_existe"], 1)
            self.assertEqual((root / "sub1" / "foto.jpg").read_bytes(), b"a")
            self.assertTrue((root / "sub2" / "extra.png").exists())

    def test_same_folder_is_still_rejected(self):
        with temporary_test_directory() as tmp:
            root, dest, db, scan = self.setup_case(tmp)
            with self.assertRaisesRegex(ValueError, "mesma pasta"):
                propose_recursive_consolidation(root, "imagem", db, scan_id=scan)

    def test_model_tool_is_allowlisted_and_bounded(self):
        self.assertIn(
            "planejar_consolidacao_recursiva",
            {t["function"]["name"] for t in TOOLS},
        )
        with temporary_test_directory() as tmp:
            root, dest, db, scan = self.setup_case(tmp)
            args = {"categoria": "imagem", "destino": str(dest), "limite": 3}
            report = dispatch_tool("planejar_consolidacao_recursiva", args, db, scan)
            self.assertEqual(report["scan_id"], scan)
            self.assertEqual(report["total_matches"], 3)
            self.assertFalse(report["executable"])
            for bad in (
                {"categoria": "imagem", "destino": str(dest), "executar": True},
                {"categoria": "imagem", "destino": str(dest), "limite": 501},
                {"categoria": "imagem", "destino": str(dest), "limite": True},
                {"categoria": "documento", "destino": str(dest)},
                {"categoria": "imagem", "destino": ""},
            ):
                with self.subTest(bad=bad):
                    with self.assertRaises(ValueError):
                        dispatch_tool("planejar_consolidacao_recursiva", bad, db, scan)

    def test_ollama_mock_requests_plan_but_never_executes(self):
        with temporary_test_directory() as tmp:
            root, dest, db, scan = self.setup_case(tmp)
            tool_call = {
                "role": "assistant", "content": "",
                "tool_calls": [{
                    "function": {
                        "name": "planejar_consolidacao_recursiva",
                        "arguments": {"categoria": "imagem", "destino": str(dest)},
                    }
                }],
            }
            final = {"role": "assistant", "content": "Plano preparado, sem mover."}
            with patch("archivia.agent._ollama_chat", side_effect=[tool_call, final]):
                answer = ask_agent(
                    "Mova todas as imagens das subpastas para o destino",
                    "modelo-ficticio", db, context_scan_id=scan,
                )
            self.assertFalse(answer["files_modified"])
            self.assertEqual(
                answer["tools_used"][0]["tool"], "planejar_consolidacao_recursiva",
            )
            self.assertEqual(answer["tools_used"][0]["result"]["total_matches"], 3)
            self.assertEqual(list(dest.iterdir()), [])
            self.assertTrue((root / "sub1" / "foto.jpg").exists())
