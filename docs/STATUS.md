# ArchivIA — Estado atual e próxima validação

**Atualizado: 22/11/2026.** Este documento registra **o estado vigente**, não um diário de cada alteração. O histórico detalhado permanece no Git e os contratos técnicos em [ARCHITECTURE.md](ARCHITECTURE.md), [AGENT.md](AGENT.md) e [GUI.md](GUI.md).

## Identidade e objetivo

Bibliotecário digital local em Python com interface PySide6 opcional e agente Ollama local. Objetivo do produto: **escolher uma pasta → inventariar/catalogar → encontrar/classificar → propor organização → revisar → autorizar execução segura (futuro)**. Não é um gerenciador genérico de utilitários. Regras de contenção de escopo em [SCOPE.md](SCOPE.md).

- Repositório: `Kameloth2004/archivia`, **branch única `main`**, código local do usuário em `D:/PROJETOS/archivia`.
- Ambiente de homologação: Windows 10, Git Bash, Python 3.12, Ollama local com `qwen3:8b-q4_K_M`.
- Dependências do motor: biblioteca padrão Python e SQLite; PySide6 opcional para interface.
- Mídias: **nenhuma operação real de mover, renomear ou apagar** implementada. Testes e fixtures devem ficar em `tests/`, nunca na biblioteca real.

## Estado confirmado

| Componente | Situação |
|---|---|
| Inventário recursivo de pastas, por metadados/extensões | Implementado e testado |
| Catálogo SQLite e histórico de snapshots por origem | Histórico permanente apenas na catalogação manual; o agente com pasta selecionada agora cria **catálogo temporário descartável** automaticamente (pendente de homologação) |
| Consulta paginada, busca por nome/caminho, extensão, categoria e período | Implementado |
| GUI PySide6 de homologação (6 abas) | Implementada, **não** é o design definitivo |
| Contexto de pasta para agente | Implementado: na GUI, pasta catalogada selecionada vincula `scan_id` ao agente |
| Ollama com ferramentas autorizadas | Integrado para consultas, simulações e **resumo global de consolidação** (novo, aguardando testes), sem shell e sem executor |
| Planejador genérico de consolidação em uma pasta | **Somente simulação**; `propose_moves()` lê até 100 ações e `summarize_consolidation()` examina até 10.000 candidatos em lotes, retornando estatísticas globais; aceita `scan_id` |
| Planejador cronológico `AAAA/MM` | Somente simulação; até 100 propostas, com bloqueio de colisões |
| SHA-256 em amostra e modo global | Homologado com fixtures; resultados parciais destacados |
| Sessão progressiva SHA-256 | Motor em memória testado, **não** integrado na GUI; não ampliar agora |
| Classificação visual/semântica | Não implementada |
| Organização/renomeação real e recuperação | Não implementados |

## Homologação recente

- **92 testes homologados no Windows pelo usuário**: `Ran 89 tests in 4.731s`, `OK (skipped=1)` (88 aprovados e um ignorado), nenhuma falha.
- Ollama real / GUI: pasta `E:\\Ashley`, snapshot **#6**, consulta `buscar_arquivos_catalogo` com `categoria=imagem`; resultado **1.344 imagens**, 10 exemplos, 135 páginas; resposta do agente coerente com os dados. Erro anterior `limite inválido` não reapareceu.
- Modo SHA-256 global / fixture snapshot #4: 134 candidatos, 3 grupos de conteúdo igual e 7 arquivos associados; com limite 50, 125 candidatos pendentes e estado **GLOBAL INCOMPLETA**. Indicador visual específico de cobertura foi implementado, **mas sua aparência final ainda não foi homologada por captura**.
- Verificação remota de `main` em 22/11/2026, antes da atualização editorial: commit `a622f47716bbad4e32aafb1dd966d2d48565d134` idêntico a `main`, zero commits divergentes; única branch encontrada: `main`. Não foram encontrados status checks associados ao commit. O repositório remoto não permite confirmar alterações locais não enviadas.

## Limites e cuidados

1. **Uma prévia de 100 ações não é um plano completo.** `propose_moves()` ainda não detecta conflitos fora da sua página. O novo `summarize_consolidation()` detecta colisões entre páginas dos candidatos examinados e informa pendências; **não retorna lista de ações**, não pode executar e tem teto de 10.000 arquivos.
2. Com pasta selecionada, o agente agora **revarre a origem em cada pergunta**, cria SQLite temporário e o descarta ao concluir. Não exige inventário salvo. Sem pasta selecionada, por compatibilidade, usa banco persistente escolhido. Inventários com erros são recusados. O novo fluxo ainda aguarda testes no Windows.
3. Inventário classifica por extensão; nenhuma fotografia é interpretada visualmente pelo Ollama nesta versão. Hashes identificam igualdade de bytes apenas dos arquivos lidos.
4. `gui.py` é uma bancada de homologação e está grande (~1.400 linhas). Modularizar **por responsabilidades**, quando realmente for iniciado o redesign; não espalhar arquivos por capricho.
5. O comando `consultar` legado ainda pode reunir muitas linhas em RAM; a interface já usa consulta paginada. Não adicionar novas rotinas que carreguem toda a biblioteca.
6. Nenhuma aprovação do usuário, resposta da IA ou plano em simulação autoriza movimentação real. Um futuro executor exigirá proteção contra sobrescrita, revalidação de caminhos/metadados, registro e recuperação.

