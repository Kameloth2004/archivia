"""TEST-ONLY: plano de movimentações sem executar nenhuma ação sobre arquivos."""
import unittest
import os
from datetime import datetime, timezone

from support import temporary_test_directory
from archivia.catalog import store_inventory, query_catalog_page
from archivia.inventory import inventory
from archivia.planner import propose_moves, propose_date_moves, summarize_consolidation


class PlannerTests(unittest.TestCase):
    def test_proposes_without_moving_or_modifying(self):
        with temporary_test_directory() as tmp:
            source = tmp / "midias"
            target = tmp / "destino"
            source.mkdir()
            target.mkdir()
            image = source / "foto.jpg"
            image.write_bytes(b"synthetic")
            db = tmp / "data" / "catalogo.sqlite3"
            store_inventory(inventory(source), db)
            plan = propose_moves(target, "imagem", db_path=db)
            self.assertFalse(plan["executable"])
            self.assertEqual(plan["mode"], "simulation")
            self.assertEqual(plan["selected"], 1)
            self.assertEqual(plan["blocked"], 0)
            self.assertEqual(plan["actions"][0]["status"], "proposto")
            self.assertTrue(image.exists())
            self.assertFalse((target / "foto.jpg").exists())

    def test_blocks_existing_destination(self):
        with temporary_test_directory() as tmp:
            source = tmp / "midias"
            target = tmp / "destino"
            source.mkdir()
            target.mkdir()
            (source / "foto.jpg").write_bytes(b"source")
            existing = target / "foto.jpg"
            existing.write_bytes(b"existing")
            db = tmp / "data" / "catalogo.sqlite3"
            store_inventory(inventory(source), db)
            plan = propose_moves(target, "imagem", db_path=db)
            self.assertEqual(plan["blocked"], 1)
            self.assertEqual(plan["actions"][0]["reason"], "destino_ja_existe_ou_link")
            self.assertEqual(existing.read_bytes(), b"existing")

    def test_blocks_duplicate_target_names_from_different_folders(self):
        # TEST-ONLY: nomes iguais em pastas distintas não devem competir pelo destino.
        with temporary_test_directory() as tmp:
            source = tmp / "midias"
            target = tmp / "destino"
            (source / "a").mkdir(parents=True)
            (source / "b").mkdir()
            target.mkdir()
            (source / "a" / "foto.jpg").write_bytes(b"um")
            (source / "b" / "foto.jpg").write_bytes(b"dois")
            db = tmp / "data" / "catalogo.sqlite3"
            store_inventory(inventory(source), db)
            plan = propose_moves(target, "imagem", db_path=db)
            self.assertEqual(plan["selected"], 2)
            self.assertEqual(plan["blocked"], 1)
            self.assertEqual(sum(a["status"] == "proposto" for a in plan["actions"]), 1)
            self.assertEqual(plan["actions"][1]["reason"], "destino_duplicado_no_plano")

    def test_blocks_changed_file(self):
        with temporary_test_directory() as tmp:
            source = tmp / "midias"
            target = tmp / "destino"
            source.mkdir()
            target.mkdir()
            image = source / "foto.jpg"
            image.write_bytes(b"a")
            db = tmp / "data" / "catalogo.sqlite3"
            store_inventory(inventory(source), db)
            image.write_bytes(b"alterado")
            plan = propose_moves(target, "imagem", db_path=db)
            self.assertEqual(plan["blocked"], 1)
            self.assertEqual(plan["actions"][0]["reason"], "origem_alterada_desde_inventario")

    def test_invalid_limit_or_destination(self):
        with temporary_test_directory() as tmp:
            source = tmp / "midias"
            source.mkdir()
            (source / "a.jpg").write_bytes(b"a")
            db = tmp / "data" / "catalogo.sqlite3"
            store_inventory(inventory(source), db)
            with self.assertRaises(ValueError):
                propose_moves(tmp / "inexistente", "imagem", db_path=db)
            with self.assertRaises(ValueError):
                propose_moves(tmp, "imagem", db_path=db, limit=0)

    def test_flat_consolidation_is_paginated_without_loading_full_catalog(self):
        # TEST-ONLY: exemplo Adele, centenas de imagens em subpastas sintéticas.
        with temporary_test_directory() as tmp:
            source = tmp / "Adele"
            destination = tmp / "Imagens Adele"
            destination.mkdir()
            for folder_number in range(6):
                folder = source / f"subpasta_{folder_number:02d}" / "fotos"
                folder.mkdir(parents=True)
                for image_number in range(35):
                    (folder / f"foto_{folder_number:02d}_{image_number:02d}.jpg").write_bytes(
                        f"TEST-ONLY-{folder_number}-{image_number}".encode()
                    )
                (folder / "musica.mp3").write_bytes(b"audio-teste")
            db = tmp / "catalogo.sqlite3"
            store_inventory(inventory(source), db)
            from unittest.mock import patch
            with patch("archivia.planner.query_catalog_page", wraps=query_catalog_page) as page:
                first = propose_moves(destination, "imagem", db_path=db, limit=50)
                self.assertEqual(page.call_count, 1)
                self.assertEqual(page.call_args.kwargs["page_size"], 50)
            self.assertEqual(first["total_matches"], 210)
            self.assertEqual(first["selected"], 50)
            self.assertTrue(first["truncated"])
            self.assertEqual(first["blocked"], 0)
            self.assertTrue(all(
                action["destination"] == str(destination / action["file"].split("/")[-1])
                for action in first["actions"]
            ))
            self.assertFalse(any(destination.iterdir()))
            self.assertEqual(len(list(source.rglob("*.jpg"))), 210)

    def test_flat_plan_can_select_older_snapshot_without_changing_sources(self):
        with temporary_test_directory() as tmp:
            old_root = tmp / "antiga"
            new_root = tmp / "nova"
            dest = tmp / "destino"
            old_root.mkdir()
            new_root.mkdir()
            dest.mkdir()
            (old_root / "foto.jpg").write_bytes(b"imagem")
            (new_root / "outra.jpg").write_bytes(b"outra")
            db = tmp / "catalogo.sqlite3"
            old = store_inventory(inventory(old_root), db)
            store_inventory(inventory(new_root), db)
            plan = propose_moves(
                dest, "imagem", db_path=db, scan_id=old["scan_id"]
            )
            self.assertEqual(plan["root"], str(old_root))
            self.assertEqual(plan["selected"], 1)
            self.assertEqual(plan["actions"][0]["file"], "foto.jpg")
            with self.assertRaises(ValueError):
                propose_moves(dest, "imagem", db_path=db, scan_id=99999)
            self.assertFalse(any(dest.iterdir()))

    def test_full_consolidation_detects_cross_page_collisions_without_writing(self):
        # TEST-ONLY: nome idêntico nos extremos de páginas SQL diferentes.
        with temporary_test_directory() as tmp:
            root = tmp / "origem"
            dest = tmp / "destino"
            dest.mkdir()
            for number in range(210):
                folder = root / f"pasta_{number:03d}"
                folder.mkdir(parents=True)
                name = "repetida.jpg" if number in (0, 209) else f"foto_{number:03d}.jpg"
                (folder / name).write_bytes(f"teste-{number}".encode())
                (folder / "audio.mp3").write_bytes(b"outro-tipo")
            db = tmp / "catalogo.sqlite3"
            snap = store_inventory(inventory(root), db)["scan_id"]
            summary = summarize_consolidation(dest, "imagem", db, scan_id=snap)
            self.assertEqual(summary["scan_id"], snap)
            self.assertEqual(summary["total_matches"], 210)
            self.assertEqual(summary["examined"], 210)
            self.assertEqual(summary["proposed"], 209)
            self.assertEqual(summary["blocked"], 1)
            self.assertEqual(summary["blocked_by_reason"]["destino_duplicado_no_plano"], 1)
            self.assertEqual(summary["pages_scanned"], 3)
            self.assertEqual(summary["pending"], 0)
            self.assertTrue(summary["complete"])
            self.assertFalse(summary["executable"])
            self.assertEqual(summary["actions"], [])
            self.assertEqual(list(dest.iterdir()), [])
            self.assertEqual(len(list(root.rglob("*.jpg"))), 210)

    def test_full_consolidation_cap_reports_pending_and_keeps_other_snapshot_out(self):
        with temporary_test_directory() as tmp:
            root = tmp / "primeira"
            other = tmp / "segunda"
            dest = tmp / "destino"
            root.mkdir()
            other.mkdir()
            dest.mkdir()
            for number in range(135):
                (root / f"foto_{number:03d}.jpg").write_bytes(b"teste")
            (other / "outra.jpg").write_bytes(b"outra")
            db = tmp / "catalogo.sqlite3"
            chosen = store_inventory(inventory(root), db)["scan_id"]
            store_inventory(inventory(other), db)
            summary = summarize_consolidation(
                dest, "imagem", db, scan_id=chosen, max_candidates=101,
            )
            self.assertEqual(summary["root"], str(root))
            self.assertEqual(summary["examined"], 101)
            self.assertEqual(summary["proposed"], 101)
            self.assertEqual(summary["pending"], 34)
            self.assertEqual(summary["pages_scanned"], 2)
            self.assertFalse(summary["complete"])
            self.assertTrue(summary["truncated"])
            self.assertEqual(summary["actions"], [])
            self.assertEqual(list(dest.iterdir()), [])
            for invalid in (0, True, 10001):
                with self.assertRaises(ValueError):
                    summarize_consolidation(dest, "imagem", db, max_candidates=invalid)

    def test_full_consolidation_blocks_existing_casefold_and_changed_sources(self):
        with temporary_test_directory() as tmp:
            root = tmp / "origem"
            dest = tmp / "destino"
            root.mkdir()
            dest.mkdir()
            (root / "Foto.JPG").write_bytes(b"arquivo-a")
            modified = root / "alterada.jpg"
            modified.write_bytes(b"original")
            existing = dest / "foto.jpg"
            existing.write_bytes(b"NAO SOBRESCREVER")
            db = tmp / "catalogo.sqlite3"
            store_inventory(inventory(root), db)
            modified.write_bytes(b"conteudo modificado")
            summary = summarize_consolidation(dest, "imagem", db)
            self.assertEqual(summary["examined"], 2)
            self.assertEqual(summary["blocked"], 2)
            self.assertEqual(summary["proposed"], 0)
            self.assertEqual(summary["blocked_by_reason"]["destino_ja_existe_ou_link"], 1)
            self.assertEqual(summary["blocked_by_reason"]["origem_alterada_desde_inventario"], 1)
            self.assertEqual(existing.read_bytes(), b"NAO SOBRESCREVER")

    def test_date_plan_proposes_year_month_without_writing(self):
        # TEST-ONLY: destino AAAA/MM fictício, nunca criado.
        with temporary_test_directory() as tmp:
            root = tmp / "origem"
            dest = tmp / "destino"
            root.mkdir()
            dest.mkdir()
            file = root / "foto.jpg"
            file.write_bytes(b"arquivo simulado")
            instant = datetime(2024, 7, 19, 12, tzinfo=timezone.utc).timestamp()
            os.utime(file, (instant, instant))
            db = tmp / "catalogo.sqlite3"
            store_inventory(inventory(root), db)
            plan = propose_date_moves(dest, "imagem", db)
            self.assertEqual(plan["mode"], "simulation")
            self.assertFalse(plan["executable"])
            self.assertEqual(plan["date_basis"], "modified_utc")
            self.assertEqual(plan["selected"], 1)
            self.assertEqual(plan["blocked"], 0)
            self.assertEqual(plan["actions"][0]["destination"], str(dest / "2024" / "07" / "foto.jpg"))
            self.assertTrue(plan["actions"][0]["directory_would_need_creation"])
            self.assertFalse((dest / "2024").exists())
            self.assertEqual(file.read_bytes(), b"arquivo simulado")

    def test_date_plan_collision_and_changed_files_are_blocked(self):
        # TEST-ONLY: dois arquivos idênticos no nome, mesmo destino anual.
        with temporary_test_directory() as tmp:
            root = tmp / "origem"
            dest = tmp / "destino"
            (root / "a").mkdir(parents=True)
            (root / "b").mkdir()
            dest.mkdir()
            instant = datetime(2025, 2, 5, tzinfo=timezone.utc).timestamp()
            for folder in ("a", "b"):
                file = root / folder / "foto.jpg"
                file.write_bytes(folder.encode())
                os.utime(file, (instant, instant))
            db = tmp / "catalogo.sqlite3"
            store_inventory(inventory(root), db)
            plan = propose_date_moves(dest, "imagem", db)
            self.assertEqual(plan["selected"], 2)
            self.assertEqual(plan["blocked"], 1)
            self.assertEqual(plan["actions"][1]["reason"], "destino_duplicado_no_plano")
            (root / "a" / "foto.jpg").write_bytes(b"alterado")
            changed = propose_date_moves(dest, "imagem", db)
            self.assertEqual(changed["actions"][0]["reason"], "origem_alterada_desde_inventario")
            self.assertFalse((dest / "2025").exists())

    def test_date_plan_flags_metadata_duplicates_without_hashing_or_writing(self):
        # TEST-ONLY: mesmo nome e tamanho são apenas suspeita, não duplicidade comprovada.
        with temporary_test_directory() as tmp:
            root = tmp / "origem"
            dest = tmp / "destino"
            (root / "a").mkdir(parents=True)
            (root / "b").mkdir()
            dest.mkdir()
            ts = datetime(2025, 2, 5, tzinfo=timezone.utc).timestamp()
            for subfolder, payload in (("a", b"ABC"), ("b", b"XYZ")):
                file = root / subfolder / "foto.jpg"
                file.write_bytes(payload)
                os.utime(file, (ts, ts))
            db = tmp / "catalogo.sqlite3"
            store_inventory(inventory(root), db)
            plan = propose_date_moves(dest, "imagem", db)
            self.assertEqual(plan["potential_duplicate_items"], 2)
            self.assertEqual(plan["name_collisions"], 1)
            self.assertEqual(plan["duplicate_detection"], "metadata_only_name_and_size_not_verified")
            self.assertTrue(all(a["possible_duplicate_by_metadata"] for a in plan["actions"]))
            blocked = next(a for a in plan["actions"] if a["status"] == "bloqueado")
            self.assertEqual(blocked["reason"], "destino_duplicado_no_plano")
            self.assertTrue(blocked["alternative_name_suggestion"].endswith("foto__2.jpg"))
            self.assertFalse((dest / "2025").exists())

    def test_date_plan_suggests_name_when_target_exists_without_overwriting(self):
        # TEST-ONLY: destino existente bloqueia proposta, alternativa é apenas texto.
        with temporary_test_directory() as tmp:
            root = tmp / "origem"
            dest = tmp / "destino"
            root.mkdir()
            (dest / "2024" / "07").mkdir(parents=True)
            file = root / "foto.jpg"
            file.write_bytes(b"nova")
            instant = datetime(2024, 7, 19, tzinfo=timezone.utc).timestamp()
            os.utime(file, (instant, instant))
            occupied = dest / "2024" / "07" / "foto.jpg"
            occupied.write_bytes(b"existente")
            db = tmp / "catalogo.sqlite3"
            store_inventory(inventory(root), db)
            plan = propose_date_moves(dest, "imagem", db)
            self.assertEqual(plan["blocked"], 1)
            self.assertEqual(plan["name_collisions"], 1)
            self.assertEqual(plan["actions"][0]["reason"], "destino_ja_existe")
            self.assertTrue(plan["actions"][0]["alternative_name_suggestion"].endswith("foto__2.jpg"))
            self.assertEqual(occupied.read_bytes(), b"existente")
            self.assertFalse((dest / "2024" / "07" / "foto__2.jpg").exists())

    def test_date_plan_rejects_missing_destination_and_invalid_limits(self):
        with temporary_test_directory() as tmp:
            root = tmp / "origem"
            root.mkdir()
            (root / "foto.jpg").write_bytes(b"abc")
            db = tmp / "catalogo.sqlite3"
            store_inventory(inventory(root), db)
            for bad in (0, True, 101):
                with self.assertRaises(ValueError):
                    propose_date_moves(tmp, "imagem", db, limit=bad)
            with self.assertRaises(ValueError):
                propose_date_moves(tmp / "nao_criar", "imagem", db)
            self.assertFalse((tmp / "nao_criar").exists())

    def test_plan_never_creates_destination(self):
        with temporary_test_directory() as tmp:
            source = tmp / "midias"
            source.mkdir()
            (source / "a.jpg").write_bytes(b"a")
            db = tmp / "data" / "catalogo.sqlite3"
            store_inventory(inventory(source), db)
            newdir = tmp / "nao_criar"
            with self.assertRaises(ValueError):
                propose_moves(newdir, "imagem", db_path=db)
            self.assertFalse(newdir.exists())


if __name__ == "__main__":
    unittest.main()
