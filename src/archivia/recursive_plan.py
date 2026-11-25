"""Planejamento recursivo detalhado de consolidação (SOMENTE LEITURA).

Usa o snapshot da origem, inclusive arquivos das subpastas. Produz ações
informativas de uma categoria até limite explícito, nunca executáveis.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path, PurePosixPath
import os
from typing import Any

from .catalog import DEFAULT_DB, query_catalog_page
from .planner import ALLOWED_CATEGORIES, _contains_symlink

_PAGE_SIZE = 100
# Limite defensivo de memória para planejamentos completos na interface.
# O agente continua limitado a 500 ações por chamada.
_MAX_ITEMS = 100_000


def propose_recursive_consolidation(
    destination: str | Path, category: str, db_path: Path = DEFAULT_DB,
    *, scan_id: int | None = None, limit: int | None = 100,
    recursive: bool = True,
) -> dict[str, Any]:
    """Propõe juntar arquivos de todas as subpastas numa pasta existente.

    Se total_matches > limit, 'complete' será falso e 'pending' positivo.
    A ausência de erros na amostra NÃO autoriza executar o restante.
    """
    if category not in ALLOWED_CATEGORIES:
        raise ValueError("Categoria inválida para planejamento recursivo.")
    if not isinstance(recursive, bool):
        raise ValueError("Escopo de análise inválido.")
    if limit is not None and (
        not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= _MAX_ITEMS
    ):
        raise ValueError(f"Limite deve estar entre 1 e {_MAX_ITEMS}.")
    if scan_id is not None and (
        not isinstance(scan_id, int) or isinstance(scan_id, bool) or scan_id < 1
    ):
        raise ValueError("Snapshot inválido.")

    dest = Path(destination).expanduser().absolute()
    if _contains_symlink(dest) or not dest.is_dir():
        raise ValueError("Destino deve ser pasta existente, sem links simbólicos.")

    first = query_catalog_page(
        db_path=db_path, category=category, scan_id=scan_id,
        page=1, page_size=_PAGE_SIZE, sort_by="name",
    )
    if first["scan_id"] is None:
        raise ValueError("Nenhum inventário disponível.")
    root = Path(first["root"]).expanduser().absolute()
    if _contains_symlink(root) or not root.is_dir():
        raise ValueError("Origem do snapshot indisponível ou contém link simbólico.")
    if dest == root:
        raise ValueError("Origem e destino não podem ser a mesma pasta.")
    nested_destination = root in dest.parents

    total = first["count"]
    occupied = {item.name.casefold() for item in dest.iterdir()}
    reserved: set[str] = set()
    actions: list[dict[str, Any]] = []
    by_reason: dict[str, int] = {}
    # None solicita planejamento completo. O teto de memória é explícito e
    # nunca é tratado como conclusão se houver mais correspondências.
    limit_actual = min(_MAX_ITEMS if limit is None else limit, total)

    for page_number in range(1, (limit_actual + _PAGE_SIZE - 1) // _PAGE_SIZE + 1):
        page = first if page_number == 1 else query_catalog_page(
            db_path=db_path, category=category, scan_id=first["scan_id"],
            page=page_number, page_size=_PAGE_SIZE, sort_by="name",
        )
        if page["scan_id"] != first["scan_id"] or page["count"] != total or not page["files"]:
            raise ValueError("Snapshot mudou ou paginação incompleta durante a simulação.")
        for item in page["files"]:
            if len(actions) >= limit_actual:
                break
            text = item["relative_path"]
            rel = PurePosixPath(text)
            source: Path | None = None
            target: Path | None = None
            reason: str | None = None
            if (
                rel.is_absolute() or not rel.parts
                or any(part in (".", "..") for part in rel.parts)
                or "\\" in text or ":" in text
            ):
                reason = "caminho_invalido"
            elif not recursive and len(rel.parts) != 1:
                # Proteção adicional: um plano de escopo local nunca pode
                # selecionar conteúdo das subpastas, mesmo em snapshot alterado.
                reason = "fora_do_escopo"
            else:
                source = root.joinpath(*rel.parts)
                target = dest / source.name
                name = source.name.casefold()
                if nested_destination and (source == dest or dest in source.parents):
                    # O snapshot pode conter arquivos que já estão no destino.
                    # Nunca proponha movê-los para o próprio diretório ou novamente.
                    reason = "ja_no_destino"
                elif _contains_symlink(source) or not source.is_file():
                    reason = "origem_ausente_ou_link"
                elif source == target:
                    reason = "mesmo_caminho"
                elif name in occupied or target.exists() or _contains_symlink(target):
                    reason = "destino_ja_existe"
                elif name in reserved:
                    reason = "nome_repetido_entre_subpastas"
                else:
                    try:
                        metadata = source.stat(follow_symlinks=False)
                        expected = datetime.fromisoformat(item["modified_utc"]).timestamp()
                        if (
                            metadata.st_size != item["size_bytes"]
                            or abs(metadata.st_mtime - expected) > 0.001
                        ):
                            reason = "origem_alterada_desde_inventario"
                    except (OSError, TypeError, ValueError, OverflowError):
                        reason = "metadados_indisponiveis"
                if reason is None:
                    reserved.add(name)
            actions.append({
                "file": text,
                "source": str(source) if source else None,
                "destination": str(target) if target else None,
                "status": "bloqueado" if reason else "proposto",
                "reason": reason,
            })

    if len(actions) != limit_actual:
        raise ValueError("Plano incompleto; não prosseguir.")

    # Uma pasta única de destino não pode receber automaticamente dois
    # arquivos com o mesmo nome-base, inclusive quando diferem só na caixa.
    # A verificação abrange TODAS as ações examinadas e não escolhe uma
    # origem vencedora baseada na ordenação ou na posição no snapshot.
    basename_counts: dict[str, int] = {}
    for action in actions:
        if isinstance(action.get("source"), str):
            name = Path(action["source"]).name.casefold()
            basename_counts[name] = basename_counts.get(name, 0) + 1
    for action in actions:
        if action["status"] == "proposto":
            name = Path(action["source"]).name.casefold()
            if basename_counts.get(name, 0) > 1:
                action["status"] = "bloqueado"
                action["reason"] = "nome_repetido_entre_subpastas"

    # Recalcular após a verificação global: ela também pode bloquear a
    # primeira ocorrência, que antes aparecia indevidamente como proposta.
    by_reason = {}
    for action in actions:
        reason = action.get("reason")
        if reason:
            by_reason[reason] = by_reason.get(reason, 0) + 1
    blocked = sum(a["status"] == "bloqueado" for a in actions)
    return {
        "schema_version": 1, "operation": "move_recursive_consolidation",
        "mode": "simulation", "executable": False,
        "requires_explicit_approval": True, "recursive": recursive,
        "root": str(root), "destination": str(dest),
        "category": category, "scan_id": first["scan_id"],
        "destination_inside_root": nested_destination,
        "total_matches": total, "examined": len(actions),
        "proposed": len(actions) - blocked, "blocked": blocked,
        "pending": total - len(actions), "complete": len(actions) == total,
        "truncated": len(actions) < total, "blocked_by_reason": by_reason,
        "actions": actions,
        "files_modified": False,
    }