## Atualização editorial e integração de 22/11/2026

- Enxugado `docs/STATUS.md` (~52 KB → ~5,5 KB antes deste registro) para representar apenas o estado vigente, conservando o histórico de mudanças nos commits Git.
- Revisados `README.md`, `docs/ARCHITECTURE.md`, `docs/AGENT.md`, `docs/GUI.md` e `docs/EDITIONS.md` para corrigir referências desatualizadas e registrar a homologação de consulta do Ollama real.
- Acrescentado somente **um teste** de integração mock de `simular_movimentacao` via agente: origem com subpastas, três imagens, um áudio e dois nomes idênticos, com outra origem mais recente no banco. Esperado: snapshot correto, três imagens, um conflito, destino intacto.
- **Nenhum código de produção, interface ou contrato da ferramenta foi modificado nesta etapa**. Sem execução de arquivos, sem novas dependências ou módulos.

## Especificação de consolidação completa — 22/11/2026

- Publicado contrato em `docs/ARCHITECTURE.md`: fixar origem/snapshot, categoria, destino único, ler por lotes estáveis, comparar nomes em **todas as páginas** e distinguir propostas, bloqueios e pendências.
- Padrão inicial: **bloquear colisões**, sem renomear nem sobrescrever automaticamente. Não retornar milhares de ações ao Ollama nem presumir conclusão quando a amostra estiver incompleta.
- **Somente documentação nesta etapa.** Os algoritmos atuais continuam com prévias limitadas a 100 itens; nenhuma mudança executável.

## Implementação em homologação — resumo global

- Publicada `summarize_consolidation()` em `src/archivia/planner.py`: análise em lotes SQL de até 100, teto explícito de 10.000, identificação de nomes em conflito entre páginas e comparação de nomes de arquivos existentes com `casefold()`.
- Retorno limitado a estatísticas `total_matches`, `examined`, `proposed`, `blocked`, `pending`, `complete`, `truncated`, `pages_scanned`, `blocked_by_reason`. O campo `actions` é vazio; não é um plano executável.
- Três testes sintéticos para colisões entre páginas, limite com pendências e destino ocupado/arquivo modificado. **Os 87 testes foram aprovados pelo usuário no Windows** (`OK (skipped=1)`).
- `propose_moves()` anterior permanece compatível. O resumo global foi agora exposto à IA como `resumir_consolidacao`, **sem botão novo na GUI**, sem dependências ou módulos novos; aguarda testes do agente.

## Integração do resumo global com o Ollama — aguardando homologação

- Adicionada ferramenta autorizada `resumir_consolidacao` em `agent.py`, com parâmetros `categoria`, `destino` e `limite` opcional (1–10.000).
- A ferramenta utiliza `context_scan_id` da pasta selecionada na GUI, rejeita parâmetros extras e só chama `summarize_consolidation()`. O retorno contém contagens e `actions=[]`, `executable=false`.
- Adicionados **dois testes MOCK-ONLY**: catálogo de 105 imagens e colisão entre páginas usando snapshot de outra origem mais recente; validação de argumentos inválidos. **89 testes homologados** (87 anteriores + 2), um ignorado.
- Sem criação de pastas, renomeação, exclusão ou movimentação de arquivos; sem nova aba ou dependência.

## Catálogo temporário automático para consultas do agente — aguardando homologação

- Adicionada `ask_agent_for_folder()` ao `agent.py`, usando `TemporaryDirectory`, `inventory()`, `store_inventory()` e o agente já existente. O banco SQLite nasce fora da pasta do usuário e é descartado após a solicitação, inclusive se houver erro.
- Na GUI, quando a origem está selecionada em Inventário, clicar em **Perguntar ao agente** agenda a varredura e catalogação temporária no worker, **sem precisar examinar previamente nem salvar inventário**. A função anterior de catalogação manual e o banco permanente ficam intocados.
- Uma pasta nova é reexaminada **em toda pergunta ao agente** nesta primeira implementação: não há cache persistente ou reaproveitamento entre consultas. Essa decisão é segura para o crescimento do banco, mas terá custo de leitura a avaliar em acervos grandes.
- Três testes `TEST-ONLY` acrescentados em `tests/test_agent.py`: sucesso sem modificar catálogo persistente; falha Ollama com limpeza; inventário incompleto recusado. **92 testes homologados no Windows**: `Ran 92 tests in 5.652s`, `OK (skipped=1)`; 91 aprovados, um ignorado.
- Sem criação de novas abas, módulos, dependências ou qualquer execução de movimentações.

## Homologação real do catálogo temporário — 22/11/2026

