"""TEST-ONLY: utilitários de isolamento; nunca importar em src/archivia.

Artefatos efêmeros de execução ficam EXCLUSIVAMENTE em tests/.runtime/
e cada diretório de caso é automaticamente removido ao fim do teste.
"""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import tempfile
from typing import Iterator

RUNTIME_DIR = Path(__file__).resolve().parent / ".runtime"


@contextmanager
def temporary_test_directory() -> Iterator[Path]:
    """TEST-ONLY: diretório temporário isolado e limpo automaticamente."""
    RUNTIME_DIR.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="archivia-test-", dir=RUNTIME_DIR) as path:
        yield Path(path)
