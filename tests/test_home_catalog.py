"""Testes da elegibilidade para salvar inventário, sem PySide6."""
import unittest

from archivia.gui_helpers import can_save_inventory_preview


class HomeCatalogEligibilityTests(unittest.TestCase):
    def test_allows_complete_preview_for_selected_folder(self):
        preview = {"summary": {"indexed_files": 4}, "errors": []}
        self.assertTrue(can_save_inventory_preview(preview, "E:/teste", "E:/teste"))

    def test_denies_missing_or_incomplete_preview(self):
        self.assertFalse(can_save_inventory_preview(None, "E:/teste", "E:/teste"))
        self.assertFalse(can_save_inventory_preview({}, "E:/teste", "E:/teste"))
        self.assertFalse(can_save_inventory_preview(
            {"summary": {}}, "E:/teste", "E:/teste",
        ))

    def test_denies_preview_with_errors(self):
        self.assertFalse(can_save_inventory_preview(
            {"summary": {"indexed_files": 2}, "errors": ["falha"]},
            "E:/teste", "E:/teste",
        ))

    def test_denies_changed_source_and_empty_selection(self):
        preview = {"summary": {"indexed_files": 2}, "errors": []}
        self.assertFalse(can_save_inventory_preview(preview, "D:/nova", "E:/anterior"))
        self.assertFalse(can_save_inventory_preview(preview, "  ", "E:/anterior"))

    def test_denies_malformed_counts_and_errors(self):
        for count in (True, "5", None):
            with self.subTest(count=count):
                self.assertFalse(can_save_inventory_preview(
                    {"summary": {"indexed_files": count}, "errors": []},
                    "E:/teste", "E:/teste",
                ))
        self.assertFalse(can_save_inventory_preview(
            {"summary": {"indexed_files": 2}, "errors": None},
            "E:/teste", "E:/teste",
        ))
