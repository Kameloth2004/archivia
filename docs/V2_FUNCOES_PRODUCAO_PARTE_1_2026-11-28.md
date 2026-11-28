# Catálogo de funções de produção — parte 1/3

Referência: `Kameloth2004/archivia`, branch `feat/v2-video-thumbnails-2026-11-27`, commit `2afb6c97edff83cadd013136ea1573ee3b66aaf9` (28/11/2026). **DOC** = descrição literal da primeira linha da docstring, **INFERÊNCIA** = responsabilidade inferida do nome e assinatura; nenhuma inferência certifica ausência de efeitos colaterais. Inclui métodos privados, especiais e funções aninhadas.

## `src/archivia/__init__.py`

Sem funções definidas.

## `src/archivia/__main__.py`

Sem funções definidas.

## `src/archivia/agent.py`

| Linha | Função / método | Responsabilidade |
|---:|---|---|
| 293 | `dispatch_tool()` | Responsável por dispatch tool, conforme a implementação **[INFERÊNCIA]** |
| 466 | `_ollama_chat()` | Responsável por  ollama chat, conforme a implementação **[INFERÊNCIA]** |
| 483 | `ask_agent()` | Responsável por ask agent, conforme a implementação **[INFERÊNCIA]** |
| 562 | `FolderCatalogSession.__init__()` | Responsável por   init  , conforme a implementação **[INFERÊNCIA]** |
| 573 | `FolderCatalogSession.ready()` | Responsável por ready, conforme a implementação **[INFERÊNCIA]** |
| 576 | `FolderCatalogSession.refresh()` | Substitui o catálogo após uma nova varredura sem deixar meio estado. **[DOC]** |
| 600 | `FolderCatalogSession.analyze_source()` | Analisa a origem no escopo escolhido, sem exigir destino. **[DOC]** |
| 610 | `FolderCatalogSession.prepare_recursive_plan()` | Responsável por prepare recursive plan, conforme a implementação **[INFERÊNCIA]** |
| 627 | `FolderCatalogSession.ask()` | Responsável por ask, conforme a implementação **[INFERÊNCIA]** |
| 648 | `FolderCatalogSession.close()` | Responsável por close, conforme a implementação **[INFERÊNCIA]** |
| 659 | `ask_agent_for_folder()` | Consulta uma pasta diretamente com catálogo descartável, sem salvar histórico. **[DOC]** |

## `src/archivia/batch_move.py`

| Linha | Função / método | Responsabilidade |
|---:|---|---|
| 17 | `move_batch_approved()` | Responsável por move batch approved, conforme a implementação **[INFERÊNCIA]** |

## `src/archivia/catalog.py`

| Linha | Função / método | Responsabilidade |
|---:|---|---|
| 41 | `store_inventory()` | Grava um novo snapshot somente se o inventário não registrou erros. **[DOC]** |
| 89 | `scan_for_folder()` | Seleciona o snapshot mais recente da pasta exata, sem gravar no banco. **[DOC]** |
| 118 | `query_catalog()` | Responsável por query catalog, conforme a implementação **[INFERÊNCIA]** |
| 165 | `catalog_summary()` | Resumo agregado do último snapshot, sem carregar registros individuais. **[DOC]** |
| 212 | `query_catalog_page()` | Responsável por query catalog page, conforme a implementação **[INFERÊNCIA]** |
| 235 | `validate_date()` | Responsável por validate date, conforme a implementação **[INFERÊNCIA]** |
| 258 | `escape_like()` | Responsável por escape like, conforme a implementação **[INFERÊNCIA]** |
| 350 | `list_catalog_scans()` | Histórico dos inventários gravados, sem ler a árvore de arquivos. **[DOC]** |
| 374 | `catalog_origins_summary()` | Resume somente o snapshot mais recente de cada origem (root). **[DOC]** |

## `src/archivia/cataloging.py`

| Linha | Função / método | Responsabilidade |
|---:|---|---|
| 14 | `catalog_verified_preview()` | Responsável por catalog verified preview, conforme a implementação **[INFERÊNCIA]** |

