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

Cada lote tem limite independente de quantidade (1–200), tamanho por arquivo (1–16 MiB) e orçamento total de leitura (1–256 MiB, padrão 64 MiB). Eventos de progresso são opcionais. Estado `done=true` significa que o cursor chegou ao fim; `complete=true` exige também zero itens ignorados. Um teto de **100 mil candidatos** impede sessão ilimitada em memória. Nenhum checkpoint é gravado; ao reiniciar o processo, reinicia-se a sessão. Este é o **motor inicial**, ainda sem comandos de GUI ou agente e sem validação Windows.

O agrupamento por `SHA-256` baseia-se no conteúdo lido em cada momento, com revalidação de metadados; não significa garantia transacional sobre alterações futuras. O formato persistente e o mecanismo de retomada após reinício precisarão de decisões específicas de proteção de dados e integridade.

## Garantias e limites
- Ainda não há executor, renomeação, exclusão, análise visual por IA ou GUI. A integração Ollama com ferramentas de consulta e simulação já foi validada.
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
