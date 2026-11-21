"""Planejador de operações: somente simulação. NÃO contém execução de movimentos.

O plano é uma proposta informativa, nunca uma autorização nem um comando.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
import os
from typing import Any

from .catalog import DEFAULT_DB, query_catalog

ALLOWED_CATEGORIES = frozenset(("imagem", "video", "audio"))
MAX_PLAN_ITEMS = 100


def _contains_symlink(path: Path) -> bool:
    """Rejeita links simbólicos em qualquer componente existente."""
    return any(part.is_symlink() for part in (path, *path.parents))


def propose_moves(
    destination: str | Path,
    category: str,
    db_path: Path = DEFAULT_DB,
    limit: int = MAX_PLAN_ITEMS,
) -> dict[str, Any]:
    """Gera prévia de arquivos do último snapshot; não move nem escreve nada."""
    if category not in ALLOWED_CATEGORIES:
        raise ValueError("Categoria inválida: imagem, video ou audio.")
    if not isinstance(limit, int) or isinstance(limit, bool) or not (1 <= limit <= MAX_PLAN_ITEMS):
        raise ValueError(f"Limite deve estar entre 1 e {MAX_PLAN_ITEMS}.")

    dest = Path(destination).expanduser().absolute()
    if _contains_symlink(dest) or not dest.is_dir():
        raise ValueError("Destino deve ser diretório real já existente, sem links simbólicos.")

    snapshot = query_catalog(db_path=db_path, category=category)
    if snapshot["scan_id"] is None:
        raise ValueError("Catálogo sem inventário.")
    root = Path(snapshot["root"]).absolute()
    if _contains_symlink(root) or not root.is_dir():
        raise ValueError("Origem do catálogo não está disponível ou contém link simbólico.")

    # Limitação deliberada: não enumerar milhares de ações em uma única prévia.
    candidates = snapshot["files"][:limit]
    actions: list[dict[str, Any]] = []
    blocked = 0
    reserved_targets: set[str] = set()
    for item in candidates:
        relative = PurePosixPath(item["relative_path"])
        if (relative.is_absolute() or not relative.parts
                or any(part in (".", "..") for part in relative.parts)
                or "\\" in item["relative_path"] or ":" in item["relative_path"]):
            actions.append({"file": item["relative_path"], "status": "bloqueado", "reason": "caminho_invalido"})
            blocked += 1
            continue
        source = root.joinpath(*relative.parts)
        target = dest / source.name
        reason = None
        if _contains_symlink(source) or not source.is_file():
            reason = "origem_ausente_ou_link"
        elif os.path.normcase(os.path.abspath(target)) in reserved_targets:
            reason = "destino_duplicado_no_plano"
        elif _contains_symlink(target) or target.exists():
            reason = "destino_ja_existe_ou_link"
        elif os.path.normcase(os.path.abspath(source)) == os.path.normcase(os.path.abspath(target)):
            reason = "mesmo_caminho"
        else:
            try:
                info = source.stat()
                if (info.st_size != item["size_bytes"]
                        or abs(info.st_mtime - datetime.fromisoformat(
                            item["modified_utc"]).timestamp()) > 0.001):
                    reason = "origem_alterada_desde_inventario"
            except (OSError, ValueError):
                reason = "metadados_indisponiveis"
        actions.append({
            "file": item["relative_path"],
            "source": str(source),
            "destination": str(target),
            "status": "bloqueado" if reason else "proposto",
            **({"reason": reason} if reason else {}),
        })
        if reason:
            blocked += 1
        else:
            reserved_targets.add(os.path.normcase(os.path.abspath(target)))

    return {
        "schema_version": 1,
        "operation": "move",
        "mode": "simulation",
        "executable": False,
        "requires_explicit_approval": True,
        "scan_id": snapshot["scan_id"],
        "root": str(root),
        "destination": str(dest),
        "category": category,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "selected": len(actions),
        "total_matches": snapshot["count"],
        "truncated": snapshot["count"] > limit,
        "blocked": blocked,
        "actions": actions,
    }
