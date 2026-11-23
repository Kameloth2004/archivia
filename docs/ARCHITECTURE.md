# ArchivIA — Arquitetura e contrato de segurança

## Objetivo
Aplicativo desktop local para inventariar, catalogar, analisar e futuramente organizar mídias. O motor Python deve ser independente de UI e de modelo de IA. Diretório local conhecido: `D:/PROJETOS/archivia`.

## Componentes
- `src/archivia/inventory.py`: inventário universal por extensão (inclusive tipos desconhecidos), sem abrir conteúdo, ZIPs ou seguir symlinks. Ver [INVENTORY.md](INVENTORY.md).
- `src/archivia/catalog.py`: snapshots SQLite em `data/catalogo.sqlite3`, consultas de leitura, resumo e `query_catalog_page()` via SQL `LIMIT/OFFSET` sem carregar todos os itens.
- `src/archivia/planner.py`: **somente simulação** de movimento, sem operações de escrita em mídias.
- `src/archivia/cli.py`: interface transitória de testes/uso, não contém regras de negócio.
- `tests/`: testes automatizados, fixtures e mocks. Nunca incorporar mocks ao motor.
- `src/archivia/agent.py`: adaptador experimental Ollama (somente ferramentas de resumo e simulação). Ver [AGENT.md](AGENT.md).\n- Futuros adaptadores: modelo visual, UI desktop PySide6, embeddings visuais, executor auditável.

## Fluxo desejado
Usuário -> interface -> agente Ollama -> ferramentas do motor -> SQLite/metadados -> plano validado -> prévia -> aprovação explícita -> executor futuro.

O modelo retorna **intenções estruturadas**, não Python, shell, PowerShell ou SQL arbitrário. Nenhuma sugestão de IA concede privilégios ao sistema de arquivos. Ferramentas determinísticas validam origens, caminhos, mudanças posteriores ao inventário e conflitos.

## Contrato do planejador v1
`python -m archivia planejar --categoria imagem --destino "D:/PROJETOS/archivia/tests/fixtures/manual/destino"`

- Trabalha somente com o **último snapshot** SQLite, independente da origem.
- Filtra uma categoria: `imagem`, `video`, `audio`.
- Destino deve existir como diretório; nunca o cria.
- Monta proposta sem executar ou gravar arquivo de plano.
- Campos: `schema_version`, `operation=move`, `mode=simulation`, `executable=false`, `requires_explicit_approval=true`, `scan_id`, `root`, `destination`, `category`, `generated_utc`, `selected`, `total_matches`, `truncated`, `blocked`, `actions`.
- Ações são `proposto` ou `bloqueado`; proposto **não significa autorização**.
- Verifica existência da origem, tamanho e tempo de modificação catalogados, links simbólicos, colisão com arquivo existente e conflito entre destinos previstos.
- Limite máximo de 100 itens por plano. **Agora usa `query_catalog_page`**, consultando somente a primeira página da categoria, sem carregar todo o catálogo em RAM. Aceita `scan_id` opcional para selecionar o snapshot. Uma página é apenas prévia: **colisões de destino entre páginas ainda não são verificadas**, logo o resultado parcial não é plano completo nem autorização de execução.

## Consolidação global — primeira implementação de resumo (sem execução)

**Escopo:** `summarize_consolidation(destination, category, db_path, scan_id=None, max_candidates=10000)` em `planner.py` percorre até 10.000 candidatos por lotes de até 100 arquivos, com origem fixa, e devolve **apenas estatísticas**. A função antiga `propose_moves()` continua intacta como prévia de até 100 ações. Não modifica mídias, não grava plano no disco e **ainda não está disponível como ferramenta do agente ou botão na GUI**.

### Requisitos de entrada e de contexto

- **Origem:** o `scan_id` da pasta selecionada na GUI, não o último snapshot global por acidente. Fixar um único snapshot durante a análise. Pasta e destino devem ser explicitamente escolhidos ou confirmados pelo usuário, sem decisões implícitas do modelo.
- **Categoria:** filtro atual por extensão (`imagem`, `video`, `audio`) como primeira etapa, expandindo para outras categorias **somente quando o produto solicitar**. Não alegar que o conteúdo visual ou semântico foi analisado.
- **Destino:** diretório existente, validado como pasta real. Não criar pastas na etapa de planejamento. Se o destino estiver dentro da origem, a catalogação prévia pode já conter seus arquivos; casos de `mesmo_caminho` e reentrada precisam ser detectados antes de um executor futuro.
- **Saída:** reutilizar o contrato de simulação existente (`scan_id`, `root`, `destination`, `category`, `total_matches`, `selected`, `blocked`, `actions`, `truncated`, `executable=false`). Metadados adicionais só quando necessários à revisão de cobertura.

