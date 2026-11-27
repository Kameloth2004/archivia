# ArchivIA — Inventário funcional e contratos recentes (27/11/2026)

> **Fonte:** inspeção estática da branch `main` em 27/11/2026, complementada por homologações relatadas pelo usuário. Esta lista descreve **caminhos presentes no código**, não certifica que todas as operações tenham sido testadas com arquivos reais. Não confundir registro histórico de `STATUS.md` com situação atual.

## Fluxo principal

1. **Selecionar origem** na interface.
2. **Analisar arquivos**: varredura da origem (com opção de incluir/excluir subpastas), sessão local de catálogo; inventário não significa mover arquivos.
3. **Selecionar destino e tipo** de mídia para organizar.
4. **Preparar prévia** de consolidação: ações propostas, bloqueios, pendências, estado completo/incompleto; conflitos de nome não são provas de duplicata de bytes.
5. **Revisar ações e bloqueios**; existem caminhos de verificação de conflito por SHA-256 e sugestão de nome alternativo, dependendo do fluxo.
6. **Autorizar execução supervisionada pela interface**, quando os requisitos do executor são cumpridos. O código contempla ação unitária, lote pequeno e fila maior, com diferentes limites; operações já concluídas em lote não têm rollback automático.
7. **Receber progresso/resultado e reanalisar** antes de operar novamente em uma pasta cujo conteúdo mudou.

## Funcionalidades por camada

| Camada | Funções / pontos de entrada | Observação |
|---|---|---|
| Inventário | `inventory.py`, `cataloging.py`, `catalog.py` | Classificação baseada em extensão/metadados; SQLite persistente ou temporário conforme fluxo |
| Busca e biblioteca | `catalog.py`, `gui.py`, `table_rows.py` | Consultas paginadas, filtros e histórico de snapshots |
| Agente local | `agent.py`, `plan_memory.py` | Ferramentas de consulta, planejamento e explicação de bloqueios; não confundir prompt com autorização de execução |
| Planejamento | `planner.py`, `recursive_plan.py` | Simulações de organização cronológica e consolidação; prévia parcial não autoriza lote |
| Duplicatas/conflitos | `duplicates.py`, `duplicate_sessions.py`, `conflict_hash.py`, `conflict_report.py` | SHA-256 para conteúdo, conflito de nome e relatórios são conceitos diferentes |
| Execução unitária | `move_executor.py:move_one_approved` | Exige plano completo do snapshot e aprovação literal `MOVER UM ARQUIVO`; revalida antes de executar |
| Lote pequeno | `batch_move.py:move_batch_approved` | Até **20** seleções; sequencial, interrompe falhas críticas, não faz rollback |
| Fila | `queue_move.py:move_queue_approved` | Até **10.000** seleções; sinal cooperativo de interrupção antes do próximo arquivo, não faz rollback |
| GUI de organização | `gui.py`, `gui_worker.py` | Handlers atuais incluem preparação, aprovação de arquivo, conflito, lote, fila e parada |
| Experimentos de cópia/movimento | `manual_copy.py`, `manual_pilot.py`, `verified_copy.py`, `move_pipeline.py`, `executor.py`, `copy_test.py` | Não assumir que todas essas rotas são caminhos de produção. Verificar escopo e consumidores antes de consolidar |
| Aparência | `gui_icons.py`, `gui_theme.py`, `gui_tables.py` | Biblioteca de ícones e helpers Qt separada; a GUI principal ainda monta os widgets |

## Contratos relevantes e ressalvas

- **`mode=simulation` e `executable=false`** caracterizam a **origem de um plano**; não significam, isoladamente, que o programa inteiro não tenha executor. O executor supervisionado avalia o plano e requer uma aprovação separada.
- **`complete=true` e `pending=0`** são pré-condições no executor; não basta aparecerem ações propostas em uma prévia parcial.
- **`destino_ja_existe`** significa conflito de nome. Só SHA-256 efetivamente comparado permite falar de igualdade de bytes.
- **Lotes não são transações.** Uma falha posterior não desfaz movimentos anteriores. A fila permite interrupção entre arquivos, não necessariamente durante a movimentação unitária.
- **Ollama não deve iniciar movimentações.** A fronteira entre o planejamento pela IA e a aprovação humana pela GUI é parte do contrato de segurança.
- **Ícones e layout:** a biblioteca `gui_icons.py` existe; resultados visuais específicos dependem de aplicação nos widgets e homologação da tela, não apenas de ter o módulo no projeto.

## Verificações pendentes

- Executar suíte completa `python -m unittest discover -s tests -v` após atualização da branch, registrar contagem real e falhas/ignorado.
- Revisar visualmente a organização compacta, caminhos de origem/destino, botões de ações, ícones, paginação, feedback de bloqueios e cancelamento.
- Verificar todas as importações/consumidores dos módulos históricos e os efeitos de logs/temporários no destino.
- Validar no Windows operações apenas com **arquivos descartáveis** em ambiente controlado, incluindo casos de conflito, erro e recuperação; não inferir segurança para a única cópia de mídia pessoal a partir de um teste de sucesso.

## Critério para novas funcionalidades

Antes de adicionar recurso semelhante a um existente, identificar: (1) função atual equivalente; (2) contrato/safety boundary; (3) ponto único de reutilização; (4) testes de regressão; (5) atualização dos documentos. Preferir evoluir o fluxo de organização existente em vez de criar um terceiro motor de lote ou cópia.
