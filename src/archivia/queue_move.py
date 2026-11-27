"""Fila supervisionada de movimentação: sem ferramenta Ollama.

Sem rollback automático. Interrupção cooperativa ocorre antes do próximo arquivo.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from .catalog import DEFAULT_DB
from .move_executor import APPROVAL_PHRASE, move_one_approved
from .move_orchestration import validate_selection, process_selection

MAX_QUEUE_FILES = 10_000


def move_queue_approved(
    plan: dict[str, Any] | None, files: list[str], *,
    db_path: Path = DEFAULT_DB, scan_id: int | None = None,
    approval: str = "",
    progress: Callable[[dict[str, Any]], None] | None = None,
    interrupted: Callable[[], bool] | None = None,
) -> dict[str, Any]:
    """Executa fila supervisionada sem execução parcial silenciosa."""
    validate_selection(
        plan, files, scan_id=scan_id, approval=approval,
        limit=MAX_QUEUE_FILES, progress=progress, interrupted=interrupted,
        reject_ambiguous_plan=True,
        messages=(
            "A movimentação exige confirmação explícita.",
            "O plano não está completo ou pertence a outra análise.",
            "Seleção inválida ou acima do limite da fila.",
            "Há arquivos não aprováveis ou ambíguos na seleção.",
            "Callbacks inválidos.",
        ),
    )
    rows, stopped_reason = process_selection(
        plan, files, db_path=db_path, scan_id=scan_id, approval=approval,
        execute_one=move_one_approved, progress=progress, interrupted=interrupted,
    )
    return {
        "operation": "approved_queue_move",
        "requested": len(files), "processed": len(rows),
        "moved": sum(r["status"] == "movido" for r in rows),
        "pending": len(files) - len(rows),
        "stopped": stopped_reason is not None,
        "stopped_reason": stopped_reason,
        "blocked": sum(r["status"] == "bloqueado" for r in rows),
        "errors": sum(r["status"] == "erro" for r in rows),
        "results": rows,
        "files_modified": any(r["status"] in ("movido", "copiado_origem_preservada")
                              for r in rows),
        "note": ("Bloqueios seguros não interrompem a fila. Falhas de integridade "
                 "interrompem imediatamente. Não há reversão automática."),
    }
