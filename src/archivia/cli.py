"""Interface de linha de comando do ArchivIA."""

from __future__ import annotations

import argparse
import json
import sys

from .catalog import DEFAULT_DB, catalog_summary, query_catalog, store_inventory
from .inventory import inventory
from .planner import propose_moves


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
    search = commands.add_parser("consultar", help="Consultar o último inventário salvo, sem alterar o banco")
    search.add_argument("--categoria", choices=("imagem", "video", "audio"), help="Filtrar categoria")
    search.add_argument("--banco", default=str(DEFAULT_DB), help="Caminho do SQLite")

    summary = commands.add_parser("resumo", help="Mostrar totais do último inventário salvo")
    summary.add_argument("--banco", default=str(DEFAULT_DB), help="Caminho do SQLite")

    planner = commands.add_parser("planejar", help="Prévia sem executar movimentações")
    planner.add_argument("--destino", required=True, help="Diretório de destino existente")
    planner.add_argument("--categoria", required=True, choices=("imagem", "video", "audio"))
    planner.add_argument("--limite", type=int, default=100, help="Máximo de operações propostas (1 a 100)")
    planner.add_argument("--banco", default=str(DEFAULT_DB), help="Caminho do SQLite")

    args = parser.parse_args(argv)

    try:
        if args.command == "planejar":
            output = propose_moves(args.destino, args.categoria, db_path=args.banco, limit=args.limite)
            result = {"errors": []}
        elif args.command == "resumo":
            output = catalog_summary(db_path=args.banco)
            result = {"errors": []}
        elif args.command == "consultar":
            output = query_catalog(db_path=args.banco, category=args.categoria)
            result = {"errors": []}
        else:
            result = inventory(args.pasta)
        if args.command == "catalogar":
            output = store_inventory(result, db_path=args.banco)
        elif args.command == "inventario":
            output = result
    except (ValueError, OSError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
