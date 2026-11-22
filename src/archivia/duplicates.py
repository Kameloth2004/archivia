"""Detecção de conteúdo idêntico via SHA-256, exclusivamente em leitura.

A análise observa uma amostra limitada de UM snapshot; não altera arquivos nem SQLite.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
import hashlib
import os
from pathlib import Path, PurePosixPath
from typing import Any, Callable

from .catalog import DEFAULT_DB, query_catalog_page

MAX_FILES = 1000
PAGE_SIZE = 100
MAX_FILE_BYTES = 16 * 1024 * 1024
MAX_TOTAL_HASH_BYTES = 256 * 1024 * 1024
CHUNK_BYTES = 256 * 1024


def _is_symlink_component(path: Path) -> bool:
    return any(
        part.is_symlink() or (hasattr(part, "is_junction") and part.is_junction())
        for part in (path, *path.parents)
    )


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
    max_total_bytes: int = 64 * 1024 * 1024,
    progress: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """SHA-256 por lotes, em amostra limitada de um único snapshot.

    Lê páginas de até 100 linhas do SQLite. Reúne no máximo 1000 metadados
    para comparar candidatos com o mesmo tamanho, inclusive entre páginas.
    Nunca conclui unicidade de arquivos que não foram processados.
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
    if progress is not None and not callable(progress):
        raise ValueError("Callback de progresso inválido.")

    def report(phase: str, processed: int, total: int) -> None:
        if progress is not None:
            progress({
                "phase": phase, "processed": processed, "total": total,
            })

    rows: list[dict[str, Any]] = []
    total_matches = 0
    selected_snapshot = scan_id
    root: Path | None = None
    pages_scanned = 0
    for page in range(1, (limit + PAGE_SIZE - 1) // PAGE_SIZE + 1):
        length = min(PAGE_SIZE, limit - len(rows))
        batch = query_catalog_page(
            db_path=db_path, category=category, scan_id=selected_snapshot,
            page=page, page_size=length if length == PAGE_SIZE else PAGE_SIZE,
            sort_by="name",
        )
        if batch["scan_id"] is None:
            raise ValueError("Catálogo sem inventário.")
        if selected_snapshot is None:
            selected_snapshot = batch["scan_id"]
            root = Path(batch["root"]).expanduser().absolute()
            total_matches = batch["count"]
        if root is None:
            root = Path(batch["root"]).expanduser().absolute()
            total_matches = batch["count"]
        if batch["scan_id"] != selected_snapshot:
            raise ValueError("Snapshot alterado durante a consulta.")
        # Com OFFSET estável, páginas intermediárias sempre têm PAGE_SIZE.
        rows.extend(batch["files"][:length])
        pages_scanned += 1
        report("catalog", len(rows), min(limit, total_matches))
        if len(rows) >= limit or len(batch["files"]) < PAGE_SIZE:
            break
    assert root is not None
    if _is_symlink_component(root) or not root.is_dir():
        raise ValueError("Origem indisponível ou com link simbólico.")

    by_size: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_size[row["size_bytes"]].append(row)
    hashes: dict[tuple[int, str], list[str]] = defaultdict(list)
    skipped: list[dict[str, str]] = []
    hashed_count = 0
    bytes_read = 0
    bytes_budget_reserved = 0
    candidate_count = sum(
        len(group) for group in by_size.values() if len(group) >= 2
    )
    handled = 0
    report("hash", 0, candidate_count)
    for size, group in sorted(by_size.items()):
        if len(group) < 2:
            continue
        for row in group:
            name = row["relative_path"]
            if size > max_file_bytes:
                skipped.append({"file": name, "reason": "arquivo_acima_do_limite"})
            elif size > max_total_bytes - bytes_budget_reserved:
                skipped.append({"file": name, "reason": "limite_total_de_leitura"})
            else:
                # Reserva quota antes da leitura, inclusive quando ela falha.
                bytes_budget_reserved += size
                try:
                    path = _candidate_path(root, name)
                    digest = _sha256_checked(path, size, row["modified_utc"])
                except (ValueError, OSError) as exc:
                    reason = str(exc) if isinstance(exc, ValueError) else "erro_de_leitura"
                    skipped.append({"file": name, "reason": reason})
                else:
                    bytes_read += size
                    hashed_count += 1
                    hashes[(size, digest)].append(name)
            handled += 1
            if handled % 10 == 0 or handled == candidate_count:
                report("hash", handled, candidate_count)

    groups = [
        {"sha256": digest, "size_bytes": size, "files": sorted(files),
         "count": len(files)}
        for (size, digest), files in hashes.items()
        if len(files) >= 2
    ]
    groups.sort(key=lambda group: (group["files"][0].casefold(), group["sha256"]))
    report("done", len(rows), len(rows))
    return {
        "operation": "verify_duplicates_sha256",
        "mode": "read_only",
        "executable": False,
        "files_modified": False,
        "scan_id": selected_snapshot,
        "root": str(root),
        "category": category,
        "total_matches": total_matches,
        "selected": len(rows),
        "truncated": total_matches > len(rows),
        "page_size": PAGE_SIZE,
        "pages_scanned": pages_scanned,
        "hash_candidates": candidate_count,
        "hashed_files": hashed_count,
        "bytes_read": bytes_read,
        "bytes_budget_reserved": bytes_budget_reserved,
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



MAX_GLOBAL_CANDIDATES = 5000


def verify_snapshot_duplicate_candidates(
    db_path: Path = DEFAULT_DB,
    category: str | None = None,
    scan_id: int | None = None,
    max_candidates: int = 1000,
    max_file_bytes: int = MAX_FILE_BYTES,
    max_total_bytes: int = 64 * 1024 * 1024,
    progress: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Verifica grupos de mesmo tamanho em todo o snapshot, com I/O limitado.

    O SQLite identifica os grupos de tamanho na integralidade do snapshot,
    sem carregar a lista inteira em Python. Grupos são selecionados inteiros:
    se não couberem no orçamento de candidatos, permanecem não verificados.
    SHA-256 e origens continuam estritamente em somente leitura.
    """
    import sqlite3
    from contextlib import closing
    from .inventory import CATEGORIES

    if category is not None and category not in CATEGORIES:
        raise ValueError("Categoria inválida.")
    if scan_id is not None and (
        not isinstance(scan_id, int) or isinstance(scan_id, bool) or scan_id < 1
    ):
        raise ValueError("ID de snapshot inválido.")
    for value, maximum, label in (
        (max_candidates, MAX_GLOBAL_CANDIDATES, "Quantidade de candidatos"),
        (max_file_bytes, MAX_FILE_BYTES, "Limite por arquivo"),
        (max_total_bytes, MAX_TOTAL_HASH_BYTES, "Orçamento de leitura"),
    ):
        if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= maximum:
            raise ValueError(f"{label} inválido: use 1 a {maximum}.")
    if progress is not None and not callable(progress):
        raise ValueError("Callback de progresso inválido.")

    def report(phase: str, processed: int, total: int) -> None:
        if progress is not None:
            progress({"phase": phase, "processed": processed, "total": total})

    db = Path(db_path).expanduser().absolute()
    if not db.is_file():
        raise ValueError(f"Catálogo não encontrado: {db}")

    try:
        with closing(sqlite3.connect(db.as_uri() + "?mode=ro", uri=True)) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA temp_store=MEMORY")
            if scan_id is None:
                scan = conn.execute(
                    "SELECT id, root FROM scans ORDER BY id DESC LIMIT 1"
                ).fetchone()
            else:
                scan = conn.execute(
                    "SELECT id, root FROM scans WHERE id=?", (scan_id,)
                ).fetchone()
            if scan is None:
                raise ValueError("Snapshot não encontrado.")
            selected_scan = scan["id"]
            root = Path(scan["root"]).expanduser().absolute()
            if _is_symlink_component(root) or not root.is_dir():
                raise ValueError("Origem indisponível ou com link simbólico.")

            where = "scan_id=?"
            params: tuple[Any, ...] = (selected_scan,)
            if category is not None:
                where += " AND category=?"
                params += (category,)
            total_matches = conn.execute(
                f"SELECT COUNT(*) FROM media WHERE {where}", params
            ).fetchone()[0]
            # SQL calcula grupos globais: não selecionamos apenas a primeira página.
            sizes = conn.execute(
                f"""SELECT size_bytes, COUNT(*) AS amount FROM media
                    WHERE {where} GROUP BY size_bytes HAVING COUNT(*) > 1
                    ORDER BY size_bytes""", params
            )
            # Guardar somente grupos de tamanho/ccontagem; não guardar caminhos.
            size_groups = [(row["size_bytes"], row["amount"]) for row in sizes]
            candidates_total = sum(amount for _, amount in size_groups)
            report("catalog", total_matches, total_matches)

            processed = 0
            groups_selected = 0
            groups_omitted = 0
            omitted_candidates = 0
            skipped: list[dict[str, str]] = []
            matches: list[dict[str, Any]] = []
            hashed_files = 0
            bytes_read = 0
            budget_reserved = 0
            sql_batches = 0
            for size, amount in size_groups:
                if amount > max_candidates - processed:
                    groups_omitted += 1
                    omitted_candidates += amount
                    continue
                processed += amount
                groups_selected += 1
                digests: dict[str, list[str]] = defaultdict(list)
                cursor = conn.execute(
                    f"""SELECT relative_path, size_bytes, modified_utc FROM media
                        WHERE {where} AND size_bytes=?
                        ORDER BY relative_path COLLATE NOCASE, relative_path""",
                    (*params, size),
                )
                while True:
                    batch = cursor.fetchmany(PAGE_SIZE)
                    if not batch:
                        break
                    sql_batches += 1
                    for row in batch:
                        name = row["relative_path"]
                        if size > max_file_bytes:
                            skipped.append({"file": name, "reason": "arquivo_acima_do_limite"})
                        elif size > max_total_bytes - budget_reserved:
                            skipped.append({"file": name, "reason": "limite_total_de_leitura"})
                        else:
                            budget_reserved += size
                            try:
                                path = _candidate_path(root, name)
                                digest = _sha256_checked(path, size, row["modified_utc"])
                            except (ValueError, OSError) as exc:
                                reason = str(exc) if isinstance(exc, ValueError) else "erro_de_leitura"
                                skipped.append({"file": name, "reason": reason})
                            else:
                                digests[digest].append(name)
                                hashed_files += 1
                                bytes_read += size
                        if (hashed_files + len(skipped)) % 20 == 0:
                            report("hash", hashed_files + len(skipped), processed)
                for digest, files in digests.items():
                    if len(files) >= 2:
                        matches.append({
                            "sha256": digest,
                            "size_bytes": size,
                            "files": sorted(files),
                            "count": len(files),
                        })
                report("hash", processed, candidates_total)

            matches.sort(key=lambda g: (g["files"][0].casefold(), g["sha256"]))
            report("done", processed, processed)
            return {
                "operation": "verify_duplicates_sha256_global",
                "analysis_mode": "global_size_candidates",
                "mode": "read_only",
                "executable": False,
                "files_modified": False,
                "scan_id": selected_scan,
                "root": str(root),
                "category": category,
                "total_matches": total_matches,
                "selected": processed,
                "truncated": bool(omitted_candidates),
                "candidate_files_total": candidates_total,
                "unprocessed_candidate_files": omitted_candidates,
                "size_groups_selected": groups_selected,
                "size_groups_omitted": groups_omitted,
                "pages_scanned": sql_batches,
                "hash_candidates": processed,
                "hashed_files": hashed_files,
                "bytes_read": bytes_read,
                "bytes_budget_reserved": budget_reserved,
                "max_file_bytes": max_file_bytes,
                "max_total_bytes": max_total_bytes,
                "confirmed_groups_in_sample": len(matches),
                "confirmed_files_in_sample": sum(g["count"] for g in matches),
                "groups": matches,
                "skipped": skipped,
                "complete": omitted_candidates == 0 and not skipped,
                "scope_note": (
                    "A seleção por tamanho abrange todo o snapshot, mas apenas grupos "
                    "completos que cabem no limite de candidatos são verificados. "
                    "Orçamento, alterações e erros podem impedir confirmação de duplicatas."
                ),
            }
    except sqlite3.Error as exc:
        raise ValueError(f"Não foi possível consultar o catálogo: {exc}") from exc
