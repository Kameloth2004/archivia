"""Piloto manual de movimentação — fase de PREPARAÇÃO, sem excluir origem.

Somente uma imagem selecionada explicitamente, em duas subpastas do mesmo
diretório de teste. Não utiliza o Ollama, catálogo ou executor de fixtures.
A confirmação da remoção da origem NÃO está implementada neste módulo.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
import uuid

_IMAGE_TYPES = frozenset({".jpg", ".jpeg", ".png", ".webp", ".avif", ".gif", ".bmp", ".tif", ".tiff"})
_MAX_SIZE = 50 * 1024 * 1024
_CHUNK = 1024 * 1024
_APPROVAL = "PREPARAR COPIA VERIFICADA"


def _check_plain(path: Path) -> Path:
    path = path.expanduser().absolute()
    for component in (path, *path.parents):
        if component.is_symlink() or (
            hasattr(os.path, "isjunction") and os.path.isjunction(component)
        ):
            raise ValueError("Links simbólicos e junctions não são aceitos no piloto.")
    return path


def _file_identity(info: os.stat_result) -> tuple[int, int, int, int]:
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)


def _read_hash(path: Path) -> tuple[str, os.stat_result]:
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags)
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError("A origem deve ser arquivo regular.")
        result = hashlib.sha256()
        with os.fdopen(os.dup(fd), "rb") as inp:
            while chunk := inp.read(_CHUNK):
                result.update(chunk)
        after = os.fstat(fd)
        at_path = path.stat(follow_symlinks=False)
        if _file_identity(before) != _file_identity(after) or _file_identity(after) != _file_identity(at_path):
            raise ValueError("Arquivo foi alterado durante a verificação.")
        return result.hexdigest(), before
    finally:
        os.close(fd)


@dataclass(frozen=True)
class ManualCopyPreview:
    root: Path
    source: Path
    destination: Path
    size_bytes: int
    modified_ns: int
    device: int
    inode: int


def preview_manual_copy(root: str | Path, source: str | Path, destination_dir: str | Path) -> ManualCopyPreview:
    """Exige raiz com subpastas 'origem' e 'destino', sem criar diretórios."""
    base = _check_plain(Path(root))
    src = _check_plain(Path(source))
    dest_dir = _check_plain(Path(destination_dir))
    if not base.is_dir() or not (base / "origem").is_dir() or not (base / "destino").is_dir():
        raise ValueError("Crie duas subpastas na pasta de teste: origem e destino.")
    if src.parent != _check_plain(base / "origem") or dest_dir != _check_plain(base / "destino"):
        raise ValueError("Selecione uma imagem em origem e a pasta destino dentro da mesma raiz de testes.")
    if src.suffix.casefold() not in _IMAGE_TYPES or not src.is_file():
        raise ValueError("O piloto aceita somente uma imagem existente.")
    if not dest_dir.is_dir():
        raise ValueError("A pasta de destino não existe.")
    info = src.stat(follow_symlinks=False)
    if not stat.S_ISREG(info.st_mode) or info.st_size > _MAX_SIZE:
        raise ValueError("Imagem inválida ou maior que 50 MiB.")
    target = _check_plain(dest_dir / src.name)
    if target.exists() or target.is_symlink() or any(
        item.name.casefold() == src.name.casefold() for item in dest_dir.iterdir()
    ):
        raise ValueError("Destino ocupado: nenhuma sobrescrita é permitida.")
    return ManualCopyPreview(base, src, target, info.st_size, info.st_mtime_ns, info.st_dev, info.st_ino)


def _journal(path: Path, event: str, source: Path, target: Path, **extra: object) -> None:
    with path.open("a", encoding="utf-8") as out:
        data = {
            "utc": datetime.now(timezone.utc).isoformat(), "event": event,
            "source": str(source), "destination": str(target), **extra,
        }
        out.write(json.dumps(data, ensure_ascii=False) + "\n")
        out.flush()
        os.fsync(out.fileno())


def prepare_manual_copy(preview: ManualCopyPreview, *, approval: str) -> dict[str, object]:
    """Publica uma cópia verificada; a imagem de origem jamais é apagada."""
    if approval != _APPROVAL:
        raise ValueError("Confirmação explícita ausente.")
    if not isinstance(preview, ManualCopyPreview):
        raise ValueError("Prévia inválida.")
    fresh = preview_manual_copy(preview.root, preview.source, preview.destination.parent)
    if fresh != preview:
        raise ValueError("Prévia desatualizada: refaça a análise.")
    lock = _check_plain(preview.root / ".archivia-manual.lock")
    try:
        lock.mkdir()
    except FileExistsError as exc:
        raise ValueError("Há uma operação ou lock pendente na pasta de testes.") from exc
    tmp = None
    tmp_identity = None
    published = False
    try:
        fresh = preview_manual_copy(preview.root, preview.source, preview.destination.parent)
        if fresh != preview:
            raise ValueError("Origem ou destino mudou após autorização.")
        journal = _check_plain(preview.root / ("archivia-manual-" + uuid.uuid4().hex + ".jsonl"))
        # Criado exclusivamente: não reutilizar journals de sessões anteriores.
        with journal.open("x", encoding="utf-8"):
            pass
        _journal(journal, "PREPARADO", preview.source, preview.destination)
        try:
            original_hash, original_info = _read_hash(preview.source)
            descriptor, filename = tempfile.mkstemp(
                dir=preview.destination.parent, prefix=".archivia-manual-", suffix=".tmp",
            )
            tmp = _check_plain(Path(filename))
            tmp_stat = os.fstat(descriptor)
            tmp_identity = (tmp_stat.st_dev, tmp_stat.st_ino)
            _journal(journal, "TEMPORARIO", preview.source, preview.destination)
            try:
                flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
                if hasattr(os, "O_NOFOLLOW"):
                    flags |= os.O_NOFOLLOW
                fd = os.open(preview.source, flags)
                try:
                    if _file_identity(os.fstat(fd)) != _file_identity(original_info):
                        raise ValueError("Origem alterada antes de copiar.")
                    with os.fdopen(os.dup(fd), "rb") as input_file:
                        with os.fdopen(descriptor, "wb") as output_file:
                            descriptor = -1
                            while block := input_file.read(_CHUNK):
                                output_file.write(block)
                            output_file.flush()
                            os.fsync(output_file.fileno())
                finally:
                    os.close(fd)
            finally:
                if descriptor != -1:
                    os.close(descriptor)
            copied_hash, copied_info = _read_hash(tmp)
            verified_hash, verified_info = _read_hash(preview.source)
            if (copied_hash != original_hash or verified_hash != original_hash
                    or _file_identity(verified_info) != _file_identity(original_info)
                    or copied_info.st_size != original_info.st_size):
                raise ValueError("Falha de integridade SHA-256. Origem preservada.")
            # Criação exclusiva no mesmo volume do temporário, sem substituir destino.
            fresh = preview_manual_copy(preview.root, preview.source, preview.destination.parent)
            if fresh != preview:
                raise ValueError("Origem ou destino mudou antes da publicação.")
            _journal(journal, "SHA256_CONFERIDO", preview.source, preview.destination, sha256=copied_hash)
            os.link(tmp, preview.destination, follow_symlinks=False)
            published = True
            _journal(journal, "COPIA_PUBLICADA", preview.source, preview.destination, sha256=copied_hash)
            return {
                "status": "copia_preparada", "source": str(preview.source),
                "destination": str(preview.destination), "sha256": copied_hash,
                "bytes": original_info.st_size, "journal": str(journal),
                "source_preserved": True, "move_completed": False,
            }
        except Exception:
            _journal(journal, "INTERROMPIDO", preview.source, preview.destination, published=published)
            raise
    finally:
        if tmp is not None:
            try:
                info = tmp.stat(follow_symlinks=False)
                if stat.S_ISREG(info.st_mode) and (info.st_dev, info.st_ino) == tmp_identity:
                    tmp.unlink()
            except OSError:
                pass
        try:
            lock.rmdir()
        except OSError:
            pass
