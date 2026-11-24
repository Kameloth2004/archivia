"""Execução unitária supervisionada do plano recursivo.

NÃO é ferramenta Ollama. Somente a interface, mediante confirmação explícita,
pode solicitar uma movimentação. Nunca sobrescreve; origem é preservada em falhas.
"""
from __future__ import annotations

from contextlib import closing
from pathlib import Path
from datetime import datetime
import hashlib
import os
import sqlite3
import tempfile
from typing import Any

from .catalog import DEFAULT_DB
from .duplicates import (
    CHUNK_BYTES, _candidate_path, _is_symlink_component,
    _sha256_checked,
)
from .conflict_hash import verify_plan_conflict
from .conflict_report import _suggest_unused_name

APPROVAL_PHRASE = "MOVER UM ARQUIVO"


class MoveSkippedError(ValueError):
    """Bloqueio identificado antes de publicar arquivo no destino.

    Apenas estes erros são seguros para registrar e seguir ao próximo item.
    Falhas imprevistas interrompem o lote para preservar integridade.
    """



def preview_conflict_move(
    plan: dict[str, Any] | None, relative_file: str, *,
    db_path: Path = DEFAULT_DB, scan_id: int | None = None,
) -> dict[str, Any]:
    """Recomenda a preservação das duas versões; NÃO altera arquivos."""
    if (not isinstance(plan, dict) or plan.get("operation") != "move_recursive_consolidation"
            or plan.get("mode") != "simulation" or plan.get("executable") is not False
            or plan.get("complete") is not True or plan.get("pending") != 0
            or plan.get("scan_id") != scan_id
            or not isinstance(plan.get("actions"), list)
            or not isinstance(relative_file, str) or not relative_file):
        raise ValueError("Planejamento inválido ou incompleto.")
    actions = plan["actions"]
    rows = [a for a in actions if isinstance(a, dict)
            and a.get("file") == relative_file
            and a.get("status") == "bloqueado"
            and a.get("reason") == "destino_ja_existe"]
    if len(rows) != 1:
        raise ValueError("Selecione um conflito de nome único.")
    name = relative_file.rsplit("/", 1)[-1]
    if sum(isinstance(a, dict) and isinstance(a.get("file"), str)
           and a["file"].rsplit("/", 1)[-1].casefold() == name.casefold()
           for a in actions) != 1:
        raise ValueError("Há duas origens com o mesmo nome; requer análise manual.")
    result = verify_plan_conflict(plan, relative_file, db_path=db_path, scan_id=scan_id)
    if result["status"] != "conteudo_diferente":
        raise ValueError("Não há duas versões diferentes confirmadas para preservar.")
    destination = Path(plan["destination"]).expanduser().absolute()
    if _is_symlink_component(destination) or not destination.is_dir():
        raise ValueError("Pasta de destino indisponível.")
    reserved = {Path(str(a["destination"])).name.casefold()
                for a in actions if isinstance(a, dict) and a.get("destination")}
    reserved.update(p.name.casefold() for p in destination.iterdir())
    alternative = _suggest_unused_name(destination, name, reserved)
    if alternative is None or _is_symlink_component(destination / alternative):
        raise ValueError("Não há um nome alternativo livre e seguro.")
    return {
        "file": relative_file,
        "original_destination": str(destination / name),
        "new_destination": str(destination / alternative),
        "suggested_filename": alternative,
        "status": "conteudo_diferente",
        "read_only": True, "files_modified": False,
    }


