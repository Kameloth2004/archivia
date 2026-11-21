"""TEST-ONLY: paginação de prévias sintéticas, sem arquivos pessoais nem Qt."""
import unittest

from archivia.preview import preview_inventory_page
from archivia.inventory import inventory
from support import temporary_test_directory


class PreviewTests(unittest.TestCase):
    def test_pages_filter_and_no_files_modified(self):
        with temporary_test_directory() as tmp:
            root = tmp / "midias"
            root.mkdir()
            for i in range(7):
                (root / f"foto{i:02d}.jpg").write_bytes(b"foto")
            (root / "video.mp4").write_bytes(b"video")
            result = inventory(root)
            first = preview_inventory_page(result, page=1, page_size=3)
            second = preview_inventory_page(result, page=2, page_size=3)
            last = preview_inventory_page(result, page=3, page_size=3)
            video = preview_inventory_page(result, category="video")
            images = preview_inventory_page(result, category="imagem", page_size=3)
            self.assertEqual(first["count"], 8)
            self.assertEqual(first["pages"], 3)
            self.assertEqual([len(p["files"]) for p in (first, second, last)], [3, 3, 2])
            self.assertEqual(video["count"], 1)
            self.assertEqual(video["files"][0]["path"], "video.mp4")
            self.assertEqual(images["count"], 7)
            self.assertEqual(images["pages"], 3)
            self.assertEqual((root / "foto00.jpg").read_bytes(), b"foto")
            self.assertEqual(len(result["files"]), 8)

    def test_validation(self):
        with temporary_test_directory() as tmp:
            root = tmp / "midias"
            root.mkdir()
            result = inventory(root)
            for bad_page in (0, True):
                with self.assertRaises(ValueError):
                    preview_inventory_page(result, page=bad_page)
            for bad_size in (0, 101, True):
                with self.assertRaises(ValueError):
                    preview_inventory_page(result, page_size=bad_size)
            # "outro" é categoria válida no inventário universal.
            valid = preview_inventory_page(result, category="outro")
            self.assertEqual(valid["count"], 0)
            with self.assertRaises(ValueError):
                preview_inventory_page(result, category="categoria_inexistente")

    def test_empty_category_and_beyond_last_page(self):
        with temporary_test_directory() as tmp:
            root = tmp / "midias"
            root.mkdir()
            (root / "foto.jpg").write_bytes(b"abc")
            result = inventory(root)
            empty = preview_inventory_page(result, category="video")
            beyond = preview_inventory_page(result, category="imagem", page=2)
            self.assertEqual(empty["count"], 0)
            self.assertEqual(empty["files"], [])
            self.assertEqual(beyond["count"], 1)
            self.assertEqual(beyond["files"], [])


if __name__ == "__main__":
    unittest.main()
