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

    def test_analyze_without_destination_is_complete_and_read_only(self):
        (self.source / "filme.mp4").write_bytes(b"video")
        report = self.session.analyze_source()
        self.assertEqual(report["summary"]["indexed_files"], 3)
        self.assertEqual(report["summary"]["by_category"]["imagem"], 2)
        self.assertEqual(report["summary"]["by_category"]["video"], 1)
        self.assertTrue(report["read_only"])
        self.assertFalse(report["files_modified"])
        self.assertIsNone(self.session._last_recursive_plan)

    def test_full_preparation_over_500_keeps_cross_page_collisions(self):
        sub_a = self.source / "subA"
        sub_b = self.source / "subB"
        sub_a.mkdir()
        sub_b.mkdir()
        for n in range(510):
            (sub_a / f"imagem_{n:04d}.jpg").write_bytes(b"a")
        (sub_b / "imagem_0001.jpg").write_bytes(b"diferente")
        report = self.session.prepare_recursive_plan(self.destination, "imagem")
        self.assertEqual(report["total_matches"], 513)
        self.assertEqual(report["examined"], 513)
        self.assertTrue(report["complete"])
        self.assertEqual(report["pending"], 0)
        # A V2 bloqueia ambas as origens com o mesmo nome-base,
        # mesmo quando a colisão atravessa páginas do catálogo.
        self.assertEqual(report["blocked"], 3)
        self.assertEqual(report["proposed"], 510)
        self.assertEqual(report["blocked_by_reason"]["destino_ja_existe"], 1)
        self.assertEqual(report["blocked_by_reason"]["nome_repetido_entre_subpastas"], 2)
        duplicate_actions = [action for action in report["actions"]
                             if action["file"].endswith("imagem_0001.jpg")]
        self.assertEqual(len(duplicate_actions), 2)
        self.assertTrue(all(action["status"] == "bloqueado"
                            and action["reason"] == "nome_repetido_entre_subpastas"
                            for action in duplicate_actions))
        self.assertEqual(len(report["actions"]), 513)
        self.assertTrue((sub_a / "imagem_0001.jpg").exists())
        self.assertTrue((sub_b / "imagem_0001.jpg").exists())

    def test_realistic_library_counts_complete_all_three_categories(self):
        for category, extension, count in (
            ("imagem", ".jpg", 1344),
            ("video", ".mp4", 648),
            ("audio", ".mp3", 652),
        ):
            folder = self.source / category
            folder.mkdir()
            for index in range(count):
                (folder / f"item_{index:04d}{extension}").write_bytes(b"x")
        analyzed = self.session.analyze_source()
        self.assertEqual(analyzed["summary"]["indexed_files"], 2646)
        for category, expected in (("imagem", 1346), ("video", 648), ("audio", 652)):
            plan = self.session.prepare_recursive_plan(self.destination, category)
            self.assertEqual(plan["total_matches"], expected)
            self.assertEqual(plan["examined"], expected)
            self.assertEqual(plan["pending"], 0)
            self.assertTrue(plan["complete"])
            self.assertFalse(plan["truncated"])
            self.assertFalse(plan["files_modified"])
            self.assertEqual(len(plan["actions"]), expected)

    def test_prepare_rejects_nonexistent_destination(self):
        with self.assertRaises(ValueError):
            self.session.prepare_recursive_plan(self.temp / "destino-ausente")
        self.assertIsNone(self.session._last_recursive_plan)


if __name__ == "__main__":
    unittest.main()
