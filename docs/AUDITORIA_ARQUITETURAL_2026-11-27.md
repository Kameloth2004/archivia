# ArchivIA — Auditoria arquitetural inicial (27/11/2026)

> **Escopo e evidência:** revisão estática da árvore da branch `main` e leitura de módulos-chave em 27/11/2026. Não é uma auditoria exaustiva de todas as linhas, nem prova de cobertura dos testes ou de segurança da execução real. A análise foi registrada em branch de documentação, sem refatorar o motor.

## Resumo executivo

O projeto passou de inventário e simulação para **movimentação supervisionada na interface**, conforme o código presente em `gui.py`, `gui_worker.py`, `move_executor.py`, `batch_move.py` e `queue_move.py`. A documentação de estado anterior ainda descreve em trechos a movimentação real como indisponível. Corrigir essa divergência é prioritário: o software altera o sistema de arquivos e seus fluxos precisam ser tratados como operações potencialmente destrutivas.

A maior duplicidade **confirmada por leitura do código** é `batch_move.py` versus `queue_move.py`: ambos validam autorização, plano completo, seleção, percorrem arquivos e chamam `move_one_approved()`, com limites e cancelamento diferentes. **Não fundir sem testes de regressão**.

## Matriz de responsabilidades / possíveis sobreposições

| Área | Módulos | Diagnóstico | Ação recomendada |
|---|---|---|---|
| Inventário e catálogo | `inventory.py`, `cataloging.py`, `catalog.py` | Responsabilidades complementares (varredura, persistência, consultas); possível redundância de leitura ainda não demonstrada | Manter fronteiras e testar contratos |
| Planejamento | `planner.py`, `recursive_plan.py`, `preview.py` | Vários formatos de prévia para objetivos diferentes | Inventariar schemas e definir interface canônica de plano, mantendo adaptadores |
| Operações em lote | `batch_move.py`, `queue_move.py` | **Repetição concreta** de validação e loop; diferença deliberada: 20 arquivos vs 10.000 e interrupção cooperativa na fila | Extrair núcleo comum em etapa própria; preservar limites, mensagens, interrupção e retorno |
| Movimento | `executor.py`, `move_pipeline.py`, `move_executor.py` | Existência de implementações históricas e de teste vs executor supervisionado atual; equivalência de segurança **não comprovada** | Mapear consumidores, marcar explicitamente TEST-ONLY, evitar mover helpers privados sem auditoria |
| Cópias | `manual_pilot.py`, `manual_copy.py`, `verified_copy.py`, `copy_test.py` | Repetição aparente de hash, temporários, publicação e journal, mas escopos distintos | Elaborar matriz de garantia antes de extrair funções de baixo nível |
| Conflitos e duplicatas | `duplicates.py`, `duplicate_sessions.py`, `conflict_hash.py`, `conflict_report.py` | Possível sobreposição terminológica (nome igual não implica conteúdo igual); sem prova de duplicação indevida | Unificar vocabulário e casos de teste, não os algoritmos por conveniência |
| Orquestração GUI | `gui.py` (~2.310 linhas), `gui_worker.py`, `gui_helpers.py`, `gui_presentation.py`, `gui_tables.py`, `table_rows.py` | `gui.py` ainda concentra muitas telas, estado e handlers; separações auxiliares já existem | Extrair por tela/fluxo, gradualmente, mantendo sinais e testes |
| Ollama e sessão | `agent.py`, `plan_memory.py` | IA consulta/planeja; executor acionado por GUI, não como ferramenta do modelo | Preservar separação de autorização; auditar invalidação de sessão e plano |

## Riscos e inconsistências prioritárias

1. **Documentação obsoleta:** `docs/STATUS.md` foi atualizado historicamente em seções sucessivas; sua conclusão ainda aponta 198 testes e afirma indisponibilidade de movimentação, embora a árvore atual contenha executores e handlers de movimentação supervisionada. Não usar esse número como total atual.
2. **Coexistência de dois lotes:** `move_batch_approved()` e `move_queue_approved()` oferecem semântica semelhante com diferenças em limite e cancelamento. Risco de corrigir um e esquecer outro.
3. **Múltiplos protocolos de journal:** módulos de cópia/movimento produzem registros específicos. Antes de compartilhar implementação, verificar compatibilidade de recuperação, durabilidade e casos de falha.
4. **Segurança em operações reais:** a presença de SHA-256, `fsync`, validações e publicação sem sobrescrita não prova ausência de condições de corrida, recuperação após falhas de energia nem conservação de ACL/metadados. A revisão completa das transições que podem remover a origem é obrigatória.
5. **Estado da GUI:** `QueryWorker` recebe grande número de parâmetros e seleciona ações por strings de modo; o crescimento torna difícil verificar combinações inválidas. Recomenda-se tipar solicitações em etapa posterior.
6. **Planos parciais e conflitos:** o planejamento deve distinguir, em todos os fluxos, `pending`, `blocked`, `complete` e colisão de nome versus duplicação confirmada por hash.
7. **Contagem dos testes:** referências em documentos a resultados passados são históricas; a revisão remota não executou `unittest` no Windows.

## Recomendações em ordem de execução

**Fase 0 — documentar e congelar contratos.** Registrar fluxos atuais, limites, strings de aprovação, estados de journal e consumidores; criar mapa de risco; revisar textos antigos e a tela de ajuda para impedir interpretação errônea de simulação/execução.

**Fase 1 — caracterização por testes.** Cobrir os dois lotes com os mesmos cenários de sucesso, bloqueio seguro, erro crítico, interrupção, mudança no plano/snapshot, destino ocupado e falha depois da publicação. Separar testes em fixtures descartáveis.

**Fase 2 — deduplicar lote/fila.** Introduzir motor sequencial comum para validação e despacho; adaptadores continuam preservando limite de 20, limite de 10.000, callback de interrupção e nomes de retorno. Nenhuma ampliação de permissões.

**Fase 3 — auditar execução/cópia.** Documentar e comparar invariantes de cada módulo; extrair somente utilitários comprovadamente equivalentes (por exemplo, leitura de hash) sem alterar semântica de journal e exclusão. Exigir cenários de falha e recuperação.

**Fase 4 — modularizar a interface.** Separar tela inicial/organização, biblioteca, inventário, avançado e configurações de acordo com responsabilidades. Evitar refatoração simultânea com alterações de fluxo de movimentação.

**Fase 5 — limpeza dirigida.** Remover implementações históricas apenas após análise de importações, testes de cobertura e decisão explícita sobre compatibilidade e retenção de fixtures.

## Critérios de aceite para cada refatoração

- Nenhuma execução por Ollama e nenhuma mudança tácita de permissões;
- prévia e aprovação explícita continuam necessárias;
- sem sobrescrita e com verificação de integridade;
- comportamento de interrupção e de falha idêntico ao anterior;
- alteração em arquivo real somente no caminho supervisionado e deliberado;
- testes de unidade/integração no Windows, além de homologação visual quando a GUI mudar;
- documentação atualizada no mesmo PR que a alteração.

## Arquivos relacionados

- [Fluxos e recursos recentes](FUNCIONALIDADES_ATUAIS_2026-11-27.md)
- [Estado anterior / registro histórico](STATUS.md)
- [Arquitetura](ARCHITECTURE.md)
- [Interface](GUI.md)
- [Política de testes](../tests/README.md)
