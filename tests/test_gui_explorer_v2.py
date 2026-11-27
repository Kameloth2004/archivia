"""TEST-ONLY: explorador da Biblioteca não modifica arquivos nem snapshots."""
from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from support import temporary_test_directory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QImage
    from PySide6.QtWidgets import QApplication
    from archivia.gui_explorer import (
        ExplorerPanel, safe_directory, _BATCH_SIZE,
        _ThumbnailEvents, _ThumbnailTask,
    )
    from archivia.gui import ArchivIAWindow
except ImportError:
    QApplication = None


@unittest.skipIf(QApplication is None, "PySide6 opcional não instalado")
class ExplorerV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.context = temporary_test_directory()
        self.tmp = self.context.__enter__()
        self.root = self.tmp / "origem"
        self.root.mkdir()
        self.child = self.root / "subpasta"
        self.child.mkdir()
        (self.root / "imagem.jpg").write_bytes(b"IMAGEM_FICTICIA")
        (self.root / "documento.pdf").write_bytes(b"PDF_FICTICIO")
        (self.child / "nota.txt").write_text("fixture", encoding="utf-8")
        self.panel = ExplorerPanel()

    def tearDown(self):
        self.panel.set_active_folder(None)
        self.panel.close()
        self.context.__exit__(None, None, None)

    def test_directory_guard_denies_outside_and_symlinks(self):
        self.assertEqual(safe_directory(self.root, self.root), self.root.resolve())
        self.assertEqual(safe_directory(self.root, self.child), self.child.resolve())
        self.assertIsNone(safe_directory(self.root, self.tmp))
        self.assertIsNone(safe_directory(self.root, self.root / ".."))
        alias = self.root / "atalho"
        try:
            alias.symlink_to(self.child, target_is_directory=True)
        except (OSError, NotImplementedError):
            return  # Windows sem permissão para criar symlink
        self.assertIsNone(safe_directory(self.root, alias))
        self.assertIsNone(safe_directory(self.root, alias / "nota.txt"))

    def test_root_lists_only_direct_children_and_navigation(self):
        self.panel.set_active_folder(self.root)
        self.assertEqual(self.panel.current_directory, self.root.resolve())
        self.assertEqual(self.panel.files.count(), 3)
        labels = {self.panel.files.item(i).text() for i in range(3)}
        self.assertEqual(labels, {"subpasta", "imagem.jpg", "documento.pdf"})
        folder_item = next(self.panel.files.item(i) for i in range(3)
                           if self.panel.files.item(i).text() == "subpasta")
        self.panel._open_item(folder_item)
        self.assertEqual(self.panel.current_directory, self.child.resolve())
        self.assertEqual(self.panel.files.count(), 1)
        self.panel._go_up()
        self.assertEqual(self.panel.current_directory, self.root.resolve())
        self.assertTrue((self.root / "imagem.jpg").is_file())

    def test_selection_properties_and_safe_double_click(self):
        self.panel.set_active_folder(self.root)
        item = next(self.panel.files.item(i) for i in range(self.panel.files.count())
                    if self.panel.files.item(i).text() == "documento.pdf")
        self.panel.files.setCurrentItem(item)
        self.panel._show_properties()
        self.assertIn("documento.pdf", self.panel.properties_text.text())
        self.assertIn("Modificado:", self.panel.properties_text.text())
        # Duplo clique em arquivo agora abre diálogo modal: simular sua
        # abertura evita bloquear a execução automatizada da suíte.
        with patch("archivia.gui_explorer.FilePreviewDialog") as preview:
            self.panel._open_item(item)
        self.assertEqual(preview.call_count, 1)
        self.assertTrue(preview.return_value.showFullScreen.called)
        self.assertTrue(preview.return_value.exec.called)
        self.assertEqual(self.panel.current_directory, self.root.resolve())
        self.assertTrue((self.root / "documento.pdf").is_file())

    def test_thumbnail_result_updates_only_current_file_generation(self):
        self.panel.set_active_folder(self.root)
        item = next(self.panel.files.item(i) for i in range(self.panel.files.count())
                    if self.panel.files.item(i).text() == "imagem.jpg")
        path = item.data(Qt.ItemDataRole.UserRole)
        meta = item.data(Qt.ItemDataRole.UserRole + 1)
        picture = QImage(24, 24, QImage.Format.Format_RGB32)
        picture.fill(Qt.GlobalColor.red)
        original_key = item.icon().cacheKey()
        self.panel._apply_thumbnail(
            path, meta[1], meta[2], self.panel._generation, picture
        )
        self.assertNotEqual(item.icon().cacheKey(), original_key)
        updated_key = item.icon().cacheKey()
        self.panel._apply_thumbnail(
            path, meta[1], meta[2], self.panel._generation - 1, picture
        )
        self.assertEqual(item.icon().cacheKey(), updated_key)

    def test_real_png_thumbnail_preserves_nanosecond_timestamp_in_signal(self):
        """TEST-ONLY: decodificação real e sinal sem conversão para int32."""
        path = self.root / "miniatura_real.png"
        picture = QImage(32, 24, QImage.Format.Format_RGB32)
        picture.fill(Qt.GlobalColor.green)
        self.assertTrue(picture.save(str(path), "PNG"))
        st = path.stat()
        self.assertGreater(st.st_mtime_ns, 2**31)

        self.panel.set_active_folder(self.root)
        item = next(
            self.panel.files.item(i) for i in range(self.panel.files.count())
            if self.panel.files.item(i).text() == "miniatura_real.png"
        )
        previous_icon = item.icon().cacheKey()
        received = []
        events = _ThumbnailEvents(self.panel)
        events.ready.connect(lambda *args: received.append(args))
        task = _ThumbnailTask(
            str(path), st.st_size, st.st_mtime_ns, self.panel._generation, events
        )
        task.run()
        self.app.processEvents()
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0][2], st.st_mtime_ns)
        self.assertFalse(received[0][4].isNull())
        self.panel._apply_thumbnail(*received[0])
        self.assertNotEqual(item.icon().cacheKey(), previous_icon)

    def test_navigation_denies_leaving_active_folder(self):
        self.panel.set_active_folder(self.root)
        self.panel._open_directory(self.tmp)
        self.assertEqual(self.panel.current_directory, self.root.resolve())
        self.panel._go_up()
        self.assertEqual(self.panel.current_directory, self.root.resolve())

    def test_listing_is_batched_and_refresh_is_readonly(self):
        for index in range(_BATCH_SIZE + 6):
            (self.root / f"arquivo_{index:04d}.txt").write_bytes(b"TESTE")
        self.panel.set_active_folder(self.root)
        self.assertEqual(self.panel.files.count(), _BATCH_SIZE)
        self.assertTrue(self.panel.more_button.isVisible() or self.panel._cursor is not None)
        self.panel._append_batch()
        self.assertEqual(self.panel.files.count(), _BATCH_SIZE + 9)
        self.panel.refresh()
        self.assertEqual(self.panel.files.count(), _BATCH_SIZE)
        self.assertTrue((self.root / "arquivo_0000.txt").is_file())

    def test_loading_more_schedules_layout_and_viewport_repaint(self):
        for index in range(_BATCH_SIZE + 3):
            (self.root / f"nova_{index:04d}.png").write_bytes(b"fixture")
        self.panel.set_active_folder(self.root)
        self.app.processEvents()
        self.assertEqual(self.panel.files.count(), _BATCH_SIZE)
        # O temporizador é one-shot: pode já ter disparado ao retornar
        # de processEvents(). Verificamos a solicitação de redesenho,
        # não o estado transitório isActive() após a execução.
        with patch.object(
            self.panel, "_schedule_viewport_repaint",
            wraps=self.panel._schedule_viewport_repaint,
        ) as request_repaint:
            self.panel._append_batch()
            self.assertEqual(self.panel.files.count(), _BATCH_SIZE + 6)
            self.app.processEvents()
            self.assertGreaterEqual(request_repaint.call_count, 1)
        self.assertEqual(
            self.panel.files.verticalScrollBarPolicy(),
            Qt.ScrollBarPolicy.ScrollBarAsNeeded,
        )

    def test_icon_replacement_requests_coalesced_repaint(self):
        self.panel.set_active_folder(self.root)
        item = next(self.panel.files.item(i) for i in range(self.panel.files.count())
                    if self.panel.files.item(i).text() == "imagem.jpg")
        path = item.data(Qt.ItemDataRole.UserRole)
        meta = item.data(Qt.ItemDataRole.UserRole + 1)
        picture = QImage(24, 24, QImage.Format.Format_RGB32)
        picture.fill(Qt.GlobalColor.blue)
        self.assertFalse(self.panel._thumbnail_repaint_timer.isActive())
        self.panel._apply_thumbnail(
            path, meta[1], meta[2], self.panel._generation, picture,
        )
        self.assertTrue(self.panel._thumbnail_repaint_timer.isActive())
        self.panel._apply_thumbnail(
            path, meta[1], meta[2], self.panel._generation, picture,
        )
        self.assertTrue(self.panel._thumbnail_repaint_timer.isActive())
        self.panel._repaint_thumbnail_viewport()

    def test_folder_switch_clears_previous_items_and_thumbnail_cache(self):
        other = self.tmp / "outra"
        other.mkdir()
        (other / "arquivo.csv").write_bytes(b"coluna")
        self.panel.set_active_folder(self.root)
        self.panel._open_directory(self.child)
        self.panel.set_active_folder(other)
        self.assertEqual(self.panel.current_directory, other.resolve())
        self.assertEqual(self.panel.files.count(), 1)
        self.assertEqual(self.panel.files.item(0).text(), "arquivo.csv")
        self.panel.set_active_folder(None)
        self.assertIsNone(self.panel.current_directory)
        self.assertEqual(self.panel.files.count(), 0)

    def test_gui_explorer_tracks_active_folder_without_sqlite_writes(self):
        window = ArchivIAWindow()
        try:
            self.assertEqual(window.library_sections.tabText(0), "Explorador")
            self.assertEqual(window.library_sections.tabText(1), "Acervo")
            self.assertEqual(window.library_sections.tabText(2), "Inventário")
            window.folder.setText(str(self.root))
            self.assertEqual(window.explorer.active_root, self.root.resolve())
            self.assertEqual(window.explorer.files.count(), 3)
            window._clear_active_folder()
            self.assertIsNone(window.explorer.active_root)
            self.assertEqual(window.explorer.files.count(), 0)
            self.assertIsNone(window._worker)
        finally:
            window.close()


if __name__ == "__main__":
    unittest.main()
