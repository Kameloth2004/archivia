"""TEST-ONLY: mock de transporte Ollama isolado; nenhum servidor ou arquivo pessoal."""
import unittest
from datetime import datetime, timezone
import os
from unittest.mock import patch

from support import temporary_test_directory
from archivia.agent import ask_agent, ask_agent_for_folder, dispatch_tool
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

    def test_agent_consolidation_preview_uses_selected_origin_and_blocks_collision(self):
        # TEST-ONLY / MOCK-ONLY: arquivos em subpastas, com nome repetido.
        with temporary_test_directory() as tmp:
            origin = tmp / "Adele"
            other = tmp / "Outra"
            destination = tmp / "Imagens Adele"
            (origin / "shows").mkdir(parents=True)
            (origin / "capas").mkdir()
            other.mkdir()
            destination.mkdir()
            (origin / "shows" / "foto.jpg").write_bytes(b"primeira")
            (origin / "capas" / "foto.jpg").write_bytes(b"segunda")
            (origin / "capas" / "capa.png").write_bytes(b"capa")
            (origin / "shows" / "audio.mp3").write_bytes(b"audio")
            (other / "outra.jpg").write_bytes(b"outra")
            db = tmp / "catalogo.sqlite3"
            selected = store_inventory(inventory(origin), db)["scan_id"]
            store_inventory(inventory(other), db)  # último global é outra pasta

            arguments = {"categoria": "imagem", "destino": str(destination)}
            mock_call = {"role": "assistant", "content": "", "tool_calls": [
                {"function": {"name": "simular_movimentacao", "arguments": arguments}}
            ]}
            final = {"role": "assistant", "content": "Plano apenas simulado."}
            with patch("archivia.agent._ollama_chat", side_effect=[mock_call, final]):
                reply = ask_agent(
                    "Reúna as imagens da pasta escolhida", "modelo-falso", db,
                    context_scan_id=selected,
                )
            self.assertEqual(reply["tools_used"][0]["arguments"], arguments)
            plan = reply["tools_used"][0]["result"]
            self.assertEqual(plan["scan_id"], selected)
            self.assertEqual(plan["root"], str(origin))
            self.assertEqual(plan["total_matches"], 3)
            self.assertEqual(plan["selected"], 3)
            self.assertEqual(plan["blocked"], 1)
            self.assertFalse(plan["truncated"])
            self.assertFalse(plan["executable"])
            self.assertEqual(plan["mode"], "simulation")
            self.assertTrue(any(
                action.get("reason") == "destino_duplicado_no_plano"
                for action in plan["actions"]
            ))
            self.assertEqual(len(list(origin.rglob("*.jpg"))), 2)
            self.assertTrue((origin / "capas" / "capa.png").exists())
            self.assertTrue((origin / "shows" / "audio.mp3").exists())
            self.assertEqual(list(destination.iterdir()), [])
            self.assertFalse(reply["files_modified"])

    def test_ollama_mock_global_consolidation_uses_selected_snapshot_and_only_summary(self):
        # TEST-ONLY/MOCK-ONLY: leitura global por IA, sem alterações nos arquivos.
        with temporary_test_directory() as tmp:
            origin = tmp / "Adele"
            other = tmp / "Outra"
            dest = tmp / "destino"
            origin.mkdir()
            other.mkdir()
            dest.mkdir()
            for number in range(105):
                folder = origin / f"sub_{number:03d}"
                folder.mkdir()
                name = "repetida.jpg" if number in (0, 104) else f"foto_{number:03d}.jpg"
                (folder / name).write_bytes(f"item-{number}".encode())
            (other / "outra.jpg").write_bytes(b"outra")
            db = tmp / "catalogo.sqlite3"
            selected = store_inventory(inventory(origin), db)["scan_id"]
            other_scan = store_inventory(inventory(other), db)["scan_id"]
            arguments = {"categoria": "imagem", "destino": str(dest)}
            first = {"role": "assistant", "content": "", "tool_calls": [
                {"function": {"name": "resumir_consolidacao", "arguments": arguments}}
            ]}
            last = {"role": "assistant", "content": "Análise global simulada."}
            with patch("archivia.agent._ollama_chat", side_effect=[first, last]):
                reply = ask_agent(
                    "Simule reunir imagens no destino indicado", "modelo-falso",
                    db, context_scan_id=selected,
                )
            tool = reply["tools_used"][0]
            self.assertEqual(tool["tool"], "resumir_consolidacao")
            self.assertEqual(tool["arguments"], arguments)
            summary = tool["result"]
            self.assertEqual(summary["scan_id"], selected)
            self.assertNotEqual(summary["scan_id"], other_scan)
            self.assertEqual(summary["total_matches"], 105)
            self.assertEqual(summary["examined"], 105)
            self.assertEqual(summary["proposed"], 104)
            self.assertEqual(summary["blocked"], 1)
            self.assertEqual(summary["pending"], 0)
            self.assertTrue(summary["complete"])
            self.assertFalse(summary["executable"])
            self.assertEqual(summary["actions"], [])
            self.assertEqual(list(dest.iterdir()), [])
            self.assertEqual(len(list(origin.rglob("*.jpg"))), 105)
            self.assertFalse(reply["files_modified"])

    def test_global_consolidation_agent_rejects_bad_arguments(self):
        with temporary_test_directory() as tmp:
            for arguments in (
                {}, {"categoria": "imagem"},
                {"categoria": "imagem", "destino": str(tmp), "execute": True},
                {"categoria": "documento", "destino": str(tmp)},
                {"categoria": "imagem", "destino": ""},
                {"categoria": "imagem", "destino": str(tmp), "limite": True},
                {"categoria": "imagem", "destino": str(tmp), "limite": 10001},
                {"categoria": "imagem", "destino": str(tmp), "limite": "500"},
            ):
                with self.subTest(arguments=arguments):
                    with self.assertRaises(ValueError):
                        dispatch_tool("resumir_consolidacao", arguments, tmp / "nada.sqlite3")

    def test_auto_folder_session_is_temporary_and_preserves_persistent_catalog(self):
        # TEST-ONLY: consulta a pasta escolhida sem aumentar histórico permanente.
        with temporary_test_directory() as tmp:
            folder = tmp / "origem"
            folder.mkdir()
            (folder / "foto.jpg").write_bytes(b"teste")
            db = tmp / "permanente.sqlite3"
            saved = store_inventory(inventory(folder), db)
            original_bytes = db.read_bytes()
            first = {"role": "assistant", "content": "", "tool_calls": [
                {"function": {"name": "buscar_arquivos_catalogo",
                              "arguments": {"categoria": "imagem"}}}
            ]}
            last = {"role": "assistant", "content": "Uma imagem."}
            with patch("archivia.agent._ollama_chat", side_effect=[first, last]):
                response = ask_agent_for_folder("Conte as imagens", "modelo-falso", folder)
            self.assertTrue(response["temporary_catalog"])
            self.assertEqual(response["source_root"], str(folder))
            result = response["tools_used"][0]["result"]
            self.assertEqual(result["count"], 1)
            self.assertEqual(result["root"], str(folder))
            self.assertEqual(result["scan_id"], 1)
            self.assertEqual(db.read_bytes(), original_bytes)
            self.assertEqual(saved["scan_id"], 1)
            self.assertTrue((folder / "foto.jpg").exists())
            self.assertFalse(response["files_modified"])

    def test_auto_folder_session_cleans_up_after_agent_failure(self):
        # MOCK-ONLY: verifica remoção da pasta temporária mesmo com erro Ollama.
        with temporary_test_directory() as tmp:
            folder = tmp / "origem"
            folder.mkdir()
            (folder / "foto.jpg").write_bytes(b"teste")
            def fail_chat(_payload):
                raise ValueError("Falha simulada no Ollama")
            with patch("archivia.agent._ollama_chat", side_effect=fail_chat):
                with self.assertRaisesRegex(ValueError, "Falha simulada"):
                    ask_agent_for_folder("Conte", "modelo-falso", folder)
            self.assertTrue((folder / "foto.jpg").exists())

    def test_auto_folder_session_rejects_unreadable_inventory_without_agent_call(self):
        with temporary_test_directory() as tmp:
            folder = tmp / "origem"
            folder.mkdir()
            with patch("archivia.agent.inventory", return_value={
                "root": str(folder), "files": [],
                "summary": {"media_files": 0, "other_files": 0,
                            "symlinks_skipped": 0, "bytes_media": 0},
                "errors": [{"path": str(folder), "error": "falha simulada"}],
            }):
                with patch("archivia.agent._ollama_chat") as chat:
                    with self.assertRaisesRegex(ValueError, "Inventário com erros"):
                        ask_agent_for_folder("Conte", "modelo-falso", folder)
                    chat.assert_not_called()

    def test_agent_logs_real_tool_arguments_and_missing_limit_uses_default(self):
        # MOCK-ONLY: texto narrado pelo modelo pode diferir do tool_call real.
        with temporary_test_directory() as tmp:
            root = tmp / "Adele"
            root.mkdir()
            (root / "foto.jpg").write_bytes(b"teste")
            db = tmp / "catalogo.sqlite3"
            recorded = store_inventory(inventory(root), db)
            args = {"categoria": "imagem", "escopo": "caminho"}
            first = {"role": "assistant", "content": "", "tool_calls": [
                {"function": {
                    "name": "buscar_arquivos_catalogo",
                    "arguments": args,
                }}
            ]}
            final = {"role": "assistant", "content": "Uma imagem."}
            with patch("archivia.agent._ollama_chat", side_effect=[first, final]):
                response = ask_agent(
                    "Quantas imagens?", "modelo-falso", db,
                    context_scan_id=recorded["scan_id"],
                )
            call = response["tools_used"][0]
            self.assertEqual(call["arguments"], args)
            self.assertEqual(call["result"]["count"], 1)
            self.assertEqual(call["result"]["scan_id"], recorded["scan_id"])
            self.assertEqual(call["result"]["page_size"], 10)
            invalid = dict(args, limite="10")
            with self.assertRaisesRegex(ValueError, "limite inválido"):
                dispatch_tool(
                    "buscar_arquivos_catalogo", invalid, db,
                    context_scan_id=recorded["scan_id"],
                )

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
