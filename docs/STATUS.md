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
7. Seletor de pastas, prévia de inventário e tabela paginada adicionados à GUI. **Tabela catalogada validada no Windows por captura de tela:** `foto_teste.jpg`, categoria `imagem`, extensão `.jpg`, 15 bytes; página 1 de 1. Seletor nativo e prévia **validados no Windows por captura de tela**: pasta `D:/PROJETOS/archivia/tests/fixtures/manual`, 1 mídia, 1 imagem, 0 vídeos, 0 áudios e 0 erros.
8. Testes em `tests/`; dados temporários em `tests/.runtime/`; mocks identificados como `MOCK-ONLY`.

## Validação confirmada pelo usuário

- 19 testes executados no Windows: `OK (skipped=1)` — 18 aprovados e um ignorado por restrição de links simbólicos.
- Planejador manual: uma ação proposta para `foto_teste.jpg`; zero bloqueios; nenhum arquivo movido.
- **Primeira integração Ollama real aprovada em 2026-11-21.** Pergunta: "Quantas imagens existem no meu catálogo?" Modelo: `qwen3:8b-q4_K_M`. O agente chamou `resumo_catalogo`, obteve `scan_id=1`, `media_files=1`, `by_category.imagem=1` e respondeu "O catálogo contém 1 imagem.". A saída indicou `files_modified=false`.
- **Segunda integração real aprovada em 2026-11-21.** O Qwen3 chamou `simular_movimentacao`, categoria `imagem`, destino `tests/fixtures/manual/destino`, obteve `selected=1`, `blocked=0`, `mode=simulation`, `executable=false`, `files_modified=false`. Nenhum arquivo foi movido.
- Os testes comprovam integração por ferramentas, **não** reconhecimento visual, mecanismo de aprovação ou operações sobre arquivos.

**GUI: agente validado em 2026-11-21.** A pergunta pela interface retornou `O catálogo contém 1 imagem.`, com `tools_used` incluindo `resumo_catalogo`, `scan_id=1`, `imagem=1`, `files_modified=false`. Essa evidência comprova a rota GUI → Ollama → Python → SQLite → GUI.

**GUI: simulação validada em 2026-11-21.** Pela janela PySide6 o Qwen3 chamou `simular_movimentacao`, com `scan_id=1`, `foto_teste.jpg`, `selected=1`, `blocked=0`, `mode=simulation`, `executable=false`; nenhum arquivo foi movimentado. A resposta do modelo sugeriu aprovação, mas tal funcionalidade **não existe** ainda — corrigir orientação/UX para não induzir o usuário a acreditar que há executor.

## GUI Standard

Protótipo inicial: `archivia-gui`, instalado opcionalmente com `python -m pip install -e ".[gui]"`. **Usuário confirmou que dependências instalaram e a janela abriu normalmente em 2026-11-21**, com captura de tela. O botão **Atualizar resumo** foi testado e aprovado pelo usuário; a interação com o agente pela GUI foi aprovada: `resumo_catalogo` devolveu 1 imagem via Qwen3. A interface atual é explicitamente provisória: redesenhar futuramente para aparência moderna, melhor hierarquia visual, navegação intuitiva e fluxos claros. Ver [GUI.md](GUI.md).

## Atualização — tabela de prévia de inventário

- Novo `src/archivia/preview.py`: fatia dados do inventário em memória, filtra por categoria, sem SQLite nem modificação de mídia.
- GUI: adicionada tabela própria para o inventário recém-examinado, com 50 registros por página, filtro de imagens/vídeos/áudios e navegação Anterior/Próxima, independente da biblioteca catalogada.
- O inventário completo permanece em memória durante a sessão; trocar a pasta ou executar nova varredura substitui a prévia anterior. Para 19.636 arquivos, a tela cria apenas 50 linhas por vez. Ainda será necessário medir uso de RAM em bibliotecas maiores.
- Corrigido erro visual antigo no painel do agente após prévia bem-sucedida.
- Novos testes isolados em `tests/test_preview.py`. **Ainda não validados no Windows**; requer `git pull` e suíte completa.
- Não há gravação SQLite nem movimentação de arquivos neste fluxo.

## Inventário universal — nova implementação

