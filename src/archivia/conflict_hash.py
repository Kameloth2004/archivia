"""Verificação SHA-256 sob demanda de UM conflito do último plano (somente leitura)."""
from __future__ import annotations

from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Any

from .catalog import DEFAULT_DB
from .duplicates import _candidate_path, _is_symlink_component, _sha256_checked


def verify_plan_conflict(
    plan: dict[str, Any] | None, file_name: str, *,
    db_path: Path = DEFAULT_DB, scan_id: int | None = None,
) -> dict[str, Any]:
    """Compara um par identificado no plano; nenhum caminho é escolhido pelo modelo.

    O hash da origem exige correspondência com os metadados do snapshot;
    o destino é revalidado antes e durante a leitura. A conclusão é pontual,
    jamais uma autorização de mover ou apagar.
    """
    if not isinstance(file_name, str) or not file_name.strip() or len(file_name) > 512:
        raise ValueError("Informe o nome relativo exato do arquivo bloqueado.")
    if (not isinstance(plan, dict) or plan.get("mode") != "simulation"
            or plan.get("executable") is not False
            or not isinstance(scan_id, int) or isinstance(scan_id, bool)
            or plan.get("scan_id") != scan_id):
        raise ValueError("Plano ausente ou pertencente a outro snapshot.")

    needle = file_name.strip().replace("\\", "/").casefold()
    actions = plan.get("actions")
    if not isinstance(actions, list):
        raise ValueError("Plano sem ações válidas.")
    matches = [a for a in actions if isinstance(a, dict)
               and a.get("status") == "bloqueado"
               and a.get("reason") == "destino_ja_existe"
               and (str(a.get("file", "")).casefold() == needle
                    or str(a.get("file", "")).rsplit("/", 1)[-1].casefold() == needle)]
    if len(matches) != 1:
        raise ValueError("É necessário identificar um único conflito de nome no último plano.")
    action = matches[0]
    result: dict[str, Any] = {
        "file": action["file"], "reason_code": "destino_ja_existe",
        "status": "inconclusivo", "duplicate_sha256_confirmed": False,
        "sha256_equal": None, "read_only": True, "files_modified": False,
        "executable": False,
    }

    def inconclusive(reason: str) -> dict[str, Any]:
        result["detail"] = reason
        return result

    try:
        root = Path(plan["root"]).expanduser().absolute()
        dest = Path(plan["destination"]).expanduser().absolute()
        if (_is_symlink_component(root) or _is_symlink_component(dest)
                or not root.is_dir() or not dest.is_dir()
                or dest == root or root in dest.parents):
            return inconclusive("origem_ou_destino_indisponivel")
        source = _candidate_path(root, action["file"])
        target = dest / source.name
        if (str(source) != action.get("source")
                or str(target) != action.get("destination")
                or _is_symlink_component(target) or not target.is_file()
                or source == target):
            return inconclusive("conflito_ou_caminho_alterado")
        db = Path(db_path).expanduser().absolute()
        with closing(sqlite3.connect(db.as_uri() + "?mode=ro", uri=True)) as conn:
            conn.row_factory = sqlite3.Row
            scan = conn.execute("SELECT root FROM scans WHERE id=?", (scan_id,)).fetchone()
            record = conn.execute(
                "SELECT size_bytes, modified_utc FROM media "
                "WHERE scan_id=? AND relative_path=?",
                (scan_id, action["file"]),
            ).fetchone()
        if scan is None or Path(scan["root"]).absolute() != root or record is None:
            return inconclusive("snapshot_incompativel")
        origin_size = record["size_bytes"]
        dest_stat = target.stat(follow_symlinks=False)
        if origin_size < 0 or dest_stat.st_size < 0:
            return inconclusive("metadados_de_tamanho_invalidos")
        # Reutiliza a rotina consolidada, com revalidação do handle e leitura em blocos.
        source_digest = _sha256_checked(source, origin_size, record["modified_utc"])
        target_stamp = datetime.fromtimestamp(
            dest_stat.st_mtime, tz=timezone.utc
        ).isoformat()
        target_digest = _sha256_checked(target, dest_stat.st_size, target_stamp)
        equal = source_digest == target_digest
        result.update({
            "status": "duplicata_confirmada" if equal else "conteudo_diferente",
            "sha256_equal": equal, "duplicate_sha256_confirmed": equal,
            "source_sha256": source_digest, "destination_sha256": target_digest,
            "source_size_bytes": origin_size, "destination_size_bytes": dest_stat.st_size,
            "detail": "Comparação pontual; o bloqueio permanece e nenhuma ação é autorizada.",
        })
        return result
    except (OSError, ValueError, sqlite3.Error, TypeError, KeyError, OverflowError):
        return inconclusive("arquivo_indisponivel_ou_alterado_durante_verificacao")
