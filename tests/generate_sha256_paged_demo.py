"""TEST-ONLY: gerador seguro de cenário SHA-256 multipágina para homologação GUI.

Cria apenas em tests/fixtures/manual/sha256_paginado por padrão.
Não executa automaticamente ao importar e nunca limpa/substitui arquivos existentes.
Os .jpg contêm bytes sintéticos, NÃO são fotografias reais.
"""
from __future__ import annotations

import argparse
from pathlib import Path

TESTS = Path(__file__).resolve().parent
DEFAULT_ROOT = TESTS / "fixtures" / "manual" / "sha256_paginado"
TOTAL_FILES = 134
EXPECTED_GROUP_SIZES = (3, 2, 2)


def fixture_payloads() -> dict[str, bytes]:
    """Constrói 134 nomes ordenáveis, incluindo duplicatas entre páginas 1 e 2."""
    # 125 preenchimentos diferentes, porém todos com o mesmo tamanho.
    # SHA-256 deve descartá-los como cópias mesmo com tamanho coincidente.
    data = {
        f"M/filler_{index:03d}.jpg": f"TEST-ONLY-FILLER-{index:03d}".encode("ascii")
        for index in range(125)
    }
    # A extensão é apenas para classificação no inventário, não é JPEG válido.
    data.update({
        "A/000_foto_original.jpg": b"TEST-ONLY-CONTENT-ALFA",
        "L/050_alias_nome.jpg": b"TEST-ONLY-CONTENT-ALFA",
        "Z/999_foto_copia.jpg": b"TEST-ONLY-CONTENT-ALFA",
        "B/010_relatorio.jpg": b"TEST-ONLY-CONTENT-BETA",
        "Y/990_outro_nome.jpg": b"TEST-ONLY-CONTENT-BETA",
        "C/020_vazio.jpg": b"",
        "X/980_vazio_copia.jpg": b"",
        "D/030_mesmo_nome.jpg": b"TEST-ONLY-ABCDE",
        "W/970_mesmo_nome.jpg": b"TEST-ONLY-ZYXWV",
    })
    assert len(data) == TOTAL_FILES
    return data


def generate_fixture(root: Path = DEFAULT_ROOT) -> dict[str, object]:
    """Cria arquivos exclusivamente em tests/; recusa pasta não vazia ou fora de tests/."""
    path = Path(root).expanduser().absolute()
    tests_root = TESTS.resolve()
    if path == tests_root or tests_root not in path.parents:
        raise ValueError("TEST-ONLY: destino deve estar estritamente dentro de tests/.")
    if any(
        part.is_symlink() or (hasattr(part, "is_junction") and part.is_junction())
        for part in (path, *path.parents)
    ):
        raise ValueError("TEST-ONLY: destino com link simbólico não permitido.")
    if path.exists() and (not path.is_dir() or any(path.iterdir())):
        raise FileExistsError(
            f"Destino já contém dados; não será sobrescrito: {path}"
        )
    if not path.exists():
        path.mkdir(parents=True, exist_ok=False)
    data = fixture_payloads()
    for relative, payload in sorted(data.items()):
        target = path / relative
        target.parent.mkdir(exist_ok=True)
        # Modo 'x' impede sobrescrita mesmo que um arquivo apareça durante a geração.
        with target.open("xb") as stream:
            stream.write(payload)
    return {"root": str(path), "files": len(data), "expected_groups": EXPECTED_GROUP_SIZES}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="TEST-ONLY: gerar cenário sintético SHA-256 com 134 arquivos."
    )
    parser.add_argument(
        "--destino", type=Path, default=DEFAULT_ROOT,
        help="Diretório vazio sob tests/ (padrão: tests/fixtures/manual/sha256_paginado)",
    )
    options = parser.parse_args()
    result = generate_fixture(options.destino)
    print("TEST-ONLY: cenário criado, nenhum arquivo pessoal alterado.")
    print("Pasta:", result["root"])
    print("Arquivos:", result["files"])
    print("Resultado SHA-256 esperado: 3 grupos, com 3 + 2 + 2 arquivos.")
    print("Use o limite de 200 arquivos para consultar duas páginas SQLite.")


if __name__ == "__main__":
    main()
