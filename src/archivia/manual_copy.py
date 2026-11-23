"""Cópia manual conservadora para homologação local com imagens descartáveis.

NÃO move nem remove a origem. NÃO é uma ferramenta do Ollama.
Operação limitada a UMA imagem pequena escolhida pelo usuário; publica
sem sobrescrever e registra journal no diretório de destino.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
from typing import Any
from uuid import uuid4

from .executor import _safe_path

_ALLOWED = frozenset((".jpg", ".jpeg", ".png", ".webp", ".avif"))
_MAX_BYTES = 32 * 1024 * 1024
_CHUNK = 1024 * 1024


def _identity(st: os.stat_result) -> tuple[int, int, int, int]:
    return st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns


def _digest(path: Path) -> tuple[str, os.stat_result]:
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags)
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError("Arquivo não regular.")
        if before.st_size > _MAX_BYTES:
            raise ValueError("Imagem acima do limite experimental de 32 MiB.")
        h = hashlib.sha256()
        with os.fdopen(os.dup(fd), "rb") as handle:
            while block := handle.read(_CHUNK):
                h.update(block)
        after = os.fstat(fd)
        current = path.stat(follow_symlinks=False)
        if _identity(before) != _identity(after) or _identity(after) != _identity(current):
            raise ValueError("Imagem alterada durante a verificação.")
        return h.hexdigest(), before
    finally:
        os.close(fd)


def _record(path: Path, event: str, source: Path, target: Path, **details: Any) -> None:
    payload = {
        "utc": datetime.now(timezone.utc).isoformat(), "event": event,
        "source": str(source), "target": str(target), **details,
    }
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, ensure_ascii=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def preview_manual_image_copy(source_file: str | Path, destination_folder: str | Path) -> dict[str, Any]:
    """Prévia e verificação de caminhos; não altera arquivos nem pastas."""
    source = _safe_path(Path(source_file))
    folder = _safe_path(Path(destination_folder))
    if source.suffix.lower() not in _ALLOWED:
        raise ValueError("O teste manual permite apenas JPG, PNG, WebP ou AVIF.")
    if not source.is_file() or not folder.is_dir():
        raise ValueError("Origem e pasta de destino devem existir.")
    if source.parent == folder:
        raise ValueError("Escolha uma pasta de destino diferente da origem.")
    before = source.stat(follow_symlinks=False)
    if not stat.S_ISREG(before.st_mode) or before.st_size > _MAX_BYTES:
        raise ValueError("Origem inválida ou acima de 32 MiB.")
    target = _safe_path(folder / source.name)
    if target.exists() or target.is_symlink() or any(
        item.name.casefold() == target.name.casefold() for item in folder.iterdir()
    ):
        raise ValueError("Já existe arquivo com esse nome no destino; nenhuma sobrescrita.")
    return {
        "source": str(source), "destination": str(target),
        "bytes": before.st_size, "source_preserved": True,
        "operation": "copy_only", "executed": False,
    }


def copy_manual_image_verified(
    source_file: str | Path, destination_folder: str | Path, *,
    approved_source: str, approved_destination: str,
) -> dict[str, Any]:
    """Copia imagem selecionada explicitamente, validando hash SHA-256.

    A confirmação chega da GUI. Nem esta função nem a GUI removem a origem.
    """
    preview = preview_manual_image_copy(source_file, destination_folder)
    if preview["source"] != approved_source or preview["destination"] != approved_destination:
        raise ValueError("Caminhos diferentes dos explicitamente aprovados.")
    source = _safe_path(Path(preview["source"]))
    target = _safe_path(Path(preview["destination"]))
    folder = target.parent
    journal = _safe_path(folder / f".archivia-manual-{uuid4().hex}.jsonl")
    # Journal criado exclusivamente; não modificar um journal pré-existente.
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    journal_fd = os.open(journal, flags, 0o600)
    os.close(journal_fd)
    temp: Path | None = None
    temp_id: tuple[int, int] | None = None
    published = False
    try:
        _record(journal, "PREPARADO", source, target)
        first_hash, before = _digest(source)
        fd, temp_name = tempfile.mkstemp(prefix=".archivia-manual-", suffix=".tmp", dir=folder)
        temp = _safe_path(Path(temp_name))
        temp_info = os.fstat(fd)
        temp_id = (temp_info.st_dev, temp_info.st_ino)
        try:
            _record(journal, "TEMPORARIO_CRIADO", source, target, temporary=str(temp))
            src_flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
            if hasattr(os, "O_NOFOLLOW"):
                src_flags |= os.O_NOFOLLOW
            read_fd = os.open(source, src_flags)
            try:
                if _identity(os.fstat(read_fd)) != _identity(before):
                    raise ValueError("Origem alterada antes da cópia.")
                with os.fdopen(os.dup(read_fd), "rb") as input_file:
                    with os.fdopen(fd, "wb") as output_file:
                        fd = -1
                        while block := input_file.read(_CHUNK):
                            output_file.write(block)
                        output_file.flush()
                        os.fsync(output_file.fileno())
                if _identity(os.fstat(read_fd)) != _identity(before):
                    raise ValueError("Origem alterada durante a cópia.")
            finally:
                os.close(read_fd)
        finally:
            if fd != -1:
                os.close(fd)

        temp_hash, _ = _digest(temp)
        source_hash, now = _digest(source)
        if temp_hash != first_hash or source_hash != first_hash or _identity(now) != _identity(before):
            raise ValueError("Falha na verificação SHA-256; a origem foi preservada.")
        _record(journal, "HASH_VERIFICADO", source, target, sha256=first_hash)
        if target.exists() or target.is_symlink() or any(
            item != temp and item.name.casefold() == target.name.casefold()
            for item in folder.iterdir()
        ):
            raise ValueError("Destino ocupado; nenhuma sobrescrita.")
        # Hardlink apenas entre temporário e nome final no MESMO volume de destino.
        os.link(temp, target, follow_symlinks=False)
        published = True
        _record(journal, "PUBLICADO", source, target)
        final_hash, final_stat = _digest(target)
        if final_hash != first_hash or (final_stat.st_dev, final_stat.st_ino) != temp_id:
            raise ValueError("Verificação final da cópia falhou; revisar journal.")
        _record(journal, "VERIFICADO", source, target, sha256=first_hash)
        return {
            "status": "copia_verificada", "source": str(source),
            "destination": str(target), "sha256": first_hash,
            "bytes": before.st_size, "journal": str(journal),
            "source_preserved": True, "files_copied": 1,
        }
    except Exception:
        try:
            _record(journal, "INTERROMPIDO", source, target, published=published)
        except OSError:
            pass
        raise
    finally:
        if temp is not None:
            try:
                last = temp.stat(follow_symlinks=False)
                if stat.S_ISREG(last.st_mode) and (last.st_dev, last.st_ino) == temp_id:
                    temp.unlink()
            except OSError:
                pass
