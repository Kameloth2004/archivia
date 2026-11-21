"""Pagina resultados de um inventário em memória, sem consultar ou modificar SQLite.

O inventário é gerado previamente pela função inventory(); esta função apenas
seleciona as linhas mostradas na GUI, sem copiar arquivos nem acessar discos.
"""
from __future__ import annotations

from typing import Any

CATEGORIES = frozenset(("imagem", "video", "audio"))


def preview_inventory_page(
    result: dict[str, Any],
    category: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> dict[str, Any]:
    """Retorna somente a página solicitada dos metadados já inventariados."""
    if category is not None and category not in CATEGORIES:
        raise ValueError("Categoria inválida: use imagem, video ou audio.")
    if not isinstance(page, int) or isinstance(page, bool) or page < 1:
        raise ValueError("Página deve ser um inteiro positivo.")
    if (not isinstance(page_size, int) or isinstance(page_size, bool)
            or not 1 <= page_size <= 100):
        raise ValueError("Tamanho de página deve estar entre 1 e 100.")

    files = result["files"]
    # Não cria uma segunda lista de 20 mil registros apenas para filtrar.
    if category is None:
        total = len(files)
        start = (page - 1) * page_size
        selected = files[start:start + page_size]
    else:
        total = 0
        selected = []
        start = (page - 1) * page_size
        for item in files:
            if item["category"] != category:
                continue
            if start <= total < start + page_size:
                selected.append(item)
            total += 1

    return {
        "root": result["root"],
        "filter_category": category,
        "page": page,
        "page_size": page_size,
        "count": total,
        "pages": (total + page_size - 1) // page_size,
        "files": selected,
    }
