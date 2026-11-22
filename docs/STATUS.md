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

## Busca Ollama sem filtros implícitos — homologada em 2026-11-21

- Usuário solicitou busca de `backup` em **todas as categorias** com cinco exemplos.
- Qwen3 chamou `buscar_arquivos_catalogo` no snapshot #2 (`D:/IW8 CONSTRUMAQ`), com `filter_name=backup`, `filter_category=null`, `filter_extension=""`, `page_size=5`, `count=26970` e `pages=5394`.
- A resposta informou o total geral e cinco exemplos, todos `.tar.gz` pela ordenação, **sem filtro de categoria ou extensão**.
- Teste funcional aprovado: modelo respeitou os filtros solicitados, o limite de exemplos e a consulta somente leitura.
- Interpretação importante: busca por `relative_path` inclui termos em **nomes de diretórios**; arquivos dentro de `BACKUPS/` contam mesmo quando seu nome individual não inclui `backup`. Diferenciar futuramente pesquisa por nome-base e pesquisa por caminho.
- Essa validação não comprova identificação de conteúdo visual nem execução de arquivos.

## Busca por nome-base, caminho e data — implementação para homologação

- Por solicitação do usuário, a atualização inclui **busca pelo nome-base ou pelo caminho completo** e **filtro/ordenação pela data de modificação**, antes da validação da versão.
- SQL `query_catalog_page()`: novo `search_scope=filename|path`, intervalo inclusivo `date_from/date_to` em AAAA-MM-DD UTC e `sort_by=name|newest|oldest`; mantém paginação, categoria, extensão, snapshot e somente leitura.
- GUI Biblioteca: seletor Caminho completo/Somente nome; datas inicial/final; ordenação Nome/Mais recentes/Mais antigos; coluna **Modificado (UTC)**.
- Ollama `buscar_arquivos_catalogo`: `escopo=nome|caminho`, `data_inicial`, `data_final`, `ordenacao=nome|recentes|antigos`, com validação no dispatcher.
- Acrescentados 3 testes SQL e 2 testes de agente para nomes de pasta, intervalos, ordenação e valores inválidos. **Suíte homologada no Windows pelo usuário: `Ran 44 tests in 0.631s`, `OK (skipped=1)`**. A interface ainda precisa de validação visual.
- Atenção: a data é `modified_utc` do sistema de arquivos no momento do inventário, não data de captura EXIF, criação ou data do snapshot.
- **Organizar fisicamente em pastas por ano/mês é futuro**: exige planejador, simulação e autorização explícita. Esta etapa só organiza os resultados na tela, não toca em arquivos.

## Homologação da busca por nome — 2026-11-21

