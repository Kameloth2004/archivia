"""TEST-ONLY: leitura explícita de metadados sem escrita em arquivos reais."""
from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from support import temporary_test_directory
from archivia.metadata import read_file_metadata
from archivia.metadata.reader import format_metadata_report

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
    def test_image_exposes_every_recognized_exif_including_user_comment(self):
        with temporary_test_directory() as base:
            path = base / "imagem_exif.jpg"
            image = Image.new("RGB", (48, 32), (40, 80, 120))
            exif = Image.Exif()
            exif[271] = "Fabricante TEST-ONLY"
            exif[272] = "Câmera de teste"
            exif[37510] = b"private user comment test data"
            exif[65000] = "Tag profissional desconhecida"
            image.save(path, "JPEG", exif=exif)
            before = path.read_bytes()
            with patch("archivia.metadata.reader.available_exiftool", return_value=None):
                info = read_file_metadata(path)
            fields = dict(info["fields"])
            self.assertEqual(fields["Dimensões"], "48 × 32 pixels")
            self.assertEqual(fields["Make"], "Fabricante TEST-ONLY")
            self.assertEqual(fields["Tag_65000"], "Tag profissional desconhecida")
            self.assertIn("hex:", fields["UserComment"])
            self.assertIn("70 72 69 76 61 74 65", fields["UserComment"])
            self.assertEqual(path.read_bytes(), before)

    @unittest.skipIf(Image is None, "Pillow opcional não instalado")
    def test_jpeg_exif_binary_block_is_not_duplicated_in_main_report(self):
        with temporary_test_directory() as base:
            path = base / "camera.jpg"
            picture = Image.new("RGB", (120, 80), (32, 64, 128))
            exif = Image.Exif()
            exif[271] = "samsung"
            exif[272] = "SM-A217M"
            exif[306] = "2024:10:25 21:39:53"
            exif[36864] = b"0230"
            picture.save(path, "JPEG", exif=exif)
            before = path.read_bytes()
            with patch("archivia.metadata.reader.available_exiftool", return_value=None):
                data = read_file_metadata(path)
            report = format_metadata_report(data)
            self.assertIn("Make: samsung", report)
            self.assertIn("Model: SM-A217M", report)
            self.assertIn("EXIF original (binário)", report)
            self.assertNotIn("exif: hex:", report.lower())
            self.assertNotIn("hex: 45 78 69 66", report)
            self.assertIn("ExifVersion: 0230", report)
            exif_raw = [
                part for part in data.get("raw_sections", [])
                if "exif" in part["name"].lower() and "data" in part
            ]
            self.assertEqual(len(exif_raw), 1)
            self.assertTrue(exif_raw[0]["data"].startswith(b"Exif\x00\x00"))
            self.assertEqual(path.read_bytes(), before)

    def test_exiftool_all_tags_are_displayed_even_in_documents(self):
        with temporary_test_directory() as base:
            document = base / "relatorio.pdf"
            document.write_bytes(b"PDF fixture")
            groups = [
                {"name": "XMP", "fields": [
                    ("Creator", "Autor profissional"),
                    ("GeoLatitude", "-27.5954"),
                    ("Unknown_001", "Identificador customizado"),
                ]},
                {"name": "EXIF", "fields": [
                    ("GPSLatitude", "27 deg 35 min S"),
                    ("UserComment", "Campo privado visível"),
                ]},
            ]
            with (
                patch("archivia.metadata.reader.available_exiftool", return_value="exiftool"),
                patch("archivia.metadata.reader.extract_exiftool", return_value=groups) as reader,
            ):
                info = read_file_metadata(document)
            reader.assert_called_once_with(document, "exiftool")
            self.assertIn("GPSLatitude", dict(info["fields"]))
            self.assertEqual(dict(info["fields"])["UserComment"], "Campo privado visível")
            self.assertIn("Autor profissional", format_metadata_report(info))
            self.assertIn("── XMP ──", format_metadata_report(info))
            self.assertIn("── EXIF ──", format_metadata_report(info))

    def test_exiftool_unavailable_on_nonimage_provides_explanatory_fallback(self):
        with temporary_test_directory() as base:
            document = base / "arquivo.docx"
            document.write_bytes(b"fixture")
            with patch("archivia.metadata.reader.available_exiftool", return_value=None):
                info = read_file_metadata(document)
            self.assertEqual(info["source"], "Sistema de arquivos")
            self.assertIn("ExifTool", info["note"])
            self.assertIn("não possui leitor", info["note"])

    def test_binary_values_are_described_not_hidden_by_privacy(self):
        from archivia.metadata.reader import _display
        raw = b"SECRET" + bytes(range(250)) * 3
        displayed = _display(raw)
        self.assertIn("53 45 43 52 45 54", displayed)
        self.assertIn("truncado", displayed)
        self.assertIn(str(len(raw)), displayed)


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
