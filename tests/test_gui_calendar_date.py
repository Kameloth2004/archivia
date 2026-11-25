"""TEST-ONLY: campos de calendário sem arquivos pessoais, SQLite ou Ollama."""
from __future__ import annotations

import os
import unittest

# Permite rodar a suíte também em máquinas sem display ativo.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import QDate
    from PySide6.QtWidgets import QApplication
    from archivia.gui_date_field import CalendarDateEdit
except ImportError:
    QApplication = None


@unittest.skipIf(QApplication is None, "PySide6 opcional não instalado")
class CalendarDateEditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_calendar_choice_uses_regional_format_and_emits_search(self):
        for key, expected in (
            ("br", "15/06/2024"), ("iso", "2024-06-15"),
            ("us", "06/15/2024"),
        ):
            with self.subTest(format=key):
                field = CalendarDateEdit(key)
                events = []
                field.returnPressed.connect(lambda: events.append("busca"))
                field._date_chosen(QDate(2024, 6, 15))
                self.assertEqual(field.text(), expected)
                self.assertEqual(events, ["busca"])
                field.close()

    def test_change_format_keeps_same_iso_day(self):
        field = CalendarDateEdit("br")
        field.setText("31/12/2024")
        field.set_date_format("iso")
        self.assertEqual(field.text(), "2024-12-31")
        field.set_date_format("us")
        self.assertEqual(field.text(), "12/31/2024")
        field.close()

    def test_blank_and_clear_remain_optional(self):
        field = CalendarDateEdit("br")
        field.setText("01/01/2024")
        events = []
        field.returnPressed.connect(lambda: events.append("busca"))
        field._clear_from_menu()
        self.assertFalse(any(char.isdigit() for char in field.text()))
        self.assertEqual(events, ["busca"])
        field.set_date_format("iso")
        self.assertFalse(any(char.isdigit() for char in field.text()))
        field.close()

    def test_invalid_and_incomplete_date_not_silently_reinterpreted(self):
        field = CalendarDateEdit("br")
        field.setText("31/02/2024")
        field.set_date_format("iso")
        self.assertFalse(any(char.isdigit() for char in field.text()))
        with self.assertRaises(ValueError):
            field.set_date_format("desconhecido")
        field.close()


if __name__ == "__main__":
    unittest.main()
