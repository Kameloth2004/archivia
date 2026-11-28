# Catálogo de testes e simulações — parte 1/3

Referência: `Kameloth2004/archivia`, branch `feat/v2-video-thumbnails-2026-11-27`, commit `2afb6c97edff83cadd013136ea1573ee3b66aaf9` (28/11/2026). Inclui todos os métodos `test_*`, fixtures, helpers e simulações definidos nestes arquivos. A descrição de funções sem docstring é **inferida pelo nome**, devendo ser complementada por inspeção do teste antes de afirmar comportamento exato.

## `tests/generate_sha256_paged_demo.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 18 | `fixture_payloads()` | Constrói 134 nomes ordenáveis, incluindo duplicatas entre páginas 1 e 2. **[DOC]** |
| 42 | `generate_fixture()` | Cria arquivos exclusivamente em tests/; recusa pasta não vazia ou fora de tests/. **[DOC]** |
| 69 | `main()` | Auxilia main **[INFERÊNCIA]** |

## `tests/support.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 17 | `temporary_test_directory()` | TEST-ONLY: diretório temporário isolado e limpo automaticamente. **[DOC]** |

## `tests/test_active_folder_v2.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 22 | `ActiveFolderV2Tests.setUpClass()` | Auxilia setUpClass **[INFERÊNCIA]** |
| 25 | `ActiveFolderV2Tests.setUp()` | Prepara fixtures e estado para cada teste **[INFERÊNCIA]** |
| 36 | `ActiveFolderV2Tests.tearDown()` | Encerra recursos e limpa fixtures após cada teste **[INFERÊNCIA]** |
| 40 | `ActiveFolderV2Tests.test_selected_folder_is_shared_and_is_not_saved_to_settings()` | Verifica selected folder is shared and is not saved to settings **[INFERÊNCIA]** |
| 51 | `ActiveFolderV2Tests.test_home_source_is_the_same_widget_as_inventory_folder()` | Verifica home source is the same widget as inventory folder **[INFERÊNCIA]** |
| 60 | `ActiveFolderV2Tests.test_global_actions_keep_source_and_navigation()` | Verifica global actions keep source and navigation **[INFERÊNCIA]** |
| 72 | `ActiveFolderV2Tests.test_analysis_details_start_closed_and_toggle_without_losing_text()` | Verifica analysis details start closed and toggle without losing text **[INFERÊNCIA]** |
| 88 | `ActiveFolderV2Tests.test_switch_folder_discards_previous_temporary_catalog_and_plan()` | Verifica switch folder discards previous temporary catalog and plan **[INFERÊNCIA]** |
| 106 | `ActiveFolderV2Tests.test_clear_keeps_saved_catalog_configuration()` | Verifica clear keeps saved catalog configuration **[INFERÊNCIA]** |
| 118 | `ActiveFolderV2Tests.test_active_catalog_uses_session_not_saved_database()` | Verifica active catalog uses session not saved database **[INFERÊNCIA]** |
| 143 | `ActiveFolderV2Tests.test_while_busy_selection_controls_are_disabled()` | Verifica while busy selection controls are disabled **[INFERÊNCIA]** |

