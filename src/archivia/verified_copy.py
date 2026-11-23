"""Cópia verificada EXPERIMENTAL (TEST-ONLY), sem remover origem.

Não é ferramenta Ollama, comando CLI nem recurso da GUI. O único escopo
permitido é um caso descartável em tests/.runtime; não usar com mídias reais.
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

from .catalog import DEFAULT_DB
from .executor import _CONFIRM, _exclusive_fixture_lock, _inside_runtime, _safe_path
from .planner import propose_moves

_BUFFER = 1024 * 1024


def _journal(journal: Path, event: str, source: Path, target: Path) -> None:
    """Registro JSONL exclusivo da cópia; nunca misturar com journal de move."""
    row = {
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "source": str(source),
        "destination": str(target),
    }
    with journal.open("a", encoding="utf-8") as out:
        out.write(json.dumps(row, ensure_ascii=False) + "\n")
        out.flush()
        os.fsync(out.fileno())


def _fingerprint(source: Path, target: Path) -> tuple[str, str, os.stat_result]:
    """Copia bytes para temporário aberto exclusivamente e verifica SHA-256."""
    src_flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    if hasattr(os, "O_NOFOLLOW"):
        src_flags |= os.O_NOFOLLOW
    fd = os.open(source, src_flags)
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError("Origem não é um arquivo regular.")
        source_hash = hashlib.sha256()
        with os.fdopen(os.dup(fd), "rb", closefd=True) as input_file:
            with target.open("wb") as out:
                while True:
                    chunk = input_file.read(_BUFFER)
                    if not chunk:
                        break
                    source_hash.update(chunk)
                    out.write(chunk)
                out.flush()
                os.fsync(out.fileno())
        after = os.fstat(fd)
        current = source.stat(follow_symlinks=False)
        identity = lambda st: (
            st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns,
        )
        if identity(before) != identity(after) or identity(before) != identity(current):
            raise ValueError("Origem alterada durante cópia: nenhuma publicação.")
        copied_hash = hashlib.sha256()
        with target.open("rb") as copied:
            while chunk := copied.read(_BUFFER):
                copied_hash.update(chunk)
        if source_hash.digest() != copied_hash.digest():
            raise ValueError("Hash SHA-256 divergente: nenhuma publicação.")
        if target.stat().st_size != before.st_size:
            raise ValueError("Tamanho da cópia divergente: nenhuma publicação.")
        return source_hash.hexdigest(), copied_hash.hexdigest(), before
    finally:
        os.close(fd)


def _validate_plan(plan: dict[str, Any], db_path: Path) -> tuple[Path, Path, Path]:
    if not isinstance(plan, dict) or plan.get("mode") != "simulation":
        raise ValueError("Plano de simulação inválido.")
    if plan.get("executable") is not False or plan.get("truncated") or plan.get("blocked") != 0:
        raise ValueError("Plano truncado, bloqueado ou executável não é permitido.")
    if plan.get("total_matches") != 1 or plan.get("selected") != 1:
        raise ValueError("A cópia experimental aceita um único arquivo.")
    if plan.get("category") not in ("imagem", "video", "audio"):
        raise ValueError("Categoria não autorizada.")
    if not isinstance(plan.get("scan_id"), int) or isinstance(plan["scan_id"], bool):
        raise ValueError("Snapshot inválido.")
    actions = plan.get("actions")
    if not isinstance(actions, list) or len(actions) != 1:
        raise ValueError("Plano sem ação única.")
    action = actions[0]
    if not isinstance(action, dict) or action.get("status") != "proposto":
        raise ValueError("Ação não proposta.")
    if not isinstance(action.get("source"), str) or not isinstance(action.get("destination"), str):
        raise ValueError("Caminhos inválidos.")
    source = _safe_path(Path(action["source"]))
    target = _safe_path(Path(action["destination"]))
    _, root = _inside_runtime(source)
    _, target_root = _inside_runtime(target)
    if root != target_root or source == target:
        raise ValueError("Apenas um caso isolado de tests/.runtime.")
    if not source.is_file() or not target.parent.is_dir():
        raise ValueError("Origem ou pasta de destino não existe.")
    if target.exists() or target.is_symlink() or any(
        entry.name.casefold() == target.name.casefold() for entry in target.parent.iterdir()
    ):
        raise ValueError("Destino já ocupado.")
    current = propose_moves(
        target.parent, plan["category"], db_path=db_path,
        scan_id=plan["scan_id"], limit=1,
    )
    if (
        current.get("root") != plan.get("root")
        or current.get("destination") != plan.get("destination")
        or current.get("total_matches") != 1
        or current.get("truncated")
        or current.get("blocked")
        or current.get("actions") != actions
    ):
        raise ValueError("Plano diverge do catálogo ou do estado atual.")
    return source, target, root


def copy_verified_test_file(
    plan: dict[str, Any],
    db_path: Path = DEFAULT_DB,
    *,
    approval: str,
) -> dict[str, Any]:
    """Copia uma fixture e preserva origem, inclusive em caso de falhas.

    Temporário é criado no volume de DESTINO; publicação com hardlink
    exclusivo impede substituir arquivo já existente. Sem exclusão de origem.
    """
    if approval != _CONFIRM:
        raise ValueError("Confirmação explícita de teste ausente.")
    if not isinstance(plan, dict) or not isinstance(plan.get("actions"), list) or len(plan["actions"]) != 1:
        raise ValueError("Plano de cópia inválido.")
    action = plan["actions"][0]
    if not isinstance(action, dict) or not isinstance(action.get("source"), str):
        raise ValueError("Origem inválida.")
    _, root = _inside_runtime(Path(action["source"]))
    with _exclusive_fixture_lock(root):
        source, target, root = _validate_plan(plan, db_path)
        journal = root / "archivia-copy-journal.jsonl"
        # Não continuar um journal já existente: evitar ambiguidade em recovery.
        if journal.exists() or journal.is_symlink():
            raise ValueError("Já existe journal de cópia: revisão manual obrigatória.")
        _journal(journal, "PREPARADO", source, target)
        temp: Path | None = None
        temp_identity: tuple[int, int] | None = None
        published = False
        try:
            fd, name = tempfile.mkstemp(prefix=".archivia-copy-", suffix=".tmp", dir=target.parent)
            temp = _safe_path(Path(name))
            temp_identity = (os.fstat(fd).st_dev, os.fstat(fd).st_ino)
            os.close(fd)
            _journal(journal, "TEMPORARIO_CRIADO", source, target)
            source_sha, dest_sha, source_before = _fingerprint(source, temp)
            _journal(journal, "HASH_VERIFICADO", source, target)
            # Conferir metadados e identidade mais uma vez imediatamente antes
            # da publicação; outros processos não respeitam o lock cooperativo.
            now = source.stat(follow_symlinks=False)
            before_id = (
                source_before.st_dev, source_before.st_ino,
                source_before.st_size, source_before.st_mtime_ns,
            )
            now_id = (now.st_dev, now.st_ino, now.st_size, now.st_mtime_ns)
            if now_id != before_id:
                raise ValueError("Origem alterada antes da publicação.")
            if target.exists() or target.is_symlink() or any(
                entry.name.casefold() == target.name.casefold() for entry in target.parent.iterdir()
                if entry != temp
            ):
                raise ValueError("Destino ocupado antes da publicação.")
            # O hardlink é criado no MESMO volume do temporário, mesmo quando
            # a origem da cópia estiver em outra unidade.
            os.link(temp, target, follow_symlinks=False)
            published = True
            _journal(journal, "PUBLICADO", source, target)
            return {
                "status": "copiado_verificado",
                "source": str(source),
                "destination": str(target),
                "sha256": dest_sha,
                "bytes": source_before.st_size,
                "source_preserved": True,
                "journal": str(journal),
                "test_only": True,
            }
        except Exception:
            _journal(journal, "INTERROMPIDO", source, target)
            raise
        finally:
            if temp is not None:
                try:
                    st = temp.stat(follow_symlinks=False)
                    if (
                        temp_identity == (st.st_dev, st.st_ino)
                        and stat.S_ISREG(st.st_mode)
                    ):
                        os.unlink(temp)
                except FileNotFoundError:
                    pass
                except OSError:
                    # Temporário remanescente exige revisão, não tocar na origem.
                    pass