### Planejamento completo com memória controlada

1. No SQLite, **fixar a identidade do snapshot e da categoria**. Contar candidatos uma vez. A primeira implementação usa páginas SQL `LIMIT/OFFSET` de até 100 arquivos, com `scan_id` fixo e contagem verificada. Para escala superior ou concorrência com atualizações do catálogo, avaliar cursor por `media.id` e transação de leitura única, pois a ordenação estável e a contagem igual **não garantem** um snapshot de leitura atômico entre consultas.
2. O planejador determina o nome-base do destino e compara colisões **entre todas as páginas**, não só na página atual. Como todos convergem para uma única pasta, a função compara nomes usando `casefold()` e também pré-carrega os nomes presentes no destino (sem carregar arquivos de origem). Verifica origem, destino, symlinks detectáveis, tamanho e mtime. **Proteção Windows completa** ainda exigirá revisão de junctions/reparse points, equivalências de nomes e TOCTOU antes do executor.
3. **Política inicial de conflitos:** bloquear destinos já ocupados e ocorrências repetidas com o mesmo nome de saída; não sobrescrever, fundir, renomear automaticamente nem deduplicar por inferência. O usuário poderá rever os conflitos quando o fluxo estiver integrado.
4. O relatório precisa distinguir **arquivos examinados, propostos, bloqueados e ainda pendentes**, garantindo que `truncated=false` só seja apresentado se a verificação da seleção estiver completa. Um plano parcial não deve ser confundido com autorização.
5. **Escala de resultados:** o motor não deve montar milhares de ações em uma única resposta ao Ollama ou na tabela Qt. A implementação retorna `total_matches`, `examined`, `proposed`, `blocked`, `pending`, `complete`, `truncated`, `pages_scanned` e `blocked_by_reason`; `actions=[]`. Acesso paginado a ações individuais ficará para uma etapa posterior, se necessário. Não criar persistência ou arquivo de checkpoint de planos até existir necessidade operacional concreta. O teto atual é `max_candidates=10000`: se houver mais arquivos, `complete=false` e `pending` explicita quantos ficaram fora da análise.
6. **Isolamento:** fontes e catálogo são somente leitura durante o planejamento; nenhum comando move, apaga, renomeia ou cria mídia. O SQLite só é alterado pela catalogação confirmada, não pela prévia.

### Critérios de aceite antes de integrar à GUI

- Fixture com mais de 200 arquivos distribuídos entre dezenas de subpastas, incluindo nomes repetidos em páginas distintas: um mesmo destino não pode resultar em duas propostas válidas.
- Arquivos com mesma extensão e nomes diferentes, vídeos/áudios no mesmo diretório, mudanças de tamanho/mtime após catalogação, arquivos ausentes, caminhos inválidos e destino já ocupado.
- Seleção da origem mais antiga enquanto há outro snapshot global mais recente: plano somente daquela origem.
- Destino dentro da árvore de origem: sem auto-inclusão silenciosa nem movimentação para o mesmo caminho.
- Custo de memória limitado e interface não bloqueante; evidenciar incompletude quando houver qualquer corte de análise.
- Toda fixture de teste em `tests/`. Conservar e executar a suíte anterior. Nenhuma mudança de código de produção, novas pastas de módulos, dependências ou telas como pré-requisito da **especificação**.

### Divisão mínima de responsabilidades

- `inventory.py`: descobrir arquivos recursivamente; `catalog.py`: fornecer páginas e contexto; `planner.py`: gerar propostas e bloqueios; `agent.py`: traduzir intenções para ferramentas já autorizadas; `gui.py`: coletar entrada e exibir uma prévia simplificada.
- Não criar um `consolidator`, um `planner_v2` nem um gerenciador de sessões para este caso. Avaliar extração de função somente se reduzir repetição e complexidade comprovadas.

**Estado:** o resumo global está implementado no planejador existente; **os testes do motor foram homologados no Windows (87 testes, 1 ignorado)**; dois testes novos de integração do agente aguardam validação (89 esperados). O código não oferece revisão paginada de ações individuais, execução ou persistência de planos. A função agora pode ser invocada pelo adaptador Ollama via `resumir_consolidacao`, com parâmetros restritos e `context_scan_id` da GUI; ainda sem botão dedicado na interface. **Não há executor disponível.**

