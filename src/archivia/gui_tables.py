"""Widget reutilizável para preenchimento de tabelas já existentes.

Não cria layouts nem altera comportamento de seleção e cabeçalhos.
"""
from __future__ import annotations

from collections.abc import Sequence

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem


def fill_table(
    table: QTableWidget,
    rows: Sequence[Sequence[str]],
    *,
    tooltips: Sequence[Sequence[str]] | None = None,
    roles: Sequence[Sequence[str | None]] | None = None,
) -> None:
    """Preenche células somente leitura, preservando colunas/configurações.

    Recusa tamanhos incompatíveis antes de alterar a tabela.
    """
    width = table.columnCount()
    if any(len(row) != width for row in rows):
        raise ValueError("Quantidade de colunas inconsistente.")
    if tooltips is not None and (
        len(tooltips) != len(rows)
        or any(len(row) != width for row in tooltips)
    ):
        raise ValueError("Tooltips não correspondem às células da tabela.")
    if roles is not None and (
        len(roles) != len(rows)
        or any(len(row) != width for row in roles)
    ):
        raise ValueError("Dados originais não correspondem às células da tabela.")

    table.setRowCount(len(rows))
    for row_index, row in enumerate(rows):
        for column, value in enumerate(row):
            cell = QTableWidgetItem(str(value))
            if tooltips is not None:
                cell.setToolTip(tooltips[row_index][column])
            if roles is not None:
                raw = roles[row_index][column]
                if raw is not None:
                    cell.setData(Qt.ItemDataRole.UserRole, raw)
            table.setItem(row_index, column, cell)
