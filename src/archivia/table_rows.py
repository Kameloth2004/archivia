"""Linhas de tabelas do ArchivIA: formatação pura, sem Qt ou acesso a disco.

Cada função recebe dados do backend já validados e devolve células prontas
para exibição. Centraliza a apresentação, sem modificar os resultados originais.
"""
from __future__ import annotations

from typing import Any

from .date_formats import display_timestamp


def inventory_preview_rows(files: list[dict[str, Any]]) -> list[tuple[str, ...]]:
    return [
        (item["path"], item["category"], item["extension"], str(item["size_bytes"]))
        for item in files
    ]


def origin_rows(origins: list[dict[str, Any]]) -> list[tuple[str, ...]]:
    return [
        (item["root"], str(item["scan_id"]), str(item["indexed_files"]),
         str(item["media_files"]))
        for item in origins
    ]


def duplicate_rows(groups: list[dict[str, Any]]) -> tuple[list[tuple[str, ...]], list[tuple[str, ...]]]:
    rows: list[tuple[str, ...]] = []
    tips: list[tuple[str, ...]] = []
    for number, group in enumerate(groups, 1):
        for filename in group["files"]:
            rows.append((str(number), filename, str(group["size_bytes"])))
            tip = f"{filename}\nSHA-256: {group['sha256']}\nGrupo: {number}"
            tips.append((tip, tip, tip))
    return rows, tips


def date_plan_rows(actions: list[dict[str, Any]]) -> tuple[list[tuple[str, ...]], list[tuple[str, ...]]]:
    rows: list[tuple[str, ...]] = []
    for item in actions:
        observation = item.get("reason") or (
            "Subpasta futura" if item.get("directory_would_need_creation")
            else "Destino disponível"
        )
        if item.get("possible_duplicate_by_metadata"):
            observation += " · Suspeita"
        rows.append((
            str(item["file"]), str(item.get("destination") or "—"),
            str(item["status"]), str(observation),
        ))
    # A tabela de planos usa o próprio texto da célula como tooltip.
    return rows, list(rows)


def catalog_rows(
    files: list[dict[str, Any]], date_format: str,
) -> tuple[list[tuple[str, ...]], list[tuple[str | None, ...]]]:
    rows: list[tuple[str, ...]] = []
    raw_roles: list[tuple[str | None, ...]] = []
    for item in files:
        rows.append((
            item["relative_path"], item["category"], item["extension"],
            str(item["size_bytes"]), display_timestamp(item["modified_utc"], date_format),
        ))
        raw_roles.append((None, None, None, None, item["modified_utc"]))
    return rows, raw_roles