## Planejador cronológico experimental — somente simulação

`propose_date_moves(destination, category, db_path, limit=100, scan_id=None)` simula a organização de arquivos de mídia (`imagem`, `video`, `audio`) em `AAAA/MM/nome.ext` de acordo com `modified_utc` do snapshot selecionado. O diretório-base precisa existir; subpastas anuais e mensais **não** são criadas. Usa `query_catalog_page()` no SQLite em modo somente leitura, retornando no máximo 100 propostas.

Antes de propor, verifica existência e integridade (tamanho/mtime) da origem, links simbólicos, colisão entre alvos no plano e alvos já existentes. Indica `directory_would_need_creation` como informação, nunca instrução executável. Retorna `mode=simulation`, `executable=false`, `requires_explicit_approval=true`. Não há executor, aprovação operacional, escrita de plano ou alteração de arquivos. Este recurso **ainda não está integrado ao agente nem à GUI**: primeiro homologar com testes automatizados.

O agrupamento utiliza data de **modificação UTC**, não EXIF, data de criação nem as preferências regionais da interface. Diretórios já organizados podem produzir proposta de caminho idêntico e são bloqueados. Não executar manualmente as ações do JSON sem revisão e cópia de segurança.

## Prévia enriquecida: conflitos e suspeitas

O simulador cronológico adiciona `name_collisions` e `potential_duplicate_items` como métricas somente da **amostra paginada**. `possible_duplicate_by_metadata` verifica nome-base normalizado + tamanho maior que zero dentro da amostra, sem hash; isso não comprova cópias idênticas. Para colisões com destinos existentes ou reservados no plano, fornece `alternative_name_suggestion` (sufixo `__2`, etc.) para análise, mantendo `status=bloqueado`. Nenhum nome alternativo é reservado ou usado para execução. Política definitiva de colisões, hashes e duplicatas confirmadas ficam para uma etapa separada.

## Diagnóstico por hash SHA-256 — somente leitura

O módulo `src/archivia/duplicates.py` implementa `verify_duplicate_hashes()` como **análise da amostra**, não detecção completa do catálogo. Usa `query_catalog_page()` read-only, valida origem/paths sem symlinks ou junctions quando detectáveis, confere tamanho e mtime do snapshot no handle antes/depois da leitura, calcula hash em blocos de 256 KiB e agrupa somente `(size, SHA-256)` iguais. Há limites de arquivos e bytes; motivos de ignorados são reportados. Nenhum hash é gravado no catálogo, nenhuma mídia é modificada, nenhuma exclusão é sugerida.

A verificação de tamanho/mtime e hash não cria garantia atômica contra alterações posteriores ou reparse points em todas as plataformas; um futuro executor precisará de projeto separado e revalidação. Os fixtures `tests/fixtures/sha256_demo/` cobrem nomes iguais/diferentes, mesmo tamanho com conteúdos diferentes e arquivos vazios. O resultado não é ferramenta disponível ao agente Ollama nesta etapa.

## SHA-256 paginado: orçamento e progresso

A análise de duplicatas aceita amostras de até **1000 registros**, mas consulta SQLite sempre em páginas de **100**, com `scan_id` fixado na primeira página (quando automático). Reúne somente metadados da amostra para agrupar tamanhos iguais; hashes entre páginas são então comparados em memória. Esse desenho reduz a carga frente à consulta integral, mas a memória ainda cresce proporcionalmente à amostra limitada. Limites por arquivo (16 MiB) e leitura total (até 256 MiB, padrão 64 MiB) são validados. Eventos de progresso `catalog/hash/done` são enviados à interface em worker Qt; não há escrita em disco nem estimativa temporal.

## Seleção global de candidatos SHA-256 sem carga integral de caminhos

`verify_snapshot_duplicate_candidates()` usa `sqlite3` em `mode=ro`, escolhe um snapshot fixo e utiliza `GROUP BY size_bytes HAVING COUNT(*) > 1` para localizar tamanhos repetidos em todo o snapshot. Guarda contadores tamanho/quantidade e percorre os registros de cada grupo com `fetchmany(100)`, sem reunir todos os caminhos em memória. Grupos de tamanho que ultrapassam o limite restante de candidatos são **omitidos por inteiro**, reportados como pendentes e nunca parcialmente declarados verificados. O teto é de 5.000 candidatos por execução. As proteções SHA-256 anteriores permanecem.

