"""Catálogo SQLite local: armazena snapshots de inventário, nunca altera mídias."""

from __future__ import annotations

from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Any

from .inventory import CATEGORIES

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
    if category is not None and category not in CATEGORIES:
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


def catalog_summary(db_path: Path = DEFAULT_DB) -> dict[str, Any]:
    """Resumo agregado do último snapshot, sem carregar registros individuais."""
    path = Path(db_path).expanduser().absolute()
    if not path.is_file():
        raise ValueError(f"Catálogo não encontrado: {path}")

    try:
        with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as conn:
            scan = conn.execute(
                """SELECT id, root, scanned_utc, media_files, other_files,
                          symlinks_skipped, bytes_media
                   FROM scans ORDER BY id DESC LIMIT 1"""
            ).fetchone()
            if scan is None:
                return {"database": str(path), "scan_id": None, "media_files": 0,
                        "bytes_media": 0, "indexed_files": 0, "bytes_indexed": 0,
                        "by_category": {category: 0 for category in CATEGORIES}}
            totals = conn.execute(
                "SELECT COUNT(*), COALESCE(SUM(size_bytes), 0) FROM media WHERE scan_id=?",
                (scan[0],),
            ).fetchone()
            counts = {category: 0 for category in CATEGORIES}
            for category, amount in conn.execute(
                "SELECT category, COUNT(*) FROM media WHERE scan_id=? GROUP BY category",
                (scan[0],),
            ):
                counts[category] = amount
            return {
                "database": str(path), "scan_id": scan[0], "root": scan[1],
                "scanned_utc": scan[2], "media_files": scan[3],
                "other_files": scan[4], "symlinks_skipped": scan[5],
                "bytes_media": scan[6], "indexed_files": totals[0],
                "bytes_indexed": totals[1], "by_category": counts,
            }
    except sqlite3.Error as exc:
        raise ValueError(f"Não foi possível consultar o catálogo: {exc}") from exc


def query_catalog_page(
    db_path: Path = DEFAULT_DB,
    category: str | None = None,
    page: int = 1,
    page_size: int = 50,
    scan_id: int | None = None,
    name_contains: str | None = None,
    extension: str | None = None,
    search_scope: str = "path",
    date_from: str | None = None,
    date_to: str | None = None,
    sort_by: str = "name",
) -> dict[str, Any]:
    """Lista página limitada, opcionalmente filtrada, em SQLite somente leitura.

    Diferente de query_catalog(), não carrega todos os arquivos na memória.
    """
    if category is not None and category not in CATEGORIES:
        raise ValueError("Categoria inválida: use imagem, video ou audio.")
    if search_scope not in ("path", "filename"):
        raise ValueError("Escopo inválido: use path ou filename.")
    if sort_by not in ("name", "newest", "oldest"):
        raise ValueError("Ordenação inválida.")
    def validate_date(value: str | None, label: str) -> str | None:
        if value is None or value == "":
            return None
        if not isinstance(value, str):
            raise ValueError(f"{label} deve estar em AAAA-MM-DD.")
        try:
            parsed = datetime.strptime(value, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError(f"{label} deve ser uma data válida em AAAA-MM-DD.") from exc
        if parsed.strftime("%Y-%m-%d") != value:
            raise ValueError(f"{label} deve estar em AAAA-MM-DD.")
        return value
    date_from = validate_date(date_from, "Data inicial")
    date_to = validate_date(date_to, "Data final")
    if date_from is not None and date_to is not None and date_from > date_to:
        raise ValueError("Data inicial não pode ser posterior à data final.")
    if scan_id is not None and (not isinstance(scan_id, int) or isinstance(scan_id, bool) or scan_id < 1):
        raise ValueError("ID de snapshot inválido.")
    if name_contains is not None and (not isinstance(name_contains, str) or len(name_contains) > 200):
        raise ValueError("Busca por nome deve ter até 200 caracteres.")
    if extension is not None and (not isinstance(extension, str) or len(extension) > 30):
        raise ValueError("Extensão deve ter até 30 caracteres.")
    # % e _ são literais: não são curingas quando digitados pelo usuário.
    def escape_like(value: str) -> str:
        return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

    normalized_name = (name_contains or "").strip()
    normalized_extension = (extension or "").strip().lower()
    if normalized_extension and not normalized_extension.startswith("."):
        normalized_extension = "." + normalized_extension
    if not isinstance(page, int) or isinstance(page, bool) or page < 1:
        raise ValueError("Página deve ser um inteiro positivo.")
    if (not isinstance(page_size, int) or isinstance(page_size, bool)
            or not 1 <= page_size <= 100):
        raise ValueError("Tamanho de página deve estar entre 1 e 100.")

    path = Path(db_path).expanduser().absolute()
    if not path.is_file():
        raise ValueError(f"Catálogo não encontrado: {path}")
    try:
        with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as conn:
            conn.row_factory = sqlite3.Row
            # A função extrai somente o nome-base; caminhos são relativos ao snapshot.
            conn.create_function(
                "archivia_filename", 1,
                lambda value: value.replace(chr(92), "/").rsplit("/", 1)[-1],
            )
            if scan_id is None:
                scan = conn.execute(
                    "SELECT id, root, scanned_utc FROM scans ORDER BY id DESC LIMIT 1"
                ).fetchone()
            else:
                scan = conn.execute(
                    "SELECT id, root, scanned_utc FROM scans WHERE id=?", (scan_id,)
                ).fetchone()
                if scan is None:
                    raise ValueError(f"Snapshot não encontrado: #{scan_id}")
            if scan is None:
                return {
                    "database": str(path), "scan_id": None, "root": None,
                    "scanned_utc": None, "filter_category": category,
                    "filter_name": normalized_name, "filter_extension": normalized_extension,
                    "search_scope": search_scope, "date_from": date_from,
                    "date_to": date_to, "sort_by": sort_by,
                    "page": page, "page_size": page_size, "count": 0,
                    "pages": 0, "files": [],
                }

            where = "scan_id=?"
            params: tuple[Any, ...] = (scan["id"],)
            if category is not None:
                where += " AND category=?"
                params += (category,)
            if normalized_name:
                column = "archivia_filename(relative_path)" if search_scope == "filename" else "relative_path"
                where += f" AND {column} LIKE ? ESCAPE '\\'"
                params += ("%" + escape_like(normalized_name) + "%",)
            if normalized_extension:
                where += " AND extension = ?"
                params += (normalized_extension,)
            if date_from is not None:
                where += " AND substr(modified_utc, 1, 10) >= ?"
                params += (date_from,)
            if date_to is not None:
                where += " AND substr(modified_utc, 1, 10) <= ?"
                params += (date_to,)
            order = {
                "name": "relative_path COLLATE NOCASE, relative_path",
                "newest": "modified_utc DESC, relative_path COLLATE NOCASE, relative_path",
                "oldest": "modified_utc ASC, relative_path COLLATE NOCASE, relative_path",
            }[sort_by]
            count = conn.execute(
                f"SELECT COUNT(*) FROM media WHERE {where}", params
            ).fetchone()[0]
            rows = conn.execute(
                f"""SELECT relative_path, category, extension, size_bytes, modified_utc
                    FROM media WHERE {where}
                    ORDER BY {order}
                    LIMIT ? OFFSET ?""",
                (*params, page_size, (page - 1) * page_size),
            ).fetchall()
            return {
                "database": str(path), "scan_id": scan["id"], "root": scan["root"],
                "scanned_utc": scan["scanned_utc"], "filter_category": category,
                "filter_name": normalized_name, "filter_extension": normalized_extension,
                "search_scope": search_scope, "date_from": date_from,
                "date_to": date_to, "sort_by": sort_by,
                "page": page, "page_size": page_size, "count": count,
                "pages": (count + page_size - 1) // page_size,
                "files": [dict(row) for row in rows],
            }
    except sqlite3.Error as exc:
        raise ValueError(f"Não foi possível consultar o catálogo: {exc}") from exc


def list_catalog_scans(db_path: Path = DEFAULT_DB, limit: int = 100) -> list[dict[str, Any]]:
    """Histórico dos inventários gravados, sem ler a árvore de arquivos.

    O histórico é retornado em ordem decrescente. A lista nunca apaga snapshots.
    """
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 1000:
        raise ValueError("Limite do histórico deve estar entre 1 e 1000.")
    path = Path(db_path).expanduser().absolute()
    if not path.is_file():
        raise ValueError(f"Catálogo não encontrado: {path}")
    try:
        with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """SELECT s.id, s.root, s.scanned_utc, s.media_files,
                          s.other_files, s.bytes_media,
                          (SELECT COUNT(*) FROM media m WHERE m.scan_id=s.id) AS indexed_files
                   FROM scans s ORDER BY s.id DESC LIMIT ?""", (limit,)
            ).fetchall()
            return [dict(row) for row in rows]
    except sqlite3.Error as exc:
        raise ValueError(f"Não foi possível consultar o histórico: {exc}") from exc


