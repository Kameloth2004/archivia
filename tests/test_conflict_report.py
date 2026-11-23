"""Testes isolados do relatório consultivo, sem modificar mídias reais."""
import unittest
from unittest.mock import patch

from support import temporary_test_directory
from archivia.agent import FolderCatalogSession, dispatch_tool


class ConflictReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = temporary_test_directory()
        self.root = self.temp.__enter__()
        self.origin = self.root / "origem"
        self.destination = self.root / "destino"
        self.origin.mkdir()
        self.destination.mkdir()
        self.source = self.origin / "foto.jpg"
        self.target = self.destination / "foto.jpg"
        self.source.write_bytes(b"mesma imagem")
        self.target.write_bytes(b"mesma imagem")
        self.session = FolderCatalogSession(self.origin)
        self.session.refresh()
        self.plan = dispatch_tool(
            "planejar_consolidacao_recursiva",
            {"categoria": "imagem", "destino": str(self.destination)},
            db_path=self.session._db, context_scan_id=self.session._scan_id,
        )

    def tearDown(self):
        self.session.close()
        self.temp.__exit__(None, None, None)

    def report(self, args=None, plan=None, snapshot=None):
        return dispatch_tool(
            "relatorio_resolucao_conflitos", {} if args is None else args,
            db_path=self.session._db,
            context_scan_id=self.session._scan_id if snapshot is None else snapshot,
            previous_plan=self.plan if plan is None else plan,
        )

    def test_identical_preserves_both_files(self):
        result = self.report()
        row = result["results"][0]
        self.assertEqual(row["status"], "duplicata_confirmada")
        self.assertIsNone(row["suggested_filename"])
        self.assertFalse(result["executable"])
        self.assertFalse(result["files_modified"])
        self.assertEqual(self.source.read_bytes(), b"mesma imagem")
        self.assertEqual(self.target.read_bytes(), b"mesma imagem")

    def test_different_content_suggests_unused_filename_without_creating(self):
        self.target.write_bytes(b"imagem distinta")
        (self.destination / "foto_archivia_1.jpg").write_bytes(b"ocupado")
        result = self.report()
        row = result["results"][0]
        self.assertEqual(row["status"], "conteudo_diferente")
        self.assertEqual(row["suggested_filename"], "foto_archivia_2.jpg")
        self.assertFalse((self.destination / "foto_archivia_2.jpg").exists())
        self.assertEqual(self.source.read_bytes(), b"mesma imagem")

    def test_inconclusive_when_source_changes(self):
        self.source.write_bytes(b"alteracao posterior ao inventario")
        row = self.report()["results"][0]
        self.assertEqual(row["status"], "inconclusivo")
        self.assertIsNone(row["suggested_filename"])

    def test_report_limit_and_snapshot_validation(self):
        for args in ({"limite": 0}, {"limite": 11}, {"limite": True},
                     {"limite": "2"}, {"executar": True}):
            with self.subTest(args=args), self.assertRaises(ValueError):
                self.report(args)
        with self.assertRaises(ValueError):
            self.report(snapshot=self.session._scan_id + 1)

    def test_ambiguous_conflict_does_not_guess_a_source(self):
        sub = self.origin / "sub"
        sub.mkdir()
        (sub / "foto.jpg").write_bytes(b"outra imagem")
        self.session.refresh()
        plan = dispatch_tool(
            "planejar_consolidacao_recursiva",
            {"categoria": "imagem", "destino": str(self.destination)},
            db_path=self.session._db, context_scan_id=self.session._scan_id,
        )
        result = self.report(plan=plan)
        self.assertEqual(result["total_blocked_in_plan"], 2)
        self.assertTrue(all(item["status"] == "inconclusivo"
                            for item in result["results"]))

    def test_agent_uses_report_on_next_question(self):
        plan_call = {"role": "assistant", "content": "", "tool_calls": [{
            "function": {"name": "planejar_consolidacao_recursiva",
                         "arguments": {"categoria": "imagem",
                                       "destino": str(self.destination)}}
        }]}
        report_call = {"role": "assistant", "content": "", "tool_calls": [{
            "function": {"name": "relatorio_resolucao_conflitos",
                         "arguments": {"limite": 10}}
        }]}
        with patch("archivia.agent._ollama_chat", side_effect=[
            plan_call, {"content": "Plano."},
            report_call, {"content": "Recomendações."},
        ]):
            first = self.session.ask("Planeje", "mock")
            second = self.session.ask("Sugira resoluções para os bloqueios", "mock")
        self.assertTrue(first["plan_memory_available"])
        self.assertEqual(second["tools_used"][0]["tool"],
                         "relatorio_resolucao_conflitos")
        self.assertEqual(second["tools_used"][0]["result"]["results"][0]["status"],
                         "duplicata_confirmada")
        self.assertFalse(second["files_modified"])


if __name__ == "__main__":
    unittest.main()
