"""Fila supervisionada de movimentação: processa seleções grandes sem liberar o Ollama.

Não há rollback automático. Falhas/interrupções param novos arquivos, mantendo
os já movimentados e a origem dos itens ainda não processados.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from .catalog import DEFAULT_DB
from .move_executor import APPROVAL_PHRASE, MoveSkippedError, move_one_approved

MAX_QUEUE_FILES = 10_000


def move_queue_approved(
    plan: dict[str, Any] | None, files: list[str], *,
    db_path: Path = DEFAULT_DB, scan_id: int | None = None,
    approval: str = "",
    progress: Callable[[dict[str, Any]], None] | None = None,
    interrupted: Callable[[], bool] | None = None,
) -> dict[str, Any]:
    """Move sequencialmente arquivos propostos, sem execução parcial silenciosa."""
    if approval != APPROVAL_PHRASE:
        raise ValueError("A movimentação exige confirmação explícita.")
    if (not isinstance(plan, dict) or plan.get("mode") != "simulation"
            or plan.get("executable") is not False
            or plan.get("operation") != "move_recursive_consolidation"
            or plan.get("complete") is not True or plan.get("pending") != 0
            or not isinstance(scan_id, int) or isinstance(scan_id, bool)
            or plan.get("scan_id") != scan_id or not isinstance(plan.get("actions"), list)):
        raise ValueError("O plano não está completo ou pertence a outra análise.")
    if (not isinstance(files, list) or not 1 <= len(files) <= MAX_QUEUE_FILES
            or any(not isinstance(f, str) or not f or len(f) > 512 for f in files)
            or len(set(files)) != len(files)):
        raise ValueError("Seleção inválida ou acima do limite da fila.")
    permitted = [a.get("file") for a in plan["actions"]
                 if isinstance(a, dict) and a.get("status") == "proposto"
                 and a.get("reason") is None and isinstance(a.get("file"), str)]
    if len(permitted) != len(set(permitted)) or not set(files).issubset(set(permitted)):
        raise ValueError("Há arquivos não aprováveis ou ambíguos na seleção.")
    if (progress is not None and not callable(progress)
            or interrupted is not None and not callable(interrupted)):
        raise ValueError("Callbacks inválidos.")
    rows: list[dict[str, Any]] = []
    stopped_reason = None
    for name in files:
        if interrupted is not None and interrupted():
            stopped_reason = "interrompido_pelo_usuario"
            break
        try:
            row = move_one_approved(
                plan, name, db_path=db_path, scan_id=scan_id,
                approval=approval,
            )
            row["file"] = name
        except MoveSkippedError as exc:
            # Bloqueio previsível ANTES de publicar o destino:
            # preservar origem, registrar e prosseguir.
            row = {"file": name, "status": "bloqueado",
                   "detail": str(exc), "files_modified": False}
        except (ValueError, OSError, RuntimeError) as exc:
            # Estado desconhecido ou falha na cópia/publicação:
            # não processar mais nenhum arquivo até nova análise.
            row = {"file": name, "status": "erro",
                   "detail": str(exc), "files_modified": False}
        rows.append(row)
        if progress is not None:
            progress({"processed": len(rows), "total": len(files),
                      "file": name, "status": row["status"]})
        if row["status"] not in ("movido", "bloqueado"):
            stopped_reason = row["status"]
            break
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
