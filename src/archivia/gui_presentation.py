"""Helpers puros de filtro, paginação e relatórios da GUI.

Sem Qt, Ollama, SQLite ou escrita de arquivos; o backend continua responsável
pelas regras de negócio. Estes helpers só preparam consulta e apresentação.
"""
from __future__ import annotations

import json
from typing import Any

from .date_formats import parse_user_date


def catalog_filters(
    *, category: str | None, scan_id: int | None, name: str,
    extension: str, scope: str, date_from: str, date_to: str,
    date_format: str, sort_by: str,
) -> dict[str, Any]:
    """Produz argumentos de busca sem alterar widgets nem parâmetros originais."""
    start = parse_user_date(date_from, date_format)
    end = parse_user_date(date_to, date_format)
    if start and end and start > end:
        raise ValueError("Data inicial não pode ser posterior à data final.")
    return {
        "category": category, "scan_id": scan_id,
        "name_contains": name.strip(), "extension": extension.strip(),
        "search_scope": scope,
        "date_from": start, "date_to": end, "sort_by": sort_by,
    }


def previous_page(current: int) -> int:
    """Volta uma página sem sair da primeira; valores inválidos não são aceitos."""
    if not isinstance(current, int) or isinstance(current, bool) or current < 1:
        raise ValueError("Página atual inválida.")
    return max(1, current - 1)


def next_page(current: int, total: int) -> int:
    """Avança somente se há outra página, preservando o estado da tela."""
    if (not isinstance(current, int) or isinstance(current, bool) or current < 1
            or not isinstance(total, int) or isinstance(total, bool) or total < 0):
        raise ValueError("Paginação inválida.")
    return current + 1 if current < total else current


def summary_report(result: dict[str, Any]) -> str:
    if result.get("scan_id") is None:
        return "Catálogo vazio: nenhuma catalogação encontrada."
    categories = result["by_category"]
    return (
        f"Inventário #{result['scan_id']} | Arquivos: {result['indexed_files']} | Mídias: {result['media_files']} "
        f"| Imagens: {categories.get('imagem', 0)} "
        f"| Vídeos: {categories.get('video', 0)} "
        f"| Áudios: {categories.get('audio', 0)} "
        f"| Espaço: {result['bytes_media']:,} bytes"
    )


def inventory_report(result: dict[str, Any]) -> str:
    info = result["summary"]
    categories = info["by_category"]
    return (
        f"Pasta: {result['root']} | Arquivos: {info['indexed_files']} | Mídias: {info['media_files']} "
        f"| Imagens: {categories.get('imagem', 0)} "
        f"| Vídeos: {categories.get('video', 0)} "
        f"| Áudios: {categories.get('audio', 0)} "
        f"| Erros: {len(result['errors'])}"
    )


def agent_report(result: dict[str, Any]) -> tuple[str, str]:
    """Retorna (resposta curta, relatório técnico), sem mudar o texto histórico."""
    answer = result.get("answer") or "(Resposta textual vazia)"
    tools = result.get("tools_used", [])
    details = json.dumps(tools, ensure_ascii=False, indent=2)
    session_info = (
        f"\n\nCATÁLOGO DE SESSÃO: {result.get('catalog_scanned_utc', 'sem horário')} UTC. "
        "Se a pasta mudou, clique em Atualizar análise da pasta."
        if result.get("temporary_catalog") else ""
    )
    full = (
        f"RESPOSTA DO AGENTE\n{answer}\n\n"
        f"FERRAMENTAS UTILIZADAS\n{details}"
        f"{session_info}\n\n"
        "Operações de movimentação: indisponíveis nesta versão."
    )
    return answer, full
