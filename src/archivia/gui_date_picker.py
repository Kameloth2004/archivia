"""Campo opcional de data com digitação guiada e calendário local (PySide6).

Somente interface: não consulta SQLite, Ollama nem altera arquivos.
Mantém a API QLineEdit.text()/clear(), compatível com catalog_filters().
"""
from __future__ import annotations

from PySide6.QtCore import QDate, QPoint, Qt, QLocale, Signal
from PySide6.QtWidgets import (
    QCalendarWidget, QFrame, QHBoxLayout, QLineEdit, QPushButton, QVBoxLayout,
)

from .date_formats import DATE_FORMATS, date_input_mask, display_date, parse_user_date
from .gui_icons import icon_for


class CalendarDateEdit(QLineEdit):
    """Data opcional: máscara para digitar, calendário e opção de limpar.

    O calendário não define uma data implicitamente: o campo inicia vazio e
    somente a seleção explícita ou digitação do usuário aplica um filtro.
    """

    dateApplied = Signal()

    def __init__(self, format_key: str = "br", parent=None) -> None:
        super().__init__(parent)
        self._format_key = "br"
        self.set_date_format(format_key)
        self.setToolTip(
            "Digite a data ou clique no calendário. "
            "Use Limpar para consultar sem filtro de data."
        )

        action = self.addAction(
            icon_for("calendar"), QLineEdit.ActionPosition.TrailingPosition
        )
        action.setToolTip("Escolher data no calendário")
        action.triggered.connect(self._show_calendar)

        # Janela popup pertence ao campo e se fecha ao clicar fora dela.
        self._popup = QFrame(self, Qt.WindowType.Popup)
        self._popup.setObjectName("archiviaCalendarPopup")
        self._popup.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(self._popup)
        layout.setContentsMargins(7, 7, 7, 7)
        layout.setSpacing(7)

        self._calendar = QCalendarWidget(self._popup)
        self._calendar.setLocale(QLocale("pt_BR"))
        self._calendar.setFirstDayOfWeek(Qt.DayOfWeek.Monday)
        self._calendar.setVerticalHeaderFormat(
            QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader
        )
        self._calendar.clicked.connect(self._select_date)
        layout.addWidget(self._calendar)

        actions = QHBoxLayout()
        today_button = QPushButton("Hoje", self._popup)
        today_button.clicked.connect(self._select_today)
        actions.addWidget(today_button)
        clear_button = QPushButton("Limpar filtro", self._popup)
        clear_button.clicked.connect(self._clear_date)
        actions.addWidget(clear_button)
        layout.addLayout(actions)

    def set_date_format(self, format_key: str) -> None:
        """Atualiza somente a apresentação; o chamador converte o dia atual."""
        if format_key not in DATE_FORMATS:
            raise ValueError("Formato de data desconhecido.")
        self._format_key = format_key
        self.setInputMask(date_input_mask(format_key))
        self.setPlaceholderText(DATE_FORMATS[format_key][1])

    def _show_calendar(self) -> None:
        if not self.isEnabled():
            return
        try:
            iso_date = parse_user_date(self.text(), self._format_key)
            initial = (
                QDate.fromString(iso_date, Qt.DateFormat.ISODate)
                if iso_date else QDate.currentDate()
            )
        except ValueError:
            # Texto incompleto/errado permanece intacto até a pessoa escolher.
            initial = QDate.currentDate()
        self._calendar.setSelectedDate(initial)
        self._calendar.showSelectedDate()
        self._popup.adjustSize()
        self._popup.move(self.mapToGlobal(QPoint(0, self.height() + 2)))
        self._popup.show()
        self._popup.raise_()

    def _select_date(self, value: QDate) -> None:
        if not value.isValid():
            return
        self.setText(display_date(
            value.toString(Qt.DateFormat.ISODate), self._format_key
        ))
        self._popup.hide()
        self.dateApplied.emit()

    def _select_today(self) -> None:
        self._select_date(QDate.currentDate())

    def _clear_date(self) -> None:
        self.clear()
        self._popup.hide()
        self.dateApplied.emit()
