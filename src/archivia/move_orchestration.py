"""Núcleo compartilhado de orquestração de movimentos supervisionados.

Não é um executor e não é uma ferramenta Ollama. Mantém a aprovação e as
restrições dos adaptadores batch_move e queue_move, sem alterar arquivos por si.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from .move_executor import APPROVAL_PHRASE, MoveSkippedError


def validate_selection(
    plan: dict[str, Any] | None, files: list[str], *,
    scan_id: int | None, approval: str, limit: int,
    messages: tuple[str, str, str, str, str],
    reject_ambiguous_plan: bool = False,
    progress: Callable[[dict[str, Any]], None] | None = None,
    interrupted: Callable[[], bool] | None = None,
) -> None:
    """Validação comum, preservando mensagens e diferenças de cada interface.

    messages: aprovação, plano, seleção, membros, callbacks.
    """
    approval_error, plan_error, selection_error, membership_error, callbacks_error = messages
    if approval != APPROVAL_PHRASE:
        raise ValueError(approval_error)
    if (
        not isinstance(plan, dict) or plan.get("mode") != "simulation"
        or plan.get("executable") is not False
        or plan.get("operation") != "move_recursive_consolidation"
        or plan.get("complete") is not True or plan.get("pending") != 0
        or not isinstance(scan_id, int) or isinstance(scan_id, bool)
        or plan.get("scan_id") != scan_id
        or not isinstance(plan.get("actions"), list)
    ):
        raise ValueError(plan_error)
    if (
        not isinstance(files, list) or not 1 <= len(files) <= limit
        or any(not isinstance(f, str) or not f or len(f) > 512 for f in files)
        or len(set(files)) != len(files)
    ):
        raise ValueError(selection_error)
    permitted = [
        action.get("file") for action in plan["actions"]
        if isinstance(action, dict) and action.get("status") == "proposto"
        and action.get("reason") is None and isinstance(action.get("file"), str)
    ]
    if (
        reject_ambiguous_plan and len(permitted) != len(set(permitted))
    ) or not set(files).issubset(set(permitted)):
        raise ValueError(membership_error)
    if (
        (progress is not None and not callable(progress))
        or (interrupted is not None and not callable(interrupted))
    ):
        raise ValueError(callbacks_error)


def process_selection(
    plan: dict[str, Any], files: list[str], *,
    db_path: Path, scan_id: int, approval: str,
    execute_one: Callable[..., dict[str, Any]],
    progress: Callable[[dict[str, Any]], None] | None = None,
    interrupted: Callable[[], bool] | None = None,
) -> tuple[list[dict[str, Any]], str | None]:
    """Move sequencialmente, parando em falha perigosa ou interrupção cooperativa."""
    rows: list[dict[str, Any]] = []
    stopped_reason: str | None = None
    for name in files:
        if interrupted is not None and interrupted():
            stopped_reason = "interrompido_pelo_usuario"
            break
        try:
            row = execute_one(
                plan, name, db_path=db_path, scan_id=scan_id, approval=approval,
            )
            row["file"] = name
        except MoveSkippedError as exc:
            row = {
                "file": name, "status": "bloqueado",
                "detail": str(exc), "files_modified": False,
            }
        except (ValueError, OSError, RuntimeError) as exc:
            row = {
                "file": name, "status": "erro",
                "detail": str(exc), "files_modified": False,
            }
        rows.append(row)
        if progress is not None:
            progress({
                "processed": len(rows), "total": len(files),
                "file": name, "status": row["status"],
            })
        if row["status"] not in ("movido", "bloqueado"):
            stopped_reason = row["status"]
            break
    return rows, stopped_reason
