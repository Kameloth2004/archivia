# Catálogo de testes e simulações — parte 3/3

Referência: `Kameloth2004/archivia`, branch `feat/v2-video-thumbnails-2026-11-27`, commit `2afb6c97edff83cadd013136ea1573ee3b66aaf9` (28/11/2026). Inclui todos os métodos `test_*`, fixtures, helpers e simulações definidos nestes arquivos. A descrição de funções sem docstring é **inferida pelo nome**, devendo ser complementada por inspeção do teste antes de afirmar comportamento exato.

## `tests/test_metadata_v2.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 27 | `MetadataReaderTests.test_common_properties_for_any_regular_file_without_content_reading()` | Verifica common properties for any regular file without content reading **[INFERÊNCIA]** |
| 39 | `MetadataReaderTests.test_missing_or_non_regular_file_is_rejected()` | Verifica missing or non regular file is rejected **[INFERÊNCIA]** |
| 47 | `MetadataReaderTests.test_image_exposes_every_recognized_exif_including_user_comment()` | Verifica image exposes every recognized exif including user comment **[INFERÊNCIA]** |
| 69 | `MetadataReaderTests.test_jpeg_exif_binary_block_is_not_duplicated_in_main_report()` | Verifica jpeg exif binary block is not duplicated in main report **[INFERÊNCIA]** |
| 97 | `MetadataReaderTests.test_exiftool_all_tags_are_displayed_even_in_documents()` | Verifica exiftool all tags are displayed even in documents **[INFERÊNCIA]** |
| 124 | `MetadataReaderTests.test_exiftool_unavailable_on_nonimage_provides_explanatory_fallback()` | Verifica exiftool unavailable on nonimage provides explanatory fallback **[INFERÊNCIA]** |
| 134 | `MetadataReaderTests.test_binary_values_are_described_not_hidden_by_privacy()` | Verifica binary values are described not hidden by privacy **[INFERÊNCIA]** |
| 146 | `ExplorerMetadataTests.setUpClass()` | Auxilia setUpClass **[INFERÊNCIA]** |
| 149 | `ExplorerMetadataTests.setUp()` | Prepara fixtures e estado para cada teste **[INFERÊNCIA]** |
| 158 | `ExplorerMetadataTests.tearDown()` | Encerra recursos e limpa fixtures após cada teste **[INFERÊNCIA]** |
| 162 | `ExplorerMetadataTests.test_selection_does_not_read_internal_metadata()` | Verifica selection does not read internal metadata **[INFERÊNCIA]** |
| 172 | `ExplorerMetadataTests.test_explicit_button_starts_background_task_and_displays_result()` | Verifica explicit button starts background task and displays result **[INFERÊNCIA]** |
| 190 | `ExplorerMetadataTests.test_selection_change_discards_stale_metadata()` | Verifica selection change discards stale metadata **[INFERÊNCIA]** |
| 206 | `ExplorerMetadataTests.test_task_reads_only_when_run_and_validates_file_identity()` | Verifica task reads only when run and validates file identity **[INFERÊNCIA]** |

## `tests/test_move_executor.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 11 | `ApprovedMoveTests.setUp()` | Prepara fixtures e estado para cada teste **[INFERÊNCIA]** |
| 25 | `ApprovedMoveTests.tearDown()` | Encerra recursos e limpa fixtures após cada teste **[INFERÊNCIA]** |
| 29 | `ApprovedMoveTests.new_plan()` | Auxilia new plan **[INFERÊNCIA]** |
| 37 | `ApprovedMoveTests.move()` | Auxilia move **[INFERÊNCIA]** |
| 45 | `ApprovedMoveTests.test_real_move_requires_approval_and_checks_hash()` | Verifica real move requires approval and checks hash **[INFERÊNCIA]** |
| 57 | `ApprovedMoveTests.test_destination_collision_never_overwrites()` | Verifica destination collision never overwrites **[INFERÊNCIA]** |
| 64 | `ApprovedMoveTests.test_modified_source_keeps_original_and_no_target()` | Verifica modified source keeps original and no target **[INFERÊNCIA]** |
| 71 | `ApprovedMoveTests.test_reject_blocked_and_ambiguous_files()` | Verifica reject blocked and ambiguous files **[INFERÊNCIA]** |
| 82 | `ApprovedMoveTests.test_wrong_snapshot_or_unknown_file_rejected()` | Verifica wrong snapshot or unknown file rejected **[INFERÊNCIA]** |
| 90 | `ApprovedMoveTests.test_simulation_tool_registry_does_not_expose_executor()` | Verifica simulation tool registry does not expose executor **[INFERÊNCIA]** |

