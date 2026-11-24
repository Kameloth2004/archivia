"""Planejamento direto pela aba Início, sem comandos técnicos ao Ollama."""
import unittest

from support import temporary_test_directory
from archivia.agent import FolderCatalogSession


class DirectPreparationTests(unittest.TestCase):
    def setUp(self):
        self.context = temporary_test_directory()
        self.temp = self.context.__enter__()
        self.source = self.temp / "origem"
        self.destination = self.temp / "destino"
        self.source.mkdir()
        self.destination.mkdir()
        (self.source / "a.jpg").write_bytes(b"imagem A")
        (self.source / "b.jpg").write_bytes(b"imagem B")
        (self.destination / "b.jpg").write_bytes(b"arquivo diferente")
        self.session = FolderCatalogSession(self.source)

    def tearDown(self):
        self.session.close()
        self.context.__exit__(None, None, None)

    def test_direct_preparation_has_same_plan_contract_without_changes(self):
        result = self.session.prepare_recursive_plan(self.destination)
        self.assertEqual(result["total_matches"], 2)
        self.assertEqual(result["proposed"], 1)
        self.assertEqual(result["blocked"], 1)
        self.assertTrue(result["complete"])
        self.assertIs(self.session._last_recursive_plan, result)
        self.assertFalse(result["files_modified"])
        self.assertTrue((self.source / "a.jpg").exists())
        self.assertTrue((self.source / "b.jpg").exists())
        self.assertFalse((self.destination / "a.jpg").exists())

    def test_prepare_refreshes_snapshot_after_source_changes(self):
        old = self.session.prepare_recursive_plan(self.destination)
        (self.source / "c.jpg").write_bytes(b"imagem C")
        current = self.session.prepare_recursive_plan(self.destination)
        self.assertEqual(old["total_matches"], 2)
        self.assertEqual(current["total_matches"], 3)
        self.assertEqual(current["proposed"], 2)

    def test_prepare_video_category_ignores_images(self):
        (self.source / "clip.mp4").write_bytes(b"video-teste")
        report = self.session.prepare_recursive_plan(self.destination, "video")
        self.assertEqual(report["category"], "video")
        self.assertEqual(report["total_matches"], 1)
        self.assertEqual(report["proposed"], 1)
        self.assertEqual(report["blocked"], 0)
        self.assertTrue(report["complete"])
        self.assertEqual([row["file"] for row in report["actions"]], ["clip.mp4"])
        self.assertTrue((self.source / "clip.mp4").exists())

    def test_prepare_audio_category_and_refresh_replaces_previous_plan(self):
        (self.source / "musica.mp3").write_bytes(b"audio-teste")
        images = self.session.prepare_recursive_plan(self.destination, "imagem")
        audios = self.session.prepare_recursive_plan(self.destination, "audio")
        self.assertEqual(images["total_matches"], 2)
        self.assertEqual(audios["total_matches"], 1)
        self.assertEqual(audios["category"], "audio")
        self.assertIs(self.session._last_recursive_plan, audios)
        self.assertFalse((self.destination / "musica.mp3").exists())

    def test_prepare_rejects_nonexistent_destination(self):
        with self.assertRaises(ValueError):
            self.session.prepare_recursive_plan(self.temp / "destino-ausente")
        self.assertIsNone(self.session._last_recursive_plan)


if __name__ == "__main__":
    unittest.main()
