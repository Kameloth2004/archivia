"""Visualização explícita de metadados brutos preservados (somente leitura)."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QVBoxLayout,
)


class RawMetadataDialog(QDialog):
    """Exibe XML XMP original sem executar, editar ou salvar conteúdo."""

    def __init__(self, sections: list[dict], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("ArchivIA — Metadados brutos")
        self.resize(850, 650)
        outer = QVBoxLayout(self)
        outer.addWidget(QLabel(
            "Metadados brutos preservados na leitura. "
            "Apenas visualização; o arquivo original não é alterado."
        ))
        self.content = QPlainTextEdit()
        self.content.setReadOnly(True)
        self.content.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.content.setPlainText("\n\n".join(
            f"── {section.get('name', 'Conteúdo bruto')} ──\n"
            f"{section.get('text', '')}"
            for section in sections
        ))
        outer.addWidget(self.content, 1)
        footer = QHBoxLayout()
        self.copy_button = QPushButton("Copiar conteúdo")
        self.copy_button.clicked.connect(self._copy)
        footer.addWidget(self.copy_button)
        footer.addStretch(1)
        self.close_button = QPushButton("Fechar")
        self.close_button.clicked.connect(self.accept)
        footer.addWidget(self.close_button)
        outer.addLayout(footer)

    def _copy(self) -> None:
        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(self.content.toPlainText())
