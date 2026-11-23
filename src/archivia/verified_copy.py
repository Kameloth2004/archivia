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


def inspect_verified_copy_test(test_directory: str | Path) -> dict[str, Any]:
    """Diagnóstico SOMENTE LEITURA de cópia em fixture.

    A presença de PUBLICADO no journal não comprova durabilidade nem integridade
    do conteúdo. Hashes atuais só demonstram igualdade NO INSTANTE da inspeção.
    Não recupera, não limpa temporários, não retoma operações.
    """
    root = _safe_path(Path(test_directory))
    runtime = _safe_path(Path(__file__).resolve().parents[2] / "tests" / ".runtime")
    if root.parent != runtime or not root.is_dir():
        raise ValueError("Inspeção restrita a caso direto de tests/.runtime.")
    journal = _safe_path(root / "archivia-copy-journal.jsonl")
    if not journal.is_file():
        raise ValueError("Journal de cópia não encontrado.")
    if journal.stat().st_size > 1024 * 1024:
        raise ValueError("Journal de cópia excessivamente grande.")

    allowed = {
        "PREPARADO", "TEMPORARIO_CRIADO", "HASH_VERIFICADO",
        "PUBLICADO", "INTERROMPIDO", "COPIA_RECONCILIADA",
    }
    events: list[str] = []
    source = destination = None
    with journal.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.endswith("\n"):
                raise ValueError("Journal contém linha incompleta.")
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError("Journal de cópia inválido.") from exc
            if (
                not isinstance(item, dict)
                or item.get("event") not in allowed
                or not isinstance(item.get("source"), str)
                or not isinstance(item.get("destination"), str)
                or not isinstance(item.get("time_utc"), str)
            ):
                raise ValueError("Registro de cópia inválido.")
            current_source = _safe_path(Path(item["source"]))
            current_dest = _safe_path(Path(item["destination"]))
            _, src_group = _inside_runtime(current_source)
            _, dst_group = _inside_runtime(current_dest)
            if src_group != root or dst_group != root:
                raise ValueError("Journal aponta para outro caso de teste.")
            if source is None:
                source, destination = current_source, current_dest
            elif source != current_source or destination != current_dest:
                raise ValueError("Journal mistura operações distintas.")
            events.append(item["event"])
    if not events or events[0] != "PREPARADO":
        raise ValueError("Sequência do journal inválida.")
    expected = ["PREPARADO", "TEMPORARIO_CRIADO", "HASH_VERIFICADO", "PUBLICADO"]
    # Uma interrupção pode ocorrer depois de qualquer evento registrado;
    # falha na criação do temporário pode deixar só PREPARADO.
    reconciled = events[-1] == "COPIA_RECONCILIADA"
    if reconciled:
        # Registro de reconciliação apenas após falha de journal pós-publicação.
        if events != [
            "PREPARADO", "TEMPORARIO_CRIADO", "HASH_VERIFICADO",
            "INTERROMPIDO", "COPIA_RECONCILIADA",
        ]:
            raise ValueError("Sequência de reconciliação inválida.")
    else:
        main = events[:-1] if events[-1] == "INTERROMPIDO" else events
        if main != expected[:len(main)] or len(main) > len(expected) or (
            "INTERROMPIDO" in events[:-1]
        ):
            raise ValueError("Sequência inconsistente do journal de cópia.")

    if not destination.parent.is_dir():
        raise ValueError("Pasta de destino indisponível para inspeção.")
    leftovers = []
    for entry in destination.parent.iterdir():
        if entry.name.startswith(".archivia-copy-") and entry.name.endswith(".tmp"):
            _safe_path(entry)  # Falha fechada para symlink/junction.
            if not entry.is_file():
                raise ValueError("Artefato temporário não é arquivo regular.")
            leftovers.append(str(entry))
    leftovers.sort()

    def _existing_regular(path: Path) -> bool:
        if not path.exists():
            return False
        info = path.stat(follow_symlinks=False)
        if not stat.S_ISREG(info.st_mode):
            raise ValueError("Caminho inspecionado não é arquivo regular.")
        return True

    source_exists = _existing_regular(source)
    destination_exists = _existing_regular(destination)

    # Relatar igualdade observada agora; não declarar 'recuperado' a partir disso.
    hashes_match: bool | None = None
    if source_exists and destination_exists:
        def digest(path: Path) -> str:
            h = hashlib.sha256()
            flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            fd = os.open(path, flags)
            try:
                with os.fdopen(fd, "rb", closefd=False) as handle:
                    while chunk := handle.read(_BUFFER):
                        h.update(chunk)
            finally:
                os.close(fd)
            return h.hexdigest()
        hashes_match = digest(source) == digest(destination)

    if reconciled:
        status = "copia_reconciliada_registrada"
    elif events[-1] == "PUBLICADO" and destination_exists and not leftovers:
        status = "publicacao_registrada_inspecionada"
    elif events[-1] == "INTERROMPIDO":
        status = "interrompido_revisao_manual"
    else:
        status = "incompleto_revisao_manual"

    return {
        "status": status,
        "events": events,
        "last_event": events[-1],
        "source": str(source),
        "destination": str(destination),
        "source_exists": source_exists,
        "destination_exists": destination_exists,
        "current_sha256_equal": hashes_match,
        "temporary_files": leftovers,
        "temporary_count": len(leftovers),
        "test_only": True,
        "read_only": True,
        "automatic_recovery": False,
    }


