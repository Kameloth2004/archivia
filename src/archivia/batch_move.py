"""Execução supervisionada, sequencial e limitada, de propostas do mesmo plano.

O lote não é ferramenta do Ollama. A GUI confirma explicitamente a seleção.
Cada arquivo é revalidado independentemente pelo executor unitário.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from .catalog import DEFAULT_DB
from .move_executor import APPROVAL_PHRASE, MoveSkippedError, move_one_approved

MAX_BATCH_FILES = 20


def move_batch_approved(
    plan: dict[str, Any] | None, files: list[str], *,
    db_path: Path = DEFAULT_DB, scan_id: int | None = None,
    approval: str = "", progress: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Executa o subconjunto selecionado; interrompe no primeiro erro ou cópia retida.

    Não oferece transação/rollback: operações concluídas permanecem concluídas.
    """
    if approval != APPROVAL_PHRASE:
        raise ValueError("Autorização explícita do lote é obrigatória.")
    if (not isinstance(plan, dict) or plan.get("mode") != "simulation"
            or plan.get("executable") is not False
            or plan.get("operation") != "move_recursive_consolidation"
            or plan.get("complete") is not True or plan.get("pending") != 0
            or not isinstance(scan_id, int) or isinstance(scan_id, bool)
            or plan.get("scan_id") != scan_id or not isinstance(plan.get("actions"), list)):
        raise ValueError("Plano incompleto, inválido ou de outro snapshot.")
    if (not isinstance(files, list) or not 1 <= len(files) <= MAX_BATCH_FILES
            or any(not isinstance(f, str) or not f or len(f) > 512 for f in files)
            or len(set(files)) != len(files)):
        raise ValueError("Selecione de 1 a 20 arquivos distintos e válidos.")
    permitted = {a["file"] for a in plan["actions"]
                 if isinstance(a, dict) and a.get("status") == "proposto"
                 and a.get("reason") is None and isinstance(a.get("file"), str)}
    if any(f not in permitted for f in files):
        raise ValueError("A seleção contém arquivo não proposto no plano.")
    if progress is not None and not callable(progress):
        raise ValueError("Progresso inválido.")
    rows: list[dict[str, Any]] = []
    stopped = False
    for name in files:
        try:
            row = move_one_approved(
                plan, name, db_path=db_path, scan_id=scan_id,
                approval=approval,
            )
            row["file"] = name
        except MoveSkippedError as exc:
            row = {"file": name, "status": "bloqueado",
                   "detail": str(exc), "files_modified": False}
        except (OSError, ValueError, RuntimeError) as exc:
            row = {"file": name, "status": "erro",
                   "detail": str(exc), "files_modified": False}
        rows.append(row)
        if progress is not None:
            progress({"processed": len(rows), "total": len(files),
                      "file": name, "status": row["status"]})
        if row["status"] not in ("movido", "bloqueado"):
            stopped = True
            break
    moved = sum(r["status"] == "movido" for r in rows)
    return {
        "operation": "approved_batch_move",
        "requested": len(files),
        "processed": len(rows),
        "moved": moved,
        "blocked": sum(r["status"] == "bloqueado" for r in rows),
        "errors": sum(r["status"] == "erro" for r in rows),
        "stopped": stopped,
        "pending": len(files) - len(rows),
        "results": rows,
        "files_modified": moved > 0 or any(
            r["status"] == "copiado_origem_preservada" for r in rows
        ),
        "note": ("Bloqueios seguros não interrompem o lote. Falhas críticas interrompem. "
                 "O lote não é transacional e arquivos movidos não são revertidos."),
    }