## `tests/test_move_pipeline.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 16 | `MovePipelineTests._setup()` | Auxilia  setup **[INFERÊNCIA]** |
| 29 | `MovePipelineTests.test_verified_move_after_hash_preserves_content()` | Verifica verified move after hash preserves content **[INFERÊNCIA]** |
| 47 | `MovePipelineTests.test_requires_distinct_explicit_approval()` | Verifica requires distinct explicit approval **[INFERÊNCIA]** |
| 57 | `MovePipelineTests.test_never_overwrites_occupied_destination()` | Verifica never overwrites occupied destination **[INFERÊNCIA]** |
| 66 | `MovePipelineTests.test_rejects_partial_and_tampered_plan()` | Verifica rejects partial and tampered plan **[INFERÊNCIA]** |
| 79 | `MovePipelineTests.test_failed_copy_preserves_original()` | Verifica failed copy preserves original **[INFERÊNCIA]** |
| 85 | `MovePipelineTests.interrupted_hash()` | Auxilia interrupted hash **[INFERÊNCIA]** |
| 97 | `MovePipelineTests.test_failed_unlink_leaves_source_and_verified_destination()` | Verifica failed unlink leaves source and verified destination **[INFERÊNCIA]** |
| 107 | `MovePipelineTests.test_rejects_existing_operation_journal()` | Verifica rejects existing operation journal **[INFERÊNCIA]** |
| 116 | `MovePipelineTests.test_rejects_concurrent_lock()` | Verifica rejects concurrent lock **[INFERÊNCIA]** |

## `tests/test_nested_destination.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 11 | `NestedDestinationTests.setUp()` | Prepara fixtures e estado para cada teste **[INFERÊNCIA]** |
| 25 | `NestedDestinationTests.tearDown()` | Encerra recursos e limpa fixtures após cada teste **[INFERÊNCIA]** |
| 29 | `NestedDestinationTests.test_moves_from_root_into_internal_directory()` | Verifica moves from root into internal directory **[INFERÊNCIA]** |
| 51 | `NestedDestinationTests.test_never_moves_items_already_within_destination()` | Verifica never moves items already within destination **[INFERÊNCIA]** |
| 72 | `NestedDestinationTests.test_existing_name_collision_is_not_overwritten()` | Verifica existing name collision is not overwritten **[INFERÊNCIA]** |
| 79 | `NestedDestinationTests.test_identical_root_destination_is_rejected()` | Verifica identical root destination is rejected **[INFERÊNCIA]** |

## `tests/test_plan_memory.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 11 | `PlanMemoryTests._plan()` | Auxilia  plan **[INFERÊNCIA]** |
| 24 | `PlanMemoryTests.test_memory_explains_conflict_without_claiming_duplicate()` | Verifica memory explains conflict without claiming duplicate **[INFERÊNCIA]** |
| 33 | `PlanMemoryTests.test_filter_by_file_name_and_invalid_requests()` | Verifica filter by file name and invalid requests **[INFERÊNCIA]** |
| 44 | `PlanMemoryTests.test_only_accepted_plan_from_current_snapshot_is_saved()` | Verifica only accepted plan from current snapshot is saved **[INFERÊNCIA]** |
| 54 | `PlanMemoryTests.test_dispatch_is_bound_to_same_snapshot_and_denies_extra_keys()` | Verifica dispatch is bound to same snapshot and denies extra keys **[INFERÊNCIA]** |
| 68 | `PlanMemoryTests.test_session_remembers_plan_across_questions_and_forgets_after_refresh()` | Verifica session remembers plan across questions and forgets after refresh **[INFERÊNCIA]** |
| 104 | `PlanMemoryTests.test_older_plan_remains_after_nonplanning_followup()` | Verifica older plan remains after nonplanning followup **[INFERÊNCIA]** |

