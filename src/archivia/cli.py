"""Interface de linha de comando do ArchivIA."""

from __future__ import annotations

import argparse
import json
import sys

from .inventory import inventory


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="archivia", description="Bibliotecário digital local")
    commands = parser.add_subparsers(dest="command", required=True)
    scan = commands.add_parser("inventario", help="Inventariar mídias sem modificar arquivos")
    scan.add_argument("pasta", help="Pasta inicial para a leitura")
    args = parser.parse_args(argv)

    try:
        result = inventory(args.pasta)
    except (ValueError, OSError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
