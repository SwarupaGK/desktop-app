# view_students.py
from qt_compat import *
from db import (get_all_students, get_students_by_academic_year,
                delete_student_by_id, get_academic_years,
                get_lc_count, increment_lc_count,
                get_lc_number_for_print,
                get_bonafide_count, increment_bonafide_count,
                promote_student)
from config import (
    DB_PATH,
    is_kindergarten_class,
    is_grade_class_1_to_12,
    next_kindergarten_or_first,
    class_prefix,
)
from certificates import build_lc_html, build_bonafide_html, show_preview, \
    validate_lc_fields, show_lc_fill_dialog, mark_student_as_passout
import sqlite3
import re

_CARD_STYLE  = "QFrame{background:white;border-radius:15px;border:1px solid #dce1e7;}"
_COMBO_STYLE = """
    QComboBox{padding:8px;font-size:13px;border:2px solid #3498db;
              border-radius:8px;background:white;color:#2c3e50;}
    QComboBox QAbstractItemView{background:white;border:2px solid #3498db;
        selection-background-color:#3498db;selection-color:white;padding:4px;}
"""
_TABLE_STYLE = """
    QTableWidget{background:white;color:#2c3e50;border-radius:10px;
                 border:1px solid #dce1e7;gridline-color:#ecf0f1;font-size:12px;}
    QTableWidget::item:selected{background:#d5f5e3;color:#2c3e50;}
    QTableWidget::item:alternate{background:#f9f9f9;}
    QHeaderView::section{background:#2c3e50;color:white;font-weight:bold;
                         font-size:11px;padding:6px 4px;border:none;
                         border-right:1px solid #3d5166;}
"""
_SEARCH_STYLE = """
    QLineEdit{background:white;color:black;border:1px solid #dce1e7;
              border-radius:8px;padding:6px 10px;font-size:13px;}
    QLineEdit::placeholder{color:#555555;}
"""
_FILTER_LABEL_STYLE = "color:black;background:transparent;font-size:13px;"

def _btn_style(color):
    return (f"QPushButton{{background:{color};color:white;border-radius:8px;"
            f"font-weight:bold;border:none;padding:0 14px;}}"
            f"QPushButton:hover{{background:#1a252f;}}")

def _is_current(s: dict) -> bool:
    status = s.get("student_status", None)
    return status is None or status == "current"


def _in_general_register(s: dict) -> bool:
    if (s.get("student_status") or "") == "passout":
        return True
    return is_grade_class_1_to_12(s.get("current_class"))


