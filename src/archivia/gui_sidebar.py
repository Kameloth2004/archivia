"""Navegação vertical do ArchivIA: somente apresentação PySide6.

A navegação compartilha o QTabWidget já existente: atalhos e métodos
setCurrentIndex/setCurrentWidget continuam apontando para as mesmas telas.
"""
from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QTabWidget, QVBoxLayout


class NavigationSidebar(QFrame):
    """Coluna redimensionável com o mesmo índice das seis áreas do aplicativo."""

    def __init__(self, tabs: QTabWidget, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("archiviaSidebar")
        self.setMinimumWidth(174)
        self.setMaximumWidth(248)
        self._tabs = tabs
        self.buttons: list[QPushButton] = []

        column = QVBoxLayout(self)
        column.setContentsMargins(10, 14, 10, 12)
        column.setSpacing(6)

        heading = QLabel("ÁREAS DE TRABALHO")
        heading.setObjectName("archiviaNavHeading")
        column.addWidget(heading)

        for index in range(tabs.count()):
            button = QPushButton(tabs.tabText(index))
            button.setObjectName("archiviaNavItem")
            button.setIcon(tabs.tabIcon(index))
            button.setIconSize(QSize(20, 20))
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setMinimumHeight(42)
            button.clicked.connect(
                lambda _checked=False, i=index: tabs.setCurrentIndex(i)
            )
            column.addWidget(button)
            self.buttons.append(button)

        column.addStretch(1)
        tabs.currentChanged.connect(self._sync_current_tab)
        self._sync_current_tab(tabs.currentIndex())

    def _sync_current_tab(self, index: int) -> None:
        """Sincroniza o destaque mesmo ao navegar por atalhos de outras abas."""
        for position, button in enumerate(self.buttons):
            button.setChecked(position == index)
