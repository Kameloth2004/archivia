"""TEST-ONLY: filtros, paginação e relatórios puros da GUI."""
import unittest

from archivia.gui_presentation import (
    catalog_filters, previous_page, next_page, summary_report,
    inventory_report, agent_report, recursive_plan_report,
)


class GUIPresentationTests(unittest.TestCase):
    def test_catalog_filters_preserve_normalized_values_and_dates(self):
        result = catalog_filters(
            category="imagem", scan_id=2, name="  Foto  ", extension=" JPG ",
            scope="filename", date_from="23/11/2026", date_to="24/11/2026",
            date_format="br", sort_by="newest",
        )
        self.assertEqual(result, {
            "category": "imagem", "scan_id": 2, "name_contains": "Foto",
            "extension": "JPG", "search_scope": "filename",
            "date_from": "2026-11-23", "date_to": "2026-11-24",
            "sort_by": "newest",
        })

    def test_catalog_filters_allow_empty_masked_dates(self):
        result = catalog_filters(
            category=None, scan_id=None, name="", extension="", scope="path",
            date_from="//", date_to="//", date_format="br", sort_by="name",
        )
        self.assertEqual(result["date_from"], "")
        self.assertEqual(result["date_to"], "")

    def test_catalog_filters_reject_inverted_dates(self):
        with self.assertRaisesRegex(ValueError, "posterior"):
            catalog_filters(
                category=None, scan_id=None, name="", extension="", scope="path",
                date_from="24/11/2026", date_to="23/11/2026",
                date_format="br", sort_by="name",
            )

    def test_page_navigation_respects_bounds(self):
        self.assertEqual(previous_page(1), 1)
        self.assertEqual(previous_page(3), 2)
        self.assertEqual(next_page(1, 1), 1)
        self.assertEqual(next_page(1, 3), 2)
        self.assertEqual(next_page(3, 3), 3)

    def test_pagination_rejects_invalid_inputs(self):
        for bad in (0, -1, True, "2"):
            with self.subTest(value=bad):
                with self.assertRaises(ValueError):
                    previous_page(bad)
        with self.assertRaises(ValueError):
            next_page(1, -1)

    def test_summary_report_preserves_text_and_counts(self):
        self.assertEqual(
            summary_report({"scan_id": None}),
            "Catálogo vazio: nenhuma catalogação encontrada.",
        )
        report = summary_report({
            "scan_id": 5, "indexed_files": 11, "media_files": 9,
            "by_category": {"imagem": 5, "video": 3, "audio": 1},
            "bytes_media": 1500,
        })
        self.assertIn("Inventário #5 | Arquivos: 11 | Mídias: 9", report)
        self.assertIn("Imagens: 5", report)
        self.assertIn("Espaço: 1,500 bytes", report)

    def test_inventory_report_preserves_messages(self):
        report = inventory_report({
            "root": "C:/fixture",
            "summary": {"indexed_files": 2, "media_files": 1,
                        "by_category": {"imagem": 1}},
            "errors": ["erro simulado"],
        })
        self.assertIn("Pasta: C:/fixture | Arquivos: 2 | Mídias: 1", report)
        self.assertIn("Vídeos: 0", report)
        self.assertIn("Erros: 1", report)

    def test_recursive_plan_report_shows_summary_and_sample(self):
        report = recursive_plan_report({"tools_used": [{
            "tool": "planejar_consolidacao_recursiva",
            "result": {
                "root": "C:/origem", "destination": "D:/destino",
                "total_matches": 18, "examined": 10, "proposed": 9,
                "blocked": 1, "pending": 8, "complete": False,
                "actions": [{"file": "sub/foto.jpg", "status": "proposto",
                             "destination": "D:/destino/foto.jpg"}],
            },
        }]})
        self.assertIn("PARCIAL", report)
        self.assertIn("Pendentes: 8", report)
        self.assertIn("sub/foto.jpg", report)
        self.assertIn("NENHUM ARQUIVO MOVIDO", report)

    def test_recursive_plan_report_does_not_invent_plan(self):
        self.assertIsNone(recursive_plan_report({"tools_used": []}))
        result = recursive_plan_report({"tools_used": [{
            "tool": "planejar_consolidacao_recursiva",
            "result": {"error": "Destino indisponível"},
        }]})
        self.assertIn("Destino indisponível", result)

    def test_agent_report_preserves_short_and_technical_versions(self):
        short, technical = agent_report({
            "answer": "Dois arquivos", "tools_used": [{"name": "resumo_catalogo"}],
            "temporary_catalog": True, "catalog_scanned_utc": "2026-11-23T10:00:00",
        })
        self.assertEqual(short, "Dois arquivos")
        self.assertIn("RESPOSTA DO AGENTE\nDois arquivos", technical)
        self.assertIn("FERRAMENTAS UTILIZADAS", technical)
        self.assertIn("CATÁLOGO DE SESSÃO", technical)
        self.assertIn("Operações de movimentação: indisponíveis nesta versão.", technical)