## `tests/test_agent.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 15 | `AgentTests.test_unknown_tool_blocked()` | Verifica unknown tool blocked **[INFERÊNCIA]** |
| 19 | `AgentTests.test_rejects_extra_tool_arguments()` | Verifica rejects extra tool arguments **[INFERÊNCIA]** |
| 26 | `AgentTests.test_ollama_mock_uses_readonly_summary()` | Verifica ollama mock uses readonly summary **[INFERÊNCIA]** |
| 44 | `AgentTests.test_search_tool_returns_limited_readonly_results()` | Verifica search tool returns limited readonly results **[INFERÊNCIA]** |
| 67 | `AgentTests.test_search_tool_rejects_unsafe_parameters()` | Verifica search tool rejects unsafe parameters **[INFERÊNCIA]** |
| 79 | `AgentTests.test_ollama_mock_search_calls_tool_without_network()` | Verifica ollama mock search calls tool without network **[INFERÊNCIA]** |
| 100 | `AgentTests.test_agent_search_by_filename_and_modification_date()` | Verifica agent search by filename and modification date **[INFERÊNCIA]** |
| 123 | `AgentTests.test_agent_search_rejects_invalid_scope_and_date()` | Verifica agent search rejects invalid scope and date **[INFERÊNCIA]** |
| 134 | `AgentTests.test_date_organization_tool_is_readonly_and_limited()` | Verifica date organization tool is readonly and limited **[INFERÊNCIA]** |
| 159 | `AgentTests.test_date_organization_tool_rejects_unauthorized_arguments()` | Verifica date organization tool rejects unauthorized arguments **[INFERÊNCIA]** |
| 175 | `AgentTests.test_ollama_mock_date_plan_never_executes()` | Verifica ollama mock date plan never executes **[INFERÊNCIA]** |
| 202 | `AgentTests.test_selected_folder_uses_its_snapshot_for_agent_tools()` | Verifica selected folder uses its snapshot for agent tools **[INFERÊNCIA]** |
| 232 | `AgentTests.test_selected_folder_without_catalog_must_not_fallback()` | Verifica selected folder without catalog must not fallback **[INFERÊNCIA]** |
| 244 | `AgentTests.test_agent_mock_enforces_selected_folder_snapshot()` | Verifica agent mock enforces selected folder snapshot **[INFERÊNCIA]** |
| 269 | `AgentTests.test_agent_consolidation_preview_uses_selected_origin_and_blocks_collision()` | Verifica agent consolidation preview uses selected origin and blocks collision **[INFERÊNCIA]** |
| 318 | `AgentTests.test_ollama_mock_global_consolidation_uses_selected_snapshot_and_only_summary()` | Verifica ollama mock global consolidation uses selected snapshot and only summary **[INFERÊNCIA]** |
| 364 | `AgentTests.test_global_consolidation_agent_rejects_bad_arguments()` | Verifica global consolidation agent rejects bad arguments **[INFERÊNCIA]** |
| 379 | `AgentTests.test_folder_session_reuses_catalog_and_refreshes_when_requested()` | Verifica folder session reuses catalog and refreshes when requested **[INFERÊNCIA]** |
| 417 | `AgentTests.test_folder_session_refresh_failure_keeps_previous_snapshot()` | Verifica folder session refresh failure keeps previous snapshot **[INFERÊNCIA]** |
| 440 | `AgentTests.test_auto_folder_session_is_temporary_and_preserves_persistent_catalog()` | Verifica auto folder session is temporary and preserves persistent catalog **[INFERÊNCIA]** |
| 451 | `AgentTests.tracked_temporary()` | Auxilia tracked temporary **[INFERÊNCIA]** |
| 476 | `AgentTests.test_auto_folder_session_cleans_up_after_agent_failure()` | Verifica auto folder session cleans up after agent failure **[INFERÊNCIA]** |
| 484 | `AgentTests.tracked_temporary()` | Auxilia tracked temporary **[INFERÊNCIA]** |
| 496 | `AgentTests.test_auto_folder_session_rejects_unreadable_inventory_without_agent_call()` | Verifica auto folder session rejects unreadable inventory without agent call **[INFERÊNCIA]** |
| 511 | `AgentTests.test_search_absolute_origin_path_is_not_a_filename_filter()` | Verifica search absolute origin path is not a filename filter **[INFERÊNCIA]** |
| 535 | `AgentTests.test_agent_logs_real_tool_arguments_and_missing_limit_uses_default()` | Verifica agent logs real tool arguments and missing limit uses default **[INFERÊNCIA]** |
| 568 | `AgentTests.test_ollama_mock_cannot_execute_unknown_tool()` | Verifica ollama mock cannot execute unknown tool **[INFERÊNCIA]** |

