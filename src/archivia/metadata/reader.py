"""Metadados locais sob demanda para arquivos de qualquer categoria.

Prioriza ExifTool quando instalado pelo usuário; caso contrário expõe
todas as tags/IFDs e informações de imagem reconhecidas por Pillow.
Não há whitelist por privacidade; campos GPS, autoria, identificadores
e desconhecidos são exibidos. Limites são estritamente técnicos.
"""
from __future__ import annotations

from datetime import datetime
import mimetypes
from pathlib import Path
import stat
from typing import Any

from .exiftool_adapter import available_exiftool, extract_exiftool
from .xmp_reader import xmp_from_image_info

_IMAGE_SUFFIXES = frozenset({
    ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff", ".avif",
})
_IMAGE_MAX_BYTES = 80 * 1024 * 1024
_MAX_FIELDS = 2000
_MAX_VALUE_CHARS = 4096
_MAX_BYTES_HEX = 512


def _display(value: Any, depth: int = 0) -> str:
    """Representa qualquer valor sem censurá-lo, com truncamento declarado."""
    if depth > 5:
        return "(estrutura aninhada além do limite técnico de 5 níveis)"
    if value is None:
        return "(nulo)"
    if isinstance(value, (bytes, bytearray, memoryview)):
        raw = bytes(value)
        content = raw[:_MAX_BYTES_HEX].hex(" ")
        if len(raw) > _MAX_BYTES_HEX:
            content += f" … [truncado: {len(raw)} bytes no total]"
        return f"hex: {content} ({len(raw)} bytes)"
    if isinstance(value, dict):
        result = "; ".join(
            f"{_display(k, depth + 1)}: {_display(v, depth + 1)}"
            for k, v in list(value.items())[:_MAX_FIELDS]
        )
        if len(value) > _MAX_FIELDS:
            result += f"; … [{len(value)} entradas, limite técnico]"
    elif isinstance(value, (tuple, list)):
        result = ", ".join(_display(v, depth + 1) for v in value[:_MAX_FIELDS])
        if len(value) > _MAX_FIELDS:
            result += f", … [{len(value)} entradas, limite técnico]"
    else:
        result = str(value).replace("\x00", "\\0")
    if len(result) > _MAX_VALUE_CHARS:
        return result[:_MAX_VALUE_CHARS] + f"… [valor truncado: {len(result)} caracteres]"
    return result


def _image_groups(candidate: Path) -> list[dict[str, Any]]:
    from PIL import Image, ExifTags

    result: list[dict[str, Any]] = []
    with Image.open(candidate) as picture:
        result.append({
            "name": "Imagem",
            "fields": [
                ("Formato interno", picture.format or "Desconhecido"),
                ("Dimensões", f"{picture.width} × {picture.height} pixels"),
                ("Modo de cor", picture.mode),
            ],
        })

        # PNG tEXt/iTXt, XMP (quando exposto), ICC, IPTC e propriedades
        # do decoder. Não omitir metadados por tipo ou sensibilidade.
        if picture.info:
            # XMP é XML, não um bloco binário arbitrário. Converter em campos
            # estruturados e guardar o pacote completo separadamente para
            # consulta no botão "Ver dados brutos".
            xmp_groups, xmp_raw, warnings = xmp_from_image_info(picture.info)
            other_fields = [
                (str(key), value) for key, value in picture.info.items()
                if not str(key).casefold() in {
                    "xmp", "xml:com.adobe.xmp", "xml:com.adobe.xmp\\x00",
                }
            ]
            if other_fields:
                result.append({
                    "name": "Informações internas da imagem",
                    "fields": other_fields,
                })
            result.extend(xmp_groups)
            if xmp_raw:
                result.append({
                    "name": "XMP — referência ao conteúdo original",
                    "fields": [("Pacotes preservados", str(len(xmp_raw)))],
                    "_raw_sections": xmp_raw,
                })
            if warnings:
                result.append({
                    "name": "XMP — avisos",
                    "fields": [(f"Aviso {i}", warning) for i, warning in enumerate(warnings, 1)],
                })
        try:
            exif = picture.getexif()
        except (OSError, TypeError, ValueError):
            exif = None
        if exif:
            roots = [(str(ExifTags.TAGS.get(tag, f"Tag_{tag}")), value)
                     for tag, value in exif.items()]
            if roots:
                result.append({"name": "EXIF", "fields": roots})
            ifds = (
                (34665, "EXIF: câmera e captura"),
                (34853, "EXIF: GPS"),
                (40965, "EXIF: interoperabilidade"),
                (1, "EXIF: thumbnail"),
            )
            for tag, name in ifds:
                try:
                    data = exif.get_ifd(tag)
                except (OSError, ValueError, TypeError, KeyError):
                    continue
                if not data:
                    continue
                fields = [
                    (str(ExifTags.GPSTAGS.get(k, f"GPS_{k}"))
                     if tag == 34853 else str(ExifTags.TAGS.get(k, f"Tag_{k}")), v)
                    for k, v in data.items()
                ]
                result.append({"name": name, "fields": fields})
    return result


