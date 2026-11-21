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

from .catalog import DEFAULT_DB, catalog_summary
from .planner import propose_moves

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
SYSTEM_PROMPT = (
    "Você é o ArchivIA, bibliotecário digital local. Use SOMENTE as ferramentas "
    "fornecidas quando precisar consultar o catálogo ou simular organização. "
    "Nenhuma ferramenta move, apaga, renomeia ou cria arquivos. "
    "Nunca afirme que uma operação foi executada. "
    "O catálogo tem classificações apenas por extensão, não por conteúdo visual. "
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
]


def dispatch_tool(name: str, arguments: dict[str, Any], db_path: Path = DEFAULT_DB) -> dict[str, Any]:
    """Executa apenas ferramentas conhecidas, com validação independente do modelo."""
    if not isinstance(arguments, dict):
        raise ValueError("Argumentos da ferramenta devem ser um objeto JSON.")
    if name == "resumo_catalogo":
        if arguments:
            raise ValueError("resumo_catalogo não aceita argumentos.")
        return catalog_summary(db_path)
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
