"""TEST-ONLY: mock de transporte Ollama isolado; nenhum servidor ou arquivo pessoal."""
import unittest
from unittest.mock import patch

from support import temporary_test_directory
from archivia.agent import ask_agent, dispatch_tool
from archivia.catalog import store_inventory
from archivia.inventory import inventory


class AgentTests(unittest.TestCase):
    def test_unknown_tool_blocked(self):
        with self.assertRaisesRegex(ValueError, "não autorizada"):
            dispatch_tool("executar_shell", {"comando": "dir"})

    def test_rejects_extra_tool_arguments(self):
        with temporary_test_directory() as tmp:
            with self.assertRaises(ValueError):
                dispatch_tool("simular_movimentacao", {
                    "categoria": "imagem", "destino": str(tmp), "execute": True
                })

    def test_ollama_mock_uses_readonly_summary(self):
        # MOCK-ONLY: substitui chamadas de rede ao Ollama, não fica em produção.
        with temporary_test_directory() as tmp:
            root = tmp / "midias"
            root.mkdir()
            (root / "foto.jpg").write_bytes(b"test")
            db = tmp / "catalogo.sqlite3"
            store_inventory(inventory(root), db)
            first = {"role": "assistant", "content": "", "tool_calls": [
                {"function": {"name": "resumo_catalogo", "arguments": {}}}
            ]}
            last = {"role": "assistant", "content": "Há uma imagem no catálogo."}
            with patch("archivia.agent._ollama_chat", side_effect=[first, last]) as mocked:
                output = ask_agent("Quantas imagens tenho?", "modelo-falso", db)
            self.assertEqual(mocked.call_count, 2)
            self.assertEqual(output["tools_used"][0]["result"]["media_files"], 1)
            self.assertFalse(output["files_modified"])

    def test_ollama_mock_cannot_execute_unknown_tool(self):
        with temporary_test_directory() as tmp:
            message = {"role": "assistant", "content": "", "tool_calls": [
                {"function": {"name": "apagar_tudo", "arguments": {}}}
            ]}
            with patch("archivia.agent._ollama_chat", side_effect=[
                message, {"role": "assistant", "content": "Não posso executar."}
            ]):
                output = ask_agent("Apague tudo", "modelo-falso", tmp / "missing.db")
            self.assertIn("error", output["tools_used"][0]["result"])
            self.assertFalse(output["files_modified"])


if __name__ == "__main__":
    unittest.main()
