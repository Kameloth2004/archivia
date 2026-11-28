# Catálogo de testes e simulações — parte 2/3

Referência: `Kameloth2004/archivia`, branch `feat/v2-video-thumbnails-2026-11-27`, commit `2afb6c97edff83cadd013136ea1573ee3b66aaf9` (28/11/2026). Inclui todos os métodos `test_*`, fixtures, helpers e simulações definidos nestes arquivos. A descrição de funções sem docstring é **inferida pelo nome**, devendo ser complementada por inspeção do teste antes de afirmar comportamento exato.

## `tests/test_exiftool_adapter_v2.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 14 | `ExifToolAdapterTests.test_groups_unknown_gps_xmp_and_duplicates_are_not_filtered()` | Verifica groups unknown gps xmp and duplicates are not filtered **[INFERÊNCIA]** |
| 47 | `ExifToolAdapterTests.test_invalid_json_and_timeouts_fail_explicitly()` | Verifica invalid json and timeouts fail explicitly **[INFERÊNCIA]** |

## `tests/test_file_identity.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 15 | `FileIdentityAndRecursionTests.test_identity_matches_previous_contract()` | Verifica identity matches previous contract **[INFERÊNCIA]** |
| 26 | `FileIdentityAndRecursionTests.test_recursive_inventory_includes_nested_files_with_relative_path()` | Verifica recursive inventory includes nested files with relative path **[INFERÊNCIA]** |
| 45 | `FileIdentityAndRecursionTests.test_symlink_directory_not_followed()` | Verifica symlink directory not followed **[INFERÊNCIA]** |

## `tests/test_gui_calendar_date.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 21 | `CalendarDateEditTests.setUpClass()` | Auxilia setUpClass **[INFERÊNCIA]** |
| 24 | `CalendarDateEditTests.test_calendar_choice_uses_regional_format_and_emits_search()` | Verifica calendar choice uses regional format and emits search **[INFERÊNCIA]** |
| 38 | `CalendarDateEditTests.test_change_format_keeps_same_iso_day()` | Verifica change format keeps same iso day **[INFERÊNCIA]** |
| 47 | `CalendarDateEditTests.test_blank_and_clear_remain_optional()` | Verifica blank and clear remain optional **[INFERÊNCIA]** |
| 59 | `CalendarDateEditTests.test_invalid_and_incomplete_date_not_silently_reinterpreted()` | Verifica invalid and incomplete date not silently reinterpreted **[INFERÊNCIA]** |

## `tests/test_gui_expanding_report_v2.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 21 | `ExpandingReportTests.setUpClass()` | Auxilia setUpClass **[INFERÊNCIA]** |
| 24 | `ExpandingReportTests.test_readonly_and_no_internal_scrollbar()` | Verifica readonly and no internal scrollbar **[INFERÊNCIA]** |
| 37 | `ExpandingReportTests.test_height_grows_to_fit_full_report()` | Verifica height grows to fit full report **[INFERÊNCIA]** |
| 48 | `ExpandingReportTests.test_report_recalculates_after_text_and_width_change()` | Verifica report recalculates after text and width change **[INFERÊNCIA]** |
| 72 | `ExpandingReportTests.test_home_report_stays_collapsible_and_external_scroll_exists()` | Verifica home report stays collapsible and external scroll exists **[INFERÊNCIA]** |

