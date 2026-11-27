"""Leitores de metadados solicitados explicitamente pelo usuário.

Nunca executar arquivos, escrever tags nem iniciar varredura automática.
"""
from .reader import read_file_metadata

__all__ = ["read_file_metadata"]
