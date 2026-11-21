"""Inventário universal por extensão, sem abrir conteúdo nem alterar arquivos."""

from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Any

EXTENSIONS = {
    "imagem": {".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif", ".bmp", ".tif", ".tiff", ".heic", ".heif", ".svg", ".raw", ".dng", ".cr2", ".nef", ".arw"},
    "video": {".mp4", ".m4v", ".mov", ".avi", ".mkv", ".webm", ".wmv", ".flv", ".mpeg", ".mpg", ".3gp"},
    "audio": {".mp3", ".wav", ".flac", ".aac", ".ogg", ".opus", ".m4a", ".wma", ".aiff"},
    "documento": {".pdf", ".txt", ".doc", ".docx", ".odt", ".rtf", ".md", ".epub"},
    "planilha": {".xls", ".xlsx", ".xlsm", ".ods", ".csv", ".tsv"},
    "apresentacao": {".ppt", ".pptx", ".odp", ".pps", ".ppsx"},
    "compactado": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".tgz"},
    "codigo": {".py", ".php", ".js", ".ts", ".html", ".htm", ".css",
               ".json", ".xml", ".yaml", ".yml", ".sql", ".sh", ".ps1",
               ".java", ".c", ".h", ".cpp", ".cs", ".go", ".rs", ".rb"},
}
MEDIA_CATEGORIES = frozenset(("imagem", "video", "audio"))
CATEGORIES = (*EXTENSIONS.keys(), "outro")
CATEGORY_BY_EXTENSION = {
    extension: category
    for category, extensions in EXTENSIONS.items()
    for extension in extensions
}


def inventory(root: str | Path) -> dict[str, Any]:
    """Lê metadados dos arquivos, sem abrir conteúdo, ZIPs ou seguir symlinks.

    Erros durante a caminhada são registrados e a varredura continua.
    """

    base = Path(root).expanduser().absolute()
    if not base.is_dir() or base.is_symlink():
        raise ValueError("A origem deve ser um diretório real e acessível (não um link simbólico).")

    files: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    summary: dict[str, Any] = {
        "media_files": 0,
        "other_files": 0,
        "indexed_files": 0,
        "bytes_indexed": 0,
        "symlinks_skipped": 0,
        "bytes_media": 0,
        "by_category": {category: 0 for category in CATEGORIES},
    }
    pending = [base]

    while pending:
        folder = pending.pop()
        try:
            with os.scandir(folder) as iterator:
                entries = sorted(iterator, key=lambda entry: entry.name.casefold())
        except OSError as exc:
            errors.append({"path": str(folder), "error": str(exc)})
            continue

        dirs: list[Path] = []
        for entry in entries:
            path = Path(entry.path)
            try:
                if entry.is_symlink():
                    summary["symlinks_skipped"] += 1
                    continue
                if entry.is_dir(follow_symlinks=False):
                    dirs.append(path)
                    continue
                if not entry.is_file(follow_symlinks=False):
                    continue
                ext = path.suffix.lower()
                category = CATEGORY_BY_EXTENSION.get(ext, "outro")
                stat = entry.stat(follow_symlinks=False)
                files.append({
                    "path": path.relative_to(base).as_posix(),
                    "category": category,
                    "extension": ext,
                    "size_bytes": stat.st_size,
                    "modified_utc": datetime.fromtimestamp(
                        stat.st_mtime, tz=timezone.utc
                    ).isoformat(),
                })
                summary["indexed_files"] += 1
                summary["bytes_indexed"] += stat.st_size
                if category in MEDIA_CATEGORIES:
                    summary["media_files"] += 1
                    summary["bytes_media"] += stat.st_size
                else:
                    summary["other_files"] += 1
                summary["by_category"][category] += 1
            except OSError as exc:
                errors.append({"path": str(path), "error": str(exc)})
        pending.extend(reversed(dirs))

    files.sort(key=lambda item: item["path"].casefold())
    return {"root": str(base), "files": files, "summary": summary, "errors": errors}
