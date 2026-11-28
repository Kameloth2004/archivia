# Arquitetura consultiva e índice integral de funções — ArchivIA V2

**Data da coleta:** 28/11/2026  
**Repositório:** `Kameloth2004/archivia`  
**Branch analisada:** `feat/v2-video-thumbnails-2026-11-27`  
**Commit fixado:** `2afb6c97edff83cadd013136ea1573ee3b66aaf9`  
**Método:** leitura integral dos arquivos Python do GitHub, identificação de declarações `def`, `async def`, classes e níveis de indentação, com número de linha e resumo por docstring (quando presente) ou inferência nominal. Não foram executados testes nem inspecionados arquivos pessoais nesta tarefa.

## Escopo e índices

A árvore examinada contém **100 arquivos Python**, dos quais **49 em `src/` e 51 em `tests/`**. O catálogo abaixo contém **752 definições de funções/métodos**, incluindo funções internas, métodos especiais, funções auxiliares, testes, fixtures e simulações (**300 na produção, 452 em testes**). Esses números representam **declarações estáticas**, não o número de casos que `unittest` executará. Classes sem métodos declarados podem não aumentar a contagem.

### Catálogo de produção

1. [Funções de produção — parte 1](V2_FUNCOES_PRODUCAO_PARTE_1_2026-11-28.md) — `src/archivia/__init__.py` a `src/archivia/gui.py`; 17 arquivos, **124 definições**.
2. [Funções de produção — parte 2](V2_FUNCOES_PRODUCAO_PARTE_2_2026-11-28.md) — módulos seguintes de GUI, navegação, imagens, vídeo e afins; 17 arquivos, **120 definições**.
3. [Funções de produção — parte 3](V2_FUNCOES_PRODUCAO_PARTE_3_2026-11-28.md) — módulos finais de metadados, movimentação, planejamento e cópia; 15 arquivos, **56 definições**.

### Catálogo de testes, fixtures e simulações

4. [Testes e simulações — parte 1](V2_FUNCOES_TESTES_PARTE_1_2026-11-28.md) — 17 arquivos, **160 definições**.
5. [Testes e simulações — parte 2](V2_FUNCOES_TESTES_PARTE_2_2026-11-28.md) — 17 arquivos, **143 definições**.
6. [Testes e simulações — parte 3](V2_FUNCOES_TESTES_PARTE_3_2026-11-28.md) — 17 arquivos, **149 definições**.

Cada documento organiza **por caminho de arquivo**, apresenta **linha original**, **função/método** (incluindo classe quando presente) e **descrição**. A etiqueta **[DOC]** recupera a primeira linha da docstring; **[INFERÊNCIA]** expressa apenas a finalidade sugerida pelo nome. Não trate inferências como contrato de comportamento ou prova de ausência de efeitos colaterais.

## 1. Fluxo operacional — visão de referência

```text
Interface PySide6 / CLI
         |
         +----> Inventário (inventory.py) ----> catálogo SQLite (catalog.py)
         |                                          |
         |                                          +--> consultas, buscas, filtros
         |
         +----> Análise de conteúdo e metadados (metadata/)
         |
         +----> Planejamento sem movimentação
         |         planner.py / recursive_plan.py
         |         preview.py / plan_memory.py / conflict_report.py
         |
         +----> Aprovação explícita da interface
         |         batch_move.py / queue_move.py
         |                         |
         |                         v
         |                move_executor.py
         |                         |
         |                         v
         |              verificações + journal
         |
         +----> Visualização de mídia (somente leitura)
                   gui_explorer.py / gui_viewer.py
                   image_decode.py / gui_video.py / video_thumbnails.py

Agente Ollama (agent.py): ferramentas nomeadas por allowlist,
sem execução direta de código gerado, shell ou movimentação autorizada.
```

Este é um **mapa conceitual de responsabilidades**, não um diagrama de chamadas exaustivo.

