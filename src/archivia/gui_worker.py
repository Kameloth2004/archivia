"""Worker da GUI (PySide6): execução local/IA fora da thread principal.

Separado dos widgets para reutilizar processamento sem duplicar handlers.
Não adiciona acesso a executor de movimentação ou cópia de arquivos pessoais.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from .agent import ask_agent, FolderCatalogSession
from .catalog import catalog_summary, query_catalog_page, list_catalog_scans, catalog_origins_summary
from .cataloging import catalog_verified_preview
from .inventory import inventory
from .manual_copy import copy_manual_image_verified
from .move_executor import move_one_approved
from .batch_move import move_batch_approved
from .queue_move import move_queue_approved
from .planner import propose_date_moves
from .duplicates import verify_duplicate_hashes, verify_snapshot_duplicate_candidates


class QueryWorker(QThread):
    """Consulta em thread própria: chamadas ao Ollama não travam a interface."""

    finished_result = Signal(object)
    failed = Signal(str)
    progress_update = Signal(object)

    def __init__(self, mode: str, database: Path, question: str = "", model: str = "",
                 page: int = 1, category: str | None = None,
                 preview: dict | None = None, scan_id: int | None = None,
                 name_contains: str = "", extension: str = "",
                 search_scope: str = "path", date_from: str = "", date_to: str = "",
                 sort_by: str = "name", destination: str = "",
                 hash_limit: int = 50, hash_file_mib: int = 16,
                 hash_budget_mib: int = 64,
                 hash_mode: str = "sample", source_folder: str = "",
                 folder_session: FolderCatalogSession | None = None,
                 manual_source: str = "", manual_folder: str = "",
                 approved_source: str = "", approved_destination: str = "",
                 move_plan: dict | None = None, move_relative: str = "",
                 move_approval: str = "",
                 move_files: list[str] | None = None,
                 approved_target_name: str | None = None,
                 include_subfolders: bool = True) -> None:
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
        self.hash_limit = hash_limit
        self.hash_file_mib = hash_file_mib
        self.hash_budget_mib = hash_budget_mib
        self.hash_mode = hash_mode
        self.source_folder = source_folder
        self.folder_session = folder_session
        self.manual_source = manual_source
        self.manual_folder = manual_folder
        self.approved_source = approved_source
        self.approved_destination = approved_destination
        self.move_plan = move_plan
        self.move_relative = move_relative
        self.move_approval = move_approval
        self.move_files = move_files
        self.approved_target_name = approved_target_name
        self.include_subfolders = include_subfolders

    def run(self) -> None:
        try:
            if self.mode == "move_queue":
                if self.folder_session is None or not self.folder_session.ready:
                    raise ValueError("Não há análise ativa para movimentação.")
                result = move_queue_approved(
                    self.move_plan, self.move_files,
                    db_path=self.folder_session._db,
                    scan_id=self.folder_session._scan_id,
                    approval=self.move_approval,
                    progress=self.progress_update.emit,
                    interrupted=self.isInterruptionRequested,
                )
            elif self.mode == "analyze_source":
                if self.folder_session is None:
                    raise ValueError("Selecione uma pasta de origem.")
                result = self.folder_session.analyze_source(
                    recursive=self.include_subfolders,
                )
            elif self.mode == "prepare_organization":
                if self.folder_session is None:
                    raise ValueError("Selecione primeiro a pasta de origem.")
                result = self.folder_session.prepare_recursive_plan(
                    self.destination, self.category or "imagem",
                    recursive=self.include_subfolders,
                )
            elif self.mode == "move_conflict":
                if self.folder_session is None or not self.folder_session.ready:
                    raise ValueError("Sessão de origem não disponível.")
                result = move_one_approved(
                    self.move_plan, self.move_relative,
                    db_path=self.folder_session._db,
                    scan_id=self.folder_session._scan_id,
                    approval=self.move_approval, resolve_conflict=True,
                    approved_target_name=self.approved_target_name,
                )
            elif self.mode == "move_batch":
                if self.folder_session is None or not self.folder_session.ready:
                    raise ValueError("Sessão de origem não disponível.")
                result = move_batch_approved(
                    self.move_plan, self.move_files,
                    db_path=self.folder_session._db,
                    scan_id=self.folder_session._scan_id,
                    approval=self.move_approval,
                    progress=self.progress_update.emit,
                )
            elif self.mode == "move_one":
                if self.folder_session is None or not self.folder_session.ready:
                    raise ValueError("Sessão de origem não disponível.")
                result = move_one_approved(
                    self.move_plan, self.move_relative,
                    db_path=self.folder_session._db,
                    scan_id=self.folder_session._scan_id,
                    approval=self.move_approval,
                )
            elif self.mode == "manual_copy":
                result = copy_manual_image_verified(
                    self.manual_source, self.manual_folder,
                    approved_source=self.approved_source,
                    approved_destination=self.approved_destination,
                )
            elif self.mode == "summary":
                result = catalog_summary(self.database)
            elif self.mode == "agent":
                result = (self.folder_session.ask(self.question, self.model)
                          if self.folder_session is not None else
                          ask_agent(self.question, self.model, self.database, context_scan_id=self.scan_id))
            elif self.mode == "refresh_folder_session":
                if self.folder_session is None:
                    raise ValueError("Selecione uma pasta para atualizar o catálogo.")
                self.folder_session.refresh()
                result = {"root": str(self.folder_session.source), "updated": True}
            elif self.mode == "catalog_page":
                # Uma pasta ativa usa seu próprio snapshot temporário, sem
                # consultar nem alterar o SQLite persistente da Biblioteca.
                database = self.database
                scan_id = self.scan_id
                if self.folder_session is not None:
                    if not self.folder_session.ready:
                        self.folder_session.refresh()
                    database = self.folder_session._db
                    scan_id = self.folder_session._scan_id
                result = query_catalog_page(
                    database, self.category, page=self.page, scan_id=scan_id,
                    name_contains=self.name_contains, extension=self.extension,
                    search_scope=self.search_scope, date_from=self.date_from,
                    date_to=self.date_to, sort_by=self.sort_by,
                )
            elif self.mode == "date_plan":
                result = propose_date_moves(
                    destination=self.destination, category=self.category,
                    db_path=self.database, limit=50, scan_id=self.scan_id,
                )
            elif self.mode == "duplicate_hash":
                arguments = {
                    "db_path": self.database,
                    "category": self.category,
                    "scan_id": self.scan_id,
                    "max_file_bytes": self.hash_file_mib * 1024 * 1024,
                    "max_total_bytes": self.hash_budget_mib * 1024 * 1024,
                    "progress": self.progress_update.emit,
                }
                if self.hash_mode == "global":
                    result = verify_snapshot_duplicate_candidates(
                        **arguments, max_candidates=self.hash_limit
                    )
                elif self.hash_mode == "sample":
                    result = verify_duplicate_hashes(
                        **arguments, limit=self.hash_limit
                    )
                else:
                    raise ValueError("Modo de análise SHA-256 não autorizado.")
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


