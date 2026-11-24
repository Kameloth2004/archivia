"""Helpers puros da GUI: validação de respostas, sem PySide6 nem efeitos no disco.

Os contratos descrevem apenas campos obrigatórios para exibição e não alteram
a estrutura retornada pelo backend. Dados ausentes são erros, nunca zeros.
"""
from __future__ import annotations

from typing import Any

_REQUIRED: dict[str, tuple[str, ...]] = {
    "analyze_source": ("root", "scan_id", "summary", "read_only", "files_modified"),
    "prepare_organization": ("actions", "total_matches", "proposed", "blocked", "complete", "pending"),
    "refresh_folder_session": ("root", "updated"),
    "summary": ("scan_id",),
    "inventory_preview": ("root", "summary", "errors", "files"),
    "catalog_verified_preview": ("scan_id",),
    "origins": ("origins", "origins_count", "indexed_files", "media_files", "overlap_warning"),
    "duplicate_hash": ("groups", "selected", "total_matches", "truncated", "skipped",
                       "scan_id", "hashed_files", "confirmed_groups_in_sample",
                       "confirmed_files_in_sample", "pages_scanned"),
    "date_plan": ("actions", "selected", "blocked", "truncated",
                  "scan_id", "total_matches"),
    "catalog_page": ("page", "pages", "files", "count", "scan_id"),
    "agent": ("answer", "tools_used"),
    "move_queue": ("operation", "requested", "processed", "moved", "pending", "results", "note"),
    "move_batch": ("operation", "requested", "processed", "moved", "pending", "results", "note"),
    "move_conflict": ("status", "source", "destination", "sha256"),
    "move_one": ("status", "source", "destination", "sha256"),
    "manual_copy": ("status", "source", "destination", "sha256",
                    "source_preserved", "files_copied", "journal"),
}
_SUMMARY_FIELDS = ("indexed_files", "media_files", "bytes_media", "by_category")
_PREVIEW_SUMMARY_FIELDS = ("indexed_files", "media_files", "by_category")


def validate_gui_result(mode: str, result: Any) -> None:
    """Recusa respostas incompletas antes de alterar widgets.

    Ausência de uma chave obrigatória gera erro claro; campos opcionais não
    recebem valores fabricados. Modos desconhecidos não são permitidos.
    """
    if mode == "history":
        if not isinstance(result, list):
            raise ValueError("Resultado inválido para histórico: esperada lista.")
        for i, item in enumerate(result):
            _require_mapping(item, ("id", "scanned_utc", "indexed_files", "root"),
                             f"history[{i}]")
        return
    if mode not in _REQUIRED:
        raise ValueError(f"Modo de resultado não autorizado: {mode}.")
    _require_mapping(result, _REQUIRED[mode], mode)
    if mode == "summary" and result["scan_id"] is not None:
        _require_mapping(result, _SUMMARY_FIELDS, "summary")
        _require_mapping(result["by_category"], (), "summary.by_category")
    if mode == "inventory_preview":
        _require_mapping(result["summary"], _PREVIEW_SUMMARY_FIELDS, "inventory_preview.summary")
        _require_mapping(result["summary"]["by_category"], (), "inventory_preview.by_category")
    if mode == "date_plan":
        _require_sequence(result["actions"], "date_plan.actions")
        for i, item in enumerate(result["actions"]):
            _require_mapping(item, ("file", "status"), f"date_plan.actions[{i}]")
    if mode == "duplicate_hash":
        _require_sequence(result["groups"], "duplicate_hash.groups")
        _require_sequence(result["skipped"], "duplicate_hash.skipped")
    if mode == "catalog_page":
        _require_sequence(result["files"], "catalog_page.files")
        for i, item in enumerate(result["files"]):
            _require_mapping(item, ("relative_path", "category", "extension",
                                   "size_bytes", "modified_utc"), f"catalog_page.files[{i}]")


def _require_mapping(value: Any, required: tuple[str, ...], context: str) -> None:
    if not isinstance(value, dict):
        raise ValueError(f"Resultado inválido em {context}: esperado dicionário.")
    absent = [key for key in required if key not in value]
    if absent:
        raise ValueError(
            f"Resultado incompleto em {context}: faltam campos {', '.join(absent)}."
        )


def _require_sequence(value: Any, context: str) -> None:
    if not isinstance(value, list):
        raise ValueError(f"Resultado inválido em {context}: esperada lista.")


def can_save_inventory_preview(
    preview: Any, selected_folder: str, preview_source: str | None,
) -> bool:
    """Apenas uma prévia válida da pasta selecionada pode ser catalogada.

    Controle de interface; o backend continua reexaminando antes de gravar.
    """
    return (
        isinstance(preview, dict)
        and isinstance(preview.get("summary"), dict)
        and isinstance(preview["summary"].get("indexed_files"), int)
        and not isinstance(preview["summary"]["indexed_files"], bool)
        and isinstance(preview.get("errors"), list)
        and not preview["errors"]
        and bool(selected_folder.strip())
        and selected_folder.strip() == preview_source
    )