## 2. Responsabilidades arquiteturais por domínio

| Domínio | Módulos principais | Responsabilidade | Atenção |
|---|---|---|---|
| Inventário | `inventory.py`, `cataloging.py` | Classificar arquivos por extensão, percorrer escopo, extrair informações do sistema | Evitar seguir links e modificar origem |
| Persistência | `catalog.py`, `cataloging.py` | Registrar snapshots e consultar catálogo SQLite | Escrita no banco não significa movimentação da mídia |
| Busca/consulta | `catalog.py`, `duplicates.py`, `duplicate_sessions.py` | Buscar, filtrar, comparar e identificar possíveis duplicidades | Nome igual não prova conteúdo igual |
| Planejamento | `planner.py`, `recursive_plan.py`, `plan_memory.py`, `preview.py` | Gerar propostas, resumos e páginas de prévia | Proposta é distinta de autorização |
| Conflitos | `conflict_hash.py`, `conflict_report.py` | Identificar conflitos e apoiar comparações/verificações | Distinguir colisão de nome e equivalência SHA-256 |
| Execução supervisionada | `move_executor.py`, `batch_move.py`, `queue_move.py`, `move_pipeline.py` | Coordenação de ações aprovadas e relatórios de resultados | Risco real de alteração em disco: revisar permissões, destino e tratamento de erro |
| Pilotos e cópia | `manual_pilot.py`, `manual_copy.py`, `copy_test.py`, `verified_copy.py` | Protótipos, etapas preparatórias e rotinas de cópia validada | Nem todo arquivo com `test` no nome é teste unittest; verificar escopo permitido |
| Agente local | `agent.py` | Interpretar pedidos e despachar ferramentas permitidas | Ollama não recebe shell nem poder implícito de executar movimentação |
| Interface | `gui.py`, `gui_navigation.py`, `gui_sidebar.py`, `gui_worker.py`, demais `gui_*.py` | Apresentação, navegação, widgets, controle do estado e tarefas | Manter operações custosas fora da thread da interface |
| Metadados | `metadata/reader.py`, `metadata/exiftool_adapter.py`, `metadata/xmp_reader.py` | Ler e formatar propriedades técnicas, EXIF e XMP | Limites e integridade ao interpretar dados externos |
| Imagens | `image_decode.py`, `gui_viewer.py`, `gui_explorer.py` | Decodificar e exibir miniaturas e prévias, incluindo fallback | Decodificação não deve sobrescrever o arquivo |
| Vídeos | `gui_video.py`, `video_thumbnails.py` | Reprodutor manual e extração de quadros em fila | Codec/FFmpeg, timeout, consumo e ciclo de vida dos recursos |
| Entrada e saída | `cli.py`, `__main__.py`, `date_formats.py`, `table_rows.py` | Comandos e transformações auxiliares | Separar apresentação de regras de negócio |

## 3. Funções particularmente importantes para compreender o projeto

