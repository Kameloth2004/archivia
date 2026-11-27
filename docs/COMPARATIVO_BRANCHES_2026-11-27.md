# ArchivIA — Comparativo de branches e plano de integração

Data: 27/11/2026. Levantamento estático de `main` (commit `ba1afea59ac8300220193acd3be1932a58f846df`) e `develop/v2.0.0` (commit `28ed282a5fd38c83f713b06e0de41d0065ba7b8a`). A branch `refactor/shared-file-identity-2026-11-27` (HEAD `581d693`) foi analisada separadamente. **Nenhum merge de código realizado nesta avaliação.**

## Histórico e divergência

| Indicador | Valor |
|---|---|
| Merge-base | `f1bb0256fd92b130cde41acec8f3059ce9846a49` |
| Commits exclusivos V2 em relação à main | 131 |
| Commits exclusivos main em relação à V2 | 1 (squash do PR #2) |
| Commit main | `ba1afea` |
| Commit V2 | `28ed282` |
| PR #4, sobre main | `581d693` (ainda não integrado) |

Os 131 commits V2 não correspondem a 131 funcionalidades independentes. Contagem histórica não serve como estimativa de maturidade, cobertura ou estabilidade.

## Matriz por função

| Subsistema | main | V2 | Recomendação |
|---|---|---|---|
| Inventário recursivo e SQLite | Implementados | Mantidos, com rótulos de categorias | Preservar V2 |
| Categorias disponíveis para organização | Parte dos planejadores restringe mídia | `planner.ALLOWED_CATEGORIES = frozenset(CATEGORIES)`, mesmas nove categorias do inventário | Preservar V2 e testar todas as categorias |
| Planejamento recursivo | Conflitos tratados durante a iteração | Segunda passagem bloqueia **todas** as ocorrências de nomes-base iguais entre subpastas | Preservar V2, inclusive bloqueio case-insensitive |
| Executor unitário supervisionado | Nomes ambíguos geram `ValueError` | Nomes ambíguos geram `MoveSkippedError`, permitindo à fila registrar bloqueio seguro | Preservar V2 |
| Fila supervisionada | Após PR #2 usa `move_orchestration.py` | Implementação repetitiva mas acrescenta `plan_blocked`, `plan_blocked_by_reason`, `unattempted_files` | **Portar núcleo compartilhado preservando campos da V2** |
| Lote pequeno | Após PR #2 usa núcleo compartilhado | Implementação anterior, comportamento semelhante | Portar testes de contrato comparando V2 |
| Identidade stat | Helper proposto no PR #4 para 3 protótipos | Duplicação nos 3 protótipos | Portar helper isoladamente sobre V2, sem merge da main |
| GUI | Bancada de organização/consulta | Navegação lateral, explorador, visualizador e relatórios ampliados | V2 como base |
| Metadados | Inventário básico e hashes | Leitor EXIF/XMP, leitor bruto sob demanda, ExifTool opcional, Pillow opcional | Preservar isolamento somente leitura; auditar limites de dados |
| Pasta ativa | Seleção relacionada aos fluxos | `_active_folder` compartilhada na sessão | Preservar V2; testar invalidação ao trocar origem |
| Arquitetura GUI | `gui.py` ~2310 linhas | `gui.py` ~2663 linhas + `gui_explorer.py` ~726 e `gui_viewer.py` ~543 | Modulalizar por fluxo após estabilização, sem reescrita total |
| Testes | Suite de base mais PR #2 e PR #4 em branches diferentes | Suite V2 com testes adicionais de explorador, viewer, metadados e nome ambíguo | Executar suíte combinada após portar alterações |

## Incompatibilidade concreta: fila e relatórios

Na V2, `queue_move.py` acrescenta os campos de saída:
- `plan_blocked` — quantidade bloqueada previamente no planejamento;
- `plan_blocked_by_reason` — códigos de motivo;
- `unattempted_files` — itens não tentados.

O `queue_move.py` da main após PR #2 não contém esses campos. **Copiar o arquivo da main para a V2 seria regressão**, inclusive possivelmente na apresentação do resultado da interface. A abordagem segura é adaptar `move_orchestration.py` como núcleo, mantendo a assinatura e o relatório da V2.

## Incompatibilidade concreta: nomes-base repetidos

A V2 implementa:
- segunda passagem em `recursive_plan.py` para bloquear todas as ações com mesmo nome-base sem diferenciar maiúsculas/minúsculas;
- classificação de conflito ambíguo como `MoveSkippedError` em `move_executor.py`;
- `tests/test_duplicate_basename_queue_v2.py` para manter a fila processando itens independentes sem eliminar as origens bloqueadas.

**Não trazer `move_executor.py` ou `recursive_plan.py` antigos da main para V2.**

## Recursividade: contrato recomendado

A busca da origem é recursiva por padrão (`inventory(..., recursive=True)`). O planejamento pode incluir/excluir subpastas e usa caminhos relativos catalogados. O executor realiza operações unitárias em itens aprovados, com revalidações. A verificação SHA-256 e `file_identity` são **por arquivo**, não fazem varredura de diretórios. O controle de escopo não pode ser removido.

## Caminho de integração recomendado (sem fusão de branches)

1. Definir `develop/v2.0.0` como **base da próxima implementação**, preservando `main` como histórico/release até decisão formal.
2. Criar branch de trabalho **a partir de V2**, portar apenas `file_identity.py` e substituições equivalentes do PR #4; executar testes V2.
3. Em outro PR derivado de V2, portar `move_orchestration.py` e adaptar lote/fila **sem eliminar os três campos V2**; executar testes de ambas as linhas, incluindo `test_duplicate_basename_queue_v2.py` e cancelamento.
4. Auditar plugins de metadados e o visualizador quanto a leitura sob demanda, limites, links/junctions, consumo de memória e acesso a recursos externos antes de adicionar novas operações.
5. Continuar auditoria de código legado (hash/journals/execução) sobre V2; não excluir protótipos sem comparar recuperação/erros e sem cobertura.
6. Atualizar `docs/STATUS.md` e README com um estado vigente único — documentos históricos ainda descrevem operações já implementadas como futuras.

## Validação e pendências

- Usuário confirmou testes Windows aprovados para `main` refatorada (PR #2) e para HEAD `581d693` da branch PR #4; não apresentou contagem exata da última rodada.
- Não houve execução local nem testes de integração V2 + refatorações neste levantamento.
- Não existe justificativa para merge direto de `main` em V2 nem V2 em `main` neste momento.
- Prioridade é manter o comportamento supervisionado e as garantias de não sobrescrita, confirmação explícita e preservação da origem em falhas.

## Referências

- [Documentação V2](V2_UNIVERSAL_LIBRARY.md)
- [Auditoria de arquitetura anterior](ARCHITECTURE.md)
- [Testes](../tests/README.md)
- [PR #2 integrado na main](https://github.com/Kameloth2004/archivia/pull/2)
- [PR #4 isolado na main](https://github.com/Kameloth2004/archivia/pull/4)
