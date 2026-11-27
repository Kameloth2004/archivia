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
from .metadata import read_file_metadata
from .gui_viewer import FilePreviewDialog

from PySide6.QtWidgets import (
    QFileIconProvider, QFileSystemModel, QHBoxLayout, QLabel, QLineEdit,
    QListView, QListWidget, QListWidgetItem, QPushButton, QSplitter,
    QTreeView, QVBoxLayout, QWidget, QAbstractItemView, QScrollArea,
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


class _MetadataEvents(QObject):
    ready = Signal(str, object, object, int, object)


class _MetadataTask(QRunnable):
    """Executa apenas após clique explícito; não compartilha estado com Ollama."""

    def __init__(self, path: str, size: int, modified_ns: int,
                 generation: int, events: _MetadataEvents) -> None:
        super().__init__()
        self.path = path
        self.size = size
        self.modified_ns = modified_ns
        self.generation = generation
        self.events = events

    def run(self) -> None:
        try:
            candidate = Path(self.path)
            if candidate.is_symlink() or _junction(candidate):
                raise ValueError("Arquivo não permitido para leitura.")
            before = candidate.stat(follow_symlinks=False)
            if (before.st_size, before.st_mtime_ns) != (self.size, self.modified_ns):
                raise ValueError("Arquivo modificado desde a seleção. Atualize o Explorador.")
            payload = read_file_metadata(candidate)
            after = candidate.stat(follow_symlinks=False)
            if (after.st_size, after.st_mtime_ns) != (self.size, self.modified_ns):
                raise ValueError("Arquivo modificado durante a leitura. Atualize o Explorador.")
        except (OSError, ValueError, RuntimeError) as exc:
            payload = {"error": str(exc)}
        self.events.ready.emit(
            self.path, self.size, self.modified_ns, self.generation, payload,
        )


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
        self._metadata_events = _MetadataEvents(self)
        self._metadata_events.ready.connect(self._apply_metadata)
        self._metadata_generation = 0

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
        self.open_preview_button = QPushButton("Ampliar arquivo")
        self.open_preview_button.setToolTip(
            "Abrir visualizador em tela cheia para o arquivo selecionado."
        )
        self.open_preview_button.setEnabled(False)
        self.open_preview_button.clicked.connect(self._open_selected_preview)
        toolbar.addWidget(self.open_preview_button)
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
        # Qt pode deixar fragmentos do ícone genérico quando a miniatura
        # chega durante a inserção/realocação de itens. Agrupamos pedidos de
        # redesenho completo para não repintar a lista a cada arquivo.
        self._thumbnail_repaint_timer = QTimer(self)
        self._thumbnail_repaint_timer.setSingleShot(True)
        self._thumbnail_repaint_timer.setInterval(30)
        self._thumbnail_repaint_timer.timeout.connect(self._repaint_thumbnail_viewport)
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

        self.verify_metadata_button = QPushButton("Verificar metadados")
        self.verify_metadata_button.setToolTip(
            "Ler metadados internos somente deste arquivo, após solicitação."
        )
        self.verify_metadata_button.clicked.connect(self._verify_selected_metadata)
        self.verify_metadata_button.setEnabled(False)
        properties_layout.addWidget(self.verify_metadata_button)

        self.edit_metadata_button = QPushButton("Editar metadados (futuro)")
        self.edit_metadata_button.setToolTip(
            "A edição exigirá prévia e confirmação explícita; ainda não implementada."
        )
        self.edit_metadata_button.setEnabled(False)
        properties_layout.addWidget(self.edit_metadata_button)

        self.metadata_status = QLabel(
            "Metadados internos não consultados. Clique em Verificar metadados."
        )
        self.metadata_status.setWordWrap(True)
        properties_layout.addWidget(self.metadata_status)
        self.metadata_details = QLabel("")
        self.metadata_details.setWordWrap(True)
        self.metadata_details.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse,
        )
        self.metadata_details.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.metadata_details.setTextFormat(Qt.TextFormat.PlainText)
        self.metadata_scroll = QScrollArea()
        self.metadata_scroll.setWidgetResizable(True)
        self.metadata_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.metadata_scroll.setWidget(self.metadata_details)
        properties_layout.addWidget(self.metadata_scroll, 1)
        self.splitter.addWidget(properties)
        self.splitter.setSizes([240, 780, 260])
        layout.addWidget(self.splitter, 1)
        self.tree.setEnabled(False)
        self.files.setEnabled(False)
        self.up_button.setEnabled(False)
        self.refresh_button.setEnabled(False)
        self.view_button.setEnabled(False)
        self.open_preview_button.setEnabled(False)

    @property
    def active_root(self) -> Path | None:
        return self._root

    @property
    def current_directory(self) -> Path | None:
        return self._directory

    def set_active_folder(self, folder: Path | None) -> None:
        """Uma troca de origem descarta arquivos/miniaturas da pasta anterior."""
        self._generation += 1
        self._metadata_generation += 1
        self._pool.clear()
        self._close_cursor()
        self._cache.clear()
        self._queued.clear()
        self._file_items.clear()
        self.files.clear()
        self.properties_text.setText("Selecione um arquivo ou pasta.")
        self._reset_metadata_selection()
        self._root = safe_directory(folder, folder) if folder is not None else None
        self._directory = None
        enabled = self._root is not None
        self.tree.setEnabled(enabled)
        self.files.setEnabled(enabled)
        self.refresh_button.setEnabled(enabled)
        self.view_button.setEnabled(enabled)
        self.open_preview_button.setEnabled(False)
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
        self._metadata_generation += 1
        self._pool.clear()
        self._close_cursor()
        self._directory = verified
        self._queued.clear()
        self._file_items.clear()
        self.files.clear()
        self.properties_text.setText("Selecione um arquivo ou pasta.")
        self._reset_metadata_selection()
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
        # Concluir a geometria da grade antes de selecionar as novas
        # miniaturas visíveis. O redesenho inteiro elimina restos do ícone
        # genérico após "Carregar mais" sem exigir rolar a lista.
        QTimer.singleShot(0, self._finish_batch_layout)

    def _finish_batch_layout(self) -> None:
        """Atualiza a grade uma vez após as novas entradas serem inseridas."""
        if self._directory is None:
            return
        self.files.doItemsLayout()
        self._schedule_visible_thumbnails()
        self._schedule_viewport_repaint()

    def _schedule_viewport_repaint(self) -> None:
        """Agrupa várias atualizações de ícones em um único redesenho."""
        if not self._thumbnail_repaint_timer.isActive():
            self._thumbnail_repaint_timer.start()

    def _repaint_thumbnail_viewport(self) -> None:
        """Redesenha também as áreas anteriormente ocupadas pelo ícone padrão."""
        self.files.viewport().update()

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
        # setIcon normalmente invalida somente o item; quando vários são
        # adicionados simultaneamente, alguns pixels do ícone antigo podem
        # permanecer até ocorrer uma rolagem. Repintar a viewport resolve.
        self._schedule_viewport_repaint()
        key = (path, size, modified_ns)
        self._cache[key] = icon
        self._cache.move_to_end(key)
        while len(self._cache) > _CACHE_LIMIT:
            self._cache.popitem(last=False)

    def _open_item(self, item: QListWidgetItem) -> None:
        path_text = item.data(Qt.ItemDataRole.UserRole)
        metadata = item.data(Qt.ItemDataRole.UserRole + 1)
        if not path_text or not metadata:
            return
        if metadata[0]:
            self._open_directory(Path(path_text))
        else:
            self._open_preview_for_item(item)

    def _open_selected_preview(self) -> None:
        selected = self.files.selectedItems()
        if len(selected) == 1:
            self._open_preview_for_item(selected[0])

    def _preview_sequence(self) -> list[tuple[Path, tuple[int, int]]]:
        """Arquivos na ordem visual, sem incluir pastas nem varrer o disco."""
        entries: list[tuple[Path, tuple[int, int]]] = []
        for index in range(self.files.count()):
            item = self.files.item(index)
            meta = item.data(Qt.ItemDataRole.UserRole + 1)
            path_text = item.data(Qt.ItemDataRole.UserRole)
            if (path_text and meta and len(meta) == 3 and not meta[0]
                    and self._root is not None
                    and safe_directory(self._root, Path(path_text).parent) is not None):
                entries.append((Path(path_text), (meta[1], meta[2])))
        return entries

    def _preview_more(self) -> list[tuple[Path, tuple[int, int]]]:
        """Apenas um lote de entradas por solicitação de navegação."""
        if self._cursor is not None:
            self._append_batch()
        return self._preview_sequence()

    def _open_preview_for_item(self, item: QListWidgetItem) -> None:
        """Só uma ação explícita abre o visualizador; não executa o arquivo."""
        if self._root is None:
            return
        path_text = item.data(Qt.ItemDataRole.UserRole)
        metadata = item.data(Qt.ItemDataRole.UserRole + 1)
        if not path_text or not metadata or metadata[0]:
            return
        path = Path(path_text)
        if (safe_directory(self._root, path.parent) is None
                or path.is_symlink() or _junction(path)):
            return
        self._preview_dialog = FilePreviewDialog(
            self._root, path, (metadata[1], metadata[2]), parent=self,
            sequence=self._preview_sequence(),
            load_more=self._preview_more,
            has_more=lambda: self._cursor is not None,
        )
        try:
            self._preview_dialog.showFullScreen()
            self._preview_dialog.exec()
        finally:
            # O Explorer mantém a seleção, a pasta e a posição de rolagem.
            self._preview_dialog.deleteLater()
            self._preview_dialog = None

    def _reset_metadata_selection(self) -> None:
        self._metadata_generation += 1
        self.verify_metadata_button.setEnabled(False)
        self.metadata_status.setText(
            "Metadados internos não consultados. Clique em Verificar metadados."
        )
        self.metadata_details.clear()

    def _verify_selected_metadata(self) -> None:
        """A leitura interna ocorre SOMENTE após este clique explícito."""
        selected = self.files.selectedItems()
        if len(selected) != 1 or self._root is None:
            return
        item = selected[0]
        path_text = item.data(Qt.ItemDataRole.UserRole)
        meta = item.data(Qt.ItemDataRole.UserRole + 1)
        if not path_text or not meta or meta[0]:
            return
        candidate = Path(path_text)
        if (safe_directory(self._root, candidate.parent) is None
                or candidate.is_symlink() or _junction(candidate)):
            self.metadata_status.setText("Arquivo fora da pasta ativa ou não permitido.")
            return
        self._metadata_generation += 1
        self.verify_metadata_button.setEnabled(False)
        self.metadata_status.setText("Lendo metadados deste arquivo…")
        self.metadata_details.clear()
        self._start_metadata_task(_MetadataTask(
            path_text, meta[1], meta[2],
            self._metadata_generation, self._metadata_events,
        ))

    def _start_metadata_task(self, task: _MetadataTask) -> None:
        """Ponto de envio testável, sem simular objetos internos do Qt."""
        self._pool.start(task)

    def _apply_metadata(self, path: str, size: int, modified_ns: int,
                        generation: int, payload: object) -> None:
        """Descarta resultados de arquivos já desmarcados ou pastas trocadas."""
        if generation != self._metadata_generation:
            return
        selected = self.files.selectedItems()
        if len(selected) != 1 or selected[0].data(Qt.ItemDataRole.UserRole) != path:
            return
        meta = selected[0].data(Qt.ItemDataRole.UserRole + 1)
        if not meta or meta[0] or meta[1] != size or meta[2] != modified_ns:
            return
        self.verify_metadata_button.setEnabled(True)
        if not isinstance(payload, dict):
            self.metadata_status.setText("Resposta inválida do leitor.")
            return
        if "error" in payload:
            self.metadata_status.setText("Não foi possível verificar metadados.")
            self.metadata_details.setText(str(payload["error"])[:250])
            return
        self.metadata_status.setText("Verificação concluída — somente leitura.")
        fields = payload.get("fields", [])
        self.metadata_details.setText(
            "\n".join(f"{label}: {value}" for label, value in fields)
            + "\n\nFonte: " + str(payload.get("source", "Não identificada"))
            + "\n\n" + str(payload.get("note", ""))
        )

    def _show_properties(self) -> None:
        self._reset_metadata_selection()
        items = self.files.selectedItems()
        self.open_preview_button.setEnabled(
            len(items) == 1 and bool(
                items[0].data(Qt.ItemDataRole.UserRole + 1)
            ) and not items[0].data(Qt.ItemDataRole.UserRole + 1)[0]
        )
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
        self.verify_metadata_button.setEnabled(not folder)
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
        self._thumbnail_repaint_timer.stop()
        self._close_cursor()
        self._pool.clear()
        super().closeEvent(event)
