"""Interpretação local de pacotes XMP/XML sem lista restritiva de campos.

Não realiza downloads, não resolve entidades externas e não modifica
arquivos. Retém o XML original separadamente para consulta sob demanda.
"""
from __future__ import annotations

from io import BytesIO
import xml.etree.ElementTree as ET
from typing import Any

_MAX_XMP_BYTES = 2 * 1024 * 1024
_MAX_XML_DEPTH = 32
_MAX_XMP_FIELDS = 2000
_XMP_KEYS = frozenset({"xmp", "xml:com.adobe.xmp", "xml:com.adobe.xmp\x00"})


def is_xmp_key(name: str) -> bool:
    return str(name).casefold() in _XMP_KEYS


def _decoded(raw: bytes | str) -> str:
    if isinstance(raw, str):
        return raw
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16")
    return raw.decode("utf-8-sig", errors="replace")


def parse_xmp(raw: bytes | str) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Retorna grupos estruturados e a seção XML original, sem filtros.

    O XML deve ser pequeno e não pode declarar entidades ou DTD. Elementos,
    atributos e valores são mantidos; nomes de tags recebem o prefixo XML
    original sempre que declarado, inclusive os nomes IPTC personalizados.
    """
    payload = raw.encode("utf-8") if isinstance(raw, str) else bytes(raw)
    if len(payload) > _MAX_XMP_BYTES:
        raise ValueError("XMP acima do limite técnico de 2 MiB.")
    source = _decoded(raw)
    if "<!doctype" in source.casefold() or "<!entity" in source.casefold():
        raise ValueError("XMP com DTD/entidades não é permitido na leitura XML.")
    nsmap: dict[str, str] = {}
    root = None
    try:
        parser = ET.iterparse(BytesIO(payload), events=("start", "start-ns"))
        for kind, value in parser:
            if kind == "start-ns":
                prefix, uri = value
                nsmap.setdefault(uri, prefix or "ns")
            elif root is None:
                root = value
    except ET.ParseError as exc:
        raise ValueError("XMP/XML malformado.") from exc
    if root is None:
        raise ValueError("XMP/XML vazio.")

    def qname(name: str) -> str:
        if name.startswith("{") and "}" in name:
            uri, local = name[1:].split("}", 1)
            prefix = nsmap.get(uri)
            return f"{prefix}:{local}" if prefix else f"{{{uri}}}{local}"
        return name

    structural = {"x:xmpmeta", "rdf:RDF", "rdf:Description",
                  "rdf:Bag", "rdf:Alt", "rdf:Seq"}
    fields: list[tuple[str, str]] = []
    stack = [(root, "", 0)]
    seen = 0
    stopped = False
    while stack:
        element, parent, depth = stack.pop()
        if depth > _MAX_XML_DEPTH or seen >= _MAX_XMP_FIELDS:
            stopped = True
            continue
        seen += 1
        name = qname(element.tag)
        is_container = name in structural
        if name == "rdf:li":
            path = parent
        elif is_container:
            path = parent
        else:
            path = f"{parent}/{name}" if parent else name

        for attr_name, value in element.attrib.items():
            if len(fields) >= _MAX_XMP_FIELDS:
                stopped = True
                break
            label = f"{path}@{qname(attr_name)}" if path else qname(attr_name)
            fields.append((label, value))
        if not len(element) and element.text and element.text.strip():
            if len(fields) < _MAX_XMP_FIELDS:
                fields.append((path or name, element.text.strip()))
            else:
                stopped = True
        children = list(element)
        for idx in range(len(children) - 1, -1, -1):
            child = children[idx]
            child_name = qname(child.tag)
            next_parent = path
            if child_name == "rdf:li":
                number = sum(qname(s.tag) == "rdf:li" for s in children[:idx + 1])
                next_parent = f"{path}[{number}]"
            stack.append((child, next_parent, depth + 1))
    groups = [{"name": "XMP — campos XML estruturados", "fields": fields}]
    if stopped:
        groups.append({"name": "XMP — limites técnicos", "fields": [
            ("Aviso", "Profundidade ou quantidade máxima de campos atingida; "
             "consulte o XML original para visualizar o pacote recebido."),
        ]})
    return groups, {"name": "XMP — XML original", "text": source}


def xmp_from_image_info(info: dict[str, Any]) -> tuple[list[dict], list[dict], list[str]]:
    """Extrai todas as entradas XMP conhecidas do dicionário do Pillow."""
    groups: list[dict] = []
    raw_sections: list[dict] = []
    warnings: list[str] = []
    for key, value in info.items():
        if not is_xmp_key(str(key)):
            continue
        try:
            parsed, raw = parse_xmp(value)
        except (ValueError, TypeError, UnicodeError) as exc:
            warnings.append(f"XMP ({key}): {exc}")
            if isinstance(value, (str, bytes)):
                text = _decoded(value)
                if len(text.encode("utf-8")) <= _MAX_XMP_BYTES:
                    raw_sections.append({
                        "name": f"XMP — XML bruto ({key})", "text": text,
                    })
            continue
        groups.extend(parsed)
        raw_sections.append(raw)
    return groups, raw_sections, warnings
