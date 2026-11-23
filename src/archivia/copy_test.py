"""Cópia verificada TEST-ONLY. Preserva sempre a origem.

Não exportada para GUI, CLI ou Ollama. Não executa movimentação entre discos:
a operação simula o protocolo de cópia com staging e publicação segura usando
apenas arquivos sintéticos em tests/.runtime.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import stat
import uuid
from typing import Any

from .catalog import DEFAULT_DB
from .executor import (
    _CONFIRM, _exclusive_fixture_lock, _inside_runtime, _record, _safe_path,
)
from .planner import propose_moves

_CHUNK = 1024 * 1024


def _hash_descriptor(handle) -> str:
    digest = hashlib.sha256()
    handle.seek(0)
    while block := handle.read(_CHUNK):
        digest.update(block)
    return digest.hexdigest()


def copy_verified_fixture(
    plan: dict[str, Any],
    db_path: Path = DEFAULT_DB,
    *,
    approval: str,
) -> dict[str, Any]:
    """Copia um arquivo da fixture para destino sem sobrescrever nem excluir origem."""
    if approval != _CONFIRM:
        raise ValueError("Confirmação explícita de teste ausente.")
    if not isinstance(plan, dict) or plan.get("mode") != "simulation":
        raise ValueError("Plano não é simulação válida.")
    if (plan.get("executable") is not False or plan.get("summary_only") or
            plan.get("truncated") or plan.get("blocked") != 0 or
            plan.get("selected") != 1 or plan.get("total_matches") != 1 or
            plan.get("category") not in ("imagem", "video", "audio") or
            type(plan.get("scan_id")) is not int):
        raise ValueError("A cópia aceita somente plano completo de um arquivo.")
    actions = plan.get("actions")
    if not isinstance(actions, list) or len(actions) != 1:
        raise ValueError("Plano deve ter uma ação única.")
    action = actions[0]
    if not isinstance(action, dict) or action.get("status") != "proposto":
        raise ValueError("Ação inválida.")
    if not isinstance(action.get("source"), str) or not isinstance(action.get("destination"), str):
        raise ValueError("Caminhos inválidos.")
    source = _safe_path(Path(action["source"]))
    target = _safe_path(Path(action["destination"]))
    _, root = _inside_runtime(source)
    _, destination_root = _inside_runtime(target)
    if root != destination_root or source == target:
        raise ValueError("Origem/destino fora do mesmo caso TEST-ONLY.")
    with _exclusive_fixture_lock(root):
        return _copy_locked(plan, Path(db_path), source, target, root)


def _copy_locked(
    plan: dict[str, Any], db_path: Path, source: Path, target: Path, root: Path,
) -> dict[str, Any]:
    if not source.is_file() or not target.parent.is_dir():
        raise ValueError("Origem ou diretório de destino indisponível.")
    if target.exists() or target.is_symlink() or any(
        p.name.casefold() == target.name.casefold() for p in target.parent.iterdir()
    ):
        raise ValueError("Destino já existe; cópia bloqueada.")
    fresh = propose_moves(
        target.parent, plan["category"], db_path=db_path,
        scan_id=plan["scan_id"], limit=1,
    )
    if (fresh["root"] != plan.get("root") or
            fresh["destination"] != plan.get("destination") or
            fresh["total_matches"] != 1 or fresh["blocked"] or
            fresh["truncated"] or fresh["actions"] != plan["actions"]):
        raise ValueError("Plano divergente do catálogo ou do disco.")

    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    original_fd = os.open(source, flags)
    temporary = target.parent / (".archivia-copy-" + uuid.uuid4().hex + ".tmp")
    journal = root / "archivia-copy-journal.jsonl"
    published = False
    temp_identity = None
    temp_created = False
    try:
        with os.fdopen(original_fd, "rb") as original:
            initial = os.fstat(original.fileno())
            if not stat.S_ISREG(initial.st_mode):
                raise ValueError("Origem não é arquivo regular.")
            if source.stat(follow_symlinks=False).st_ino != initial.st_ino:
                raise ValueError("Origem alterada antes da leitura.")
            _record(journal, "COPIA_PREPARADA", source, target)
            create_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
            out_fd = os.open(temporary, create_flags, 0o600)
            temp_created = True
            temp_identity = os.fstat(out_fd)
            source_hash = hashlib.sha256()
            with os.fdopen(out_fd, "wb") as output:
                while chunk := original.read(_CHUNK):
                    source_hash.update(chunk)
                    output.write(chunk)
                output.flush()
                os.fsync(output.fileno())
            after = os.fstat(original.fileno())
            if ((after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) !=
                    (initial.st_dev, initial.st_ino, initial.st_size, initial.st_mtime_ns)):
                raise ValueError("Origem mudou durante a cópia.")
            if _hash_descriptor(original) != source_hash.hexdigest():
                raise ValueError("Origem mudou após a cópia.")
            with temporary.open("rb") as staged:
                if (_hash_descriptor(staged) != source_hash.hexdigest() or
                        staged.seek(0, os.SEEK_END) != initial.st_size):
                    raise ValueError("Hash ou tamanho da cópia não confere.")
            current = source.stat(follow_symlinks=False)
            if ((current.st_dev, current.st_ino, current.st_size, current.st_mtime_ns) !=
                    (initial.st_dev, initial.st_ino, initial.st_size, initial.st_mtime_ns)):
                raise ValueError("Caminho de origem alterado.")
            _record(journal, "COPIA_VERIFICADA", source, target)
            # Hardlink do arquivo temporário: criação exclusiva do nome final.
            # Diferente de os.replace, jamais substitui destino existente.
            os.link(temporary, target, follow_symlinks=False)
            published = True
            _record(journal, "COPIA_PUBLICADA", source, target)
            return {
                "status": "copiado_verificado",
                "source": str(source),
                "destination": str(target),
                "sha256": source_hash.hexdigest(),
                "source_preserved": True,
                "test_only": True,
                "journal": str(journal),
            }
    except BaseException:
        # Não alterar o destino publicado em caso de falha de journal.
        # Não remover origem em nenhuma circunstância.
        try:
            _record(journal, "COPIA_INTERROMPIDA", source, target)
        except OSError:
            pass
        raise
    finally:
        if temp_created:
            try:
                status = temporary.stat(follow_symlinks=False)
                if (temp_identity is not None and
                        (status.st_dev, status.st_ino) ==
                        (temp_identity.st_dev, temp_identity.st_ino)):
                    temporary.unlink()
            except FileNotFoundError:
                pass
            except OSError:
                pass
