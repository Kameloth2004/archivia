"""Pipeline de MOVIMENTAÇÃO experimental, isolado em tests/.runtime.

Testa a estratégia válida também entre volumes: copiar para temporário no
destino, validar SHA-256, publicar sem sobrescrever e só então remover origem.
Nenhum acesso por GUI, agente ou CLI. Nunca usar com mídias pessoais.
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

from .executor import _exclusive_fixture_lock, _inside_runtime, _safe_path
from .catalog import DEFAULT_DB
from .planner import propose_moves

_APPROVAL = "CONFIRMO MOVIMENTO DE TESTE"
_CHUNK = 1024 * 1024


def _identity(st: os.stat_result) -> tuple[int, int, int, int]:
    return st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns


def _event(journal: Path, stage: str, source: Path, target: Path, **details: Any) -> None:
    row = {
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "event": stage,
        "source": str(source),
        "destination": str(target),
        **details,
    }
    with journal.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def _digest(path: Path) -> tuple[str, os.stat_result]:
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags)
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError("Arquivo não regular.")
        h = hashlib.sha256()
        with os.fdopen(os.dup(fd), "rb") as inp:
            while block := inp.read(_CHUNK):
                h.update(block)
        after = os.fstat(fd)
        current = path.stat(follow_symlinks=False)
        if _identity(before) != _identity(after) or _identity(before) != _identity(current):
            raise ValueError("Arquivo alterado durante verificação.")
        return h.hexdigest(), before
    finally:
        os.close(fd)


def _verify_plan(plan: dict[str, Any], database: Path) -> tuple[Path, Path, Path]:
    if (
        not isinstance(plan, dict) or plan.get("mode") != "simulation"
        or plan.get("executable") is not False or plan.get("summary_only")
        or plan.get("truncated") or plan.get("blocked") != 0
        or plan.get("total_matches") != 1 or plan.get("selected") != 1
        or plan.get("category") not in ("imagem", "video", "audio")
        or not isinstance(plan.get("scan_id"), int)
        or isinstance(plan.get("scan_id"), bool)
    ):
        raise ValueError("Plano não autorizado para teste de movimentação.")
    actions = plan.get("actions")
    if not isinstance(actions, list) or len(actions) != 1 or not isinstance(actions[0], dict):
        raise ValueError("Plano deve conter uma única ação.")
    action = actions[0]
    if action.get("status") != "proposto" or not isinstance(action.get("source"), str) or not isinstance(action.get("destination"), str):
        raise ValueError("Ação de movimentação inválida.")
    source = _safe_path(Path(action["source"]))
    target = _safe_path(Path(action["destination"]))
    _, root = _inside_runtime(source)
    _, target_root = _inside_runtime(target)
    if root != target_root or source == target:
        raise ValueError("Movimentação restrita ao mesmo caso tests/.runtime.")
    if not source.is_file() or not target.parent.is_dir():
        raise ValueError("Origem ou destino indisponíveis.")
    if target.exists() or target.is_symlink() or any(
        p.name.casefold() == target.name.casefold() for p in target.parent.iterdir()
    ):
        raise ValueError("Destino já ocupado.")
    refreshed = propose_moves(
        target.parent, plan["category"], db_path=database,
        scan_id=plan["scan_id"], limit=1,
    )
    if (
        refreshed.get("root") != plan.get("root")
        or refreshed.get("destination") != plan.get("destination")
        or refreshed.get("total_matches") != 1
        or refreshed.get("blocked") or refreshed.get("truncated")
        or refreshed.get("actions") != actions
    ):
        raise ValueError("Plano diverge do snapshot ou do disco.")
    return source, target, root


def move_verified_test_file(
    plan: dict[str, Any],
    db_path: Path = DEFAULT_DB,
    *,
    approval: str,
) -> dict[str, Any]:
    """Move uma fixture somente após cópia publicada e verificada.

    Falhas ou queda entre publicação e remoção podem deixar os dois arquivos.
    Falhas após remoção podem deixar destino presente e journal incompleto.
    Nunca repetir automaticamente; inspecionar e resolver manualmente.
    """
    if approval != _APPROVAL:
        raise ValueError("Confirmação explícita de movimento de teste ausente.")
    if not isinstance(plan, dict) or not isinstance(plan.get("actions"), list) or len(plan["actions"]) != 1:
        raise ValueError("Plano inválido.")
    action = plan["actions"][0]
    if not isinstance(action, dict) or not isinstance(action.get("source"), str):
        raise ValueError("Origem inválida.")
    _, root = _inside_runtime(Path(action["source"]))
    with _exclusive_fixture_lock(root):
        source, target, root = _verify_plan(plan, db_path)
        journal = _safe_path(root / "archivia-move-v2.jsonl")
        if journal.exists() or journal.is_symlink():
            raise ValueError("Journal de movimentação existente; revisão manual obrigatória.")
        _event(journal, "PREPARADO", source, target)
        tmp: Path | None = None
        temp_id: tuple[int, int] | None = None
        fd = -1
        published = False
        try:
            source_hash, source_before = _digest(source)
            fd, name = tempfile.mkstemp(
                dir=target.parent, prefix=".archivia-move-", suffix=".tmp",
            )
            tmp = _safe_path(Path(name))
            tmp_info = os.fstat(fd)
            temp_id = (tmp_info.st_dev, tmp_info.st_ino)
            _event(journal, "TEMPORARIO_CRIADO", source, target, temporary=str(tmp))
            flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            src_fd = os.open(source, flags)
            try:
                before_copy = os.fstat(src_fd)
                if _identity(before_copy) != _identity(source_before):
                    raise ValueError("Origem alterada antes da cópia.")
                with os.fdopen(os.dup(src_fd), "rb") as input_file:
                    with os.fdopen(fd, "wb") as output_file:
                        fd = -1
                        while block := input_file.read(_CHUNK):
                            output_file.write(block)
                        output_file.flush()
                        os.fsync(output_file.fileno())
                after_copy = os.fstat(src_fd)
                if _identity(after_copy) != _identity(source_before):
                    raise ValueError("Origem alterada durante a cópia.")
            finally:
                os.close(src_fd)
            copied_hash, _ = _digest(tmp)
            fresh_hash, current_source = _digest(source)
            if copied_hash != source_hash or fresh_hash != source_hash or (
                _identity(current_source) != _identity(source_before)
            ):
                raise ValueError("SHA-256 ou identidade divergente; origem preservada.")
            _event(journal, "HASH_VERIFICADO", source, target, sha256=copied_hash)
            if target.exists() or target.is_symlink() or any(
                p != tmp and p.name.casefold() == target.name.casefold()
                for p in target.parent.iterdir()
            ):
                raise ValueError("Destino ocupado antes da publicação.")
            os.link(tmp, target, follow_symlinks=False)
            published = True
            _event(journal, "PUBLICADO", source, target, sha256=copied_hash)
            # Revalidar conteúdo e identidade antes da etapa destrutiva.
            verified_target, target_stat = _digest(target)
            verified_source, current_source = _digest(source)
            if (
                verified_target != copied_hash
                or verified_source != copied_hash
                or _identity(current_source) != _identity(source_before)
                or (target_stat.st_dev, target_stat.st_ino) != temp_id
            ):
                raise ValueError("Arquivo alterado após publicação; preservar origem.")
            _event(journal, "REMOCAO_AUTORIZADA", source, target, sha256=copied_hash)
            os.unlink(source)
            _event(journal, "CONCLUIDO", source, target, sha256=copied_hash)
            return {
                "status": "movido", "source": str(source),
                "destination": str(target), "sha256": copied_hash,
                "journal": str(journal), "files_moved": 1,
                "test_only": True,
            }
        except Exception:
            _event(journal, "INTERROMPIDO", source, target, published=published)
            raise
        finally:
            if fd != -1:
                os.close(fd)
            if tmp is not None:
                try:
                    st = tmp.stat(follow_symlinks=False)
                    if stat.S_ISREG(st.st_mode) and (
                        st.st_dev, st.st_ino
                    ) == temp_id:
                        tmp.unlink()
                except OSError:
                    # Em caso de suspeita, preservar o arquivo temporário.
                    pass