O modo global não identifica duplicatas em snapshots diferentes nem permite execução de movimentos. A seleção global por tamanho é completa, mas a **verificação por hash só pode ser considerada completa** quando `unprocessed_candidate_files=0`, `skipped=[]` e `complete=true`. Limites por arquivo, orçamento I/O, alterações da origem e arquivos inacessíveis impedem conclusões sobre itens não lidos. A GUI indica a incompletude; a ausência de grupos retornados não comprova unicidade no acervo.

## Sessão progressiva em RAM — protótipo sem interface

O módulo `src/archivia/duplicate_sessions.py` implementa `ProgressiveDuplicateSession(db_path, category, scan_id)`, com `next_batch(batch_size=100, max_file_bytes, max_total_bytes)`. Seleciona candidatos pelo SQLite em leitura (`mode=ro`) com agrupamento de tamanhos repetidos; utiliza cursor `media.id` crescente para não recalcular hashes de arquivos já processados em **uma mesma sessão**. O contexto de snapshot/categoria é fixo. Resultados SHA-256 são acumulados em RAM, permitindo descobrir pares cujos arquivos estejam em lotes distintos.

Cada lote tem limite independente de quantidade (1–200), tamanho por arquivo (1–16 MiB) e orçamento total de leitura (1–256 MiB, padrão 64 MiB). Eventos de progresso são opcionais. Estado `done=true` significa que o cursor chegou ao fim; `complete=true` exige também zero itens ignorados. Um teto de **100 mil candidatos** impede sessão ilimitada em memória. Nenhum checkpoint é gravado; ao reiniciar o processo, reinicia-se a sessão. Este é o **motor inicial**, ainda sem comandos de GUI ou agente; a suíte automatizada de 83 testes foi aprovada no Windows.

O agrupamento por `SHA-256` baseia-se no conteúdo lido em cada momento, com revalidação de metadados; não significa garantia transacional sobre alterações futuras. O formato persistente e o mecanismo de retomada após reinício precisarão de decisões específicas de proteção de dados e integridade.

## Ciclo de vida dos dados no agente (fluxo automático novo)

Com uma pasta selecionada em Inventário, `gui.py` aciona `ask_agent_for_folder()` em uma thread: varredura `inventory()` → `store_inventory()` em SQLite localizado num `TemporaryDirectory` → `ask_agent()` com snapshot da sessão → exclusão automática do diretório temporário. A leitura não modifica arquivos da origem. Se a varredura encontrar erros, o banco não é criado e a pergunta não é enviada ao Ollama.

**O SQLite permanente continua existindo para o fluxo manual**, com snapshots históricos; o novo fluxo não escreve nesse banco. A pasta é examinada novamente a cada solicitação, para evitar crescimento persistente e dados antigos; armazenamento de sessão reaproveitável e recuperação após encerramento abrupto são trabalhos futuros, se necessários. O agente sem pasta selecionada continua usando o catálogo permanente por compatibilidade. Até homologar os testes no Windows, esta integração deve ser considerada experimental.

## Contexto de origem e consolidação simulada

O seletor da GUI define a origem: `scan_for_folder()` localiza o snapshot mais recente **daquela pasta exata**, e o adaptador Ollama restringe as ferramentas ao `scan_id` correspondente. O planejador `propose_moves()` aceita esse `scan_id`, categoria e um destino único existente; consulta **uma página** SQLite limitada (até 100 itens) e retorna `mode=simulation`, `executable=false`. Conflitos entre páginas ainda não são analisados; nenhum plano parcial pode ser executado. A classificação atualmente é por extensão, não por conteúdo.

## Garantias e limites
- Ainda não há executor, renomeação ou exclusão de mídias, nem análise visual por IA. A **GUI PySide6 de homologação já existe** e a integração Ollama com consultas foi validada com pasta selecionada.
- Nenhum plano é executável; não transformar `executable` em `true` sem projeto e revisão separados.
- Não há validação atômica entre planejamento e uma execução futura (TOCTOU), nem confirmação de identidade por hash.
- Múltiplas origens, permissões granulares, política para colisões Windows com casefold, segurança de junction/reparse points e destinos em outros volumes exigem revisão posterior.
- Por enquanto, não confiar no JSON do plano para executar movimentos, mesmo se alterado externamente.

## Perfis de distribuição

Um único motor Python compartilhado por Standard, Lite sem IA e Lite + IA. No momento, desenvolver e validar primeiro a Standard no Windows com RTX 3060 e Ollama local. Detalhes, dependências opcionais, limites e ordem de implementação em [EDITIONS.md](EDITIONS.md).

