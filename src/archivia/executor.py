"""Executor EXPERIMENTAL: somente um arquivo fictício sob tests/.runtime.

Não existe integração com CLI, GUI ou Ollama. Não utilizar com mídias reais.
Este estágio suporta apenas hardlink + remoção no mesmo volume, com journal.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import stat
from typing import Any

from .catalog import DEFAULT_DB
from .planner import propose_moves

_CONFIRM = "CONFIRMO TESTE ARCHIVIA"
_RUNTIME = Path(__file__).resolve().parents[2] / "tests" / ".runtime"


def _safe_path(path: Path) -> Path:
    """Rejeita links simbólicos e junctions inclusive em componentes ancestrais."""
    absolute = path.expanduser().absolute()
    for component in (absolute, *absolute.parents):
        if component.is_symlink() or (
            hasattr(os.path, "isjunction") and os.path.isjunction(component)
        ):
            raise ValueError("Links simbólicos/junctions não são permitidos.")
    return absolute


def _inside_runtime(path: Path) -> tuple[Path, Path]:
    runtime = _safe_path(_RUNTIME)
    candidate = _safe_path(path)
    try:
        parts = candidate.relative_to(runtime).parts
    except ValueError as exc:
        raise ValueError("Executor limitado a tests/.runtime.") from exc
    if len(parts) < 3:
        raise ValueError("Origem/destino devem estar em pastas de teste isoladas.")
    return runtime, runtime / parts[0]


def _record(journal: Path, event: str, source: Path, target: Path) -> None:
    payload = {
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "source": str(source),
        "destination": str(target),
    }
    with journal.open("a", encoding="utf-8") as output:
        output.write(json.dumps(payload, ensure_ascii=False) + "\n")
        output.flush()
        os.fsync(output.fileno())


def execute_test_move(
    plan: dict[str, Any],
    db_path: Path = DEFAULT_DB,
    *,
    approval: str,
) -> dict[str, Any]:
    """Move um único arquivo TEST-ONLY; sem sobrescrita, sem operações por IA.

    A origem e o destino DEVEM estar dentro do mesmo caso de teste isolado.
    Nunca aceitar resumos globais, planos truncados, bloqueados ou arbitrários.
    Falha entre hardlink e remoção pode deixar dois nomes: consultar o journal
    e resolver manualmente; não efetuar rollback automático.
    """
    if approval != _CONFIRM:
        raise ValueError("Confirmação explícita de teste ausente.")
    if not isinstance(plan, dict) or plan.get("mode") != "simulation":
        raise ValueError("Plano inválido.")
    if plan.get("summary_only") or plan.get("executable") is not False:
        raise ValueError("Apenas uma prévia simulada pode ser validada.")
    if plan.get("truncated") or plan.get("blocked") != 0:
        raise ValueError("Plano incompleto ou com conflitos.")
    if plan.get("total_matches") != 1 or plan.get("selected") != 1:
        raise ValueError("Executor experimental aceita exatamente um arquivo.")
    if plan.get("category") not in ("imagem", "video", "audio"):
        raise ValueError("Categoria não autorizada.")
    if not isinstance(plan.get("scan_id"), int) or isinstance(plan["scan_id"], bool):
        raise ValueError("Snapshot inválido.")
    actions = plan.get("actions")
    if not isinstance(actions, list) or len(actions) != 1:
        raise ValueError("Plano deve conter uma única ação.")
    action = actions[0]
    if not isinstance(action, dict) or action.get("status") != "proposto":
        raise ValueError("Ação não aprovada.")

    source = _safe_path(Path(action["source"]))
    target = _safe_path(Path(action["destination"]))
    runtime, test_root = _inside_runtime(source)
    _, dest_test_root = _inside_runtime(target)
    if test_root != dest_test_root or source == target:
        raise ValueError("Origem e destino devem estar no mesmo teste isolado.")
    if not target.parent.is_dir() or not source.is_file():
        raise ValueError("Origem ou destino indisponíveis.")
    if target.exists() or target.is_symlink():
        raise ValueError("Destino já existe.")
    if any(entry.name.casefold() == target.name.casefold()
           for entry in target.parent.iterdir()):
        raise ValueError("Destino equivalente já existe.")

    # Recria a proposta da base SQLite para evitar plano adulterado ou obsoleto.
    refreshed = propose_moves(
        target.parent, plan["category"], db_path=db_path,
        limit=1, scan_id=plan["scan_id"],
    )
    if (refreshed["root"] != plan.get("root") or
            refreshed["destination"] != plan.get("destination") or
            refreshed["total_matches"] != 1 or refreshed["blocked"] or
            refreshed["truncated"] or refreshed["actions"] != actions):
        raise ValueError("Plano não corresponde mais ao catálogo ou ao disco.")

    before = source.stat(follow_symlinks=False)
    if not stat.S_ISREG(before.st_mode):
        raise ValueError("Origem não é arquivo regular.")
    if before.st_dev != target.parent.stat().st_dev:
        raise ValueError("Movimentação entre volumes ainda não está disponível.")

    journal = test_root / "archivia-executor-journal.jsonl"
    _record(journal, "PREPARADO", source, target)
    try:
        # Criação atômica sem sobrescrita; suportada apenas no mesmo volume.
        os.link(source, target, follow_symlinks=False)
    except OSError as exc:
        _record(journal, "FALHA_CRIACAO", source, target)
        raise ValueError(f"Não foi possível criar destino seguro: {exc}") from exc

    linked = target.stat(follow_symlinks=False)
    current = source.stat(follow_symlinks=False)
    if (linked.st_dev, linked.st_ino) != (before.st_dev, before.st_ino) or (
        current.st_dev, current.st_ino, current.st_size, current.st_mtime_ns
    ) != (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns):
        _record(journal, "INTERROMPIDO_VERIFICACAO", source, target)
        raise ValueError("Origem mudou; dois caminhos podem existir. Consulte o journal.")

    _record(journal, "DESTINO_CRIADO", source, target)
    try:
        os.unlink(source)
    except OSError as exc:
        _record(journal, "INTERROMPIDO_REMOCAO", source, target)
        raise ValueError(
            "Destino criado, mas origem preservada. Consulte o journal antes de repetir."
        ) from exc
    _record(journal, "CONCLUIDO", source, target)
    return {
        "status": "movido",
        "source": str(source),
        "destination": str(target),
        "journal": str(journal),
        "files_moved": 1,
        "test_only": True,
    }
