# ArchivIA — Auditoria 2: cópia, movimento e protótipos (27/11/2026)

> **Método e limitações:** levantamento estático dos pontos de entrada, cabeçalhos, funções públicas, imports da GUI/CLI e testes selecionados na `main` após o merge de PR #2. Não houve execução de operações, revisão integral de fluxos de erro ou teste de segurança. A ausência de import nos pontos de entrada inspecionados **não prova** inexistência de outros consumidores.

## Mapa de caminhos

| Módulo | Finalidade identificada | Exposição observada | Garantia/limitação relevante | Classificação |
|---|---|---|---|---|
| `move_executor.py` | `move_one_approved()` e `preview_conflict_move()`, operação supervisionada com plano recursivo | Consumido diretamente por `gui_worker.py`; lote/fila chamam executor unitário | Exige aprovação `MOVER UM ARQUIVO` e plano completo; pode remover origem após verificações | **ATIVO / CRÍTICO** |
| `manual_copy.py` | `preview_manual_image_copy()`, `copy_manual_image_verified()` | Consumido por `gui_worker.py` | Uma imagem JPG/PNG/WebP/AVIF até 32 MiB; cópia sem remover origem; registro próprio | **ATIVO / EXPERIMENTAL NA GUI** |
| `executor.py` | `execute_test_move()`, inspeção e rollback de journal de fixture; helpers de caminho e lock | Testado por `test_executor.py`; helpers privados importados por outros protótipos e `manual_copy.py` | TEST-ONLY em `tests/.runtime`, hardlink e mesma unidade, sem GUI/CLI/Ollama | **BASE DE TESTES / DEPENDÊNCIA COMPARTILHADA** |
| `move_pipeline.py` | `move_verified_test_file()`, protótipo copy-hash-publish-remove | Testado em `test_move_pipeline.py`; sem entrada GUI/CLI encontrada | TEST-ONLY, journal próprio, sem rollback automático | **PROTÓTIPO DE SEGURANÇA** |
| `verified_copy.py` | `copy_verified_test_file()`, inspeção e reconciliação de cópia | Testado em `test_verified_copy.py`; sem entrada GUI/CLI encontrada | TEST-ONLY, preserva origem, valida plano, journal e recuperação específica | **PROTÓTIPO DE SEGURANÇA** |
| `copy_test.py` | `copy_verified_fixture()` | Nenhum consumidor GUI/CLI observado neste levantamento | TEST-ONLY, origem preservada, escopo de fixture | **LEGADO CANDIDATO A REVISÃO** |
| `manual_pilot.py` | `preview_manual_copy()`, `prepare_manual_copy()` | Nenhum consumidor GUI/CLI observado neste levantamento | Preparação experimental, sem remover origem, limite próprio de 50 MiB | **PILOTO CANDIDATO A REVISÃO** |
| `batch_move.py` e `queue_move.py` | Adaptadores de lote/fila para `move_one_approved()` | Consumidos por `gui_worker.py` | Já usam `move_orchestration.py` após PR #2; limites e cancelamento distintos | **ATIVOS / RECÉM-CONSOLIDADOS** |

## Duplicações confirmadas por inspeção de funções

1. **Leitura/hash de arquivo:** `_identity()` e `_digest()` aparecem em `manual_copy.py` e `move_pipeline.py`; `manual_pilot.py` contém `_file_identity()` e `_read_hash()`; `verified_copy.py` usa `_fingerprint()`. Sem equivalência comprovada: alguns métodos também copiam ou impõem tamanhos máximos.
2. **Journals JSONL com `fsync`:** `executor.py:_record()`, `manual_copy.py:_record()`, `manual_pilot.py:_journal()`, `verified_copy.py:_journal()` e `move_pipeline.py:_event()`. Eventos, campos, caminhos, exclusividade e recuperação divergem. **Não consolidar antes de tabelar schemas e falhas.**
3. **Publicação de arquivos verificados:** os protótipos compartilham padrões de temporário no destino, SHA-256, publicação sem sobrescrita e limpeza defensiva, mas com precondições distintas. Unificar um protocolo incompleto pode reduzir segurança.
4. **Validação de caminhos e de plano:** `executor.py` fornece `_safe_path()` e `_inside_runtime()`, já utilizados em outros módulos; `move_executor.py` trabalha com validação ligada ao snapshot recursivo. A equivalência funcional não foi estabelecida.

