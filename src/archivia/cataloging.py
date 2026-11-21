"""Catalogação controlada a partir de prévia: valida novamente antes de gravar SQLite.

Nenhuma mídia é alterada. A escrita ocorre exclusivamente no banco do catálogo.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .catalog import DEFAULT_DB, store_inventory
from .inventory import inventory


def catalog_verified_preview(
    preview: dict[str, Any], db_path: Path = DEFAULT_DB
) -> dict[str, Any]:
    """Recusa prévias incompletas ou obsoletas e grava snapshot após revarredura.

    Mesmo com prévia aprovada na GUI, a pasta pode ter mudado: uma segunda
    varredura completa verifica caminhos, categorias, tamanhos e mtime.
    """
    if not isinstance(preview, dict) or not isinstance(preview.get("files"), list):
        raise ValueError("Prévia inválida. Examine a pasta novamente.")
    if preview.get("errors"):
        raise ValueError("Prévia contém erros. Catalogação cancelada.")
    root = preview.get("root")
    if not isinstance(root, str) or not root:
        raise ValueError("Origem inválida. Examine a pasta novamente.")

    new_scan = inventory(root)
    if new_scan["errors"]:
        raise ValueError("Nova leitura encontrou erros. Catalogação cancelada.")
    if (new_scan["root"] != root or new_scan["files"] != preview["files"]
            or new_scan["summary"] != preview.get("summary")):
        raise ValueError("Os arquivos mudaram desde a prévia. Examine novamente antes de catalogar.")

    # store_inventory somente escreve no SQLite; jamais modifica a origem.
    return store_inventory(new_scan, db_path)
