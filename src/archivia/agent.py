"""Ponte experimental Ollama -> ferramentas permitidas do ArchivIA.

A IA jamais executa código fornecido pelo modelo; somente nomes em allowlist.
Sem acesso a shell, criação de pastas, movimentação ou exclusão.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .catalog import DEFAULT_DB, catalog_summary, query_catalog_page
from .inventory import CATEGORIES
from .planner import propose_moves

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
SYSTEM_PROMPT = (
    "Você é o ArchivIA, bibliotecário digital local. Use SOMENTE as ferramentas "
    "fornecidas quando precisar consultar o catálogo ou simular organização. "
    "Nenhuma ferramenta move, apaga, renomeia ou cria arquivos. "
    "Nunca afirme que uma operação foi executada. "
    "O catálogo tem classificações apenas por extensão, não por conteúdo visual. "
    "Ao buscar arquivos, utilize buscar_arquivos_catalogo; ela consulta somente um snapshot, "
    "por padrão o mais recente, e retorna uma página limitada. "
    "Não confunda resultados parciais com a biblioteca inteira. "
    "A seleção de histórico feita na GUI não é compartilhada automaticamente com o agente. "
    "Responda de forma curta e clara em português."
)

TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "resumo_catalogo",
            "description": "Retorna estatísticas do último inventário SQLite, sem alterar mídias.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "simular_movimentacao",
            "description": "Gera apenas proposta de movimentação por categoria; NÃO move arquivos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "categoria": {"type": "string", "enum": ["imagem", "video", "audio"]},
                    "destino": {"type": "string", "description": "Pasta de destino existente"},
                    "limite": {"type": "integer", "minimum": 1, "maximum": 100},
                },
                "required": ["categoria", "destino"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_arquivos_catalogo",
            "description": (
                "Busca arquivos pelo nome/caminho relativo e/ou extensão/categoria no "
                "SQLite, sem acessar os arquivos físicos. Consulta somente um snapshot, "
                "o mais recente por padrão. Retorna no máximo 20 arquivos por página."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "nome": {"type": "string", "description": "Trecho literal do nome ou caminho"},
                    "extensao": {"type": "string", "description": "Exemplo: pdf, .jpg"},
                    "categoria": {"type": "string", "enum": list(CATEGORIES)},
                    "pagina": {"type": "integer", "minimum": 1, "maximum": 100},
                    "limite": {"type": "integer", "minimum": 1, "maximum": 20},
                    "scan_id": {
                        "type": "integer", "minimum": 1,
                        "description": "Opcional; sem ID usa o snapshot mais recente"
                    },
                },
                "additionalProperties": False,
            },
        },
    },
]


def dispatch_tool(name: str, arguments: dict[str, Any], db_path: Path = DEFAULT_DB) -> dict[str, Any]:
    """Executa apenas ferramentas conhecidas, com validação independente do modelo."""
    if not isinstance(arguments, dict):
        raise ValueError("Argumentos da ferramenta devem ser um objeto JSON.")
    if name == "resumo_catalogo":
        if arguments:
            raise ValueError("resumo_catalogo não aceita argumentos.")
        return catalog_summary(db_path)
    if name == "buscar_arquivos_catalogo":
        allowed = {"nome", "extensao", "categoria", "pagina", "limite", "scan_id"}
        if set(arguments) - allowed:
            raise ValueError("Argumento não permitido na busca.")
        for key in ("nome", "extensao", "categoria"):
            if key in arguments and not isinstance(arguments[key], str):
                raise ValueError(f"{key} deve ser texto.")
        for key, maximum in (("pagina", 100), ("limite", 20), ("scan_id", None)):
            if key in arguments:
                value = arguments[key]
                if (not isinstance(value, int) or isinstance(value, bool)
                        or value < 1 or (maximum is not None and value > maximum)):
                    raise ValueError(f"{key} inválido.")
        category = arguments.get("categoria")
        if category is not None and category not in CATEGORIES:
            raise ValueError("Categoria desconhecida.")
        return query_catalog_page(
            db_path=db_path,
            name_contains=arguments.get("nome"),
            extension=arguments.get("extensao"),
            category=category,
            page=arguments.get("pagina", 1),
            page_size=arguments.get("limite", 10),
            scan_id=arguments.get("scan_id"),
        )
    if name == "simular_movimentacao":
        if set(arguments) - {"categoria", "destino", "limite"}:
            raise ValueError("Argumento não permitido.")
        if not {"categoria", "destino"} <= set(arguments):
            raise ValueError("Categoria e destino são obrigatórios.")
        if not isinstance(arguments["categoria"], str) or not isinstance(arguments["destino"], str):
            raise ValueError("Categoria e destino devem ser textos.")
        return propose_moves(
            arguments["destino"], arguments["categoria"], db_path=db_path,
            limit=arguments.get("limite", 100),
        )
    raise ValueError("Ferramenta não autorizada.")


def _ollama_chat(payload: dict[str, Any], timeout: float = 120) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(
        OLLAMA_URL, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            result = json.loads(response.read(5_000_000).decode("utf-8"))
    except (URLError, HTTPError, TimeoutError) as exc:
        raise ValueError(f"Falha na conexão local com Ollama: {exc}") from exc
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("Resposta inválida do Ollama.") from exc
    if not isinstance(result, dict) or not isinstance(result.get("message"), dict):
        raise ValueError("Resposta incompleta do Ollama.")
    return result["message"]


def ask_agent(prompt: str, model: str, db_path: Path = DEFAULT_DB) -> dict[str, Any]:
    """Uma solicitação, no máximo uma rodada de ferramentas, seguida da resposta final."""
    if not prompt.strip() or not model.strip():
        raise ValueError("Solicitação e modelo não podem estar vazios.")
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    message = _ollama_chat({
        "model": model, "messages": messages, "tools": TOOLS, "stream": False,
    })
    calls = message.get("tool_calls") or []
    if not isinstance(calls, list) or len(calls) > 3:
        raise ValueError("Quantidade de chamadas de ferramentas inválida.")
    results: list[dict[str, Any]] = []
    if calls:
        messages.append(message)
        for call in calls:
            func = call.get("function") if isinstance(call, dict) else None
            if not isinstance(func, dict):
                raise ValueError("Chamada de ferramenta malformada.")
            name = func.get("name")
            args = func.get("arguments")
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError as exc:
                    raise ValueError("Argumentos JSON inválidos.") from exc
            if not isinstance(name, str):
                raise ValueError("Nome de ferramenta inválido.")
            try:
                value = dispatch_tool(name, args, db_path)
            except (ValueError, OSError) as exc:
                value = {"error": str(exc)}
            results.append({"tool": name, "result": value})
            messages.append({
                "role": "tool", "tool_name": name,
                "content": json.dumps(value, ensure_ascii=False),
            })
        # Segunda chamada sem ferramentas: não cria ciclo de autonomia.
        message = _ollama_chat({"model": model, "messages": messages, "stream": False})
    return {"model": model, "answer": str(message.get("content") or ""),
            "tools_used": results, "files_modified": False}
