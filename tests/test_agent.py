"""TEST-ONLY: mock de transporte Ollama isolado; nenhum servidor ou arquivo pessoal."""
import unittest
from datetime import datetime, timezone
import os
from unittest.mock import patch

from support import temporary_test_directory
from archivia.agent import ask_agent, dispatch_tool
from archivia.catalog import store_inventory, scan_for_folder
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

    def test_date_organization_tool_is_readonly_and_limited(self):
        # TEST-ONLY: arquivos sintéticos; a ferramenta não cria subpastas.
        with temporary_test_directory() as tmp:
            root = tmp / "origem"
            dest = tmp / "destino"
            root.mkdir()
            dest.mkdir()
            media = root / "foto.jpg"
            media.write_bytes(b"imagem de teste")
            ts = datetime(2025, 8, 9, tzinfo=timezone.utc).timestamp()
            os.utime(media, (ts, ts))
            db = tmp / "catalogo.sqlite3"
            snapshot = store_inventory(inventory(root), db)
            result = dispatch_tool("simular_organizacao_por_data", {
                "categoria": "imagem", "destino": str(dest),
                "scan_id": snapshot["scan_id"], "limite": 1,
            }, db)
            self.assertFalse(result["executable"])
            self.assertEqual(result["mode"], "simulation")
            self.assertEqual(result["blocked"], 0)
            self.assertEqual(result["selected"], 1)
            self.assertEqual(result["actions"][0]["destination"], str(dest / "2025" / "08" / "foto.jpg"))
            self.assertFalse((dest / "2025").exists())
            self.assertTrue(media.exists())

    def test_date_organization_tool_rejects_unauthorized_arguments(self):
        # TEST-ONLY: falhas são verificadas antes de qualquer tentativa de leitura.
        with temporary_test_directory() as tmp:
            for args in (
                {}, {"categoria": "imagem"},
                {"categoria": "documento", "destino": str(tmp)},
                {"categoria": "imagem", "destino": ""},
                {"categoria": "imagem", "destino": str(tmp), "execute": True},
                {"categoria": "imagem", "destino": str(tmp), "limite": 51},
                {"categoria": "imagem", "destino": str(tmp), "limite": True},
                {"categoria": "imagem", "destino": str(tmp), "scan_id": 0},
            ):
                with self.subTest(arguments=args):
                    with self.assertRaises(ValueError):
                        dispatch_tool("simular_organizacao_por_data", args, tmp / "nao_existe.db")

    def test_ollama_mock_date_plan_never_executes(self):
        # MOCK-ONLY: modelo simulado, sem chamadas de rede Ollama.
        with temporary_test_directory() as tmp:
            root = tmp / "origem"
            dest = tmp / "destino"
            root.mkdir()
            dest.mkdir()
            media = root / "imagem.jpg"
            media.write_bytes(b"x")
            db = tmp / "catalogo.sqlite3"
            store_inventory(inventory(root), db)
            first = {"role": "assistant", "content": "", "tool_calls": [
                {"function": {
                    "name": "simular_organizacao_por_data",
                    "arguments": {"categoria": "imagem", "destino": str(dest)},
                }}
            ]}
            final = {"role": "assistant", "content": "Simulação produzida; nada foi movido."}
            with patch("archivia.agent._ollama_chat", side_effect=[first, final]) as mocked:
                output = ask_agent("Simule ano e mês", "modelo-falso", db)
            self.assertEqual(mocked.call_count, 2)
            self.assertEqual(output["tools_used"][0]["tool"], "simular_organizacao_por_data")
            self.assertFalse(output["tools_used"][0]["result"]["executable"])
            self.assertFalse(output["files_modified"])
            self.assertTrue(media.exists())
            self.assertEqual(list(dest.iterdir()), [])

    def test_selected_folder_uses_its_snapshot_for_agent_tools(self):
        # TEST-ONLY: não misturar origens mesmo com snapshot mais novo no banco.
        with temporary_test_directory() as tmp:
            first_root = tmp / "Adele"
            second_root = tmp / "Outra"
            first_root.mkdir()
            second_root.mkdir()
            (first_root / "foto.jpg").write_bytes(b"foto")
            (second_root / "outra.jpg").write_bytes(b"outra")
            db = tmp / "catalogo.sqlite3"
            first = store_inventory(inventory(first_root), db)
            newer = store_inventory(inventory(second_root), db)
            selected = scan_for_folder(first_root, db)
            self.assertEqual(selected, first["scan_id"])
            self.assertNotEqual(selected, newer["scan_id"])
            summary = dispatch_tool("resumo_catalogo", {}, db, context_scan_id=selected)
            self.assertEqual(summary["root"], str(first_root))
            found = dispatch_tool(
                "buscar_arquivos_catalogo", {"categoria": "imagem"}, db,
                context_scan_id=selected,
            )
            self.assertEqual(found["scan_id"], selected)
            self.assertEqual(found["files"][0]["relative_path"], "foto.jpg")
            with self.assertRaises(ValueError):
                dispatch_tool(
                    "buscar_arquivos_catalogo",
                    {"scan_id": newer["scan_id"]}, db,
                    context_scan_id=selected,
                )

    def test_selected_folder_without_catalog_must_not_fallback(self):
        with temporary_test_directory() as tmp:
            root = tmp / "NaoCatalogada"
            root.mkdir()
            db = tmp / "catalogo.sqlite3"
            known = tmp / "Catalogada"
            known.mkdir()
            (known / "foto.jpg").write_bytes(b"teste")
            store_inventory(inventory(known), db)
            with self.assertRaises(ValueError):
                scan_for_folder(root, db)

    def test_agent_mock_enforces_selected_folder_snapshot(self):
        with temporary_test_directory() as tmp:
            first_root = tmp / "Adele"
            other_root = tmp / "Outra"
            first_root.mkdir()
            other_root.mkdir()
            (first_root / "foto.jpg").write_bytes(b"foto")
            (other_root / "foto.jpg").write_bytes(b"foto")
            db = tmp / "catalogo.sqlite3"
            first = store_inventory(inventory(first_root), db)
            other = store_inventory(inventory(other_root), db)
            question = {"role": "assistant", "content": "", "tool_calls": [
                {"function": {"name": "buscar_arquivos_catalogo", "arguments": {
                    "scan_id": other["scan_id"], "categoria": "imagem",
                }}}
            ]}
            done = {"role": "assistant", "content": "Não foi consultada outra origem."}
            with patch("archivia.agent._ollama_chat", side_effect=[question, done]):
                output = ask_agent(
                    "Localize imagens da pasta escolhida", "modelo-falso", db,
                    context_scan_id=first["scan_id"],
                )
            self.assertIn("error", output["tools_used"][0]["result"])
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
