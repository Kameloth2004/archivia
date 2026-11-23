"""Helpers puros para navegar da catalogação ao snapshot salvo."""
from __future__ import annotations

from typing import Any


def find_saved_snapshot(scans: list[dict[str, Any]], scan_id: int) -> bool:
    """Exige ID exato no histórico retornado; não confundir com 'mais recente'."""
    if not isinstance(scan_id, int) or isinstance(scan_id, bool) or scan_id < 1:
        raise ValueError("Identificador do snapshot salvo inválido.")
    return any(
        isinstance(row, dict) and row.get("id") == scan_id
        for row in scans
    )
