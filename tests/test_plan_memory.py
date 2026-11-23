"""Memória operacional do plano: somente fixtures e transporte Ollama simulado."""
import unittest
from unittest.mock import patch

from support import temporary_test_directory
from archivia.agent import FolderCatalogSession, dispatch_tool
from archivia.plan_memory import latest_recursive_plan, blocked_details


class PlanMemoryTests(unittest.TestCase):
    def _plan(self):
        return {
            "mode": "simulation", "executable": False, "scan_id": 1,
            "complete": True, "root": "X:/origem", "destination": "Y:/destino",
            "actions": [
                {"file": "sub/a.jpg", "source": "X:/origem/sub/a.jpg",
                 "destination": "Y:/destino/a.jpg", "status": "bloqueado",
                 "reason": "destino_ja_existe"},
                {"file": "sub/b.jpg", "source": "X:/origem/sub/b.jpg",
                 "destination": "Y:/destino/b.jpg", "status": "proposto", "reason": None},
            ],
        }

    def test_memory_explains_conflict_without_claiming_duplicate(self):
        info = blocked_details(self._plan())
        self.assertEqual(info["matching_blocked"], 1)
        self.assertEqual(info["files"][0]["reason_code"], "destino_ja_existe")
        self.assertIn("mesmo nome", info["files"][0]["explanation"])
        self.assertFalse(info["files"][0]["duplicate_sha256_confirmed"])
        self.assertTrue(info["read_only"])
        self.assertFalse(info["files_modified"])

    def test_filter_by_file_name_and_invalid_requests(self):
        self.assertEqual(blocked_details(self._plan(), file_name="a.jpg")["returned"], 1)
        self.assertEqual(blocked_details(self._plan(), file_name="sub/a.jpg")["returned"], 1)
        self.assertEqual(blocked_details(self._plan(), file_name="b.jpg")["returned"], 0)
        for bad_limit in (0, 26, True, "5"):
            with self.subTest(limit=bad_limit):
                with self.assertRaises(ValueError):
                    blocked_details(self._plan(), limit=bad_limit)
        with self.assertRaisesRegex(ValueError, "Não há plano"):
            blocked_details(None)

    def test_only_accepted_plan_from_current_snapshot_is_saved(self):
        valid = {"tool": "planejar_consolidacao_recursiva", "result": self._plan()}
        chosen = latest_recursive_plan([valid], 1)
        self.assertIsNotNone(chosen)
        chosen["actions"][0]["reason"] = "alterado"
        self.assertEqual(self._plan()["actions"][0]["reason"], "destino_ja_existe")
        self.assertIsNone(latest_recursive_plan([valid], 2))
        self.assertIsNone(latest_recursive_plan([{"tool": "resumo_catalogo", "result": self._plan()}], 1))
        self.assertIsNone(latest_recursive_plan([{"tool": "planejar_consolidacao_recursiva", "result": {"error": "falha"}}], 1))

    def test_dispatch_is_bound_to_same_snapshot_and_denies_extra_keys(self):
        plan = self._plan()
        report = dispatch_tool("consultar_bloqueios_ultimo_plano", {"arquivo": "a.jpg"},
                               context_scan_id=1, previous_plan=plan)
        self.assertEqual(report["returned"], 1)
        for snapshot, args in [
            (2, {}), (None, {}), (1, {"executar": True}),
            (1, {"limite": 100}), (1, {"arquivo": None}),
        ]:
            with self.subTest(snapshot=snapshot, args=args):
                with self.assertRaises(ValueError):
                    dispatch_tool("consultar_bloqueios_ultimo_plano", args,
                                  context_scan_id=snapshot, previous_plan=plan)

    def test_session_remembers_plan_across_questions_and_forgets_after_refresh(self):
        with temporary_test_directory() as tmp:
            origin = tmp / "origem"
            dest = tmp / "destino"
            origin.mkdir()
            dest.mkdir()
            (origin / "a.jpg").write_bytes(b"a")
            (dest / "a.jpg").write_bytes(b"outra imagem")
            session = FolderCatalogSession(origin)
            plan_call = {"role": "assistant", "content": "", "tool_calls": [{
                "function": {"name": "planejar_consolidacao_recursiva",
                             "arguments": {"categoria": "imagem", "destino": str(dest)}}
            }]}
            blocked_call = {"role": "assistant", "content": "", "tool_calls": [{
                "function": {"name": "consultar_bloqueios_ultimo_plano",
                             "arguments": {"arquivo": "a.jpg"}}
            }]}
            final_plan = {"role": "assistant", "content": "Plano gerado."}
            final_reason = {"role": "assistant", "content": "Nome de destino ocupado."}
            with patch("archivia.agent._ollama_chat",
                       side_effect=[plan_call, final_plan, blocked_call, final_reason]) as model:
                first = session.ask("Planeje reunir imagens", "modelo-falso")
                second = session.ask("Por que a imagem foi bloqueada?", "modelo-falso")
            self.assertTrue(first["plan_memory_available"])
            self.assertTrue(second["plan_memory_available"])
            self.assertTrue(second["catalog_reused"])
            report = second["tools_used"][0]["result"]
            self.assertEqual(report["files"][0]["reason_code"], "destino_ja_existe")
            self.assertEqual(model.call_count, 4)
            self.assertTrue(origin.joinpath("a.jpg").exists())
            self.assertEqual(dest.joinpath("a.jpg").read_bytes(), b"outra imagem")
            session.refresh()
            self.assertIsNone(session._last_recursive_plan)
            session.close()
            self.assertIsNone(session._last_recursive_plan)

    def test_older_plan_remains_after_nonplanning_followup(self):
        with temporary_test_directory() as tmp:
            origin = tmp / "origem"
            dest = tmp / "destino"
            origin.mkdir()
            dest.mkdir()
            (origin / "a.jpg").write_bytes(b"a")
            (dest / "a.jpg").write_bytes(b"x")
            session = FolderCatalogSession(origin)
            plan_call = {"role": "assistant", "content": "", "tool_calls": [{
                "function": {"name": "planejar_consolidacao_recursiva",
                             "arguments": {"categoria": "imagem", "destino": str(dest)}}
            }]}
            with patch("archivia.agent._ollama_chat", side_effect=[
                plan_call, {"content": "Plano pronto."},
                {"role": "assistant", "content": "Certo."},
            ]):
                session.ask("Planejar", "mock")
                result = session.ask("Obrigado", "mock")
            self.assertTrue(result["plan_memory_available"])
            self.assertIsNotNone(session._last_recursive_plan)
            session.close()
