"""Extração de metadados sob demanda, somente leitura e extensível.

A função não é chamada por listagens, miniaturas ou seleção de arquivos:
apenas a ação explícita Verificar metadados deve solicitá-la.
Não analisa conteúdo documental, executa código ou grava tags.
"""
from __future__ import annotations

from datetime import datetime
import mimetypes
from pathlib import Path
import stat
from typing import Any

_IMAGE_SUFFIXES = frozenset({
    ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff", ".avif",
})
_IMAGE_MAX_BYTES = 40 * 1024 * 1024
_EXIF_ALLOWED = {
    "DateTimeOriginal": "Capturado em (EXIF)",
    "DateTimeDigitized": "Digitalizado em (EXIF)",
    "DateTime": "Data interna (EXIF)",
    "Make": "Fabricante",
    "Model": "Câmera / modelo",
    "Software": "Software",
    "Artist": "Artista",
    "Copyright": "Direitos autorais",
    "LensModel": "Lente",
    "ExposureTime": "Tempo de exposição",
    "FNumber": "Abertura (f)",
    "ISOSpeedRatings": "ISO",
    "PhotographicSensitivity": "ISO",
    "FocalLength": "Distância focal",
    "Orientation": "Orientação (EXIF)",
}
# GPS, dados privados, UserComment, MakerNote e blobs nunca são expostos.
_MAX_VALUE_LENGTH = 180


def _text(value: Any) -> str:
    if isinstance(value, bytes):
        return "(valor binário omitido)"
    result = str(value).strip().replace("\x00", "")
    return result[:_MAX_VALUE_LENGTH] + ("…" if len(result) > _MAX_VALUE_LENGTH else "")


def read_file_metadata(path: str | Path) -> dict[str, Any]:
    """Extrai dados gerais e, quando suportado, metadados da imagem.

    Limites de tamanho e tipos aplicam-se a leitores internos. A segurança
    do caminho dentro da pasta ativa deve ser verificada pela GUI antes
    de invocar esta função.
    """
    candidate = Path(path)
    if candidate.is_symlink():
        raise ValueError("Links simbólicos não são aceitos na verificação.")
    info = candidate.stat(follow_symlinks=False)
    if not stat.S_ISREG(info.st_mode):
        raise ValueError("A verificação aceita somente arquivos regulares.")

    modified = datetime.fromtimestamp(info.st_mtime).strftime("%d/%m/%Y %H:%M:%S")
    mime, _ = mimetypes.guess_type(candidate.name)
    fields: list[tuple[str, str]] = [
        ("Formato identificado pela extensão", mime or "Desconhecido"),
        ("Tamanho", f"{info.st_size:,} bytes"),
        ("Modificado (sistema)", modified),
    ]
    result: dict[str, Any] = {
        "name": candidate.name,
        "fields": fields,
        "source": "Sistema de arquivos",
        "note": "Nenhum conteúdo interno foi lido.",
    }
    if candidate.suffix.lower() not in _IMAGE_SUFFIXES:
        result["note"] = (
            "Este formato ainda não possui leitor de metadados internos. "
            "Os dados gerais estão disponíveis; leitores especializados "
            "serão acrescentados sem executar o arquivo."
        )
        return result
    if info.st_size > _IMAGE_MAX_BYTES:
        result["note"] = (
            "Imagem acima do limite de 40 MiB para leitura de metadados. "
            "Somente dados gerais foram exibidos."
        )
        return result

    try:
        from PIL import Image, ExifTags
    except ImportError:
        # A V2 básica permanece funcional sem instalar bibliotecas extras.
        result["note"] = (
            "Para ler EXIF e detalhes internos de imagens, instale o suporte "
            "opcional de metadados (Pillow). Nenhuma imagem foi modificada."
        )
        return result

    try:
        with Image.open(candidate) as picture:
            fields.append(("Formato interno", picture.format or "Desconhecido"))
            fields.append(("Dimensões", f"{picture.width} × {picture.height} pixels"))
            fields.append(("Modo de cor", picture.mode))
            # getexif() lê tags, não carrega/descompacta os pixels da imagem.
            exif = picture.getexif()
            if exif:
                added: set[str] = set()
                # Datas da captura, ISO e lente frequentemente estão no
                # subdiretório Exif IFD (34665), não no IFD principal.
                # Nunca expandir o GPS IFD (34853).
                sources = [exif]
                try:
                    camera_ifd = exif.get_ifd(34665)
                    if camera_ifd:
                        sources.append(camera_ifd)
                except (ValueError, TypeError, KeyError, OSError):
                    pass
                for tags in sources:
                    for tag_id, value in tags.items():
                        name = ExifTags.TAGS.get(tag_id, "")
                        label = _EXIF_ALLOWED.get(name)
                        if not label or label in added:
                            continue
                        fields.append((label, _text(value)))
                        added.add(label)
                result["source"] = "Sistema de arquivos + EXIF"
                result["note"] = (
                    "Somente tags EXIF selecionadas. GPS e campos privados "
                    "não são exibidos."
                )
            else:
                result["source"] = "Sistema de arquivos + cabeçalho da imagem"
                result["note"] = "A imagem não apresenta tags EXIF acessíveis."
    except (OSError, ValueError, SyntaxError, TypeError) as exc:
        # Nunca renderizar o conteúdo bruto de arquivos inválidos.
        result["note"] = f"Não foi possível ler metadados internos: {type(exc).__name__}."
    return result
