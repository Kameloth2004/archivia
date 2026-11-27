"""Explorador visual da pasta ativa — somente leitura, sem SQLite ou Ollama.

Árvore de diretórios, grade de arquivos e propriedades. Imagens pequenas
recebem miniaturas geradas em threads; não abrimos documentos nem executamos
arquivos. A listagem é paginada para não bloquear pastas grandes.
"""
from __future__ import annotations

from collections import OrderedDict
from datetime import datetime
import os
from pathlib import Path

from PySide6.QtCore import QDir, QFileInfo, QSize, Qt, QObject, QRunnable, QThreadPool, Signal, QTimer
from PySide6.QtGui import QIcon, QImageReader, QPixmap, QImage
from PySide6.QtWidgets import (
    QFileIconProvider, QFileSystemModel, QHBoxLayout, QLabel, QLineEdit,
    QListView, QListWidget, QListWidgetItem, QPushButton, QSplitter,
    QTreeView, QVBoxLayout, QWidget, QAbstractItemView,
)

_BATCH_SIZE = 120
_MAX_THUMB_BYTES = 40 * 1024 * 1024
_MAX_THUMB_PIXELS = 32_000_000
_THUMB_SIZE = QSize(128, 104)
_CACHE_LIMIT = 128
_IMAGE_EXTENSIONS = frozenset(
    (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff", ".avif")
)


def _junction(path: Path) -> bool:
    return bool(getattr(os.path, "isjunction", lambda _p: False)(path))


def safe_directory(root: Path, candidate: Path) -> Path | None:
    """Somente pastas reais dentro da origem, sem symlinks/junctions."""
    try:
        if root.is_symlink() or _junction(root) or not root.is_dir():
            return None
        if candidate.is_symlink() or _junction(candidate) or not candidate.is_dir():
            return None
        # Verificar componentes ANTES de resolve(): resolve() ocultaria
        # symlinks/junctions existentes nos diretórios intermediários.
        base = root.expanduser().absolute()
        proposed = candidate.expanduser().absolute()
        segments = proposed.relative_to(base).parts
        if ".." in segments:
            return None
        current = base
        for segment in segments:
            current = current / segment
            if current.is_symlink() or _junction(current):
                return None
        canonical_root = base.resolve(strict=True)
        canonical_target = current.resolve(strict=True)
        canonical_target.relative_to(canonical_root)
        return canonical_target
    except (ValueError, OSError, RuntimeError):
        return None


class _ThumbnailEvents(QObject):
    # st_mtime_ns é um inteiro de 64 bits (em torno de 1e18).
    # Signal(int) usa o inteiro C++ de 32 bits, truncando/falhando no
    # transporte e impedindo a miniatura de chegar à interface.
    # object preserva os inteiros Python, inclusive arquivos grandes.
    ready = Signal(str, object, object, int, object)


class _ThumbnailTask(QRunnable):
    """Decodifica QImage fora da interface; nunca cria QPixmap na thread."""

    def __init__(self, path: str, size: int, modified_ns: int,
                 generation: int, events: _ThumbnailEvents) -> None:
        super().__init__()
        self.path = path
        self.size = size
        self.modified_ns = modified_ns
        self.generation = generation
        self.events = events

    def run(self) -> None:
        try:
            reader = QImageReader(self.path)
            reader.setAutoTransform(True)
            dimensions = reader.size()
            if (not dimensions.isValid() or dimensions.width() <= 0
                    or dimensions.height() <= 0
                    or dimensions.width() * dimensions.height() > _MAX_THUMB_PIXELS):
                return
            reader.setScaledSize(dimensions.scaled(
                _THUMB_SIZE, Qt.AspectRatioMode.KeepAspectRatio,
            ))
            image = reader.read()
            if not image.isNull():
                self.events.ready.emit(
                    self.path, self.size, self.modified_ns, self.generation, image,
                )
        except (OSError, RuntimeError, ValueError):
            # Falhas de decodificação mantêm o ícone normal do arquivo.
            return


class ExplorerPanel(QWidget):
    """Painel de navegação em um diretório por vez, sem modificar arquivos."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("archiviaExplorer")
        self._root: Path | None = None
        self._directory: Path | None = None
        self._cursor = None
        self._pending = None
        self._generation = 0
        self._file_items: dict[str, QListWidgetItem] = {}
        self._queued: set[tuple[str, int, int, int]] = set()
        self._cache: OrderedDict[tuple[str, int, int], QIcon] = OrderedDict()
        self._icons = QFileIconProvider()
        self._pool = QThreadPool(self)
        self._pool.setMaxThreadCount(2)
        self._events = _ThumbnailEvents(self)
        self._events.ready.connect(self._apply_thumbnail)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(7)
        toolbar = QHBoxLayout()
        self.up_button = QPushButton("Subir")
        self.up_button.clicked.connect(self._go_up)
        toolbar.addWidget(self.up_button)
        self.path_field = QLineEdit()
        self.path_field.setReadOnly(True)
        self.path_field.setPlaceholderText("Selecione uma pasta ativa da sessão")
        toolbar.addWidget(self.path_field, 1)
        self.refresh_button = QPushButton("Atualizar")
        self.refresh_button.clicked.connect(self.refresh)
        toolbar.addWidget(self.refresh_button)
        self.view_button = QPushButton("Ver detalhes")
        self.view_button.clicked.connect(self._toggle_view)
        toolbar.addWidget(self.view_button)
        layout.addLayout(toolbar)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.tree = QTreeView()
        self.tree.setHeaderHidden(True)
        self.tree.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tree.setDragEnabled(False)
        self.tree.setAcceptDrops(False)
        self.folders = QFileSystemModel(self)
        self.folders.setReadOnly(True)
        self.folders.setFilter(
            QDir.Filter.AllDirs | QDir.Filter.NoDotAndDotDot | QDir.Filter.NoSymLinks
        )
        self.tree.setModel(self.folders)
        for column in (1, 2, 3):
            self.tree.hideColumn(column)
        self.tree.clicked.connect(self._tree_clicked)
        self.splitter.addWidget(self.tree)

        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(5)
        self.files = QListWidget()
        self.files.setViewMode(QListView.ViewMode.IconMode)
        self.files.setResizeMode(QListView.ResizeMode.Adjust)
        self.files.setMovement(QListView.Movement.Static)
        self.files.setWrapping(True)
        self.files.setWordWrap(True)
        self.files.setIconSize(_THUMB_SIZE)
        self.files.setGridSize(QSize(165, 147))
        self.files.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.files.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.files.setDragEnabled(False)
        self.files.setAcceptDrops(False)
        self.files.itemSelectionChanged.connect(self._show_properties)
        self.files.itemDoubleClicked.connect(self._open_item)
        self.files.verticalScrollBar().valueChanged.connect(self._schedule_visible_thumbnails)
        center_layout.addWidget(self.files, 1)
        bottom = QHBoxLayout()
        self.count_label = QLabel("Nenhuma pasta selecionada.")
        bottom.addWidget(self.count_label, 1)
        self.more_button = QPushButton("Carregar mais")
        self.more_button.clicked.connect(self._append_batch)
        self.more_button.hide()
        bottom.addWidget(self.more_button)
        center_layout.addLayout(bottom)
        self.splitter.addWidget(center)

        properties = QWidget()
        properties_layout = QVBoxLayout(properties)
        properties_layout.setContentsMargins(10, 8, 10, 8)
        properties_layout.addWidget(QLabel("PROPRIEDADES"))
        self.properties_text = QLabel("Selecione um arquivo ou pasta.")
        self.properties_text.setWordWrap(True)
        self.properties_text.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse,
        )
        self.properties_text.setAlignment(Qt.AlignmentFlag.AlignTop)
        properties_layout.addWidget(self.properties_text)
        properties_layout.addStretch(1)
        self.splitter.addWidget(properties)
        self.splitter.setSizes([240, 780, 260])
        layout.addWidget(self.splitter, 1)
        self.tree.setEnabled(False)
        self.files.setEnabled(False)
        self.up_button.setEnabled(False)
        self.refresh_button.setEnabled(False)
        self.view_button.setEnabled(False)

    @property
    def active_root(self) -> Path | None:
        return self._root

    @property
    def current_directory(self) -> Path | None:
        return self._directory

    def set_active_folder(self, folder: Path | None) -> None:
        """Uma troca de origem descarta arquivos/miniaturas da pasta anterior."""
        self._generation += 1
        self._pool.clear()
        self._close_cursor()
        self._cache.clear()
        self._queued.clear()
        self._file_items.clear()
        self.files.clear()
        self.properties_text.setText("Selecione um arquivo ou pasta.")
        self._root = safe_directory(folder, folder) if folder is not None else None
        self._directory = None
        enabled = self._root is not None
        self.tree.setEnabled(enabled)
        self.files.setEnabled(enabled)
        self.refresh_button.setEnabled(enabled)
        self.view_button.setEnabled(enabled)
        self.more_button.hide()
        if not enabled:
            self.path_field.clear()
            self.count_label.setText("Escolha uma pasta ativa para visualizar arquivos.")
            self.up_button.setEnabled(False)
            self.tree.setRootIndex(self.folders.index(""))
            return
        self.folders.setRootPath(str(self._root))
        self.tree.setRootIndex(self.folders.index(str(self._root)))
        self._open_directory(self._root)

    def _tree_clicked(self, index) -> None:
        if self._root is None:
            return
        self._open_directory(Path(self.folders.filePath(index)))

    def _open_directory(self, path: Path) -> None:
        if self._root is None:
            return
        verified = safe_directory(self._root, path)
        if verified is None:
            self.count_label.setText("Pasta indisponível ou fora da origem ativa.")
            return
        self._generation += 1
        self._pool.clear()
        self._close_cursor()
        self._directory = verified
        self._queued.clear()
        self._file_items.clear()
        self.files.clear()
        self.properties_text.setText("Selecione um arquivo ou pasta.")
        self.path_field.setText(str(verified))
        self.up_button.setEnabled(verified != self._root)
        self.more_button.hide()
        try:
            self._cursor = os.scandir(verified)
        except OSError as exc:
            self.count_label.setText(f"Não foi possível ler a pasta: {exc}")
            return
        self._append_batch()

    def _close_cursor(self) -> None:
        if self._cursor is not None:
            self._cursor.close()
        self._cursor = None
        self._pending = None

    def _append_batch(self) -> None:
        if self._cursor is None or self._directory is None:
            return
        count = 0
        while count < _BATCH_SIZE:
            try:
                entry = self._pending if self._pending is not None else next(self._cursor)
                self._pending = None
            except StopIteration:
                self._close_cursor()
                break
            except OSError:
                self._close_cursor()
                self.count_label.setText("A leitura da pasta foi interrompida.")
                break
            try:
                p = Path(entry.path)
                if entry.is_symlink() or _junction(p):
                    continue
                is_folder = entry.is_dir(follow_symlinks=False)
                is_file = entry.is_file(follow_symlinks=False)
                if not is_folder and not is_file:
                    continue
                info = entry.stat(follow_symlinks=False)
                icon = self._icons.icon(QFileInfo(str(p)))
                item = QListWidgetItem(icon, entry.name)
                item.setData(Qt.ItemDataRole.UserRole, str(p))
                item.setData(Qt.ItemDataRole.UserRole + 1, (
                    is_folder, info.st_size, info.st_mtime_ns,
                ))
                item.setToolTip(entry.name)
                item.setFlags(
                    Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable,
                )
                self.files.addItem(item)
                if not is_folder:
                    self._file_items[str(p)] = item
                count += 1
            except (OSError, ValueError):
                continue
        if self._cursor is not None:
            try:
                self._pending = next(self._cursor)
            except (StopIteration, OSError):
                self._close_cursor()
        has_more = self._cursor is not None
        self.more_button.setVisible(has_more)
        self.count_label.setText(
            f"{self.files.count()} itens exibidos"
            + (" — existem mais itens nesta pasta." if has_more else " nesta pasta.")
        )
        # Qt precisa concluir o layout dos itens antes de conhecer quais
        # miniaturas estão visíveis na viewport.
        QTimer.singleShot(0, self._schedule_visible_thumbnails)

    def _schedule_visible_thumbnails(self, *_args) -> None:
        if self._directory is None:
            return
        # Apenas elementos visíveis e alguns próximos. Nada de gerar
        # miniaturas para dezenas de milhares de arquivos de uma só vez.
        viewport = self.files.viewport().rect().adjusted(0, -180, 0, 180)
        generation = self._generation
        submitted = 0
        for row in range(self.files.count()):
            if submitted >= 24:
                break
            item = self.files.item(row)
            if not self.files.visualItemRect(item).intersects(viewport):
                continue
            path_text = item.data(Qt.ItemDataRole.UserRole)
            meta = item.data(Qt.ItemDataRole.UserRole + 1)
            if not path_text or not meta or meta[0]:
                continue
            path = Path(path_text)
            if path.suffix.lower() not in _IMAGE_EXTENSIONS:
                continue
            size, mtime = meta[1], meta[2]
            if size > _MAX_THUMB_BYTES:
                continue
            key = (path_text, size, mtime)
            cached = self._cache.get(key)
            if cached is not None:
                self._cache.move_to_end(key)
                item.setIcon(cached)
                continue
            queued = (path_text, size, mtime, generation)
            if queued in self._queued:
                continue
            self._queued.add(queued)
            self._pool.start(_ThumbnailTask(
                path_text, size, mtime, generation, self._events,
            ))
            submitted += 1

    def _apply_thumbnail(self, path: str, size: int, modified_ns: int,
                         generation: int, image: QImage) -> None:
        self._queued.discard((path, size, modified_ns, generation))
        if generation != self._generation or image.isNull():
            return
        item = self._file_items.get(path)
        if item is None:
            return
        # QVariant pode devolver a tupla como uma lista, dependendo da
        # versão do PySide6. Comparar campos, não a classe do contêiner.
        meta = item.data(Qt.ItemDataRole.UserRole + 1)
        if (not meta or len(meta) != 3 or bool(meta[0])
                or meta[1] != size or meta[2] != modified_ns):
            return
        # QPixmap só é criado na thread de interface.
        icon = QIcon(QPixmap.fromImage(image))
        item.setIcon(icon)
        key = (path, size, modified_ns)
        self._cache[key] = icon
        self._cache.move_to_end(key)
        while len(self._cache) > _CACHE_LIMIT:
            self._cache.popitem(last=False)

    def _open_item(self, item: QListWidgetItem) -> None:
        path_text = item.data(Qt.ItemDataRole.UserRole)
        metadata = item.data(Qt.ItemDataRole.UserRole + 1)
        if path_text and metadata and metadata[0]:
            self._open_directory(Path(path_text))
        # Arquivos nunca são executados ou abertos em outros aplicativos.

    def _show_properties(self) -> None:
        items = self.files.selectedItems()
        if not items:
            self.properties_text.setText("Selecione um arquivo ou pasta.")
            return
        if len(items) > 1:
            self.properties_text.setText(f"{len(items)} itens selecionados.\nSomente leitura.")
            return
        item = items[0]
        path_text = item.data(Qt.ItemDataRole.UserRole)
        if not path_text:
            return
        metadata = item.data(Qt.ItemDataRole.UserRole + 1)
        if not metadata:
            return
        folder, size, modified_ns = metadata
        try:
            formatted_date = datetime.fromtimestamp(
                modified_ns / 1_000_000_000
            ).strftime("%d/%m/%Y %H:%M")
        except (OverflowError, OSError, ValueError):
            formatted_date = "Data indisponível"
        self.properties_text.setText(
            f"Nome: {item.text()}\n"
            f"Tipo: {'Pasta' if folder else 'Arquivo'}\n"
            f"Extensão: {Path(path_text).suffix.lower() or '—'}\n"
            f"Tamanho: {'—' if folder else format(size, ',') + ' bytes'}\n"
            f"Modificado: {formatted_date}\n\n"
            f"Caminho:\n{path_text}\n\n"
            "Visualização somente leitura."
        )

    def _go_up(self) -> None:
        if self._root is not None and self._directory is not None:
            if self._directory != self._root:
                self._open_directory(self._directory.parent)

    def refresh(self) -> None:
        if self._directory is not None:
            self._open_directory(self._directory)

    def _toggle_view(self) -> None:
        if self.files.viewMode() == QListView.ViewMode.IconMode:
            self.files.setViewMode(QListView.ViewMode.ListMode)
            self.files.setGridSize(QSize())
            self.view_button.setText("Ver miniaturas")
        else:
            self.files.setViewMode(QListView.ViewMode.IconMode)
            self.files.setGridSize(QSize(165, 147))
            self.view_button.setText("Ver detalhes")
        self._schedule_visible_thumbnails()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        QTimer.singleShot(0, self._schedule_visible_thumbnails)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        QTimer.singleShot(0, self._schedule_visible_thumbnails)

    def closeEvent(self, event) -> None:
        self._generation += 1
        self._close_cursor()
        self._pool.clear()
        super().closeEvent(event)