## Dependências que impedem exclusão ingênua

- **`executor.py` não pode ser apagado** enquanto `manual_copy.py`, `verified_copy.py`, `move_pipeline.py` e `copy_test.py` importarem seus helpers.
- **`move_executor.py` é central** para movimentação unitária, lote e fila; nenhuma limpeza dos protótipos deve alterar suas APIs ou política de aprovação.
- O teste `test_executor.py` exercita journal e rollback de fixture; `test_verified_copy.py` exercita inspeção/reconciliação; `test_move_pipeline.py` exercita movimento de fixture; `test_manual_copy.py` exercita cópia da GUI. Apagar esses módulos sem substituto remove evidências de testes de segurança.
- `manual_pilot.py` e `copy_test.py` precisam de busca completa de referências (incluindo docs e testes indiretos) antes de qualquer decisão de remoção.

## Proposta de destino arquitetural (NÃO IMPLEMENTADA)

1. **Motor ativo único de movimentação:** `move_executor.py` permanece a referência de execução aprovada; `move_orchestration.py` organiza lote/fila, sem implementar operações de arquivo.
2. **Cópia manual conservadora:** manter `manual_copy.py` isolado e identificado como experimento; não confundir com mover ou com duplicata confirmada.
3. **Laboratório:** manter `executor.py`, `verified_copy.py`, `move_pipeline.py` e `copy_test.py` como experimentos identificados; avaliar depois separação de `src/` e `tests/` respeitando imports e compatibilidade.
4. **Pilotos anteriores:** antes de descartar `manual_pilot.py`, documentar por que surgiu, seus contratos exclusivos (tamanho e raiz) e qual teste cobre seus cenários.
5. **Utilitários comuns:** somente após comparar semântica em testes de contrato, extrair funções puras de identidade/hash/caminho. Não compartilhar automaticamente `journal`, `unlink` ou etapas de publicação entre protocolos de risco diferente.

## Riscos de segurança a testar antes de ampliar a execução

- Substituição da origem ou destino por processo externo entre validação, hash, publicação e remoção (TOCTOU).
- Falha depois de publicar destino e antes/depois de remover origem, incluindo estado de journal.
- Queda de energia e sincronização do diretório, especialmente entre volumes.
- Arquivos em uso, junctions/reparse points no Windows, caminhos longos e diferenças case-insensitive.
- Recuperação e reconciliação idempotentes; nunca assumir rollback transacional de lote/fila.
- Preservação de timestamps, atributos, ACLs e erros de cópia parcial.

## Plano incremental

**A. Matriz de contratos:** documentar para cada implementação pré-condições, limite de bytes, volume, evento de journal, pós-condições e recuperação; elaborar testes de regressão sem mídia pessoal.

**B. Rastreio de dependências:** buscar imports por arquivo no repositório completo, distinguindo testes, GUI, CLI e ferramentas Ollama. Marcar protótipos não integrados em docs sem excluir código.

**C. Extração mínima:** começar somente por helpers puros equivalentes depois de testes de caracterização; mudanças em journal e exclusão ficam para revisão dedicada.

**D. Migração/limpeza:** proposta separada para retirada de legado, demonstrando ausência de consumidores e substituição de cenários de teste. Uma alteração por PR.

## Status de validação

- **PR #2:** usuário relatou que todos os testes executados no Windows passaram; integração em `main` confirmada no commit `ba1afea59ac8300220193acd3be1932a58f846df`.
- **Esta auditoria:** apenas documentação; nenhuma alteração operacional, nenhum teste novo executado.
- **Conclusão:** existe repetição de padrões técnicos, mas ainda **não há justificativa para remover automaticamente** os executores experimentais.
