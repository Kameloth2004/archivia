"""Tema visual PySide6 do ArchivIA: somente apresentação, sem lógica de arquivos."""

ARCHIVIA_STYLESHEET = """
QMainWindow, QWidget#archiviaRoot {
    background: #eaf6fc;
    color: #18314d;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 12px;
}
QLabel#archiviaTitle {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #083c66,stop:0.64 #09688d,stop:1 #11aebc);
    color: white;
    font-size: 23px;
    font-weight: 700;
    padding: 17px 18px 4px 18px;
    border-top-left-radius: 11px;
    border-top-right-radius: 11px;
}
QLabel#archiviaBrand {
    background: #ffffff;
    border: 1px solid #c3deee;
    border-radius: 11px;
    padding: 3px 12px;
}
QLabel#archiviaSubtitle {
    background: #09688d;
    color: #eafaff;
    padding: 2px 18px 13px 18px;
    border-bottom-left-radius: 11px;
    border-bottom-right-radius: 11px;
}
QGroupBox {
    background: #f9fdff;
    border: 1px solid #c3deee;
    border-radius: 12px;
    margin-top: 13px;
    padding: 13px 11px 10px 11px;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 15px;
    padding: 0 7px;
    color: #084d70;
}
QLineEdit, QComboBox, QSpinBox, QPlainTextEdit, QTableWidget, QListWidget {
    background: white;
    color: #17324b;
    border: 1px solid #a9c8da;
    border-radius: 6px;
    padding: 6px;
    selection-background-color: #247cb4;
}
QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus {
    border: 2px solid #087fba;
}
QPushButton {
    color: #174166;
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffffff,stop:1 #cfebfb);
    border: 1px solid #82b6d5;
    border-radius: 8px;
    padding: 8px 11px;
    font-weight: 600;
    min-height: 19px;
}
QPushButton:hover {
    background: #d2f2ff;
    border-color: #1288bd;
}
QPushButton:pressed { background: #a6d9ed; }
QPushButton:disabled {
    background: #e0e7ec;
    color: #7e929e;
    border-color: #cbd7df;
}
QPushButton#archiviaAnalyze, QPushButton#archiviaAdvanced {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #0aa6b0,stop:1 #065680);
    color: white;
    border: 1px solid #087e9e;
    font-size: 13px;
}
QPushButton#archiviaAnalyze:hover, QPushButton#archiviaAdvanced:hover {
    background: #087b99;
}
QPushButton#archiviaPrepare {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #10b9bd,stop:1 #065477);
    color: white;
    border: 1px solid #087e9e;
    font-size: 13px;
}
QPushButton#archiviaReview {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #348fdf,stop:1 #114f91);
    color: white;
    border: 1px solid #1e6aab;
    font-size: 13px;
}
QPushButton#archiviaMoveAll {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #36b85e,stop:1 #08743d);
    color: white;
    border: 1px solid #218548;
    font-size: 13px;
}
QPushButton#archiviaStop {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffc33b,stop:1 #d87a0b);
    color: #422b0c;
    border: 1px solid #d89926;
    font-size: 13px;
}
QPushButton#archiviaPrepare:hover { background: #087d9d; }
QPushButton#archiviaReview:hover { background: #1769b3; }
QPushButton#archiviaMoveAll:hover { background: #168b4b; }
QPushButton#archiviaStop:hover { background: #e99b22; }
QPushButton#archiviaPrepare:disabled,
QPushButton#archiviaReview:disabled,
QPushButton#archiviaMoveAll:disabled,
QPushButton#archiviaStop:disabled {
    background: #e0e7ec;
    color: #7e929e;
    border: 1px solid #cbd7df;
}
QLabel#archiviaQueueProgress {
    background: #e1f5ee;
    color: #176149;
    border: 1px solid #bde0cf;
    border-radius: 8px;
    padding: 8px;
    font-weight: 600;
}
QLabel#archiviaSafety, QLabel#archiviaStatus {
    background: #dbf3fb;
    color: #205472;
    border: 1px solid #b4ddea;
    border-radius: 7px;
    padding: 6px 10px;
}
QTabWidget::pane {
    border: 1px solid #b7d8e9;
    background: #eaf6fc;
    border-radius: 9px;
}
QTabBar::tab {
    background: #d9eafa;
    border: 1px solid #a9c8db;
    border-bottom: 0;
    padding: 9px 19px;
    margin-right: 3px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    color: #234b69;
    font-weight: 600;
}
QTabBar::tab:selected {
    background: #a8edf1;
    color: #064a66;
    border-color: #4bafc2;
}
QHeaderView::section {
    background: #dceef8;
    color: #1c506d;
    padding: 6px;
    border: 0;
    border-bottom: 1px solid #b5d1e2;
    font-weight: 600;
}
QProgressBar {
    border: 1px solid #a7cadb;
    border-radius: 5px;
    background: white;
    text-align: center;
}
QProgressBar::chunk { background: #0d9aaf; border-radius: 4px; }
/* Layout compacto aprovado: dois campos e ações quadradas na mesma linha. */
QGroupBox { margin-top: 11px; padding: 9px 9px 7px 9px; }
QGroupBox::title { left: 12px; }
QPushButton#archiviaPrepare,
QPushButton#archiviaReview,
QPushButton#archiviaMoveAll,
QPushButton#archiviaStop {
    border-radius: 13px;
    padding: 7px 6px;
    font-size: 13px;
    font-weight: 700;
}
QWidget#archiviaCategoryPanel { background: transparent; }
QPushButton#archiviaExtrasToggle {
    background: #edf8ff;
    color: #14416d;
    border: 1px solid #bad9e8;
    text-align: left;
    padding: 7px 14px;
}
QLabel#archiviaQueueProgress:empty {
    background: transparent;
    border: none;
    padding: 0;
}
"""