| Função | Arquivo | Papel |
|---|---|---|
| `inventory()` | `inventory.py` | Inventariar arquivos e categorias; não é executor de mudanças |
| `store_inventory()` | `catalog.py` | Persistir resultado de inventário como snapshot no SQLite |
| `scan_for_folder()` | `catalog.py` | Consultar o snapshot correspondente à pasta |
| `query_catalog()` e `query_catalog_page()` | `catalog.py` | Consultar e paginar arquivos do catálogo |
| `catalog_summary()` | `catalog.py` | Resumo quantitativo do catálogo |
| `propose_recursive_consolidation()` | `recursive_plan.py` | Planejar consolidação recursiva em modo somente leitura |
| `latest_recursive_plan()` | `plan_memory.py` | Recuperar memória efêmera do último plano |
| `blocked_details()` | `plan_memory.py` | Explicar bloqueios identificados no plano |
| `preview_conflict_move()` | `move_executor.py` | Prévia da possibilidade de ação diante de conflitos |
| `move_one_approved()` | `move_executor.py` | Unidade executora supervisionada; **pode modificar arquivos** |
| `move_queue_approved()` | `queue_move.py` | Processar fila de ações autorizadas; **pode modificar arquivos** |
| `preview_manual_copy()` | `manual_pilot.py` | Preparação de cópia piloto, não executa remoção da origem |
| `prepare_manual_copy()` | `manual_pilot.py` | Preparar cópia piloto com frase explícita de aprovação |
| `copy_verified_test_file()` | `verified_copy.py` | Cópia experimental **TEST-ONLY** sem remover origem |
| `dispatch_tool()` | `agent.py` | Despachar chamadas à lista permitida de ferramentas do agente |
| `ask_agent()` | `agent.py` | Conversar com Ollama usando ferramentas permitidas |
| `ask_agent_for_folder()` | `agent.py` | Conversar com agente no contexto de uma pasta |
| `decode_preview()` | `image_decode.py` | Gerar imagem visualizável com fallback de decodificador |
| `VideoThumbnailService.request()` | `video_thumbnails.py` | Pedir quadro de miniatura sem gravar no acervo |
| `LocalVideoPlayer.open_local()` | `gui_video.py` | Preparar vídeo no player, sem iniciar reprodução automaticamente |
| `main()` | `cli.py` | Ponto de entrada dos comandos CLI |

**Nota:** os nomes e responsabilidades acima são um resumo de arquitetura. Os catálogos detalhados trazem o conjunto integral de declarações; módulos com múltiplos procedimentos internos não foram reduzidos a essas funções-chave.

## 4. Simulações e testes: como interpretá-los

O projeto emprega termos próximos, mas que não são equivalentes:

- **Prévia, simulação e plano:** descrevem ações propostas; devem manter distinção entre `proposed`, `blocked` e executado.
- **Teste `test_*`:** caso automatizado de `unittest`; pode operar sobre fixtures temporárias para provar segurança, erros e resultados.
- **Fixture/helper:** prepara arquivos e estados artificiais, cria mocks e realiza limpeza; não é recurso normal da interface.
- **Piloto experimental:** módulo de produção limitado a ambientes controlados, que pode efetivamente criar arquivos de teste; não deve ser aplicado a dados reais sem rever restrições.
- **Executor aprovado:** código que pode alterar arquivos mediante autorização, sujeito a verificações. Seu nome não o transforma em simulação.

Verificar `tests/support.py` e `tests/generate_sha256_paged_demo.py` ao analisar a criação de fixtures, execução de simulações e organização de diretórios de teste. Para as rotinas de teste de operações de arquivo, conferir especialmente os cenários em `test_move_executor.py`, `test_queue_move.py`, `test_batch_move.py`, `test_verified_copy.py`, `test_recursive_plan.py` e `test_duplicate_basename_queue_v2.py`.

## 5. Uso recomendado deste catálogo

Ao investigar um comportamento, consultar nesta ordem:

1. O **mapa de domínio** acima para localizar a responsabilidade.
2. O **arquivo/método** exato em uma das seis partes, junto da linha.
3. O **código-fonte e os testes relacionados** — especialmente onde a descrição está marcada `[INFERÊNCIA]`.
4. Os **contratos de segurança e aprovação** antes de alterar planners, executores ou filas.

Não considerar este catálogo como substituto de auditoria funcional linha a linha: ele é um **índice estático completo das declarações encontradas na revisão fixada**, e deve ser regenerado quando novos métodos, módulos ou testes forem adicionados.

## 6. Situação de desenvolvimento

A branch de documentação parte da branch de miniaturas de vídeo, que ainda depende das mudanças dos PRs de AVIF/JFIF e do player. **Esta documentação não deve ser incorporada diretamente à `main`** nem usada para mesclar V2 em direção inversa. Antes de integrar, verificar qual branch já contém os PRs #7, #8 e #9.