## `tests/test_planner.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 13 | `PlannerTests.test_proposes_without_moving_or_modifying()` | Verifica proposes without moving or modifying **[INFERÊNCIA]** |
| 32 | `PlannerTests.test_blocks_existing_destination()` | Verifica blocks existing destination **[INFERÊNCIA]** |
| 48 | `PlannerTests.test_blocks_duplicate_target_names_from_different_folders()` | Verifica blocks duplicate target names from different folders **[INFERÊNCIA]** |
| 66 | `PlannerTests.test_blocks_changed_file()` | Verifica blocks changed file **[INFERÊNCIA]** |
| 81 | `PlannerTests.test_invalid_limit_or_destination()` | Verifica invalid limit or destination **[INFERÊNCIA]** |
| 93 | `PlannerTests.test_flat_consolidation_is_paginated_without_loading_full_catalog()` | Verifica flat consolidation is paginated without loading full catalog **[INFERÊNCIA]** |
| 125 | `PlannerTests.test_flat_plan_can_select_older_snapshot_without_changing_sources()` | Verifica flat plan can select older snapshot without changing sources **[INFERÊNCIA]** |
| 148 | `PlannerTests.test_full_consolidation_detects_cross_page_collisions_without_writing()` | Verifica full consolidation detects cross page collisions without writing **[INFERÊNCIA]** |
| 177 | `PlannerTests.test_full_consolidation_cap_reports_pending_and_keeps_other_snapshot_out()` | Verifica full consolidation cap reports pending and keeps other snapshot out **[INFERÊNCIA]** |
| 207 | `PlannerTests.test_full_consolidation_blocks_existing_casefold_and_changed_sources()` | Verifica full consolidation blocks existing casefold and changed sources **[INFERÊNCIA]** |
| 229 | `PlannerTests.test_date_plan_proposes_year_month_without_writing()` | Verifica date plan proposes year month without writing **[INFERÊNCIA]** |
| 253 | `PlannerTests.test_date_plan_collision_and_changed_files_are_blocked()` | Verifica date plan collision and changed files are blocked **[INFERÊNCIA]** |
| 277 | `PlannerTests.test_date_plan_flags_metadata_duplicates_without_hashing_or_writing()` | Verifica date plan flags metadata duplicates without hashing or writing **[INFERÊNCIA]** |
| 302 | `PlannerTests.test_date_plan_suggests_name_when_target_exists_without_overwriting()` | Verifica date plan suggests name when target exists without overwriting **[INFERÊNCIA]** |
| 325 | `PlannerTests.test_date_plan_rejects_missing_destination_and_invalid_limits()` | Verifica date plan rejects missing destination and invalid limits **[INFERÊNCIA]** |
| 339 | `PlannerTests.test_plan_never_creates_destination()` | Verifica plan never creates destination **[INFERÊNCIA]** |

## `tests/test_preview.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 10 | `PreviewTests.test_pages_filter_and_no_files_modified()` | Verifica pages filter and no files modified **[INFERÊNCIA]** |
| 33 | `PreviewTests.test_validation()` | Verifica validation **[INFERÊNCIA]** |
| 50 | `PreviewTests.test_empty_category_and_beyond_last_page()` | Verifica empty category and beyond last page **[INFERÊNCIA]** |

## `tests/test_queue_move.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 12 | `QueueMoveTests.setUp()` | Prepara fixtures e estado para cada teste **[INFERÊNCIA]** |
| 29 | `QueueMoveTests.tearDown()` | Encerra recursos e limpa fixtures após cada teste **[INFERÊNCIA]** |
| 33 | `QueueMoveTests.run_queue()` | Auxilia run queue **[INFERÊNCIA]** |
| 40 | `QueueMoveTests.test_moves_all_approved_without_touching_other_files()` | Verifica moves all approved without touching other files **[INFERÊNCIA]** |
| 51 | `QueueMoveTests.test_interrupt_between_files_preserves_remaining_origins()` | Verifica interrupt between files preserves remaining origins **[INFERÊNCIA]** |
| 66 | `QueueMoveTests.test_safe_collision_is_reported_and_remaining_files_are_moved()` | Verifica safe collision is reported and remaining files are moved **[INFERÊNCIA]** |
| 79 | `QueueMoveTests.test_reject_bad_authorization_or_unplanned_files()` | Verifica reject bad authorization or unplanned files **[INFERÊNCIA]** |
| 88 | `QueueMoveTests.test_inconclusive_copy_stops_queue()` | Verifica inconclusive copy stops queue **[INFERÊNCIA]** |