class ViewStudentsPage(QWidget):
    def __init__(self, main_app):
        super().__init__()
        self.main_app               = main_app
        self._gen_data              = []
        self._cur_data              = []
        self._kg_data               = []
        self.selected_academic_year = None

        self.stack = QStackedWidget()
        self.stack.addWidget(self._create_menu_page())        # 0
        self.stack.addWidget(self._create_year_select_page()) # 1
        self.stack.addWidget(self._create_general_page())     # 2
        self.stack.addWidget(self._create_current_page())     # 3
        self.stack.addWidget(self._create_kg_page())          # 4

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stack)
        self.setLayout(layout)

        self._load_academic_years()

    # ══════════════════════════════════════════════════════════════
    # PAGE 0 — MENU
    # ══════════════════════════════════════════════════════════════
    def _create_menu_page(self):
        page   = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        title = QLabel("📋 विद्यार्थी यादी / Student List")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color:#2c3e50;background:transparent;margin-bottom:20px;")
        layout.addWidget(title)

        card = QFrame()
        card.setStyleSheet(_CARD_STYLE)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(40, 40, 40, 40)
        cl.setSpacing(20)

        sub = QLabel("एक पर्याय निवडा / Select an option:")
        sub.setFont(QFont("Arial", 14))
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("color:#7f8c8d;background:transparent;")
        cl.addWidget(sub)

        gen_btn = QPushButton("📚  सामान्य रजिस्टर / General Register")
        gen_btn.setFixedHeight(60)
        gen_btn.setStyleSheet("""
            QPushButton{background:#123456;color:white;border-radius:12px;
                        font-size:16px;font-weight:bold;border:none;padding:15px;}
            QPushButton:hover{background:#123456;}
        """)
        gen_btn.clicked.connect(self._open_year_select)
        cl.addWidget(gen_btn)

        cur_btn = QPushButton("🎓  वर्तमान विद्यार्थी / Current Students")
        cur_btn.setFixedHeight(60)
        cur_btn.setStyleSheet("""
            QPushButton{background:#123456;color:white;border-radius:12px;
                        font-size:16px;font-weight:bold;border:none;padding:15px;}
            QPushButton:hover{background:#123456;}
        """)
        cur_btn.clicked.connect(self._open_current_students)
        cl.addWidget(cur_btn)

        kg_btn = QPushButton("🧸  बालवाडी / Kindergarten")
        kg_btn.setFixedHeight(60)
        kg_btn.setStyleSheet("""
            QPushButton{background:#6d4c41;color:white;border-radius:12px;
                        font-size:16px;font-weight:bold;border:none;padding:15px;}
            QPushButton:hover{background:#5d4037;}
        """)
        kg_btn.clicked.connect(self._open_kindergarten)
        cl.addWidget(kg_btn)

        info = QLabel(
            "📌 सामान्य रजिस्टर: इयत्ता १–१२ व पासआउट — LC निर्मिती\n"
            "🎓 वर्तमान: इयत्ता १–१२ — बोनाफाईड\n"
            "🧸 बालवाडी: Nursery, LKG, UKG — प्रोन्नती व UKG काढणे"
        )
        info.setFont(QFont("Arial", 11))
        info.setAlignment(Qt.AlignCenter)
        info.setWordWrap(True)
        info.setStyleSheet(
            "color:#555;background:#FAF9F6;border-radius:8px;padding:14px;margin-top:8px;"
        )
        cl.addWidget(info)

        layout.addWidget(card)
        page.setLayout(layout)
        return page

    # ══════════════════════════════════════════════════════════════
    # PAGE 1 — YEAR SELECTION
    # ══════════════════════════════════════════════════════════════
    def _create_year_select_page(self):
        page   = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        card = QFrame()
        card.setStyleSheet(_CARD_STYLE)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(40, 40, 40, 40)
        cl.setSpacing(20)

        title = QLabel("🗓️ शैक्षणिक वर्ष निवडा / Select Academic Year")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color:#2c3e50;background:transparent;")
        cl.addWidget(title)

        cl.addWidget(QLabel("शैक्षणिक वर्ष / Academic Year:"))

        self.year_combo = QComboBox()
        self.year_combo.setMinimumWidth(260)
        self.year_combo.setStyleSheet(_COMBO_STYLE)
        cl.addWidget(self.year_combo, alignment=Qt.AlignCenter)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(15)

        back = QPushButton("← मागे / Back")
        back.setStyleSheet(
            "QPushButton{background:#6c757d;color:white;border-radius:8px;"
            "font-size:14px;font-weight:bold;border:none;padding:10px 20px;}"
        )
        back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        btn_row.addWidget(back)

        all_btn = QPushButton("📋 सर्व विद्यार्थी / All Years")
        all_btn.setStyleSheet(
            "QPushButton{background:#123456;color:white;border-radius:8px;"
            "font-size:14px;font-weight:bold;border:none;padding:10px 20px;}"
        )
        all_btn.clicked.connect(self._open_general_all)
        btn_row.addWidget(all_btn)

        proceed = QPushButton("पुढे जा / Proceed →")
        proceed.setStyleSheet(
            "QPushButton{background:#28a745;color:white;border-radius:8px;"
            "font-size:14px;font-weight:bold;border:none;padding:10px 20px;}"
        )
        proceed.clicked.connect(self._proceed_general)
        btn_row.addWidget(proceed)

        cl.addLayout(btn_row)
        layout.addWidget(card)
        page.setLayout(layout)
        return page

    def _load_academic_years(self):
        try:
            years = get_academic_years()
            self.year_combo.clear()
            self.year_combo.addItem("Select Academic Year")
            if years:
                self.year_combo.addItems(years)
                self.year_combo.setCurrentIndex(1)
            else:
                self.year_combo.setCurrentIndex(0)
        except Exception as e:
            print(f"Error loading academic years: {e}")

    def _open_year_select(self):
        self._load_academic_years()
        self.stack.setCurrentIndex(1)

    def _open_general_all(self):
        self.selected_academic_year = None
        self._load_general_students()
        self.stack.setCurrentIndex(2)

    def _proceed_general(self):
        sel = self.year_combo.currentText()
        if not sel or sel == "Select Academic Year":
            QMessageBox.warning(self, "❌ Error", "कृपया शैक्षणिक वर्ष निवडा!")
            return
        self.selected_academic_year = sel
        self._load_general_students()
        self.stack.setCurrentIndex(2)

    def _open_current_students(self):
        self._load_current_students()
        self.stack.setCurrentIndex(3)

    def _open_kindergarten(self):
        self._load_kg_students()
        self.stack.setCurrentIndex(4)

    # ══════════════════════════════════════════════════════════════
    # PAGE 2 — GENERAL REGISTER
    # ══════════════════════════════════════════════════════════════
    def _create_general_page(self):
        page   = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)

        hdr = QHBoxLayout()
        back = QPushButton("⬅️ मागे")
        back.setMinimumSize(100, 36)
        back.setStyleSheet(_btn_style("#95a5a6"))
        back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        hdr.addWidget(back)
        hdr.addStretch()
        self.gen_title = QLabel("📚 सामान्य रजिस्टर / General Register")
        self.gen_title.setFont(QFont("Arial", 16, QFont.Bold))
        self.gen_title.setStyleSheet("color:#2c3e50;background:transparent;")
        hdr.addWidget(self.gen_title)
        hdr.addStretch()
        self.gen_count_lbl = QLabel("")
        self.gen_count_lbl.setStyleSheet(
            "color:black;background:#27ae60;border-radius:10px;"
            "padding:4px 12px;font-weight:bold;font-size:13px;"
        )
        hdr.addWidget(self.gen_count_lbl)
        ref = QPushButton("🔄")
        ref.setFixedSize(36, 36)
        ref.setStyleSheet(_btn_style("#2196F3"))
        ref.clicked.connect(self._load_general_students)
        hdr.addWidget(ref)
        layout.addLayout(hdr)

        fc = QFrame()
        fc.setStyleSheet(_CARD_STYLE)
        fl = QHBoxLayout(fc)
        fl.setContentsMargins(10, 6, 10, 6)
        fl.setSpacing(6)

        fl.addWidget(QLabel("🔍"))
        self.gen_search = QLineEdit()
        self.gen_search.setPlaceholderText("नाव, जन्मतारीख, ID ने शोधा...")
        self.gen_search.setFixedHeight(40)
        self.gen_search.setStyleSheet(_SEARCH_STYLE)
        self.gen_search.textChanged.connect(self._load_general_students)
        fl.addWidget(self.gen_search, 1)

        year_lbl = QLabel("Year:")
        year_lbl.setStyleSheet(_FILTER_LABEL_STYLE)
        fl.addWidget(year_lbl)
        self.gen_year_filter = QComboBox()
        self.gen_year_filter.setStyleSheet(_COMBO_STYLE)
        self.gen_year_filter.addItem("All Years")
        self.gen_year_filter.setStyleSheet(_COMBO_STYLE)
        self.gen_year_filter.currentTextChanged.connect(self._load_general_students)
        fl.addWidget(self.gen_year_filter)

        lc_lbl = QLabel("LC:")
        lc_lbl.setStyleSheet(_FILTER_LABEL_STYLE)
        fl.addWidget(lc_lbl)
        self.gen_lc_filter = QComboBox()
        self.gen_lc_filter.setStyleSheet(_COMBO_STYLE)
        self.gen_lc_filter.addItems(["All", "✓ LC Generated", "✗ No LC"])
        self.gen_lc_filter.setStyleSheet(_COMBO_STYLE)
        self.gen_lc_filter.currentTextChanged.connect(self._load_general_students)
        fl.addWidget(self.gen_lc_filter)

        type_lbl = QLabel("Type:")
        type_lbl.setStyleSheet(_FILTER_LABEL_STYLE)
        fl.addWidget(type_lbl)
        self.gen_type_filter = QComboBox()
        self.gen_type_filter.setStyleSheet(_COMBO_STYLE)
        self.gen_type_filter.addItems(["All", "Current", "Passout"])
        self.gen_type_filter.setStyleSheet(_COMBO_STYLE)
        self.gen_type_filter.currentTextChanged.connect(self._load_general_students)
        fl.addWidget(self.gen_type_filter)

        layout.addWidget(fc)

        self.gen_table = self._make_table('general')
        layout.addWidget(self.gen_table)

        bc = QFrame()
        bc.setStyleSheet(_CARD_STYLE)
        bl = QHBoxLayout(bc)
        bl.setContentsMargins(10, 6, 10, 6)
        bl.setSpacing(6)

        edit_btn = QPushButton("✏️ Edit")
        edit_btn.setFixedHeight(36)
        edit_btn.setStyleSheet(_btn_style("#FF9800"))
        edit_btn.clicked.connect(lambda: self._edit_student(self.gen_table, self._gen_data))
        bl.addWidget(edit_btn)

        del_btn = QPushButton("🗑️ Delete")
        del_btn.setFixedHeight(36)
        del_btn.setStyleSheet(_btn_style("#e74c3c"))
        del_btn.clicked.connect(lambda: self._delete_student(self.gen_table, self._gen_data))
        bl.addWidget(del_btn)

        bl.addStretch()
        leg = QLabel("🟠 = LC Generated  ⬜ = No LC  🔴 row = Passout")
        leg.setStyleSheet("color:#555;font-size:11px;background:transparent;")
        bl.addWidget(leg)
        layout.addWidget(bc)
        return page

    # ══════════════════════════════════════════════════════════════
    # PAGE 3 — CURRENT STUDENTS
    # ══════════════════════════════════════════════════════════════
    def _create_current_page(self):
        page   = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)

        hdr = QHBoxLayout()
        back = QPushButton("⬅️ मागे")
        back.setMinimumSize(100, 36)
        back.setStyleSheet(_btn_style("#95a5a6"))
        back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        hdr.addWidget(back)
        hdr.addStretch()
        self.cur_title = QLabel("🎓 वर्तमान विद्यार्थी / Current Students")
        self.cur_title.setFont(QFont("Arial", 16, QFont.Bold))
        self.cur_title.setStyleSheet("color:#2c3e50;background:transparent;")
        hdr.addWidget(self.cur_title)
        hdr.addStretch()
        self.cur_count_lbl = QLabel("")
        self.cur_count_lbl.setStyleSheet(
            "color:white;background:#3498db;border-radius:10px;"
            "padding:4px 12px;font-weight:bold;font-size:13px;"
        )
        hdr.addWidget(self.cur_count_lbl)
        ref = QPushButton("🔄")
        ref.setFixedSize(36, 36)
        ref.setStyleSheet(_btn_style("#2196F3"))
        ref.clicked.connect(self._load_current_students)
        hdr.addWidget(ref)
        layout.addLayout(hdr)

        fc = QFrame()
        fc.setStyleSheet(_CARD_STYLE)
        fl = QHBoxLayout(fc)
        fl.setContentsMargins(10, 6, 10, 6)
        fl.setSpacing(6)

        fl.addWidget(QLabel("🔍"))
        self.cur_search = QLineEdit()
        self.cur_search.setPlaceholderText("नाव, जन्मतारीख, ID ने शोधा...")
        self.cur_search.setFixedHeight(34)
        self.cur_search.setStyleSheet(_SEARCH_STYLE)
        self.cur_search.textChanged.connect(self._load_current_students)
        fl.addWidget(self.cur_search, 1)

        class_lbl = QLabel("Class:")
        class_lbl.setStyleSheet(_FILTER_LABEL_STYLE)
        fl.addWidget(class_lbl)
        self.cur_class_filter = QComboBox()
        self.cur_class_filter.addItems(
            ["All"] + [str(i) for i in range(1, 13)]
        )
        self.cur_class_filter.setStyleSheet(_COMBO_STYLE)
        self.cur_class_filter.currentTextChanged.connect(self._load_current_students)
        fl.addWidget(self.cur_class_filter)

        div_lbl = QLabel("Div:")
        div_lbl.setStyleSheet(_FILTER_LABEL_STYLE)
        fl.addWidget(div_lbl)
        self.cur_div_filter = QComboBox()
        self.cur_div_filter.addItems(["All","A","B","C","D"])
        self.cur_div_filter.setStyleSheet(_COMBO_STYLE)
        self.cur_div_filter.currentTextChanged.connect(self._load_current_students)
        fl.addWidget(self.cur_div_filter)

        bon_lbl = QLabel("Bonafide:")
        bon_lbl.setStyleSheet(_FILTER_LABEL_STYLE)
        fl.addWidget(bon_lbl)
        self.cur_bon_filter = QComboBox()
        self.cur_bon_filter.setStyleSheet(_COMBO_STYLE)
        self.cur_bon_filter.addItems(["All", "✓ Issued", "✗ None"])
        self.cur_bon_filter.currentTextChanged.connect(self._load_current_students)
        fl.addWidget(self.cur_bon_filter)

        layout.addWidget(fc)

        self.cur_table = self._make_table('current')
        layout.addWidget(self.cur_table)

        bc = QFrame()
        bc.setStyleSheet(_CARD_STYLE)
        bl = QHBoxLayout(bc)
        bl.setContentsMargins(10, 6, 10, 6)
        bl.setSpacing(6)

        edit_btn = QPushButton("✏️ Edit")
        edit_btn.setFixedHeight(36)
        edit_btn.setStyleSheet(_btn_style("#FF9800"))
        edit_btn.clicked.connect(lambda: self._edit_student(self.cur_table, self._cur_data))
        bl.addWidget(edit_btn)

        del_btn = QPushButton("🗑️ Delete")
        del_btn.setFixedHeight(36)
        del_btn.setStyleSheet(_btn_style("#e74c3c"))
        del_btn.clicked.connect(lambda: self._delete_student(self.cur_table, self._cur_data))
        bl.addWidget(del_btn)

        bl.addStretch()
        leg = QLabel("🟦 = Bonafide Issued  ⬜ = None yet")
        leg.setStyleSheet("color:#555;font-size:11px;background:transparent;")
        bl.addWidget(leg)
        layout.addWidget(bc)
        return page

    # ══════════════════════════════════════════════════════════════
    # PAGE 4 — KINDERGARTEN
    # ══════════════════════════════════════════════════════════════
    def _create_kg_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)

        hdr = QHBoxLayout()
        back = QPushButton("⬅️ मागे")
        back.setMinimumSize(100, 36)
        back.setStyleSheet(_btn_style("#95a5a6"))
        back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        hdr.addWidget(back)
        hdr.addStretch()
        self.kg_title = QLabel("🧸 बालवाडी / Kindergarten (Nursery, LKG, UKG)")
        self.kg_title.setFont(QFont("Arial", 16, QFont.Bold))
        self.kg_title.setStyleSheet("color:#2c3e50;background:transparent;")
        hdr.addWidget(self.kg_title)
        hdr.addStretch()
        self.kg_count_lbl = QLabel("")
        self.kg_count_lbl.setStyleSheet(
            "color:white;background:#6d4c41;border-radius:10px;"
            "padding:4px 12px;font-weight:bold;font-size:13px;"
        )
        hdr.addWidget(self.kg_count_lbl)
        ref = QPushButton("🔄")
        ref.setFixedSize(36, 36)
        ref.setStyleSheet(_btn_style("#2196F3"))
        ref.clicked.connect(self._load_kg_students)
        hdr.addWidget(ref)
        layout.addLayout(hdr)

        fc = QFrame()
        fc.setStyleSheet(_CARD_STYLE)
        fl = QHBoxLayout(fc)
        fl.setContentsMargins(10, 6, 10, 6)
        fl.setSpacing(6)
        fl.addWidget(QLabel("🔍"))
        self.kg_search = QLineEdit()
        self.kg_search.setPlaceholderText("नाव, जन्मतारीख, ID ने शोधा...")
        self.kg_search.setFixedHeight(34)
        self.kg_search.setStyleSheet(_SEARCH_STYLE)
        self.kg_search.textChanged.connect(self._load_kg_students)
        fl.addWidget(self.kg_search, 1)
        fl.addWidget(QLabel("KG:"))
        self.kg_level_filter = QComboBox()
        self.kg_level_filter.setStyleSheet(_COMBO_STYLE)
        self.kg_level_filter.addItems(["All", "Nursery", "LKG", "UKG"])
        self.kg_level_filter.currentTextChanged.connect(self._load_kg_students)
        fl.addWidget(self.kg_level_filter)
        layout.addWidget(fc)

        self.kg_table = self._make_table("kg")
        layout.addWidget(self.kg_table)

        bc = QFrame()
        bc.setStyleSheet(_CARD_STYLE)
        bl = QHBoxLayout(bc)
        bl.setContentsMargins(10, 6, 10, 6)
        bl.setSpacing(6)
        edit_btn = QPushButton("✏️ Edit")
        edit_btn.setFixedHeight(36)
        edit_btn.setStyleSheet(_btn_style("#FF9800"))
        edit_btn.clicked.connect(lambda: self._edit_student(self.kg_table, self._kg_data))
        bl.addWidget(edit_btn)
        bl.addStretch()
        note = QLabel("प्रोन्नती: तारीख = नवीन प्रवेश तारीख. UKG → इयत्ता १ सामान्य रजिस्टरमध्ये दिसेल.")
        note.setStyleSheet("color:#555;font-size:11px;background:transparent;")
        note.setWordWrap(True)
        bl.addWidget(note)
        layout.addWidget(bc)
        return page

    # ══════════════════════════════════════════════════════════════
    # TABLE FACTORY — ALL fields shown
    # ══════════════════════════════════════════════════════════════
    def _make_table(self, mode: str) -> QTableWidget:
        if mode == 'kg':
            cols = [
                ("student_id",       "Student ID"),
                ("name_mr",          "नाव / Name"),
                ("residential_status", "रहिवासी / Res."),
                ("mother_name_mr",   "Mother"),
                ("birth_date_num",   "DOB"),
                ("current_class",    "Class"),
                ("admission_date",   "Admission"),
                ("academic_year",    "Academic Year"),
                ("_kg_actions",      "Actions ▶"),
            ]
        elif mode == 'general':
            # ALL 22 student fields + LC button
            cols = [
                ("student_id",       "Student ID"),
                ("name_mr",          "नाव / Name"),
                ("residential_status", "रहिवासी / Res."),
                ("mother_name_mr",   "आईचे नाव / Mother"),
                ("aadhaar",          "Aadhaar"),
                ("pen_number",       "PEN Number"),
                ("caste",            "Caste / जात"),
                ("subcaste",         "Subcaste"),
                ("religion",         "Nationality"),
                ("birth_place",      "Birth Place"),
                ("birth_taluka",     "Taluka"),
                ("birth_dist",       "District"),
                ("birth_date_num",   "DOB (Numeric)"),
                ("birth_date_words", "DOB (Words)"),
                ("previous_school",  "Previous School"),
                ("admission_date",   "Admission Date"),
                ("current_class",    "Class"),
                ("progress",         "Progress"),
                ("behaviour",        "Behaviour"),
                ("leaving_date",     "Leaving Date"),
                ("class_at_leaving", "Class at Leaving"),
                ("leaving_reason",   "Leaving Reason"),
                ("remark",           "Remarks"),
                ("academic_year",    "Academic Year"),
                ("student_status",   "Status"),
                ("passout_year",     "Passout Year"),
                ("_lc_btn",          "Generate LC ▶"),
            ]
        else:
            # Current students — all relevant fields + action buttons
            cols = [
                ("student_id",       "Student ID"),
                ("name_mr",          "नाव / Name"),
                ("residential_status", "रहिवासी / Res."),
                ("mother_name_mr",   "आईचे नाव / Mother"),
                ("aadhaar",          "Aadhaar"),
                ("pen_number",       "PEN Number"),
                ("caste",            "Caste / जात"),
                ("subcaste",         "Subcaste"),
                ("religion",         "Nationality"),
                ("birth_place",      "Birth Place"),
                ("birth_taluka",     "Taluka"),
                ("birth_dist",       "District"),
                ("birth_date_num",   "DOB (Numeric)"),
                ("birth_date_words", "DOB (Words)"),
                ("previous_school",  "Previous School"),
                ("admission_date",   "Admission Date"),
                ("current_class",    "Class-Div"),
                ("progress",         "Progress"),
                ("behaviour",        "Behaviour"),
                ("remark",           "Remarks"),
                ("academic_year",    "Academic Year"),
                ("_promote_btn",     "Promote ▶"),
                ("_bon_btn",         "Generate Bonafide ▶"),
                ("_lc_btn",          "Generate LC ▶"),
            ]

        t = QTableWidget()
        t.setColumnCount(len(cols))
        t.setHorizontalHeaderLabels([c[1] for c in cols])
        t.setProperty("_cols", cols)

        hdr = t.horizontalHeader()
        for i, (key, _) in enumerate(cols):
            if key in ("_lc_btn", "_bon_btn", "_promote_btn", "_kg_actions"):
                hdr.setSectionResizeMode(i, QHeaderView.Fixed)
                t.setColumnWidth(i, 220 if key == "_kg_actions" else 175)
            elif key in ("student_id", "name_mr", "previous_school",
                         "birth_date_words", "class_at_leaving", "leaving_reason"):
                hdr.setSectionResizeMode(i, QHeaderView.Interactive)
                t.setColumnWidth(i, 150)
            elif key in ("mother_name_mr",):
                hdr.setSectionResizeMode(i, QHeaderView.Interactive)
                t.setColumnWidth(i, 130)
            else:
                hdr.setSectionResizeMode(i, QHeaderView.Interactive)
                t.setColumnWidth(i, 110)

        t.setSelectionBehavior(QAbstractItemView.SelectRows)
        t.setEditTriggers(QAbstractItemView.NoEditTriggers)
        t.setAlternatingRowColors(True)
        t.setWordWrap(False)
        t.verticalHeader().setDefaultSectionSize(36)
        t.setStyleSheet(_TABLE_STYLE)
        return t

    # ══════════════════════════════════════════════════════════════
    # LOAD — GENERAL REGISTER
    # ══════════════════════════════════════════════════════════════
    def _load_general_students(self):
        search   = self.gen_search.text().strip().lower()
        lc_filt  = self.gen_lc_filter.currentText()
        typ_filt = self.gen_type_filter.currentText()

        # Refresh year filter options
        years = get_academic_years()
        self.gen_year_filter.blockSignals(True)
        current_yr_sel = self.gen_year_filter.currentText()
        self.gen_year_filter.clear()
        self.gen_year_filter.addItem("All Years")
        self.gen_year_filter.addItems(years)
        idx = self.gen_year_filter.findText(current_yr_sel)
        self.gen_year_filter.setCurrentIndex(max(idx, 0))
        self.gen_year_filter.blockSignals(False)

        yr_sel = self.gen_year_filter.currentText()

        if yr_sel and yr_sel != "All Years":
            raw = get_students_by_academic_year(yr_sel)
        elif self.selected_academic_year:
            raw = get_students_by_academic_year(self.selected_academic_year)
        else:
            raw = get_all_students()

        data = []
        for s in raw:
            if not _in_general_register(s):
                continue
            lc     = get_lc_count(s["id"])
            is_cur = _is_current(s)

            if typ_filt == "Current" and not is_cur: continue
            if typ_filt == "Passout" and is_cur:     continue
            if lc_filt == "✓ LC Generated" and lc == 0: continue
            if lc_filt == "✗ No LC"         and lc > 0:  continue

            txt = (
                (s.get("name_mr") or "").lower() + " " +
                (s.get("student_id") or "").lower() + " " +
                (s.get("birth_date_num") or "").lower()
            )
            if search and search not in txt:
                continue

            data.append({**s, "_lc": lc})

        self._gen_data = data
        cols = self.gen_table.property("_cols")
        self.gen_table.setRowCount(len(data))

        for row_idx, student in enumerate(data):
            lc_count = student["_lc"]
            is_cur   = _is_current(student)
            for col_idx, (key, _) in enumerate(cols):
                if key == "_lc_btn":
                    self._set_lc_btn(self.gen_table, row_idx, col_idx, student, lc_count)
                else:
                    val  = student.get(key, "") or ""
                    item = QTableWidgetItem(str(val))
                    if not is_cur:
                        item.setBackground(QColor("#fff8e1"))
                    elif lc_count > 0:
                        item.setBackground(QColor("#fffbf0"))
                    if key == "student_status":
                        if not is_cur:
                            item.setText("✓ Passout")
                            item.setForeground(QColor("#c0392b"))
                        else:
                            item.setText("● Current")
                            item.setForeground(QColor("#27ae60"))
                    self.gen_table.setItem(row_idx, col_idx, item)

        total_reg = sum(1 for x in get_all_students() if _in_general_register(x))
        shown = len(data)
        self.gen_count_lbl.setText(f"Showing {shown} / Register total {total_reg}")
        yr_tag = f" — {yr_sel}" if yr_sel and yr_sel != "All Years" else (
            f" — {self.selected_academic_year}" if self.selected_academic_year else " — All Years"
        )
        self.gen_title.setText(f"📚 सामान्य रजिस्टर{yr_tag}")

    def _set_lc_btn(self, table, row, col, student, lc_count):
        w = QWidget()
        w.setStyleSheet("background:transparent;")
        h = QHBoxLayout(w)
        h.setContentsMargins(3, 2, 3, 2)
        color = "#27ae60" if lc_count == 0 else "#8e44ad"
        text  = "Generate LC" if lc_count == 0 else f"Dup LC ×{lc_count}"
        btn   = QPushButton(text)
        btn.setFixedHeight(28)
        btn.setStyleSheet(
            f"QPushButton{{background:{color};color:white;border-radius:5px;"
            f"font-size:11px;font-weight:bold;border:none;padding:0 6px;}}"
            f"QPushButton:hover{{background:#1a252f;}}"
        )
        s = student
        btn.clicked.connect(lambda _, st=s: self._open_lc_module_for(st))
        h.addWidget(btn)
        table.setCellWidget(row, col, w)

    # ══════════════════════════════════════════════════════════════
    # LOAD — CURRENT STUDENTS
    # ══════════════════════════════════════════════════════════════
    def _load_current_students(self):
        search   = self.cur_search.text().strip().lower()
        cls_filt = self.cur_class_filter.currentText()
        div_filt = self.cur_div_filter.currentText()
        bon_filt = self.cur_bon_filter.currentText()

        raw  = get_all_students()
        data = []

        for s in raw:
            if not _is_current(s):
                continue
            if not is_grade_class_1_to_12(s.get("current_class")):
                continue
            bon = get_bonafide_count(s["id"])
            lc  = get_lc_count(s["id"])
            full_class = s.get("current_class", "") or ""
            if cls_filt != "All" and not full_class.startswith(f"{cls_filt}-"):
                continue
            if div_filt != "All" and not full_class.endswith(f"-{div_filt}"):
                continue
            if bon_filt == "✓ Issued" and bon == 0: continue
            if bon_filt == "✗ None"   and bon > 0:  continue
            txt = (
                (s.get("name_mr") or "").lower() + " " +
                (s.get("student_id") or "").lower() + " " +
                (s.get("birth_date_num") or "").lower()
            )
            if search and search not in txt:
                continue
            data.append({**s, "_bon": bon, "_lc": lc})

        self._cur_data = data
        cols = self.cur_table.property("_cols")
        self.cur_table.setRowCount(len(data))

        for row_idx, student in enumerate(data):
            bon_count = student["_bon"]
            lc_count  = student["_lc"]
            for col_idx, (key, _) in enumerate(cols):
                if key == "_promote_btn":
                    self._set_promote_btn(self.cur_table, row_idx, col_idx, student)
                elif key == "_bon_btn":
                    self._set_bon_btn(self.cur_table, row_idx, col_idx, student, bon_count)
                elif key == "_lc_btn":
                    self._set_lc_btn(self.cur_table, row_idx, col_idx, student, lc_count)
                else:
                    val  = student.get(key, "") or ""
                    item = QTableWidgetItem(str(val))
                    if bon_count > 0:
                        item.setBackground(QColor("#e8f4fd"))
                    self.cur_table.setItem(row_idx, col_idx, item)

        total_cur = sum(
            1 for s in get_all_students()
            if _is_current(s) and is_grade_class_1_to_12(s.get("current_class"))
        )
        self.cur_count_lbl.setText(f"Showing {len(data)} / Total {total_cur}")

    def _set_bon_btn(self, table, row, col, student, bon_count):
        w = QWidget()
        w.setStyleSheet("background:transparent;")
        h = QHBoxLayout(w)
        h.setContentsMargins(3, 2, 3, 2)
        color = "#e67e22" if bon_count == 0 else "#2980b9"
        text  = "Generate Bonafide" if bon_count == 0 else f"Bonafide ×{bon_count}"
        btn   = QPushButton(text)
        btn.setFixedHeight(28)
        btn.setStyleSheet(
            f"QPushButton{{background:{color};color:white;border-radius:5px;"
            f"font-size:11px;font-weight:bold;border:none;padding:0 6px;}}"
            f"QPushButton:hover{{background:#1a252f;}}"
        )
        s = student
        btn.clicked.connect(lambda _, st=s: self._generate_bonafide_for(st))
        h.addWidget(btn)
        table.setCellWidget(row, col, w)

    def _set_promote_btn(self, table, row, col, student):
        w = QWidget()
        w.setStyleSheet("background:transparent;")
        h = QHBoxLayout(w)
        h.setContentsMargins(3, 2, 3, 2)
        
        # Check if student is in 12th grade
        full_class = (student.get("current_class", "") or "").strip()
        current_class = ""
        if "-" in full_class:
            try:
                current_class = full_class.split("-")[0]
            except:
                current_class = full_class
        
        # Only show promote button if not in 12th grade
        if current_class != "12":
            btn = QPushButton("Promote")
            btn.setFixedHeight(28)
            btn.setStyleSheet(
                "QPushButton{background:#16a085;color:white;border-radius:5px;"
                "font-size:11px;font-weight:bold;border:none;padding:0 6px;}"
                "QPushButton:hover{background:#117864;}"
            )
            s = student
            btn.clicked.connect(lambda _, st=s: self._promote_student(st))
            h.addWidget(btn)
        else:
            # Show "12th" label instead of promote button
            label = QLabel("12th")
            label.setStyleSheet("color:#e74c3c;font-weight:bold;font-size:11px;")
            h.addWidget(label)
        
        table.setCellWidget(row, col, w)

    def _next_academic_year(self, academic_year: str) -> str:
        if not academic_year or "-" not in academic_year:
            return academic_year
        try:
            start_year, end_year = academic_year.split("-", 1)
            return f"{int(start_year) + 1}-{int(end_year) + 1}"
        except ValueError:
            return academic_year

    def _open_lc_module_for(self, student: dict):
        dashboard = getattr(self.main_app, "dashboard_page", None)
        if dashboard is None:
            QMessageBox.warning(self, "Open LC Error", "Certificate module is not available.")
            return
        dashboard.open_lc_module_for(student)

    def _promote_student(self, student: dict):
        full_class = (student.get("current_class", "") or "").strip()
        if not full_class or "-" not in full_class:
            QMessageBox.warning(
                self, "Promotion Error",
                "Student class/division is invalid. Please edit the record first."
            )
            return

        current_class, division = full_class.split("-", 1)
        try:
            next_class = str(int(current_class) + 1)
        except ValueError:
            QMessageBox.warning(
                self, "Promotion Error",
                "Student class must be numeric to promote."
            )
            return

        if int(current_class) >= 12:
            QMessageBox.information(
                self, "Promotion Not Available",
                "Class 12 students cannot be promoted further."
            )
            return

        new_class = f"{next_class}-{division}"
        new_year = self._next_academic_year(student.get("academic_year", "") or "")
        name = student.get("name_mr", "") or "Student"
        message = (
            f"Promote '{name}' from {full_class} to {new_class}?\n"
            f"Academic Year: {student.get('academic_year', '') or '-'} → {new_year or '-'}"
        )
        confirm = QMessageBox.question(
            self,
            "Confirm Promotion",
            message,
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        promoted = promote_student(
            student["id"],
            new_class,
            new_year if new_year != (student.get("academic_year", "") or "") else None
        )
        if not promoted:
            QMessageBox.critical(
                self,
                "Promotion Error",
                "Student promotion could not be saved."
            )
            return

        student["current_class"] = new_class
        if new_year:
            student["academic_year"] = new_year
        QMessageBox.information(
            self,
            "Promoted",
            f"'{name}' promoted to {new_class}."
        )
        self._load_current_students()
        self._load_general_students()
        self._load_kg_students()

    def _load_kg_students(self):
        search = self.kg_search.text().strip().lower()
        lvl = self.kg_level_filter.currentText()
        raw = get_all_students()
        data = []
        for s in raw:
            if not _is_current(s):
                continue
            if not is_kindergarten_class(s.get("current_class")):
                continue
            pref = class_prefix(s.get("current_class"))
            if lvl != "All" and pref != lvl:
                continue
            txt = (
                (s.get("name_mr") or "").lower() + " " +
                (s.get("student_id") or "").lower() + " " +
                (s.get("birth_date_num") or "").lower()
            )
            if search and search not in txt:
                continue
            data.append(dict(s))

        self._kg_data = data
        cols = self.kg_table.property("_cols")
        self.kg_table.setRowCount(len(data))
        for row_idx, student in enumerate(data):
            for col_idx, (key, _) in enumerate(cols):
                if key == "_kg_actions":
                    self._set_kg_actions(self.kg_table, row_idx, col_idx, student)
                else:
                    val = student.get(key, "") or ""
                    self.kg_table.setItem(row_idx, col_idx, QTableWidgetItem(str(val)))

        total_kg = sum(
            1 for x in get_all_students()
            if _is_current(x) and is_kindergarten_class(x.get("current_class"))
        )
        self.kg_count_lbl.setText(f"Showing {len(data)} / Total KG {total_kg}")

    def _set_kg_actions(self, table, row, col, student):
        w = QWidget()
        w.setStyleSheet("background:transparent;")
        h = QHBoxLayout(w)
        h.setContentsMargins(2, 2, 2, 2)
        h.setSpacing(4)
        prom = QPushButton("Promote")
        prom.setFixedHeight(28)
        prom.setStyleSheet(
            "QPushButton{background:#16a085;color:white;border-radius:5px;"
            "font-size:11px;font-weight:bold;border:none;padding:0 8px;}"
            "QPushButton:hover{background:#117864;}"
        )
        st = student
        prom.clicked.connect(lambda _, s=st: self._promote_kg_student(s))
        h.addWidget(prom)
        if class_prefix(student.get("current_class")) == "UKG":
            dl = QPushButton("Delete")
            dl.setFixedHeight(28)
            dl.setStyleSheet(
                "QPushButton{background:#e74c3c;color:white;border-radius:5px;"
                "font-size:11px;font-weight:bold;border:none;padding:0 8px;}"
            )
            dl.clicked.connect(lambda _, s=st: self._delete_kg_student(s))
            h.addWidget(dl)
        h.addStretch()
        table.setCellWidget(row, col, w)

    def _delete_kg_student(self, student: dict):
        if class_prefix(student.get("current_class")) != "UKG":
            return
        name = student.get("name_mr", "Student")
        confirm = QMessageBox.question(
            self, "खात्री करा / Confirm Delete",
            f"UKG विद्यार्थी '{name}' हटवायचे?\nDelete this UKG student?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return
        if delete_student_by_id(student["id"]):
            self.main_app.load_students_from_db()
            if hasattr(self.main_app, "dashboard_page"):
                self.main_app.dashboard_page.update_stats()
            QMessageBox.information(self, "✅ हटवले", "विद्यार्थी नोंद काढली.")
            self._load_kg_students()
            self._load_general_students()
            self._load_current_students()

    def _promote_kg_student(self, student: dict):
        nxt = next_kindergarten_or_first(student.get("current_class"))
        if not nxt:
            QMessageBox.warning(
                self, "Promotion Error",
                "या वर्गासाठी प्रोन्नती उपलब्ध नाही.\nNo promotion path for this class.",
            )
            return
        cur_cls = (student.get("current_class", "") or "").strip()
        dlg = QDialog(self)
        dlg.setWindowTitle("प्रोन्नती तारीख / Promotion date")
        dlg.setMinimumWidth(420)
        vl = QVBoxLayout(dlg)
        vl.addWidget(QLabel(
            f"<b>{cur_cls}</b> → <b>{nxt}</b><br><br>"
            "प्रोन्नतीची तारीख नवीन <b>प्रवेश तारीख</b> म्हणून जतन होईल.<br>"
            "Promotion date will be saved as the new <b>admission date</b>."
        ))
        dt_in = QLineEdit()
        dt_in.setPlaceholderText("e.g. 01/06/2026")
        adm0 = (student.get("admission_date") or "").strip()
        if adm0:
            dt_in.setText(adm0)
        vl.addWidget(QLabel("तारीख / Date:"))
        vl.addWidget(dt_in)
        bb = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        vl.addWidget(bb)
        if dlg.exec() != DIALOG_ACCEPTED:
            return
        promo_date = dt_in.text().strip()
        if not promo_date:
            QMessageBox.warning(
                self, "Error",
                "कृपया प्रोन्नतीची तारीख भरा.\nPlease enter the promotion date.",
            )
            return

        new_year = None
        if class_prefix(nxt) == "1":
            ny = self._next_academic_year(student.get("academic_year", "") or "")
            if ny and ny != (student.get("academic_year", "") or ""):
                new_year = ny

        ok = promote_student(
            student["id"],
            nxt,
            new_year,
            promo_date,
        )
        if not ok:
            QMessageBox.critical(self, "Error", "प्रोन्नती जतन करता आली नाही.\nCould not save promotion.")
            return
        name = student.get("name_mr", "") or "Student"
        extra = ""
        if class_prefix(nxt) == "1":
            extra = "\n\nविद्यार्थी आता सामान्य रजिस्टर व वर्तमान यादीत (इयत्ता १) दिसेल."
        QMessageBox.information(
            self, "✅ प्रोन्नती / Promoted",
            f"'{name}' → {nxt}. प्रवेश तारीख: {promo_date}.{extra}",
        )
        self._load_kg_students()
        self._load_general_students()
        self._load_current_students()
        if hasattr(self.main_app, "dashboard_page"):
            self.main_app.dashboard_page.update_stats()

    # ══════════════════════════════════════════════════════════════
    # GENERATE LC  (with validation + status change)
    # ══════════════════════════════════════════════════════════════
    def _generate_lc_for(self, student: dict):
        # Step 1: validate all 16 fields
        missing = validate_lc_fields(student)
        if missing:
            updated = show_lc_fill_dialog(self, student, missing)
            if updated is None:
                return
            student = updated

        lc_count    = get_lc_count(student["id"])
        copy_number = lc_count + 1
        lc_no       = get_lc_number_for_print(student["id"])
        html        = build_lc_html(student, copy_number=copy_number, lc_no=lc_no)
        name        = student.get("name_mr", "") or ""

        show_preview(html, parent=self,
                     title=f"LC Print — Copy {copy_number} — {name}")

        confirm = QMessageBox.question(
            self, "✅ LC नोंद करा / Record LC?",
            "LC यशस्वीरित्या प्रिंट झाले का?\nWas the LC printed successfully?\n\n"
            "होय → LC नोंद होईल + विद्यार्थी Passout होईल\n"
            "Yes → Record LC + mark student as Passout.",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            new_count = increment_lc_count(student["id"])
            marked = mark_student_as_passout(
                student["id"],
                student.get("leaving_date", "") or ""
            )
            if not marked:
                QMessageBox.critical(
                    self,
                    "❌ Error",
                    "LC count was saved, but student status could not be updated to Passout."
                )
                return

            student["student_status"] = "passout"
            QMessageBox.information(
                self, "✅ नोंद झाली / Recorded",
                f"LC Copy No. {new_count} नोंदवली गेली.\n"
                f"विद्यार्थी '{name}' Passout झाला."
            )
            self._load_general_students()
            self._load_current_students()
            self._load_kg_students()

    # ══════════════════════════════════════════════════════════════
    # GENERATE BONAFIDE
    # ══════════════════════════════════════════════════════════════
    def _generate_bonafide_for(self, student: dict):
        html = build_bonafide_html(student)
        name = student.get("name_mr", "") or ""
        show_preview(html, parent=self, title=f"Bonafide Print — {name}")

        confirm = QMessageBox.question(
            self, "✅ Bonafide नोंद करा / Record?",
            "Bonafide यशस्वीरित्या प्रिंट झाले का?\n\nहोय → नोंद होईल.",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            new_count = increment_bonafide_count(student["id"])
            QMessageBox.information(
                self, "✅ नोंद झाली", f"Bonafide Copy No. {new_count} नोंदवली गेली."
            )
            self._load_current_students()
            self._load_kg_students()

    # ══════════════════════════════════════════════════════════════
    # DELETE
    # ══════════════════════════════════════════════════════════════
    def _delete_student(self, table: QTableWidget, data: list):
        row = table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "निवड नाही", "कृपया एक विद्यार्थी निवडा!")
            return
        student = data[row]
        name    = student.get("name_mr", "Student")
        confirm = QMessageBox.question(
            self, "खात्री करा / Confirm Delete",
            f"'{name}' ला हटवायचे आहे का?\nAre you sure?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            if delete_student_by_id(student["id"]):
                self.main_app.load_students_from_db()
                if hasattr(self.main_app, 'dashboard_page'):
                    self.main_app.dashboard_page.update_stats()
                QMessageBox.information(self, "✅ हटवले", "विद्यार्थी नोंद काढली.")
                self._load_general_students()
                self._load_current_students()
                self._load_kg_students()

    # ══════════════════════════════════════════════════════════════
    # EDIT
    # ══════════════════════════════════════════════════════════════
    def _edit_student(self, table: QTableWidget, data: list):
        row = table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "निवड नाही", "कृपया एक विद्यार्थी निवडा!")
            return
        self._show_edit_dialog(data[row], table)

    def _show_edit_dialog(self, data: dict, table: QTableWidget):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"📝 Edit: {data.get('name_mr', 'Student')}")
        from ui_responsive import apply_main_window_geometry, configure_scroll_area, apply_label_constraints

        apply_main_window_geometry(dialog, preferred=(860, 700), minimum=(520, 400))

        main_layout = QVBoxLayout(dialog)
        scroll = QScrollArea()
        configure_scroll_area(scroll)
        scroll.setStyleSheet("QScrollArea{border:none;}")
        container = QWidget()
        container.setStyleSheet("QWidget{background:white;border-radius:10px;}")
        form = QFormLayout(container)
        form.setFieldGrowthPolicy(FORM_EXPAND_FIELDS)
        form.setLabelAlignment(ALIGN_LEFT_TOP)
        form.setContentsMargins(20, 16, 20, 16)
        form.setSpacing(12)

        label_map = {
            "student_id":       "Student ID / विद्यार्थी आयडी",
            "aadhaar":          "Aadhaar No / आधार क्रमांक",
            "pen_number":       "PEN Number / पेन नंबर",
            "name_mr":          "Student Name / विद्यार्थ्याचे नाव",
            "mother_name_mr":   "Mother Name / आईचे नाव",
            "caste":            "Caste / जात",
            "subcaste":         "Subcaste / पोटजात",
            "religion":         "Nationality / राष्ट्रीयत्व",
            "birth_place":      "Birth Place / जन्मस्थळ",
            "birth_taluka":     "Taluka / तालुका",
            "birth_dist":       "District / जिल्हा",
            "birth_date_num":   "Birth Date (Numeric) / जन्मतारीख (अंकी)",
            "birth_date_words": "Birth Date (Words) / जन्मतारीख (अक्षरी)",
            "previous_school":  "Previous School / यापूर्वीची शाळा",
            "admission_date":   "Admission Date / प्रवेशाची तारीख",
            "current_class":    "Current Class / इयत्ता",
            "progress":         "Progress / प्रगती",
            "behaviour":        "Behaviour / वर्तणूक",
            "leaving_date":     "Leaving Date / शाळा सोडल्याची तारीख",
            "class_at_leaving": "Class at Leaving / शाळा सोडली ती इयत्ता",
            "leaving_reason":   "Leaving Reason / शाळा सोडण्याचे कारण",
            "remark":           "Remarks / शेरा",
            "student_status":   "Student Status (current / passout)",
            "passout_year":     "Passout Year / उत्तीर्ण वर्ष",
            "academic_year":    "Academic Year / शैक्षणिक वर्ष",
        }

        entries = {}
        for key, lbl_text in label_map.items():
            lbl = QLabel(lbl_text)
            apply_label_constraints(lbl)
            lbl.setStyleSheet(
                "font-weight:bold;font-size:12px;color:#2c3e50;background:transparent;"
            )
            ent = QLineEdit(str(data.get(key, "") or ""))
            ent.setFixedHeight(34)
            ent.setStyleSheet(
                "QLineEdit{padding:4px 10px;border:1px solid #ccc;border-radius:5px;"
                "color:#2c3e50;background:white;font-size:12px;}"
                "QLineEdit:focus{border:2px solid #4CAF50;}"
            )
            form.addRow(lbl, ent)
            entries[key] = ent

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        br = QHBoxLayout()
        cancel = QPushButton("रद्द करा / Cancel")
        cancel.setFixedSize(150, 42)
        cancel.setStyleSheet(
            "QPushButton{background:#7f8c8d;color:white;border-radius:8px;"
            "font-weight:bold;border:none;}"
        )
        cancel.clicked.connect(dialog.reject)
        save = QPushButton("💾 अपडेट करा / Update")
        save.setFixedSize(200, 42)
        save.setStyleSheet(
            "QPushButton{background:#27ae60;color:white;border-radius:8px;"
            "font-weight:bold;border:none;}"
        )
        br.addStretch()
        br.addWidget(cancel)
        br.addWidget(save)
        main_layout.addLayout(br)

        def _save():
            conn = sqlite3.connect(DB_PATH)
            cur  = conn.cursor()
            try:
                set_clause = ", ".join(f"{k}=?" for k in entries)
                values     = [e.text().strip() for e in entries.values()]
                values.append(data["id"])
                cur.execute(f"UPDATE students SET {set_clause} WHERE id=?", values)
                conn.commit()
                QMessageBox.information(dialog, "✅ यशस्वी", "विद्यार्थी माहिती अपडेट झाली!")
                dialog.accept()
                self._load_general_students()
                self._load_current_students()
                self._load_kg_students()
                if hasattr(self.main_app, 'dashboard_page'):
                    self.main_app.dashboard_page.update_stats()
            except Exception as e:
                QMessageBox.critical(dialog, "❌ Error", str(e))
            finally:
                conn.close()

        save.clicked.connect(_save)
        dialog.exec()

    # ══════════════════════════════════════════════════════════════
    # PUBLIC
    # ══════════════════════════════════════════════════════════════
    def load_students(self):
        self._load_academic_years()
        self.stack.setCurrentIndex(0)
