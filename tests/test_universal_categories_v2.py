"""Testes isolados: categorias universais, escopos e integridade de arquivos da V2."""
from __future__ import annotations

import unittest
from contextlib import closing

from support import temporary_test_directory
from archivia.agent import FolderCatalogSession, TOOLS, dispatch_tool
from archivia.inventory import CATEGORIES, CATEGORY_LABELS, inventory
from archivia.move_executor import APPROVAL_PHRASE
from archivia.queue_move import move_queue_approved


SAMPLES = {
    "imagem": "foto.jpg",
    "video": "filme.mp4",
    "audio": "musica.mp3",
    "documento": "relatorio.pdf",
    "planilha": "dados.xlsx",
    "apresentacao": "palestra.pptx",
    "compactado": "pacote.zip",
    "codigo": "programa.py",
    "outro": "arquivo.semextensaoconhecida",
}


class UniversalCategoriesV2Tests(unittest.TestCase):
    def test_category_list_has_all_indexed_groups(self):
        self.assertEqual(set(CATEGORIES), set(SAMPLES))
        self.assertEqual(set(CATEGORY_LABELS), set(CATEGORIES))
        self.assertEqual(len(CATEGORIES), 9)
        from archivia.planner import ALLOWED_CATEGORIES
        self.assertEqual(ALLOWED_CATEGORIES, frozenset(CATEGORIES))

    def test_root_only_plans_and_moves_every_category_safely(self):
        with temporary_test_directory() as tmp:
            root = tmp / "origem"
            destination = root / "Biblioteca"
            destination.mkdir(parents=True)
            nested = root / "nao_tocar"
            nested.mkdir()
            (nested / "preservar.pdf").write_bytes(b"subpasta inalterada")
            (destination / "preservado.txt").write_bytes(b"destino inalterado")
            expected = {}
            for category, name in SAMPLES.items():
                payload = ("conteudo original " + category).encode("utf-8")
                (root / name).write_bytes(payload)
                (nested / name).write_bytes(b"preservar subpasta")
                expected[category] = payload

            with closing(FolderCatalogSession(root)) as session:
                analysis = session.analyze_source(recursive=False)
                self.assertEqual(analysis["summary"]["indexed_files"], 9)
                for category, filename in SAMPLES.items():
                    with self.subTest(category=category):
                        plan = session.prepare_recursive_plan(
                            destination, category, recursive=False,
                        )
                        self.assertFalse(plan["recursive"])
                        self.assertTrue(plan["complete"])
                        self.assertEqual(plan["total_matches"], 1)
                        self.assertEqual(plan["proposed"], 1)
                        self.assertEqual(plan["actions"][0]["file"], filename)
                        report = move_queue_approved(
                            plan, [filename],
                            db_path=session._db, scan_id=session._scan_id,
                            approval=APPROVAL_PHRASE,
                        )
                        self.assertEqual(report["moved"], 1)
                        self.assertFalse((root / filename).exists())
                        self.assertEqual(
                            (destination / filename).read_bytes(), expected[category]
                        )
                        self.assertEqual(
                            (nested / filename).read_bytes(), b"preservar subpasta"
                        )
                self.assertEqual(
                    (destination / "preservado.txt").read_bytes(), b"destino inalterado"
                )
                self.assertEqual(
                    (nested / "preservar.pdf").read_bytes(), b"subpasta inalterada"
                )

    def test_other_includes_files_without_extension(self):
        with temporary_test_directory() as tmp:
            root = tmp / "origem"
            root.mkdir()
            (root / "README").write_bytes(b"without extension")
            (root / "programa.exe").write_bytes(b"synthetic executable")
            (root / "foto.jpg").write_bytes(b"image")
            report = inventory(root, recursive=False)
            self.assertEqual(report["summary"]["by_category"]["outro"], 2)
            self.assertEqual(report["summary"]["by_category"]["imagem"], 1)

    def test_agent_simulations_accept_universal_categories_without_writing(self):
        with temporary_test_directory() as tmp:
            root = tmp / "origem"
            dest = tmp / "destino"
            root.mkdir()
            dest.mkdir()
            (root / "relatorio.pdf").write_bytes(b"synthetic pdf")
            with closing(FolderCatalogSession(root)) as session:
                session.analyze_source()
                for category in ("documento", "planilha", "apresentacao",
                                 "compactado", "codigo", "outro"):
                    with self.subTest(category=category):
                        proposal = dispatch_tool(
                            "planejar_consolidacao_recursiva",
                            {"categoria": category, "destino": str(dest)},
                            db_path=session._db, context_scan_id=session._scan_id,
                        )
                        self.assertFalse(proposal["executable"])
                        self.assertEqual(proposal["category"], category)
                self.assertTrue((root / "relatorio.pdf").exists())
                self.assertEqual(list(dest.iterdir()), [])
            allowed = {
                tool["function"]["name"]: tool["function"]["parameters"]["properties"]
                for tool in TOOLS if tool["function"]["name"] in (
                    "planejar_consolidacao_recursiva",
                    "simular_movimentacao", "resumir_consolidacao",
                    "simular_organizacao_por_data",
                )
            }
            self.assertEqual(len(allowed), 4)
            for properties in allowed.values():
                self.assertEqual(set(properties["categoria"]["enum"]), set(CATEGORIES))

    def test_conflicts_cannot_overwrite_documents_or_other_files(self):
        with temporary_test_directory() as tmp:
            root = tmp / "origem"
            dest = tmp / "destino"
            root.mkdir()
            dest.mkdir()
            (root / "relatorio.pdf").write_bytes(b"novo pdf")
            (dest / "relatorio.pdf").write_bytes(b"pdf existente")
            with closing(FolderCatalogSession(root)) as session:
                plan = session.prepare_recursive_plan(dest, "documento")
                self.assertEqual(plan["proposed"], 0)
                self.assertEqual(plan["blocked_by_reason"]["destino_ja_existe"], 1)
            self.assertEqual((root / "relatorio.pdf").read_bytes(), b"novo pdf")
            self.assertEqual((dest / "relatorio.pdf").read_bytes(), b"pdf existente")


if __name__ == "__main__":
    unittest.main()