- GUI: usuário selecionou `E:\\Ashley` e perguntou ao Ollama sem usar **Examinar pasta** ou **Salvar inventário**; resposta `1.344 imagens`.
- Ferramenta real `buscar_arquivos_catalogo`: argumentos `{"categoria":"imagem","scan_id":1}`, resultado `count=1344`, `page_size=10`, `pages=135`, `root=E:\\Ashley`.
- SQLite foi criado em `%LOCALAPPDATA%/Temp/archivia-session-*/catalogo.sqlite3`, confirmando o uso do **catálogo temporário** e não do banco persistente. `scan_id=1` é local à sessão.
- **Homologado:** selecionar pasta → inventário/catalogação automáticos → consulta Ollama. Nenhum arquivo foi movimentado.
- **Limite da evidência:** o resultado mostra o banco temporário em uso, mas não comprova por si só a remoção após o retorno; a limpeza foi testada anteriormente com mocks (suíte de 92 testes), incluindo erro simulado.
- Próximas prioridades: evitar nova varredura a cada pergunta na mesma sessão, revisar tratamento de falhas abruptas e desenhar o fluxo principal simplificado; sem persistência involuntária e sem executor de arquivos.

## Sessão temporária reutilizável — atualização pendente de homologação

- `FolderCatalogSession` reutiliza um único catálogo SQLite temporário para várias perguntas na **mesma pasta**, sem revarrer a origem a cada chamada.
- A troca da pasta selecionada e o fechamento normal da janela descartam o catálogo; consultas em andamento impedem fechamento/troca até terminar.
- **Atualizar análise da pasta** faz nova varredura manual e substitui o snapshot da sessão. Falha de atualização preserva o último catálogo válido, sinalizando erro. A interface informa a data da catalogação e alerta que mudanças externas **não são detectadas automaticamente**.
- `ask_agent_for_folder()` anterior continua disponível como consulta temporária isolada por chamada; fluxo novo da GUI usa `FolderCatalogSession`.
- Dois testes de sessão acrescentados (reutilização, atualização e erro). **94 testes homologados no Windows pelo usuário**: `Ran 94 tests in 6.206s`, `OK (skipped=1)`; 93 aprovados e um ignorado.
- Nenhum banco permanente, nova dependência, módulo ou executor de arquivos foi criado.

## Correção de seleção de origem e filtros — aguardando homologação

- Relatório real mostrou `database=D:\\PROJETOS\\archivia\\data\\catalogo.sqlite3` (histórico persistente), `scan_id=7`, `nome=E:/Ashley` e `count=0`. O parâmetro `nome` filtra **caminhos relativos**, não seleciona a origem. O zero foi produto do filtro incorreto; não indica ausência de imagens.
- A GUI agora **exige pasta selecionada em Inventário** para o agente e não faz fallback silencioso ao histórico. Informar uma pasta apenas no texto da pergunta não a seleciona na interface.
- A busca do agente ignora o filtro `nome` apenas quando ele é exatamente o caminho absoluto da origem do snapshot. Outros caminhos absolutos são rejeitados; filtros relativos normais mantidos.
- Instruções do agente e descrição da ferramenta esclarecem que `nome` nunca deve conter o diretório absoluto da origem.
- Um teste sintético novo cobre origem absoluta e rejeição de outro caminho. **Suíte esperada: 95 testes** (94 anteriores + 1), um possivelmente ignorado. Execução Windows pendente.
- O timeout anterior foi atribuído pelo usuário a outro aplicativo utilizando VRAM; após fechá-lo o Ollama respondeu. Nenhuma alteração de timeout foi feita.

## Homologação real da reutilização — 22/11/2026

- Usuário confirmou nova pergunta ao Ollama sobre áudio, vídeos e imagens após uma consulta anterior de vídeos **sem atualizar a análise nem trocar de pasta**.
- As três chamadas de `buscar_arquivos_catalogo` na nova pergunta utilizaram a mesma origem `E:\\Ashley`, `scan_id=1`, `scanned_utc=2026-11-22T21:46:18.416633+00:00` e **exatamente o mesmo SQLite temporário** `archivia-session-aao5bfsh/catalogo.sqlite3` da consulta anterior.
- Contagens confirmadas: **652 áudios, 648 vídeos, 1.344 imagens, total de 2.644 arquivos**.
- **Homologado em uso real:** reutilização do mesmo catálogo nas perguntas consecutivas e atualização manual criando nova sessão (ver teste anterior); nenhum arquivo modificado.
- **Limite da evidência:** confirmação do mesmo caminho comprova reutilização do catálogo, não mede diretamente novas leituras físicas; a ausência de nova varredura decorre do fluxo do código e é coberta por teste de mock. Descarte após fechar a GUI também permanece coberto por código/testes, sem observação direta nesta execução.
- Fluxo principal estável para consultas; priorizar simplificação de interface e futura revisão das propostas antes de qualquer executor.

## Primeira migração visual — Início simplificado (pendente de homologação)

