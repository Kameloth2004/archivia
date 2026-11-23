"""Memória operacional, efêmera, do último plano recursivo.

Sem escrita em disco. Preserva apenas os dados estruturados gerados pelo
planejador Python, jamais afirma que nomes iguais são duplicatas SHA-256.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

_REASONS = {
    "destino_ja_existe": "Já existe no destino um arquivo com o mesmo nome; o conteúdo não foi comparado por SHA-256.",
    "nome_repetido_entre_subpastas": "Mais de uma origem do plano produziria o mesmo nome no destino.",
    "origem_ausente_ou_link": "A origem não está disponível ou há um link simbólico no caminho.",
    "origem_alterada_desde_inventario": "Tamanho ou data de modificação da origem mudou desde o inventário.",
    "mesmo_caminho": "Origem e destino correspondem ao mesmo caminho.",
    "caminho_invalido": "O caminho registrado no catálogo é inválido.",
    "metadados_indisponiveis": "Não foi possível verificar os metadados da origem.",
}
_MAX_ACTIONS = 500


def latest_recursive_plan(tools_used: Any, scan_id: int | None) -> dict[str, Any] | None:
    """Retém apenas um resultado do planejador ligado ao snapshot da sessão."""
    if not isinstance(tools_used, list):
        return None
    for call in reversed(tools_used):
        if not isinstance(call, dict) or call.get("tool") != "planejar_consolidacao_recursiva":
            continue
        result = call.get("result")
        if (
            not isinstance(result, dict)
            or result.get("mode") != "simulation"
            or result.get("executable") is not False
            or result.get("scan_id") != scan_id
            or not isinstance(result.get("actions"), list)
            or len(result["actions"]) > _MAX_ACTIONS
        ):
            continue
        return deepcopy(result)
    return None


def blocked_details(plan: dict[str, Any] | None, *,
                    file_name: str = "", limit: int = 25) -> dict[str, Any]:
    """Consulta em memória por nome relativo ou nome-base; não acessa disco."""
    if plan is None:
        raise ValueError("Não há plano recursivo anterior nesta sessão. Gere uma prévia.")
    if not isinstance(file_name, str) or len(file_name) > 512:
        raise ValueError("Filtro de nome inválido.")
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 25:
        raise ValueError("Limite inválido; máximo 25.")
    actions = plan.get("actions", [])
    blocked = [action for action in actions if (
        isinstance(action, dict) and action.get("status") == "bloqueado"
    )]
    needle = file_name.strip().replace(chr(92), "/").casefold()
    if needle:
        blocked = [action for action in blocked if (
            str(action.get("file", "")).casefold() == needle
            or str(action.get("file", "")).rsplit("/", 1)[-1].casefold() == needle
        )]
    rows = [{
        "file": action.get("file"),
        "source": action.get("source"),
        "destination": action.get("destination"),
        "reason_code": action.get("reason"),
        "explanation": _REASONS.get(
            action.get("reason"), "Bloqueio registrado pelo planejador; requer inspeção."
        ),
        "duplicate_sha256_confirmed": False,
    } for action in blocked[:limit]]
    return {
        "scan_id": plan.get("scan_id"),
        "root": plan.get("root"),
        "destination": plan.get("destination"),
        "total_blocked_in_plan": sum(
            1 for action in actions if isinstance(action, dict) and action.get("status") == "bloqueado"
        ),
        "matching_blocked": len(blocked),
        "returned": len(rows),
        "truncated": len(blocked) > limit,
        "plan_complete": plan.get("complete") is True,
        "files": rows,
        "read_only": True,
        "files_modified": False,
    }