## `tests/test_recursive_plan.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 13 | `RecursivePlanningTests.setup_case()` | Auxilia setup case **[INFERÊNCIA]** |
| 27 | `RecursivePlanningTests.test_recursion_and_name_conflicts_do_not_move_anything()` | Verifica recursion and name conflicts do not move anything **[INFERÊNCIA]** |
| 50 | `RecursivePlanningTests.test_partial_plan_is_explicit()` | Verifica partial plan is explicit **[INFERÊNCIA]** |
| 60 | `RecursivePlanningTests.test_existing_destination_blocks_without_replacement()` | Verifica existing destination blocks without replacement **[INFERÊNCIA]** |
| 68 | `RecursivePlanningTests.test_nested_destination_skips_files_already_inside()` | Verifica nested destination skips files already inside **[INFERÊNCIA]** |
| 83 | `RecursivePlanningTests.test_same_folder_is_still_rejected()` | Verifica same folder is still rejected **[INFERÊNCIA]** |
| 89 | `RecursivePlanningTests.test_model_tool_is_allowlisted_and_bounded()` | Verifica model tool is allowlisted and bounded **[INFERÊNCIA]** |
| 119 | `RecursivePlanningTests.test_ollama_mock_requests_plan_but_never_executes()` | Verifica ollama mock requests plan but never executes **[INFERÊNCIA]** |

## `tests/test_root_only_scope.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 12 | `RootOnlyScopeTests.setUp()` | Prepara fixtures e estado para cada teste **[INFERÊNCIA]** |
| 27 | `RootOnlyScopeTests.tearDown()` | Encerra recursos e limpa fixtures após cada teste **[INFERÊNCIA]** |
| 31 | `RootOnlyScopeTests.test_inventory_only_root_files_without_visiting_subdirectories()` | Verifica inventory only root files without visiting subdirectories **[INFERÊNCIA]** |
| 39 | `RootOnlyScopeTests.test_root_only_analysis_and_plan_ignore_subfolders()` | Verifica root only analysis and plan ignore subfolders **[INFERÊNCIA]** |
| 56 | `RootOnlyScopeTests.test_real_move_only_root_and_preserves_subfolder_contents()` | Verifica real move only root and preserves subfolder contents **[INFERÊNCIA]** |
| 77 | `RootOnlyScopeTests.test_recursive_default_still_sees_nested_images()` | Verifica recursive default still sees nested images **[INFERÊNCIA]** |
| 86 | `RootOnlyScopeTests.test_executor_enforces_declared_root_only_scope()` | Verifica executor enforces declared root only scope **[INFERÊNCIA]** |
| 98 | `RootOnlyScopeTests.test_only_subfolders_results_in_empty_valid_plan()` | Verifica only subfolders results in empty valid plan **[INFERÊNCIA]** |

## `tests/test_sha256_paged_fixture.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 15 | `PagedFixtureTests.test_generator_produces_expected_groups_between_pages_without_changes()` | Verifica generator produces expected groups between pages without changes **[INFERÊNCIA]** |
| 51 | `PagedFixtureTests.test_sample_of_100_is_partial_and_cross_page_pairs_can_be_missed()` | Verifica sample of 100 is partial and cross page pairs can be missed **[INFERÊNCIA]** |
| 68 | `PagedFixtureTests.test_generator_rejects_existing_content_and_paths_outside_tests()` | Verifica generator rejects existing content and paths outside tests **[INFERÊNCIA]** |

## `tests/test_table_rows.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 11 | `TableRowsTests.test_inventory_rows_are_immutable_presentations()` | Verifica inventory rows are immutable presentations **[INFERÊNCIA]** |
| 20 | `TableRowsTests.test_origin_rows()` | Verifica origin rows **[INFERÊNCIA]** |
| 25 | `TableRowsTests.test_duplicate_rows_repeat_original_tooltips()` | Verifica duplicate rows repeat original tooltips **[INFERÊNCIA]** |
| 34 | `TableRowsTests.test_date_plan_rows_preserve_reason_and_warning()` | Verifica date plan rows preserve reason and warning **[INFERÊNCIA]** |
| 43 | `TableRowsTests.test_date_plan_rows_show_future_subfolder()` | Verifica date plan rows show future subfolder **[INFERÊNCIA]** |
| 50 | `TableRowsTests.test_catalog_rows_keep_iso_original_for_date_toggle()` | Verifica catalog rows keep iso original for date toggle **[INFERÊNCIA]** |
| 64 | `TableRowsTests.test_empty_tables()` | Verifica empty tables **[INFERÊNCIA]** |