## `tests/test_gui_explorer_v2.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 28 | `ExplorerV2Tests.setUpClass()` | Auxilia setUpClass **[INFERÊNCIA]** |
| 31 | `ExplorerV2Tests.setUp()` | Prepara fixtures e estado para cada teste **[INFERÊNCIA]** |
| 43 | `ExplorerV2Tests.tearDown()` | Encerra recursos e limpa fixtures após cada teste **[INFERÊNCIA]** |
| 57 | `ExplorerV2Tests.test_directory_guard_denies_outside_and_symlinks()` | Verifica directory guard denies outside and symlinks **[INFERÊNCIA]** |
| 70 | `ExplorerV2Tests.test_root_lists_only_direct_children_and_navigation()` | Verifica root lists only direct children and navigation **[INFERÊNCIA]** |
| 85 | `ExplorerV2Tests.test_selection_properties_and_safe_double_click()` | Verifica selection properties and safe double click **[INFERÊNCIA]** |
| 103 | `ExplorerV2Tests.test_thumbnail_result_updates_only_current_file_generation()` | Verifica thumbnail result updates only current file generation **[INFERÊNCIA]** |
| 122 | `ExplorerV2Tests.test_real_png_thumbnail_preserves_nanosecond_timestamp_in_signal()` | TEST-ONLY: decodificação real e sinal sem conversão para int32. **[DOC]** |
| 151 | `ExplorerV2Tests.test_viewer_sequence_matches_displayed_file_order_and_skips_folders()` | Verifica viewer sequence matches displayed file order and skips folders **[INFERÊNCIA]** |
| 174 | `ExplorerV2Tests.test_viewer_paginates_only_on_demand()` | Verifica viewer paginates only on demand **[INFERÊNCIA]** |
| 186 | `ExplorerV2Tests.test_navigation_denies_leaving_active_folder()` | Verifica navigation denies leaving active folder **[INFERÊNCIA]** |
| 193 | `ExplorerV2Tests.test_listing_is_batched_and_refresh_is_readonly()` | Verifica listing is batched and refresh is readonly **[INFERÊNCIA]** |
| 205 | `ExplorerV2Tests.test_loading_more_schedules_layout_and_viewport_repaint()` | Verifica loading more schedules layout and viewport repaint **[INFERÊNCIA]** |
| 227 | `ExplorerV2Tests.test_icon_replacement_requests_coalesced_repaint()` | Verifica icon replacement requests coalesced repaint **[INFERÊNCIA]** |
| 246 | `ExplorerV2Tests.test_folder_switch_clears_previous_items_and_thumbnail_cache()` | Verifica folder switch clears previous items and thumbnail cache **[INFERÊNCIA]** |
| 260 | `ExplorerV2Tests.test_gui_explorer_tracks_active_folder_without_sqlite_writes()` | Verifica gui explorer tracks active folder without sqlite writes **[INFERÊNCIA]** |

## `tests/test_gui_helpers.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 8 | `GUIHelpersTests.test_summary_empty_snapshot_is_valid()` | Verifica summary empty snapshot is valid **[INFERÊNCIA]** |
| 11 | `GUIHelpersTests.test_summary_requires_all_counts_if_catalog_exists()` | Verifica summary requires all counts if catalog exists **[INFERÊNCIA]** |
| 19 | `GUIHelpersTests.test_preview_requires_nested_summary()` | Verifica preview requires nested summary **[INFERÊNCIA]** |
| 26 | `GUIHelpersTests.test_catalog_page_requires_iso_field_in_every_file()` | Verifica catalog page requires iso field in every file **[INFERÊNCIA]** |
| 34 | `GUIHelpersTests.test_rejects_unknown_mode_and_wrong_shape()` | Verifica rejects unknown mode and wrong shape **[INFERÊNCIA]** |
| 42 | `GUIHelpersTests.test_accepts_minimal_valid_date_plan_and_history()` | Verifica accepts minimal valid date plan and history **[INFERÊNCIA]** |

## `tests/test_gui_navigation.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 8 | `SavedSnapshotNavigationTests.test_finds_exact_snapshot_not_simply_newest()` | Verifica finds exact snapshot not simply newest **[INFERÊNCIA]** |
| 17 | `SavedSnapshotNavigationTests.test_rejects_invalid_snapshot_ids()` | Verifica rejects invalid snapshot ids **[INFERÊNCIA]** |
| 23 | `SavedSnapshotNavigationTests.test_empty_history_does_not_falsely_confirm()` | Verifica empty history does not falsely confirm **[INFERÊNCIA]** |
| 26 | `SavedSnapshotNavigationTests.test_ignores_unrelated_history_rows()` | Verifica ignores unrelated history rows **[INFERÊNCIA]** |