def catalog_origins_summary(db_path: Path = DEFAULT_DB) -> dict[str, Any]:
    """Resume somente o snapshot mais recente de cada origem (root).

    Não soma históricos repetidos da mesma pasta; não altera o SQLite.
    Uma pasta contida em outra pode representar arquivos sobrepostos.
    """
    path = Path(db_path).expanduser().absolute()
    if not path.is_file():
        raise ValueError(f"Catálogo não encontrado: {path}")
    try:
        with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """WITH recent AS (
                       SELECT MAX(id) AS scan_id FROM scans GROUP BY root
                   )
                   SELECT s.id AS scan_id, s.root, s.scanned_utc,
                          s.media_files, s.bytes_media,
                          COUNT(m.id) AS indexed_files,
                          COALESCE(SUM(m.size_bytes), 0) AS bytes_indexed
                   FROM recent r
                   JOIN scans s ON s.id = r.scan_id
                   LEFT JOIN media m ON m.scan_id = s.id
                   GROUP BY s.id, s.root, s.scanned_utc,
                            s.media_files, s.bytes_media
                   ORDER BY s.root COLLATE NOCASE, s.root"""
            ).fetchall()
            origins = [dict(row) for row in rows]
            # Agrega as categorias dos mesmos scans de maneira independente.
            category_counts = {category: 0 for category in CATEGORIES}
            for category, count in conn.execute(
                """WITH recent AS (
                       SELECT MAX(id) AS scan_id FROM scans GROUP BY root
                   )
                   SELECT m.category, COUNT(*)
                   FROM media m JOIN recent r ON r.scan_id = m.scan_id
                   GROUP BY m.category"""
            ):
                category_counts[category] = count
            return {
                "database": str(path),
                "origins_count": len(origins),
                "indexed_files": sum(row["indexed_files"] for row in origins),
                "bytes_indexed": sum(row["bytes_indexed"] for row in origins),
                "media_files": sum(row["media_files"] for row in origins),
                "by_category": category_counts,
                "origins": origins,
                "overlap_warning": (
                    "Origens sobrepostas podem conter os mesmos arquivos; "
                    "o total não elimina duplicações entre pastas."
                ),
            }
    except sqlite3.Error as exc:
        raise ValueError(f"Não foi possível consultar as origens: {exc}") from exc