## `tests/test_universal_categories_v2.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 28 | `UniversalCategoriesV2Tests.test_category_list_has_all_indexed_groups()` | Verifica category list has all indexed groups **[INFERÊNCIA]** |
| 35 | `UniversalCategoriesV2Tests.test_root_only_plans_and_moves_every_category_safely()` | Verifica root only plans and moves every category safely **[INFERÊNCIA]** |
| 84 | `UniversalCategoriesV2Tests.test_other_includes_files_without_extension()` | Verifica other includes files without extension **[INFERÊNCIA]** |
| 95 | `UniversalCategoriesV2Tests.test_agent_simulations_accept_universal_categories_without_writing()` | Verifica agent simulations accept universal categories without writing **[INFERÊNCIA]** |
| 128 | `UniversalCategoriesV2Tests.test_conflicts_cannot_overwrite_documents_or_other_files()` | Verifica conflicts cannot overwrite documents or other files **[INFERÊNCIA]** |

## `tests/test_verified_copy.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 13 | `VerifiedCopyTests._setup()` | Auxilia  setup **[INFERÊNCIA]** |
| 25 | `VerifiedCopyTests.test_copy_preserves_source_and_checks_sha256()` | Verifica copy preserves source and checks sha256 **[INFERÊNCIA]** |
| 42 | `VerifiedCopyTests.test_inspect_published_copy_is_read_only()` | Verifica inspect published copy is read only **[INFERÊNCIA]** |
| 60 | `VerifiedCopyTests.test_inspect_failure_after_publication_preserves_both_files()` | Verifica inspect failure after publication preserves both files **[INFERÊNCIA]** |
| 66 | `VerifiedCopyTests.fail_publication_log()` | Auxilia fail publication log **[INFERÊNCIA]** |
| 84 | `VerifiedCopyTests.test_inspect_partial_copy_and_leftover_temp_without_cleanup()` | Verifica inspect partial copy and leftover temp without cleanup **[INFERÊNCIA]** |
| 104 | `VerifiedCopyTests.test_inspect_refuses_invalid_journal_and_outside_runtime()` | Verifica inspect refuses invalid journal and outside runtime **[INFERÊNCIA]** |
| 119 | `VerifiedCopyTests._interrupted_published_fixture()` | Auxilia  interrupted published fixture **[INFERÊNCIA]** |
| 123 | `VerifiedCopyTests.fail_published()` | Auxilia fail published **[INFERÊNCIA]** |
| 134 | `VerifiedCopyTests.test_reconcile_published_interrupted_journal_without_deleting()` | Verifica reconcile published interrupted journal without deleting **[INFERÊNCIA]** |
| 158 | `VerifiedCopyTests.test_reconcile_refuses_changed_destination_and_no_approval()` | Verifica reconcile refuses changed destination and no approval **[INFERÊNCIA]** |
| 172 | `VerifiedCopyTests.test_reconcile_refuses_leftover_temporary_without_removing_it()` | Verifica reconcile refuses leftover temporary without removing it **[INFERÊNCIA]** |
| 186 | `VerifiedCopyTests.test_reconcile_refuses_prepublication_interruption()` | Verifica reconcile refuses prepublication interruption **[INFERÊNCIA]** |
| 202 | `VerifiedCopyTests.test_copy_denies_without_explicit_approval()` | Verifica copy denies without explicit approval **[INFERÊNCIA]** |
| 210 | `VerifiedCopyTests.test_copy_refuses_existing_destination()` | Verifica copy refuses existing destination **[INFERÊNCIA]** |
| 219 | `VerifiedCopyTests.test_copy_refuses_partial_or_tampered_plan()` | Verifica copy refuses partial or tampered plan **[INFERÊNCIA]** |
| 233 | `VerifiedCopyTests.test_copy_rejects_lock_from_concurrent_fixture()` | Verifica copy rejects lock from concurrent fixture **[INFERÊNCIA]** |
| 248 | `VerifiedCopyTests.test_copy_failure_preserves_original_and_destination()` | Verifica copy failure preserves original and destination **[INFERÊNCIA]** |
| 265 | `VerifiedCopyTests.test_copy_refuses_reusing_journal()` | Verifica copy refuses reusing journal **[INFERÊNCIA]** |