def reconcile_published_test_copy(
    test_directory: str | Path, *, approval: str,
) -> dict[str, Any]:
    """Reconcilia SOMENTE o journal após publicação confirmada em fixture.

    Jamais apaga, move, altera ou recupera arquivos. O formato antigo do
    journal não identifica temporários nem a identidade da cópia publicada:
    por isso este procedimento só autoriza marcar a cópia como verificada
    com ambos os arquivos presentes e nenhum temporário remanescente.
    """
    if approval != _CONFIRM:
        raise ValueError("Confirmação explícita de reconciliação ausente.")
    folder = _safe_path(Path(test_directory))
    with _exclusive_fixture_lock(folder):
        report = inspect_verified_copy_test(folder)
        if report["events"] != [
            "PREPARADO", "TEMPORARIO_CRIADO", "HASH_VERIFICADO",
            "INTERROMPIDO",
        ]:
            raise ValueError("Journal não permite reconciliação deste estado.")
        if (not report["source_exists"] or not report["destination_exists"]
                or report["temporary_count"] != 0
                or report["current_sha256_equal"] is not True):
            raise ValueError("Arquivos ou temporários exigem revisão manual.")

        source = _safe_path(Path(report["source"]))
        destination = _safe_path(Path(report["destination"]))
        # Revalidar SHA-256 e metadados sem modificar os dois arquivos.
        def stable_digest(path: Path) -> str:
            flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            fd = os.open(path, flags)
            try:
                before = os.fstat(fd)
                if not stat.S_ISREG(before.st_mode):
                    raise ValueError("Arquivo deixou de ser regular.")
                digest = hashlib.sha256()
                with os.fdopen(os.dup(fd), "rb") as f:
                    while chunk := f.read(_BUFFER):
                        digest.update(chunk)
                after = os.fstat(fd)
                now = path.stat(follow_symlinks=False)
                identity = lambda st: (
                    st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns,
                )
                if identity(before) != identity(after) or identity(after) != identity(now):
                    raise ValueError("Arquivo mudou durante verificação.")
                return digest.hexdigest()
            finally:
                os.close(fd)

        source_hash = stable_digest(source)
        dest_hash = stable_digest(destination)
        if source_hash != dest_hash:
            raise ValueError("Hashes divergentes; revisão manual obrigatória.")
        # Esta é uma reconciliação de REGISTRO, não uma garantia de segurança
        # contra processos externos nem de resistência a queda de energia.
        journal = _safe_path(folder / "archivia-copy-journal.jsonl")
        _journal(journal, "COPIA_RECONCILIADA", source, destination)
        return {
            "status": "copia_reconciliada_registrada",
            "source": str(source),
            "destination": str(destination),
            "sha256": source_hash,
            "source_preserved": True,
            "destination_preserved": True,
            "automatic_cleanup": False,
            "test_only": True,
        }