def move_one_approved(
    plan: dict[str, Any] | None, relative_file: str, *,
    db_path: Path = DEFAULT_DB, scan_id: int | None = None,
    approval: str = "", resolve_conflict: bool = False,
    approved_target_name: str | None = None,
) -> dict[str, Any]:
    """Copia, verifica, publica sem overwrite e remove a origem após revalidação.

    Em caso de falha após a publicação, mantém origem e informa cópia retida.
    Não resolve automaticamente conflitos/duplicatas do plano.
    """
    if approval != APPROVAL_PHRASE:
        raise ValueError("Confirmação explícita da interface é obrigatória.")
    if (not isinstance(relative_file, str) or not relative_file.strip()
            or len(relative_file) > 512):
        raise ValueError("Informe o caminho relativo exato de um arquivo.")
    if (not isinstance(scan_id, int) or isinstance(scan_id, bool) or scan_id < 1
            or not isinstance(plan, dict) or plan.get("scan_id") != scan_id
            or plan.get("mode") != "simulation"
            or plan.get("executable") is not False
            or not isinstance(plan.get("actions"), list)
            or plan.get("complete") is not True
            or plan.get("pending") != 0
            or plan.get("operation") != "move_recursive_consolidation"):
        raise ValueError("Planejamento inválido ou de outro snapshot.")
    actions = plan["actions"]
    selected = [a for a in actions if isinstance(a, dict)
                and a.get("file") == relative_file
                and a.get("status") == ("bloqueado" if resolve_conflict else "proposto")
                and a.get("reason") == ("destino_ja_existe" if resolve_conflict else None)]
    if len(selected) != 1:
        raise ValueError("O arquivo não está proposto de maneira única no plano.")
    action = selected[0]
    root = Path(plan["root"]).expanduser().absolute()
    destination = Path(plan["destination"]).expanduser().absolute()
    if (_is_symlink_component(root) or _is_symlink_component(destination)
            or not root.is_dir() or not destination.is_dir()
            or destination == root or root in destination.parents):
        raise ValueError("Origem ou destino inválido, aninhado ou com link.")
    source = _candidate_path(root, relative_file)
    original_target = destination / source.name
    if (source == original_target or str(source) != action.get("source")
            or str(original_target) != action.get("destination")):
        raise ValueError("Os caminhos não correspondem ao planejamento.")
    target = original_target
    # Não aprovar nomes-base disputados por outras ações, mesmo bloqueadas.
    if sum(isinstance(a, dict) and isinstance(a.get("file"), str)
           and a["file"].rsplit("/", 1)[-1].casefold() == source.name.casefold()
           for a in actions) != 1:
        raise ValueError("Nome-base ambíguo entre arquivos do plano.")
    if not resolve_conflict:
        if any(p.name.casefold() == target.name.casefold() for p in destination.iterdir()):
            raise MoveSkippedError("Nome de destino já ocupado.")
        if _is_symlink_component(target) or target.exists():
            raise MoveSkippedError("Destino não está livre.")

    # Não reconstruímos TODA a prévia por arquivo: em uma fila com milhares
    # de itens isso seria O(n²). Os vínculos e metadados do item são
    # revalidados imediatamente antes da cópia e o destino é rechecado na publicação.
    if resolve_conflict:
        # O nome efetivo deve ser exatamente aquele mostrado na confirmação.
        preview = preview_conflict_move(
            plan, relative_file, db_path=db_path, scan_id=scan_id,
        )
        if (not isinstance(approved_target_name, str)
                or preview["suggested_filename"] != approved_target_name):
            raise ValueError("Nome alternativo mudou; revise e confirme novamente.")
        target = destination / approved_target_name

    db = Path(db_path).expanduser().absolute()
    with closing(sqlite3.connect(db.as_uri() + "?mode=ro", uri=True)) as conn:
        conn.row_factory = sqlite3.Row
        scan = conn.execute("SELECT root FROM scans WHERE id=?", (scan_id,)).fetchone()
        record = conn.execute(
            "SELECT size_bytes, modified_utc FROM media "
            "WHERE scan_id=? AND relative_path=? AND category=?",
            (scan_id, relative_file, plan["category"]),
        ).fetchone()
    if scan is None or Path(scan["root"]).absolute() != root or record is None:
        raise ValueError("Arquivo não pertence ao snapshot selecionado.")
    size, modified = record["size_bytes"], record["modified_utc"]
    if not isinstance(size, int) or size < 0:
        raise MoveSkippedError("Tamanho do arquivo inválido no inventário.")

    original_stat = source.stat(follow_symlinks=False)
    expected_timestamp = datetime.fromisoformat(modified).timestamp()
    if original_stat.st_size != size or abs(original_stat.st_mtime - expected_timestamp) > .001:
        raise MoveSkippedError("Origem mudou desde o inventário.")
    try:
        source_hash = _sha256_checked(source, size, modified)
    except (OSError, ValueError) as exc:
        raise MoveSkippedError(f"Origem indisponível ou modificada: {exc}") from exc
    stage: Path | None = None
    published = False
    try:
        # Temporário nasce no MESMO volume do destino (inclusive entre D: e E:).
        fd, stage_name = tempfile.mkstemp(prefix=".archivia-stage-", suffix=".tmp",
                                          dir=destination)
        stage = Path(stage_name)
        with os.fdopen(fd, "wb") as output:
            flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
            source_fd = os.open(source, flags)
            with os.fdopen(source_fd, "rb") as input_file:
                source_fstat = os.fstat(input_file.fileno())
                if (source_fstat.st_dev != original_stat.st_dev
                        or source_fstat.st_ino != original_stat.st_ino
                        or source_fstat.st_size != size
                        or source_fstat.st_mtime_ns != original_stat.st_mtime_ns):
                    raise ValueError("Origem alterada antes da cópia.")
                digest = hashlib.sha256()
                copied = 0
                while True:
                    chunk = input_file.read(CHUNK_BYTES)
                    if not chunk:
                        break
                    copied += len(chunk)
                    if copied > size:
                        raise ValueError("Origem alterada durante a cópia.")
                    digest.update(chunk)
                    output.write(chunk)
                after = os.fstat(input_file.fileno())
                if (copied != size or digest.hexdigest() != source_hash
                        or after.st_size != source_fstat.st_size
                        or after.st_mtime_ns != source_fstat.st_mtime_ns):
                    raise ValueError("Origem alterada durante a cópia.")
            output.flush()
            os.fsync(output.fileno())
        # Confere os bytes realmente gravados, sem depender do hash em trânsito.
        with stage.open("rb") as stream:
            verifier = hashlib.sha256()
            while chunk := stream.read(CHUNK_BYTES):
                verifier.update(chunk)
            verified_hash = verifier.hexdigest()
        if verified_hash != source_hash or stage.stat().st_size != size:
            raise ValueError("Falha de integridade na cópia temporária.")
        if (_is_symlink_component(destination)
                or any(p.name.casefold() == target.name.casefold()
                       for p in destination.iterdir())):
            raise ValueError("Destino ficou ocupado durante a cópia.")
        # Hardlink temporário -> definitivo, NO MESMO volume. os.link falha se
        # o destino já existir: publicação atômica sem overwrite.
        try:
            os.link(stage, target)
        except FileExistsError as exc:
            raise MoveSkippedError("Nome de destino ocupado durante a cópia.") from exc
        published = True
        # Uma alteração concorrente na origem deve impedir sua remoção.
        try:
            current = source.stat(follow_symlinks=False)
            unchanged = (
                current.st_dev == original_stat.st_dev
                and current.st_ino == original_stat.st_ino
                and current.st_size == original_stat.st_size
                and current.st_mtime_ns == original_stat.st_mtime_ns
                and not _is_symlink_component(source)
                and _sha256_checked(source, size, modified) == source_hash
            )
        except (OSError, ValueError):
            unchanged = False
        if not unchanged:
            return {
                "status": "copiado_origem_preservada", "source": str(source),
                "destination": str(target), "sha256": source_hash,
                "detail": "Origem alterada ou indisponível após a publicação; não removida.",
            }
        try:
            source.unlink()
        except OSError:
            return {
                "status": "copiado_origem_preservada", "source": str(source),
                "destination": str(target), "sha256": source_hash,
                "detail": "Não foi possível remover a origem; ambas as cópias permanecem.",
            }
        return {
            "status": "movido", "source": str(source),
            "destination": str(target), "sha256": source_hash,
            "bytes": size, "files_modified": True,
        }
    finally:
        if stage is not None:
            try:
                stage.unlink(missing_ok=True)
            except OSError:
                pass
        # Nunca removemos o destino publicado automaticamente: em falha depois
        # da publicação, manter ambas as cópias é mais seguro que perder dados.
