"""Primeira interface desktop do ArchivIA Standard (PySide6 opcional).

Somente consultas e solicitações ao agente com ferramentas de leitura/simulação.
Sem operações reais de organização, exclusão ou renomeação.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QApplication, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMainWindow,
    QMessageBox, QPushButton, QPlainTextEdit, QVBoxLayout, QWidget,
    QFileDialog, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
)

from .agent import ask_agent
from .catalog import DEFAULT_DB, catalog_summary, query_catalog_page, list_catalog_scans
from .cataloging import catalog_verified_preview
from .inventory import inventory
from .preview import preview_inventory_page

DEFAULT_MODEL = "qwen3:8b-q4_K_M"


class QueryWorker(QThread):
    """Consulta em thread própria: chamadas ao Ollama não travam a interface."""

    finished_result = Signal(object)
    failed = Signal(str)

    def __init__(self, mode: str, database: Path, question: str = "", model: str = "",
                 page: int = 1, category: str | None = None,
                 preview: dict | None = None, scan_id: int | None = None) -> None:
        super().__init__()
        self.mode = mode
        self.database = database
        self.question = question
        self.model = model
        self.page = page
        self.category = category
        self.preview = preview
        self.scan_id = scan_id

    def run(self) -> None:
        try:
            if self.mode == "summary":
                result = catalog_summary(self.database)
            elif self.mode == "agent":
                result = ask_agent(self.question, self.model, self.database)
            elif self.mode == "catalog_page":
                result = query_catalog_page(self.database, self.category, page=self.page, scan_id=self.scan_id)
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
        self._page = 1
        self._pages = 0
        self._preview_result: dict | None = None
        self._preview_source_path: str | None = None
        self._preview_page = 1
        self._preview_pages = 0
        self.setWindowTitle("ArchivIA Standard — Prévia")
        self.resize(960, 1020)

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
        root.addWidget(database_box)

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
        root.addWidget(folder_box)

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

        self.catalog_table = QTableWidget(0, 4)
        self.catalog_table.setHorizontalHeaderLabels(
            ["Arquivo (caminho relativo)", "Categoria", "Extensão", "Bytes"]
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
        root.addWidget(catalog_box)

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
        root.addWidget(agent_box)

        result_box = QGroupBox("Resposta e ferramentas utilizadas")
        result_layout = QVBoxLayout(result_box)
        self.result_view = QPlainTextEdit()
        self.result_view.setReadOnly(True)
        self.result_view.setPlaceholderText(
            "A resposta do modelo e as chamadas de ferramentas aparecerão aqui."
        )
        result_layout.addWidget(self.result_view)
        root.addWidget(result_box, 1)

        self.status = QLabel("Pronto. Nenhuma operação de escrita em mídias está disponível.")
        root.addWidget(self.status)
        self.setCentralWidget(content)

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

    def _load_history(self) -> None:
        if self._worker is not None:
            return
        try:
            database = self._database_path()
        except ValueError as exc:
            self._show_error(str(exc))
            return
        self._start_worker("history", database)

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
        self._start_worker(
            "catalog_page", database, page=self._page,
            category=self.category_filter.currentData(),
            scan_id=self.history_select.currentData()
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
        scan_id: int | None = None
    ) -> None:
        if self._worker is not None:
            return
        self._set_busy(True)
        self.status.setText("Aguardando Ollama..." if mode == "agent" else "Processando consulta local...")
        worker = QueryWorker(mode, database, question, model, page, category, preview, scan_id)
        self._worker = worker
        worker.finished_result.connect(lambda result: self._show_result(mode, result))
        worker.failed.connect(self._show_error)
        worker.finished.connect(self._worker_done)
        worker.start()

    def _set_busy(self, busy: bool) -> None:
        self.summary_button.setEnabled(not busy)
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
            self.status.setText(
                f"Histórico consultado: {len(result)} snapshots encontrados (máximo 100)."
            )
        elif mode == "catalog_page":
            self._page = result["page"]
            self._pages = result["pages"]
            items = result["files"]
            self.catalog_table.setRowCount(len(items))
            for row_index, item in enumerate(items):
                for column, value in enumerate((
                    item["relative_path"], item["category"],
                    item["extension"], str(item["size_bytes"])
                )):
                    self.catalog_table.setItem(row_index, column, QTableWidgetItem(value))
            self.page_label.setText(
                f"Página {self._page} de {self._pages or 0} — {result['count']} arquivos"
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
