"""Primeira interface desktop do ArchivIA Standard (PySide6 opcional).

Somente consultas e solicitações ao agente com ferramentas de leitura/simulação.
Sem operações reais de organização, exclusão ou renomeação.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QThread, Signal, QSettings
from PySide6.QtWidgets import (
    QApplication, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMainWindow,
    QMessageBox, QPushButton, QPlainTextEdit, QVBoxLayout, QWidget,
    QFileDialog, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget,
)

from .agent import ask_agent
from .catalog import DEFAULT_DB, catalog_summary, query_catalog_page, list_catalog_scans, catalog_origins_summary
from .cataloging import catalog_verified_preview
from .date_formats import DATE_FORMATS, date_input_mask, parse_user_date, display_date, display_timestamp
from .inventory import inventory
from .preview import preview_inventory_page
from .planner import propose_date_moves

DEFAULT_MODEL = "qwen3:8b-q4_K_M"


class QueryWorker(QThread):
    """Consulta em thread própria: chamadas ao Ollama não travam a interface."""

    finished_result = Signal(object)
    failed = Signal(str)

    def __init__(self, mode: str, database: Path, question: str = "", model: str = "",
                 page: int = 1, category: str | None = None,
                 preview: dict | None = None, scan_id: int | None = None,
                 name_contains: str = "", extension: str = "",
                 search_scope: str = "path", date_from: str = "", date_to: str = "",
                 sort_by: str = "name", destination: str = "") -> None:
        super().__init__()
        self.mode = mode
        self.database = database
        self.question = question
        self.model = model
        self.page = page
        self.category = category
        self.preview = preview
        self.scan_id = scan_id
        self.name_contains = name_contains
        self.extension = extension
        self.search_scope = search_scope
        self.date_from = date_from
        self.date_to = date_to
        self.sort_by = sort_by
        self.destination = destination

    def run(self) -> None:
        try:
            if self.mode == "summary":
                result = catalog_summary(self.database)
            elif self.mode == "agent":
                result = ask_agent(self.question, self.model, self.database)
            elif self.mode == "catalog_page":
                result = query_catalog_page(
                    self.database, self.category, page=self.page, scan_id=self.scan_id,
                    name_contains=self.name_contains, extension=self.extension,
                    search_scope=self.search_scope, date_from=self.date_from,
                    date_to=self.date_to, sort_by=self.sort_by,
                )
            elif self.mode == "date_plan":
                result = propose_date_moves(
                    destination=self.destination, category=self.category,
                    db_path=self.database, limit=50, scan_id=self.scan_id,
                )
            elif self.mode == "origins":
                result = catalog_origins_summary(self.database)
            elif self.mode == "history":
                result = list_catalog_scans(self.database)
            elif self.mode == "inventory_preview":
                result = inventory(self.question)
            elif self.mode == "catalog_verified_preview":
                if self.preview is None:
                    raise ValueError("Nenhuma prévia para catalogar.")
                result = catalog_verified_preview(self.preview, self.database)
            else:
                raise ValueError("Ação não autorizada na interface.")
            self.finished_result.emit(result)
        except (ValueError, OSError, RuntimeError) as exc:
            self.failed.emit(str(exc))
        except Exception as exc:
            # Evita que exceções em threads encerrem a aplicação sem diagnóstico.
            self.failed.emit(f"Erro inesperado ({type(exc).__name__}): {exc}")


class ArchivIAWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._worker: QueryWorker | None = None
        self._settings = QSettings(QSettings.Format.IniFormat, QSettings.Scope.UserScope, "ArchivIA", "Standard")
        stored_format = self._settings.value("interface/date_format", "br")
        self._date_format = stored_format if stored_format in DATE_FORMATS else "br"
        self._page = 1
        self._pages = 0
        self._preview_result: dict | None = None
        self._preview_source_path: str | None = None
        self._preview_page = 1
        self._preview_pages = 0
        self.setWindowTitle("ArchivIA Standard — Prévia")
        self.resize(960, 760)
        self.setMinimumSize(760, 540)

        content = QWidget(self)
        root = QVBoxLayout(content)
        root.setSpacing(12)

        title = QLabel("ArchivIA — Bibliotecário digital local")
        title.setStyleSheet("font-size: 20px; font-weight: 600;")
        root.addWidget(title)

        info = QLabel(
            "Primeira interface de homologação. Somente consulta e simulação; "
            "nenhum arquivo será movimentado."
        )
        info.setWordWrap(True)
        root.addWidget(info)

        # Organiza funções por contexto e evita que a área do agente saia da tela.
        self.tabs = QTabWidget()
        overview_page = QWidget()
        overview_layout = QVBoxLayout(overview_page)
        inventory_page = QWidget()
        inventory_layout = QVBoxLayout(inventory_page)
        library_page = QWidget()
        library_layout = QVBoxLayout(library_page)
        organize_page = QWidget()
        organize_layout = QVBoxLayout(organize_page)
        agent_page = QWidget()
        agent_page_layout = QVBoxLayout(agent_page)
        settings_page = QWidget()
        settings_layout = QVBoxLayout(settings_page)
        self.tabs.addTab(overview_page, "Visão geral")
        self.tabs.addTab(inventory_page, "Inventário")
        self.tabs.addTab(library_page, "Biblioteca")
        self.tabs.addTab(organize_page, "Organização")
        self.tabs.addTab(agent_page, "Agente IA")
        self.tabs.addTab(settings_page, "Configurações")
        root.addWidget(self.tabs, 1)

        database_box = QGroupBox("Catálogo SQLite")
        database_layout = QVBoxLayout(database_box)
        self.database = QLineEdit(str(DEFAULT_DB))
        self.database.setToolTip("Caminho do catálogo SQLite existente")
        database_layout.addWidget(self.database)
        self.summary_button = QPushButton("Atualizar resumo")
        self.summary_button.clicked.connect(self._run_summary)
        database_layout.addWidget(self.summary_button)
        self.summary_view = QLabel("Clique em Atualizar resumo para consultar o catálogo.")
        self.summary_view.setWordWrap(True)
        self.summary_view.setTextInteractionFlags(
            self.summary_view.textInteractionFlags()
        )
        database_layout.addWidget(self.summary_view)
        overview_layout.addWidget(database_box)

        origins_box = QGroupBox("Origens catalogadas — último snapshot por pasta")
        origins_layout = QVBoxLayout(origins_box)
        origins_toolbar = QHBoxLayout()
        self.origins_button = QPushButton("Atualizar origens")
        self.origins_button.clicked.connect(self._load_origins)
        origins_toolbar.addWidget(self.origins_button)
        self.origins_label = QLabel("Consulte as origens sem contar snapshots antigos da mesma pasta.")
        self.origins_label.setWordWrap(True)
        origins_toolbar.addWidget(self.origins_label, 1)
        origins_layout.addLayout(origins_toolbar)
        self.origins_table = QTableWidget(0, 4)
        self.origins_table.setHorizontalHeaderLabels(
            ["Pasta de origem", "Snapshot", "Arquivos", "Mídias"]
        )
        self.origins_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.origins_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.origins_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.origins_table.setMaximumHeight(180)
        origins_layout.addWidget(self.origins_table)
        overview_layout.addWidget(origins_box)
        overview_layout.addStretch(1)

        # Inventário independente do catálogo: nunca grava resultados no SQLite.
        folder_box = QGroupBox("Examinar pasta (somente leitura)")
        folder_layout = QVBoxLayout(folder_box)
        folder_row = QHBoxLayout()
        self.folder = QLineEdit()
        self.folder.textChanged.connect(self._folder_changed)
        self.folder.setPlaceholderText("Escolha uma pasta para examinar, sem catalogar")
        folder_row.addWidget(self.folder)
        self.folder_button = QPushButton("Escolher pasta...")
        self.folder_button.clicked.connect(self._choose_folder)
        folder_row.addWidget(self.folder_button)
        folder_layout.addLayout(folder_row)
        self.inventory_button = QPushButton("Examinar pasta — prévia")
        self.inventory_button.clicked.connect(self._run_inventory_preview)
        folder_layout.addWidget(self.inventory_button)
        self.inventory_view = QLabel("Nenhuma pasta examinada nesta sessão.")
        self.inventory_view.setWordWrap(True)
        folder_layout.addWidget(self.inventory_view)
        self.catalog_preview_button = QPushButton("Salvar inventário no catálogo SQLite...")
        self.catalog_preview_button.setEnabled(False)
        self.catalog_preview_button.clicked.connect(self._confirm_catalog_preview)
        folder_layout.addWidget(self.catalog_preview_button)

        preview_toolbar = QHBoxLayout()
        preview_toolbar.addWidget(QLabel("Filtrar prévia:"))
        self.preview_filter = QComboBox()
        self.preview_filter.addItem("Todas", None)
        self.preview_filter.addItem("Imagens", "imagem")
        self.preview_filter.addItem("Vídeos", "video")
        self.preview_filter.addItem("Áudios", "audio")
        self.preview_filter.addItem("Documentos", "documento")
        self.preview_filter.addItem("Planilhas", "planilha")
        self.preview_filter.addItem("Apresentações", "apresentacao")
        self.preview_filter.addItem("Compactados", "compactado")
        self.preview_filter.addItem("Código-fonte", "codigo")
        self.preview_filter.addItem("Outros", "outro")
        self.preview_filter.currentIndexChanged.connect(self._reset_preview_page)
        preview_toolbar.addWidget(self.preview_filter)
        self.preview_label = QLabel("Examine uma pasta para listar os arquivos.")
        preview_toolbar.addWidget(self.preview_label, 1)
        folder_layout.addLayout(preview_toolbar)

        self.preview_table = QTableWidget(0, 4)
        self.preview_table.setHorizontalHeaderLabels(
            ["Arquivo encontrado (caminho relativo)", "Categoria", "Extensão", "Bytes"]
        )
        self.preview_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.preview_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.preview_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.preview_table.setMinimumHeight(150)
        folder_layout.addWidget(self.preview_table)
        preview_pagination = QHBoxLayout()
        self.preview_prev = QPushButton("Anterior — prévia")
        self.preview_prev.clicked.connect(self._previous_preview_page)
        preview_pagination.addWidget(self.preview_prev)
        self.preview_page_label = QLabel("Página —")
        preview_pagination.addWidget(self.preview_page_label)
        self.preview_next = QPushButton("Próxima — prévia")
        self.preview_next.clicked.connect(self._next_preview_page)
        preview_pagination.addWidget(self.preview_next)
        folder_layout.addLayout(preview_pagination)
        self.preview_prev.setEnabled(False)
        self.preview_next.setEnabled(False)
        inventory_layout.addWidget(folder_box, 1)

        catalog_box = QGroupBox("Biblioteca catalogada — somente leitura")
        catalog_layout = QVBoxLayout(catalog_box)
        history_row = QHBoxLayout()
        history_row.addWidget(QLabel("Histórico de snapshots:"))
        self.history_select = QComboBox()
        self.history_select.addItem("Mais recente (automático)", None)
        self.history_select.currentIndexChanged.connect(self._reset_catalog_page)
        history_row.addWidget(self.history_select, 1)
        self.history_button = QPushButton("Atualizar histórico")
        self.history_button.clicked.connect(self._load_history)
        history_row.addWidget(self.history_button)
        catalog_layout.addLayout(history_row)
        catalog_toolbar = QHBoxLayout()
        catalog_toolbar.addWidget(QLabel("Categoria:"))
        self.category_filter = QComboBox()
        self.category_filter.addItem("Todas", None)
        self.category_filter.addItem("Imagens", "imagem")
        self.category_filter.addItem("Vídeos", "video")
        self.category_filter.addItem("Áudios", "audio")
        self.category_filter.addItem("Documentos", "documento")
        self.category_filter.addItem("Planilhas", "planilha")
        self.category_filter.addItem("Apresentações", "apresentacao")
        self.category_filter.addItem("Compactados", "compactado")
        self.category_filter.addItem("Código-fonte", "codigo")
        self.category_filter.addItem("Outros", "outro")
        self.category_filter.currentIndexChanged.connect(self._reset_catalog_page)
        catalog_toolbar.addWidget(self.category_filter)
        self.list_button = QPushButton("Listar catálogo")
        self.list_button.clicked.connect(self._reset_catalog_page)
        catalog_toolbar.addWidget(self.list_button)
        catalog_layout.addLayout(catalog_toolbar)

        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Pesquisar em:"))
        self.catalog_search_scope = QComboBox()
        self.catalog_search_scope.addItem("Caminho completo", "path")
        self.catalog_search_scope.addItem("Somente nome", "filename")
        self.catalog_search_scope.setToolTip("Nome ignora o texto das pastas; caminho inclui as pastas")
        search_row.addWidget(self.catalog_search_scope)
        search_row.addWidget(QLabel("Termo:"))
        self.catalog_name_filter = QLineEdit()
        self.catalog_name_filter.setPlaceholderText("Ex.: ventilador ou BACKUPS/")
        self.catalog_name_filter.returnPressed.connect(self._reset_catalog_page)
        search_row.addWidget(self.catalog_name_filter, 2)
        search_row.addWidget(QLabel("Extensão:"))
        self.catalog_extension_filter = QLineEdit()
        self.catalog_extension_filter.setPlaceholderText("Ex.: pdf")
        self.catalog_extension_filter.setMaximumWidth(110)
        self.catalog_extension_filter.returnPressed.connect(self._reset_catalog_page)
        search_row.addWidget(self.catalog_extension_filter)
        self.clear_search_button = QPushButton("Limpar busca")
        self.clear_search_button.clicked.connect(self._clear_catalog_search)
        search_row.addWidget(self.clear_search_button)
        catalog_layout.addLayout(search_row)
        date_row = QHBoxLayout()
        date_row.addWidget(QLabel("Modificado de:"))
        self.catalog_date_from = QLineEdit()
        self.catalog_date_from.setInputMask(date_input_mask(self._date_format))
        self.catalog_date_from.setPlaceholderText(DATE_FORMATS[self._date_format][1])
        self.catalog_date_from.setMaximumWidth(112)
        self.catalog_date_from.returnPressed.connect(self._reset_catalog_page)
        date_row.addWidget(self.catalog_date_from)
        date_row.addWidget(QLabel("até:"))
        self.catalog_date_to = QLineEdit()
        self.catalog_date_to.setInputMask(date_input_mask(self._date_format))
        self.catalog_date_to.setPlaceholderText(DATE_FORMATS[self._date_format][1])
        self.catalog_date_to.setMaximumWidth(112)
        self.catalog_date_to.returnPressed.connect(self._reset_catalog_page)
        date_row.addWidget(self.catalog_date_to)
        date_row.addWidget(QLabel("Ordenar:"))
        self.catalog_sort = QComboBox()
        self.catalog_sort.addItem("Nome", "name")
        self.catalog_sort.addItem("Mais recentes", "newest")
        self.catalog_sort.addItem("Mais antigos", "oldest")
        date_row.addWidget(self.catalog_sort, 1)
        catalog_layout.addLayout(date_row)
        self.catalog_table = QTableWidget(0, 5)
        self.catalog_table.setHorizontalHeaderLabels(
            ["Arquivo (caminho relativo)", "Categoria", "Extensão", "Bytes", "Modificado (UTC)"]
        )
        self.catalog_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.catalog_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.catalog_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.catalog_table.setMinimumHeight(155)
        catalog_layout.addWidget(self.catalog_table)
        pagination_row = QHBoxLayout()
        self.prev_button = QPushButton("Anterior")
        self.prev_button.clicked.connect(self._previous_page)
        pagination_row.addWidget(self.prev_button)
        self.page_label = QLabel("Página —")
        pagination_row.addWidget(self.page_label)
        self.next_button = QPushButton("Próxima")
        self.next_button.clicked.connect(self._next_page)
        pagination_row.addWidget(self.next_button)
        catalog_layout.addLayout(pagination_row)
        self.prev_button.setEnabled(False)
        self.next_button.setEnabled(False)
        library_layout.addWidget(catalog_box, 1)

        plan_box = QGroupBox("Organizar por ano e mês — SOMENTE SIMULAÇÃO")
        plan_layout = QVBoxLayout(plan_box)
        plan_intro = QLabel(
            "Prévia AAAA/MM baseada na data de modificação UTC. "
            "Não cria pastas, não movimenta arquivos e não permite executar planos."
        )
        plan_intro.setWordWrap(True)
        plan_layout.addWidget(plan_intro)
        plan_folder_row = QHBoxLayout()
        plan_folder_row.addWidget(QLabel("Destino-base existente:"))
        self.plan_destination = QLineEdit()
        self.plan_destination.setPlaceholderText("Escolha uma pasta já existente (não será alterada)")
        plan_folder_row.addWidget(self.plan_destination, 1)
        self.plan_browse_button = QPushButton("Escolher pasta...")
        self.plan_browse_button.clicked.connect(self._choose_plan_destination)
        plan_folder_row.addWidget(self.plan_browse_button)
        plan_layout.addLayout(plan_folder_row)
        plan_options = QHBoxLayout()
        plan_options.addWidget(QLabel("Categoria:"))
        self.plan_category = QComboBox()
        self.plan_category.addItem("Imagens", "imagem")
        self.plan_category.addItem("Vídeos", "video")
        self.plan_category.addItem("Áudios", "audio")
        plan_options.addWidget(self.plan_category)
        plan_options.addWidget(QLabel("Snapshot:"))
        self.plan_snapshot = QComboBox()
        self.plan_snapshot.addItem("Mais recente (automático)", None)
        plan_options.addWidget(self.plan_snapshot, 1)
        self.plan_history_button = QPushButton("Atualizar histórico")
        self.plan_history_button.clicked.connect(self._load_history)
        plan_options.addWidget(self.plan_history_button)
        plan_layout.addLayout(plan_options)
        self.plan_button = QPushButton("Simular organização — sem alterações")
        self.plan_button.clicked.connect(self._run_date_plan)
        plan_layout.addWidget(self.plan_button)
        self.plan_summary = QLabel("Nenhum plano gerado. Serão examinados no máximo 50 arquivos.")
        self.plan_summary.setWordWrap(True)
        plan_layout.addWidget(self.plan_summary)
        self.plan_table = QTableWidget(0, 6)
        self.plan_table.setHorizontalHeaderLabels(
            ["Origem (arquivo)", "Destino proposto", "Situação", "Observação",
             "Possível duplicata?", "Nome alternativo sugerido"]
        )
        self.plan_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.plan_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.plan_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.plan_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        plan_layout.addWidget(self.plan_table, 1)
        organize_layout.addWidget(plan_box, 1)

        agent_box = QGroupBox("Agente Ollama local")
        agent_layout = QVBoxLayout(agent_box)
        model_row = QHBoxLayout()
        model_row.addWidget(QLabel("Modelo:"))
        self.model = QLineEdit(DEFAULT_MODEL)
        model_row.addWidget(self.model)
        agent_layout.addLayout(model_row)
        self.question = QLineEdit()
        self.question.setPlaceholderText("Ex.: Quantas imagens existem no meu catálogo?")
        self.question.returnPressed.connect(self._run_agent)
        agent_layout.addWidget(self.question)
        self.ask_button = QPushButton("Perguntar ao agente")
        self.ask_button.clicked.connect(self._run_agent)
        agent_layout.addWidget(self.ask_button)
        agent_page_layout.addWidget(agent_box)

        result_box = QGroupBox("Resposta e ferramentas utilizadas")
        result_layout = QVBoxLayout(result_box)
        self.result_view = QPlainTextEdit()
        self.result_view.setReadOnly(True)
        self.result_view.setPlaceholderText(
            "A resposta do modelo e as chamadas de ferramentas aparecerão aqui."
        )
        result_layout.addWidget(self.result_view)
        agent_page_layout.addWidget(result_box, 1)

        date_settings = QGroupBox("Preferências de data")
        date_settings_layout = QVBoxLayout(date_settings)
        format_row = QHBoxLayout()
        format_row.addWidget(QLabel("Formato:"))
        self.date_format_select = QComboBox()
        self.date_format_select.addItem("Brasileiro — DD/MM/AAAA", "br")
        self.date_format_select.addItem("Internacional (ISO) — AAAA-MM-DD", "iso")
        self.date_format_select.addItem("Norte-americano — MM/DD/AAAA", "us")
        self.date_format_select.setCurrentIndex(
            max(0, self.date_format_select.findData(self._date_format))
        )
        format_row.addWidget(self.date_format_select, 1)
        date_settings_layout.addLayout(format_row)
        self.date_format_info = QLabel(
            "Aplica-se aos campos de data e à coluna Modificado na Biblioteca. "
            "O catálogo permanece em ISO 8601 UTC."
        )
        self.date_format_info.setWordWrap(True)
        date_settings_layout.addWidget(self.date_format_info)
        self.date_format_select.currentIndexChanged.connect(self._change_date_format)
        settings_layout.addWidget(date_settings)
        settings_layout.addStretch(1)

        self._refresh_date_placeholders()

        self.status = QLabel("Pronto. Nenhuma operação de escrita em mídias está disponível.")
        root.addWidget(self.status)
        self.setCentralWidget(content)

    def _refresh_date_placeholders(self) -> None:
        hint = DATE_FORMATS[self._date_format][1]
        self.catalog_date_from.setPlaceholderText(hint)
        self.catalog_date_to.setPlaceholderText(hint)

    def _change_date_format(self, *_args) -> None:
        next_format = self.date_format_select.currentData()
        if next_format == self._date_format:
            return
        previous_format = self._date_format
        # Capture as datas ANTES de alterar as máscaras; elas ficam em ISO internamente.
        saved = []
        invalid_date_cleared = False
        for widget in (self.catalog_date_from, self.catalog_date_to):
            try:
                saved.append(parse_user_date(widget.text(), previous_format))
            except ValueError:
                saved.append("")
                invalid_date_cleared = True
        self._date_format = next_format
        for widget, iso in zip(
            (self.catalog_date_from, self.catalog_date_to), saved
        ):
            widget.clear()
            widget.setInputMask(date_input_mask(next_format))
            if iso:
                widget.setText(display_date(iso, next_format))
        self._settings.setValue("interface/date_format", next_format)
        self._settings.sync()
        self._refresh_date_placeholders()
        # Reexibe as datas já apresentadas, sem reler SQLite ou alterar arquivos.
        for row in range(self.catalog_table.rowCount()):
            cell = self.catalog_table.item(row, 4)
            if cell is not None and cell.text():
                try:
                    iso = datetime.strptime(
                        cell.text(), DATE_FORMATS[previous_format][0] + " %H:%M:%S UTC"
                    ).strftime("%Y-%m-%dT%H:%M:%S+00:00")
                    cell.setText(display_timestamp(iso, next_format))
                except ValueError:
                    pass
        message = (
            f"Formato salvo: {DATE_FORMATS[next_format][1]}. "
            "Separadores inseridos automaticamente. SQLite não alterado."
        )
        if invalid_date_cleared:
            message += " Um campo de data incompleto foi limpo."
        self.status.setText(message)

    def _database_path(self) -> Path:
        value = self.database.text().strip()
        if not value:
            raise ValueError("Informe um caminho de catálogo SQLite.")
        return Path(value)

    def _choose_folder(self) -> None:
        chosen = QFileDialog.getExistingDirectory(
            self, "Selecionar pasta para examinar", self.folder.text().strip() or str(Path.home())
        )
        if chosen:
            self.folder.setText(chosen)
            self._clear_preview()

    def _folder_changed(self, *_args) -> None:
        if self._preview_result is not None:
            self._clear_preview()
            self.inventory_view.setText("Pasta alterada. Examine novamente antes de catalogar.")

    def _confirm_catalog_preview(self) -> None:
        if self._worker is not None or self._preview_result is None:
            return
        preview = self._preview_result
        if preview.get("errors"):
            self._show_error("Prévia incompleta: catalogação indisponível.")
            return
        if self.folder.text().strip() != self._preview_source_path:
            self._show_error("Pasta alterada. Examine novamente.")
            return
        try:
            database = self._database_path()
        except ValueError as exc:
            self._show_error(str(exc))
            return
        count = preview["summary"]["indexed_files"]
        answer = QMessageBox.question(
            self, "Confirmar catalogação",
            f"Origem: {preview['root']}\n"
            f"Arquivos: {count}\n"
            f"Banco: {database}\n\n"
            "A pasta será examinada novamente antes da gravação.\n"
            "Somente o banco SQLite será alterado; os arquivos serão preservados.\n"
            "Um novo snapshot será adicionado sem remover os anteriores.\n\n"
            "Deseja salvar o inventário?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            self.status.setText("Catalogação cancelada; nenhum dado gravado.")
            return
        self._start_worker("catalog_verified_preview", database, preview=preview)

    def _run_inventory_preview(self) -> None:
        path = self.folder.text().strip()
        if not path:
            self._show_error("Selecione uma pasta antes de examinar.")
            return
        # Um inventário novo substitui a prévia anterior; somente RAM, nunca SQLite.
        self._clear_preview()
        self._start_worker("inventory_preview", Path(), question=path)

    def _clear_preview(self) -> None:
        self._preview_result = None
        self._preview_source_path = None
        self.catalog_preview_button.setEnabled(False)
        self._preview_page = 1
        self._preview_pages = 0
        self.preview_table.setRowCount(0)
        self.preview_page_label.setText("Página —")
        self.preview_label.setText("Examine uma pasta para listar os arquivos.")
        self.preview_prev.setEnabled(False)
        self.preview_next.setEnabled(False)

    def _reset_preview_page(self, *_args) -> None:
        self._preview_page = 1
        self._show_preview_page()

    def _previous_preview_page(self) -> None:
        if self._preview_page > 1:
            self._preview_page -= 1
            self._show_preview_page()

    def _next_preview_page(self) -> None:
        if self._preview_page < self._preview_pages:
            self._preview_page += 1
            self._show_preview_page()

    def _show_preview_page(self) -> None:
        if self._preview_result is None:
            return
        page = preview_inventory_page(
            self._preview_result,
            category=self.preview_filter.currentData(),
            page=self._preview_page,
        )
        self._preview_pages = page["pages"]
        self.preview_table.setRowCount(len(page["files"]))
        for row_index, item in enumerate(page["files"]):
            for column, value in enumerate((
                item["path"], item["category"], item["extension"], str(item["size_bytes"])
            )):
                self.preview_table.setItem(row_index, column, QTableWidgetItem(value))
        self.preview_page_label.setText(
            f"Página {self._preview_page} de {self._preview_pages or 0}"
        )
        self.preview_label.setText(f"{page['count']} arquivos na categoria selecionada")
        self.preview_prev.setEnabled(self._worker is None and self._preview_page > 1)
        self.preview_next.setEnabled(
            self._worker is None and self._preview_page < self._preview_pages
        )

    def _load_origins(self) -> None:
        if self._worker is not None:
            return
        try:
            database = self._database_path()
        except ValueError as exc:
            self._show_error(str(exc))
            return
        self._start_worker("origins", database)

    def _load_history(self) -> None:
        if self._worker is not None:
            return
        try:
            database = self._database_path()
        except ValueError as exc:
            self._show_error(str(exc))
            return
        self._start_worker("history", database)

    def _clear_catalog_search(self) -> None:
        self.catalog_name_filter.clear()
        self.catalog_extension_filter.clear()
        self.catalog_date_from.clear()
        self.catalog_date_to.clear()
        self.catalog_search_scope.setCurrentIndex(0)
        self.catalog_sort.setCurrentIndex(0)
        self._reset_catalog_page()

    def _reset_catalog_page(self, *_args) -> None:
        self._page = 1
        self._load_catalog_page()

    def _load_catalog_page(self) -> None:
        if self._worker is not None:
            return
        try:
            database = self._database_path()
        except ValueError as exc:
            self._show_error(str(exc))
            return
        try:
            date_from = parse_user_date(self.catalog_date_from.text(), self._date_format)
            date_to = parse_user_date(self.catalog_date_to.text(), self._date_format)
        except ValueError as exc:
            self._show_error(str(exc))
            return
        self._start_worker(
            "catalog_page", database, page=self._page,
            category=self.category_filter.currentData(),
            scan_id=self.history_select.currentData(),
            name_contains=self.catalog_name_filter.text().strip(),
            extension=self.catalog_extension_filter.text().strip(),
            search_scope=self.catalog_search_scope.currentData(),
            date_from=date_from,
            date_to=date_to,
            sort_by=self.catalog_sort.currentData(),
        )

    def _previous_page(self) -> None:
        if self._page > 1:
            self._page -= 1
            self._load_catalog_page()

    def _next_page(self) -> None:
        if self._page < self._pages:
            self._page += 1
            self._load_catalog_page()

    def _run_summary(self) -> None:
        try:
            database = self._database_path()
        except ValueError as exc:
            self._show_error(str(exc))
            return
        self._start_worker("summary", database)

    def _choose_plan_destination(self) -> None:
        chosen = QFileDialog.getExistingDirectory(
            self, "Escolher destino-base para simulação",
            self.plan_destination.text().strip() or str(Path.home()),
        )
        if chosen:
            self.plan_destination.setText(chosen)

    def _run_date_plan(self) -> None:
        destination = self.plan_destination.text().strip()
        if not destination:
            self._show_error("Escolha um destino-base existente para simular.")
            return
        try:
            database = self._database_path()
        except ValueError as exc:
            self._show_error(str(exc))
            return
        self.plan_table.setRowCount(0)
        self.plan_summary.setText("Calculando apenas uma prévia, sem modificar arquivos...")
        self._start_worker(
            "date_plan", database,
            category=self.plan_category.currentData(),
            scan_id=self.plan_snapshot.currentData(),
            destination=destination,
        )

    def _run_agent(self) -> None:
        try:
            database = self._database_path()
        except ValueError as exc:
            self._show_error(str(exc))
            return
        question = self.question.text().strip()
        model = self.model.text().strip()
        if not question or not model:
            self._show_error("Informe a pergunta e o modelo Ollama.")
            return
        self._start_worker("agent", database, question, model)

    def _start_worker(
        self, mode: str, database: Path, question: str = "", model: str = "",
        page: int = 1, category: str | None = None,
        preview: dict | None = None,
        scan_id: int | None = None, name_contains: str = "", extension: str = "",
        search_scope: str = "path", date_from: str = "", date_to: str = "",
        sort_by: str = "name", destination: str = ""
    ) -> None:
        if self._worker is not None:
            return
        self._set_busy(True)
        self.status.setText("Aguardando Ollama..." if mode == "agent" else "Processando consulta local...")
        worker = QueryWorker(
            mode, database, question, model, page, category, preview,
            scan_id, name_contains, extension, search_scope, date_from, date_to, sort_by,
            destination,
        )
        self._worker = worker
        worker.finished_result.connect(lambda result: self._show_result(mode, result))
        worker.failed.connect(self._show_error)
        worker.finished.connect(self._worker_done)
        worker.start()

    def _set_busy(self, busy: bool) -> None:
        self.summary_button.setEnabled(not busy)
        self.plan_destination.setEnabled(not busy)
        self.plan_browse_button.setEnabled(not busy)
        self.plan_category.setEnabled(not busy)
        self.plan_snapshot.setEnabled(not busy)
        self.plan_history_button.setEnabled(not busy)
        self.plan_button.setEnabled(not busy)
        self.ask_button.setEnabled(not busy)
        self.database.setEnabled(not busy)
        self.model.setEnabled(not busy)
        self.question.setEnabled(not busy)
        self.folder.setEnabled(not busy)
        self.folder_button.setEnabled(not busy)
        self.inventory_button.setEnabled(not busy)
        self.catalog_preview_button.setEnabled(
            not busy and self._preview_result is not None
            and not self._preview_result.get("errors")
            and self.folder.text().strip() == self._preview_source_path
        )
        self.preview_filter.setEnabled(not busy)
        self.preview_prev.setEnabled(not busy and self._preview_page > 1)
        self.preview_next.setEnabled(not busy and self._preview_page < self._preview_pages)
        self.category_filter.setEnabled(not busy)
        self.list_button.setEnabled(not busy)
        self.catalog_name_filter.setEnabled(not busy)
        self.catalog_extension_filter.setEnabled(not busy)
        self.clear_search_button.setEnabled(not busy)
        self.catalog_search_scope.setEnabled(not busy)
        self.catalog_date_from.setEnabled(not busy)
        self.catalog_date_to.setEnabled(not busy)
        self.catalog_sort.setEnabled(not busy)
        self.origins_button.setEnabled(not busy)
        self.history_button.setEnabled(not busy)
        self.history_select.setEnabled(not busy)
        self.prev_button.setEnabled(not busy and self._page > 1)
        self.next_button.setEnabled(not busy and self._page < self._pages)

    def _show_result(self, mode: str, result: dict) -> None:
        if mode == "summary":
            if result.get("scan_id") is None:
                self.summary_view.setText("Catálogo vazio: nenhuma catalogação encontrada.")
            else:
                categories = result.get("by_category", {})
                self.summary_view.setText(
                    f"Inventário #{result['scan_id']} | Arquivos: {result['indexed_files']} | Mídias: {result['media_files']} "
                    f"| Imagens: {categories.get('imagem', 0)} "
                    f"| Vídeos: {categories.get('video', 0)} "
                    f"| Áudios: {categories.get('audio', 0)} "
                    f"| Espaço: {result['bytes_media']:,} bytes"
                )
            self.status.setText("Resumo consultado. Banco não alterado.")
        elif mode == "inventory_preview":
            self._preview_result = result
            self._preview_source_path = self.folder.text().strip()
            self._preview_page = 1
            self._show_preview_page()
            info = result["summary"]
            self.inventory_view.setText(
                f"Pasta: {result['root']} | Arquivos: {info['indexed_files']} | Mídias: {info['media_files']} "
                f"| Imagens: {info['by_category'].get('imagem', 0)} "
                f"| Vídeos: {info['by_category'].get('video', 0)} "
                f"| Áudios: {info['by_category'].get('audio', 0)} "
                f"| Erros: {len(result['errors'])}"
            )
            self.status.setText(
                "Prévia concluída. Nenhum dado gravado no catálogo; arquivos preservados."
            )
            # Um erro antigo de outra seção não deve permanecer após esta prévia bem-sucedida.
            if self.result_view.toPlainText().startswith("Erro:"):
                self.result_view.clear()
        elif mode == "catalog_verified_preview":
            # Após salvar, uma nova catalogação exige nova prévia explícita.
            self._preview_result = None
            self._preview_source_path = None
            self.catalog_preview_button.setEnabled(False)
            self.status.setText(
                f"Snapshot #{result['scan_id']} salvo no SQLite. "
                "Arquivos originais preservados."
            )
            self.summary_view.setText(
                "Novo snapshot salvo. Clique em Atualizar resumo para conferir os totais."
            )
            self._page = 1
            self._pages = 0
            self.catalog_table.setRowCount(0)
            self.page_label.setText("Novo snapshot salvo — clique em Listar catálogo")
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)
        elif mode == "origins":
            origins = result["origins"]
            self.origins_table.setRowCount(len(origins))
            for row_index, item in enumerate(origins):
                values = (
                    item["root"], str(item["scan_id"]),
                    str(item["indexed_files"]), str(item["media_files"])
                )
                for col_index, value in enumerate(values):
                    self.origins_table.setItem(
                        row_index, col_index, QTableWidgetItem(value)
                    )
            self.origins_label.setText(
                f"{result['origins_count']} origens | "
                f"{result['indexed_files']} arquivos | "
                f"{result['media_files']} mídias"
            )
            self.origins_label.setToolTip(result["overlap_warning"])
            self.status.setText(
                "Origens consultadas no SQLite, sem alterar snapshots. "
                "Pastas sobrepostas podem duplicar arquivos entre origens."
            )
        elif mode == "history":
            current = self.history_select.currentData()
            self.history_select.blockSignals(True)
            self.history_select.clear()
            self.history_select.addItem("Mais recente (automático)", None)
            for scan in result:
                label = (
                    f"#{scan['id']} | {scan['scanned_utc']} | "
                    f"{scan['indexed_files']} arquivos | {scan['root']}"
                )
                self.history_select.addItem(label, scan["id"])
            index = self.history_select.findData(current)
            self.history_select.setCurrentIndex(max(0, index))
            self.history_select.blockSignals(False)
            selected_plan = self.plan_snapshot.currentData()
            self.plan_snapshot.blockSignals(True)
            self.plan_snapshot.clear()
            self.plan_snapshot.addItem("Mais recente (automático)", None)
            for scan in result:
                self.plan_snapshot.addItem(
                    f"#{scan['id']} | {scan['root']}", scan["id"]
                )
            self.plan_snapshot.setCurrentIndex(
                max(0, self.plan_snapshot.findData(selected_plan))
            )
            self.plan_snapshot.blockSignals(False)
            self.status.setText(
                f"Histórico consultado: {len(result)} snapshots encontrados (máximo 100)."
            )
        elif mode == "date_plan":
            self.plan_table.setRowCount(len(result["actions"]))
            for row_index, item in enumerate(result["actions"]):
                values = (
                    item["file"], item.get("destination") or "—",
                    item["status"], item.get("reason") or (
                        "Subpasta futura" if item.get("directory_would_need_creation")
                        else "Destino-base pronto"
                    ),
                    "Sim (não confirmada)" if item.get("possible_duplicate_by_metadata") else "Não",
                    item.get("alternative_name_suggestion") or "—",
                )
                for col_index, value in enumerate(values):
                    self.plan_table.setItem(
                        row_index, col_index, QTableWidgetItem(str(value))
                    )
            self.plan_summary.setText(
                f"Snapshot #{result['scan_id']} | {result['selected']} examinados "
                f"de {result['total_matches']} arquivos da categoria | "
                f"{result['blocked']} bloqueados | "
                f"{result.get('name_collisions', 0)} colisões de nome | "
                f"{result.get('potential_duplicate_items', 0)} suspeitas por metadados | "
                f"{'Resultado parcial' if result['truncated'] else 'Categoria completa'}"
                " — SIMULAÇÃO: nenhuma operação de escrita."
            )
            self.status.setText("Simulação de organização concluída; nada foi alterado.")
        elif mode == "catalog_page":
            self._page = result["page"]
            self._pages = result["pages"]
            items = result["files"]
            self.catalog_table.setRowCount(len(items))
            for row_index, item in enumerate(items):
                for column, value in enumerate((
                    item["relative_path"], item["category"],
                    item["extension"], str(item["size_bytes"]),
                    display_timestamp(item["modified_utc"], self._date_format)
                )):
                    self.catalog_table.setItem(row_index, column, QTableWidgetItem(value))
            self.page_label.setText(
                f"Página {self._page} de {self._pages or 0} — {result['count']} arquivos encontrados"
            )
            self.status.setText("Snapshot #{} consultado em modo somente leitura.".format(result["scan_id"]))
        else:
            answer = result.get("answer") or "(Resposta textual vazia)"
            tools = result.get("tools_used", [])
            details = json.dumps(tools, ensure_ascii=False, indent=2)
            self.result_view.setPlainText(
                f"RESPOSTA DO AGENTE\n{answer}\n\n"
                f"FERRAMENTAS UTILIZADAS\n{details}\n\n"
                "Operações de movimentação: indisponíveis nesta versão."
            )
            self.status.setText("Resposta recebida. Nenhum arquivo de mídia modificado.")

    def _show_error(self, message: str) -> None:
        self.status.setText(f"Erro: {message}")
        self.result_view.setPlainText(f"Erro: {message}")

    def _worker_done(self) -> None:
        if self._worker is not None:
            self._worker.deleteLater()
            self._worker = None
        self._set_busy(False)

    def closeEvent(self, event) -> None:
        # Não destruir QThread enquanto a operação Ollama estiver em andamento.
        if self._worker is not None:
            event.ignore()
            QMessageBox.information(
                self, "ArchivIA", "Há uma consulta em andamento. Feche após a conclusão."
            )
        else:
            event.accept()


def main() -> int:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    window = ArchivIAWindow()
    window.show()
    return app.exec()
