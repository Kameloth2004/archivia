"""Ícones vetoriais nativos em Qt, sem fontes ou arquivos externos.

Os desenhos usam coordenadas 24x24, rasterizados em alta resolução com
antialiasing; a mesma paleta é aplicada em todos os controles do ArchivIA.
"""
from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap


def icon_for(name: str, color: str = "#0b577d", size: int = 28) -> QIcon:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.scale(size / 24.0, size / 24.0)
    pen = QPen(QColor(color), 1.9, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    def line(x1, y1, x2, y2):
        painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

    def polygon(coords, fill=False):
        path = QPainterPath()
        path.moveTo(*coords[0])
        for x, y in coords[1:]:
            path.lineTo(x, y)
        path.closeSubpath()
        if fill:
            painter.fillPath(path, QColor(color))
        painter.drawPath(path)

    if name == "folder":
        path = QPainterPath()
        path.moveTo(2.5, 7)
        path.lineTo(9.5, 7)
        path.lineTo(12, 9.5)
        path.lineTo(21, 9.5)
        path.lineTo(21, 19.5)
        path.quadTo(21, 21, 19.5, 21)
        path.lineTo(4, 21)
        path.quadTo(2.5, 21, 2.5, 19.5)
        path.closeSubpath()
        painter.drawPath(path)
        line(3, 7, 3, 5)
        line(3, 5, 10, 5)
        line(10, 5, 12, 7)
    elif name == "layers":
        polygon([(12, 2.5), (21, 7.3), (12, 12.3), (3, 7.3)])
        painter.drawPolyline([QPointF(x, y) for x, y in
                              [(3, 12), (12, 17), (21, 12)]])
        painter.drawPolyline([QPointF(x, y) for x, y in
                              [(3, 16.5), (12, 21.5), (21, 16.5)]])
    elif name == "search":
        painter.drawEllipse(QRectF(3, 2, 13, 13))
        line(14, 14, 21, 21)
    elif name == "play":
        polygon([(6, 3.5), (20, 12), (6, 20.5)], fill=True)
    elif name == "stop":
        painter.setBrush(QColor(color))
        painter.drawRoundedRect(QRectF(5, 5, 14, 14), 2, 2)
    elif name == "settings":
        painter.drawEllipse(QRectF(8, 8, 8, 8))
        for x1, y1, x2, y2 in [
            (12, 1.5, 12, 5), (12, 19, 12, 22.5),
            (1.5, 12, 5, 12), (19, 12, 22.5, 12),
            (4.5, 4.5, 7, 7), (17, 17, 19.5, 19.5),
            (17, 7, 19.5, 4.5), (4.5, 19.5, 7, 17),
        ]:
            line(x1, y1, x2, y2)
    elif name == "home":
        polygon([(2.5, 11), (12, 3), (21.5, 11)])
        line(5, 10, 5, 21)
        line(19, 10, 19, 21)
        line(5, 21, 19, 21)
        line(10, 21, 10, 14)
        line(10, 14, 14, 14)
        line(14, 14, 14, 21)
    elif name == "file-text":
        path = QPainterPath()
        path.moveTo(5, 2.5)
        path.lineTo(15, 2.5)
        path.lineTo(20, 7.5)
        path.lineTo(20, 21.5)
        path.lineTo(5, 21.5)
        path.closeSubpath()
        painter.drawPath(path)
        line(15, 2.5, 15, 7.5)
        line(15, 7.5, 20, 7.5)
        line(8, 11, 17, 11)
        line(8, 14, 17, 14)
        line(8, 17, 15, 17)
    elif name == "image":
        painter.drawRoundedRect(QRectF(2.5, 3.5, 19, 17), 2, 2)
        painter.drawEllipse(QRectF(14, 6, 3.5, 3.5))
        polygon([(5, 17.5), (9.5, 12), (12, 14.5), (14, 12.5), (19, 18)])
    elif name == "video":
        painter.drawRoundedRect(QRectF(2.5, 5, 19, 14), 2, 2)
        polygon([(10, 8), (16, 12), (10, 16)], fill=True)
    elif name == "music":
        line(11, 5, 20, 3)
        line(11, 5, 11, 18)
        line(20, 3, 20, 15)
        painter.drawEllipse(QRectF(4, 16.2, 7, 4.3))
        painter.drawEllipse(QRectF(13, 13.2, 7, 4.3))
    elif name == "refresh":
        painter.drawArc(QRectF(3.5, 3.5, 17, 17), 25 * 16, 285 * 16)
        polygon([(19, 4), (21, 10), (15, 9)])
    elif name == "sparkles":
        polygon([(12, 2), (14.3, 9.5), (22, 12), (14.3, 14.3),
                 (12, 22), (9.7, 14.3), (2, 12), (9.7, 9.5)])
    elif name == "database":
        painter.drawEllipse(QRectF(3, 2.5, 18, 6))
        painter.drawArc(QRectF(3, 11, 18, 6), 180 * 16, 180 * 16)
        painter.drawArc(QRectF(3, 16, 18, 6), 180 * 16, 180 * 16)
        line(3, 5.5, 3, 19)
        line(21, 5.5, 21, 19)
    elif name == "save":
        painter.drawRoundedRect(QRectF(3, 3, 18, 18), 1.5, 1.5)
        painter.drawRect(QRectF(7, 3, 10, 6))
        painter.drawRect(QRectF(7, 14, 10, 7))
    elif name == "info":
        painter.drawEllipse(QRectF(3, 3, 18, 18))
        painter.drawPoint(QPointF(12, 8))
        line(12, 11, 12, 17)
    elif name == "chevron":
        line(5, 9, 12, 16)
        line(12, 16, 19, 9)
    else:
        painter.drawEllipse(QRectF(5, 5, 14, 14))
    painter.end()
    return QIcon(pixmap)
