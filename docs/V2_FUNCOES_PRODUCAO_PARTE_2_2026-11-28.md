# Catálogo de funções de produção — parte 2/3

Referência: `Kameloth2004/archivia`, branch `feat/v2-video-thumbnails-2026-11-27`, commit `2afb6c97edff83cadd013136ea1573ee3b66aaf9` (28/11/2026). **DOC** = descrição literal da primeira linha da docstring, **INFERÊNCIA** = responsabilidade inferida do nome e assinatura; nenhuma inferência certifica ausência de efeitos colaterais. Inclui métodos privados, especiais e funções aninhadas.

## `src/archivia/gui_date_picker.py`

| Linha | Função / método | Responsabilidade |
|---:|---|---|
| 26 | `CalendarDateEdit.__init__()` | Responsável por   init  , conforme a implementação **[INFERÊNCIA]** |
| 67 | `CalendarDateEdit.set_date_format()` | Atualiza somente a apresentação; o chamador converte o dia atual. **[DOC]** |
| 75 | `CalendarDateEdit._show_calendar()` | Responsável por  show calendar, conforme a implementação **[INFERÊNCIA]** |
| 94 | `CalendarDateEdit._select_date()` | Responsável por  select date, conforme a implementação **[INFERÊNCIA]** |
| 103 | `CalendarDateEdit._select_today()` | Responsável por  select today, conforme a implementação **[INFERÊNCIA]** |
| 106 | `CalendarDateEdit._clear_date()` | Responsável por  clear date, conforme a implementação **[INFERÊNCIA]** |

## `src/archivia/gui_expanding_report.py`

| Linha | Função / método | Responsabilidade |
|---:|---|---|
| 20 | `ExpandingReport.__init__()` | Responsável por   init  , conforme a implementação **[INFERÊNCIA]** |
| 31 | `ExpandingReport._update_height()` | Mede o texto em pixels, inclusive linhas quebradas pela largura. **[DOC]** |
| 57 | `ExpandingReport.showEvent()` | Responsável por showEvent, conforme a implementação **[INFERÊNCIA]** |
| 61 | `ExpandingReport.resizeEvent()` | Responsável por resizeEvent, conforme a implementação **[INFERÊNCIA]** |

## `src/archivia/gui_explorer.py`