- A interface possui agora **Início, Biblioteca e Configurações** como abas principais. O botão alternável **Avançado** exibe a bancada original dentro de uma aba temporária com Visão geral, Inventário, Organização e Agente IA.
- **Início** tem seletor de pasta sincronizado com o controle antigo, atalhos de contagem de imagens/vídeos/áudios, instrução natural, pasta de destino opcional para pedidos de simulação, atualização do catálogo temporário e uma resposta textual simples. Reutiliza o mesmo `_run_agent()` e `FolderCatalogSession`; nenhuma lógica nova sobre mídia.
- A configuração do modelo Ollama foi realocada para **Configurações**. A resposta detalhada com `tools_used` segue acessível em Avançado → Agente IA.
- **Limites da primeira migração:** a aba Biblioteca ainda depende do fluxo histórico do banco persistente; a tela Início exige Ollama para os atalhos de contagem e não possui ainda fluxo local equivalente no modo sem IA. Não é o redesign final nem habilita executor.
- **Código publicado, sem suíte executada nesta atualização de layout.** Os últimos testes informados pelo usuário foram os 94 testes anteriores; a atualização subsequente de filtro de origem acrescentou um teste (95 previstos). Validar testes e abertura da GUI no Windows antes de ocultar/remover mais controles.

## Executor experimental de arquivo único — TEST-ONLY (aguardando homologação)

- `src/archivia/executor.py`: **única operação real de arquivo introduzida**, deliberadamente **inacessível pela GUI, Ollama ou CLI**. Aceita somente uma ação da prévia `propose_moves()`, sem truncamento, conflitos ou itens adicionais, e exige a confirmação literal `CONFIRMO TESTE ARCHIVIA`.
- **Escopo físico obrigatório:** origem e destino dentro do **mesmo caso isolado** em `tests/.runtime/`, com diretório de destino previamente existente. Não suporta caminhos pessoais, `E:\\Ashley`, movimentação entre discos ou operações em lote. Não introduzir opção que contorne essa contenção nesta etapa.
- Valida a proposta contra o catálogo e o estado físico antes da operação. Rejeita links simbólicos e junctions detectáveis; bloqueia destinos já ocupados (inclusive diferença de maiúsculas/minúsculas); testa mesmo volume e identidade do arquivo.
- Usa `os.link` sem substituição do destino, seguido de `os.unlink` da origem, e grava eventos em `archivia-executor-journal.jsonl` dentro da fixture, com `fsync`. **Não é transação atômica**: falha após criar o hardlink pode deixar os dois caminhos. Nessa condição, **não repetir automaticamente** nem alegar rollback; revisão manual do journal é obrigatória.
- Cinco testes `TEST-ONLY` novos cobrem movimentação de fixture, ausência de consentimento, destino ocupado/arquivo alterado, plano adulterado ou parcial e tentativa de saída de `tests/.runtime`. **100 testes homologados no Windows** (`Ran 100 tests in 5.329s`, `OK (skipped=1)`); 99 aprovados e um ignorado.
- **Não implementado:** recuperação automática, rollback confiável, movimentação entre unidades, segurança completa contra condições de corrida, autorização de lote, interface de revisão e executor generalizado.
- **Suíte anterior homologada:** 100 testes, com 1 ignorado. Nenhuma mídia do usuário deve ser usada nesta fase.

## Inspeção do journal e falhas interrompidas — aguardando testes Windows

- Em `executor.py`, adicionada `inspect_test_journal(test_directory)`, inspeção **somente leitura** restrita a `tests/.runtime/<caso>`. Não desfaz, repete, apaga ou modifica mídias.
- O diagnóstico verifica a estrutura dos registros JSONL e a permanência da origem e do destino; classifica como `concluido_registrado`, `falha_registrada` ou `revisao_manual_obrigatoria`.
- A situação `INTERROMPIDO_REMOCAO` pode deixar dois nomes para o mesmo conteúdo no mesmo volume. A inspeção reporta presença, **não prova igualdade nem recupera automaticamente**.
- Três testes sintéticos novos: conclusão normal, falha simulada na remoção com ambos os caminhos preservados, journal ausente/inválido e isolamento da área de testes.
- **103 testes homologados no Windows**: `Ran 103 tests in 5.516s`, `OK (skipped=1)`; 102 aprovados, um ignorado.
- Pendências antes de permitir arquivos pessoais: identidade verificável, journal resistente a múltiplas operações, análise de condições de corrida, recuperação idempotente e suporte seguro a volumes diferentes.

## Recuperação restrita do hardlink TEST-ONLY — aguardando homologação

- Adicionada `rollback_interrupted_test_move()` a `executor.py`. Só aceita journal com sequência exata `PREPARADO → DESTINO_CRIADO → INTERROMPIDO_REMOCAO` e aprovação literal `CONFIRMO TESTE ARCHIVIA`.
- Verifica que ambos os arquivos são regulares, estão no mesmo caso isolado em `tests/.runtime` e possuem **mesma identidade física (device e inode)**; revalida identidade, tamanho e mtime imediatamente antes da operação.
- Nesse estado delimitado, elimina **apenas o hardlink extra do destino**, preservando a origem; registra `RECUPERACAO_INICIADA` e `RECUPERADO` no journal e recusa reexecuções posteriores.
- Três testes `TEST-ONLY` adicionados: recuperação de falha de remoção, recusa de destino substituído/sem aprovação e recusa de operação concluída. **106 testes homologados no Windows** em 22/11/2026: `Ran 106 tests in 5.618s`, `OK (skipped=1)`; 105 aprovados e um ignorado.
- **Limitação de segurança:** o caminho pode ser substituído por outro processo entre a última verificação e `os.unlink` (TOCTOU); não há garantia de integridade sob concorrência adversarial, nem suporte a volumes diferentes. Portanto, ainda não liberar arquivos reais nem integrar a GUI/Ollama.
- A inspeção anterior permanece somente leitura; o rollback exige autorização explícita e continua restrito à fixture. A recuperação automática geral **não existe**.

