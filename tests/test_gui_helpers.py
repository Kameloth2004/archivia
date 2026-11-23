"""TEST-ONLY: contratos puros da GUI, sem PySide6."""
import unittest

from archivia.gui_helpers import validate_gui_result


class GUIHelpersTests(unittest.TestCase):
    def test_summary_empty_snapshot_is_valid(self):
        validate_gui_result("summary", {"scan_id": None})

    def test_summary_requires_all_counts_if_catalog_exists(self):
        with self.assertRaisesRegex(ValueError, "indexed_files"):
            validate_gui_result("summary", {"scan_id": 1})
        validate_gui_result("summary", {
            "scan_id": 1, "indexed_files": 2, "media_files": 2,
            "bytes_media": 42, "by_category": {"imagem": 2},
        })

    def test_preview_requires_nested_summary(self):
        with self.assertRaisesRegex(ValueError, "by_category"):
            validate_gui_result("inventory_preview", {
                "root": "synthetic", "errors": [], "files": [],
                "summary": {"indexed_files": 1, "media_files": 1},
            })

    def test_catalog_page_requires_iso_field_in_every_file(self):
        with self.assertRaisesRegex(ValueError, "modified_utc"):
            validate_gui_result("catalog_page", {
                "page": 1, "pages": 1, "count": 1, "scan_id": 1,
                "files": [{"relative_path": "fake.jpg", "category": "imagem",
                           "extension": ".jpg", "size_bytes": 10}],
            })

    def test_rejects_unknown_mode_and_wrong_shape(self):
        with self.assertRaisesRegex(ValueError, "não autorizado"):
            validate_gui_result("unknown", {})
        with self.assertRaisesRegex(ValueError, "esperada lista"):
            validate_gui_result("history", {})
        with self.assertRaisesRegex(ValueError, "faltam campos"):
            validate_gui_result("date_plan", {"actions": []})

    def test_accepts_minimal_valid_date_plan_and_history(self):
        validate_gui_result("date_plan", {
            "actions": [{"file": "fake.jpg", "status": "proposto"}],
            "selected": 1, "blocked": 0, "truncated": False,
            "scan_id": 1, "total_matches": 1,
        })
        validate_gui_result("history", [{
            "id": 1, "scanned_utc": "2026-11-23T00:00:00+00:00",
            "indexed_files": 1, "root": "synthetic",
        }])
