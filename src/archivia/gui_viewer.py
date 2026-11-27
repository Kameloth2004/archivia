"""Visualizador local em tela cheia: zoom e propriedades, somente leitura.

Nenhum arquivo é executado. Miniaturas ampliadas usam decodificação Qt com
limites de memória; metadados internos só são lidos após clique explícito.
Formatos sem visualizador próprio continuam com propriedades e metadados.
"""
from __future__ import annotations

from datetime import datetime
import mimetypes
import os
from pathlib import Path
import stat

from PySide6.QtCore import QObject, QRunnable, QThreadPool, QSize, Qt, QTimer, Signal
from PySide6.QtGui import (
    QColor, QBrush, QImage, QImageReader, QPainter, QPixmap, QKeySequence,
    QShortcut,
)
from PySide6.QtWidgets import (
    QDialog, QFrame, QGraphicsPixmapItem, QGraphicsScene, QGraphicsView,
    QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QSplitter, QStackedWidget,
    QVBoxLayout, QWidget, QSizePolicy,
)

from .metadata import read_file_metadata


IMAGE_EXTENSIONS = frozenset({
    ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff", ".avif",
})
PREVIEW_MAX_BYTES = 80 * 1024 * 1024
PREVIEW_MAX_SOURCE_PIXELS = 100_000_000
PREVIEW_MAX_SIDE = 4096


def _junction(path: Path) -> bool:
    return bool(getattr(os.path, "isjunction", lambda _p: False)(path))


def verified_file(root: Path, file: Path, expected: tuple[int, int]) -> os.stat_result:
    """Valida escopo, links e identidade antes de qualquer leitura interna."""
    base = root.expanduser().absolute()
    candidate = file.expanduser().absolute()
    relative = candidate.relative_to(base)
    current = base
    if base.is_symlink() or _junction(base):
        raise ValueError("Pasta de origem não permitida.")
    for part in relative.parts:
        if part == "..":
            raise ValueError("Arquivo fora da pasta ativa.")
        current = current / part
        if current.is_symlink() or _junction(current):
            raise ValueError("Atalho simbólico não permitido.")
    current.resolve(strict=True).relative_to(base.resolve(strict=True))
    info = candidate.stat(follow_symlinks=False)
    if not stat.S_ISREG(info.st_mode):
        raise ValueError("A visualização aceita apenas arquivos regulares.")
    if (info.st_size, info.st_mtime_ns) != expected:
        raise ValueError("O arquivo mudou desde a listagem. Atualize o Explorador.")
    return info


class _ViewerEvents(QObject):
    image_ready = Signal(int, object)
    metadata_ready = Signal(int, object)


class _ImageLoad(QRunnable):
    """Decodifica um único arquivo em thread; QPixmap fica na thread de GUI."""

    def __init__(self, root: Path, file: Path, expected: tuple[int, int],
                 generation: int, events: _ViewerEvents) -> None:
        super().__init__()
        self.root, self.file = root, file
        self.expected, self.generation, self.events = expected, generation, events

    def run(self) -> None:
        try:
            info = verified_file(self.root, self.file, self.expected)
            if info.st_size > PREVIEW_MAX_BYTES:
                raise ValueError("Arquivo acima do limite de 80 MiB para prévia ampliada.")
            reader = QImageReader(str(self.file))
            reader.setAutoTransform(True)
            source = reader.size()
            if (not source.isValid() or source.width() <= 0 or source.height() <= 0
                    or source.width() * source.height() > PREVIEW_MAX_SOURCE_PIXELS):
                raise ValueError("Dimensões indisponíveis ou acima do limite de segurança.")
            size = source.scaled(
                QSize(PREVIEW_MAX_SIDE, PREVIEW_MAX_SIDE),
                Qt.AspectRatioMode.KeepAspectRatio,
            )
            reader.setScaledSize(size)
            image = reader.read()
            if image.isNull():
                raise ValueError("O decodificador não conseguiu abrir esta imagem.")
            verified_file(self.root, self.file, self.expected)
            payload = {"image": image, "original": (source.width(), source.height())}
        except Exception as exc:
            payload = {"error": f"Não foi possível visualizar: {type(exc).__name__} — {str(exc)[:160]}"}
        self.events.image_ready.emit(self.generation, payload)