## `tests/test_gui_presentation.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 11 | `GUIPresentationTests.test_catalog_filters_preserve_normalized_values_and_dates()` | Verifica catalog filters preserve normalized values and dates **[INFERÊNCIA]** |
| 24 | `GUIPresentationTests.test_catalog_filters_allow_empty_masked_dates()` | Verifica catalog filters allow empty masked dates **[INFERÊNCIA]** |
| 32 | `GUIPresentationTests.test_catalog_filters_reject_inverted_dates()` | Verifica catalog filters reject inverted dates **[INFERÊNCIA]** |
| 40 | `GUIPresentationTests.test_page_navigation_respects_bounds()` | Verifica page navigation respects bounds **[INFERÊNCIA]** |
| 47 | `GUIPresentationTests.test_pagination_rejects_invalid_inputs()` | Verifica pagination rejects invalid inputs **[INFERÊNCIA]** |
| 55 | `GUIPresentationTests.test_summary_report_preserves_text_and_counts()` | Verifica summary report preserves text and counts **[INFERÊNCIA]** |
| 69 | `GUIPresentationTests.test_inventory_report_preserves_messages()` | Verifica inventory report preserves messages **[INFERÊNCIA]** |
| 80 | `GUIPresentationTests.test_recursive_plan_report_shows_summary_and_sample()` | Verifica recursive plan report shows summary and sample **[INFERÊNCIA]** |
| 96 | `GUIPresentationTests.test_recursive_plan_report_does_not_invent_plan()` | Verifica recursive plan report does not invent plan **[INFERÊNCIA]** |
| 104 | `GUIPresentationTests.test_agent_report_preserves_short_and_technical_versions()` | Verifica agent report preserves short and technical versions **[INFERÊNCIA]** |

## `tests/test_gui_sidebar_v2.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 15 | `SidebarStructureTests.test_maximizes_on_start_not_exclusive_fullscreen()` | Verifica maximizes on start not exclusive fullscreen **[INFERÊNCIA]** |
| 22 | `SidebarStructureTests.test_sidebar_uses_same_tab_widget_and_horizontal_splitter()` | Verifica sidebar uses same tab widget and horizontal splitter **[INFERÊNCIA]** |
| 50 | `SidebarInteractionTests.setUpClass()` | Auxilia setUpClass **[INFERÊNCIA]** |
| 53 | `SidebarInteractionTests.setUp()` | Prepara fixtures e estado para cada teste **[INFERÊNCIA]** |
| 56 | `SidebarInteractionTests.tearDown()` | Encerra recursos e limpa fixtures após cada teste **[INFERÊNCIA]** |
| 59 | `SidebarInteractionTests.test_six_navigation_buttons_and_highlight_follow_each_tab()` | Verifica six navigation buttons and highlight follow each tab **[INFERÊNCIA]** |
| 85 | `SidebarInteractionTests.test_existing_programmatic_navigation_updates_sidebar()` | Verifica existing programmatic navigation updates sidebar **[INFERÊNCIA]** |
| 93 | `SidebarInteractionTests.test_sidebar_never_initiates_moves_or_scans()` | Verifica sidebar never initiates moves or scans **[INFERÊNCIA]** |