## Exclusão cooperativa e revalidação final — aguardando homologação Windows

- O executor passou a proteger **execução e recuperação** com o mesmo lock exclusivo por caso de fixture: diretório atômico `.archivia-operation.lock` criado com `os.mkdir`; tentativa concorrente é recusada. Um lock remanescente após falha/crash exige revisão, não é removido automaticamente em nova execução.
- Após persistir `DESTINO_CRIADO`, o executor revalida `st_dev`, `st_ino`, tamanho e `mtime_ns` da origem e identidade do hardlink destino antes de tentar remover a origem. Se algo mudar, registra `INTERROMPIDO_VERIFICACAO` e preserva ambos os caminhos para revisão.
- Três testes novos: concorrência na execução, concorrência na recuperação e modificação durante o registro do destino. **109 testes homologados no Windows:** `Ran 109 tests in 5.879s`, `OK (skipped=1)`; 108 aprovados e um ignorado.
- **Limitação expressa:** lock é cooperativo apenas entre chamadas do ArchivIA que o respeitam; processos externos podem modificar caminhos. A revalidação ainda sofre TOCTOU entre `stat` e `unlink`. Nenhuma garantia de segurança geral nem permissão para utilizar arquivos reais.
- Permanece **TEST-ONLY** dentro de `tests/.runtime`, sem integração com GUI, CLI ou Ollama.

## Cópia verificada de fixture — SHA-256 e publicação exclusiva (pendente Windows)

- Implementado `src/archivia/verified_copy.py` com `copy_verified_test_file()`, **separado do executor de movimentação**, sem integração GUI/CLI/Ollama.
- Permite **um único arquivo fictício por vez**, exclusivamente sob a mesma fixture em `tests/.runtime/`, com aprovação explícita e plano de simulação integral, não bloqueado e revalidado. Usa o mesmo lock cooperativo da movimentação/recuperação.
- Abre a origem em modo de leitura, cria arquivo temporário exclusivo **dentro do diretório de destino**, copia em blocos e força `fsync`; compara **SHA-256 da origem e da cópia**, tamanho e identidade/metadados da origem.
- Publica o temporário com `os.link(temp, destino)` para **não substituir destino existente** e remove somente o nome temporário depois; **nunca apaga a origem**. Um hardlink entre temporário e destino é criado no volume do destino, independentemente de onde esteja a origem, embora **não tenha sido testado em duas unidades reais**.
- Journal independente `archivia-copy-journal.jsonl`: `PREPARADO`, `TEMPORARIO_CRIADO`, `HASH_VERIFICADO`, `PUBLICADO` e `INTERROMPIDO`. Journal existente recusa nova cópia para não ocultar falhas anteriores. Interrupção após publicação pode deixar destino publicado; não tentar repetição automática.
- Sete testes automatizados novos: cópia correta/hash/origem preservada, ausência de aprovação, destino ocupado, plano adulterado/truncado, lock concorrente, falha injetada e journal já existente. **116 testes homologados no Windows**: `Ran 116 tests in 7.871s`, `OK (skipped=1)`; 115 aprovados e um ignorado.
- Limitações: não implementa rollback de cópia; não prova resistência a alterações por processos externos entre verificações (TOCTOU), não valida ACLs/atributos/metadados estendidos, não cobre quedas de energia com confirmação de diretórios, e não habilita remoção da origem. **Não utilizar arquivos pessoais.**

## Diagnóstico somente leitura das cópias — aguardando homologação Windows

- Adicionada `inspect_verified_copy_test()` em `src/archivia/verified_copy.py`, limitada a um caso descartável de `tests/.runtime`; nenhuma remoção, repetição, rollback ou limpeza automática.
- Lê e valida sequência dos eventos JSONL da cópia (`PREPARADO`, `TEMPORARIO_CRIADO`, `HASH_VERIFICADO`, `PUBLICADO`, `INTERROMPIDO`). Rejeita registros inválidos, misturados, truncados ou que apontem para outro caso.
- Inspeciona presença de origem e destino, calcula SHA-256 atual dos dois arquivos quando ambos existem e lista eventuais temporários `.archivia-copy-*.tmp`. **Igualdade de hash só indica igualdade no instante da inspeção**; não comprova durabilidade nem autoriza exclusão da origem.
- A falha de journal após a publicação do hardlink pode deixar origem e destino presentes com último evento `INTERROMPIDO`: estado `interrompido_revisao_manual`. Cópias normais reportam `publicacao_registrada_inspecionada`. Nenhum estado dispara recuperação.
- Quatro novos testes de fixture verificam publicação, falha injetada pós-publicação, temporário remanescente e journal inválido/fora de escopo. **120 testes homologados no Windows:** `Ran 120 tests in 6.459s`, `OK (skipped=1)`; 119 aprovados e 1 ignorado.
- **Pendentes antes de qualquer mídia real:** consistência de journal sob falha de energia, identidade/TOCTOU, recuperabilidade idempotente, movimentação entre volumes distintos e confirmação do usuário na interface.

