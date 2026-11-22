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
- Dois testes de sessão acrescentados (reutilização, atualização e erro). **94 testes esperados** (92 anteriores + 2), um possivelmente ignorado. A execução no Windows ainda está pendente.
- Nenhum banco permanente, nova dependência, módulo ou executor de arquivos foi criado.

## Próxima etapa

Executar **94 testes** no Windows. Depois homologar duas consultas ao Ollama na mesma origem sem nova varredura e, após alterar uma fixture, usar **Atualizar análise da pasta** para confirmar a nova contagem. O catálogo da sessão é um snapshot por definição: para acervo alterado externamente a atualização é explícita, não automática.

## Referências

- [Escopo mínimo e decisões de produto](SCOPE.md)
- [Arquitetura e limites de segurança](ARCHITECTURE.md)
- [Contrato Ollama](AGENT.md)
- [Interface de homologação](GUI.md)
- [Perfis futuros](EDITIONS.md)
- [Testes e fixtures](../tests/README.md)