## `tests/test_gui_structure.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 17 | `GUIStructureTests.setUpClass()` | Auxilia setUpClass **[INFERÊNCIA]** |
| 25 | `GUIStructureTests.method()` | Auxilia method **[INFERÊNCIA]** |
| 31 | `GUIStructureTests.test_busy_guards_run_before_widget_mutations()` | Verifica busy guards run before widget mutations **[INFERÊNCIA]** |
| 43 | `GUIStructureTests.test_catalog_dates_use_calendar_without_changing_search_contract()` | Verifica catalog dates use calendar without changing search contract **[INFERÊNCIA]** |
| 56 | `GUIStructureTests.test_home_reuses_single_active_folder_and_does_not_stretch_notice()` | Verifica home reuses single active folder and does not stretch notice **[INFERÊNCIA]** |
| 68 | `GUIStructureTests.test_compact_global_toolbar_and_collapsible_home_analysis()` | Verifica compact global toolbar and collapsible home analysis **[INFERÊNCIA]** |
| 84 | `GUIStructureTests.test_active_folder_and_catalog_sources_are_isolated()` | Verifica active folder and catalog sources are isolated **[INFERÊNCIA]** |
| 105 | `GUIStructureTests.test_timestamp_cell_keeps_raw_iso_in_user_role()` | Verifica timestamp cell keeps raw iso in user role **[INFERÊNCIA]** |
| 115 | `GUIStructureTests.test_date_format_uses_saved_iso_not_previous_display()` | Verifica date format uses saved iso not previous display **[INFERÊNCIA]** |
| 122 | `GUIStructureTests.test_worker_moved_out_of_main_window_module()` | Verifica worker moved out of main window module **[INFERÊNCIA]** |
| 131 | `GUIStructureTests.test_catalog_filters_and_pagination_use_shared_helpers()` | Verifica catalog filters and pagination use shared helpers **[INFERÊNCIA]** |
| 140 | `GUIStructureTests.test_reports_are_delegated_to_presentation_module()` | Verifica reports are delegated to presentation module **[INFERÊNCIA]** |
| 147 | `GUIStructureTests.test_saved_snapshot_navigation_waits_for_worker_finish()` | Verifica saved snapshot navigation waits for worker finish **[INFERÊNCIA]** |
| 155 | `GUIStructureTests.test_saved_snapshot_selection_uses_id_and_clears_old_filters()` | Verifica saved snapshot selection uses id and clears old filters **[INFERÊNCIA]** |
| 164 | `GUIStructureTests.test_home_catalog_buttons_reuse_existing_handlers()` | Verifica home catalog buttons reuse existing handlers **[INFERÊNCIA]** |
| 172 | `GUIStructureTests.test_home_preview_opens_library_inventory_section()` | Verifica home preview opens library inventory section **[INFERÊNCIA]** |
| 179 | `GUIStructureTests.test_busy_and_saved_preview_control_all_catalog_buttons()` | Verifica busy and saved preview control all catalog buttons **[INFERÊNCIA]** |
| 192 | `GUIStructureTests.test_manual_copy_is_opt_in_only_from_gui()` | Verifica manual copy is opt in only from gui **[INFERÊNCIA]** |
| 203 | `GUIStructureTests.test_manual_copy_uses_existing_worker_and_disables_button()` | Verifica manual copy uses existing worker and disables button **[INFERÊNCIA]** |
| 210 | `GUIStructureTests.test_six_tabs_are_permanent_and_handlers_are_reused()` | Verifica six tabs are permanent and handlers are reused **[INFERÊNCIA]** |
| 227 | `GUIStructureTests.test_document_shortcuts_use_existing_catalog_and_do_not_move_files()` | Verifica document shortcuts use existing catalog and do not move files **[INFERÊNCIA]** |
| 239 | `GUIStructureTests.test_home_direct_organization_is_independent_of_ollama()` | Verifica home direct organization is independent of ollama **[INFERÊNCIA]** |
| 262 | `GUIStructureTests.test_analyze_without_destination_and_move_all_are_explicit()` | Verifica analyze without destination and move all are explicit **[INFERÊNCIA]** |
| 278 | `GUIStructureTests.test_home_understands_mova_and_renders_recursive_plan()` | Verifica home understands mova and renders recursive plan **[INFERÊNCIA]** |
| 285 | `GUIStructureTests.test_result_contract_is_checked_before_render()` | Verifica result contract is checked before render **[INFERÊNCIA]** |

## `tests/test_gui_video_v2.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 29 | `VideoPlayerV2Tests.setUpClass()` | Auxilia setUpClass **[INFERÊNCIA]** |
| 32 | `VideoPlayerV2Tests.setUp()` | Prepara fixtures e estado para cada teste **[INFERÊNCIA]** |
| 41 | `VideoPlayerV2Tests.tearDown()` | Encerra recursos e limpa fixtures após cada teste **[INFERÊNCIA]** |
| 46 | `VideoPlayerV2Tests._expected()` | Auxilia  expected **[INFERÊNCIA]** |
| 50 | `VideoPlayerV2Tests.test_extensions_and_time_format()` | Verifica extensions and time format **[INFERÊNCIA]** |
| 57 | `VideoPlayerV2Tests.test_open_does_not_autoplay_and_release_clears_source()` | Verifica open does not autoplay and release clears source **[INFERÊNCIA]** |
| 65 | `VideoPlayerV2Tests.test_seek_clamps_to_duration_and_requires_seekable()` | Verifica seek clamps to duration and requires seekable **[INFERÊNCIA]** |
| 77 | `VideoPlayerV2Tests.test_video_dialog_does_not_submit_image_or_autoplay()` | Verifica video dialog does not submit image or autoplay **[INFERÊNCIA]** |
| 89 | `VideoPlayerV2Tests.test_navigation_out_of_video_releases_player()` | Verifica navigation out of video releases player **[INFERÊNCIA]** |