def read_file_metadata(path: str | Path) -> dict[str, Any]:
    """Consulta explicitamente um arquivo regular, sem escrita.

    A GUI verifica escopo e identidade do arquivo antes e depois desta
    chamada; o leitor mantém a restrição para arquivo regular.
    """
    candidate = Path(path)
    if candidate.is_symlink():
        raise ValueError("Links simbólicos não são aceitos na verificação.")
    info = candidate.stat(follow_symlinks=False)
    if not stat.S_ISREG(info.st_mode):
        raise ValueError("A verificação aceita somente arquivos regulares.")

    modified = datetime.fromtimestamp(info.st_mtime).strftime("%d/%m/%Y %H:%M:%S")
    mime, _ = mimetypes.guess_type(candidate.name)
    basic = [
        ("Formato identificado pela extensão", mime or "Desconhecido"),
        ("Tamanho", f"{info.st_size:,} bytes"),
        ("Modificado (sistema)", modified),
    ]
    result: dict[str, Any] = {
        "name": candidate.name,
        "fields": basic,
        "groups": [{"name": "Sistema de arquivos", "fields": basic}],
        "source": "Sistema de arquivos",
        "note": "",
    }

    executable = available_exiftool()
    if executable:
        try:
            groups = extract_exiftool(candidate, executable)
            if groups:
                result["groups"].extend(groups)
                result["source"] = "Sistema de arquivos + ExifTool"
                result["note"] = (
                    "Todas as tags reconhecidas pelo ExifTool são apresentadas "
                    "sem exclusões por privacidade. Campos binários podem ser "
                    "representados por descritores ou tamanhos pelo ExifTool."
                )
                return _finalize(result)
        except (ValueError, RuntimeError, OSError) as exc:
            result["note"] = (
                f"ExifTool não concluiu a leitura ({type(exc).__name__}); "
                "tentando leitor de imagem local."
            )

    if candidate.suffix.lower() in _IMAGE_SUFFIXES:
        if info.st_size > _IMAGE_MAX_BYTES:
            result["note"] += (
                " Imagem acima do limite técnico de 80 MiB para Pillow. "
                "Dados gerais disponíveis."
            )
            return _finalize(result)
        try:
            groups = _image_groups(candidate)
            for group in groups:
                result.setdefault("raw_sections", []).extend(
                    group.pop("_raw_sections", [])
                )
            result["groups"].extend(groups)
            result["source"] = "Sistema de arquivos + Pillow"
            if len(groups) == 1:
                result["note"] += (
                    " Nenhum grupo EXIF ou informação interna adicional "
                    "foi encontrado pelo Pillow; outros padrões ainda podem existir."
                )
            else:
                result["note"] += (
                    " Os campos de metadados interpretáveis foram apresentados "
                    "por grupos. XMP/XML original pode ser consultado separadamente. "
                    "ExifTool pode identificar estruturas adicionais."
                )
        except ImportError:
            result["note"] += (
                " Pillow não instalado. Instale o extra metadata para ler "
                "campos internos de imagem."
            )
        except (OSError, ValueError, TypeError, SyntaxError) as exc:
            result["note"] += f" Leitura de imagem não concluída: {type(exc).__name__}."
    else:
        result["note"] += (
            " Este formato ainda não possui leitor interno na instalação atual. "
            "Instale ExifTool localmente para consultar formatos adicionais "
            "(PDF, Office, áudio, vídeo, compactados e outros)."
        )
    return _finalize(result)


def _finalize(result: dict[str, Any]) -> dict[str, Any]:
    """Compatibilidade com a GUI antiga e representação legível estruturada."""
    groups = []
    remaining = _MAX_FIELDS
    for group in result["groups"]:
        entries = []
        for label, value in group["fields"]:
            if remaining <= 0:
                break
            entries.append((str(label), _display(value)))
            remaining -= 1
        if entries:
            groups.append({"name": group["name"], "fields": entries})
        if remaining <= 0:
            break
    result["groups"] = groups
    result["fields"] = [
        (label, value) for group in groups for label, value in group["fields"]
    ]
    if remaining <= 0:
        result["note"] += (
            f" Limite técnico de {_MAX_FIELDS} campos por leitura atingido; "
            "o arquivo pode conter mais tags."
        )
    return result


def format_metadata_report(result: dict[str, Any]) -> str:
    """Agrupa os campos para leitura profissional em ambos os painéis Qt."""
    lines: list[str] = []
    groups = result.get("groups")
    if groups:
        for group in groups:
            lines.append(f"── {group.get('name', 'Sem grupo')} ──")
            lines.extend(
                f"{label}: {value}" for label, value in group.get("fields", [])
            )
            lines.append("")
    else:
        lines.extend(
            f"{label}: {value}" for label, value in result.get("fields", [])
        )
    lines.append(f"Fonte: {result.get('source', 'Não identificada')}")
    note = result.get("note")
    if note:
        lines.extend(("", str(note)))
    return "\n".join(lines)