- Inventário agora indexa todos os arquivos regulares, reconhecendo documento, planilha, apresentação, compactado, código e outro, além de imagem/vídeo/áudio.
- Preserva semântica histórica de `media_files` e `bytes_media`; adiciona `indexed_files` e `bytes_indexed`.
- GUI mostra filtros para novas categorias e a quantidade geral de arquivos. SQLite mantém schema e snapshots anteriores; novos snapshots recebem mais tipos de arquivos.
- ZIP, RAR e 7z continuam **sem inspeção interna**. Sem execução de movimentos ou exclusões.
- Testes atualizados para regras universais e compatibilidade. **Aguardando execução no Windows**.
- Ver contrato e limites em [INVENTORY.md](INVENTORY.md).

## Catalogação confirmada pela GUI — pendente de homologação

- Universal inventory validado pelo usuário: testes Bash e GUI aprovados, com categorias adicionais visíveis.
- Novo módulo `src/archivia/cataloging.py` valida a prévia por revarredura e somente depois grava novo snapshot SQLite.
- Novo botão **Salvar inventário no catálogo SQLite...**, habilitado após prévia sem erros, requer confirmação e grava apenas no SQLite.
- Previsão de segurança: origem não é modificada; mudança ou falha na revarredura bloqueia gravação; cada confirmação aceita gera snapshot histórico novo.
- Após sucesso, exige nova prévia para nova gravação; tabela catalogada é limpa até `Listar catálogo`.
- Testes de regressão em `tests/test_cataloging.py`.
- **Ainda não validado no Windows**; testar primeiro `tests/fixtures/manual`, não uma pasta de trabalho extensa.

## Histórico de inventários — atualização para homologação

- **Snapshot #2 validado visualmente pelo usuário:** origem `D:/IW8 CONSTRUMAQ`, **44.383 arquivos**, 19.636 mídias (19.511 imagens, 125 vídeos), 0 erros; resumo e listagem da biblioteca SQLite exibem os mesmos dados.
- Introduzido `list_catalog_scans()`, consulta somente leitura dos últimos 100 snapshots, retornando ID, origem, data e quantidade de arquivos.
- `query_catalog_page(scan_id=...)` agora permite ver um snapshot histórico sem alterar o padrão do último snapshot.
- Nova seleção **Histórico de snapshots** na GUI, com botão **Atualizar histórico**; selecionar snapshot muda a listagem de arquivos do catálogo.
- Dois testes adicionais verificam histórico, seleção, limites e ausência de gravação.
- **Ainda não validado no Windows:** executar testes e confirmar alternância #1 ↔ #2.
- O histórico do banco é preservado; não existe exclusão ou movimentação de arquivos nesse fluxo.

## Origens consolidadas — atualização para homologação

- Usuário confirmou **histórico de snapshots #1 e #2 funcional** na GUI.
- Novo `catalog_origins_summary()`: seleciona somente o snapshot de ID mais alto **por caminho de origem** e soma arquivos, bytes e categorias sem contar históricos repetidos.
- Novo painel na GUI **Origens catalogadas — último snapshot por pasta** com botão **Atualizar origens**, tabela de pastas, IDs de snapshots, quantidade de arquivos e mídias.
- CTE SQL faz consulta de leitura `mode=ro`; não varre pastas, não grava SQLite, não altera mídias.
- Advertência: uma pasta que está dentro de outra pode conter os mesmos arquivos; esta versão não remove sobreposições **entre origens distintas**. Caminhos alternativos para uma mesma pasta também não são normalizados.
- Testes sintéticos de origens repetidas, origens diferentes e catálogo ausente. Código **ainda precisa de homologação Windows**.

## Correção de regressão dos testes — 2026-11-21

- Interface **Origens catalogadas** homologada: 2 origens, 44.384 arquivos, 19.637 mídias.
- Execução no Windows: `Ran 34 tests`, `FAILED (failures=1, skipped=1)`.
- Falha identificada em `tests/test_preview.py::test_validation`: o teste tratava `outro` como categoria inválida, apesar de ela ter passado a ser suportada pelo inventário universal.
- Ajustada **somente a expectativa do teste**: `outro` retorna lista vazia em pasta de teste sem arquivos desconhecidos; `categoria_inexistente` deve gerar `ValueError`.
- Nenhuma mudança em regras de negócio, arquivos de mídia ou banco real. Correção publicada; **aguarda reexecução da suíte no Windows**.

## Busca no catálogo SQLite — implementação para homologação

