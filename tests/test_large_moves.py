"""Validação real de arquivos maiores que 16 MiB em pastas temporárias."""
import unittest
from unittest.mock import patch

from support import temporary_test_directory
from archivia.agent import FolderCatalogSession
from archivia.move_executor import APPROVAL_PHRASE, move_one_approved, preview_conflict_move
from archivia.queue_move import move_queue_approved


LARGE_BYTES = 20 * 1024 * 1024 + 17


class LargeFileMoveTests(unittest.TestCase):
    def setUp(self):
        self.directory = temporary_test_directory()
        self.temp = self.directory.__enter__()
        self.origin = self.temp / "origem"
        self.dest = self.temp / "destino"
        self.origin.mkdir()
        self.dest.mkdir()
        self.session = FolderCatalogSession(self.origin)

    def tearDown(self):
        self.session.close()
        self.directory.__exit__(None, None, None)

    def large_file(self, name):
        path = self.origin / name
        # Grava o conteúdo diretamente no arquivo, sem alocar 20 MiB em RAM.
        with path.open("wb") as stream:
            stream.truncate(LARGE_BYTES)
            stream.seek(0)
            stream.write(b"ARCHIVIA")
            stream.seek(LARGE_BYTES - 7)
            stream.write(b"FIMTEST")
        return path

    def test_large_video_moves_with_integrity(self):
        source = self.large_file("video.mp4")
        plan = self.session.prepare_recursive_plan(self.dest, "video")
        result = move_one_approved(
            plan, "video.mp4", db_path=self.session._db,
            scan_id=self.session._scan_id, approval=APPROVAL_PHRASE,
        )
        self.assertEqual(result["status"], "movido")
        self.assertEqual(result["bytes"], LARGE_BYTES)
        self.assertFalse(source.exists())
        destination = self.dest / "video.mp4"
        self.assertEqual(destination.stat().st_size, LARGE_BYTES)
        with destination.open("rb") as stream:
            self.assertEqual(stream.read(8), b"ARCHIVIA")
            stream.seek(LARGE_BYTES - 7)
            self.assertEqual(stream.read(7), b"FIMTEST")
        self.assertFalse(list(self.dest.glob(".archivia-stage-*")))

    def test_large_audio_queue_continues_through_safe_collision(self):
        large = self.large_file("audio_a.mp3")
        second = self.origin / "audio_b.mp3"
        second.write_bytes(b"outro-audio")
        third = self.origin / "audio_c.mp3"
        third.write_bytes(b"terceiro-audio")
        plan = self.session.prepare_recursive_plan(self.dest, "audio")
        # A colisão surgiu após o planejamento e será registrada como bloqueio.
        (self.dest / "audio_b.mp3").write_bytes(b"NAO-SOBRESCREVER")
        result = move_queue_approved(
            plan, ["audio_a.mp3", "audio_b.mp3", "audio_c.mp3"],
            db_path=self.session._db, scan_id=self.session._scan_id,
            approval=APPROVAL_PHRASE,
        )
        self.assertEqual(result["moved"], 2)
        self.assertEqual(result["blocked"], 1)
        self.assertEqual(result["pending"], 0)
        self.assertFalse(result["stopped"])
        self.assertEqual((self.dest / "audio_a.mp3").stat().st_size, LARGE_BYTES)
        self.assertEqual((self.dest / "audio_b.mp3").read_bytes(), b"NAO-SOBRESCREVER")
        self.assertTrue(second.exists())
        self.assertFalse(large.exists())
        self.assertFalse(third.exists())

    def test_large_video_conflict_hash_and_alternative(self):
        source = self.large_file("repetido.mp4")
        target = self.dest / "repetido.mp4"
        with target.open("wb") as stream:
            stream.truncate(LARGE_BYTES)
            stream.write(b"outra-versao")
        plan = self.session.prepare_recursive_plan(self.dest, "video")
        preview = preview_conflict_move(
            plan, "repetido.mp4", db_path=self.session._db,
            scan_id=self.session._scan_id,
        )
        self.assertEqual(preview["status"], "conteudo_diferente")
        self.assertEqual(preview["suggested_filename"], "repetido_archivia_1.mp4")
        self.assertTrue(source.exists())
        self.assertEqual(target.stat().st_size, LARGE_BYTES)

    def test_unsafe_failure_stops_queue(self):
        for n in ("a.jpg", "b.jpg", "c.jpg"):
            (self.origin / n).write_bytes(b"teste")
        plan = self.session.prepare_recursive_plan(self.dest, "imagem")
        real_move = move_one_approved
        def fail_second(plan, relative, **kwargs):
            if relative == "b.jpg":
                raise OSError("falha inesperada de armazenamento")
            return real_move(plan, relative, **kwargs)
        with patch("archivia.queue_move.move_one_approved", side_effect=fail_second):
            result = move_queue_approved(
                plan, ["a.jpg", "b.jpg", "c.jpg"],
                db_path=self.session._db, scan_id=self.session._scan_id,
                approval=APPROVAL_PHRASE,
            )
        self.assertEqual(result["moved"], 1)
        self.assertEqual(result["errors"], 1)
        self.assertEqual(result["pending"], 1)
        self.assertTrue(result["stopped"])
        self.assertTrue((self.origin / "c.jpg").exists())


if __name__ == "__main__":
    unittest.main()