## Decisões de engenharia
1. Código de produção em `src/`, testes exclusivamente em `tests/`.
2. SQLite local em `data/`; dados privados não entram no Git.
3. Escritas em mídias só em um executor separado, com revisão e aprovação explícita.
4. Documentar mudanças técnicas em Markdown versionado.

## Executor experimental de arquivo único — TEST-ONLY (aguardando homologação)

- `src/archivia/executor.py`: **única operação real de arquivo introduzida**, deliberadamente **inacessível pela GUI, Ollama ou CLI**. Aceita somente uma ação da prévia `propose_moves()`, sem truncamento, conflitos ou itens adicionais, e exige a confirmação literal `CONFIRMO TESTE ARCHIVIA`.
- **Escopo físico obrigatório:** origem e destino dentro do **mesmo caso isolado** em `tests/.runtime/`, com diretório de destino previamente existente. Não suporta caminhos pessoais, `E:\\Ashley`, movimentação entre discos ou operações em lote. Não introduzir opção que contorne essa contenção nesta etapa.
- Valida a proposta contra o catálogo e o estado físico antes da operação. Rejeita links simbólicos e junctions detectáveis; bloqueia destinos já ocupados (inclusive diferença de maiúsculas/minúsculas); testa mesmo volume e identidade do arquivo.
- Usa `os.link` sem substituição do destino, seguido de `os.unlink` da origem, e grava eventos em `archivia-executor-journal.jsonl` dentro da fixture, com `fsync`. **Não é transação atômica**: falha após criar o hardlink pode deixar os dois caminhos. Nessa condição, **não repetir automaticamente** nem alegar rollback; revisão manual do journal é obrigatória.
- Cinco testes `TEST-ONLY` novos cobrem movimentação de fixture, ausência de consentimento, destino ocupado/arquivo alterado, plano adulterado ou parcial e tentativa de saída de `tests/.runtime`. Execução Windows ainda pendente.
- **Não implementado:** recuperação automática, rollback confiável, movimentação entre unidades, segurança completa contra condições de corrida, autorização de lote, interface de revisão e executor generalizado.
- **Suíte esperada:** 100 testes, assumindo 95 anteriores (o teste 95 ainda não teve homologação reportada). Nenhuma mídia do usuário deve ser usada nesta fase.


## Pipeline de movimentação verificada TEST-ONLY (aguardando homologação Windows)

- Implementado `src/archivia/move_pipeline.py`: **pipeline independente**, sem integração à GUI, CLI ou Ollama. Recebe somente uma ação integral de `propose_moves()`, revalida o plano no catálogo/disco e exige aprovação literal `CONFIRMO MOVIMENTO DE TESTE`. Origem e destino continuam fisicamente restritos ao **mesmo caso descartável** de `tests/.runtime`.
- Fluxo: identifica e calcula SHA-256 da origem; cria temporário exclusivo no destino; copia em blocos e executa `fsync`; compara SHA-256 e metadados da cópia/origem; publica o temporário com `os.link` sem sobrescrita; valida novamente ambos os arquivos; registra `REMOCAO_AUTORIZADA`; **só então tenta remover a origem** e registra `CONCLUIDO`. O temporário é limpo somente se ainda possuir a identidade física registrada.
- Journal próprio: `archivia-move-v2.jsonl`, com eventos `PREPARADO`, `TEMPORARIO_CRIADO`, `HASH_VERIFICADO`, `PUBLICADO`, `REMOCAO_AUTORIZADA`, `CONCLUIDO`, `INTERROMPIDO`. Journal pré-existente bloqueia reexecução; **sem rollback automático**.
- `tests/test_move_pipeline.py`: **8 testes novos** de sucesso/remoção da origem fictícia, confirmação obrigatória, destino ocupado, plano adulterado, falha de hash, falha de remoção com origem preservada, journal preexistente e bloqueio cooperativo. **174 testes esperados** (166 anteriormente homologados + 8 novos; 1 possivelmente ignorado), ainda não executados no Windows.
- A estratégia de temporário no volume do destino permite projetar movimentação futura entre unidades, **mas esta versão ainda não realiza nem homologa transferências reais entre volumes diferentes**.
- **Limitações críticas antes de liberar mídias pessoais:** corrida entre `stat`/`hash` e `unlink` contra processos externos (TOCTOU), resistência do journal a falha de energia/diretório, tratamento de falha pós-exclusão da origem, preservação de metadados/ACLs relevantes, múltiplos arquivos e recuperação idempotente. O lock é apenas cooperativo entre chamadas do ArchivIA. Não autorizar uso com arquivos pessoais nem conectar o agente IA.