- Busca por termo no caminho relativo (`name_contains`), extensão exata (`extension`) e categoria já existente, combináveis e com respeito ao snapshot selecionado.
- `query_catalog_page()` segue usando `LIMIT/OFFSET` e abrindo SQLite em `mode=ro`. Usa parâmetros SQL e trata `%` e `_` como caracteres literais na busca.
- GUI: campos **Nome/caminho**, **Extensão**, botão **Limpar busca**; Enter ou **Listar catálogo** executa a pesquisa. Paginação retorna somente 50 linhas.
- Dois testes sintéticos adicionais; **a atualização ainda precisa ser validada no Windows**.
- Ollama ainda não recebeu nova ferramenta de busca nesta etapa; primeiro validar o motor e a GUI.

## Ferramenta de busca Ollama — aguardando homologação

- Usuário confirmou busca por `backup` no snapshot #2 pela GUI, sem erros reportados no Bash.
- Adicionada à allowlist do agente a ferramenta `buscar_arquivos_catalogo`: nome/caminho, extensão, categoria, página, limite e `scan_id` opcional.
- Máximo 20 resultados por página, padrão 10; página limitada a 100. Os parâmetros são validados **antes** de consultar SQLite.
- Usa `query_catalog_page()` em modo somente leitura; nunca executa comandos, movimenta ou altera arquivos.
- Três novos testes de dispatcher e transporte Ollama mockado em `tests/test_agent.py`.
- **Ainda não executado com Qwen3 real nesta etapa**; validar testes e uma pergunta natural no painel.
- Contrato atualizado em [AGENT.md](AGENT.md).

## Interface em abas — correção aguardando homologação

- Captura do usuário confirmou problema de altura: agente Ollama inacessível pela janela única extensa.
- GUI reorganizada em **Visão geral, Inventário, Biblioteca e Agente IA** usando PySide6 QTabWidget.
- Janela inicial reduzida para 960×760 (mínimo 760×540), status mantido fora das abas.
- Nenhuma mudança no motor SQLite, função de busca do agente, catálogo ou autorização de movimentação.
- **Homologado pelo usuário:** GUI abriu corretamente com as quatro abas em 2026-11-21; o problema da janela única foi resolvido no teste visual. O fluxo da nova ferramenta de busca pelo Ollama continua pendente.
- Redesign moderno e intuitivo continua como etapa posterior, agora sobre estrutura modular.

## Busca Ollama real — homologada com observação

- Usuário aprovou a integração real na GUI: Qwen3 chamou `buscar_arquivos_catalogo` no snapshot #2 da pasta `D:/IW8 CONSTRUMAQ`; `filter_name=backup`, `page_size=5`, cinco exemplos, `count=2298`, `pages=460` para o filtro aplicado.
- **Observação:** o modelo acrescentou `filter_category=outro` sem solicitação expressa; 2.298 é total **da categoria outro**, não total geral de todas as categorias.
- Ajustado `SYSTEM_PROMPT` e descrição de ferramenta para omitir filtros não solicitados, explicitar total versus exemplos e descrever restrições realmente aplicadas. Mudança apenas nas instruções ao modelo, sem mudar o SQLite, GUI ou permissões.
- Ajuste depende do comportamento do modelo e **ainda precisa de validação com Qwen3 real**; não garante sozinho a omissão de filtros.

## Próximo passo seguro

**Próximo teste:** atualizar `main` e repetir busca por arquivos contendo `backup` sem restringir categoria. Conferir `filter_category=null` e distinção entre `count` total e cinco exemplos. A atualização não altera arquivos.

## Limitações e evolução

- O agente não lê conteúdos visuais, apenas metadados do SQLite.
- A GUI já usa consultas SQL paginadas; o planejador e o comando `consultar` ainda carregam itens da categoria em memória. Planejador deverá migrar para paginação antes de escalonar.
- Próximas etapas: interface gráfica PySide6, paginação SQLite e análise visual local.
- **Três edições planejadas, sem implementação separada no momento:** Standard (prioritária), Lite sem IA e Lite + IA opcional. Consultar [EDITIONS.md](EDITIONS.md).
- Nenhum modelo recebe comandos para mover, apagar ou executar shell; não há executor.

## Referências

- [Arquitetura](ARCHITECTURE.md)
- [Contrato do agente](AGENT.md)
- [Edições e prioridades](EDITIONS.md)
- [Inventário universal](INVENTORY.md)
- [Política de testes](../tests/README.md)