## `src/archivia/cli.py`

| Linha | Função / método | Responsabilidade |
|---:|---|---|
| 15 | `main()` | Responsável por main, conforme a implementação **[INFERÊNCIA]** |

## `src/archivia/conflict_hash.py`

| Linha | Função / método | Responsabilidade |
|---:|---|---|
| 14 | `verify_plan_conflict()` | Responsável por verify plan conflict, conforme a implementação **[INFERÊNCIA]** |
| 51 | `inconclusive()` | Responsável por inconclusive, conforme a implementação **[INFERÊNCIA]** |

## `src/archivia/conflict_report.py`

| Linha | Função / método | Responsabilidade |
|---:|---|---|
| 14 | `_suggest_unused_name()` | Somente propõe um nome; não cria nem reserva arquivos no disco. **[DOC]** |
| 25 | `conflict_resolution_report()` | Responsável por conflict resolution report, conforme a implementação **[INFERÊNCIA]** |

## `src/archivia/copy_test.py`

| Linha | Função / método | Responsabilidade |
|---:|---|---|
| 25 | `_hash_descriptor()` | Responsável por  hash descriptor, conforme a implementação **[INFERÊNCIA]** |
| 33 | `copy_verified_fixture()` | Responsável por copy verified fixture, conforme a implementação **[INFERÊNCIA]** |
| 68 | `_copy_locked()` | Responsável por  copy locked, conforme a implementação **[INFERÊNCIA]** |

## `src/archivia/date_formats.py`

| Linha | Função / método | Responsabilidade |
|---:|---|---|
| 20 | `date_input_mask()` | Máscara Qt para inserir separadores automaticamente na digitação. **[DOC]** |
| 27 | `is_empty_date_field()` | Aceita campo vazio que o QLineEdit com máscara devolve como // ou --. **[DOC]** |
| 36 | `parse_user_date()` | Converte data digitada para AAAA-MM-DD; vazio desativa filtro. **[DOC]** |
| 56 | `display_date()` | Converte data ISO para a preferência sem alterar o valor gravado. **[DOC]** |
| 64 | `display_timestamp()` | Mostra instante de modificação UTC no formato escolhido, com hora. **[DOC]** |

## `src/archivia/duplicate_sessions.py`

| Linha | Função / método | Responsabilidade |
|---:|---|---|
| 25 | `_validate_positive()` | Responsável por  validate positive, conforme a implementação **[INFERÊNCIA]** |
| 30 | `_where()` | Responsável por  where, conforme a implementação **[INFERÊNCIA]** |
| 41 | `ProgressiveDuplicateSession.__init__()` | Responsável por   init  , conforme a implementação **[INFERÊNCIA]** |
| 97 | `ProgressiveDuplicateSession.done()` | Responsável por done, conforme a implementação **[INFERÊNCIA]** |
| 100 | `ProgressiveDuplicateSession.next_batch()` | Responsável por next batch, conforme a implementação **[INFERÊNCIA]** |
| 178 | `ProgressiveDuplicateSession.summary()` | Responsável por summary, conforme a implementação **[INFERÊNCIA]** |

## `src/archivia/duplicates.py`

| Linha | Função / método | Responsabilidade |
|---:|---|---|
| 23 | `_is_symlink_component()` | Responsável por  is symlink component, conforme a implementação **[INFERÊNCIA]** |
| 30 | `_candidate_path()` | Responsável por  candidate path, conforme a implementação **[INFERÊNCIA]** |
| 45 | `_sha256_checked()` | Lê em blocos e revalida metadados; não grava nem mantém conteúdo em RAM. **[DOC]** |
| 79 | `verify_duplicate_hashes()` | Responsável por verify duplicate hashes, conforme a implementação **[INFERÊNCIA]** |
| 106 | `report()` | Responsável por report, conforme a implementação **[INFERÊNCIA]** |
| 226 | `verify_snapshot_duplicate_candidates()` | Responsável por verify snapshot duplicate candidates, conforme a implementação **[INFERÊNCIA]** |
| 262 | `report()` | Responsável por report, conforme a implementação **[INFERÊNCIA]** |