| Linha | Função / método | Responsabilidade |
|---:|---|---|
| 40 | `_junction()` | Responsável por  junction, conforme a implementação **[INFERÊNCIA]** |
| 44 | `safe_directory()` | Somente pastas reais dentro da origem, sem symlinks/junctions. **[DOC]** |
| 82 | `_ThumbnailTask.__init__()` | Responsável por   init  , conforme a implementação **[INFERÊNCIA]** |
| 91 | `_ThumbnailTask.run()` | Responsável por run, conforme a implementação **[INFERÊNCIA]** |
| 115 | `_MetadataTask.__init__()` | Responsável por   init  , conforme a implementação **[INFERÊNCIA]** |
| 124 | `_MetadataTask.run()` | Responsável por run, conforme a implementação **[INFERÊNCIA]** |
| 146 | `ExplorerPanel.__init__()` | Responsável por   init  , conforme a implementação **[INFERÊNCIA]** |
| 310 | `ExplorerPanel.active_root()` | Responsável por active root, conforme a implementação **[INFERÊNCIA]** |
| 314 | `ExplorerPanel.current_directory()` | Responsável por current directory, conforme a implementação **[INFERÊNCIA]** |
| 317 | `ExplorerPanel.set_active_folder()` | Uma troca de origem descarta arquivos/miniaturas da pasta anterior. **[DOC]** |
| 349 | `ExplorerPanel._tree_clicked()` | Responsável por  tree clicked, conforme a implementação **[INFERÊNCIA]** |
| 354 | `ExplorerPanel._open_directory()` | Responsável por  open directory, conforme a implementação **[INFERÊNCIA]** |
| 382 | `ExplorerPanel._close_cursor()` | Responsável por  close cursor, conforme a implementação **[INFERÊNCIA]** |
| 388 | `ExplorerPanel._append_batch()` | Responsável por  append batch, conforme a implementação **[INFERÊNCIA]** |
| 444 | `ExplorerPanel._finish_batch_layout()` | Atualiza a grade uma vez após as novas entradas serem inseridas. **[DOC]** |
| 452 | `ExplorerPanel._schedule_viewport_repaint()` | Agrupa várias atualizações de ícones em um único redesenho. **[DOC]** |
| 457 | `ExplorerPanel._repaint_thumbnail_viewport()` | Redesenha também as áreas anteriormente ocupadas pelo ícone padrão. **[DOC]** |
| 461 | `ExplorerPanel._schedule_visible_thumbnails()` | Responsável por  schedule visible thumbnails, conforme a implementação **[INFERÊNCIA]** |
| 505 | `ExplorerPanel._apply_video_thumbnail()` | Responsável por  apply video thumbnail, conforme a implementação **[INFERÊNCIA]** |
| 533 | `ExplorerPanel._apply_thumbnail()` | Responsável por  apply thumbnail, conforme a implementação **[INFERÊNCIA]** |
| 560 | `ExplorerPanel._open_item()` | Responsável por  open item, conforme a implementação **[INFERÊNCIA]** |
| 570 | `ExplorerPanel._open_selected_preview()` | Responsável por  open selected preview, conforme a implementação **[INFERÊNCIA]** |
| 575 | `ExplorerPanel._preview_sequence()` | Arquivos na ordem visual, sem incluir pastas nem varrer o disco. **[DOC]** |
| 588 | `ExplorerPanel._preview_more()` | Apenas um lote de entradas por solicitação de navegação. **[DOC]** |
| 594 | `ExplorerPanel._open_preview_for_item()` | Só uma ação explícita abre o visualizador; não executa o arquivo. **[DOC]** |
| 620 | `ExplorerPanel._reset_metadata_selection()` | Responsável por  reset metadata selection, conforme a implementação **[INFERÊNCIA]** |
| 631 | `ExplorerPanel._show_raw_metadata()` | Responsável por  show raw metadata, conforme a implementação **[INFERÊNCIA]** |
| 635 | `ExplorerPanel._verify_selected_metadata()` | A leitura interna ocorre SOMENTE após este clique explícito. **[DOC]** |
| 659 | `ExplorerPanel._start_metadata_task()` | Ponto de envio testável, sem simular objetos internos do Qt. **[DOC]** |
| 663 | `ExplorerPanel._apply_metadata()` | Responsável por  apply metadata, conforme a implementação **[INFERÊNCIA]** |
| 688 | `ExplorerPanel._show_properties()` | Responsável por  show properties, conforme a implementação **[INFERÊNCIA]** |
| 727 | `ExplorerPanel._go_up()` | Responsável por  go up, conforme a implementação **[INFERÊNCIA]** |
| 732 | `ExplorerPanel.refresh()` | Responsável por refresh, conforme a implementação **[INFERÊNCIA]** |
| 736 | `ExplorerPanel._toggle_view()` | Responsável por  toggle view, conforme a implementação **[INFERÊNCIA]** |
| 747 | `ExplorerPanel.showEvent()` | Responsável por showEvent, conforme a implementação **[INFERÊNCIA]** |
| 751 | `ExplorerPanel.resizeEvent()` | Responsável por resizeEvent, conforme a implementação **[INFERÊNCIA]** |
| 755 | `ExplorerPanel.closeEvent()` | Responsável por closeEvent, conforme a implementação **[INFERÊNCIA]** |

## `src/archivia/gui_helpers.py`

| Linha | Função / método | Responsabilidade |
|---:|---|---|
| 36 | `validate_gui_result()` | Recusa respostas incompletas antes de alterar widgets. **[DOC]** |
| 72 | `_require_mapping()` | Responsável por  require mapping, conforme a implementação **[INFERÊNCIA]** |
| 82 | `_require_sequence()` | Responsável por  require sequence, conforme a implementação **[INFERÊNCIA]** |
| 87 | `can_save_inventory_preview()` | Responsável por can save inventory preview, conforme a implementação **[INFERÊNCIA]** |

## `src/archivia/gui_icons.py`

| Linha | Função / método | Responsabilidade |
|---:|---|---|
| 12 | `icon_for()` | Responsável por icon for, conforme a implementação **[INFERÊNCIA]** |
| 23 | `line()` | Responsável por line, conforme a implementação **[INFERÊNCIA]** |
| 26 | `polygon()` | Responsável por polygon, conforme a implementação **[INFERÊNCIA]** |

## `src/archivia/gui_metadata_raw.py`

| Linha | Função / método | Responsabilidade |
|---:|---|---|
| 12 | `_raw_section_text()` | Renderiza XML original ou hex sem abreviar blocos pequenos. **[DOC]** |
| 33 | `RawMetadataDialog.__init__()` | Responsável por   init  , conforme a implementação **[INFERÊNCIA]** |
| 61 | `RawMetadataDialog._copy()` | Responsável por  copy, conforme a implementação **[INFERÊNCIA]** |

## `src/archivia/gui_navigation.py`

| Linha | Função / método | Responsabilidade |
|---:|---|---|
| 7 | `find_saved_snapshot()` | Exige ID exato no histórico retornado; não confundir com 'mais recente'. **[DOC]** |

