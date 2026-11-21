"""Formatos de data para apresentação; SQLite permanece em ISO 8601 UTC."""
from __future__ import annotations

from datetime import date, datetime

DATE_FORMATS = {
    "br": ("%d/%m/%Y", "DD/MM/AAAA"),
    "iso": ("%Y-%m-%d", "AAAA-MM-DD"),
    "us": ("%m/%d/%Y", "MM/DD/AAAA"),
}


def parse_user_date(value: str, format_key: str = "br") -> str:
    """Converte data digitada para AAAA-MM-DD; vazio desativa filtro."""
    if format_key not in DATE_FORMATS:
        raise ValueError("Formato de data desconhecido.")
    if not isinstance(value, str):
        raise ValueError("A data deve ser texto.")
    raw = value.strip()
    if not raw:
        return ""
    try:
        parsed = datetime.strptime(raw, DATE_FORMATS[format_key][0]).date()
    except ValueError as exc:
        raise ValueError(
            f"Data inválida: use {DATE_FORMATS[format_key][1]}."
        ) from exc
    if parsed.strftime(DATE_FORMATS[format_key][0]) != raw:
        raise ValueError(f"Data inválida: use {DATE_FORMATS[format_key][1]}.")
    return parsed.isoformat()


def display_date(iso_value: str, format_key: str = "br") -> str:
    """Converte data ISO para a preferência sem alterar o valor gravado."""
    if format_key not in DATE_FORMATS:
        raise ValueError("Formato de data desconhecido.")
    parsed = date.fromisoformat(iso_value)
    return parsed.strftime(DATE_FORMATS[format_key][0])


def display_timestamp(iso_value: str, format_key: str = "br") -> str:
    """Mostra instante de modificação UTC no formato escolhido, com hora."""
    if not iso_value:
        return ""
    if format_key not in DATE_FORMATS:
        raise ValueError("Formato de data desconhecido.")
    parsed = datetime.fromisoformat(iso_value.replace("Z", "+00:00"))
    return parsed.strftime(DATE_FORMATS[format_key][0] + " %H:%M:%S") + " UTC"
