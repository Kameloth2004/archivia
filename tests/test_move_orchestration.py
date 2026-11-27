"""Caracterização da orquestração de lote/fila usando planos e executor simulados.

Os testes não movem arquivos e preservam as diferenças de contrato da GUI.
"""
import unittest
from unittest.mock import patch

from archivia.batch_move import move_batch_approved, MAX_BATCH_FILES
from archivia.queue_move import move_queue_approved, MAX_QUEUE_FILES
from archivia.move_executor import APPROVAL_PHRASE, MoveSkippedError


def plan_for(*names):
    return {
        "mode": "simulation", "executable": False,
        "operation": "move_recursive_consolidation",
        "complete": True, "pending": 0, "scan_id": 7,
        "actions": [
            {"file": n, "status": "proposto", "reason": None}
            for n in names
        ],
    }


class SharedMoveOrchestrationTests(unittest.TestCase):
    def test_limits_and_public_result_keys(self):
        self.assertEqual(MAX_BATCH_FILES, 20)
        self.assertEqual(MAX_QUEUE_FILES, 10_000)
        plan = plan_for("a.jpg")
        with patch("archivia.batch_move.move_one_approved", return_value={"status": "movido"}):
            batch = move_batch_approved(plan, ["a.jpg"], scan_id=7, approval=APPROVAL_PHRASE)
        with patch("archivia.queue_move.move_one_approved", return_value={"status": "movido"}):
            queue = move_queue_approved(plan, ["a.jpg"], scan_id=7, approval=APPROVAL_PHRASE)
        self.assertEqual(batch["operation"], "approved_batch_move")
        self.assertEqual(queue["operation"], "approved_queue_move")
        self.assertNotIn("stopped_reason", batch)
        self.assertIsNone(queue["stopped_reason"])
        self.assertEqual(batch["moved"], queue["moved"])
        self.assertTrue(batch["files_modified"])
        self.assertTrue(queue["files_modified"])

    def test_cancel_queue_before_first_file(self):
        plan = plan_for("a.jpg")
        with patch("archivia.queue_move.move_one_approved") as executor:
            result = move_queue_approved(
                plan, ["a.jpg"], scan_id=7, approval=APPROVAL_PHRASE,
                interrupted=lambda: True,
            )
        executor.assert_not_called()
        self.assertEqual(result["processed"], 0)
        self.assertEqual(result["pending"], 1)
        self.assertEqual(result["stopped_reason"], "interrompido_pelo_usuario")

    def test_cancel_queue_between_items_and_report_progress(self):
        plan = plan_for("a.jpg", "b.jpg")
        progress = []
        with patch("archivia.queue_move.move_one_approved", return_value={"status": "movido"}) as executor:
            result = move_queue_approved(
                plan, ["a.jpg", "b.jpg"], scan_id=7, approval=APPROVAL_PHRASE,
                progress=progress.append, interrupted=lambda: len(progress) == 1,
            )
        self.assertEqual(executor.call_count, 1)
        self.assertEqual([e["processed"] for e in progress], [1])
        self.assertEqual(result["processed"], 1)
        self.assertEqual(result["pending"], 1)
        self.assertTrue(result["stopped"])

    def test_safe_block_still_continues_both_adapters(self):
        plan = plan_for("a.jpg", "b.jpg")
        for module, func in (
            ("archivia.batch_move.move_one_approved", move_batch_approved),
            ("archivia.queue_move.move_one_approved", move_queue_approved),
        ):
            with self.subTest(module=module):
                with patch(module, side_effect=[
                    MoveSkippedError("ocupado"), {"status": "movido"},
                ]):
                    result = func(plan, ["a.jpg", "b.jpg"], scan_id=7, approval=APPROVAL_PHRASE)
                self.assertEqual(result["blocked"], 1)
                self.assertEqual(result["moved"], 1)
                self.assertFalse(result["stopped"])

    def test_unsafe_error_stops_both_adapters(self):
        plan = plan_for("a.jpg", "b.jpg")
        for module, func in (
            ("archivia.batch_move.move_one_approved", move_batch_approved),
            ("archivia.queue_move.move_one_approved", move_queue_approved),
        ):
            with self.subTest(module=module):
                with patch(module, side_effect=OSError("disco indisponível")) as executor:
                    result = func(plan, ["a.jpg", "b.jpg"], scan_id=7, approval=APPROVAL_PHRASE)
                self.assertEqual(executor.call_count, 1)
                self.assertEqual(result["errors"], 1)
                self.assertEqual(result["pending"], 1)
                self.assertTrue(result["stopped"])

    def test_queue_rejects_ambiguous_plan_even_when_selected_once(self):
        plan = plan_for("a.jpg", "a.jpg")
        with self.assertRaises(ValueError):
            move_queue_approved(plan, ["a.jpg"], scan_id=7, approval=APPROVAL_PHRASE)

    def test_rejects_wrong_snapshot_and_approval_before_executor(self):
        plan = plan_for("a.jpg")
        for module, func in (
            ("archivia.batch_move.move_one_approved", move_batch_approved),
            ("archivia.queue_move.move_one_approved", move_queue_approved),
        ):
            with self.subTest(module=module), patch(module) as executor:
                with self.assertRaises(ValueError):
                    func(plan, ["a.jpg"], scan_id=7, approval="")
                with self.assertRaises(ValueError):
                    func(plan, ["a.jpg"], scan_id=8, approval=APPROVAL_PHRASE)
                executor.assert_not_called()


if __name__ == "__main__":
    unittest.main()
