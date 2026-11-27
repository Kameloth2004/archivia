"""Identidade física e metadados de arquivo para validações conservadoras.

Função pura de stat: não abre, percorre, copia, move ou exclui arquivos.
Não substitui SHA-256 nem prova que um arquivo não mudou entre operações.
"""
from __future__ import annotations

import os


def file_identity(info: os.stat_result) -> tuple[int, int, int, int]:
    """Retorna (volume, inode, tamanho, mtime_ns) sem alterar os dados."""
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns
