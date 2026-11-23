"""Teste isolado do SHA-256 em conflitos de nome, sem mídia real."""
import unittest
from unittest.mock import patch

from support import temporary_test_directory
from archivia.agent import FolderCatalogSession, dispatch_tool
from archivia.conflict_hash import verify_plan_conflict


class PlanConflictHashTests(unittest.TestCase):
    def setUp(self):
        self.tmp = temporary_test_directory()
        self.work = self.tmp.__enter__()
        self.origin = self.work / "origem"
        self.dest = self.work / "destino"
        self.origin.mkdir()
        self.dest.mkdir()
        self.source = self.origin / "a.jpg"
        self.target = self.dest / "a.jpg"
        self.source.write_bytes(b"mesmo conteudo")
        self.target.write_bytes(b"mesmo conteudo")
        self.session = FolderCatalogSession(self.origin)
        self.session.refresh()
        self.plan = dispatch_tool(
            "planejar_consolidacao_recursiva",
            {"categoria": "imagem", "destino": str(self.dest)},
            db_path=self.session._db, context_scan_id=self.session._scan_id,
        )
        self.assertEqual(self.plan["blocked"], 1)

    def tearDown(self):
        self.session.close()
        self.tmp.__exit__(None, None, None)

    def verify(self, name="a.jpg"):
        return dispatch_tool(
            "verificar_sha256_bloqueio_ultimo_plano", {"arquivo": name},
            db_path=self.session._db, context_scan_id=self.session._scan_id,
            previous_plan=self.plan,
        )

    def test_identical_bytes_confirm_duplicate_read_only(self):
        result = self.verify()
        self.assertEqual(result["status"], "duplicata_confirmada")
        self.assertTrue(result["sha256_equal"])
        self.assertFalse(result["files_modified"])
        self.assertFalse(result["executable"])
        self.assertEqual(self.source.read_bytes(), self.target.read_bytes())

    def test_different_bytes_confirm_conflict_not_duplicate(self):
        self.target.write_bytes(b"conteudo diferente")
        result = self.verify()
        self.assertEqual(result["status"], "conteudo_diferente")
        self.assertFalse(result["duplicate_sha256_confirmed"])
        self.assertFalse(result["sha256_equal"])

    def test_modified_source_is_inconclusive(self):
        self.source.write_bytes(b"alterado apos inventario")
        result = self.verify()
        self.assertEqual(result["status"], "inconclusivo")
        self.assertIsNone(result["sha256_equal"])

    def test_missing_destination_is_inconclusive(self):
        self.target.unlink()
        result = self.verify()
        self.assertEqual(result["status"], "inconclusivo")

    def test_reject_ambiguous_or_unplanned_names(self):
        for filename in ("../a.jpg", "b.jpg", ""):
            with self.subTest(filename=filename), self.assertRaises(ValueError):
                self.verify(filename)
        with self.assertRaises(ValueError):
            dispatch_tool(
                "verificar_sha256_bloqueio_ultimo_plano",
                {"arquivo": "a.jpg", "executar": True},
                db_path=self.session._db, context_scan_id=self.session._scan_id,
                previous_plan=self.plan,
            )

    def test_reject_stale_snapshot(self):
        with self.assertRaises(ValueError):
            dispatch_tool(
                "verificar_sha256_bloqueio_ultimo_plano", {"arquivo": "a.jpg"},
                db_path=self.session._db,
                context_scan_id=self.session._scan_id + 1,
                previous_plan=self.plan,
            )

    def test_agent_calls_hash_tool_across_turns(self):
        plan_call = {"role": "assistant", "content": "", "tool_calls": [{
            "function": {"name": "planejar_consolidacao_recursiva",
                         "arguments": {"categoria": "imagem", "destino": str(self.dest)}}
        }]}
        hash_call = {"role": "assistant", "content": "", "tool_calls": [{
            "function": {"name": "verificar_sha256_bloqueio_ultimo_plano",
                         "arguments": {"arquivo": "a.jpg"}}
        }]}
        self.session._last_recursive_plan = None
        with patch("archivia.agent._ollama_chat", side_effect=[
            plan_call, {"content": "Prévia pronta."},
            hash_call, {"content": "SHA-256 idêntico."},
        ]):
            first = self.session.ask("Planejar", "mock")
            second = self.session.ask("Compare SHA-256 de a.jpg", "mock")
        self.assertTrue(first["plan_memory_available"])
        self.assertEqual(second["tools_used"][0]["result"]["status"],
                         "duplicata_confirmada")
        self.assertFalse(second["files_modified"])


if __name__ == "__main__":
    unittest.main()
