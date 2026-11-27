"""TEST-ONLY: leitura explícita de metadados sem escrita em arquivos reais."""
from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from support import temporary_test_directory
from archivia.metadata import read_file_metadata

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PIL import Image
except ImportError:
    Image = None

try:
    from PySide6.QtWidgets import QApplication
    from archivia.gui_explorer import ExplorerPanel, _MetadataTask, _MetadataEvents
except ImportError:
    QApplication = None


class MetadataReaderTests(unittest.TestCase):
    def test_common_properties_for_any_regular_file_without_content_reading(self):
        with temporary_test_directory() as base:
            file = base / "codigo.py"
            content = b"print('TESTE')\n"
            file.write_bytes(content)
            before = file.read_bytes()
            info = read_file_metadata(file)
            self.assertEqual(info["name"], file.name)
            self.assertEqual(info["source"], "Sistema de arquivos")
            self.assertIn("não possui leitor", info["note"])
            self.assertEqual(file.read_bytes(), before)

    def test_missing_or_non_regular_file_is_rejected(self):
        with temporary_test_directory() as base:
            with self.assertRaises((OSError, ValueError)):
                read_file_metadata(base / "nao_existe.jpg")
            with self.assertRaises(ValueError):
                read_file_metadata(base)

    @unittest.skipIf(Image is None, "Pillow opcional não instalado")
    def test_image_dimensions_and_allowlisted_exif_without_gps(self):
        with temporary_test_directory() as base:
            path = base / "imagem_exif.jpg"
            image = Image.new("RGB", (48, 32), (40, 80, 120))
            exif = Image.Exif()
            exif[271] = "Fabricante TEST-ONLY"  # Make
            exif[272] = "Câmera de teste"      # Model
            exif[37510] = b"private user comment test data"  # UserComment não exibido
            image.save(path, "JPEG", exif=exif)
            before = path.read_bytes()
            info = read_file_metadata(path)
            fields = dict(info["fields"])
            self.assertEqual(fields["Dimensões"], "48 × 32 pixels")
            self.assertEqual(fields["Fabricante"], "Fabricante TEST-ONLY")
            self.assertNotIn("GPS", str(info["fields"]).upper())
            self.assertNotIn("private user comment", str(info["fields"]).lower())
            self.assertEqual(path.read_bytes(), before)


@unittest.skipIf(QApplication is None, "PySide6 opcional não instalado")
class ExplorerMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.context = temporary_test_directory()
        self.base = self.context.__enter__()
        self.root = self.base / "origem"
        self.root.mkdir()
        (self.root / "texto.txt").write_text("TESTE", encoding="utf-8")
        self.panel = ExplorerPanel()
        self.panel.set_active_folder(self.root)

    def tearDown(self):
        self.panel.close()
        self.context.__exit__(None, None, None)

    def test_selection_does_not_read_internal_metadata(self):
        with patch("archivia.gui_explorer.read_file_metadata") as reader:
            item = self.panel.files.item(0)
            self.panel.files.setCurrentItem(item)
            self.assertTrue(self.panel.verify_metadata_button.isEnabled())
            self.assertIn("não consultados", self.panel.metadata_status.text())
            reader.assert_not_called()
            self.assertEqual(self.panel.metadata_details.text(), "")
            self.assertFalse(self.panel.edit_metadata_button.isEnabled())

    def test_explicit_button_starts_background_task_and_displays_result(self):
        item = self.panel.files.item(0)
        self.panel.files.setCurrentItem(item)
        with patch.object(self.panel, "_start_metadata_task") as start:
            self.panel.verify_metadata_button.click()
        self.assertEqual(start.call_count, 1)
        task = start.call_args.args[0]
        self.assertIsInstance(task, _MetadataTask)
        self.assertFalse(self.panel.verify_metadata_button.isEnabled())
        self.assertIn("Lendo metadados", self.panel.metadata_status.text())
        self.panel._apply_metadata(
            task.path, task.size, task.modified_ns, task.generation,
            {"fields": [("Tipo", "Texto")], "source": "Sistema de arquivos",
             "note": "Leitura segura."},
        )
        self.assertIn("Tipo: Texto", self.panel.metadata_details.text())
        self.assertTrue(self.panel.verify_metadata_button.isEnabled())

    def test_selection_change_discards_stale_metadata(self):
        other = self.root / "segundo.txt"
        other.write_text("SEGUNDO", encoding="utf-8")
        self.panel.refresh()
        item = self.panel.files.item(0)
        self.panel.files.setCurrentItem(item)
        with patch.object(self.panel, "_start_metadata_task") as start:
            self.panel.verify_metadata_button.click()
        task = start.call_args.args[0]
        self.panel.files.setCurrentItem(self.panel.files.item(1))
        self.panel._apply_metadata(
            task.path, task.size, task.modified_ns, task.generation,
            {"fields": [("Autor", "ANTIGO")]},
        )
        self.assertNotIn("ANTIGO", self.panel.metadata_details.text())

    def test_task_reads_only_when_run_and_validates_file_identity(self):
        file = self.root / "texto.txt"
        info = file.stat()
        received = []
        events = _MetadataEvents(self.panel)
        events.ready.connect(lambda *args: received.append(args))
        task = _MetadataTask(str(file), info.st_size, info.st_mtime_ns, 2, events)
        task.run()
        self.app.processEvents()
        self.assertEqual(len(received), 1)
        self.assertIn("fields", received[0][4])
        self.assertEqual(file.read_text(encoding="utf-8"), "TESTE")
        # Identidade obsoleta: não ler o conteúdo interno.
        received.clear()
        with patch("archivia.gui_explorer.read_file_metadata") as reader:
            _MetadataTask(str(file), info.st_size + 1, info.st_mtime_ns, 3, events).run()
            reader.assert_not_called()
        self.app.processEvents()
        self.assertIn("error", received[0][4])


if __name__ == "__main__":
    unittest.main()