## `src/archivia/executor.py`

| Linha | Função / método | Responsabilidade |
|---:|---|---|
| 23 | `_safe_path()` | Rejeita links simbólicos e junctions inclusive em componentes ancestrais. **[DOC]** |
| 34 | `_inside_runtime()` | Responsável por  inside runtime, conforme a implementação **[INFERÊNCIA]** |
| 46 | `_record()` | Responsável por  record, conforme a implementação **[INFERÊNCIA]** |
| 60 | `_exclusive_fixture_lock()` | Bloqueio cooperativo entre processos ArchivIA no mesmo caso de teste. **[DOC]** |
| 90 | `execute_test_move()` | Responsável por execute test move, conforme a implementação **[INFERÊNCIA]** |
| 109 | `_execute_test_move_unlocked()` | Responsável por  execute test move unlocked, conforme a implementação **[INFERÊNCIA]** |
| 227 | `inspect_test_journal()` | Diagnóstico estritamente de leitura; nunca executa rollback. **[DOC]** |
| 297 | `rollback_interrupted_test_move()` | Responsável por rollback interrupted test move, conforme a implementação **[INFERÊNCIA]** |
| 310 | `_rollback_interrupted_test_move_unlocked()` | Responsável por  rollback interrupted test move unlocked, conforme a implementação **[INFERÊNCIA]** |

## `src/archivia/file_identity.py`

| Linha | Função / método | Responsabilidade |
|---:|---|---|
| 11 | `file_identity()` | Retorna (volume, inode, tamanho, mtime_ns) sem alterar os dados. **[DOC]** |

## `src/archivia/gui.py`

