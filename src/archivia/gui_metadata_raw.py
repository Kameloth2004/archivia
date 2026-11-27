"""Visualização explícita de metadados brutos preservados (somente leitura)."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QVBoxLayout,
)


_MAX_RAW_DISPLAY_BYTES = 2 * 1024 * 1024


def _raw_section_text(section: dict) -> str:
    """Renderiza XML original ou hex sem abreviar blocos pequenos."""
    if "data" not in section:
        return str(section.get("text", ""))
    data = bytes(section["data"])
    visible = data[:_MAX_RAW_DISPLAY_BYTES]
    lines = [
        f"{offset:08X}: " + visible[offset:offset + 16].hex(" ")
        for offset in range(0, len(visible), 16)
    ]
    if len(data) > len(visible):
        lines.append(
            f"Prévia limitada por segurança a {_MAX_RAW_DISPLAY_BYTES:,} bytes "
            f"de um total de {len(data):,} bytes."
        )
    return "\n".join(lines) + f"\nTamanho original: {len(data):,} bytes"


class RawMetadataDialog(QDialog):
    """Exibe XML e bytes originais sem executar, editar ou salvar conteúdo."""

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
            f"{_raw_section_text(section)}"
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
