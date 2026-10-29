"""
Qt bindings for StudentHub.

- Windows 7 .exe: build with Python 3.8 + PySide2 (set SCHOOLAPP_QT=pyside2).
- Windows 10+: development may use PySide6 (default when installed).
"""
from __future__ import annotations

import os

_QT_PREF = os.environ.get("SCHOOLAPP_QT", "").strip().lower()

if _QT_PREF == "pyside2":
    from PySide2.QtWidgets import *  # noqa: F401,F403
    from PySide2.QtCore import *  # noqa: F401,F403
    from PySide2.QtGui import *  # noqa: F401,F403
    from PySide2.QtPrintSupport import *  # noqa: F401,F403
    IS_QT6 = False
    IS_QT5 = True
    QT_API_VERSION = 5
elif _QT_PREF == "pyside6":
    from PySide6.QtWidgets import *  # noqa: F401,F403
    from PySide6.QtCore import *  # noqa: F401,F403
    from PySide6.QtGui import *  # noqa: F401,F403
    from PySide6.QtPrintSupport import *  # noqa: F401,F403
    IS_QT6 = True
    IS_QT5 = False
    QT_API_VERSION = 6
else:
    try:
        from PySide6.QtWidgets import *  # noqa: F401,F403
        from PySide6.QtCore import *  # noqa: F401,F403
        from PySide6.QtGui import *  # noqa: F401,F403
        from PySide6.QtPrintSupport import *  # noqa: F401,F403
        IS_QT6 = True
        IS_QT5 = False
        QT_API_VERSION = 6
    except ImportError:
        from PySide2.QtWidgets import *  # noqa: F401,F403
        from PySide2.QtCore import *  # noqa: F401,F403
        from PySide2.QtGui import *  # noqa: F401,F403
        from PySide2.QtPrintSupport import *  # noqa: F401,F403
        IS_QT6 = False
        IS_QT5 = True
        QT_API_VERSION = 5

if IS_QT6:
    from PySide6.QtCore import QMarginsF
    from PySide6.QtGui import QPageSize, QPageLayout
else:
    QMarginsF = None  # type: ignore
    QPageSize = None  # type: ignore
    QPageLayout = None  # type: ignore

if IS_QT6:
    ALIGN_LEFT = Qt.AlignmentFlag.AlignLeft
    ALIGN_TOP = Qt.AlignmentFlag.AlignTop
    ALIGN_CENTER = Qt.AlignmentFlag.AlignCenter
    ALIGN_LEFT_TOP = ALIGN_LEFT | ALIGN_TOP
    SCROLLBAR_AS_NEEDED = Qt.ScrollBarPolicy.ScrollBarAsNeeded
    SCROLLBAR_ALWAYS_OFF = Qt.ScrollBarPolicy.ScrollBarAlwaysOff
    SCROLL_AREA_NO_FRAME = QScrollArea.Shape.NoFrame
    SIZE_FIXED = QSizePolicy.Policy.Fixed
    SIZE_EXPANDING = QSizePolicy.Policy.Expanding
    SIZE_PREFERRED = QSizePolicy.Policy.Preferred
    FORM_EXPAND_FIELDS = QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow
    DIALOG_ACCEPTED = QDialog.DialogCode.Accepted
else:
    ALIGN_LEFT = Qt.AlignLeft
    ALIGN_TOP = Qt.AlignTop
    ALIGN_CENTER = Qt.AlignCenter
    ALIGN_LEFT_TOP = Qt.AlignLeft | Qt.AlignTop
    SCROLLBAR_AS_NEEDED = Qt.ScrollBarAsNeeded
    SCROLLBAR_ALWAYS_OFF = Qt.ScrollBarAlwaysOff
    SCROLL_AREA_NO_FRAME = QScrollArea.NoFrame
    SIZE_FIXED = QSizePolicy.Fixed
    SIZE_EXPANDING = QSizePolicy.Expanding
    SIZE_PREFERRED = QSizePolicy.Preferred
    FORM_EXPAND_FIELDS = QFormLayout.ExpandingFieldsGrow
    DIALOG_ACCEPTED = QDialog.Accepted


def configure_printer_a4(printer: QPrinter, output_path: str | None = None) -> QPrinter:
    """Configure A4 printer for LC/bonafide PDF or print preview."""
    if IS_QT6:
        printer.setPageSize(QPageSize(QPageSize.A4))
        printer.setPageMargins(QMarginsF(5, 5, 5, 5), QPageLayout.Millimeter)
    else:
        printer.setPageSize(QPrinter.A4)
        printer.setPageMargins(5, 5, 5, 5, QPrinter.Millimeter)
    if output_path:
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(output_path)
    else:
        printer.setOutputFormat(QPrinter.NativeFormat)
    return printer


def printer_document_page_size(printer: QPrinter):
    """Page size for QTextDocument layout (Qt5/Qt6)."""
    if IS_QT6:
        return printer.pageLayout().paintRect(QPageLayout.Point).size()
    return printer.pageRect().size()


def qt_binding_name() -> str:
    return "PySide6" if IS_QT6 else "PySide2"
