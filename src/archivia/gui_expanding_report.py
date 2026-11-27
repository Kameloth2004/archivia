"""Relatório expansível de leitura, sem rolagem vertical aninhada.

Calcula altura em pixels usando um QTextDocument de medição. Isso é
necessário porque QPlainTextDocumentLayout.documentSize().height()
representa os blocos de texto, não a altura visual em pixels.
Relatórios longos passam a usar somente o QScrollArea externo.
"""
from __future__ import annotations

from math import ceil

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextDocument
from PySide6.QtWidgets import QPlainTextEdit, QSizePolicy


class ExpandingReport(QPlainTextEdit):
    """Relatório somente leitura que ajusta a altura ao conteúdo completo."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._updating_height = False
        self.setReadOnly(True)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(48)
        self.textChanged.connect(self._update_height)

    def _update_height(self) -> None:
        """Mede o texto em pixels, inclusive linhas quebradas pela largura."""
        if self._updating_height:
            return
        self._updating_height = True
        try:
            width = max(80, self.viewport().width())
            # O layout simplificado de QPlainTextEdit não fornece altura em
            # pixels via documentSize(). QTextDocument faz essa medição.
            measurement = QTextDocument()
            measurement.setDefaultFont(self.font())
            measurement.setDocumentMargin(self.document().documentMargin())
            measurement.setPlainText(self.toPlainText())
            measurement.setTextWidth(width)
            visual_height = ceil(measurement.size().height())
            # Margem extra para padding do tema e diferenças de métricas
            # entre QTextDocument e o renderizador simplificado.
            target = max(
                self.minimumHeight(),
                visual_height + 2 * self.frameWidth() + 24,
            )
            if self.height() != target:
                self.setFixedHeight(target)
        finally:
            self._updating_height = False

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._update_height()

    def resizeEvent(self, event) -> None:
        previous_width = event.oldSize().width()
        super().resizeEvent(event)
        if event.size().width() != previous_width:
            self._update_height()