## `tests/test_gui_viewer_v2.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 27 | `FullscreenViewerV2Tests.setUpClass()` | Auxilia setUpClass **[INFERÊNCIA]** |
| 30 | `FullscreenViewerV2Tests.setUp()` | Prepara fixtures e estado para cada teste **[INFERÊNCIA]** |
| 42 | `FullscreenViewerV2Tests.tearDown()` | Encerra recursos e limpa fixtures após cada teste **[INFERÊNCIA]** |
| 45 | `FullscreenViewerV2Tests._expected()` | Auxilia  expected **[INFERÊNCIA]** |
| 49 | `FullscreenViewerV2Tests.test_real_image_preview_and_zoom()` | Verifica real image preview and zoom **[INFERÊNCIA]** |
| 73 | `FullscreenViewerV2Tests.test_arrows_navigate_and_reset_zoom_and_metadata_without_auto_read()` | Verifica arrows navigate and reset zoom and metadata without auto read **[INFERÊNCIA]** |
| 128 | `FullscreenViewerV2Tests.test_old_async_image_is_ignored_after_navigating()` | Verifica old async image is ignored after navigating **[INFERÊNCIA]** |
| 159 | `FullscreenViewerV2Tests.test_next_file_can_load_one_more_batch()` | Verifica next file can load one more batch **[INFERÊNCIA]** |
| 168 | `FullscreenViewerV2Tests.load_one()` | Auxilia load one **[INFERÊNCIA]** |
| 191 | `FullscreenViewerV2Tests.test_real_decoder_task_works_without_modifying_fixture()` | Verifica real decoder task works without modifying fixture **[INFERÊNCIA]** |
| 205 | `FullscreenViewerV2Tests.test_non_image_shows_readonly_placeholder_and_requires_metadata_click()` | Verifica non image shows readonly placeholder and requires metadata click **[INFERÊNCIA]** |
| 225 | `FullscreenViewerV2Tests.test_close_button_marks_dialog_closed_and_returns_to_explorer()` | Verifica close button marks dialog closed and returns to explorer **[INFERÊNCIA]** |
| 232 | `FullscreenViewerV2Tests.test_stale_metadata_and_image_after_close_are_ignored()` | Verifica stale metadata and image after close are ignored **[INFERÊNCIA]** |
| 240 | `FullscreenViewerV2Tests.test_reject_outside_folder_or_modified_file()` | Verifica reject outside folder or modified file **[INFERÊNCIA]** |
| 251 | `FullscreenViewerV2Tests.test_explorer_doubleclick_opens_preview_only_for_files()` | Verifica explorer doubleclick opens preview only for files **[INFERÊNCIA]** |

## `tests/test_home_catalog.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 8 | `HomeCatalogEligibilityTests.test_allows_complete_preview_for_selected_folder()` | Verifica allows complete preview for selected folder **[INFERÊNCIA]** |
| 12 | `HomeCatalogEligibilityTests.test_denies_missing_or_incomplete_preview()` | Verifica denies missing or incomplete preview **[INFERÊNCIA]** |
| 19 | `HomeCatalogEligibilityTests.test_denies_preview_with_errors()` | Verifica denies preview with errors **[INFERÊNCIA]** |
| 25 | `HomeCatalogEligibilityTests.test_denies_changed_source_and_empty_selection()` | Verifica denies changed source and empty selection **[INFERÊNCIA]** |
| 30 | `HomeCatalogEligibilityTests.test_denies_malformed_counts_and_errors()` | Verifica denies malformed counts and errors **[INFERÊNCIA]** |