## `src/archivia/gui_presentation.py`

| Linha | Função / método | Responsabilidade |
|---:|---|---|
| 14 | `catalog_filters()` | Responsável por catalog filters, conforme a implementação **[INFERÊNCIA]** |
| 32 | `previous_page()` | Volta uma página sem sair da primeira; valores inválidos não são aceitos. **[DOC]** |
| 39 | `next_page()` | Avança somente se há outra página, preservando o estado da tela. **[DOC]** |
| 47 | `summary_report()` | Responsável por summary report, conforme a implementação **[INFERÊNCIA]** |
| 60 | `inventory_report()` | Responsável por inventory report, conforme a implementação **[INFERÊNCIA]** |
| 72 | `agent_report()` | Retorna (resposta curta, relatório técnico), sem mudar o texto histórico. **[DOC]** |
| 91 | `recursive_plan_report()` | Resumo legível do plano escolhido pelo Ollama; dados reais são do Python. **[DOC]** |

## `src/archivia/gui_sidebar.py`

| Linha | Função / método | Responsabilidade |
|---:|---|---|
| 15 | `NavigationSidebar.__init__()` | Responsável por   init  , conforme a implementação **[INFERÊNCIA]** |
| 49 | `NavigationSidebar._select_tab()` | Mantém o item ativo marcado mesmo ao clicar na aba já selecionada. **[DOC]** |
| 56 | `NavigationSidebar._sync_current_tab()` | Sincroniza o destaque mesmo ao navegar por atalhos de outras abas. **[DOC]** |

## `src/archivia/gui_tables.py`

| Linha | Função / método | Responsabilidade |
|---:|---|---|
| 13 | `fill_table()` | Responsável por fill table, conforme a implementação **[INFERÊNCIA]** |

## `src/archivia/gui_theme.py`

Sem funções definidas.

## `src/archivia/gui_video.py`

| Linha | Função / método | Responsabilidade |
|---:|---|---|
| 24 | `format_media_time()` | Responsável por format media time, conforme a implementação **[INFERÊNCIA]** |
| 37 | `LocalVideoPlayer.__init__()` | Responsável por   init  , conforme a implementação **[INFERÊNCIA]** |
| 109 | `LocalVideoPlayer._set_controls()` | Responsável por  set controls, conforme a implementação **[INFERÊNCIA]** |
| 116 | `LocalVideoPlayer.open_local()` | Abre fonte local, mas NÃO chama play(). **[DOC]** |
| 123 | `LocalVideoPlayer.release()` | Solta a fonte ao navegar/fechar, para não manter o arquivo aberto. **[DOC]** |
| 135 | `LocalVideoPlayer.seek_relative()` | Responsável por seek relative, conforme a implementação **[INFERÊNCIA]** |
| 142 | `LocalVideoPlayer._start_seek()` | Responsável por  start seek, conforme a implementação **[INFERÊNCIA]** |
| 145 | `LocalVideoPlayer._finish_seek()` | Responsável por  finish seek, conforme a implementação **[INFERÊNCIA]** |
| 150 | `LocalVideoPlayer._duration_changed()` | Responsável por  duration changed, conforme a implementação **[INFERÊNCIA]** |
| 155 | `LocalVideoPlayer._position_changed()` | Responsável por  position changed, conforme a implementação **[INFERÊNCIA]** |
| 160 | `LocalVideoPlayer._toggle_mute()` | Responsável por  toggle mute, conforme a implementação **[INFERÊNCIA]** |
| 165 | `LocalVideoPlayer._playback_state()` | Responsável por  playback state, conforme a implementação **[INFERÊNCIA]** |
| 171 | `LocalVideoPlayer._error()` | Responsável por  error, conforme a implementação **[INFERÊNCIA]** |

## `src/archivia/gui_viewer.py`