## `tests/test_batch_move.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 12 | `SupervisedBatchTests.setUp()` | Prepara fixtures e estado para cada teste **[INFERÊNCIA]** |
| 25 | `SupervisedBatchTests.tearDown()` | Encerra recursos e limpa fixtures após cada teste **[INFERÊNCIA]** |
| 29 | `SupervisedBatchTests.plan_now()` | Auxilia plan now **[INFERÊNCIA]** |
| 37 | `SupervisedBatchTests.run_batch()` | Auxilia run batch **[INFERÊNCIA]** |
| 44 | `SupervisedBatchTests.test_batch_moves_all_three_and_reports_progress()` | Verifica batch moves all three and reports progress **[INFERÊNCIA]** |
| 58 | `SupervisedBatchTests.test_batch_skips_collision_and_moves_remaining_files()` | Verifica batch skips collision and moves remaining files **[INFERÊNCIA]** |
| 72 | `SupervisedBatchTests.test_missing_approval_rejects_before_writing()` | Verifica missing approval rejects before writing **[INFERÊNCIA]** |
| 77 | `SupervisedBatchTests.test_reject_unplanned_or_duplicate_names()` | Verifica reject unplanned or duplicate names **[INFERÊNCIA]** |
| 85 | `SupervisedBatchTests.test_reject_incomplete_or_different_snapshot()` | Verifica reject incomplete or different snapshot **[INFERÊNCIA]** |
| 96 | `SupervisedBatchTests.test_copy_preserved_stops_batch_without_removing_other_files()` | Verifica copy preserved stops batch without removing other files **[INFERÊNCIA]** |

## `tests/test_catalog.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 17 | `CatalogTests.test_persists_snapshot_without_changing_media()` | Verifica persists snapshot without changing media **[INFERÊNCIA]** |
| 42 | `CatalogTests.test_rejects_incomplete_inventory()` | Verifica rejects incomplete inventory **[INFERÊNCIA]** |
| 57 | `CatalogTests.test_query_latest_snapshot_and_category_filter()` | Verifica query latest snapshot and category filter **[INFERÊNCIA]** |
| 79 | `CatalogTests.test_summary_uses_latest_snapshot_without_listing_files()` | Verifica summary uses latest snapshot without listing files **[INFERÊNCIA]** |
| 97 | `CatalogTests.test_universal_catalog_persists_and_filters_without_migration()` | Verifica universal catalog persists and filters without migration **[INFERÊNCIA]** |
| 122 | `CatalogTests.test_summary_missing_database_never_creates_file()` | Verifica summary missing database never creates file **[INFERÊNCIA]** |
| 129 | `CatalogTests.test_pagination_and_category_filters_are_read_only()` | Verifica pagination and category filters are read only **[INFERÊNCIA]** |
| 155 | `CatalogTests.test_pagination_rejects_bad_limits_and_missing_database()` | Verifica pagination rejects bad limits and missing database **[INFERÊNCIA]** |
| 172 | `CatalogTests.test_history_lists_snapshots_and_selects_previous_scan()` | Verifica history lists snapshots and selects previous scan **[INFERÊNCIA]** |
| 195 | `CatalogTests.test_history_rejects_invalid_ids_and_missing_database()` | Verifica history rejects invalid ids and missing database **[INFERÊNCIA]** |
| 213 | `CatalogTests.test_origins_summary_uses_only_latest_snapshot_for_each_root()` | Verifica origins summary uses only latest snapshot for each root **[INFERÊNCIA]** |
| 243 | `CatalogTests.test_origins_summary_missing_database_and_empty_catalog()` | Verifica origins summary missing database and empty catalog **[INFERÊNCIA]** |
| 257 | `CatalogTests.test_search_name_extension_history_and_literal_wildcards()` | Verifica search name extension history and literal wildcards **[INFERÊNCIA]** |
| 286 | `CatalogTests.test_search_filters_reject_invalid_inputs()` | Verifica search filters reject invalid inputs **[INFERÊNCIA]** |
| 297 | `CatalogTests.test_filename_scope_excludes_directory_matches()` | Verifica filename scope excludes directory matches **[INFERÊNCIA]** |
| 314 | `CatalogTests.test_modified_date_range_and_sorting()` | Verifica modified date range and sorting **[INFERÊNCIA]** |
| 347 | `CatalogTests.test_search_scope_and_date_validations()` | Verifica search scope and date validations **[INFERÊNCIA]** |
| 366 | `CatalogTests.test_query_missing_database_does_not_create_it()` | Verifica query missing database does not create it **[INFERÊNCIA]** |

