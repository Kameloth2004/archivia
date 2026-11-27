"""Execução supervisionada de lote pequeno; sem ferramenta Ollama."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from .catalog import DEFAULT_DB
from .move_executor import APPROVAL_PHRASE, move_one_approved
from .move_orchestration import validate_selection, process_selection

MAX_BATCH_FILES = 20


def move_batch_approved(
    plan: dict[str, Any] | None, files: list[str], *,
    db_path: Path = DEFAULT_DB, scan_id: int | None = None,
    approval: str = "", progress: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Executa até 20 ações; interrupção em falha crítica, sem rollback."""
    validate_selection(
        plan, files, scan_id=scan_id, approval=approval,
        limit=MAX_BATCH_FILES, progress=progress,
        messages=(
            "Autorização explícita do lote é obrigatória.",
            "Plano incompleto, inválido ou de outro snapshot.",
            "Selecione de 1 a 20 arquivos distintos e válidos.",
            "A seleção contém arquivo não proposto no plano.",
            "Progresso inválido.",
        ),
    )
    rows, stopped_reason = process_selection(
        plan, files, db_path=db_path, scan_id=scan_id, approval=approval,
        execute_one=move_one_approved, progress=progress,
    )
    moved = sum(r["status"] == "movido" for r in rows)
    return {
        "operation": "approved_batch_move",
        "requested": len(files),
        "processed": len(rows),
        "moved": moved,
        "blocked": sum(r["status"] == "bloqueado" for r in rows),
        "errors": sum(r["status"] == "erro" for r in rows),
        "stopped": stopped_reason is not None,
        "pending": len(files) - len(rows),
        "results": rows,
        "files_modified": moved > 0 or any(
            r["status"] == "copiado_origem_preservada" for r in rows
        ),
        "note": ("Bloqueios seguros não interrompem o lote. Falhas críticas interrompem. "
                 "O lote não é transacional e arquivos movidos não são revertidos."),
    }
