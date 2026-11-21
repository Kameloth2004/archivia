# ArchivIA — Arquitetura e contrato de segurança

## Objetivo
Aplicativo desktop local para inventariar, catalogar, analisar e futuramente organizar mídias. O motor Python deve ser independente de UI e de modelo de IA. Diretório local conhecido: `D:/PROJETOS/archivia`.

## Componentes
- `src/archivia/inventory.py`: examina nomes/metadados sem abrir conteúdo nem seguir symlinks.
- `src/archivia/catalog.py`: snapshots SQLite em `data/catalogo.sqlite3`, consultas de leitura e resumo.
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
- Limite máximo de 100 itens por plano. Ainda usa `query_catalog`, que carrega os registros da categoria em memória antes de selecionar 100; isso **precisa ser substituído por consulta SQL paginada** antes de inventários muito grandes.

## Garantias e limites
- Ainda não há executor, renomeação, exclusão, IA ou GUI.
- Nenhum plano é executável; não transformar `executable` em `true` sem projeto e revisão separados.
- Não há validação atômica entre planejamento e uma execução futura (TOCTOU), nem confirmação de identidade por hash.
- Múltiplas origens, permissões granulares, política para colisões Windows com casefold, segurança de junction/reparse points e destinos em outros volumes exigem revisão posterior.
- Por enquanto, não confiar no JSON do plano para executar movimentos, mesmo se alterado externamente.

## Decisões de engenharia
1. Código de produção em `src/`, testes exclusivamente em `tests/`.
2. SQLite local em `data/`; dados privados não entram no Git.
3. Escritas em mídias só em um executor separado, com revisão e aprovação explícita.
4. Documentar mudanças técnicas em Markdown versionado.
