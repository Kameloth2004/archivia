"""TEST-ONLY: mock de transporte Ollama isolado; nenhum servidor ou arquivo pessoal."""
import unittest
from datetime import datetime, timezone
import os
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

    def test_search_tool_returns_limited_readonly_results(self):
        # TEST-ONLY: consulta local sintética; não acessa dados reais.
        with temporary_test_directory() as tmp:
            root = tmp / "arquivos"
            root.mkdir()
            (root / "ventilador.pdf").write_bytes(b"doc")
            (root / "ventilador.jpg").write_bytes(b"foto")
            (root / "outro.txt").write_bytes(b"outro")
            db = tmp / "catalogo.sqlite3"
            store_inventory(inventory(root), db)
            result = dispatch_tool("buscar_arquivos_catalogo", {
                "nome": "ventilador", "limite": 1,
            }, db)
            self.assertEqual(result["count"], 2)
            self.assertEqual(len(result["files"]), 1)
            self.assertEqual(result["pages"], 2)
            self.assertTrue((root / "ventilador.pdf").is_file())
            pdf = dispatch_tool("buscar_arquivos_catalogo", {
                "nome": "ventilador", "extensao": "pdf",
            }, db)
            self.assertEqual(pdf["count"], 1)
            self.assertEqual(pdf["files"][0]["relative_path"], "ventilador.pdf")

    def test_search_tool_rejects_unsafe_parameters(self):
        with temporary_test_directory() as tmp:
            for payload in (
                {"limite": 21}, {"limite": 0}, {"pagina": 101},
                {"pagina": True}, {"scan_id": 0},
                {"nome": "abc", "execute": True},
                {"categoria": "inexistente"}, {"extensao": 12},
            ):
                with self.subTest(payload=payload):
                    with self.assertRaises(ValueError):
                        dispatch_tool("buscar_arquivos_catalogo", payload, tmp / "absent.db")

    def test_ollama_mock_search_calls_tool_without_network(self):
        # MOCK-ONLY: ferramenta selecionada pelo modelo simulado, sem Ollama real.
        with temporary_test_directory() as tmp:
            root = tmp / "arquivos"
            root.mkdir()
            (root / "backup.zip").write_bytes(b"abc")
            db = tmp / "catalogo.sqlite3"
            store_inventory(inventory(root), db)
            first = {"role": "assistant", "content": "", "tool_calls": [
                {"function": {
                    "name": "buscar_arquivos_catalogo",
                    "arguments": {"nome": "backup", "limite": 5},
                }}
            ]}
            second = {"role": "assistant", "content": "Encontrei um arquivo compactado."}
            with patch("archivia.agent._ollama_chat", side_effect=[first, second]):
                result = ask_agent("Procure backup no catálogo", "modelo-falso", db)
            self.assertEqual(result["tools_used"][0]["tool"], "buscar_arquivos_catalogo")
            self.assertEqual(result["tools_used"][0]["result"]["count"], 1)
            self.assertFalse(result["files_modified"])

    def test_agent_search_by_filename_and_modification_date(self):
        # TEST-ONLY: testes de data e nome-base em diretórios descartáveis.
        with temporary_test_directory() as tmp:
            root = tmp / "arquivos"
            folder = root / "BACKUPS"
            folder.mkdir(parents=True)
            (folder / "relatorio.pdf").write_bytes(b"x")
            backup = root / "backup_final.pdf"
            backup.write_bytes(b"y")
            ts = datetime(2025, 6, 15, tzinfo=timezone.utc).timestamp()
            os.utime(backup, (ts, ts))
            db = tmp / "catalogo.sqlite3"
            store_inventory(inventory(root), db)
            result = dispatch_tool("buscar_arquivos_catalogo", {
                "nome": "backup", "escopo": "nome",
                "data_inicial": "2025-06-01", "data_final": "2025-06-30",
                "ordenacao": "recentes",
            }, db)
            self.assertEqual(result["count"], 1)
            self.assertEqual(result["search_scope"], "filename")
            self.assertEqual(result["sort_by"], "newest")
            self.assertEqual(result["files"][0]["relative_path"], "backup_final.pdf")

    def test_agent_search_rejects_invalid_scope_and_date(self):
        with temporary_test_directory() as tmp:
            for arguments in (
                {"escopo": "diretorio"}, {"ordenacao": "aleatorio"},
                {"data_inicial": "2025-02-30"},
                {"data_inicial": "2026-01-01", "data_final": "2025-01-01"},
            ):
                with self.subTest(arguments=arguments):
                    with self.assertRaises(ValueError):
                        dispatch_tool("buscar_arquivos_catalogo", arguments, tmp / "ausente.db")

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
