"""Detecção de conteúdo idêntico via SHA-256, exclusivamente em leitura.

A análise observa uma amostra limitada de UM snapshot; não altera arquivos nem SQLite.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
import hashlib
import os
from pathlib import Path, PurePosixPath
from typing import Any

from .catalog import DEFAULT_DB, query_catalog_page

MAX_FILES = 100
MAX_FILE_BYTES = 16 * 1024 * 1024
MAX_TOTAL_HASH_BYTES = 64 * 1024 * 1024
CHUNK_BYTES = 256 * 1024


def _is_symlink_component(path: Path) -> bool:
    return any(part.is_symlink() for part in (path, *path.parents))


def _candidate_path(root: Path, relative_path: str) -> Path:
    if not isinstance(relative_path, str) or "\\" in relative_path or ":" in relative_path:
        raise ValueError("caminho_invalido")
    relative = PurePosixPath(relative_path)
    if (relative.is_absolute() or not relative.parts
            or any(part in (".", "..") for part in relative.parts)):
        raise ValueError("caminho_invalido")
    candidate = root.joinpath(*relative.parts)
    if _is_symlink_component(candidate):
        raise ValueError("link_simbolico")
    if not candidate.is_file():
        raise ValueError("arquivo_ausente")
    return candidate


def _sha256_checked(path: Path, expected_size: int, expected_modified: str) -> str:
    """Lê em blocos e revalida metadados; não grava nem mantém conteúdo em RAM."""
    flags = os.O_RDONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags)
    with os.fdopen(fd, "rb") as stream:
        before = os.fstat(stream.fileno())
        expected_timestamp = datetime.fromisoformat(expected_modified).timestamp()
        if (before.st_size != expected_size
                or abs(before.st_mtime - expected_timestamp) > 0.001):
            raise ValueError("arquivo_alterado_desde_inventario")
        hasher = hashlib.sha256()
        read_bytes = 0
        while True:
            chunk = stream.read(CHUNK_BYTES)
            if not chunk:
                break
            read_bytes += len(chunk)
            if read_bytes > expected_size:
                raise ValueError("arquivo_alterado_durante_leitura")
            hasher.update(chunk)
        after = os.fstat(stream.fileno())
        if (read_bytes != expected_size
                or before.st_size != after.st_size
                or before.st_mtime_ns != after.st_mtime_ns):
            raise ValueError("arquivo_alterado_durante_leitura")
        # Um arquivo foi revalidado no handle aberto, mas isso não impede
        # uma alteração posterior: o relatório não é garantia para execução futura.
        return hasher.hexdigest()


def verify_duplicate_hashes(
    db_path: Path = DEFAULT_DB,
    category: str | None = None,
    scan_id: int | None = None,
    limit: int = 50,
    max_file_bytes: int = MAX_FILE_BYTES,
    max_total_bytes: int = MAX_TOTAL_HASH_BYTES,
) -> dict[str, Any]:
    """Identifica grupos de hashes iguais dentro da amostra de até 100 arquivos.

    Só lê conteúdos para tamanhos que aparecem duas ou mais vezes na amostra.
    Arquivos não processados (limite/segurança/erro) não são declarados únicos.
    """
    if (not isinstance(limit, int) or isinstance(limit, bool)
            or not 1 <= limit <= MAX_FILES):
        raise ValueError(f"Limite deve estar entre 1 e {MAX_FILES}.")
    if (not isinstance(max_file_bytes, int) or isinstance(max_file_bytes, bool)
            or not 1 <= max_file_bytes <= MAX_FILE_BYTES):
        raise ValueError("Limite de bytes por arquivo inválido.")
    if (not isinstance(max_total_bytes, int) or isinstance(max_total_bytes, bool)
            or not 1 <= max_total_bytes <= MAX_TOTAL_HASH_BYTES):
        raise ValueError("Limite total de bytes inválido.")

    snapshot = query_catalog_page(
        db_path=db_path, category=category, scan_id=scan_id,
        page=1, page_size=limit, sort_by="name",
    )
    if snapshot["scan_id"] is None:
        raise ValueError("Catálogo sem inventário.")
    root = Path(snapshot["root"]).expanduser().absolute()
    if _is_symlink_component(root) or not root.is_dir():
        raise ValueError("Origem indisponível ou com link simbólico.")

    rows = snapshot["files"]
    by_size: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_size[row["size_bytes"]].append(row)

    hashes: dict[tuple[int, str], list[str]] = defaultdict(list)
    skipped: list[dict[str, str]] = []
    hashed_count = 0
    bytes_read = 0
    candidate_count = sum(
        len(group) for group in by_size.values() if len(group) >= 2
    )
    for size, group in sorted(by_size.items()):
        if len(group) < 2:
            continue
        for row in group:
            name = row["relative_path"]
            if size > max_file_bytes:
                skipped.append({"file": name, "reason": "arquivo_acima_do_limite"})
                continue
            if size > max_total_bytes - bytes_read:
                skipped.append({"file": name, "reason": "limite_total_de_leitura"})
                continue
            try:
                path = _candidate_path(root, name)
                digest = _sha256_checked(path, size, row["modified_utc"])
            except (ValueError, OSError) as exc:
                reason = str(exc) if isinstance(exc, ValueError) else "erro_de_leitura"
                skipped.append({"file": name, "reason": reason})
                continue
            bytes_read += size
            hashed_count += 1
            hashes[(size, digest)].append(name)

    groups = [
        {"sha256": digest, "size_bytes": size, "files": sorted(files),
         "count": len(files)}
        for (size, digest), files in hashes.items()
        if len(files) >= 2
    ]
    groups.sort(key=lambda group: (group["files"][0].casefold(), group["sha256"]))
    return {
        "operation": "verify_duplicates_sha256",
        "mode": "read_only",
        "executable": False,
        "files_modified": False,
        "scan_id": snapshot["scan_id"],
        "root": str(root),
        "category": category,
        "total_matches": snapshot["count"],
        "selected": len(rows),
        "truncated": snapshot["count"] > len(rows),
        "hash_candidates": candidate_count,
        "hashed_files": hashed_count,
        "bytes_read": bytes_read,
        "max_file_bytes": max_file_bytes,
        "max_total_bytes": max_total_bytes,
        "confirmed_groups_in_sample": len(groups),
        "confirmed_files_in_sample": sum(group["count"] for group in groups),
        "groups": groups,
        "skipped": skipped,
        "scope_note": (
            "SHA-256 confirma conteúdo igual apenas nos arquivos efetivamente lidos "
            "da amostra; não demonstra ausência de duplicatas no catálogo inteiro."
        ),
    }
