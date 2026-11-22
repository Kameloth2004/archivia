"""Verificação progressiva SHA-256, estritamente em memória e somente leitura.

A sessão fixa snapshot/categoria e avança por ID SQLite, sem reler arquivos já
processados. Nunca modifica mídias ou banco. Não é persistida entre execuções.
"""
from __future__ import annotations

from collections import defaultdict
from contextlib import closing
from pathlib import Path
import sqlite3
from typing import Any, Callable

from .catalog import DEFAULT_DB
from .duplicates import (
    MAX_FILE_BYTES, MAX_TOTAL_HASH_BYTES, _candidate_path,
    _is_symlink_component, _sha256_checked,
)
from .inventory import CATEGORIES

MAX_SESSION_CANDIDATES = 100_000
MAX_BATCH_FILES = 200


def _validate_positive(value: int, maximum: int, label: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= maximum:
        raise ValueError(f"{label} deve estar entre 1 e {maximum}.")


def _where(category: str | None) -> str:
    return "scan_id=? AND category=?" if category is not None else "scan_id=?"


class ProgressiveDuplicateSession:
    """Sessão read-only para um snapshot: hash em lotes, grupos entre lotes.

    Mantém apenas hashes/caminhos e contadores em RAM. Nenhum cache é gravado;
    retomar após encerrar o processo não está disponível nesta primeira versão.
    """

    def __init__(
        self,
        db_path: Path = DEFAULT_DB,
        category: str | None = None,
        scan_id: int | None = None,
    ) -> None:
        if category is not None and category not in CATEGORIES:
            raise ValueError("Categoria inválida.")
        if scan_id is not None:
            _validate_positive(scan_id, 2**63 - 1, "ID do snapshot")
        self.db_path = Path(db_path).expanduser().absolute()
        if not self.db_path.is_file():
            raise ValueError("Catálogo SQLite não encontrado.")
        self.category = category
        try:
            with closing(sqlite3.connect(self.db_path.as_uri() + "?mode=ro", uri=True)) as conn:
                conn.row_factory = sqlite3.Row
                scan = conn.execute(
                    "SELECT id, root FROM scans WHERE id=?"
                    if scan_id is not None else
                    "SELECT id, root FROM scans ORDER BY id DESC LIMIT 1",
                    (scan_id,) if scan_id is not None else (),
                ).fetchone()
                if scan is None:
                    raise ValueError("Snapshot não encontrado.")
                self.scan_id = scan["id"]
                self.root = Path(scan["root"]).absolute()
                if _is_symlink_component(self.root) or not self.root.is_dir():
                    raise ValueError("Pasta de origem indisponível ou contém link.")
                args = (self.scan_id, category) if category is not None else (self.scan_id,)
                where = _where(category)
                self.total_files = conn.execute(
                    f"SELECT COUNT(*) FROM media WHERE {where}", args
                ).fetchone()[0]
                counts = conn.execute(
                    f"""SELECT size_bytes, COUNT(*) AS n FROM media
                        WHERE {where} GROUP BY size_bytes HAVING COUNT(*) > 1""",
                    args,
                )
                self.total_candidates = sum(row["n"] for row in counts)
        except sqlite3.Error as exc:
            raise ValueError(f"Falha ao consultar catálogo: {exc}") from exc
        if self.total_candidates > MAX_SESSION_CANDIDATES:
            raise ValueError(
                f"Snapshot contém mais de {MAX_SESSION_CANDIDATES} candidatos; "
                "sessão progressiva recusada para limitar memória."
            )
        self._last_media_id = 0
        self._processed = 0
        self._hashed = 0
        self._bytes_read = 0
        self._skipped: list[dict[str, str]] = []
        self._digests: dict[tuple[int, str], list[str]] = defaultdict(list)
        self._done = self.total_candidates == 0

    @property
    def done(self) -> bool:
        return self._done

    def next_batch(
        self,
        batch_size: int = 100,
        max_file_bytes: int = MAX_FILE_BYTES,
        max_total_bytes: int = 64 * 1024 * 1024,
        progress: Callable[[dict[str, int | str]], None] | None = None,
    ) -> dict[str, Any]:
        """Avança uma página de candidatos; orçamentos de bytes são POR lote."""
        _validate_positive(batch_size, MAX_BATCH_FILES, "Arquivos por lote")
        _validate_positive(max_file_bytes, MAX_FILE_BYTES, "Limite por arquivo")
        _validate_positive(max_total_bytes, MAX_TOTAL_HASH_BYTES, "Orçamento por lote")
        if progress is not None and not callable(progress):
            raise ValueError("Callback de progresso inválido.")
        if self._done:
            return self.summary(batch_selected=0, batch_hashed=0, batch_bytes=0)

        args = (self.scan_id, self.category) if self.category is not None else (self.scan_id,)
        clause = _where(self.category)
        sql = f"""WITH repeated AS (
            SELECT size_bytes FROM media WHERE {clause}
            GROUP BY size_bytes HAVING COUNT(*) > 1
        )
        SELECT m.id, m.relative_path, m.size_bytes, m.modified_utc
        FROM media AS m JOIN repeated AS r ON r.size_bytes=m.size_bytes
        WHERE m.scan_id=? {"AND m.category=?" if self.category is not None else ""}
          AND m.id>? ORDER BY m.id LIMIT ?"""
        parameters = (*args, *args, self._last_media_id, batch_size)
        try:
            with closing(sqlite3.connect(self.db_path.as_uri() + "?mode=ro", uri=True)) as conn:
                conn.row_factory = sqlite3.Row
                scan = conn.execute(
                    "SELECT root FROM scans WHERE id=?", (self.scan_id,)
                ).fetchone()
                if scan is None or Path(scan["root"]).absolute() != self.root:
                    raise ValueError("Snapshot alterado: sessão inválida.")
                rows = conn.execute(sql, parameters).fetchall()
        except sqlite3.Error as exc:
            raise ValueError(f"Falha ao consultar lote: {exc}") from exc

        budget_reserved = 0
        batch_hashed = 0
        batch_bytes = 0
        for index, item in enumerate(rows, start=1):
            size, name = item["size_bytes"], item["relative_path"]
            if size > max_file_bytes:
                self._skipped.append({"file": name, "reason": "arquivo_acima_do_limite"})
            elif size > max_total_bytes - budget_reserved:
                self._skipped.append({"file": name, "reason": "limite_de_leitura_do_lote"})
            else:
                budget_reserved += size
                try:
                    candidate = _candidate_path(self.root, name)
                    digest = _sha256_checked(candidate, size, item["modified_utc"])
                except (ValueError, OSError) as exc:
                    self._skipped.append({
                        "file": name,
                        "reason": str(exc) if isinstance(exc, ValueError) else "erro_de_leitura",
                    })
                else:
                    self._digests[(size, digest)].append(name)
                    batch_hashed += 1
                    batch_bytes += size
            self._last_media_id = item["id"]
            self._processed += 1
            if progress is not None and (index % 20 == 0 or index == len(rows)):
                progress({
                    "phase": "hash",
                    "processed": self._processed,
                    "total": self.total_candidates,
                })
        self._hashed += batch_hashed
        self._bytes_read += batch_bytes
        self._done = len(rows) < batch_size or self._processed >= self.total_candidates
        return self.summary(
            batch_selected=len(rows), batch_hashed=batch_hashed,
            batch_bytes=batch_bytes,
        )

    def summary(
        self, batch_selected: int = 0, batch_hashed: int = 0,
        batch_bytes: int = 0,
    ) -> dict[str, Any]:
        groups = [
            {"size_bytes": size, "sha256": digest,
             "files": sorted(paths), "count": len(paths)}
            for (size, digest), paths in self._digests.items()
            if len(paths) >= 2
        ]
        groups.sort(key=lambda group: (group["files"][0].casefold(), group["sha256"]))
        return {
            "operation": "verify_duplicates_sha256_progressive",
            "mode": "read_only",
            "executable": False,
            "files_modified": False,
            "state_storage": "memory_only",
            "scan_id": self.scan_id,
            "root": str(self.root),
            "category": self.category,
            "total_matches": self.total_files,
            "candidate_files_total": self.total_candidates,
            "selected": self._processed,
            "hashed_files": self._hashed,
            "bytes_read": self._bytes_read,
            "remaining_candidates": self.total_candidates - self._processed,
            "batch_selected": batch_selected,
            "batch_hashed": batch_hashed,
            "batch_bytes": batch_bytes,
            "skipped": list(self._skipped),
            "groups": groups,
            "confirmed_groups": len(groups),
            "confirmed_files": sum(group["count"] for group in groups),
            "done": self._done,
            "complete": self._done and not self._skipped,
            "scope_note": (
                "Resultados acumulados apenas nesta sessão e neste snapshot. "
                "Hashes representam o momento da leitura, não garantem integridade futura."
            ),
        }