class _MetadataLoad(QRunnable):
    """Lê metadados exclusivamente sob comando Verificar metadados."""

    def __init__(self, root: Path, file: Path, expected: tuple[int, int],
                 generation: int, events: _ViewerEvents) -> None:
        super().__init__()
        self.root, self.file = root, file
        self.expected, self.generation, self.events = expected, generation, events

    def run(self) -> None:
        try:
            verified_file(self.root, self.file, self.expected)
            payload = read_file_metadata(self.file)
            verified_file(self.root, self.file, self.expected)
        except Exception as exc:
            payload = {"error": f"Falha na leitura: {type(exc).__name__} — {str(exc)[:160]}"}
        self.events.metadata_ready.emit(self.generation, payload)


class ZoomImageView(QGraphicsView):
    """Zoom pela roda do mouse e botões, arraste para mover."""

    zoom_changed = Signal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self._pixmap_item = QGraphicsPixmapItem()
        self._scene.addItem(self._pixmap_item)
        self._has_image = False
        self._fit_mode = True
        self._zoom_relative = 1.0
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setBackgroundBrush(QBrush(QColor("#171d26")))
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        self.setTransformationAnchor(
            QGraphicsView.ViewportAnchor.AnchorUnderMouse,
        )
        self.setResizeAnchor(
            QGraphicsView.ViewportAnchor.AnchorViewCenter,
        )
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

    def set_image(self, image: QImage) -> None:
        self._pixmap_item.setPixmap(QPixmap.fromImage(image))
        self._scene.setSceneRect(self._pixmap_item.boundingRect())
        self._has_image = not image.isNull()
        self.fit_image()

    def fit_image(self) -> None:
        if not self._has_image:
            return
        self._fit_mode = True
        self._zoom_relative = 1.0
        self.resetTransform()
        self.fitInView(
            self._pixmap_item, Qt.AspectRatioMode.KeepAspectRatio,
        )
        self._report_zoom()

    def actual_size(self) -> None:
        if not self._has_image:
            return
        self._fit_mode = False
        self.resetTransform()
        self._report_zoom()

    def zoom_by(self, multiplier: float) -> None:
        if not self._has_image:
            return
        if not (0.2 <= self._zoom_relative * multiplier <= 8.0):
            return
        self._zoom_relative *= multiplier
        self._fit_mode = False
        self.scale(multiplier, multiplier)
        self._report_zoom()

    def _report_zoom(self) -> None:
        self.zoom_changed.emit(round(self.transform().m11() * 100))

    def wheelEvent(self, event) -> None:
        if not self._has_image:
            super().wheelEvent(event)
            return
        delta = event.angleDelta().y()
        if delta:
            self.zoom_by(1.25 if delta > 0 else 0.8)
            event.accept()
        else:
            super().wheelEvent(event)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._has_image and self._fit_mode:
            self.fit_image()