## `tests/test_image_decode_v2.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 23 | `ImageDecodeTests.setUpClass()` | Auxilia setUpClass **[INFERÊNCIA]** |
| 26 | `ImageDecodeTests.test_png_qt_original_dimensions_and_small_preview()` | Verifica png qt original dimensions and small preview **[INFERÊNCIA]** |
| 39 | `ImageDecodeTests.test_png_too_many_pixels_fails_before_decode()` | Verifica png too many pixels fails before decode **[INFERÊNCIA]** |
| 47 | `ImageDecodeTests.test_unknown_file_explains_missing_pillow_or_invalid_file()` | Verifica unknown file explains missing pillow or invalid file **[INFERÊNCIA]** |
| 54 | `ImageDecodeTests.test_valid_avif_decodes_with_pillow_when_available()` | Verifica valid avif decodes with pillow when available **[INFERÊNCIA]** |
| 71 | `ImageDecodeTests.test_jfif_is_indexed_as_image_and_decoded()` | Verifica jfif is indexed as image and decoded **[INFERÊNCIA]** |
| 90 | `ImageDecodeTests.test_avif_thumbnail_task_uses_shared_fallback()` | Verifica avif thumbnail task uses shared fallback **[INFERÊNCIA]** |
| 114 | `ImageDecodeTests.test_pillow_fallback_when_qt_reader_rejects_valid_png()` | Verifica pillow fallback when qt reader rejects valid png **[INFERÊNCIA]** |

## `tests/test_inventory.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 12 | `InventoryTests.test_inventory_only_reads_and_classifies_extensions()` | Verifica inventory only reads and classifies extensions **[INFERÊNCIA]** |
| 34 | `InventoryTests.test_universal_categories_and_archives_not_opened()` | Verifica universal categories and archives not opened **[INFERÊNCIA]** |
| 60 | `InventoryTests.test_nonexistent_directory_is_rejected()` | Verifica nonexistent directory is rejected **[INFERÊNCIA]** |
| 65 | `InventoryTests.test_symlink_not_followed()` | Verifica symlink not followed **[INFERÊNCIA]** |

## `tests/test_large_moves.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 15 | `LargeFileMoveTests.setUp()` | Prepara fixtures e estado para cada teste **[INFERÊNCIA]** |
| 24 | `LargeFileMoveTests.tearDown()` | Encerra recursos e limpa fixtures após cada teste **[INFERÊNCIA]** |
| 28 | `LargeFileMoveTests.large_file()` | Auxilia large file **[INFERÊNCIA]** |
| 39 | `LargeFileMoveTests.test_large_video_moves_with_integrity()` | Verifica large video moves with integrity **[INFERÊNCIA]** |
| 57 | `LargeFileMoveTests.test_large_audio_queue_continues_through_safe_collision()` | Verifica large audio queue continues through safe collision **[INFERÊNCIA]** |
| 81 | `LargeFileMoveTests.test_large_video_conflict_hash_and_alternative()` | Verifica large video conflict hash and alternative **[INFERÊNCIA]** |
| 97 | `LargeFileMoveTests.test_unsafe_failure_stops_queue()` | Verifica unsafe failure stops queue **[INFERÊNCIA]** |
| 102 | `LargeFileMoveTests.fail_second()` | Auxilia fail second **[INFERÊNCIA]** |

## `tests/test_manual_copy.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 14 | `ManualCopyTests.fixture()` | Auxilia fixture **[INFERÊNCIA]** |
| 23 | `ManualCopyTests.approve()` | Auxilia approve **[INFERÊNCIA]** |
| 30 | `ManualCopyTests.test_copies_one_image_with_hash_and_preserves_original()` | Verifica copies one image with hash and preserves original **[INFERÊNCIA]** |
| 44 | `ManualCopyTests.test_requires_exact_approved_paths()` | Verifica requires exact approved paths **[INFERÊNCIA]** |
| 55 | `ManualCopyTests.test_refuses_existing_target_without_replacing()` | Verifica refuses existing target without replacing **[INFERÊNCIA]** |
| 65 | `ManualCopyTests.test_rejects_unsupported_extension()` | Verifica rejects unsupported extension **[INFERÊNCIA]** |
| 72 | `ManualCopyTests.test_rejects_same_source_destination_directory()` | Verifica rejects same source destination directory **[INFERÊNCIA]** |
| 78 | `ManualCopyTests.test_copy_failure_does_not_delete_source()` | Verifica copy failure does not delete source **[INFERÊNCIA]** |
| 85 | `ManualCopyTests.fail_temp_digest()` | Auxilia fail temp digest **[INFERÊNCIA]** |
| 96 | `ManualCopyTests.test_collision_case_insensitive_is_rejected()` | Verifica collision case insensitive is rejected **[INFERÊNCIA]** |

