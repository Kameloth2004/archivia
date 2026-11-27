"""TEST-ONLY: regressões estruturais da GUI sem abrir janelas Qt.

A suíte roda mesmo quando PySide6 não está instalado (aplicação opcional).
"""
from __future__ import annotations

import ast
from pathlib import Path
import unittest


GUI_FILE = Path(__file__).resolve().parents[1] / "src" / "archivia" / "gui.py"


class GUIStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tree = ast.parse(GUI_FILE.read_text(encoding="utf-8"))
        cls.window = next(
            node for node in cls.tree.body
            if isinstance(node, ast.ClassDef) and node.name == "ArchivIAWindow"
        )

    @classmethod
    def method(cls, name):
        return next(
            node for node in cls.window.body
            if isinstance(node, ast.FunctionDef) and node.name == name
        )

    def test_busy_guards_run_before_widget_mutations(self):
        for name in (
            "_run_inventory_preview", "_run_summary",
            "_run_date_plan", "_run_duplicate_hash",
        ):
            with self.subTest(name=name):
                method = self.method(name)
                first = method.body[0]
                self.assertIsInstance(first, ast.If)
                self.assertIn("self._worker is not None", ast.unparse(first.test))
                self.assertIsInstance(first.body[0], ast.Return)

    def test_catalog_dates_use_calendar_without_changing_search_contract(self):
        constructor = ast.unparse(self.method("__init__"))
        date_format = ast.unparse(self.method("_change_date_format"))
        filters = ast.unparse(self.method("_load_catalog_page"))
        self.assertIn("self.catalog_date_from = CalendarDateEdit(self._date_format)", constructor)
        self.assertIn("self.catalog_date_to = CalendarDateEdit(self._date_format)", constructor)
        self.assertIn("self.catalog_date_from.returnPressed.connect(self._reset_catalog_page)", constructor)
        self.assertIn("self.catalog_date_to.returnPressed.connect(self._reset_catalog_page)", constructor)
        self.assertIn("widget.set_date_format(next_format)", date_format)
        self.assertIn("date_from=self.catalog_date_from.text()", filters)
        self.assertIn("date_to=self.catalog_date_to.text()", filters)
        self.assertNotIn("QDateEdit(", constructor)

    def test_home_reuses_single_active_folder_and_does_not_stretch_notice(self):
        constructor = ast.unparse(self.method("__init__"))
        busy = ast.unparse(self.method("_set_busy"))
        self.assertIn("self.home_folder = self.folder", constructor)
        self.assertNotIn("home_source_box = QGroupBox(", constructor)
        self.assertNotIn("self.home_choose_button", constructor)
        self.assertIn("home_layout.addStretch(1)", constructor)
        self.assertIn("self.home_analyze_button.clicked.connect(self._analyze_home_source)", constructor)
        self.assertIn("self.home_folder.textChanged.connect(self._invalidate_home_organization)", constructor)
        self.assertIn("self.home_folder.textChanged.connect(self.organize_source.setText)", constructor)
        self.assertNotIn("self.home_choose_button", busy)

    def test_compact_global_toolbar_and_collapsible_home_analysis(self):
        constructor = ast.unparse(self.method("__init__"))
        label = ast.unparse(self.method("_refresh_home_analysis_label"))
        self.assertIn("self.active_folder_display.setMaximumWidth(520)", constructor)
        self.assertIn("active_row.addWidget(self.active_folder_choose)", constructor)
        self.assertIn("active_row.addWidget(self.active_folder_clear)", constructor)
        self.assertIn("active_row.addWidget(self.home_analyze_button)", constructor)
        self.assertIn("active_row.addWidget(self.open_organize_button)", constructor)
        self.assertEqual(constructor.count("home_layout.addWidget(self.home_analyze_button)"), 0)
        self.assertIn("self.home_analysis_toggle.setCheckable(True)", constructor)
        self.assertIn("self.home_analysis_toggle.toggled.connect(self.home_result.setVisible)", constructor)
        self.assertIn("self.home_result.setVisible(False)", constructor)
        self.assertIn("self.home_result.textChanged.connect(self._refresh_home_analysis_label)", constructor)
        self.assertIn("'Análise concluída'", label)
        self.assertIn("self.home_analysis_toggle.setText(", label)

    def test_active_folder_and_catalog_sources_are_isolated(self):
        constructor = ast.unparse(self.method("__init__"))
        current = ast.unparse(self.method("_folder_changed"))
        listing = ast.unparse(self.method("_load_catalog_page"))
        refresh = ast.unparse(self.method("_refresh_active_catalog"))
        finished = ast.unparse(self.method("_worker_done"))
        worker = (GUI_FILE.parent / "gui_worker.py").read_text(encoding="utf-8")
        self.assertIn("self.active_folder_choose.clicked.connect(self._choose_folder)", constructor)
        self.assertIn("self.active_folder_clear.clicked.connect(self._clear_active_folder)", constructor)
        self.assertIn("self.catalog_source.addItem('Pasta ativa (sessão)', 'active')", constructor)
        self.assertIn("self._active_folder = active", current)
        self.assertIn("self._folder_session.close()", current)
        self.assertIn("self._clear_catalog_table_for_session()", current)
        self.assertIn("folder_session=session", listing)
        self.assertIn("scan_id=None if active_mode else self.history_select.currentData()", listing)
        self.assertIn('self._start_worker(', refresh)
        self.assertIn('completed_mode == "refresh_folder_session"', finished.replace(chr(39), chr(34)))
        self.assertIn("database = self.folder_session._db", worker)
        self.assertIn("scan_id = self.folder_session._scan_id", worker)
        self.assertNotIn('self._settings.setValue("session/active_folder"', constructor)

    def test_timestamp_cell_keeps_raw_iso_in_user_role(self):
        method = self.method("_render_result")
        body = ast.unparse(method)
        self.assertIn("catalog_rows(items, self._date_format)", body)
        self.assertIn("fill_table(self.catalog_table, rows, roles=roles)", body)
        helper = (GUI_FILE.parent / "gui_tables.py").read_text(encoding="utf-8")
        self.assertIn("cell.setData(Qt.ItemDataRole.UserRole, raw)", helper)
        row_helper = (GUI_FILE.parent / "table_rows.py").read_text(encoding="utf-8")
        self.assertIn('item["modified_utc"]', row_helper)

    def test_date_format_uses_saved_iso_not_previous_display(self):
        method = self.method("_change_date_format")
        body = ast.unparse(method)
        self.assertIn("cell.data(Qt.ItemDataRole.UserRole)", body)
        self.assertNotIn("datetime.strptime(cell.text()", body)
        self.assertIn("display_timestamp(iso, next_format)", body)

    def test_worker_moved_out_of_main_window_module(self):
        top_classes = [
            node.name for node in self.tree.body if isinstance(node, ast.ClassDef)
        ]
        self.assertNotIn("QueryWorker", top_classes)
        self.assertIn("ArchivIAWindow", top_classes)
        imports = ast.unparse(self.tree)
        self.assertIn("from .gui_worker import QueryWorker", imports)

    def test_catalog_filters_and_pagination_use_shared_helpers(self):
        catalog = ast.unparse(self.method("_load_catalog_page"))
        self.assertIn("catalog_filters(", catalog)
        self.assertIn("**filters", catalog)
        self.assertIn("previous_page(", ast.unparse(self.method("_previous_page")))
        self.assertIn("next_page(", ast.unparse(self.method("_next_page")))
        self.assertIn("previous_page(", ast.unparse(self.method("_previous_preview_page")))
        self.assertIn("next_page(", ast.unparse(self.method("_next_preview_page")))

    def test_reports_are_delegated_to_presentation_module(self):
        rendered = ast.unparse(self.method("_render_result"))
        self.assertIn("summary_report(result)", rendered)
        self.assertIn("inventory_report(result)", rendered)
        self.assertIn("agent_report(result)", rendered)
        self.assertNotIn("json.dumps(", rendered)

    def test_saved_snapshot_navigation_waits_for_worker_finish(self):
        body = ast.unparse(self.method("_worker_done")).replace(chr(39), chr(34))
        self.assertIn('completed_mode == "catalog_verified_preview"', body)
        self.assertIn('self._start_worker("history", Path(navigation["database"]))', body)
        self.assertIn('completed_mode == "history"', body)
        self.assertIn('navigation["stage"] == "await_listing"', body)
        self.assertIn("self._load_catalog_page()", body)

    def test_saved_snapshot_selection_uses_id_and_clears_old_filters(self):
        body = ast.unparse(self.method("_render_result")).replace(chr(39), chr(34))
        self.assertIn("find_saved_snapshot(result, saved_id)", body)
        self.assertIn("self.history_select.findData(saved_id)", body)
        self.assertIn("self._clear_catalog_search()", body)
        self.assertIn("self.category_filter.setCurrentIndex(0)", body)
        self.assertIn("self.tabs.setCurrentWidget(self.library_workspace)", body)
        self.assertIn("self.library_sections.setCurrentIndex(0)", body)

    def test_home_catalog_buttons_reuse_existing_handlers(self):
        constructor = ast.unparse(self.method("__init__"))
        self.assertIn("self.home_inventory_button.clicked.connect(self._run_inventory_preview)", constructor)
        self.assertIn("self.home_catalog_button.clicked.connect(self._confirm_catalog_preview)", constructor)
        self.assertIn("self.home_preview_button.clicked.connect(self._home_view_preview)", constructor)
        self.assertNotIn("copy_verified_test_file", constructor)
        self.assertNotIn("execute_test_move", constructor)

    def test_home_preview_opens_library_inventory_section(self):
        body = ast.unparse(self.method("_home_view_preview"))
        self.assertIn("can_save_inventory_preview(", body)
        self.assertIn("self.tabs.setCurrentWidget(self.library_workspace)", body)
        self.assertIn("self.library_sections.setCurrentIndex(1)", body)
        self.assertNotIn("advanced_button", body)

    def test_busy_and_saved_preview_control_all_catalog_buttons(self):
        busy = ast.unparse(self.method("_set_busy"))
        self.assertIn("can_save_inventory_preview(", busy)
        for name in ("catalog_preview_button", "home_preview_button", "home_catalog_button"):
            self.assertIn(f"self.{name}.setEnabled(ready)", busy)
        cleared = ast.unparse(self.method("_clear_preview"))
        for name in ("home_preview_button", "home_catalog_button"):
            self.assertIn(f"self.{name}.setEnabled(False)", cleared)
        result = ast.unparse(self.method("_render_result"))
        self.assertIn("preview_report = inventory_report(result)", result)
        confirm = ast.unparse(self.method("_confirm_catalog_preview"))
        self.assertIn("can_save_inventory_preview(", confirm)

    def test_manual_copy_is_opt_in_only_from_gui(self):
        init = ast.unparse(self.method("__init__"))
        self.assertIn("self.manual_copy_button.clicked.connect(self._manual_copy_image)", init)
        handler = ast.unparse(self.method("_manual_copy_image"))
        self.assertIn("QFileDialog.getOpenFileName", handler)
        self.assertIn("QFileDialog.getExistingDirectory", handler)
        self.assertIn("QMessageBox.question", handler)
        self.assertIn("preview_manual_image_copy", handler)
        self.assertIn('self._start_worker(', handler)
        self.assertNotIn("os.unlink", handler)

    def test_manual_copy_uses_existing_worker_and_disables_button(self):
        busy = ast.unparse(self.method("_set_busy"))
        self.assertIn("self.manual_copy_button.setEnabled(not busy)", busy)
        result = ast.unparse(self.method("_render_result"))
        self.assertIn('mode == "manual_copy"', result.replace(chr(39), chr(34)))
        self.assertIn("A imagem original NÃO foi removida", result)

    def test_six_tabs_are_permanent_and_handlers_are_reused(self):
        constructor = ast.unparse(self.method("__init__"))
        for tab in ("Início", "Biblioteca", "Documentos", "Organizar",
                    "Agente IA", "Configurações"):
            with self.subTest(tab=tab):
                self.assertIn(repr(tab), constructor)
        self.assertIn("self.library_sections.addTab(inventory_page, 'Inventário')", constructor)
        self.assertIn("self.library_sections.addTab(overview_page, 'Visão geral')", constructor)
        self.assertIn("self.home_folder.textChanged.connect(self.organize_source.setText)", constructor)
        self.assertIn("move_layout.addWidget(self.move_choice)", constructor)
        self.assertIn("organize_move_layout.addWidget(home_move_box)", constructor)
        self.assertIn("organize_move_layout.addWidget(move_box)", constructor)
        self.assertIn("organize_move_layout.addWidget(self.organize_result)", constructor)
        self.assertNotIn("advanced_button", constructor)
        self.assertNotIn("self.advanced_tabs", constructor)

    def test_document_shortcuts_use_existing_catalog_and_do_not_move_files(self):
        constructor = ast.unparse(self.method("__init__"))
        handler = ast.unparse(self.method("_open_document_library"))
        for category in ("documento", "planilha", "apresentacao"):
            self.assertIn(repr(category), constructor)
        self.assertIn("self.category_filter.findData(category)", handler)
        self.assertIn("self.catalog_extension_filter.setText(extension or '')", handler)
        self.assertIn("self.tabs.setCurrentWidget(self.library_workspace)", handler)
        self.assertIn("self._reset_catalog_page()", handler)
        self.assertNotIn("move_one_approved(", handler)
        self.assertNotIn("_approve_all_moves(", handler)

    def test_home_direct_organization_is_independent_of_ollama(self):
        init = ast.unparse(self.method("__init__"))
        preparation = ast.unparse(self.method("_prepare_home_organization"))
        invalidation = ast.unparse(self.method("_invalidate_home_organization"))
        busy = ast.unparse(self.method("_set_busy"))
        self.assertIn("self.home_prepare_button.clicked.connect(self._prepare_home_organization)", init)
        # V2 gera as nove opções diretamente do inventário universal.
        # Não exigir as antigas chamadas individuais da V1.
        self.assertIn("for category in CATEGORIES:", init)
        self.assertIn(
            "self.home_organize_category.addItem(CATEGORY_LABELS[category], category)",
            init,
        )
        self.assertIn("self.home_folder.textChanged.connect(self._invalidate_home_organization)", init)
        self.assertIn("self.home_destination.textChanged.connect(self._invalidate_home_organization)", init)
        self.assertIn("self.home_organize_category.currentIndexChanged.connect(self._invalidate_home_organization)", init)
        self.assertIn("self._start_worker(", preparation)
        self.assertIn("self.home_organize_category.currentData()", preparation)
        self.assertNotIn("self._run_agent(", preparation)
        self.assertIn("session._last_recursive_plan = None", invalidation)
        self.assertIn("plan.get('complete') is True", busy)
        self.assertIn("self.home_prepare_button.setEnabled(not busy)", busy)

    def test_analyze_without_destination_and_move_all_are_explicit(self):
        init = ast.unparse(self.method("__init__"))
        analyze = ast.unparse(self.method("_analyze_home_source"))
        all_moves = ast.unparse(self.method("_approve_all_moves"))
        cancel = ast.unparse(self.method("_stop_move_queue"))
        rendered = ast.unparse(self.method("_render_result"))
        self.assertIn("self.home_analyze_button.clicked.connect(self._analyze_home_source)", init)
        self.assertIn("self.home_all_button.clicked.connect(self._approve_all_moves)", init)
        self.assertIn("self.home_stop_button.clicked.connect(self._stop_move_queue)", init)
        self.assertIn("folder_session=session", analyze)
        self.assertNotIn("home_destination", analyze)
        self.assertIn("QMessageBox.question", all_moves)
        self.assertIn("self._start_worker(", all_moves)
        self.assertIn("self._worker.requestInterruption()", cancel)
        self.assertIn("move_queue", rendered)

    def test_home_understands_mova_and_renders_recursive_plan(self):
        handler = ast.unparse(self.method("_home_ask"))
        self.assertIn("'mova'", handler)
        self.assertIn("'mover'", handler)
        rendered = ast.unparse(self.method("_render_result"))
        self.assertIn("recursive_plan_report(result)", rendered)

    def test_result_contract_is_checked_before_render(self):
        body = ast.unparse(self.method("_show_result"))
        self.assertLess(body.index("validate_gui_result("), body.index("self._render_result("))


if __name__ == "__main__":
    unittest.main()
