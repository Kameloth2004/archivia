# ArchivIA V2 — Integração da identidade compartilhada (27/11/2026)

## Objetivo

Transportar a refatoração do PR #4 (criada originalmente sobre a `main`) para a **linha V2** sem mesclar as duas branches.

## Escopo da mudança

- Novo `src/archivia/file_identity.py`, helper puro `file_identity(stat)` que retorna `(st_dev, st_ino, st_size, st_mtime_ns)`.
- `manual_copy.py`, `manual_pilot.py` e `move_pipeline.py` passam a chamar esse helper, removendo as três implementações locais literalmente equivalentes.
- `tests/test_file_identity.py` verifica contrato do helper, inventário recursivo de subpastas e `recursive=False`, além de tratamento conservador de links simbólicos (quando suportado pelo Windows).
- Nenhum código em `gui.py`, `gui_worker.py`, `agent.py`, `planner.py`, `recursive_plan.py`, `queue_move.py` ou `move_executor.py` foi alterado por esta integração.

## Invariantes preservadas

A descoberta recursiva e o planejamento continuam sob `inventory()` e `propose_recursive_consolidation()`. A função `file_identity()` não percorre diretórios e não calcula SHA-256: opera somente sobre um `os.stat_result` recebido. Hash, autorização, journaling, temporários, verificação, não sobrescrita, execução e remoção não foram modificados.

A V2 também mantém suas nove categorias, a verificação de nomes-base ambíguos entre subpastas, o explorador, os metadados EXIF/XMP e a GUI atual. **Não utilizar o código da `main` para sobrescrever esses componentes.**

## Validação

**Pendente de homologação Windows nesta branch V2 específica.** Os testes aprovados anteriormente na branch `refactor/shared-file-identity-2026-11-27` não certificam a integração V2. Executar:

```bash
git fetch origin refactor/v2-shared-file-identity-2026-11-27
git switch -c refactor/v2-shared-file-identity-2026-11-27 FETCH_HEAD
python -m unittest discover -s tests -v
```

Se a branch local já existir, não recriá-la: ajustar o comando conforme seu estado. Nunca usar acervos pessoais para testes destrutivos.

## Próxima etapa

Após homologação, integrar somente este PR em `develop/v2.0.0`. Depois portar cuidadosamente o motor compartilhado lote/fila da `main` para V2, preservando os campos V2 `plan_blocked`, `plan_blocked_by_reason`, `unattempted_files` e os testes de ambiguidade. Evitar merge direto entre as branches.

## Correção de limpeza de teste no Windows (27/11/2026)

A execução da suíte V2 relatou `Ran 343 tests ... FAILED (errors=1, skipped=2)`: `test_real_png_thumbnail_preserves_nanosecond_timestamp_in_signal` falhou **no `tearDown`**, quando `TemporaryDirectory` tentou excluir `miniatura_real.png` ainda aberta por um leitor assíncrono de miniaturas (`WinError 32`). A mudança de identidade dos arquivos não afeta o explorador; o erro é consistente com o ciclo de vida da thread do Qt.

Foi ajustado somente `tests/test_gui_explorer_v2.py`: após limpar/desativar o painel, o teste aguarda o `QThreadPool` terminar usando `waitForDone(10000)` **antes** de destruir a fixture. Se a espera exceder o limite, o teste falha explicitamente. Não se usou `ignore_errors`, não se silenciaram exceções e a implementação de produção do explorador e do executor não foi alterada.

**Pendente:** repetir o teste específico e, depois, toda a suíte na branch atualizada. A correção ainda não foi homologada no Windows.

```bash
git fetch origin refactor/v2-shared-file-identity-2026-11-27
git merge --ff-only FETCH_HEAD
python -m unittest discover -s tests -p "test_gui_explorer_v2.py" -v
python -m unittest discover -s tests -v
```
