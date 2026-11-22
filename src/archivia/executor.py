"""Executor EXPERIMENTAL: somente um arquivo fictício sob tests/.runtime.

Não existe integração com CLI, GUI ou Ollama. Não utilizar com mídias reais.
Este estágio suporta apenas hardlink + remoção no mesmo volume, com journal.
"""
from __future__ import annotations

from datetime import datetime, timezone
from contextlib import contextmanager
import json
import os
from pathlib import Path
import stat
from typing import Any

from .catalog import DEFAULT_DB
from .planner import propose_moves

_CONFIRM = "CONFIRMO TESTE ARCHIVIA"
_RUNTIME = Path(__file__).resolve().parents[2] / "tests" / ".runtime"


def _safe_path(path: Path) -> Path:
    """Rejeita links simbólicos e junctions inclusive em componentes ancestrais."""
    absolute = path.expanduser().absolute()
    for component in (absolute, *absolute.parents):
        if component.is_symlink() or (
            hasattr(os.path, "isjunction") and os.path.isjunction(component)
        ):
            raise ValueError("Links simbólicos/junctions não são permitidos.")
    return absolute


def _inside_runtime(path: Path) -> tuple[Path, Path]:
    runtime = _safe_path(_RUNTIME)
    candidate = _safe_path(path)
    try:
        parts = candidate.relative_to(runtime).parts
    except ValueError as exc:
        raise ValueError("Executor limitado a tests/.runtime.") from exc
    if len(parts) < 3:
        raise ValueError("Origem/destino devem estar em pastas de teste isoladas.")
    return runtime, runtime / parts[0]


def _record(journal: Path, event: str, source: Path, target: Path) -> None:
    payload = {
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "source": str(source),
        "destination": str(target),
    }
    with journal.open("a", encoding="utf-8") as output:
        output.write(json.dumps(payload, ensure_ascii=False) + "\n")
        output.flush()
        os.fsync(output.fileno())


@contextmanager
def _exclusive_fixture_lock(test_root: Path):
    """Bloqueio cooperativo entre processos ArchivIA no mesmo caso de teste.

    Se houver lock remanescente após crash, NÃO removê-lo automaticamente.
    Outros aplicativos não respeitam este lock; não elimina TOCTOU externo.
    """
    runtime = _safe_path(_RUNTIME)
    folder = _safe_path(test_root)
    if folder.parent != runtime or not folder.is_dir():
        raise ValueError("Lock limitado a caso isolado em tests/.runtime.")
    # Diretório de lock é criado atomicamente. Não usar unlink aqui:
    # a operação de remoção do arquivo de origem pode falhar em testes.
    lock = _safe_path(folder / ".archivia-operation.lock")
    try:
        os.mkdir(lock)
    except FileExistsError as exc:
        raise ValueError(
            "Outro processo ArchivIA pode estar operando neste caso; "
            "lock presente. Inspeção manual necessária."
        ) from exc
    try:
        yield
    finally:
        # Em caso de falha de remoção, manter bloqueado e exigir revisão.
        try:
            os.rmdir(lock)
        except OSError:
            pass


def execute_test_move(
    plan: dict[str, Any],
    db_path: Path = DEFAULT_DB,
    *,
    approval: str,
) -> dict[str, Any]:
    """Entrada com exclusão cooperativa; ainda TEST-ONLY."""
    if approval != _CONFIRM:
        raise ValueError("Confirmação explícita de teste ausente.")
    if not isinstance(plan, dict) or not isinstance(plan.get("actions"), list) or len(plan["actions"]) != 1:
        raise ValueError("Plano deve conter uma única ação.")
    action = plan["actions"][0]
    if not isinstance(action, dict) or not isinstance(action.get("source"), str):
        raise ValueError("Origem inválida no plano.")
    _, folder = _inside_runtime(Path(action["source"]))
    with _exclusive_fixture_lock(folder):
        return _execute_test_move_unlocked(plan, db_path, approval=approval)


