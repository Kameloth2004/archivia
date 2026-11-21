"""Catálogo SQLite local: armazena snapshots de inventário, nunca altera mídias."""

from __future__ import annotations

from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Any

# src/archivia/catalog.py -> raiz do projeto (D:/PROJETOS/archivia no Windows).
DEFAULT_DB = Path(__file__).resolve().parents[2] / "data" / "catalogo.sqlite3"

SCHEMA = """
CREATE TABLE IF NOT EXISTS scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    root TEXT NOT NULL,
    scanned_utc TEXT NOT NULL,
    media_files INTEGER NOT NULL,
    other_files INTEGER NOT NULL,
    symlinks_skipped INTEGER NOT NULL,
    bytes_media INTEGER NOT NULL,
    error_count INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS media (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id INTEGER NOT NULL REFERENCES scans(id),
    relative_path TEXT NOT NULL,
    category TEXT NOT NULL,
    extension TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    modified_utc TEXT NOT NULL,
    UNIQUE(scan_id, relative_path)
);
CREATE INDEX IF NOT EXISTS idx_media_scan ON media(scan_id);
"""


def store_inventory(result: dict[str, Any], db_path: Path = DEFAULT_DB) -> dict[str, Any]:
    """Grava um novo snapshot somente se o inventário não registrou erros.

    A única escrita é no banco local escolhido; nenhum arquivo da origem é alterado.
    """
    if result["errors"]:
        raise ValueError("Inventário com erros: catálogo não gravado para evitar snapshot incompleto.")

    db_path = Path(db_path).expanduser().absolute()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute("PRAGMA foreign_keys=ON")
        conn.executescript(SCHEMA)
        with conn:
            cursor = conn.execute(
                """INSERT INTO scans
                (root, scanned_utc, media_files, other_files, symlinks_skipped,
                 bytes_media, error_count) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    result["root"], timestamp, result["summary"]["media_files"],
                    result["summary"]["other_files"],
                    result["summary"]["symlinks_skipped"],
                    result["summary"]["bytes_media"], 0,
                ),
            )
            scan_id = cursor.lastrowid
            conn.executemany(
                """INSERT INTO media
                   (scan_id, relative_path, category, extension, size_bytes, modified_utc)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                [
                    (scan_id, item["path"], item["category"], item["extension"],
                     item["size_bytes"], item["modified_utc"])
                    for item in result["files"]
                ],
            )
    return {
        "database": str(db_path),
        "scan_id": scan_id,
        "root": result["root"],
        "media_files": result["summary"]["media_files"],
        "bytes_media": result["summary"]["bytes_media"],
        "scanned_utc": timestamp,
    }


def query_catalog(
    db_path: Path = DEFAULT_DB, category: str | None = None
) -> dict[str, Any]:
    """Consulta somente o último inventário. Abre o SQLite em modo somente leitura."""
    if category is not None and category not in ("imagem", "video", "audio"):
        raise ValueError("Categoria inválida: use imagem, video ou audio.")

    path = Path(db_path).expanduser().absolute()
    if not path.is_file():
        raise ValueError(f"Catálogo não encontrado: {path}")

    # URI file: com mode=ro impede criação ou alteração do banco pela consulta.
    uri = path.as_uri() + "?mode=ro"
    try:
        with closing(sqlite3.connect(uri, uri=True)) as conn:
            conn.row_factory = sqlite3.Row
            scan = conn.execute(
                "SELECT id, root, scanned_utc FROM scans ORDER BY id DESC LIMIT 1"
            ).fetchone()
            if scan is None:
                return {"database": str(path), "scan_id": None, "files": [], "count": 0}
            if category is None:
                rows = conn.execute(
                    """SELECT relative_path, category, extension, size_bytes, modified_utc
                       FROM media WHERE scan_id=? ORDER BY relative_path""",
                    (scan["id"],),
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT relative_path, category, extension, size_bytes, modified_utc
                       FROM media WHERE scan_id=? AND category=? ORDER BY relative_path""",
                    (scan["id"], category),
                ).fetchall()
            items = [dict(row) for row in rows]
            return {
                "database": str(path),
                "scan_id": scan["id"],
                "root": scan["root"],
                "scanned_utc": scan["scanned_utc"],
                "filter_category": category,
                "count": len(items),
                "files": items,
            }
    except sqlite3.Error as exc:
        raise ValueError(f"Não foi possível consultar o catálogo: {exc}") from exc
