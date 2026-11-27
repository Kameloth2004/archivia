"""Adaptador opcional para ExifTool — extração local, somente leitura.

Não baixa executáveis nem modifica arquivos. Executa somente um arquivo
explicitamente solicitado, sem expansão recursiva e com timeout. Retorna
todas as tags publicadas pelo ExifTool, inclusive desconhecidas, GPS e
tags de autoria, sem bloqueios por natureza do conteúdo.
"""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
from typing import Any

_TIMEOUT_SECONDS = 15
_MAX_JSON_BYTES = 12 * 1024 * 1024


def available_exiftool() -> str | None:
    """O ExifTool é opt-in pela instalação local no PATH."""
    return shutil.which("exiftool")


def extract_exiftool(path: Path, executable: str) -> list[dict[str, Any]]:
    """Devolve grupos legíveis; a única execução externa é o leitor local.

    -j: dados estruturados; -G1:4: grupo e instância da tag;
    -a: duplicatas; -U: tags desconhecidas inclusive binárias;
    -ee: metadados embutidos; -s: nomes técnicos das tags;
    -struct: preserva estruturas XMP em vez de achatá-las.
    """
    command = [
        executable, "-j", "-G1:4", "-a", "-U", "-ee", "-s", "-struct",
        "--", str(path),
    ]
    try:
        result = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=_TIMEOUT_SECONDS, check=False, shell=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"ExifTool indisponível: {type(exc).__name__}") from exc
    if len(result.stdout) > _MAX_JSON_BYTES:
        raise ValueError("Saída do ExifTool acima do limite técnico de 12 MiB.")
    if result.returncode != 0:
        raise ValueError(f"ExifTool retornou código {result.returncode}.")
    try:
        records = json.loads(result.stdout.decode("utf-8-sig"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("Resposta JSON inválida do ExifTool.") from exc
    if not isinstance(records, list) or len(records) != 1 or not isinstance(records[0], dict):
        raise ValueError("ExifTool não retornou um único registro de arquivo.")

    groups: dict[str, list[tuple[str, Any]]] = {}
    for key, value in records[0].items():
        if ":" in key:
            group, tag = key.split(":", 1)
        else:
            group, tag = "ExifTool", key
        groups.setdefault(group, []).append((tag, value))
    return [
        {"name": name, "fields": tags}
        for name, tags in groups.items() if tags
    ]
