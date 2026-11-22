"""Planejador de operações: somente simulação. NÃO contém execução de movimentos.

O plano é uma proposta informativa, nunca uma autorização nem um comando.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
import os
from typing import Any

from .catalog import DEFAULT_DB, query_catalog, query_catalog_page

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


def propose_date_moves(
    destination: str | Path,
    category: str,
    db_path: Path = DEFAULT_DB,
    limit: int = MAX_PLAN_ITEMS,
    scan_id: int | None = None,
) -> dict[str, Any]:
    """Simula organização ano/mês por modified_utc; NÃO cria pastas nem move arquivos.

    Examina somente uma página limitada do snapshot escolhido. O diretório-base
    deve existir, mas os subdiretórios AAAA/MM são apenas destinos propostos.
    """
    if category not in ALLOWED_CATEGORIES:
        raise ValueError("Categoria inválida: imagem, video ou audio.")
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= MAX_PLAN_ITEMS:
        raise ValueError(f"Limite deve estar entre 1 e {MAX_PLAN_ITEMS}.")
    dest = Path(destination).expanduser().absolute()
    if _contains_symlink(dest) or not dest.is_dir():
        raise ValueError("Destino-base deve ser diretório real já existente, sem links simbólicos.")

    snapshot = query_catalog_page(
        db_path=db_path, category=category, page=1,
        page_size=limit, scan_id=scan_id, sort_by="name",
    )
    if snapshot["scan_id"] is None:
        raise ValueError("Catálogo sem inventário.")
    root = Path(snapshot["root"]).absolute()
    if _contains_symlink(root) or not root.is_dir():
        raise ValueError("Origem do catálogo não está disponível ou contém link simbólico.")

    actions: list[dict[str, Any]] = []
    blocked = 0
    reserved_targets: set[str] = set()
    # Suspeitas por metadados, não duplicatas confirmadas por conteúdo.
    # Nome-base normalizado + extensão + tamanho são apenas indícios.
    metadata_groups: dict[tuple[str, int], int] = {}
    for row in snapshot["files"]:
        key = (PurePosixPath(row["relative_path"]).name.casefold(), row["size_bytes"])
        if row["size_bytes"] > 0:
            metadata_groups[key] = metadata_groups.get(key, 0) + 1
    potential_duplicates = 0
    name_collisions = 0
    for item in snapshot["files"]:
        relative = PurePosixPath(item["relative_path"])
        reason = None
        target: Path | None = None
        source: Path | None = None
        if (relative.is_absolute() or not relative.parts
                or any(part in (".", "..") for part in relative.parts)
                or "\\" in item["relative_path"] or ":" in item["relative_path"]):
            reason = "caminho_invalido"
        else:
            source = root.joinpath(*relative.parts)
            try:
                modified = datetime.fromisoformat(item["modified_utc"])
                if modified.tzinfo is None:
                    raise ValueError("Data sem fuso UTC.")
                modified = modified.astimezone(timezone.utc)
                year, month = modified.strftime("%Y"), modified.strftime("%m")
                target = dest / year / month / source.name
            except (TypeError, ValueError, OverflowError):
                reason = "data_invalida"
            if reason is None and target is not None:
                target_key = os.path.normcase(os.path.abspath(target))
                source_key = os.path.normcase(os.path.abspath(source))
                if _contains_symlink(source) or not source.is_file():
                    reason = "origem_ausente_ou_link"
                elif _contains_symlink(target):
                    reason = "destino_com_link"
                elif (target.parent.exists() and not target.parent.is_dir()):
                    reason = "pasta_destino_invalida"
                elif target_key == source_key:
                    reason = "mesmo_caminho"
                elif target_key in reserved_targets:
                    reason = "destino_duplicado_no_plano"
                elif target.exists():
                    reason = "destino_ja_existe"
                else:
                    try:
                        info = source.stat()
                        if (info.st_size != item["size_bytes"]
                                or abs(info.st_mtime - modified.timestamp()) > 0.001):
                            reason = "origem_alterada_desde_inventario"
                    except (OSError, ValueError, OverflowError):
                        reason = "metadados_indisponiveis"

        key = (relative.name.casefold(), item["size_bytes"])
        suspected = item["size_bytes"] > 0 and metadata_groups.get(key, 0) > 1
        if suspected:
            potential_duplicates += 1

        # Alternativa apenas textual para colisões; a ação continua bloqueada.
        alternative = None
        if reason in ("destino_duplicado_no_plano", "destino_ja_existe") and target is not None:
            name_collisions += 1
            for number in range(2, 22):
                candidate = target.with_name(f"{target.stem}__{number}{target.suffix}")
                candidate_key = os.path.normcase(os.path.abspath(candidate))
                if (candidate_key not in reserved_targets and not candidate.exists()
                        and not _contains_symlink(candidate)):
                    alternative = str(candidate)
                    break
        action = {
            "file": item["relative_path"],
            "source": str(source) if source else None,
            "destination": str(target) if target else None,
            "status": "bloqueado" if reason else "proposto",
            "modified_utc": item["modified_utc"],
            "possible_duplicate_by_metadata": suspected,
            "alternative_name_suggestion": alternative,
        }
        if reason:
            action["reason"] = reason
            blocked += 1
        elif target is not None:
            reserved_targets.add(os.path.normcase(os.path.abspath(target)))
            action["directory_would_need_creation"] = not target.parent.is_dir()
        actions.append(action)

    return {
        "schema_version": 1,
        "operation": "organize_by_modified_date",
        "mode": "simulation",
        "executable": False,
        "requires_explicit_approval": True,
        "date_basis": "modified_utc",
        "directory_pattern": "AAAA/MM",
        "scan_id": snapshot["scan_id"],
        "root": str(root),
        "destination": str(dest),
        "category": category,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "selected": len(actions),
        "total_matches": snapshot["count"],
        "truncated": snapshot["count"] > limit,
        "blocked": blocked,
        "potential_duplicate_items": potential_duplicates,
        "name_collisions": name_collisions,
        "duplicate_detection": "metadata_only_name_and_size_not_verified",
        "actions": actions,
    }
