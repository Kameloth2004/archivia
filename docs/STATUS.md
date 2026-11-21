# ArchivIA — Estado e retomada

Atualizado em 2026-11-21.

## Ambiente

- Windows, Git Bash, Python 3.12, projeto: `D:/PROJETOS/archivia`.
- Repositório: `Kameloth2004/archivia`, branch `main`.
- Ollama local, RTX 3060 12 GB.
- Modelo utilizado no primeiro teste real: `qwen3:8b-q4_K_M`.

## Implementado

1. Inventário de imagens, vídeos e áudios por extensão e metadados.
2. Catálogo SQLite persistente em `data/catalogo.sqlite3`.
3. Consultas e resumo do último snapshot, sem revarrer mídias.
4. Planejador de movimentos **exclusivamente em simulação**, sem executor.
5. Adaptador local Ollama com allowlist de ferramentas: `resumo_catalogo` e `simular_movimentacao`.
6. Interface gráfica PySide6 inicial criada em `src/archivia/gui.py`; instalação opcional concluída e janela aberta no Windows em 2026-11-21.
7. Testes em `tests/`; dados temporários em `tests/.runtime/`; mocks identificados como `MOCK-ONLY`.

## Validação confirmada pelo usuário

- 19 testes executados no Windows: `OK (skipped=1)` — 18 aprovados e um ignorado por restrição de links simbólicos.
- Planejador manual: uma ação proposta para `foto_teste.jpg`; zero bloqueios; nenhum arquivo movido.
- **Primeira integração Ollama real aprovada em 2026-11-21.** Pergunta: "Quantas imagens existem no meu catálogo?" Modelo: `qwen3:8b-q4_K_M`. O agente chamou `resumo_catalogo`, obteve `scan_id=1`, `media_files=1`, `by_category.imagem=1` e respondeu "O catálogo contém 1 imagem.". A saída indicou `files_modified=false`.
- **Segunda integração real aprovada em 2026-11-21.** O Qwen3 chamou `simular_movimentacao`, categoria `imagem`, destino `tests/fixtures/manual/destino`, obteve `selected=1`, `blocked=0`, `mode=simulation`, `executable=false`, `files_modified=false`. Nenhum arquivo foi movido.
- Os testes comprovam integração por ferramentas, **não** reconhecimento visual, mecanismo de aprovação ou operações sobre arquivos.

**GUI: agente validado em 2026-11-21.** A pergunta pela interface retornou `O catálogo contém 1 imagem.`, com `tools_used` incluindo `resumo_catalogo`, `scan_id=1`, `imagem=1`, `files_modified=false`. Essa evidência comprova a rota GUI → Ollama → Python → SQLite → GUI.

## GUI Standard

Protótipo inicial: `archivia-gui`, instalado opcionalmente com `python -m pip install -e ".[gui]"`. **Usuário confirmou que dependências instalaram e a janela abriu normalmente em 2026-11-21**, com captura de tela. O botão **Atualizar resumo** foi testado e aprovado pelo usuário; a interação com o agente pela GUI foi aprovada: `resumo_catalogo` devolveu 1 imagem via Qwen3. A interface atual é explicitamente provisória: redesenhar futuramente para aparência moderna, melhor hierarquia visual, navegação intuitiva e fluxos claros. Ver [GUI.md](GUI.md).

## Próximo passo seguro

**Próxima validação, uma por vez:** com a GUI aberta, testar a ferramenta `simular_movimentacao` por linguagem natural, usando somente a pasta sintética `tests/fixtures/manual/destino`; confirmar que não há movimentação física. Ambos os botões de resumo e consulta ao agente foram aprovados. Não executar movimentações reais. Preservar motor independente da GUI/Ollama para as futuras edições Lite.

## Limitações e evolução

- O agente não lê conteúdos visuais, apenas metadados do SQLite.
- O planejador ainda carrega itens da categoria em memória; implementar paginação antes de escalonar.
- Próximas etapas: interface gráfica PySide6, paginação SQLite e análise visual local.
- **Três edições planejadas, sem implementação separada no momento:** Standard (prioritária), Lite sem IA e Lite + IA opcional. Consultar [EDITIONS.md](EDITIONS.md).
- Nenhum modelo recebe comandos para mover, apagar ou executar shell; não há executor.

## Referências

- [Arquitetura](ARCHITECTURE.md)
- [Contrato do agente](AGENT.md)
- [Edições e prioridades](EDITIONS.md)
- [Política de testes](../tests/README.md)
