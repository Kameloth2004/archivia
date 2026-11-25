"""Campo de data editável com calendário opcional para a Biblioteca.

A apresentação respeita as preferências locais; o catálogo continua em ISO.
Não realiza consultas nem operações em arquivos.
"""
from __future__ import annotations

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import QCalendarWidget, QLineEdit, QMenu, QWidgetAction

from .date_formats import DATE_FORMATS, date_input_mask, display_date, parse_user_date
from .gui_icons import icon_for


class CalendarDateEdit(QLineEdit):
    """QLineEdit mascarado com calendário e ação explícita de limpar."""

    def __init__(self, format_key: str = "br", parent=None) -> None:
        super().__init__(parent)
        self._format_key = format_key
        self.setInputMask(date_input_mask(format_key))
        self.setPlaceholderText(DATE_FORMATS[format_key][1])
        self.setMinimumWidth(148)
        self.setMaximumWidth(175)
        self.setToolTip(
            "Digite uma data ou clique no calendário. Deixe vazio para não filtrar."
        )

        self._menu = QMenu(self)
        self._calendar = QCalendarWidget(self._menu)
        self._calendar.setGridVisible(True)
        self._calendar.setFirstDayOfWeek(Qt.DayOfWeek.Monday)
        self._calendar.clicked.connect(self._date_chosen)
        calendar_action = QWidgetAction(self._menu)
        calendar_action.setDefaultWidget(self._calendar)
        self._menu.addAction(calendar_action)
        self._menu.addSeparator()
        self._menu.addAction("Limpar data", self._clear_from_menu)

        button = self.addAction(
            icon_for("calendar"), QLineEdit.ActionPosition.TrailingPosition
        )
        button.setToolTip("Escolher data no calendário")
        button.triggered.connect(self._show_calendar)

    def set_date_format(self, format_key: str) -> None:
        """Troca formato mantendo o mesmo dia, se a data estiver válida."""
        if format_key not in DATE_FORMATS:
            raise ValueError("Formato de data desconhecido.")
        try:
            selected = parse_user_date(self.text(), self._format_key)
        except ValueError:
            selected = ""
        self._format_key = format_key
        self.clear()
        self.setInputMask(date_input_mask(format_key))
        self.setPlaceholderText(DATE_FORMATS[format_key][1])
        if selected:
            self.setText(display_date(selected, format_key))

    def _show_calendar(self) -> None:
        try:
            iso = parse_user_date(self.text(), self._format_key)
        except ValueError:
            iso = ""
        selected = QDate.fromString(iso, Qt.DateFormat.ISODate) if iso else QDate.currentDate()
        if not selected.isValid():
            selected = QDate.currentDate()
        self._calendar.setSelectedDate(selected)
        self._calendar.showSelectedDate()
        self._menu.popup(self.mapToGlobal(self.rect().bottomLeft()))

    def _date_chosen(self, selected: QDate) -> None:
        if not selected.isValid():
            return
        self.setText(display_date(selected.toString(Qt.DateFormat.ISODate), self._format_key))
        self._menu.hide()
        # Reutiliza a atualização já conectada ao Enter no Acervo.
        self.returnPressed.emit()

    def _clear_from_menu(self) -> None:
        self.clear()
        self._menu.hide()
        self.returnPressed.emit()