## Reconciliação restrita de cópia publicada — TEST-ONLY (pendente de homologação)

- `reconcile_published_test_copy()` em `src/archivia/verified_copy.py` aceita somente um journal com sequência exata `PREPARADO → TEMPORARIO_CRIADO → HASH_VERIFICADO → INTERROMPIDO`, ambos os arquivos presentes e nenhum temporário remanescente. Exige `CONFIRMO TESTE ARCHIVIA` e compartilha lock por fixture.
- Calcula novamente SHA-256 dos dois arquivos, verifica que seus metadados e identidades físicas permaneceram estáveis durante a leitura e exige hashes iguais. Após essas condições, **apenas registra `COPIA_RECONCILIADA`** no journal. **Nunca remove, move, substitui ou altera origem/destino**; não retoma publicação nem limpa temporários.
- `inspect_verified_copy_test()` reconhece a sequência reconciliada e reporta `copia_reconciliada_registrada`; a segunda tentativa é recusada. Journals inconsistentes, arquivo modificado, ausência de arquivo ou temporário remanescente bloqueiam a reconciliação.
- **Limite importante:** o journal legado não identifica o temporário individualmente nem comprova que a publicação realmente ocorreu naquele evento; o processo apenas reconcilia evidência atual de conteúdo igual. Continua existindo risco de concorrência externa e falha de energia. Não declarar como garantia de recuperabilidade universal.
- Quatro testes novos: reconciliação válida sem alteração de arquivos, ausência de consentimento/destino alterado, temporário remanescente e interrupção anterior à publicação. **124 testes homologados no Windows**, conforme execução informada pelo usuário (`OK`, 1 ignorado). São 123 aprovados e 1 ignorado.
- Nenhum arquivo pessoal ou unidade física externa à fixture é autorizado; GUI/CLI/Ollama continuam desconectados do executor.

## Revisão externa da GUI — análise inicial

- O usuário submeteu `src/archivia/gui.py` ao Gemini e apresentou cinco observações. Conferência com a versão atual de **1.615 linhas** em `main`: sincronização direta dos campos `home_folder` e `folder` não constitui, isoladamente, prova de loop infinito; `QueryWorker` tem sinais `finished_result`, `failed` e `finished` com limpeza em `_worker_done`.
- **Prioridade alta:** handlers `_run_inventory_preview`, `_run_date_plan` e `_run_duplicate_hash` modificam/limpam widgets antes de `_start_worker` recusar segunda operação; colocar guarda explícita antes de mudanças visuais.
- **Prioridade média:** em `_change_date_format`, reinterpretação do texto já formatado pode falhar silenciosamente; preferir ISO preservado em `Qt.UserRole` para reexibição. Em `_show_result`, validar contratos obrigatórios e não converter erros de schema em zeros ou dados falsos via `.get` indiscriminado.
- **Outros pontos:** `DEFAULT_DB` passado ao worker em modo `folder_session` não é consultado quando a sessão existe, conforme implementação de `QueryWorker.run`. Fechamento bloqueado durante trabalho é intencional; cancelamento cooperativo pode ser projetado mais tarde.
- Revisão registrada **sem alteração no código da GUI**. Executar correções isoladas com regressão visual antes de qualquer novo redesign.

## Estabilização incremental da GUI — código publicado, testes Windows pendentes

- A versão anterior do `src/archivia/gui.py` possuía **1.615 linhas**. Extraída a classe `QueryWorker` (~5 kB, ~90 linhas) para `src/archivia/gui_worker.py`. `ArchivIAWindow` importa a classe, mantendo os sinais, parâmetros e fluxos de leitura, catálogo, prévia e Ollama originais. `gui.py` passou a aproximadamente **1.525 linhas**; não houve redesenho de telas ou integração do executor.
- Criado `src/archivia/gui_helpers.py`, independente de PySide6, com `validate_gui_result()`: valida campos obrigatórios antes de renderizar. A GUI captura respostas incompletas e exibe erro explícito; **não converte campos faltantes em valores numéricos fictícios**.
- Adicionadas guardas `if self._worker is not None: return` no início de `_run_inventory_preview`, `_run_summary`, `_run_date_plan`, `_run_duplicate_hash`, impedindo limpar visualizações enquanto outro worker trabalha.
- Itens da coluna de datas da tabela de catálogo agora guardam o ISO original no `Qt.ItemDataRole.UserRole`. `_change_date_format` usa esse valor original para reexibir, sem `strptime` do texto já formatado e sem `except ValueError: pass` silencioso.
- Seis testes de contratos independentes de Qt em `tests/test_gui_helpers.py` e cinco testes estruturais em `tests/test_gui_structure.py`. **135 testes homologados no Windows**, conforme execução informada pelo usuário: `Ran 135 tests in 6.889s`, `OK (skipped=1)`; 134 aprovados e 1 ignorado.
- Decisões preservadas: não alterar sincronização bidirecional de campos sem falha reproduzida; não alterar ciclo de vida `QThread` ou lógica de fechamento enquanto estiverem estáveis; não fragmentar os 1.525 linhas restantes em uma refatoração ampla sem homologação incremental.
- Limitações: testes estruturais e de contrato não substituem abertura real da GUI com PySide6; verificar visualmente Início, Biblioteca, Configurações, Avançado e troca de formatos de data. O executor real continua desconectado da GUI.