| Linha | Função / método | Responsabilidade |
|---:|---|---|
| 52 | `ArchivIAWindow.__init__()` | Responsável por   init  , conforme a implementação **[INFERÊNCIA]** |
| 1037 | `ArchivIAWindow._refresh_date_placeholders()` | Responsável por  refresh date placeholders, conforme a implementação **[INFERÊNCIA]** |
| 1042 | `ArchivIAWindow._change_date_format()` | Responsável por  change date format, conforme a implementação **[INFERÊNCIA]** |
| 1082 | `ArchivIAWindow._database_path()` | Responsável por  database path, conforme a implementação **[INFERÊNCIA]** |
| 1088 | `ArchivIAWindow._choose_folder()` | Responsável por  choose folder, conforme a implementação **[INFERÊNCIA]** |
| 1097 | `ArchivIAWindow._clear_active_folder()` | Descarta o contexto temporário; não apaga o catálogo SQLite salvo. **[DOC]** |
| 1103 | `ArchivIAWindow._sync_active_folder_display()` | Apresenta uma única origem comum a todas as abas. **[DOC]** |
| 1141 | `ArchivIAWindow._folder_changed()` | Troca de origem invalida análises, sem apagar snapshots persistentes. **[DOC]** |
| 1169 | `ArchivIAWindow._clear_catalog_table_for_session()` | Nunca mostrar linhas do snapshot anterior como dados da nova pasta. **[DOC]** |
| 1182 | `ArchivIAWindow._change_catalog_source()` | Responsável por  change catalog source, conforme a implementação **[INFERÊNCIA]** |
| 1191 | `ArchivIAWindow._refresh_active_catalog()` | Responsável por  refresh active catalog, conforme a implementação **[INFERÊNCIA]** |
| 1204 | `ArchivIAWindow._confirm_catalog_preview()` | Responsável por  confirm catalog preview, conforme a implementação **[INFERÊNCIA]** |
| 1242 | `ArchivIAWindow._run_inventory_preview()` | Responsável por  run inventory preview, conforme a implementação **[INFERÊNCIA]** |
| 1253 | `ArchivIAWindow._clear_preview()` | Responsável por  clear preview, conforme a implementação **[INFERÊNCIA]** |
| 1267 | `ArchivIAWindow._reset_preview_page()` | Responsável por  reset preview page, conforme a implementação **[INFERÊNCIA]** |
| 1271 | `ArchivIAWindow._previous_preview_page()` | Responsável por  previous preview page, conforme a implementação **[INFERÊNCIA]** |
| 1276 | `ArchivIAWindow._next_preview_page()` | Responsável por  next preview page, conforme a implementação **[INFERÊNCIA]** |
| 1281 | `ArchivIAWindow._show_preview_page()` | Responsável por  show preview page, conforme a implementação **[INFERÊNCIA]** |
| 1300 | `ArchivIAWindow._load_origins()` | Responsável por  load origins, conforme a implementação **[INFERÊNCIA]** |
| 1310 | `ArchivIAWindow._load_history()` | Responsável por  load history, conforme a implementação **[INFERÊNCIA]** |
| 1320 | `ArchivIAWindow._clear_catalog_search()` | Responsável por  clear catalog search, conforme a implementação **[INFERÊNCIA]** |
| 1329 | `ArchivIAWindow._reset_catalog_page()` | Responsável por  reset catalog page, conforme a implementação **[INFERÊNCIA]** |
| 1333 | `ArchivIAWindow._load_catalog_page()` | Responsável por  load catalog page, conforme a implementação **[INFERÊNCIA]** |
| 1372 | `ArchivIAWindow._previous_page()` | Responsável por  previous page, conforme a implementação **[INFERÊNCIA]** |
| 1377 | `ArchivIAWindow._next_page()` | Responsável por  next page, conforme a implementação **[INFERÊNCIA]** |
| 1382 | `ArchivIAWindow._run_summary()` | Responsável por  run summary, conforme a implementação **[INFERÊNCIA]** |
| 1392 | `ArchivIAWindow._choose_plan_destination()` | Responsável por  choose plan destination, conforme a implementação **[INFERÊNCIA]** |
| 1400 | `ArchivIAWindow._show_plan_item_detail()` | Responsável por  show plan item detail, conforme a implementação **[INFERÊNCIA]** |
| 1420 | `ArchivIAWindow._run_date_plan()` | Responsável por  run date plan, conforme a implementação **[INFERÊNCIA]** |
| 1445 | `ArchivIAWindow._hash_mode_changed()` | Responsável por  hash mode changed, conforme a implementação **[INFERÊNCIA]** |
| 1460 | `ArchivIAWindow._update_hash_progress()` | Responsável por  update hash progress, conforme a implementação **[INFERÊNCIA]** |
| 1485 | `ArchivIAWindow._run_duplicate_hash()` | Responsável por  run duplicate hash, conforme a implementação **[INFERÊNCIA]** |
| 1512 | `ArchivIAWindow._refresh_home_analysis_label()` | Resumir o resultado no cabeçalho sem abrir automaticamente o painel. **[DOC]** |
| 1528 | `ArchivIAWindow._mirror_home_report()` | Apresenta também em Organizar o relatório do mesmo worker. **[DOC]** |
| 1532 | `ArchivIAWindow._open_document_library()` | Navega para a listagem existente, aplicando filtros somente de leitura. **[DOC]** |
| 1557 | `ArchivIAWindow._manual_copy_image()` | Responsável por  manual copy image, conforme a implementação **[INFERÊNCIA]** |
| 1601 | `ArchivIAWindow._home_view_preview()` | Responsável por  home view preview, conforme a implementação **[INFERÊNCIA]** |
| 1613 | `ArchivIAWindow._home_choose_destination()` | Responsável por  home choose destination, conforme a implementação **[INFERÊNCIA]** |
| 1621 | `ArchivIAWindow._home_count()` | Responsável por  home count, conforme a implementação **[INFERÊNCIA]** |
| 1629 | `ArchivIAWindow._home_ask()` | Responsável por  home ask, conforme a implementação **[INFERÊNCIA]** |
| 1654 | `ArchivIAWindow._session_for_folder()` | Responsável por  session for folder, conforme a implementação **[INFERÊNCIA]** |
| 1665 | `ArchivIAWindow._refresh_folder_session()` | Responsável por  refresh folder session, conforme a implementação **[INFERÊNCIA]** |
| 1677 | `ArchivIAWindow._run_agent()` | Responsável por  run agent, conforme a implementação **[INFERÊNCIA]** |
| 1702 | `ArchivIAWindow._update_move_choices()` | Responsável por  update move choices, conforme a implementação **[INFERÊNCIA]** |
| 1741 | `ArchivIAWindow._approve_one_move()` | Responsável por  approve one move, conforme a implementação **[INFERÊNCIA]** |
| 1776 | `ArchivIAWindow._change_home_scope()` | Responsável por  change home scope, conforme a implementação **[INFERÊNCIA]** |
| 1792 | `ArchivIAWindow._invalidate_home_organization()` | Novos parâmetros exigem novo planejamento e nova aprovação. **[DOC]** |
| 1807 | `ArchivIAWindow._analyze_home_source()` | Inventaria completamente a origem, sem exigir pasta de destino. **[DOC]** |
| 1821 | `ArchivIAWindow._prepare_home_organization()` | Planeja a organização em um clique, sem Ollama e sem mover arquivos. **[DOC]** |
| 1851 | `ArchivIAWindow._approve_conflict_move()` | Resolução guiada de um conflito, sem comandos técnicos ao usuário. **[DOC]** |
| 1925 | `ArchivIAWindow._approve_all_moves()` | Confirma e inicia a fila completa, sem envolver o Ollama. **[DOC]** |
| 1969 | `ArchivIAWindow._stop_move_queue()` | Responsável por  stop move queue, conforme a implementação **[INFERÊNCIA]** |
| 1977 | `ArchivIAWindow._approve_batch_move()` | Responsável por  approve batch move, conforme a implementação **[INFERÊNCIA]** |
| 2039 | `ArchivIAWindow._start_worker()` | Responsável por  start worker, conforme a implementação **[INFERÊNCIA]** |
| 2082 | `ArchivIAWindow._set_busy()` | Responsável por  set busy, conforme a implementação **[INFERÊNCIA]** |
| 2177 | `ArchivIAWindow._show_result()` | Responsável por  show result, conforme a implementação **[INFERÊNCIA]** |
| 2189 | `ArchivIAWindow._render_result()` | Responsável por  render result, conforme a implementação **[INFERÊNCIA]** |
| 2607 | `ArchivIAWindow._show_error()` | Responsável por  show error, conforme a implementação **[INFERÊNCIA]** |
| 2612 | `ArchivIAWindow._worker_done()` | Responsável por  worker done, conforme a implementação **[INFERÊNCIA]** |
| 2642 | `ArchivIAWindow.closeEvent()` | Responsável por closeEvent, conforme a implementação **[INFERÊNCIA]** |
| 2656 | `main()` | Responsável por main, conforme a implementação **[INFERÊNCIA]** |

## `src/archivia/gui_date_field.py`

| Linha | Função / método | Responsabilidade |
|---:|---|---|
| 18 | `CalendarDateEdit.__init__()` | Responsável por   init  , conforme a implementação **[INFERÊNCIA]** |
| 46 | `CalendarDateEdit.set_date_format()` | Troca formato mantendo o mesmo dia, se a data estiver válida. **[DOC]** |
| 61 | `CalendarDateEdit._show_calendar()` | Responsável por  show calendar, conforme a implementação **[INFERÊNCIA]** |
| 73 | `CalendarDateEdit._date_chosen()` | Responsável por  date chosen, conforme a implementação **[INFERÊNCIA]** |
| 81 | `CalendarDateEdit._clear_from_menu()` | Responsável por  clear from menu, conforme a implementação **[INFERÊNCIA]** |