## `tests/test_cataloging.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 11 | `CatalogingTests.test_valid_preview_creates_snapshot_only_in_sqlite()` | Verifica valid preview creates snapshot only in sqlite **[INFERÊNCIA]** |
| 25 | `CatalogingTests.test_modified_file_rejects_without_creating_db()` | Verifica modified file rejects without creating db **[INFERÊNCIA]** |
| 38 | `CatalogingTests.test_added_file_rejects_without_creating_db()` | Verifica added file rejects without creating db **[INFERÊNCIA]** |
| 50 | `CatalogingTests.test_incomplete_or_invalid_preview_rejected()` | Verifica incomplete or invalid preview rejected **[INFERÊNCIA]** |

## `tests/test_conflict_hash.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 11 | `PlanConflictHashTests.setUp()` | Prepara fixtures e estado para cada teste **[INFERÊNCIA]** |
| 31 | `PlanConflictHashTests.tearDown()` | Encerra recursos e limpa fixtures após cada teste **[INFERÊNCIA]** |
| 35 | `PlanConflictHashTests.verify()` | Auxilia verify **[INFERÊNCIA]** |
| 42 | `PlanConflictHashTests.test_identical_bytes_confirm_duplicate_read_only()` | Verifica identical bytes confirm duplicate read only **[INFERÊNCIA]** |
| 50 | `PlanConflictHashTests.test_different_bytes_confirm_conflict_not_duplicate()` | Verifica different bytes confirm conflict not duplicate **[INFERÊNCIA]** |
| 57 | `PlanConflictHashTests.test_modified_source_is_inconclusive()` | Verifica modified source is inconclusive **[INFERÊNCIA]** |
| 63 | `PlanConflictHashTests.test_missing_destination_is_inconclusive()` | Verifica missing destination is inconclusive **[INFERÊNCIA]** |
| 68 | `PlanConflictHashTests.test_reject_ambiguous_or_unplanned_names()` | Verifica reject ambiguous or unplanned names **[INFERÊNCIA]** |
| 80 | `PlanConflictHashTests.test_reject_stale_snapshot()` | Verifica reject stale snapshot **[INFERÊNCIA]** |
| 89 | `PlanConflictHashTests.test_agent_calls_hash_tool_across_turns()` | Verifica agent calls hash tool across turns **[INFERÊNCIA]** |

## `tests/test_conflict_move.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 12 | `ConflictMoveTests.setUp()` | Prepara fixtures e estado para cada teste **[INFERÊNCIA]** |
| 27 | `ConflictMoveTests.tearDown()` | Encerra recursos e limpa fixtures após cada teste **[INFERÊNCIA]** |
| 31 | `ConflictMoveTests.new_plan()` | Auxilia new plan **[INFERÊNCIA]** |
| 38 | `ConflictMoveTests.preview()` | Auxilia preview **[INFERÊNCIA]** |
| 44 | `ConflictMoveTests.move()` | Auxilia move **[INFERÊNCIA]** |
| 51 | `ConflictMoveTests.test_different_content_preserves_original_destination_and_moves_renamed()` | Verifica different content preserves original destination and moves renamed **[INFERÊNCIA]** |
| 64 | `ConflictMoveTests.test_existing_alternative_generates_next_free_name()` | Verifica existing alternative generates next free name **[INFERÊNCIA]** |
| 72 | `ConflictMoveTests.test_alternative_changed_after_confirmation_is_rejected()` | Verifica alternative changed after confirmation is rejected **[INFERÊNCIA]** |
| 80 | `ConflictMoveTests.test_identical_content_never_executes_conflict_move()` | Verifica identical content never executes conflict move **[INFERÊNCIA]** |
| 89 | `ConflictMoveTests.test_wrong_approval_or_unconfirmed_name_cannot_move()` | Verifica wrong approval or unconfirmed name cannot move **[INFERÊNCIA]** |
| 99 | `ConflictMoveTests.test_changed_source_blocks_rename()` | Verifica changed source blocks rename **[INFERÊNCIA]** |
| 107 | `ConflictMoveTests.test_ambiguous_sources_are_not_automatically_resolved()` | Verifica ambiguous sources are not automatically resolved **[INFERÊNCIA]** |

