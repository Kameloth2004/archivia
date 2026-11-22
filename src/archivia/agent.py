"""Ponte experimental Ollama -> ferramentas permitidas do ArchivIA.

A IA jamais executa código fornecido pelo modelo; somente nomes em allowlist.
Sem acesso a shell, criação de pastas, movimentação ou exclusão.
"""
from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .catalog import DEFAULT_DB, catalog_summary, query_catalog_page, store_inventory
from .inventory import CATEGORIES, inventory
from .planner import propose_moves, propose_date_moves, summarize_consolidation

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
SYSTEM_PROMPT = (
    "Você é o ArchivIA, bibliotecário digital local. Use SOMENTE as ferramentas "
    "fornecidas quando precisar consultar o catálogo ou simular organização. "
    "Nenhuma ferramenta move, apaga, renomeia ou cria arquivos. "
    "Nunca afirme que uma operação foi executada. "
    "O catálogo tem classificações apenas por extensão, não por conteúdo visual. "
    "Ao buscar arquivos, utilize buscar_arquivos_catalogo; ela consulta somente um snapshot, "
    "por padrão o mais recente, e retorna uma página limitada. "
    "Se o usuário pedir busca sem restringir categoria, extensão ou snapshot, "
    "NÃO invente essas restrições: omita os parâmetros não solicitados. "
    "Na resposta, para toda busca, informe o total de correspondências do campo count, "
    "a quantidade efetivamente exibida em files, o snapshot e os filtros que a ferramenta "
    "realmente aplicou (filter_name, filter_extension e filter_category). "
    "Deixe explícito que uma página de exemplos não esgota a pesquisa. "
    "Não afirme um total geral de todas as categorias se houver filtro de categoria. "
    "Não confunda resultados parciais com a biblioteca inteira. "
    "Para busca somente no nome do arquivo, use escopo=nome; para incluir pastas, use escopo=caminho. "
    "Para datas, utilize modificação de arquivo, não data de criação; filtros estão em UTC, AAAA-MM-DD. "
    "Ordene pela data quando solicitado; não confunda ordenar resultados com movimentar arquivos. "
    "Para simular distribuição física em pastas AAAA/MM, use simular_organizacao_por_data, "
    "somente quando o usuário pedir uma SIMULAÇÃO, fornecer categoria de mídia e caminho "
    "de destino-base já existente. Se faltar destino ou categoria, pergunte antes de simular. "
    "A simulação seleciona no máximo 50 arquivos, pode ser parcial e NUNCA executa ações. "
    "Relate total_matches, selected, blocked, truncated e o snapshot utilizado; "
    "Para simulação, se truncated=false, diga resultado COMPLETO para a categoria no snapshot. "
    "Somente diga PARCIAL se truncated=true; selected=total_matches não é parcial. "
    "não declare criação de pastas, movimentação ou autorização disponível. "
    "Na GUI, a pasta selecionada em Inventário fixa o snapshot da consulta. "
    "Para consolidar muitos arquivos em uma pasta única, use resumir_consolidacao "
    "se houver categoria de mídia e um destino existente informado pelo usuário. "
    "Esta ferramenta retorna apenas totais, nunca ações executáveis. "
    "Informe examined, proposed, blocked, pending, complete e total_matches. "
    "Nunca chame um resultado PARCIAL de completo. "
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
            "name": "resumir_consolidacao",
            "description": (
                "SIMULA consolidação da categoria imagem/video/audio numa única pasta "
                "existente informada pelo usuário. Examina até 10000 arquivos em lotes, "
                "identifica conflitos de nomes entre páginas e retorna somente totais. "
                "NÃO move, renomeia, cria nem apaga. Exige categoria e destino real."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "categoria": {"type": "string", "enum": ["imagem", "video", "audio"]},
                    "destino": {
                        "type": "string",
                        "description": "Pasta de destino já existente, explicitamente informada pelo usuário"
                    },
                    "limite": {
                        "type": "integer", "minimum": 1, "maximum": 10000,
                        "description": "Máximo de arquivos a examinar; padrão 10000"
                    },
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
                "o mais recente por padrão. Retorna no máximo 20 arquivos por página. "
                "NÃO aplique categoria ou extensão se o usuário não solicitar. "
                "escopo=nome busca somente nome-base, escopo=caminho inclui diretórios. "
                "Permite período de modificação e ordenação cronológica."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "nome": {"type": "string", "description": "Trecho literal do nome ou caminho"},
                    "extensao": {"type": "string", "description": "Exemplo: pdf, .jpg"},
                    "escopo": {
                        "type": "string", "enum": ["nome", "caminho"],
                        "description": "Use nome para buscar somente no nome-base; caminho inclui pastas. Padrão: caminho."
                    },
                    "data_inicial": {"type": "string", "description": "Data inicial de modificação UTC em AAAA-MM-DD"},
                    "data_final": {"type": "string", "description": "Data final de modificação UTC em AAAA-MM-DD"},
                    "ordenacao": {
                        "type": "string", "enum": ["nome", "recentes", "antigos"],
                        "description": "Ordenação da listagem, sem mover arquivos."
                    },
                    "categoria": {"type": "string", "enum": list(CATEGORIES),
                                  "description": "OPCIONAL: só informar quando o usuário limitar explicitamente a categoria"},
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
    {
        "type": "function",
        "function": {
            "name": "simular_organizacao_por_data",
            "description": (
                "SIMULA, sem escrita, destino AAAA/MM/nome.ext com base na data de modificação UTC. "
                "Exige categoria imagem/video/audio e destino-base já existente informado pelo usuário. "
                "Pode escolher scan_id. Nunca cria pastas, move, renomeia, apaga ou executa ações. "
                "Retorna até 50 propostas, incluindo conflitos e aviso de resultado parcial."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "categoria": {"type": "string", "enum": ["imagem", "video", "audio"]},
                    "destino": {
                        "type": "string",
                        "description": "Pasta de destino-base JÁ EXISTENTE, informada pelo usuário"
                    },
                    "scan_id": {
                        "type": "integer", "minimum": 1,
                        "description": "Opcional; se omitido usa último snapshot do catálogo"
                    },
                    "limite": {
                        "type": "integer", "minimum": 1, "maximum": 50,
                        "description": "Máximo 50 propostas por consulta; padrão 10"
                    },
                },
                "required": ["categoria", "destino"],
                "additionalProperties": False,
            },
        },
    },
]