## `tests/test_video_thumbnails_v2.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 24 | `VideoThumbnailTests.setUpClass()` | Auxilia setUpClass **[INFERÊNCIA]** |
| 27 | `VideoThumbnailTests.setUp()` | Prepara fixtures e estado para cada teste **[INFERÊNCIA]** |
| 36 | `VideoThumbnailTests.tearDown()` | Encerra recursos e limpa fixtures após cada teste **[INFERÊNCIA]** |
| 40 | `VideoThumbnailTests.test_rejects_old_generation_and_nonvideo()` | Verifica rejects old generation and nonvideo **[INFERÊNCIA]** |
| 46 | `VideoThumbnailTests.test_capture_emits_image_then_releases_source()` | Verifica capture emits image then releases source **[INFERÊNCIA]** |
| 55 | `VideoThumbnailTests.Frame.isValid()` | Auxilia isValid **[INFERÊNCIA]** |
| 57 | `VideoThumbnailTests.Frame.toImage()` | Auxilia toImage **[INFERÊNCIA]** |
| 68 | `VideoThumbnailTests.test_reset_discards_pending_and_active_work()` | Verifica reset discards pending and active work **[INFERÊNCIA]** |
| 79 | `VideoThumbnailTests.test_cache_hit_returns_without_decoding()` | Verifica cache hit returns without decoding **[INFERÊNCIA]** |
| 91 | `VideoThumbnailTests.test_failed_file_is_not_decoded_again_for_same_identity()` | Verifica failed file is not decoded again for same identity **[INFERÊNCIA]** |
| 103 | `VideoThumbnailTests.test_first_frame_does_not_require_seek()` | Verifica first frame does not require seek **[INFERÊNCIA]** |
| 115 | `VideoThumbnailTests.test_timeout_does_not_abort_next_generation()` | Verifica timeout does not abort next generation **[INFERÊNCIA]** |
| 121 | `VideoThumbnailTests.test_explorer_can_apply_video_overlay_to_matching_item()` | Verifica explorer can apply video overlay to matching item **[INFERÊNCIA]** |

## `tests/test_xmp_gui_v2.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 24 | `XmpGuiTests.setUpClass()` | Auxilia setUpClass **[INFERÊNCIA]** |
| 27 | `XmpGuiTests.setUp()` | Prepara fixtures e estado para cada teste **[INFERÊNCIA]** |
| 38 | `XmpGuiTests.tearDown()` | Encerra recursos e limpa fixtures após cada teste **[INFERÊNCIA]** |
| 41 | `XmpGuiTests.test_explorer_button_appears_only_after_explicit_metadata_result()` | Verifica explorer button appears only after explicit metadata result **[INFERÊNCIA]** |
| 64 | `XmpGuiTests.test_fullscreen_viewer_resets_raw_on_next_file()` | Verifica fullscreen viewer resets raw on next file **[INFERÊNCIA]** |
| 86 | `XmpGuiTests.test_raw_dialog_displays_complete_exif_bytes_instead_of_hex_preview()` | Verifica raw dialog displays complete exif bytes instead of hex preview **[INFERÊNCIA]** |
| 102 | `XmpGuiTests.test_raw_dialog_shows_full_text_without_modifying_source_file()` | Verifica raw dialog shows full text without modifying source file **[INFERÊNCIA]** |

## `tests/test_xmp_metadata_v2.py`

| Linha | Teste / helper / simulação | O que verifica ou realiza |
|---:|---|---|
| 32 | `XmpMetadataTests.test_structured_values_are_not_hex_or_truncated()` | Verifica structured values are not hex or truncated **[INFERÊNCIA]** |
| 43 | `XmpMetadataTests.test_no_whitelist_for_custom_xmp_fields()` | Verifica no whitelist for custom xmp fields **[INFERÊNCIA]** |
| 55 | `XmpMetadataTests.test_dtd_entities_are_rejected_but_raw_is_preserved()` | Verifica dtd entities are rejected but raw is preserved **[INFERÊNCIA]** |
| 64 | `XmpMetadataTests.test_real_png_pillow_reader_decodes_structured_xmp_and_preserves_raw()` | Verifica real png pillow reader decodes structured xmp and preserves raw **[INFERÊNCIA]** |
| 87 | `XmpMetadataTests.test_xmp_size_limit_is_explicit()` | Verifica xmp size limit is explicit **[INFERÊNCIA]** |

