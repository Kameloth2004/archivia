"""Extração serial de quadros de vídeos locais para miniaturas (somente leitura).

Qt Multimedia roda assíncrono no loop Qt; nenhuma reprodução fica ativa após
a captura. Um único decodificador por vez, fila pequena e cancelamento por
geração ao mudar a pasta. Nenhuma miniatura é gravada no disco.
"""
from __future__ import annotations

from collections import OrderedDict, deque
from pathlib import Path
import os

from PySide6.QtCore import QObject, QTimer, QUrl, Qt, Signal
from PySide6.QtGui import QImage
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer, QVideoSink

from .gui_video import VIDEO_EXTENSIONS


_THUMB_WIDTH = 128
_THUMB_HEIGHT = 104
_MAX_PENDING = 24
_MAX_CACHE = 128
_TIMEOUT_MS = 5000


class VideoThumbnailService(QObject):
    """Publica imagens por (caminho, tamanho, mtime_ns, geração)."""

    ready = Signal(str, object, object, int, object)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._queue: deque[tuple[str, int, int, int]] = deque()
        self._seen: set[tuple[str, int, int, int]] = set()
        self._cache: OrderedDict[tuple[str, int, int], QImage] = OrderedDict()
        self._generation = 0
        self._current: tuple[str, int, int, int] | None = None
        self._player = QMediaPlayer(self)
        self._audio = QAudioOutput(self)
        self._audio.setMuted(True)
        self._player.setAudioOutput(self._audio)
        self._sink = QVideoSink(self)
        self._player.setVideoOutput(self._sink)
        self._timeout = QTimer(self)
        self._timeout.setSingleShot(True)
        self._timeout.setInterval(_TIMEOUT_MS)
        self._timeout.timeout.connect(self._finish)
        self._player.mediaStatusChanged.connect(self._media_status)
        self._player.errorOccurred.connect(self._failed)
        self._sink.videoFrameChanged.connect(self._frame_ready)

    def reset(self, generation: int) -> None:
        """Esquece pedidos antigos; interrompe a fonte sem descartar o cache."""
        self._generation = generation
        self._queue.clear()
        self._seen.clear()
        self._timeout.stop()
        self._current = None
        self._player.stop()
        self._player.setSource(QUrl())

    def request(self, path: str, size: int, modified_ns: int, generation: int) -> None:
        if generation != self._generation or Path(path).suffix.lower() not in VIDEO_EXTENSIONS:
            return
        key = (path, size, modified_ns)
        cached = self._cache.get(key)
        if cached is not None:
            self._cache.move_to_end(key)
            self.ready.emit(path, size, modified_ns, generation, cached)
            return
        task = (path, size, modified_ns, generation)
        if task in self._seen or len(self._queue) >= _MAX_PENDING:
            return
        self._queue.append(task)
        self._seen.add(task)
        self._start_next()

    def _start_next(self) -> None:
        if self._current is not None:
            return
        while self._queue:
            task = self._queue.popleft()
            path, size, modified_ns, generation = task
            if generation != self._generation:
                self._seen.discard(task)
                continue
            try:
                item = Path(path)
                if item.is_symlink() or (
                    hasattr(os.path, "isjunction") and os.path.isjunction(item)
                ):
                    raise OSError("Atalho indisponível")
                info = item.stat(follow_symlinks=False)
                if (info.st_size, info.st_mtime_ns) != (size, modified_ns):
                    raise OSError("Arquivo alterado")
            except (OSError, ValueError):
                self._seen.discard(task)
                continue
            self._current = task
            self._player.setSource(QUrl.fromLocalFile(path))
            self._timeout.start()
            return

    def _media_status(self, status: QMediaPlayer.MediaStatus) -> None:
        if self._current is None:
            return
        if status in (
            QMediaPlayer.MediaStatus.LoadedMedia,
            QMediaPlayer.MediaStatus.BufferedMedia,
        ):
            # Decodificação é necessária para produzir quadros; áudio fica mutado.
            if self._player.isSeekable() and self._player.duration() > 2000:
                self._player.setPosition(1000)
            self._player.play()
        elif status == QMediaPlayer.MediaStatus.InvalidMedia:
            self._finish()

    def _failed(self, *_args: object) -> None:
        self._finish()

    def _frame_ready(self, frame: object) -> None:
        task = self._current
        if task is None or not frame.isValid():
            return
        image = frame.toImage()
        if image.isNull():
            return
        path, size, modified_ns, generation = task
        if generation != self._generation:
            self._finish()
            return
        try:
            info = Path(path).stat(follow_symlinks=False)
            if (info.st_size, info.st_mtime_ns) != (size, modified_ns):
                self._finish()
                return
        except OSError:
            self._finish()
            return
        image = image.scaled(
            _THUMB_WIDTH, _THUMB_HEIGHT,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        if image.isNull():
            self._finish()
            return
        key = (path, size, modified_ns)
        self._cache[key] = image
        self._cache.move_to_end(key)
        while len(self._cache) > _MAX_CACHE:
            self._cache.popitem(last=False)
        self.ready.emit(path, size, modified_ns, generation, image)
        self._finish()

    def _finish(self) -> None:
        current = self._current
        self._current = None
        self._timeout.stop()
        self._player.stop()
        self._player.setSource(QUrl())
        if current is not None:
            self._seen.discard(current)
        # Evitar reentrância nas callbacks de Qt Multimedia.
        QTimer.singleShot(0, self._start_next)

    def close(self) -> None:
        self.reset(self._generation + 1)
        self._cache.clear()