def _execute_test_move_unlocked(
    plan: dict[str, Any],
    db_path: Path = DEFAULT_DB,
    *,
    approval: str,
) -> dict[str, Any]:
    """Move um único arquivo TEST-ONLY; sem sobrescrita, sem operações por IA.

    A origem e o destino DEVEM estar dentro do mesmo caso de teste isolado.
    Nunca aceitar resumos globais, planos truncados, bloqueados ou arbitrários.
    Falha entre hardlink e remoção pode deixar dois nomes: consultar o journal
    e resolver manualmente; não efetuar rollback automático.
    """
    if approval != _CONFIRM:
        raise ValueError("Confirmação explícita de teste ausente.")
    if not isinstance(plan, dict) or plan.get("mode") != "simulation":
        raise ValueError("Plano inválido.")
    if plan.get("summary_only") or plan.get("executable") is not False:
        raise ValueError("Apenas uma prévia simulada pode ser validada.")
    if plan.get("truncated") or plan.get("blocked") != 0:
        raise ValueError("Plano incompleto ou com conflitos.")
    if plan.get("total_matches") != 1 or plan.get("selected") != 1:
        raise ValueError("Executor experimental aceita exatamente um arquivo.")
    if plan.get("category") not in ("imagem", "video", "audio"):
        raise ValueError("Categoria não autorizada.")
    if not isinstance(plan.get("scan_id"), int) or isinstance(plan["scan_id"], bool):
        raise ValueError("Snapshot inválido.")
    actions = plan.get("actions")
    if not isinstance(actions, list) or len(actions) != 1:
        raise ValueError("Plano deve conter uma única ação.")
    action = actions[0]
    if not isinstance(action, dict) or action.get("status") != "proposto":
        raise ValueError("Ação não aprovada.")

    source = _safe_path(Path(action["source"]))
    target = _safe_path(Path(action["destination"]))
    runtime, test_root = _inside_runtime(source)
    _, dest_test_root = _inside_runtime(target)
    if test_root != dest_test_root or source == target:
        raise ValueError("Origem e destino devem estar no mesmo teste isolado.")
    if not target.parent.is_dir() or not source.is_file():
        raise ValueError("Origem ou destino indisponíveis.")
    if target.exists() or target.is_symlink():
        raise ValueError("Destino já existe.")
    if any(entry.name.casefold() == target.name.casefold()
           for entry in target.parent.iterdir()):
        raise ValueError("Destino equivalente já existe.")

    # Recria a proposta da base SQLite para evitar plano adulterado ou obsoleto.
    refreshed = propose_moves(
        target.parent, plan["category"], db_path=db_path,
        limit=1, scan_id=plan["scan_id"],
    )
    if (refreshed["root"] != plan.get("root") or
            refreshed["destination"] != plan.get("destination") or
            refreshed["total_matches"] != 1 or refreshed["blocked"] or
            refreshed["truncated"] or refreshed["actions"] != actions):
        raise ValueError("Plano não corresponde mais ao catálogo ou ao disco.")

    before = source.stat(follow_symlinks=False)
    if not stat.S_ISREG(before.st_mode):
        raise ValueError("Origem não é arquivo regular.")
    if before.st_dev != target.parent.stat().st_dev:
        raise ValueError("Movimentação entre volumes ainda não está disponível.")

    journal = test_root / "archivia-executor-journal.jsonl"
    _record(journal, "PREPARADO", source, target)
    try:
        # Criação atômica sem sobrescrita; suportada apenas no mesmo volume.
        os.link(source, target, follow_symlinks=False)
    except OSError as exc:
        _record(journal, "FALHA_CRIACAO", source, target)
        raise ValueError(f"Não foi possível criar destino seguro: {exc}") from exc

    linked = target.stat(follow_symlinks=False)
    current = source.stat(follow_symlinks=False)
    if (linked.st_dev, linked.st_ino) != (before.st_dev, before.st_ino) or (
        current.st_dev, current.st_ino, current.st_size, current.st_mtime_ns
    ) != (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns):
        _record(journal, "INTERROMPIDO_VERIFICACAO", source, target)
        raise ValueError("Origem mudou; dois caminhos podem existir. Consulte o journal.")

    _record(journal, "DESTINO_CRIADO", source, target)
    # Checagem adicional após persistir o evento: se outro programa substituiu
    # algum caminho durante a escrita do journal, preservar ambos.
    try:
        last_source = source.stat(follow_symlinks=False)
        last_target = target.stat(follow_symlinks=False)
        unchanged = (
            (last_source.st_dev, last_source.st_ino, last_source.st_size,
             last_source.st_mtime_ns) ==
            (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
            and (last_target.st_dev, last_target.st_ino) ==
            (before.st_dev, before.st_ino)
        )
    except OSError:
        unchanged = False
    if not unchanged:
        _record(journal, "INTERROMPIDO_VERIFICACAO", source, target)
        raise ValueError("Origem/destino mudaram antes da remoção; revisão manual obrigatória.")
    try:
        os.unlink(source)
    except OSError as exc:
        _record(journal, "INTERROMPIDO_REMOCAO", source, target)
        raise ValueError(
            "Destino criado, mas origem preservada. Consulte o journal antes de repetir."
        ) from exc
    _record(journal, "CONCLUIDO", source, target)
    return {
        "status": "movido",
        "source": str(source),
        "destination": str(target),
        "journal": str(journal),
        "files_moved": 1,
        "test_only": True,
    }


def inspect_test_journal(test_directory: str | Path) -> dict[str, Any]:
    """Diagnóstico estritamente de leitura; nunca executa rollback.

    Lê eventos do journal de um caso em tests/.runtime e verifica a presença
    atual de origem e destino. Não interpreta presença como identidade de bytes
    nem declara uma operação interrompida como recuperada.
    """
    folder = _safe_path(Path(test_directory))
    runtime = _safe_path(_RUNTIME)
    if folder.parent != runtime or not folder.is_dir():
        raise ValueError("Inspeção limitada a um caso direto de tests/.runtime.")
    journal = _safe_path(folder / "archivia-executor-journal.jsonl")
    if not journal.is_file():
        raise ValueError("Journal do caso de teste não encontrado.")
    if journal.stat().st_size > 1024 * 1024:
        raise ValueError("Journal excessivamente grande para inspeção.")
    events: list[str] = []
    source: Path | None = None
    destination: Path | None = None
    with journal.open("r", encoding="utf-8") as handle:
        for raw in handle:
            if not raw.endswith("\n"):
                raise ValueError("Journal contém registro incompleto.")
            try:
                event = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError("Journal contém JSON inválido.") from exc
            if (not isinstance(event, dict) or
                    event.get("event") not in (
                        "PREPARADO", "FALHA_CRIACAO", "DESTINO_CRIADO",
                        "INTERROMPIDO_VERIFICACAO", "INTERROMPIDO_REMOCAO",
                        "CONCLUIDO", "RECUPERACAO_INICIADA", "RECUPERADO",
                    ) or not isinstance(event.get("source"), str) or
                    not isinstance(event.get("destination"), str)):
                raise ValueError("Registro do journal inválido.")
            current_source = _safe_path(Path(event["source"]))
            current_destination = _safe_path(Path(event["destination"]))
            _, group_source = _inside_runtime(current_source)
            _, group_dest = _inside_runtime(current_destination)
            if group_source != folder or group_dest != folder:
                raise ValueError("Journal aponta para outro caso de teste.")
            if source is None:
                source = current_source
                destination = current_destination
            elif source != current_source or destination != current_destination:
                raise ValueError("Journal reúne operações diferentes; revisão manual necessária.")
            events.append(event["event"])
    if not events or events[0] != "PREPARADO":
        raise ValueError("Journal não começa com preparação válida.")
    if events[-1] == "CONCLUIDO":
        status = "concluido_registrado"
    elif events[-1] == "RECUPERADO":
        status = "recuperado_registrado"
    elif events[-1] == "FALHA_CRIACAO":
        status = "falha_registrada"
    else:
        status = "revisao_manual_obrigatoria"
    return {
        "status": status,
        "last_event": events[-1],
        "events": events,
        "source_exists": source.exists(),
        "destination_exists": destination.exists(),
        "source": str(source),
        "destination": str(destination),
        "test_only": True,
        "automatic_recovery": False,
    }


def rollback_interrupted_test_move(
    test_directory: str | Path, *, approval: str,
) -> dict[str, Any]:
    """Exclusão cooperativa compartilhada entre execução e recuperação."""
    if approval != _CONFIRM:
        raise ValueError("Confirmação explícita de recuperação ausente.")
    folder = _safe_path(Path(test_directory))
    with _exclusive_fixture_lock(folder):
        return _rollback_interrupted_test_move_unlocked(
            folder, approval=approval,
        )


def _rollback_interrupted_test_move_unlocked(
    test_directory: str | Path, *, approval: str,
) -> dict[str, Any]:
    """Reverte APENAS o hardlink extra de uma falha TEST-ONLY conhecida.

    A origem precisa permanecer intacta e compartilhar a identidade física do
    destino. Outros estados exigem inspeção manual. Não oferece garantia contra
    troca simultânea de caminhos por outro processo; não usar com arquivos reais.
    """
    if approval != _CONFIRM:
        raise ValueError("Confirmação explícita de recuperação ausente.")
    report = inspect_test_journal(test_directory)
    if report["events"] != [
        "PREPARADO", "DESTINO_CRIADO", "INTERROMPIDO_REMOCAO",
    ]:
        raise ValueError("Estado do journal não permite recuperação automática.")
    source = _safe_path(Path(report["source"]))
    target = _safe_path(Path(report["destination"]))
    if not source.is_file() or not target.is_file():
        raise ValueError("Origem e destino devem existir como arquivos regulares.")
    before_source = source.stat(follow_symlinks=False)
    before_target = target.stat(follow_symlinks=False)
    if (not stat.S_ISREG(before_source.st_mode) or
            not stat.S_ISREG(before_target.st_mode) or
            (before_source.st_dev, before_source.st_ino) !=
            (before_target.st_dev, before_target.st_ino) or
            before_source.st_nlink < 2):
        raise ValueError("Identidade física não comprovada: revisão manual obrigatória.")
    journal = _safe_path(Path(test_directory) / "archivia-executor-journal.jsonl")
    _record(journal, "RECUPERACAO_INICIADA", source, target)
    # Segunda checagem imediatamente antes do unlink; contenção de escopo
    # permanece obrigatória, mesmo após inspeção e aprovação.
    _inside_runtime(source)
    _inside_runtime(target)
    current_source = source.stat(follow_symlinks=False)
    current_target = target.stat(follow_symlinks=False)
    if ((current_source.st_dev, current_source.st_ino,
         current_source.st_size, current_source.st_mtime_ns) !=
        (before_source.st_dev, before_source.st_ino,
         before_source.st_size, before_source.st_mtime_ns) or
        (current_target.st_dev, current_target.st_ino) !=
        (before_source.st_dev, before_source.st_ino)):
        raise ValueError("Arquivo alterado durante recuperação. Revisão manual.")
    os.unlink(target)
    _record(journal, "RECUPERADO", source, target)
    return {
        "status": "recuperado",
        "source_exists": source.exists(),
        "destination_exists": target.exists(),
        "journal": str(journal),
        "test_only": True,
    }
