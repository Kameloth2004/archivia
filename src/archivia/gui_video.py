"""Reprodução local de vídeo em PySide6, sem execução automática.

O widget somente recebe caminhos locais previamente validados pela camada
de visualização. Não indexa, escreve, transcodifica nem procura na rede.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QSlider, QVBoxLayout, QWidget,
)


VIDEO_EXTENSIONS = frozenset((
    ".mp4", ".m4v", ".mov", ".mkv", ".avi", ".webm",
    ".wmv", ".flv", ".mpeg", ".mpg", ".3gp",
))


def format_media_time(milliseconds: int) -> str:
    seconds = max(0, int(milliseconds) // 1000)
    hours, remaining = divmod(seconds, 3600)
    minutes, seconds = divmod(remaining, 60)
    return (
        f"{hours:02}:{minutes:02}:{seconds:02}"
        if hours else f"{minutes:02}:{seconds:02}"
    )


class LocalVideoPlayer(QWidget):
    """Reprodutor incorporado; abre a origem em estado parado."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("archiviaLocalVideo")
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.audio.setVolume(0.65)
        self.video = QVideoWidget(self)
        self.video.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        self.player.setAudioOutput(self.audio)
        self.player.setVideoOutput(self.video)
        self._duration = 0
        self._seeking = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(self.video, 1)

        line = QHBoxLayout()
        self.play_button = QPushButton("▶ Reproduzir")
        self.pause_button = QPushButton("⏸ Pausar")
        self.stop_button = QPushButton("■ Parar")
        self.back_button = QPushButton("◀ 10s")
        self.forward_button = QPushButton("10s ▶")
        for button in (
            self.play_button, self.pause_button, self.stop_button,
            self.back_button, self.forward_button,
        ):
            line.addWidget(button)
        self.play_button.clicked.connect(self.player.play)
        self.pause_button.clicked.connect(self.player.pause)
        self.stop_button.clicked.connect(self.player.stop)
        self.back_button.clicked.connect(lambda: self.seek_relative(-10_000))
        self.forward_button.clicked.connect(lambda: self.seek_relative(10_000))
        layout.addLayout(line)

        progress = QHBoxLayout()
        self.elapsed_label = QLabel("00:00")
        self.timeline = QSlider(Qt.Orientation.Horizontal)
        self.timeline.setRange(0, 0)
        self.total_label = QLabel("00:00")
        progress.addWidget(self.elapsed_label)
        progress.addWidget(self.timeline, 1)
        progress.addWidget(self.total_label)
        layout.addLayout(progress)
        self.timeline.sliderPressed.connect(self._start_seek)
        self.timeline.sliderReleased.connect(self._finish_seek)
        self.player.positionChanged.connect(self._position_changed)
        self.player.durationChanged.connect(self._duration_changed)

        sound = QHBoxLayout()
        self.mute_button = QPushButton("🔊 Áudio")
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(65)
        self.volume_slider.setMaximumWidth(150)
        self.volume_slider.valueChanged.connect(
            lambda value: self.audio.setVolume(value / 100.0)
        )
        self.mute_button.clicked.connect(self._toggle_mute)
        sound.addStretch(1)
        sound.addWidget(self.mute_button)
        sound.addWidget(self.volume_slider)
        layout.addLayout(sound)

        self.status_label = QLabel("Vídeo pronto. Clique em Reproduzir.")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        self.player.errorOccurred.connect(self._error)
        self.player.playbackStateChanged.connect(self._playback_state)
        self._set_controls(False)

    def _set_controls(self, available: bool) -> None:
        for control in (
            self.play_button, self.pause_button, self.stop_button,
            self.back_button, self.forward_button, self.timeline,
        ):
            control.setEnabled(available)

    def open_local(self, path: Path) -> None:
        """Abre fonte local, mas NÃO chama play()."""
        self.release()
        self._set_controls(True)
        self.status_label.setText("Vídeo pronto. Clique em Reproduzir.")
        self.player.setSource(QUrl.fromLocalFile(str(path)))

    def release(self) -> None:
        """Solta a fonte ao navegar/fechar, para não manter o arquivo aberto."""
        self.player.stop()
        self.player.setSource(QUrl())
        self._duration = 0
        self._seeking = False
        self.timeline.setRange(0, 0)
        self.timeline.setValue(0)
        self.elapsed_label.setText("00:00")
        self.total_label.setText("00:00")
        self._set_controls(False)

    def seek_relative(self, delta_ms: int) -> None:
        if not self.player.isSeekable():
            return
        self.player.setPosition(max(
            0, min(self.player.position() + delta_ms, self._duration),
        ))

    def _start_seek(self) -> None:
        self._seeking = True

    def _finish_seek(self) -> None:
        self._seeking = False
        if self.player.isSeekable():
            self.player.setPosition(self.timeline.value())

    def _duration_changed(self, duration: int) -> None:
        self._duration = max(0, duration)
        self.timeline.setRange(0, self._duration)
        self.total_label.setText(format_media_time(self._duration))

    def _position_changed(self, position: int) -> None:
        self.elapsed_label.setText(format_media_time(position))
        if not self._seeking:
            self.timeline.setValue(max(0, position))

    def _toggle_mute(self) -> None:
        muted = not self.audio.isMuted()
        self.audio.setMuted(muted)
        self.mute_button.setText("🔇 Sem áudio" if muted else "🔊 Áudio")

    def _playback_state(self, state) -> None:
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.status_label.setText("Reproduzindo.")
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self.status_label.setText("Pausado.")

    def _error(self, _error, message: str) -> None:
        self.status_label.setText(
            "Não foi possível reproduzir este vídeo. "
            f"Verifique codec/backend multimídia: {message[:180]}"
        )