## Homologação visual parcial — mudança de pasta e consultas (23/11/2026)

- Usuário abriu a GUI após os 135 testes automatizados e selecionou uma pasta de origem e uma pasta de destino já existente.
- Consultou a **quantidade de imagens** da primeira pasta: resultado conferido como correto.
- Sem atualizar manualmente a análise, consultou a **quantidade de vídeos** da mesma pasta: resultado conferido como correto.
- Mudou a **pasta de origem durante a mesma sessão** e consultou novamente a quantidade de imagens, sem atualização manual: resultado conferido como correto.
- **Homologação parcial da GUI:** consultas sucessivas e troca de contexto de origem funcionaram em uso real, com o `QueryWorker` extraído. A pasta de destino estava selecionada, mas o relato não implica execução de plano ou movimentação.
- **Validação adicional informada pelo usuário:** a alternância do formato de datas na GUI funciona. O relato confirma a mudança visual do formato; não comprova separadamente todas as sequências de formatos ou casos de datas inválidas. **Ainda pendente:** revisão detalhada das demais telas e teste de erro do backend; não declarar homologação visual integral.

## Modularização da apresentação das tabelas — implementação publicada (pendente de homologação)

- `src/archivia/table_rows.py`: funções puras `inventory_preview_rows`, `origin_rows`, `duplicate_rows`, `date_plan_rows` e `catalog_rows`, sem dependência de PySide6. Centralizam as células, os tooltips e a preservação do timestamp ISO original no catálogo; não acessam ou alteram arquivos.
- `src/archivia/gui_tables.py`: `fill_table()`, helper PySide6 para preencher `QTableWidget` já configurada. Valida a largura e as dimensões de tooltips e metadados antes de modificar o número de linhas; mantém a configuração das tabelas e usa `Qt.ItemDataRole.UserRole` para ISO.
- `src/archivia/gui.py`: cinco laços de preenchimento foram substituídos por chamadas aos helpers; `QTableWidgetItem` não é mais importado diretamente. Redução de aproximadamente **1.525 para 1.481 linhas**. Nenhum redesign, renomeação de abas, mudança de consulta ao Ollama ou acesso ao executor.
- `tests/test_table_rows.py`: **sete testes** de formatação sem Qt (prévia, origens, duplicatas, planos e datas, inclusive casos vazios). O teste estrutural de ISO existente foi adaptado para verificar `table_rows.py` + `gui_tables.py`, sem acrescentar nova contagem de testes.
- **142 testes homologados no Windows:** `Ran 142 tests in 6.884s`, `OK (skipped=1)`; 141 aprovados, 1 ignorado e nenhuma falha. **Homologação visual das tabelas ainda pendente.** Validar visualmente as cinco tabelas e alternância BR/ISO/US antes de continuar a extração.
- **Pendente:** testes visuais completos dos componentes Qt, avaliação futura de um modelo/delegate de tabela se houver necessidade de desempenho ou paginação maior, sem reescrita prematura.

## Homologação visual da modularização das tabelas — 23/11/2026

- Usuário confirmou que **tudo foi preservado** após abrir a GUI e verificar a apresentação, em resposta à solicitação de conferir tabelas de inventário/catálogo, datas e detalhes disponíveis de duplicatas e simulação.
- Somado à suíte Windows de **142 testes** (`OK (skipped=1)`), o resultado aprova a segunda etapa incremental de extração de `table_rows.py` e `gui_tables.py` para prosseguir.
- Limite da evidência: a confirmação é de preservação visual observada; não demonstra todos os estados possíveis, concorrência externa, nem autoriza movimentação de mídias pessoais.

## Terceira modularização da GUI — filtros, paginação e relatórios (aguardando homologação)

- Adicionado `src/archivia/gui_presentation.py`, módulo **puro**, sem Qt, Ollama ou SQLite, com `catalog_filters`, `previous_page`, `next_page`, `summary_report`, `inventory_report` e `agent_report`.
- `catalog_filters` centraliza a tradução das datas digitadas para ISO e os demais parâmetros de pesquisa; passa os mesmos argumentos ao worker e recusa intervalo de datas invertido antes da consulta. Isso é validação de UI; as validações do backend permanecem.
- A navegação pelas páginas de inventário e catálogo compartilha helpers de limites, preservando os handlers e sinais de widgets existentes.
- Os textos de resumo, prévia e resposta detalhada do agente foram movidos para funções reutilizáveis sem alteração intencional de conteúdo, incluindo avisos de segurança e horário de catálogo temporário.
- `gui.py` passou de aproximadamente **1.481 para 1.454 linhas**; nenhuma tela foi redesenhada, os algoritmos e o executor não foram alterados.
- **Dez testes novos:** oito em `tests/test_gui_presentation.py` (filtros, datas, paginação e relatórios) e dois de integração estrutural em `tests/test_gui_structure.py`. **152 testes homologados no Windows**: `Ran 152 tests in 6.507s`, `OK (skipped=1)`; 151 aprovados, 1 ignorado e zero falhas. A verificação visual desta terceira etapa ainda está pendente.
- Próxima validação visual: busca no catálogo com filtros, mudança de data e paginação; prévia paginada e resposta do agente em Início/Avançado; textos de resumo iguais aos da versão anterior. Não há liberação de movimentos reais.

