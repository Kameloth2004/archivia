"""Decodificação local de imagens para prévias Qt, sem modificar arquivos.

Qt permanece como leitor principal; Pillow 11.3+ serve de fallback para formatos compatíveis.
Limites referem-se a pixels decodificados e ao tamanho da prévia exibida:
não são limites arbitrários de resolução do monitor.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QImage, QImageReader


def decode_preview(
    path: str | Path, *,
    max_side: int,
    max_source_pixels: int,
) -> tuple[QImage, tuple[int, int]]:
    """Retorna (imagem redimensionada, dimensões originais) sem gravar no disco."""
    path = Path(path)
    reader = QImageReader(str(path))
    reader.setAutoTransform(True)
    source = reader.size()
    valid = source.isValid() and source.width() > 0 and source.height() > 0
    if valid:
        pixels = source.width() * source.height()
        if pixels > max_source_pixels:
            raise ValueError(
                f"Imagem de {source.width()} × {source.height()} pixels excede "
                f"o limite de processamento ({max_source_pixels:,} pixels)."
            )
        target = source.scaled(
            QSize(max_side, max_side), Qt.AspectRatioMode.KeepAspectRatio
        )
        reader.setScaledSize(target)
        image = reader.read()
        if not image.isNull():
            return image, (source.width(), source.height())

    qt_detail = reader.errorString()
    return _decode_with_pillow(
        path, max_side=max_side, max_source_pixels=max_source_pixels,
        qt_detail=qt_detail,
    )


def _decode_with_pillow(
    path: Path, *, max_side: int, max_source_pixels: int, qt_detail: str,
) -> tuple[QImage, tuple[int, int]]:
    try:
        from PIL import Image, UnidentifiedImageError
        from PIL import __version__ as pillow_version
    except ImportError as exc:
        raise ValueError(
            "O Qt não conseguiu decodificar a imagem e Pillow não está instalado. "
            "Instale o leitor opcional: pip install 'Pillow>=11.3,<13'."
        ) from exc

    try:
        with Image.open(path) as opened:
            if opened.format is None:
                raise ValueError("O arquivo não contém um formato de imagem reconhecido.")
            width, height = opened.size
            if width <= 0 or height <= 0:
                raise ValueError("A imagem não informa dimensões válidas.")
            if width * height > max_source_pixels:
                raise ValueError(
                    f"Imagem de {width} × {height} pixels excede "
                    f"o limite de processamento ({max_source_pixels:,} pixels)."
                )
            # thumbnail() pode usar redução nativa de codec; de todo modo
            # o teto de pixels originais evita descompressões descontroladas.
            opened.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
            rgba = opened.convert("RGBA")
            raw = rgba.tobytes()
            image = QImage(
                raw, rgba.width, rgba.height, rgba.width * 4,
                QImage.Format.Format_RGBA8888,
            ).copy()  # desacopla QImage da memória Python/Pillow
            if image.isNull():
                raise ValueError("Não foi possível transformar AVIF em imagem Qt.")
            return image, (width, height)
    except (OSError, UnidentifiedImageError) as exc:
        raise ValueError(
            "O Qt não conseguiu abrir a imagem "
            f"({qt_detail or 'formato indisponível'}); Pillow {pillow_version} "
            "também não conseguiu decodificá-la. Verifique o formato e "
            "a integridade do arquivo."
        ) from exc
