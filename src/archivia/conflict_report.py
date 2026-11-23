"""Relatório consultivo de conflitos do último planejamento; nenhuma ação executável."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .catalog import DEFAULT_DB
from .conflict_hash import verify_plan_conflict

_MAX_ITEMS = 10
_MAX_SUFFIX = 1000


def _suggest_unused_name(destination: Path, filename: str, reserved: set[str]) -> str | None:
    """Somente propõe um nome; não cria nem reserva arquivos no disco."""
    base = Path(filename)
    # Evita colisões, inclusive por diferença de caixa e pelos demais itens planejados.
    for number in range(1, _MAX_SUFFIX + 1):
        candidate = f"{base.stem}_archivia_{number}{base.suffix}"
        if candidate.casefold() not in reserved and not (destination / candidate).exists():
            return candidate
    return None


def conflict_resolution_report(
    plan: dict[str, Any] | None, *, db_path: Path = DEFAULT_DB,
    scan_id: int | None = None, limit: int = 10,
) -> dict[str, Any]:
    """Avalia até dez conflitos; todos permanecem bloqueados e não executáveis."""
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= _MAX_ITEMS:
        raise ValueError("Limite de conflitos inválido (1 a 10).")
    if (not isinstance(plan, dict) or plan.get("mode") != "simulation"
            or plan.get("executable") is not False
            or not isinstance(scan_id, int) or isinstance(scan_id, bool)
            or plan.get("scan_id") != scan_id
            or not isinstance(plan.get("actions"), list)):
        raise ValueError("Plano anterior indisponível ou de outro snapshot.")
    actions = plan["actions"]
    blocked = [a for a in actions if isinstance(a, dict) and a.get("status") == "bloqueado"]
    selected = blocked[:limit]
    # Detecta nomes-base repetidos em TODO o plano, inclusive fora do limite.
    # Não escolhe automaticamente qual origem seria comparada.
    basename_counts: dict[str, int] = {}
    for item in actions:
        if isinstance(item, dict) and isinstance(item.get("file"), str):
            basename = item["file"].rsplit("/", 1)[-1].casefold()
            basename_counts[basename] = basename_counts.get(basename, 0) + 1
    # Nomes já presentes no planejamento não podem ser sugeridos como alternativas.
    reserved = {Path(str(a.get("destination"))).name.casefold()
                for a in actions if isinstance(a, dict) and a.get("destination")}
    destination = Path(plan["destination"]).expanduser().absolute()
    # Incorporar nomes do destino preserva a segurança em sistemas sem case-fold.
    try:
        if not destination.is_dir() or destination.is_symlink():
            raise OSError("destino indisponível")
        reserved.update(p.name.casefold() for p in destination.iterdir())
        destination_valid = True
    except (OSError, ValueError, TypeError):
        destination_valid = False

    rows: list[dict[str, Any]] = []
    for action in selected:
        name = action.get("file")
        reason = action.get("reason")
        row: dict[str, Any] = {
            "file": name,
            "reason_code": reason,
            "status": "inconclusivo",
            "recommendation": "Manter bloqueado e solicitar nova análise.",
            "suggested_filename": None,
            "executable": False,
        }
        if reason == "destino_ja_existe" and isinstance(name, str):
            if basename_counts.get(name.rsplit("/", 1)[-1].casefold(), 0) > 1:
                row["detail"] = "nome_base_ambiguo_entre_origens"
                row["sha256_equal"] = None
                rows.append(row)
                continue
            try:
                result = verify_plan_conflict(plan, name, db_path=db_path, scan_id=scan_id)
            except ValueError:
                result = {"status": "inconclusivo", "sha256_equal": None,
                          "detail": "conflito_ambiguo_ou_plano_invalido"}
            row["status"] = result["status"]
            row["sha256_equal"] = result["sha256_equal"]
            if result["status"] == "duplicata_confirmada":
                row["recommendation"] = (
                    "Conteúdo idêntico: conservar a cópia existente no destino; "
                    "não excluir nem mover automaticamente a origem."
                )
            elif result["status"] == "conteudo_diferente":
                row["recommendation"] = (
                    "Conteúdo diferente: preservar ambos; avaliar nome alternativo "
                    "antes de qualquer movimentação."
                )
                if destination_valid:
                    alternative = _suggest_unused_name(destination, Path(name).name, reserved)
                    if alternative:
                        row["suggested_filename"] = alternative
                        reserved.add(alternative.casefold())
            else:
                row["detail"] = result.get("detail")
        elif reason != "destino_ja_existe":
            row["recommendation"] = (
                "Bloqueio não relacionado a destino existente: revisar o motivo "
                "original antes de planejar qualquer ação."
            )
        rows.append(row)

    return {
        "operation": "conflict_resolution_advice",
        "scan_id": scan_id,
        "total_blocked_in_plan": len(blocked),
        "examined": len(rows),
        "pending": len(blocked) - len(rows),
        "complete": len(rows) == len(blocked),
        "results": rows,
        "note": ("Sugestões são informativas e podem ficar desatualizadas; "
                 "não reservam nomes e não autorizam ações."),
        "mode": "read_only",
        "executable": False,
        "files_modified": False,
    }