## Navegação automática após salvar inventário — implementação publicada, homologação pendente

- Após o usuário confirmar **Salvar inventário no catálogo SQLite** em **Avançado → Inventário**, a GUI aguarda a conclusão do `QueryWorker` de gravação, atualiza o histórico pelo banco configurado e seleciona pelo **ID exato** o snapshot recém-criado. Só então abre a aba **Biblioteca** e lista os arquivos; não confia na seleção genérica `Mais recente (automático)`.
- Filtros anteriores do catálogo são limpos durante a consulta do histórico, antes de iniciar a listagem, para não aplicar inadvertidamente critérios de outra pasta; a categoria também é redefinida para **Todas**. As operações encadeadas não iniciam um segundo worker antes do encerramento do anterior.
- Em caso de histórico sem o novo snapshot, exibe erro claro e não seleciona outro silenciosamente; falhas de apresentação cancelam o encadeamento. A atualização do histórico após a gravação não exige uma nova varredura da pasta nem envia dados ao Ollama.
- Criado `src/archivia/gui_navigation.py` com helper puro `find_saved_snapshot()`. Quatro testes de ID/histórico em `tests/test_gui_navigation.py` e dois novos testes estruturais de fluxo em `tests/test_gui_structure.py`. **158 testes esperados** (152 homologados anteriormente + 6 novos, um possivelmente ignorado). **Ainda não executados pelo usuário no Windows.**
- Escopo: melhora somente a navegação entre catálogo persistente e Biblioteca. O catálogo temporário do **Início** segue separado; nenhuma mídia é movida/copiada/excluída pelo agente ou interface.
- Homologação visual necessária: salvar fixture sem dados pessoais, confirmar seleção do snapshot salvo e abertura da Biblioteca; filtros anteriores devem ser removidos. Testar retorno ao fluxo manual caso a consulta ao histórico falhe.

## Catalogação opcional pelo Início — implementação publicada (homologação pendente)

- Adicionados três comandos na tela **Início**: **Examinar pasta para catalogar**, **Conferir arquivos da prévia** e **Salvar no catálogo SQLite...**. Eles reutilizam os métodos existentes do **Avançado → Inventário**, sem duplicar consultas ou alterar o backend.
- Ao examinar a pasta, o resultado apresenta no **Início** os totais e erros da prévia. **Conferir arquivos da prévia** abre a aba **Avançado → Inventário** para inspecionar a mesma tabela paginada. O botão de salvar só é habilitado após prévia válida, sem erros, e da pasta ainda selecionada.
- **Salvar** continua mostrando o diálogo de confirmação explícita do caminho, número de arquivos e banco SQLite, e o backend continua verificando a pasta novamente antes de persistir o snapshot. Após salvar, segue o fluxo já implementado de abertura da **Biblioteca** com seleção do ID exato e limpeza dos filtros.
- Criada `can_save_inventory_preview()` em `gui_helpers.py`, reutilizada por botões, navegação e validação antes da confirmação; mudança de pasta e início de tarefa desabilitam salvamento enquanto a prévia não é válida.
- Adicionados **5 testes puros** em `tests/test_home_catalog.py` e **3 testes estruturais** à suíte da GUI; **166 testes esperados** (152 homologados anteriormente + 6 da navegação pós-catalogação + 8 desta etapa). A navegação anterior recebeu aprovação **visual** do usuário, mas não foi informada execução explícita da suíte de 158 testes.
- Mudança somente no fluxo visual e gravação **consentida do catálogo SQLite**, que já existia. Nenhuma alteração em mídias, nenhuma movimentação/cópia pelo Ollama e nenhum uso do executor experimental da área `tests/.runtime`.
- **Pendente:** rodar os 166 testes no Windows e conferir visualmente os novos botões do Início, inclusive prévia válida/inválida, mudança de pasta e confirmação de gravação.

## Próxima etapa

No Windows, atualizar `main` e executar `python -m unittest discover -s tests -v` (**166 testes esperados**, 1 historicamente ignorado). Depois, abrir `archivia-gui` e testar exclusivamente o novo fluxo `Início → Examinar pasta para catalogar → Conferir prévia → Salvar no catálogo SQLite`. Confirmar que a prévia inválida impede salvamento e que o snapshot salvo abre na Biblioteca. Não utilizar a ferramenta experimental de movimentação em arquivos reais.

## Referências

- [Escopo mínimo e decisões de produto](SCOPE.md)
- [Arquitetura e limites de segurança](ARCHITECTURE.md)
- [Contrato Ollama](AGENT.md)
- [Interface de homologação](GUI.md)
- [Perfis futuros](EDITIONS.md)
- [Testes e fixtures](../tests/README.md)
