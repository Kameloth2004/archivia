"""Relatório expansível de leitura, sem rolagem vertical aninhada.

O documento ajusta sua altura ao conteúdo; se o texto exceder a janela,
o QScrollArea externo é responsável pela rolagem. Não altera arquivos.
"""
from __future__ import annotations

from math import ceil

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QPlainTextEdit, QSizePolicy


class ExpandingReport(QPlainTextEdit):
    """QPlainTextEdit somente leitura que ocupa a altura do relatório completo."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._height_update_pending = False
        self.setReadOnly(True)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(48)
        self.textChanged.connect(self._schedule_height_update)

    def _schedule_height_update(self) -> None:
        """Calcula após o Qt atualizar o layout e a quebra das linhas."""
        if self._height_update_pending:
            return
        self._height_update_pending = True
        QTimer.singleShot(0, self._update_height)

    def _update_height(self) -> None:
        self._height_update_pending = False
        # QPlainTextDocumentLayout considera as linhas quebradas conforme
        # a largura disponível; frame/padding não fazem parte do documento.
        document_height = ceil(self.document().documentLayout().documentSize().height())
        minimum_content = self.fontMetrics().lineSpacing()
        target = max(
            self.minimumHeight(),
            max(document_height, minimum_content) + 2 * self.frameWidth() + 12,
        )
        if self.height() != target:
            self.setFixedHeight(target)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._schedule_height_update()

    def resizeEvent(self, event) -> None:
        previous_width = event.oldSize().width()
        super().resizeEvent(event)
        if event.size().width() != previous_width:
            self._schedule_height_update()
