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
)

from .agent import ask_agent
from .catalog import DEFAULT_DB, catalog_summary

DEFAULT_MODEL = "qwen3:8b-q4_K_M"


class QueryWorker(QThread):
    """Consulta em thread própria: chamadas ao Ollama não travam a interface."""

    finished_result = Signal(object)
    failed = Signal(str)

    def __init__(self, mode: str, database: Path, question: str = "", model: str = "") -> None:
        super().__init__()
        self.mode = mode
        self.database = database
        self.question = question
        self.model = model

    def run(self) -> None:
        try:
            if self.mode == "summary":
                result = catalog_summary(self.database)
            elif self.mode == "agent":
                result = ask_agent(self.question, self.model, self.database)
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
        self.setWindowTitle("ArchivIA Standard — Prévia")
        self.resize(860, 660)

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
        self, mode: str, database: Path, question: str = "", model: str = ""
    ) -> None:
        if self._worker is not None:
            return
        self._set_busy(True)
        self.status.setText("Consultando catálogo..." if mode == "summary" else "Aguardando Ollama...")
        worker = QueryWorker(mode, database, question, model)
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

    def _show_result(self, mode: str, result: dict) -> None:
        if mode == "summary":
            if result.get("scan_id") is None:
                self.summary_view.setText("Catálogo vazio: nenhuma catalogação encontrada.")
            else:
                categories = result.get("by_category", {})
                self.summary_view.setText(
                    f"Inventário #{result['scan_id']} | Mídias: {result['media_files']} "
                    f"| Imagens: {categories.get('imagem', 0)} "
                    f"| Vídeos: {categories.get('video', 0)} "
                    f"| Áudios: {categories.get('audio', 0)} "
                    f"| Espaço: {result['bytes_media']:,} bytes"
                )
            self.status.setText("Resumo consultado. Banco não alterado.")
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