## `tests/test_conflict_report.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 10 | `ConflictReportTests.setUp()` | Prepara fixtures e estado para cada teste **[INFERÊNCIA]** |
| 29 | `ConflictReportTests.tearDown()` | Encerra recursos e limpa fixtures após cada teste **[INFERÊNCIA]** |
| 33 | `ConflictReportTests.report()` | Auxilia report **[INFERÊNCIA]** |
| 41 | `ConflictReportTests.test_identical_preserves_both_files()` | Verifica identical preserves both files **[INFERÊNCIA]** |
| 51 | `ConflictReportTests.test_different_content_suggests_unused_filename_without_creating()` | Verifica different content suggests unused filename without creating **[INFERÊNCIA]** |
| 61 | `ConflictReportTests.test_inconclusive_when_source_changes()` | Verifica inconclusive when source changes **[INFERÊNCIA]** |
| 67 | `ConflictReportTests.test_report_limit_and_snapshot_validation()` | Verifica report limit and snapshot validation **[INFERÊNCIA]** |
| 75 | `ConflictReportTests.test_ambiguous_conflict_does_not_guess_a_source()` | Verifica ambiguous conflict does not guess a source **[INFERÊNCIA]** |
| 90 | `ConflictReportTests.test_agent_uses_report_on_next_question()` | Verifica agent uses report on next question **[INFERÊNCIA]** |

## `tests/test_date_formats.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 9 | `DateFormatsTests.test_parse_formats_into_same_iso_day()` | Verifica parse formats into same iso day **[INFERÊNCIA]** |
| 20 | `DateFormatsTests.test_masks_insert_locale_separators()` | Verifica masks insert locale separators **[INFERÊNCIA]** |
| 28 | `DateFormatsTests.test_masked_blank_fields_and_incomplete_dates()` | Verifica masked blank fields and incomplete dates **[INFERÊNCIA]** |
| 40 | `DateFormatsTests.test_display_timestamp_in_utc()` | Verifica display timestamp in utc **[INFERÊNCIA]** |
| 46 | `DateFormatsTests.test_empty_date_and_reject_invalid_or_ambiguous()` | Verifica empty date and reject invalid or ambiguous **[INFERÊNCIA]** |

## `tests/test_direct_preparation.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 9 | `DirectPreparationTests.setUp()` | Prepara fixtures e estado para cada teste **[INFERÊNCIA]** |
| 21 | `DirectPreparationTests.tearDown()` | Encerra recursos e limpa fixtures após cada teste **[INFERÊNCIA]** |
| 25 | `DirectPreparationTests.test_direct_preparation_has_same_plan_contract_without_changes()` | Verifica direct preparation has same plan contract without changes **[INFERÊNCIA]** |
| 37 | `DirectPreparationTests.test_prepare_refreshes_snapshot_after_source_changes()` | Verifica prepare refreshes snapshot after source changes **[INFERÊNCIA]** |
| 45 | `DirectPreparationTests.test_prepare_video_category_ignores_images()` | Verifica prepare video category ignores images **[INFERÊNCIA]** |
| 56 | `DirectPreparationTests.test_prepare_audio_category_and_refresh_replaces_previous_plan()` | Verifica prepare audio category and refresh replaces previous plan **[INFERÊNCIA]** |
| 66 | `DirectPreparationTests.test_analyze_without_destination_is_complete_and_read_only()` | Verifica analyze without destination is complete and read only **[INFERÊNCIA]** |
| 76 | `DirectPreparationTests.test_full_preparation_over_500_keeps_cross_page_collisions()` | Verifica full preparation over 500 keeps cross page collisions **[INFERÊNCIA]** |
| 105 | `DirectPreparationTests.test_realistic_library_counts_complete_all_three_categories()` | Verifica realistic library counts complete all three categories **[INFERÊNCIA]** |
| 127 | `DirectPreparationTests.test_prepare_rejects_nonexistent_destination()` | Verifica prepare rejects nonexistent destination **[INFERÊNCIA]** |