class FilePreviewDialog(QDialog):
    """Tela cheia fechável por X/Esc, sem interferir na seleção do Explorador."""

    def __init__(self, root: Path, file: Path, expected: tuple[int, int],
                 parent=None) -> None:
        super().__init__(parent)
        self.root, self.file, self.expected = root, file, expected
        self.setWindowTitle(f"ArchivIA — {file.name}")
        self.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint,
        )
        self.setModal(True)
        self._generation = 1
        self._closed = False
        self._image_loaded = False
        # Sem parent: tarefas ainda em execução podem emitir após fechar;
        # a desconexão automática do Qt impede atualizar a janela destruída.
        self._events = _ViewerEvents()
        self._events.image_ready.connect(self._image_loaded_result)
        self._events.metadata_ready.connect(self._metadata_loaded_result)
        self._pool = QThreadPool.globalInstance()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 8, 10, 10)
        outer.setSpacing(8)
        header = QHBoxLayout()
        self.title_label = QLabel(f"ArchivIA  |  {file.name}")
        self.title_label.setObjectName("archiviaPreviewTitle")
        self.title_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        header.addWidget(self.title_label, 1)
        self.close_button = QPushButton("✕")
        self.close_button.setAccessibleName("Fechar visualização")
        self.close_button.setObjectName("archiviaPreviewClose")
        self.close_button.setFixedSize(44, 38)
        self.close_button.clicked.connect(self.reject)
        header.addWidget(self.close_button)
        outer.addLayout(header)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        controls = QHBoxLayout()
        self.zoom_out_button = QPushButton("−  Lupa −")
        self.zoom_in_button = QPushButton("+  Lupa +")
        self.fit_button = QPushButton("Ajustar à tela")
        self.actual_button = QPushButton("1:1")
        self.zoom_label = QLabel("—")
        for button in (
            self.zoom_out_button, self.zoom_in_button,
            self.fit_button, self.actual_button,
        ):
            button.setEnabled(False)
            controls.addWidget(button)
        controls.addWidget(self.zoom_label)
        controls.addStretch(1)
        left_layout.addLayout(controls)
        self.zoom_view = ZoomImageView()
        self.zoom_view.zoom_changed.connect(
            lambda percent: self.zoom_label.setText(f"{percent}%"),
        )
        self.zoom_out_button.clicked.connect(lambda: self.zoom_view.zoom_by(0.8))
        self.zoom_in_button.clicked.connect(lambda: self.zoom_view.zoom_by(1.25))
        self.fit_button.clicked.connect(self.zoom_view.fit_image)
        self.actual_button.clicked.connect(self.zoom_view.actual_size)
        self.placeholder = QLabel("Preparando pré-visualização…")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder.setWordWrap(True)
        self.placeholder.setStyleSheet(
            "background: #171d26; color: #e3edf5; font-size: 15px;"
        )
        self.display = QStackedWidget()
        self.display.addWidget(self.placeholder)
        self.display.addWidget(self.zoom_view)
        left_layout.addWidget(self.display, 1)
        self.hint_label = QLabel("Roda do mouse: zoom  |  Arrastar: mover  |  Esc: fechar")
        left_layout.addWidget(self.hint_label)
        splitter.addWidget(left)

        right = QWidget()
        right.setMinimumWidth(245)
        right.setMaximumWidth(485)
        properties = QVBoxLayout(right)
        properties.setContentsMargins(12, 8, 10, 8)
        properties.addWidget(QLabel("PROPRIEDADES"))
        self.properties_text = QLabel(self._basic_properties())
        self.properties_text.setWordWrap(True)
        self.properties_text.setTextFormat(Qt.TextFormat.PlainText)
        self.properties_text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.properties_text.setAlignment(Qt.AlignmentFlag.AlignTop)
        properties.addWidget(self.properties_text)
        self.verify_button = QPushButton("Verificar metadados")
        self.verify_button.clicked.connect(self._request_metadata)
        properties.addWidget(self.verify_button)
        self.edit_button = QPushButton("Editar metadados (futuro)")
        self.edit_button.setEnabled(False)
        properties.addWidget(self.edit_button)
        self.metadata_status = QLabel(
            "Metadados internos ainda não consultados."
        )
        self.metadata_status.setWordWrap(True)
        properties.addWidget(self.metadata_status)
        self.metadata_text = QPlainTextEdit()
        self.metadata_text.setReadOnly(True)
        self.metadata_text.setPlaceholderText(
            "Clique em Verificar metadados para solicitar a leitura."
        )
        properties.addWidget(self.metadata_text, 1)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        splitter.setSizes([1000, 335])
        outer.addWidget(splitter, 1)

        self.setStyleSheet("""
            QDialog { background: #e9f5fc; }
            QLabel#archiviaPreviewTitle { color: #13435b; font-size: 16px; font-weight: 700; }
            QPushButton#archiviaPreviewClose {
                background: #dcebf5; border: 1px solid #9dc5d9;
                border-radius: 6px; font-size: 20px; font-weight: 700;
            }
            QPushButton#archiviaPreviewClose:hover {
                background: #d84c4c; color: white;
            }
        """)
        QShortcut(QKeySequence("Escape"), self, activated=self.reject)
        self._start_preview_if_image()

    def _basic_properties(self) -> str:
        try:
            info = verified_file(self.root, self.file, self.expected)
            date = datetime.fromtimestamp(info.st_mtime).strftime("%d/%m/%Y %H:%M")
            size = f"{info.st_size:,} bytes"
        except (OSError, ValueError, OverflowError):
            date, size = "Indisponível", "Arquivo alterado ou inacessível"
        mime = mimetypes.guess_type(self.file.name)[0] or "Desconhecido"
        return (
            f"Nome: {self.file.name}\n"
            f"Tipo: {mime}\n"
            f"Extensão: {self.file.suffix.lower() or '—'}\n"
            f"Tamanho: {size}\n"
            f"Modificado: {date}\n\n"
            f"Caminho:\n{self.file}\n\nSomente leitura."
        )

    def _start_preview_if_image(self) -> None:
        if self.file.suffix.lower() not in IMAGE_EXTENSIONS:
            self.placeholder.setText(
                "Pré-visualização de conteúdo ainda não disponível para este "
                "formato. Propriedades e verificação de metadados estão acessíveis."
            )
            self.hint_label.setText("Esc ou X para retornar ao Explorador.")
            return
        self._submit_image(_ImageLoad(
            self.root, self.file, self.expected, self._generation, self._events,
        ))

    def _submit_image(self, task: _ImageLoad) -> None:
        self._pool.start(task)

    def _image_loaded_result(self, generation: int, payload: object) -> None:
        if self._closed or generation != self._generation:
            return
        if not isinstance(payload, dict) or "image" not in payload:
            message = payload.get("error", "Imagem indisponível.") if isinstance(payload, dict) else "Resposta inválida."
            self.placeholder.setText(message)
            return
        self._image_loaded = True
        self.zoom_view.set_image(payload["image"])
        self.display.setCurrentWidget(self.zoom_view)
        for button in (
            self.zoom_out_button, self.zoom_in_button,
            self.fit_button, self.actual_button,
        ):
            button.setEnabled(True)
        w, h = payload["original"]
        self.hint_label.setText(
            f"Imagem original: {w} × {h}  |  Roda do mouse: zoom  "
            "|  Arrastar: mover  |  Esc: fechar"
        )
        QTimer.singleShot(0, self.zoom_view.fit_image)

    def _request_metadata(self) -> None:
        if self._closed:
            return
        self.verify_button.setEnabled(False)
        self.metadata_status.setText("Verificando metadados deste arquivo…")
        self.metadata_text.clear()
        self._submit_metadata(_MetadataLoad(
            self.root, self.file, self.expected, self._generation, self._events,
        ))

    def _submit_metadata(self, task: _MetadataLoad) -> None:
        self._pool.start(task)

    def _metadata_loaded_result(self, generation: int, payload: object) -> None:
        if self._closed or generation != self._generation:
            return
        self.verify_button.setEnabled(True)
        if not isinstance(payload, dict):
            self.metadata_status.setText("Resultado de metadados inválido.")
            return
        if "error" in payload:
            self.metadata_status.setText("Falha na verificação dos metadados.")
            self.metadata_text.setPlainText(str(payload["error"])[:250])
            return
        self.metadata_status.setText("Metadados verificados — somente leitura.")
        lines = [f"{name}: {value}" for name, value in payload.get("fields", [])]
        lines += [
            "", f"Fonte: {payload.get('source', 'Não identificada')}",
            "", str(payload.get("note", "")),
        ]
        self.metadata_text.setPlainText("\n".join(lines))

    def reject(self) -> None:
        self._closed = True
        self._generation += 1
        super().reject()