def dispatch_tool(name: str, arguments: dict[str, Any], db_path: Path = DEFAULT_DB,
                  context_scan_id: int | None = None) -> dict[str, Any]:
    """Executa apenas ferramentas conhecidas, com validação independente do modelo."""
    if not isinstance(arguments, dict):
        raise ValueError("Argumentos da ferramenta devem ser um objeto JSON.")
    if context_scan_id is not None and (
        not isinstance(context_scan_id, int)
        or isinstance(context_scan_id, bool) or context_scan_id < 1
    ):
        raise ValueError("Snapshot de contexto inválido.")
    if context_scan_id is not None and "scan_id" in arguments:
        if arguments["scan_id"] != context_scan_id:
            raise ValueError("O agente não pode consultar outro snapshot fora da pasta selecionada.")
    if name == "resumo_catalogo":
        if arguments:
            raise ValueError("resumo_catalogo não aceita argumentos.")
        return catalog_summary(db_path, scan_id=context_scan_id)
    if name == "buscar_arquivos_catalogo":
        allowed = {"nome", "extensao", "categoria", "pagina", "limite", "scan_id",
                   "escopo", "data_inicial", "data_final", "ordenacao"}
        if set(arguments) - allowed:
            raise ValueError("Argumento não permitido na busca.")
        for key in ("nome", "extensao", "categoria", "escopo", "data_inicial", "data_final", "ordenacao"):
            if key in arguments and not isinstance(arguments[key], str):
                raise ValueError(f"{key} deve ser texto.")
        for key, maximum in (("pagina", 100), ("limite", 20), ("scan_id", None)):
            if key in arguments:
                value = arguments[key]
                if (not isinstance(value, int) or isinstance(value, bool)
                        or value < 1 or (maximum is not None and value > maximum)):
                    raise ValueError(f"{key} inválido.")
        scope = arguments.get("escopo", "caminho")
        if scope not in ("nome", "caminho"):
            raise ValueError("Escopo inválido.")
        order = arguments.get("ordenacao", "nome")
        if order not in ("nome", "recentes", "antigos"):
            raise ValueError("Ordenação inválida.")
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
            scan_id=context_scan_id if context_scan_id is not None else arguments.get("scan_id"),
            search_scope={"nome": "filename", "caminho": "path"}[scope],
            date_from=arguments.get("data_inicial"),
            date_to=arguments.get("data_final"),
            sort_by={"nome": "name", "recentes": "newest", "antigos": "oldest"}[order],
        )
    if name == "simular_organizacao_por_data":
        allowed = {"categoria", "destino", "scan_id", "limite"}
        if set(arguments) - allowed:
            raise ValueError("Argumento não permitido na simulação cronológica.")
        if not {"categoria", "destino"} <= set(arguments):
            raise ValueError("Categoria e destino-base são obrigatórios.")
        category = arguments["categoria"]
        destination = arguments["destino"]
        if not isinstance(category, str) or category not in ("imagem", "video", "audio"):
            raise ValueError("Categoria inválida para simulação cronológica.")
        if not isinstance(destination, str) or not destination.strip():
            raise ValueError("Destino-base deve ser um caminho informado e não vazio.")
        for key, max_value in (("limite", 50), ("scan_id", None)):
            if key in arguments:
                value = arguments[key]
                if (not isinstance(value, int) or isinstance(value, bool)
                        or value < 1 or (max_value is not None and value > max_value)):
                    raise ValueError(f"{key} inválido.")
        return propose_date_moves(
            destination=destination,
            category=category,
            db_path=db_path,
            limit=arguments.get("limite", 10),
            scan_id=context_scan_id if context_scan_id is not None else arguments.get("scan_id"),
        )
    if name == "resumir_consolidacao":
        if set(arguments) - {"categoria", "destino", "limite"}:
            raise ValueError("Argumento não permitido no resumo de consolidação.")
        if not {"categoria", "destino"} <= set(arguments):
            raise ValueError("Categoria e destino são obrigatórios.")
        if arguments["categoria"] not in ("imagem", "video", "audio"):
            raise ValueError("Categoria inválida para consolidação.")
        if not isinstance(arguments["destino"], str) or not arguments["destino"].strip():
            raise ValueError("Destino deve ser um caminho informado e não vazio.")
        if "limite" in arguments:
            value = arguments["limite"]
            if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 10000:
                raise ValueError("limite inválido.")
        return summarize_consolidation(
            destination=arguments["destino"],
            category=arguments["categoria"],
            db_path=db_path,
            scan_id=context_scan_id,
            max_candidates=arguments.get("limite", 10000),
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
            scan_id=context_scan_id,
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


def ask_agent(prompt: str, model: str, db_path: Path = DEFAULT_DB,
              context_scan_id: int | None = None) -> dict[str, Any]:
    """Uma solicitação, no máximo uma rodada de ferramentas, seguida da resposta final."""
    if not prompt.strip() or not model.strip():
        raise ValueError("Solicitação e modelo não podem estar vazios.")
    if context_scan_id is not None and (not isinstance(context_scan_id, int)
            or isinstance(context_scan_id, bool) or context_scan_id < 1):
        raise ValueError("Snapshot de contexto inválido.")
    instructions = SYSTEM_PROMPT
    if context_scan_id is not None:
        instructions += (" A interface selecionou a pasta do snapshot "
                         f"#{context_scan_id}. Use exclusivamente esse contexto; "
                         "não tente acessar outro snapshot.")
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": instructions},
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
                value = dispatch_tool(name, args, db_path, context_scan_id=context_scan_id)
            except (ValueError, OSError) as exc:
                value = {"error": str(exc)}
            # Registra argumentos efetivamente recebidos, não o texto narrado pelo
            # modelo. Essencial para diagnosticar tool calls malformadas.
            results.append({"tool": name, "arguments": args, "result": value})
            messages.append({
                "role": "tool", "tool_name": name,
                "content": json.dumps(value, ensure_ascii=False),
            })
        # Segunda chamada sem ferramentas: não cria ciclo de autonomia.
        message = _ollama_chat({"model": model, "messages": messages, "stream": False})
    return {"model": model, "answer": str(message.get("content") or ""),
            "tools_used": results, "files_modified": False}



class FolderCatalogSession:
    """Catálogo SQLite descartável reutilizado entre perguntas da mesma origem.

    O inventário representa o estado do instante de catalogação, NÃO uma
    verificação contínua do disco. Use refresh() após alterações externas.
    """

    def __init__(self, folder: str | Path) -> None:
        self.source = Path(folder).expanduser().absolute()
        if not self.source.is_dir() or self.source.is_symlink():
            raise ValueError("Selecione uma pasta de origem real e válida.")
        self._temporary: TemporaryDirectory | None = None
        self._db: Path | None = None
        self._scan_id: int | None = None
        self._scanned_utc: str | None = None

    @property
    def ready(self) -> bool:
        return self._temporary is not None and self._db is not None

    def refresh(self) -> None:
        """Substitui o catálogo após uma nova varredura sem deixar meio estado."""
        if not self.source.is_dir() or self.source.is_symlink():
            raise ValueError("Pasta de origem não está mais disponível.")
        temp = TemporaryDirectory(prefix="archivia-session-")
        try:
            db = Path(temp.name) / "catalogo.sqlite3"
            report = inventory(self.source)
            if report["errors"]:
                raise ValueError("Inventário com erros; a consulta foi cancelada.")
            scan = store_inventory(report, db)
            summary = catalog_summary(db, scan_id=scan["scan_id"])
        except BaseException:
            temp.cleanup()
            raise
        old = self._temporary
        self._temporary = temp
        self._db = db
        self._scan_id = scan["scan_id"]
        self._scanned_utc = summary["scanned_utc"]
        if old is not None:
            old.cleanup()

    def ask(self, prompt: str, model: str) -> dict[str, Any]:
        reused = self.ready
        if not reused:
            self.refresh()
        if not self.source.is_dir() or self.source.is_symlink():
            raise ValueError("Pasta de origem não está mais disponível.")
        result = ask_agent(prompt, model, self._db, context_scan_id=self._scan_id)
        result["temporary_catalog"] = True
        result["catalog_reused"] = reused
        result["source_root"] = str(self.source)
        result["catalog_scanned_utc"] = self._scanned_utc
        result["catalog_may_be_stale"] = True
        return result

    def close(self) -> None:
        temp = self._temporary
        self._temporary = None
        self._db = None
        self._scan_id = None
        self._scanned_utc = None
        if temp is not None:
            temp.cleanup()


def ask_agent_for_folder(prompt: str, model: str, folder: str | Path) -> dict[str, Any]:
    """Consulta uma pasta diretamente com catálogo descartável, sem salvar histórico.

    Não altera arquivos de origem. O banco e seus arquivos auxiliares vivem apenas
    durante esta solicitação; falha de inventário impede consulta parcial ao agente.
    """
    source = Path(folder).expanduser().absolute()
    if not source.is_dir():
        raise ValueError("Selecione uma pasta de origem válida.")
    with TemporaryDirectory(prefix="archivia-session-") as temp:
        db = Path(temp) / "catalogo.sqlite3"
        scan = store_inventory(inventory(source), db)
        result = ask_agent(prompt, model, db, context_scan_id=scan["scan_id"])
        result["temporary_catalog"] = True
        result["source_root"] = scan["root"]
        return result