## `tests/test_duplicate_basename_queue_v2.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 12 | `AmbiguousBasenameQueueTests.setUp()` | Prepara fixtures e estado para cada teste **[INFERÊNCIA]** |
| 28 | `AmbiguousBasenameQueueTests.tearDown()` | Encerra recursos e limpa fixtures após cada teste **[INFERÊNCIA]** |
| 32 | `AmbiguousBasenameQueueTests.test_plan_blocks_all_ambiguous_sources_and_moves_remaining()` | Verifica plan blocks all ambiguous sources and moves remaining **[INFERÊNCIA]** |
| 56 | `AmbiguousBasenameQueueTests.test_legacy_plan_ambiguous_item_is_safe_block_not_fatal_error()` | Verifica legacy plan ambiguous item is safe block not fatal error **[INFERÊNCIA]** |
| 79 | `AmbiguousBasenameQueueTests.test_batch_also_continues_after_safe_ambiguity()` | Verifica batch also continues after safe ambiguity **[INFERÊNCIA]** |

## `tests/test_duplicate_sessions.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 15 | `ProgressiveDuplicateSessionTests._make()` | Auxilia  make **[INFERÊNCIA]** |
| 25 | `ProgressiveDuplicateSessionTests.test_progressive_matches_hashes_across_six_batches()` | Verifica progressive matches hashes across six batches **[INFERÊNCIA]** |
| 53 | `ProgressiveDuplicateSessionTests.test_per_batch_limits_mark_skipped_without_false_completeness()` | Verifica per batch limits mark skipped without false completeness **[INFERÊNCIA]** |
| 67 | `ProgressiveDuplicateSessionTests.test_session_stays_on_selected_snapshot_after_new_catalog()` | Verifica session stays on selected snapshot after new catalog **[INFERÊNCIA]** |
| 80 | `ProgressiveDuplicateSessionTests.test_modified_file_is_skipped_in_next_batch()` | Verifica modified file is skipped in next batch **[INFERÊNCIA]** |
| 91 | `ProgressiveDuplicateSessionTests.test_invalid_limits_and_missing_catalog()` | Verifica invalid limits and missing catalog **[INFERÊNCIA]** |

## `tests/test_duplicates.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 18 | `DuplicateHashTests._catalog_fixture()` | Auxilia  catalog fixture **[INFERÊNCIA]** |
| 25 | `DuplicateHashTests.test_identifies_same_bytes_across_names_and_zero_byte_files()` | Verifica identifies same bytes across names and zero byte files **[INFERÊNCIA]** |
| 51 | `DuplicateHashTests.test_limits_skip_large_files_and_incomplete_sample()` | Verifica limits skip large files and incomplete sample **[INFERÊNCIA]** |
| 66 | `DuplicateHashTests.test_rejects_invalid_limits_and_unavailable_catalog()` | Verifica rejects invalid limits and unavailable catalog **[INFERÊNCIA]** |
| 81 | `DuplicateHashTests.test_changed_or_missing_sources_are_not_reported_equal()` | Verifica changed or missing sources are not reported equal **[INFERÊNCIA]** |
| 92 | `DuplicateHashTests.test_paged_scan_detects_equal_content_across_pages()` | Verifica paged scan detects equal content across pages **[INFERÊNCIA]** |
| 121 | `DuplicateHashTests.test_page_limit_prevents_false_global_completeness()` | Verifica page limit prevents false global completeness **[INFERÊNCIA]** |
| 142 | `DuplicateHashTests.test_progress_input_validation_and_budget_maximum()` | Verifica progress input validation and budget maximum **[INFERÊNCIA]** |
| 161 | `DuplicateHashTests.test_total_read_budget_is_respected()` | Verifica total read budget is respected **[INFERÊNCIA]** |