| Linha | Função / método | Responsabilidade |
|---:|---|---|
| 42 | `_junction()` | Responsável por  junction, conforme a implementação **[INFERÊNCIA]** |
| 46 | `verified_file()` | Valida escopo, links e identidade antes de qualquer leitura interna. **[DOC]** |
| 77 | `_ImageLoad.__init__()` | Responsável por   init  , conforme a implementação **[INFERÊNCIA]** |
| 83 | `_ImageLoad.run()` | Responsável por run, conforme a implementação **[INFERÊNCIA]** |
| 102 | `_MetadataLoad.__init__()` | Responsável por   init  , conforme a implementação **[INFERÊNCIA]** |
| 108 | `_MetadataLoad.run()` | Responsável por run, conforme a implementação **[INFERÊNCIA]** |
| 123 | `ZoomImageView.__init__()` | Responsável por   init  , conforme a implementação **[INFERÊNCIA]** |
| 143 | `ZoomImageView.clear_image()` | Libera a imagem anterior antes de navegar para outro arquivo. **[DOC]** |
| 152 | `ZoomImageView.set_image()` | Responsável por set image, conforme a implementação **[INFERÊNCIA]** |
| 158 | `ZoomImageView.fit_image()` | Responsável por fit image, conforme a implementação **[INFERÊNCIA]** |
| 169 | `ZoomImageView.actual_size()` | Responsável por actual size, conforme a implementação **[INFERÊNCIA]** |
| 176 | `ZoomImageView.zoom_by()` | Responsável por zoom by, conforme a implementação **[INFERÊNCIA]** |
| 186 | `ZoomImageView._report_zoom()` | Responsável por  report zoom, conforme a implementação **[INFERÊNCIA]** |
| 189 | `ZoomImageView.wheelEvent()` | Responsável por wheelEvent, conforme a implementação **[INFERÊNCIA]** |
| 200 | `ZoomImageView.resizeEvent()` | Responsável por resizeEvent, conforme a implementação **[INFERÊNCIA]** |
| 209 | `FilePreviewDialog.__init__()` | Responsável por   init  , conforme a implementação **[INFERÊNCIA]** |
| 382 | `FilePreviewDialog._update_navigation_buttons()` | Desabilita setas nos limites, respeitando carregamento progressivo. **[DOC]** |
| 394 | `FilePreviewDialog._previous_file()` | Responsável por  previous file, conforme a implementação **[INFERÊNCIA]** |
| 397 | `FilePreviewDialog._next_file()` | Responsável por  next file, conforme a implementação **[INFERÊNCIA]** |
| 400 | `FilePreviewDialog._navigate()` | Responsável por  navigate, conforme a implementação **[INFERÊNCIA]** |
| 444 | `FilePreviewDialog._basic_properties()` | Responsável por  basic properties, conforme a implementação **[INFERÊNCIA]** |
| 461 | `FilePreviewDialog._start_preview_if_image()` | Responsável por  start preview if image, conforme a implementação **[INFERÊNCIA]** |
| 487 | `FilePreviewDialog._submit_image()` | Responsável por  submit image, conforme a implementação **[INFERÊNCIA]** |
| 490 | `FilePreviewDialog._image_loaded_result()` | Responsável por  image loaded result, conforme a implementação **[INFERÊNCIA]** |
| 512 | `FilePreviewDialog._show_raw_metadata()` | Responsável por  show raw metadata, conforme a implementação **[INFERÊNCIA]** |
| 516 | `FilePreviewDialog._request_metadata()` | Responsável por  request metadata, conforme a implementação **[INFERÊNCIA]** |
| 529 | `FilePreviewDialog._submit_metadata()` | Responsável por  submit metadata, conforme a implementação **[INFERÊNCIA]** |
| 532 | `FilePreviewDialog._metadata_loaded_result()` | Responsável por  metadata loaded result, conforme a implementação **[INFERÊNCIA]** |
| 549 | `FilePreviewDialog.reject()` | Responsável por reject, conforme a implementação **[INFERÊNCIA]** |

## `src/archivia/gui_worker.py`

| Linha | Função / método | Responsabilidade |
|---:|---|---|
| 31 | `QueryWorker.__init__()` | Responsável por   init  , conforme a implementação **[INFERÊNCIA]** |
| 81 | `QueryWorker.run()` | Responsável por run, conforme a implementação **[INFERÊNCIA]** |

## `src/archivia/image_decode.py`

| Linha | Função / método | Responsabilidade |
|---:|---|---|
| 15 | `decode_preview()` | Responsável por decode preview, conforme a implementação **[INFERÊNCIA]** |
| 48 | `_decode_with_pillow()` | Responsável por  decode with pillow, conforme a implementação **[INFERÊNCIA]** |

## `src/archivia/inventory.py`

| Linha | Função / método | Responsabilidade |
|---:|---|---|
| 42 | `inventory()` | Lê metadados dos arquivos, sem abrir conteúdo, ZIPs ou seguir symlinks. **[DOC]** |

## `src/archivia/manual_copy.py`

| Linha | Função / método | Responsabilidade |
|---:|---|---|
| 27 | `_digest()` | Responsável por  digest, conforme a implementação **[INFERÊNCIA]** |
| 51 | `_record()` | Responsável por  record, conforme a implementação **[INFERÊNCIA]** |
| 62 | `preview_manual_image_copy()` | Prévia e verificação de caminhos; não altera arquivos nem pastas. **[DOC]** |
| 87 | `copy_manual_image_verified()` | Responsável por copy manual image verified, conforme a implementação **[INFERÊNCIA]** |

