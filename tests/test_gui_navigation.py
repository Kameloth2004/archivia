"""Regressões do fluxo pós-catalogação: somente dados sintéticos."""
import unittest

from archivia.gui_navigation import find_saved_snapshot


class SavedSnapshotNavigationTests(unittest.TestCase):
    def test_finds_exact_snapshot_not_simply_newest(self):
        history = [
            {"id": 18, "root": "D:/OUTRA"},
            {"id": 17, "root": "E:/ORIGEM"},
            {"id": 16, "root": "C:/ANTERIOR"},
        ]
        self.assertTrue(find_saved_snapshot(history, 17))
        self.assertFalse(find_saved_snapshot(history, 19))

    def test_rejects_invalid_snapshot_ids(self):
        for invalid in (0, -1, True, None, "17"):
            with self.subTest(value=invalid):
                with self.assertRaises(ValueError):
                    find_saved_snapshot([], invalid)

    def test_empty_history_does_not_falsely_confirm(self):
        self.assertFalse(find_saved_snapshot([], 4))

    def test_ignores_unrelated_history_rows(self):
        self.assertFalse(find_saved_snapshot([None, "invalid", {"root": "E:/ORIGEM"}], 7))