## `tests/test_duplicates_global.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 17 | `GlobalCandidatesTests.test_global_scope_uses_all_eight_fixture_files()` | Verifica global scope uses all eight fixture files **[INFERÊNCIA]** |
| 38 | `GlobalCandidatesTests.test_group_not_sliced_even_when_larger_than_candidate_limit()` | Verifica group not sliced even when larger than candidate limit **[INFERÊNCIA]** |
| 63 | `GlobalCandidatesTests.test_global_detects_distant_pair_in_snapshot_above_one_thousand()` | Verifica global detects distant pair in snapshot above one thousand **[INFERÊNCIA]** |
| 83 | `GlobalCandidatesTests.test_global_rejects_invalid_args_and_preserves_originals()` | Verifica global rejects invalid args and preserves originals **[INFERÊNCIA]** |

## `tests/test_executor.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 13 | `ExecutorTests._setup()` | Auxilia  setup **[INFERÊNCIA]** |
| 25 | `ExecutorTests.test_moves_one_fixture_with_explicit_approval_and_journal()` | Verifica moves one fixture with explicit approval and journal **[INFERÊNCIA]** |
| 41 | `ExecutorTests.test_inspect_completed_move_without_recovery()` | Verifica inspect completed move without recovery **[INFERÊNCIA]** |
| 52 | `ExecutorTests.test_inspect_interrupted_move_leaves_files_untouched()` | Verifica inspect interrupted move leaves files untouched **[INFERÊNCIA]** |
| 72 | `ExecutorTests.test_recover_interrupted_fixture_with_verified_hardlink()` | Verifica recover interrupted fixture with verified hardlink **[INFERÊNCIA]** |
| 94 | `ExecutorTests.test_recovery_rejects_wrong_identity_and_missing_confirmation()` | Verifica recovery rejects wrong identity and missing confirmation **[INFERÊNCIA]** |
| 112 | `ExecutorTests.test_recovery_rejects_completed_operation_and_does_not_delete()` | Verifica recovery rejects completed operation and does not delete **[INFERÊNCIA]** |
| 122 | `ExecutorTests.test_inspection_rejects_corrupt_journal_and_outside_runtime()` | Verifica inspection rejects corrupt journal and outside runtime **[INFERÊNCIA]** |
| 137 | `ExecutorTests.test_move_refuses_concurrent_fixture_lock()` | Verifica move refuses concurrent fixture lock **[INFERÊNCIA]** |
| 152 | `ExecutorTests.test_recovery_refuses_concurrent_fixture_lock()` | Verifica recovery refuses concurrent fixture lock **[INFERÊNCIA]** |
| 170 | `ExecutorTests.test_move_rechecks_source_after_destination_logged()` | Verifica move rechecks source after destination logged **[INFERÊNCIA]** |
| 176 | `ExecutorTests.mutate_after_record()` | Auxilia mutate after record **[INFERÊNCIA]** |
| 193 | `ExecutorTests.test_rejects_missing_approval_and_preserves_fixture()` | Verifica rejects missing approval and preserves fixture **[INFERÊNCIA]** |
| 201 | `ExecutorTests.test_rejects_occupied_target_and_changed_source()` | Verifica rejects occupied target and changed source **[INFERÊNCIA]** |
| 216 | `ExecutorTests.test_rejects_tampered_and_partial_plans()` | Verifica rejects tampered and partial plans **[INFERÊNCIA]** |
| 233 | `ExecutorTests.test_rejects_destination_outside_test_runtime()` | Verifica rejects destination outside test runtime **[INFERÊNCIA]** |

