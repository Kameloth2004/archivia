"""Interface de linha de comando do ArchivIA."""

from __future__ import annotations

import argparse
import json
import sys

from .catalog import DEFAULT_DB, store_inventory
from .inventory import inventory


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="archivia", description="Bibliotecário digital local")
    commands = parser.add_subparsers(dest="command", required=True)

    scan = commands.add_parser("inventario", help="Inventariar mídias sem modificar arquivos")
    scan.add_argument("pasta", help="Pasta inicial para a leitura")

    catalog = commands.add_parser("catalogar", help="Inventariar e salvar snapshot no SQLite local")
    catalog.add_argument("pasta", help="Pasta inicial para a leitura")
    catalog.add_argument(
        "--banco", default=str(DEFAULT_DB),
        help="Caminho do SQLite (padrão: data/catalogo.sqlite3 na raiz do projeto)",
    )
    args = parser.parse_args(argv)

    try:
        result = inventory(args.pasta)
        if args.command == "catalogar":
            output = store_inventory(result, db_path=args.banco)
        else:
            output = result
    except (ValueError, OSError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