- Usuário confirmou que a pesquisa **Somente nome** na GUI está correta: termo `leo`, snapshot mais recente (#2), 14 arquivos encontrados.
- Ocorrências verificadas em nomes-base como `TableOfContents.php` (`leO`), `AddIndexableObjectIdAndTypeIndex.php`, `SierraLeone.js` e arquivos com `Óleo`.
- A busca é por **substring** e, para caracteres ASCII, sem distinção de maiúsculas/minúsculas; não exige limites de palavras.
- Esta aprovação valida a consulta por nome e a exibição da GUI; não implica homologação do filtro/ordenação cronológicos nem movimentação física.
- Próxima validação funcional: filtro de datas `AAAA-MM-DD` e ordenação **Mais recentes / Mais antigos** na aba Biblioteca.

## Configurações — preferência regional de data (aguardando homologação)

- Criada quinta aba **Configurações** para preferências que não precisam ocupar os painéis de trabalho.
- Primeiro ajuste: formato de data da interface — brasileiro `DD/MM/AAAA` (padrão inicial), internacional ISO 8601 `AAAA-MM-DD`, norte-americano `MM/DD/AAAA`.
- Nova rotina isolada `src/archivia/date_formats.py` valida entradas e converte para ISO antes de consultar SQLite. A tabela Biblioteca exibe `Modificado (UTC)` na preferência selecionada, mantendo hora e indicação UTC.
- Preferência persistida pelo Qt `QSettings` como INI no perfil do usuário, não no banco de dados nem no repositório. Ao trocar a preferência, campos válidos preenchidos são convertidos e datas da tabela já exibida são atualizadas sem nova busca.
- Testes sintéticos em `tests/test_date_formats.py` para Brasil, ISO, EUA, datas inválidas e UTC (3 novos testes).
- **Pendente de homologação no Windows:** confirmar mudança entre formatos, persistência ao reabrir a GUI e consulta por período usando `DD/MM/AAAA`.
- Os filtros e o banco continuam recebendo/armazenando datas ISO 8601; nada altera datas reais de arquivos ou snapshots.
- Preferências adicionais poderão ser incluídas nesta aba posteriormente.

## Máscara automática de datas — aguardando homologação

- Usuário confirmou funcionamento dos filtros com `01/01/2024` e `31/12/2024`, mas precisou digitar manualmente as barras.
- Aplicadas máscaras `QLineEdit.setInputMask()` nos dois campos de data da Biblioteca: Brasil/EUA `00/00/0000`, ISO `0000-00-00`; o usuário só digita números, Qt insere separadores.
- Mudança em Configurações converte datas preenchidas válidas e substitui a máscara automaticamente, sem alterar o SQLite. Campos vazios mascarados (`//` ou `--`) são aceitos como filtro desativado; incompletos continuam inválidos.
- Novos testes isolados em `tests/test_date_formats.py` verificam máscaras, campos vazios e incompletos (2 testes).
- **Pendente de homologação Windows:** executar suíte e digitar `01012024` e `31122024` sem separadores; testar também a seleção ISO/EUA.
- Não modifica metadados de arquivos, inventário ou snapshots.

## Planejamento de organização por ano/mês — simulação em homologação

- Preferência de formatos e máscara automática confirmadas pelo usuário na GUI Windows.
- Adicionado `propose_date_moves()` em `src/archivia/planner.py` para propor `AAAA/MM/nome.ext` pela data de modificação UTC.
- Somente categorias `imagem/video/audio`, último snapshot global por padrão ou `scan_id` explícito. Destino-base **já existente**, sem links simbólicos.
- A consulta SQL é paginada: no máximo 100 arquivos por plano, sem carregar dezenas de milhares em memória.
- Verifica symlinks, colisões, destinos existentes, tamanho e modificação da origem; marca ações bloqueadas ou propostas. **Não cria subpastas e não move arquivos.**
- Três testes novos em `tests/test_planner.py` com fixtures sintéticas, sem escrita em mídias pessoais.
- **Motor aprovado na suíte de testes pelo usuário no Windows.** Interface de prévia adicionada posteriormente e ainda pendente de homologação visual.

## Organização cronológica na interface — aguardando homologação

- Criada aba **Organização** entre Biblioteca e Agente IA, separada da busca e do inventário.
- Permite escolher **destino-base já existente**, categoria `imagem/video/audio` e snapshot específico após clicar **Atualizar histórico**.
- Botão **Simular organização — sem alterações** chama `propose_date_moves()` em thread e mostra até **50** propostas `AAAA/MM/nome.ext` na tabela com situação, bloqueios e indicação de subpastas futuras.
- O motor continua `executable=false`, não cria diretórios, não move, não renomeia, não apaga arquivos e não grava alterações no SQLite. Não há botão de aprovação ou execução.
- O resumo informa quantidade selecionada, total da categoria e se a amostra é parcial. A consulta considera apenas um snapshot por vez.
- **Aguardando confirmação na GUI Windows**. Testar preferencialmente com snapshot de fixtures e um destino-base descartável já existente.

## Simulação cronológica na GUI — homologada visualmente

- Captura do usuário confirmou aba **Organização** funcional: snapshot #1, origem `D:/PROJETOS/archivia/tests/fixtures/manual`, categoria imagem.
- `foto_teste.jpg` apresentou situação `proposto`, zero bloqueios e destino sugerido `D:/IW8 CONSTRUMAQ/2026/11/foto_teste.jpg` com indicação **Subpasta futura**.
- Interface exibiu `1 examinados de 1`, `Categoria completa` e **SIMULAÇÃO: nenhuma operação de escrita**.
- **Atenção de segurança:** o destino-base escolhido foi uma pasta de trabalho real (`D:/IW8 CONSTRUMAQ`). Embora a operação atual seja estritamente não executável, testes futuros envolvendo qualquer criação/movimento devem usar apenas pastas descartáveis em `tests/`.
- Evidência confirma cálculo do plano e apresentação de prévia; não comprova execução de arquivos nem existência de subpastas no destino. O motor não contém operações de escrita nesse fluxo.
- Próxima evolução possível: ampliar parâmetros de planejamento/validação e somente depois avaliar exposição da simulação ao Ollama, sem introduzir executor.

## Agente Ollama: simulação cronológica — código para homologação

- Integrada `simular_organizacao_por_data` na allowlist de `src/archivia/agent.py`. Reutiliza `propose_date_moves()`; não adiciona executor, criação, exclusão nem movimentação.
- Parâmetros: `categoria` (imagem, video, audio) e `destino` existentes obrigatórios; `scan_id` opcional, `limite` de 1 a 50 (padrão 10), rejeição de argumentos desconhecidos e tipos inválidos.
- O prompt proíbe afirmar execução e orienta a solicitar categoria e destino explícitos se ausentes; retorno de ferramenta contém `mode=simulation`, `executable=false`, `truncated`, `blocked`.
- 3 testes novos em `tests/test_agent.py`, incluindo modelo Ollama **MOCK-ONLY**, destino sintético, validação de argumentos e confirmação de ausência de subpastas criadas.
- **Não homologado com Qwen3 real ainda**. Primeiro rodar suíte Windows e testar em pasta-base descartável.
- Histórico/configuração da GUI **não** é compartilhado automaticamente com o agente.

## Integração real Qwen3 → planejador cronológico — homologada

- O usuário testou com Qwen3 a ferramenta `simular_organizacao_por_data` em snapshot #1, categoria imagem, destino-base `D:/PROJETOS/archivia/tests/fixtures/manual`.
- Resultado estruturado: `operation=organize_by_modified_date`, `mode=simulation`, `executable=false`, `requires_explicit_approval=true`, `scan_id=1`, `selected=1`, `total_matches=1`, `blocked=0`, `truncated=false`.
- Proposta: `foto_teste.jpg` → `2026/11/foto_teste.jpg` dentro da pasta-base de teste; `directory_would_need_creation=true` apenas sinaliza futuro diretório, sem criá-lo.
- Integração com ferramenta real **homologada**; o plano não possui executor e não há autorização de movimentação.
- Ajuste de precisão: a resposta textual do Qwen3 afirmou incorretamente que o resultado era parcial apesar de `truncated=false`. Reforçado no prompt que `truncated=false` significa que a categoria selecionada foi completamente representada no plano, não resultado parcial. **A nova instrução ainda não foi revalidada com Qwen3 real.**

## Diagnóstico de conflitos e duplicatas potenciais — aguardando homologação

- Acrescentado à **simulação cronológica** um diagnóstico por amostra: `possible_duplicate_by_metadata` assinala arquivos do mesmo nome-base (casefold) e mesmo tamanho **dentro da página selecionada**, sem abrir ou hashear conteúdos. **É suspeita, não duplicata confirmada**.
- `name_collisions` contabiliza ações bloqueadas por destino já existente ou conflito de nome dentro do plano. `potential_duplicate_items` conta itens suspeitos; ambos abrangem apenas a página do plano, não o catálogo completo.
- Quando um nome de destino colide, o planejador oferece `alternative_name_suggestion` (exemplo `foto__2.jpg`) **somente para visualização**. O status original continua `bloqueado` e a sugestão não é reservada nem executada.
- A aba Organização apresenta novas colunas **Possível duplicata?** e **Nome alternativo sugerido**, além dos contadores.
- Dois novos testes sintéticos verificam suspeitas com conteúdos deliberadamente diferentes, conflitos, alternativas e ausência de gravação.
- **Ainda não homologado no Windows**. Ainda não existe detecção real por hash nem escolha de política de conflitos para execução.

## Legibilidade da aba Organização — revisão para homologação

- Captura do usuário confirmou truncamento dos títulos e excesso de colunas da tabela de simulação.
- `src/archivia/gui.py` reorganizado em **1. Parâmetros da simulação**, **2. Resumo do plano** e **3. Arquivos e destinos propostos**.
- Resumo apresenta Examinados, Bloqueados, Colisões e Suspeitas em indicadores separados. A tabela usa 4 colunas principais; dados secundários são apresentados no painel de detalhe ao selecionar uma linha, incluindo possíveis duplicatas, nome alternativo, caminho completo e motivos.
- Ajustados tooltip, seleção por linha, larguras e linhas alternadas para melhorar leitura em janelas comuns. Interface ainda em homologação; não é redesign final.
- **Nenhuma mudança em `planner.py`, `agent.py` ou `catalog.py` nesta etapa.** Motor, permissões, snapshot e simulações permanecem inalterados.
- **Aguardando teste visual no Windows.**

## Aba Organização — novo layout validado visualmente

- Usuário apresentou captura da GUI Windows com as três seções (**Parâmetros**, **Resumo**, **Arquivos e destinos propostos**) legíveis.
- Snapshot #1 da pasta sintética; destino-base `D:/PROJETOS/archivia/tests`; categoria imagens. Simulação de `foto_teste.jpg` → `D:/PROJETOS/archivia/tests/2026/11/foto_teste.jpg`.
- Indicadores exibidos: 1 examinado, 0 bloqueios, 0 colisões, 0 suspeitas; categoria completa.
- A tabela de quatro colunas e o painel inferior de detalhes exibiram os campos sem truncar cabeçalhos, resolvendo o problema visual relatado.
- Status na interface: **Simulação concluída; nenhum arquivo modificado**. Não há mecanismo de execução ou movimentação.
- Esta aprovação é visual/funcional da prévia, não constitui validação de detecção por hash nem de operação real de arquivos.

## Verificação SHA-256 de duplicatas — implementação em homologação

- Criados **8 arquivos sintéticos** em `tests/fixtures/sha256_demo/` (além do README), com cenários criativos: nome igual/conteúdo igual; mesmo conteúdo/nomes diferentes; nome e tamanho iguais mas bytes diferentes; e dois arquivos vazios.
- Novo `src/archivia/duplicates.py`: `verify_duplicate_hashes()` consulta **um snapshot por vez** via `query_catalog_page()` e agrupa por tamanho antes de calcular SHA-256 em blocos. Só lê conteúdo quando há pelo menos dois candidatos do mesmo tamanho na amostra.
- Limites rígidos: **até 100 itens** (GUI usa 50), **16 MiB por arquivo** e **64 MiB de orçamento total de leitura** (reservado antes de cada tentativa, mesmo que a leitura falhe). Links simbólicos/junctions, arquivos ausentes/alterados e arquivos acima do limite não são declarados iguais; motivo de cada exclusão é exibido.
- A igualdade de SHA-256 confirma conteúdo idêntico entre os itens **efetivamente processados**; nenhuma conclusão de unicidade pode ser tirada sobre arquivos omitidos, não verificados ou sobre o catálogo inteiro.
- Nova subaba **Organização → Duplicatas (SHA-256)**: categoria e snapshot próprios, botão de verificação somente leitura, tabela agrupada, hashes completos em dicas e painel inferior, totais de processados/ignorados.
- Foram adicionados **5 testes** em `tests/test_duplicates.py`: grupos iguais reais, falsos positivos, arquivos vazios, limites, alterações/remoções e nenhuma escrita nas mídias.
- Correção preventiva: em `planner.py` (planejador legado `propose_moves`), removidos campos que referenciavam variáveis não inicializadas; sem mudança nas ações planejadas.
- **Aguardando homologação da suíte Windows e teste visual**. Nenhum botão de apagar, mover ou executar está disponível; não foi adicionada ferramenta nova ao Ollama.

## SHA-256 — suíte automatizada homologada

- Usuário confirmou a aprovação dos **62 testes** após a implementação dos cenários `tests/fixtures/sha256_demo` e do verificador SHA-256.
- A aprovação cobre os testes automatizados; **a subaba Duplicatas (SHA-256) ainda requer homologação visual no Windows**.
- Próximo teste: catalogar explicitamente somente a pasta sintética `tests/fixtures/sha256_demo` na aba Inventário; em Organização → Duplicatas (SHA-256), selecionar o snapshot recém-criado e categoria Imagens. Esperados **2 grupos com 5 arquivos de conteúdo idêntico na amostra**.
- Não utilizar pastas reais nem eliminar, mover ou renomear arquivos durante a homologação.

## SHA-256 — homologação visual concluída

- Usuário apresentou captura da subaba **Organização → Duplicatas (SHA-256)** em execução local no Windows.
- Snapshot **#3**, origem sintética `D:/PROJETOS/archivia/tests/fixtures/sha256_demo`, categoria Imagens.
- Resultado confirmado: **8 de 8 arquivos**, **8 hashes calculados**, **2 grupos SHA-256**, **5 arquivos com conteúdo idêntico na amostra**, **0 ignorados** e cobertura completa da categoria nesse snapshot.
- Grupo 1: `A/foto_igual.jpg`, `B/alias_nome_diferente.jpg`, `B/foto_igual.jpg`. Grupo 2: `A/vazio.jpg`, `B/vazio_copia.jpg`.
- Os demais casos preparados com nome/tamanho coincidentes, mas bytes diferentes, não foram confirmados como duplicatas.
- Status apresentado: **SHA-256 consultado em somente leitura; nada foi modificado**.
- Teste comprova a classificação na fixture e a apresentação na GUI, **não** uma varredura completa de duplicatas nos discos reais.
- Próxima evolução recomendada: paginação e análise ampliada de candidatos, preservando limites de I/O e sem habilitar operações de exclusão ou movimentação.

## SHA-256 por lotes e progresso — versão aguardando homologação

- `verify_duplicate_hashes()` ampliado para **até 1.000 arquivos por execução**, lendo páginas SQLite de 100 registros do mesmo snapshot. O agrupamento por tamanho considera metadados de todas as páginas da **amostra selecionada**, identificando pares distribuídos entre páginas diferentes.
- **Limites independentes:** até 16 MiB por arquivo e orçamento de 256 MiB por execução (configuráveis para valores inferiores). Valores padrão: 50 arquivos, 16 MiB e 64 MiB. O orçamento é reservado antes da tentativa de leitura, incluindo falhas.
- `progress` opcional recebe fase `catalog`/`hash`/`done`, processados e total. A GUI recebe atualizações via signal Qt, mostrando barra de progresso sem travar a janela.
- Na subaba **Organização → Duplicatas (SHA-256)**, novos controles numéricos para quantidade de arquivos, tamanho por arquivo e orçamento de leitura; mostra o número de páginas SQLite percorridas e conserva agrupamento/ignorados.
- Três testes novos cobrem pares iguais em páginas diferentes, amostra limitada que não comprova unicidade, callback e validação de limites.
- Os hashes só são calculados para arquivos de mesmo tamanho na **amostra**. A operação continua read-only, sem escrita de mídias, alteração SQLite ou exclusão. Não é varredura exaustiva dos 44 mil arquivos.
- **Ainda não validado no Windows** nesta revisão. Suíte esperada: 65 testes, com um possivelmente ignorado.

## SHA-256 paginado — homologação visual da GUI

- Usuário enviou captura da aba **Organização → Duplicatas (SHA-256)** no Windows com snapshot #3 (`tests/fixtures/sha256_demo`), categoria Imagens e limite ajustado para **100 arquivos**.
- Barra de progresso concluída, resultados **8 de 8 arquivos**, **8 hashes calculados**, **2 grupos confirmados**, **5 arquivos com conteúdo idêntico**, **0 ignorados**, **1 lote SQL**; status **somente leitura**, sem alteração de arquivos.
- Interface e opções de limites/progresso aprovadas na amostra sintética. Como ela possui apenas 8 arquivos, a captura **não** demonstra processamento de múltiplas páginas; essa situação é coberta por testes automatizados e permanece sem homologação visual específica no Windows.
- Próxima evolução recomendada: teste sintético com mais de 100 arquivos em pastas de teste, comparação entre páginas, orçamento de leitura e progresso. Não habilitar movimentação nem exclusão.

## Cenário manual SHA-256 com 134 arquivos — aguardando homologação

- Adicionado gerador seguro **`tests/generate_sha256_paged_demo.py`**, sem alteração de código de produção, para criar **134 arquivos sintéticos** em `tests/fixtures/manual/sha256_paginado` (ignorado pelo Git). Não substitui arquivo existente, recusa pasta preenchida, destinos fora de `tests/`, symlinks e junctions Windows.
- Cenário desenhado para SHA-256 entre duas páginas SQL de 100 registros: **3 grupos confirmados, 7 arquivos idênticos**, com 125 arquivos diferentes como controle de falsos positivos e par de mesmo nome/tamanho mas conteúdo diferente.
- **3 testes automatizados novos** em `tests/test_sha256_paged_fixture.py`: verificação de 134 itens e duas páginas; amostra parcial de 100; proteção contra sobrescrita e execução fora de `tests/`.
- Não é necessária atualização de motor ou interface: usam a verificação SHA-256 paginada já aprovada na GUI.
- **Pendente validação local:** rodar `python -m unittest discover -s tests -v` (expectativa de **68 testes**, com 1 possível skip) e depois `python tests/generate_sha256_paged_demo.py`; catalogar a pasta sintética manualmente na aba Inventário; na subaba Duplicatas usar o novo snapshot, categoria Imagens e limite **200**.
- O gerador e os testes são **TEST-ONLY**. Nenhum mecanismo de exclusão ou movimentação foi acrescentado.

## Cenário SHA-256 multipágina — suíte e gerador homologados

- Usuário confirmou no Windows: `Ran 68 tests in 2.970s`, `OK (skipped=1)` — 67 aprovados, 1 ignorado, zero falhas.
- Executado `python tests/generate_sha256_paged_demo.py` com sucesso; saída confirmou criação de **134 arquivos TEST-ONLY** em `D:/PROJETOS/archivia/tests/fixtures/manual/sha256_paginado`.
- Cenário esperado: 3 grupos SHA-256 com 3 + 2 + 2 arquivos idênticos. Para validação na GUI, usar limite de 200 arquivos, total de 134 e **2 páginas SQL**.
- **Próxima homologação ainda pendente:** catalogar explicitamente a pasta sintética no Inventário, salvar novo snapshot e executar SHA-256 no snapshot criado. Nenhuma operação de movimentação ou exclusão permitida.

## Próximo passo seguro

**Suíte de 68 testes e criação do cenário de 134 arquivos confirmadas pelo usuário.** Próximo passo: catalogar a pasta sintética pelo Inventário, confirmar novo snapshot; então, na subaba Duplicatas, selecionar o snapshot e limite 200 e verificar 134 arquivos, 2 lotes SQL, 3 grupos SHA-256 e 7 arquivos iguais. Nenhuma movimentação ou exclusão habilitada.

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
