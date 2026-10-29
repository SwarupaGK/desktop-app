"""Layout helpers for smaller displays and varying screen sizes."""
from qt_compat import (
    QApplication,
    QScrollArea,
    QSizePolicy,
    SCROLL_AREA_NO_FRAME,
    SCROLLBAR_AS_NEEDED,
    SIZE_EXPANDING,
    SIZE_PREFERRED,
)


def available_screen_size():
    app = QApplication.instance()
    if app and app.primaryScreen():
        geo = app.primaryScreen().availableGeometry()
        return geo.width(), geo.height()
    return 1366, 768


def is_compact_screen(width_threshold=1280, height_threshold=720):
    w, h = available_screen_size()
    return w < width_threshold or h < height_threshold


def apply_main_window_geometry(window, preferred=(1024, 720), minimum=(640, 480), margin=0.92):
    sw, sh = available_screen_size()
    pw, ph = preferred
    mw, mh = minimum
    w = min(pw, int(sw * margin))
    h = min(ph, int(sh * margin))
    window.resize(max(w, mw), max(h, mh))
    window.setMinimumSize(min(mw, sw - 40), min(mh, sh - 80))


def configure_scroll_area(scroll: QScrollArea):
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(SCROLL_AREA_NO_FRAME)
    scroll.setHorizontalScrollBarPolicy(SCROLLBAR_AS_NEEDED)
    scroll.setVerticalScrollBarPolicy(SCROLLBAR_AS_NEEDED)


def form_label_width():
    w, _ = available_screen_size()
    if w < 900:
        return 160
    if w < 1024:
        return 200
    if w < 1280:
        return 240
    return 280


def apply_label_constraints(label, min_w=None, max_w=None):
    label.setWordWrap(True)
    max_w = max_w if max_w is not None else form_label_width()
    min_w = min_w if min_w is not None else min(120, max_w)
    label.setMinimumWidth(min_w)
    label.setMaximumWidth(max_w)
    label.setSizePolicy(SIZE_PREFERRED, SIZE_PREFERRED)


def apply_field_expanding(widget, min_width=80):
    widget.setSizePolicy(SIZE_EXPANDING, QSizePolicy.Fixed)
    widget.setMinimumWidth(min_width)


def layout_margins(normal=(40, 20, 40, 40)):
    if is_compact_screen():
        return tuple(max(8, m // 2) for m in normal)
    return normal
