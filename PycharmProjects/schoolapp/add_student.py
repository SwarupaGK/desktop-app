from qt_compat import *
from ui_responsive import (
    configure_scroll_area,
    apply_label_constraints,
    apply_field_expanding,
    layout_margins,
    is_compact_screen,
)
from db import save_student as save_db_student, get_academic_years, add_academic_year
import re
from datetime import datetime


class AddStudentPage(QWidget):
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.selected_year = ""

        self.stack = QStackedWidget()
        self.year_page = self.create_year_page()
        self.form_page = self.create_form_page()

        self.stack.addWidget(self.year_page)
        self.stack.addWidget(self.form_page)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stack)
        self.setLayout(layout)

        self._load_academic_years()

    # =========================
    # PAGE 1 → SELECT ACADEMIC YEAR
    # =========================
    def create_year_page(self):
        page = QWidget()
        page.setStyleSheet("QWidget { background: #f0f2f5; }")
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Card
        card = QFrame()
        card.setStyleSheet("""
            QFrame { background: white; border-radius: 15px; border: 1px solid #dce1e7; }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(20)

        # Title
        title = QLabel("🎓 शैक्षणिक वर्ष निवडा / Select Academic Year")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2c3e50; background: transparent; margin-bottom: 20px;")
        card_layout.addWidget(title)

        # Academic year dropdown
        year_label = QLabel("शैक्षणिक वर्ष निवडा / Academic Year:")
        year_label.setFont(QFont("Arial", 12))
        year_label.setStyleSheet("color: #2c3e50; background: transparent; margin-bottom: 10px;")
        card_layout.addWidget(year_label)

        self.year_combo = QComboBox()
        self.year_combo.setStyleSheet("""
            QComboBox {
                padding: 12px;
                font-size: 14px;
                border: 2px solid #3498db;
                border-radius: 8px;
                background: white;
                min-width: 250px;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #3498db;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background: white;
                border: 2px solid #3498db;
                selection-background-color: #3498db;
                selection-color: white;
                padding: 5px;
            }
        """)
        self.year_combo.setMinimumWidth(250)
        card_layout.addWidget(self.year_combo, alignment=Qt.AlignCenter)

        # Admin section
        admin_section = QFrame()
        admin_section.setStyleSheet("""
            QFrame { background: #f8f9fa; border-radius: 8px; border: 1px solid #e9ecef; }
        """)
        admin_layout = QVBoxLayout(admin_section)
        admin_layout.setContentsMargins(20, 15, 20, 15)

        admin_title = QLabel("⚙️ व्यवस्थापक पर्याय / Admin Options")
        admin_title.setFont(QFont("Arial", 12, QFont.Bold))
        admin_title.setStyleSheet("color: #6c757d; background: transparent; margin-bottom: 10px;")
        admin_layout.addWidget(admin_title)

        add_year_btn = QPushButton("नवीन वर्ष जोडा / Add New Year")
        add_year_btn.setStyleSheet("""
            QPushButton { background:#6c757d; color:white; border-radius:6px;
                          font-size:12px; font-weight:bold; border:none; padding:8px 15px; }
            QPushButton:hover { background:#5a6268; }
        """)
        add_year_btn.clicked.connect(self._add_new_academic_year)
        admin_layout.addWidget(add_year_btn, alignment=Qt.AlignCenter)

        card_layout.addWidget(admin_section)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        back_btn = QPushButton("← मागे जा / Back")
        back_btn.setStyleSheet("""
            QPushButton { background:#6c757d; color:white; border-radius:8px;
                          font-size:14px; font-weight:bold; border:none; padding:10px 20px; }
            QPushButton:hover { background:#5a6268; }
        """)
        back_btn.clicked.connect(self.go_back_to_dashboard)
        button_layout.addWidget(back_btn)

        proceed_btn = QPushButton("पुढे जा / Proceed →")
        proceed_btn.setStyleSheet("""
            QPushButton { background:#28a745; color:white; border-radius:8px;
                          font-size:14px; font-weight:bold; border:none; padding:10px 20px; }
            QPushButton:hover { background:#218838; }
            QPushButton:disabled { background:#6c757d; }
        """)
        proceed_btn.clicked.connect(self.go_to_form)
        button_layout.addWidget(proceed_btn)

        card_layout.addLayout(button_layout)

        main_layout.addWidget(card)
        page.setLayout(main_layout)

        return page

    def _load_academic_years(self):
        """Load academic years into dropdown."""
        try:
            years = get_academic_years()
            self.year_combo.clear()

            if not years:
                # If no years exist, add default current year
                current_year = datetime.now().year
                default_year = f"{current_year}-{current_year + 1}"
                self.year_combo.addItem(default_year)
            else:
                self.year_combo.addItems(years)
                self.year_combo.setCurrentIndex(0)

        except Exception as e:
            print(f"Error loading academic years: {e}")
            current_year = datetime.now().year
            default_year = f"{current_year}-{current_year + 1}"
            self.year_combo.addItem(default_year)

    def _add_new_academic_year(self):
        """Add new academic year dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle("नवीन शैक्षणिक वर्ष जोडा / Add Academic Year")
        dialog.setStyleSheet("""
        QDialog {font-size:14px;}
        """)
        dialog.setFixedSize(400, 200)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)

        label = QLabel("शैक्षणिक वर्ष (YYYY-YYYY) / Academic Year:")
        label.setStyleSheet(""" 
        QLabel { color:black; font-size:14px; font-weight:bold; }
        """)
        layout.addWidget(label)

        year_input = QLineEdit()
        year_input.setPlaceholderText("e.g., 2025-2026")
        year_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 5px;
                font-size: 14px;
                background: white;
                color: black;
            }
            QLineEdit:focus {
                border-color: #3498db;
                background: white;
                color: black;
            }
        """)
        layout.addWidget(year_input)

        button_layout = QHBoxLayout()

        cancel_btn = QPushButton("रद्द करा / Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)

        add_btn = QPushButton("जोडा / Add")
        add_btn.setStyleSheet("""
            QPushButton { background:#28a745; color:white; border-radius:5px;
                          font-weight:bold; border:none; padding:8px 15px; }
            QPushButton:hover { background:#218838; }
        """)
        add_btn.clicked.connect(lambda: self._save_academic_year(year_input.text().strip(), dialog))
        button_layout.addWidget(add_btn)

        layout.addLayout(button_layout)

        dialog.exec()

    def _save_academic_year(self, year_text, dialog):
        """Save new academic year."""
        if not year_text:
            QMessageBox.warning(self, "Error", "कृपया शैक्षणिक वर्ष प्रविष्ट करा!\nPlease enter academic year!")
            return

        if not re.match(r'^\d{4}-\d{4}$', year_text):
            QMessageBox.warning(self, "Error",
                                "वर्ष YYYY-YYYY स्वरूपात असावा (उदा. 2025-2026)!\nYear must be in YYYY-YYYY format!")
            return

        start_year, end_year = map(int, year_text.split('-'))
        if end_year != start_year + 1:
            QMessageBox.warning(self, "Error",
                                "शेवटचे वर्ष सुरुवातीच्या वर्षापेक्षा फक्त 1 जास्त असावे!\nEnd year must be exactly 1 greater than start year!")
            return

        existing_years = [self.year_combo.itemText(i) for i in range(self.year_combo.count())]
        if year_text in existing_years:
            QMessageBox.warning(self, "Error",
                                "हा शैक्षणिक वर्ष आधीच अस्तित्वात आहे!\nThis academic year already exists!")
            return

        if not add_academic_year(year_text):
            QMessageBox.critical(self, "Error", "Academic year could not be saved.")
            return

        self.year_combo.addItem(year_text)
        self.year_combo.setCurrentText(year_text)

        dialog.accept()
        QMessageBox.information(self, "Success",
                                f"शैक्षणिक वर्ष {year_text} यशस्वीरित्या जोडला!\nAcademic year {year_text} added successfully!")

    def go_to_form(self):
        year = self.year_combo.currentText()

        if not year:
            QMessageBox.warning(self, "❌ Error",
                                "कृपया शैक्षणिक वर्ष निवडा!\nPlease select academic year!")
            return

        self.selected_year = year
        self.stack.setCurrentWidget(self.form_page)

    def go_back_to_dashboard(self):
        """Go back to dashboard."""
        self.main_app.show_dashboard()

    def go_back(self):
        """Go back to year selection."""
        self.stack.setCurrentWidget(self.year_page)

    # =========================
    # PAGE 2 → STUDENT FORM (with Radio Buttons)
    # =========================
    def create_form_page(self):
        page = QWidget()
        page.setStyleSheet("QWidget { background: #f0f2f5; }")
        main_layout = QVBoxLayout(page)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        configure_scroll_area(scroll)
        scroll.setStyleSheet("QScrollArea { border: none; background: #f0f2f5; }")

        container = QWidget()
        container.setStyleSheet("QWidget { background: #f0f2f5; }")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(*layout_margins((40, 20, 40, 40)))
        layout.setSpacing(10)

        # Title
        title = QLabel("विद्यार्थी माहिती / Student Details")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 18 if is_compact_screen() else 22, QFont.Bold))
        title.setStyleSheet("color: #2c3e50; margin: 15px; background: transparent;")
        layout.addWidget(title)

        # Back button
        back_btn = QPushButton("⬅️ वर्ष निवडीकडे परत / Back to Year Selection")
        back_btn.setMinimumHeight(40)
        back_btn.setMinimumWidth(200)
        back_btn.setStyleSheet("""
            QPushButton {
                background: #7f8c8d;
                color: white;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover { background: #636e72; }
        """)
        back_btn.clicked.connect(self.go_back)
        layout.addWidget(back_btn, alignment=Qt.AlignLeft)
        layout.addSpacing(10)

        # Form card
        form_card = QFrame()
        form_card.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 15px;
                border: 1px solid #dce1e7;
            }
        """)
        form_card_layout = QVBoxLayout(form_card)
        form_card_layout.setContentsMargins(30, 25, 30, 30)
        form_card_layout.setSpacing(0)

        self.entries = {}

        # ── Helper styles ──────────────────────────────────────────
        label_style = """
            font-size: 14px;
            font-weight: bold;
            color: #2c3e50;
            background: transparent;
            padding-right: 8px;
        """
        field_style = """
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #ccc;
                border-radius: 6px;
                background-color: white;
                color: #2c3e50;
                font-size: 15px;
            }
            QLineEdit:focus {
                border: 2px solid #4CAF50;
                background: #f8fff8;
            }
            QLineEdit:disabled {
                background: #ecf0f1;
                color: #7f8c8d;
            }
        """
        section_style = """
            font-size: 13px;
            font-weight: bold;
            color: white;
            background: #2c3e50;
            border-radius: 6px;
            padding: 6px 12px;
        """
        radio_style = """
            QRadioButton {
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
                spacing: 8px;
                background: transparent;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
            QRadioButton::indicator:unchecked {
                border: 2px solid #7f8c8d;
                border-radius: 9px;
                background: white;
            }
            QRadioButton::indicator:checked {
                border: 2px solid #27ae60;
                border-radius: 9px;
                background: #27ae60;
            }
        """

        def make_line(key, placeholder="", enabled=True):
            e = QLineEdit()
            e.setFixedHeight(46)
            e.setPlaceholderText(placeholder)
            e.setEnabled(enabled)
            e.setStyleSheet(field_style)
            self.entries[key] = e
            return e

        def make_label(text):
            lbl = QLabel(text)
            lbl.setWordWrap(True)
            lbl.setStyleSheet(label_style)
            return lbl

        def section_header(text):
            hdr = QLabel(text)
            hdr.setStyleSheet(section_style)
            hdr.setFixedHeight(32)
            return hdr

        def add_section(text):
            form_card_layout.addSpacing(14)
            form_card_layout.addWidget(section_header(text))
            form_card_layout.addSpacing(10)

        def add_row(label_widget, *field_widgets):
            row = QHBoxLayout()
            row.setSpacing(10)
            apply_label_constraints(label_widget)
            row.addWidget(label_widget, 0)
            for fw in field_widgets:
                apply_field_expanding(fw)
                row.addWidget(fw, 1)
            form_card_layout.addLayout(row)
            form_card_layout.addSpacing(10)

        # ══════════════════════════════════════════════════════════
        # STUDENT STATUS SECTION
        # ══════════════════════════════════════════════════════════
        add_section("🎯 विद्यार्थी स्थिती / Student Status")

        # Create a container widget for radio buttons with proper styling
        radio_container = QWidget()
        radio_container.setStyleSheet("background: transparent;")
        radio_layout = QHBoxLayout(radio_container)
        radio_layout.setSpacing(30)
        radio_layout.setContentsMargins(0, 5, 0, 5)

        self.current_radio = QRadioButton("✅ चालू विद्यार्थी / Current Student")
        self.current_radio.setChecked(True)
        self.current_radio.setStyleSheet(radio_style)
        self.current_radio.toggled.connect(self._on_status_changed)

        self.passout_radio = QRadioButton("📤 पूर्व विद्यार्थी / Passout Student")
        self.passout_radio.setStyleSheet(radio_style)
        self.passout_radio.toggled.connect(self._on_status_changed)

        radio_layout.addWidget(self.current_radio)
        radio_layout.addWidget(self.passout_radio)
        radio_layout.addStretch()

        form_card_layout.addWidget(radio_container)
        form_card_layout.addSpacing(10)

        # ══════════════════════════════════════════════════════════
        # DYNAMIC SECTION: Class/Division (for Current) OR Passout Year (for Passout)
        # ══════════════════════════════════════════════════════════
        self.dynamic_container = QWidget()
        self.dynamic_container.setStyleSheet("background: transparent;")
        self.dynamic_layout = QVBoxLayout(self.dynamic_container)
        self.dynamic_layout.setContentsMargins(0, 0, 0, 0)
        self.dynamic_layout.setSpacing(10)
        form_card_layout.addWidget(self.dynamic_container)

        # Current Student Widgets — solid panel so global theme / stacked rows never bleed through
        self.current_widget = QWidget()
        self.current_widget.setAttribute(Qt.WA_StyledBackground, True)
        self.current_widget.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-radius: 8px;
                border: 1px solid #e1e4e8;
            }
        """)
        current_layout = QVBoxLayout(self.current_widget)
        current_layout.setContentsMargins(12, 12, 12, 12)
        current_layout.setSpacing(10)

        _combo_solid_base = """
            QComboBox {
                padding: 10px 12px;
                font-size: 15px;
                border-radius: 6px;
                border: 1px solid #ccc;
                background-color: #ffffff;
                color: #2c3e50;
                min-height: 46px;
            }
            QComboBox:hover { border: 1px solid #27ae60; }
            QComboBox:on, QComboBox:focus { background-color: #ffffff; }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #2c3e50;
                outline: none;
                border: 1px solid #bdc3c7;
                selection-background-color: #3498db;
                selection-color: #ffffff;
            }
        """

        track_row = QHBoxLayout()
        track_row.setSpacing(15)
        track_lbl = QLabel("वर्ग प्रकार / Class type:")
        track_lbl.setStyleSheet(
            label_style.replace("transparent", "#ffffff").replace("padding-right: 8px", "padding: 4px 8px 4px 4px")
        )
        self.class_track_combo = QComboBox()
        self.class_track_combo.addItems([
            "बालवाडी (Nursery / LKG / UKG)",
            "इयत्ता १ ते १२ / Standard 1 to 12",
        ])
        self.class_track_combo.setStyleSheet(
            _combo_solid_base + "QComboBox { min-width: 280px; }"
        )
        track_row.addWidget(track_lbl)
        track_row.addWidget(self.class_track_combo)
        track_row.addStretch()
        current_layout.addLayout(track_row)

        self.kg_class_row = QWidget()
        self.kg_class_row.setAttribute(Qt.WA_StyledBackground, True)
        self.kg_class_row.setStyleSheet("QWidget { background-color: #ffffff; border: none; }")
        kg_row_layout = QHBoxLayout(self.kg_class_row)
        kg_row_layout.setContentsMargins(4, 6, 4, 6)
        kg_row_layout.setSpacing(15)
        kg_lbl = QLabel("बालवाडी पातळी / KG:")
        kg_lbl.setStyleSheet(label_style.replace("transparent", "#ffffff"))
        self.kg_level_combo = QComboBox()
        self.kg_level_combo.addItems(["Nursery", "LKG", "UKG"])
        self.kg_level_combo.setStyleSheet(
            _combo_solid_base + "QComboBox { min-width: 140px; min-height: 44px; }"
        )
        kg_div_lbl = QLabel("तुकडी / Division:")
        kg_div_lbl.setStyleSheet(label_style.replace("transparent", "#ffffff"))
        self.kg_div_combo = QComboBox()
        self.kg_div_combo.addItems(["A", "B", "C", "D"])
        self.kg_div_combo.setStyleSheet(
            _combo_solid_base + "QComboBox { min-width: 88px; min-height: 44px; font-size: 14px; }"
        )
        kg_row_layout.addWidget(kg_lbl)
        kg_row_layout.addWidget(self.kg_level_combo)
        kg_row_layout.addWidget(kg_div_lbl)
        kg_row_layout.addWidget(self.kg_div_combo)
        kg_row_layout.addStretch()

        self.std_class_row = QWidget()
        self.std_class_row.setAttribute(Qt.WA_StyledBackground, True)
        self.std_class_row.setStyleSheet("QWidget { background-color: #ffffff; border: none; }")
        class_div_row = QHBoxLayout(self.std_class_row)
        class_div_row.setContentsMargins(4, 6, 4, 6)
        class_div_row.setSpacing(15)

        class_label = QLabel("वर्ग / Class:")
        class_label.setStyleSheet(label_style.replace("transparent", "#ffffff"))
        self.class_combo = QComboBox()
        self.class_combo.addItems([str(i) for i in range(1, 13)])
        self.class_combo.setStyleSheet(
            _combo_solid_base + "QComboBox { min-width: 100px; }"
        )

        div_label = QLabel("तुकडी / Division:")
        div_label.setStyleSheet(label_style.replace("transparent", "#ffffff"))
        self.div_combo = QComboBox()
        self.div_combo.addItems(["A", "B", "C", "D"])
        self.div_combo.setStyleSheet(
            _combo_solid_base + "QComboBox { min-width: 88px; min-height: 44px; font-size: 14px; }"
        )

        class_div_row.addWidget(class_label)
        class_div_row.addWidget(self.class_combo)
        class_div_row.addWidget(div_label)
        class_div_row.addWidget(self.div_combo)
        class_div_row.addStretch()

        self.class_rows_stack = QStackedWidget()
        self.class_rows_stack.setStyleSheet(
            "QStackedWidget { background-color: #ffffff; border: none; }"
        )
        self.class_rows_stack.addWidget(self.kg_class_row)
        self.class_rows_stack.addWidget(self.std_class_row)
        current_layout.addWidget(self.class_rows_stack)

        self.class_track_combo.currentIndexChanged.connect(self._on_class_track_changed)
        self._on_class_track_changed()

        # Hidden field for current_class (will be set on save)
        self.entries["current_class"] = QLineEdit()
        self.entries["current_class"].setVisible(False)

        # Passout Student Widgets
        self.passout_widget = QWidget()
        self.passout_widget.setStyleSheet("background: transparent;")
        passout_layout = QHBoxLayout(self.passout_widget)
        passout_layout.setSpacing(15)

        passout_year_label = QLabel("पूर्व विद्यार्थी वर्ष / Passout Year:")
        passout_year_label.setStyleSheet(label_style)
        self.passout_year_combo = QComboBox()
        self.passout_year_combo.setEditable(True)

        # Add recent years to passout year combo
        current_year = datetime.now().year
        for year in range(current_year - 10, current_year + 5):
            self.passout_year_combo.addItem(str(year))

        self.passout_year_combo.setStyleSheet("""
            QComboBox {
                padding: 10px 12px;
                font-size: 15px;
                border-radius: 6px;
                border: 1px solid #ccc;
                background-color: white;
                min-width: 120px;
                min-height: 46px;
            }
            QComboBox:hover {
                border: 1px solid #27ae60;
            }
            QComboBox QLineEdit {
                padding: 6px 8px;
            }
        """)

        passout_layout.addWidget(passout_year_label)
        passout_layout.addWidget(self.passout_year_combo)
        passout_layout.addStretch()

        # Add both widgets to dynamic container
        self.dynamic_layout.addWidget(self.current_widget)
        self.dynamic_layout.addWidget(self.passout_widget)

        # Initially show current student widgets, hide passout widgets
        self.current_widget.setVisible(True)
        self.passout_widget.setVisible(False)

        # Store student status in entries
        self.entries["student_status"] = "current"
        self.entries["passout_year"] = ""

        form_card_layout.addSpacing(10)

        # ══════════════════════════════════════════════════════════
        # 1. विद्यार्थी ओळख / Student Identity
        # ══════════════════════════════════════════════════════════
        add_section("① विद्यार्थी ओळख / Student Identity")

        res_row = QHBoxLayout()
        res_row.setSpacing(10)
        res_lbl = make_label("रहिवासी स्थिती\nResidential Status")
        apply_label_constraints(res_lbl)
        res_row.addWidget(res_lbl, 0)

        self.residential_combo = QComboBox()
        self.residential_combo.addItems(["निवासी", "अनिवासी"])
        self.residential_combo.setStyleSheet("""
            QComboBox {
                padding: 10px 12px;
                font-size: 15px;
                border-radius: 6px;
                border: 1px solid #ccc;
                background-color: white;
                min-width: 150px;
                min-height: 46px;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox QAbstractItemView {
                background: white;
                border: 1px solid #ccc;
                selection-background-color: #3498db;
                selection-color: white;
            }
        """)
        apply_field_expanding(self.residential_combo, min_width=120)
        res_row.addWidget(self.residential_combo, 1)
        form_card_layout.addLayout(res_row)
        form_card_layout.addSpacing(10)

        add_row(make_label("विद्यार्थी आयडी क्रमांक\nStudent ID Number"),
                make_line("student_id", "e.g. EKL-2024-001"))

        add_row(make_label("आधार कार्ड क्रमांक\nAadhaar Card Number"),
                make_line("aadhaar", "12-digit Aadhaar number"))

        add_row(make_label("पेन नंबर\nPEN Number"),
                make_line("pen_number", "Enter PEN Number"))

        # ══════════════════════════════════════════════════════════
        # 2. विद्यार्थ्याचे नाव / Student Name
        # ══════════════════════════════════════════════════════════
        add_section("② विद्यार्थ्याचे नाव / Student Name")

        name_row = QHBoxLayout()
        name_row.setSpacing(10)
        name_lbl = make_label("विद्यार्थ्याचे नाव, वडिलांचे नाव, आडनाव\nFirst Name, Father's Name, Surname")
        apply_label_constraints(name_lbl)
        name_row.addWidget(name_lbl, 0)

        fname = make_line("first_name", "नाव / First Name")
        father = make_line("father_name", "वडिलांचे नाव / Father's Name")
        surname = make_line("surname", "आडनाव / Surname")
        for f in [fname, father, surname]:
            apply_field_expanding(f)
            name_row.addWidget(f, 1)
        form_card_layout.addLayout(name_row)
        form_card_layout.addSpacing(10)

        add_row(make_label("आईचे नाव\nMother's Name"),
                make_line("mother_name_mr", "आईचे पूर्ण नाव"))

        # ══════════════════════════════════════════════════════════
        # 3. जात व धर्म / Caste & Religion
        # ══════════════════════════════════════════════════════════
        add_section("③ जात व धर्म / Caste & Religion")

        caste_row = QHBoxLayout()
        caste_row.setSpacing(10)
        caste_lbl = make_label("जात व पोटजात\nCaste & Sub-caste")
        apply_label_constraints(caste_lbl)
        caste_row.addWidget(caste_lbl, 0)
        caste_f = make_line("caste", "जात / Caste")
        subcaste_f = make_line("subcaste", "पोटजात / Sub-caste")
        for f in (caste_f, subcaste_f):
            apply_field_expanding(f)
            caste_row.addWidget(f, 1)
        form_card_layout.addLayout(caste_row)
        form_card_layout.addSpacing(10)

        add_row(make_label("धर्म\nReligion"),
                make_line("religion", "e.g. Hindu / Muslim / Christian"))

        # ══════════════════════════════════════════════════════════
        # 4. जन्म माहिती / Birth Details
        # ══════════════════════════════════════════════════════════
        add_section("④ जन्म माहिती / Birth Details")

        birth_row = QHBoxLayout()
        birth_row.setSpacing(10)
        birth_lbl = make_label("जन्मस्थळ, तालुका, जिल्हा\nPlace of Birth, Taluka, District")
        apply_label_constraints(birth_lbl)
        birth_row.addWidget(birth_lbl, 0)
        bp = make_line("birth_place", "गाव / Village")
        bt = make_line("birth_taluka", "तालुका / Taluka")
        bd = make_line("birth_dist", "जिल्हा / District")
        for f in [bp, bt, bd]:
            apply_field_expanding(f)
            birth_row.addWidget(f, 1)
        form_card_layout.addLayout(birth_row)
        form_card_layout.addSpacing(10)

        dob_row = QHBoxLayout()
        dob_row.setSpacing(10)
        dob_lbl = make_label("जन्मतारीख (अंकी व अक्षरी)\nDate of Birth (Figures & Words)")
        apply_label_constraints(dob_lbl)
        dob_row.addWidget(dob_lbl, 0)
        dob_num = make_line("birth_date_num", "अंकी / Figures  e.g. 15/08/2010")
        dob_words = make_line("birth_date_words", "अक्षरी / Words  e.g. पंधरा ऑगस्ट दोन हजार दहा")
        for f in (dob_num, dob_words):
            apply_field_expanding(f)
            dob_row.addWidget(f, 1)
        form_card_layout.addLayout(dob_row)
        form_card_layout.addSpacing(10)

        # ══════════════════════════════════════════════════════════
        # 5. प्रवेश माहिती / Admission Details
        # ══════════════════════════════════════════════════════════
        add_section("⑤ प्रवेश माहिती / Admission Details")

        add_row(make_label("यापूर्वी शिकत असलेली शाळा\nPrevious School Attended"),
                make_line("previous_school", "शाळेचे नाव व ठिकाण / School name & place"))

        adm_row = QHBoxLayout()
        adm_row.setSpacing(10)
        adm_lbl = make_label("या शाळेत प्रवेश दिल्याची तारीख\nDate of Admission")
        apply_label_constraints(adm_lbl)
        adm_row.addWidget(adm_lbl, 0)
        adm_date = make_line("admission_date", "तारीख / Date  e.g. 01/06/2022")
        apply_field_expanding(adm_date)
        adm_row.addWidget(adm_date, 1)
        form_card_layout.addLayout(adm_row)
        form_card_layout.addSpacing(10)

        # ══════════════════════════════════════════════════════════
        # 6. प्रगती व वर्तणूक / Progress & Conduct
        # ══════════════════════════════════════════════════════════
        add_section("⑥ प्रगती व वर्तणूक / Progress & Conduct")

        add_row(make_label("अभ्यासातील प्रगती\nAcademic Progress"),
                make_line("progress", "e.g. चांगली / Good"))

        add_row(make_label("वर्तणूक\nConduct / Behaviour"),
                make_line("behaviour", "e.g. उत्तम / Excellent"))

        # ══════════════════════════════════════════════════════════
        # 7. शाळा सोडणे / School Leaving (Optional)
        # ══════════════════════════════════════════════════════════
        add_section("⑦ शाळा सोडणे / School Leaving Details (Optional)")

        add_row(make_label("शाळा सोडल्याची तारीख\nDate of Leaving School"),
                make_line("leaving_date", "e.g. 31/03/2024"))

        leave_cls_row = QHBoxLayout()
        leave_cls_row.setSpacing(10)
        leave_cls_lbl = make_label(
            "कोणत्या इयत्तेत शिकत होता व कितीपासून\n(अंकी व अक्षरी)\nClass Studied & Since When")
        apply_label_constraints(leave_cls_lbl)
        leave_cls_row.addWidget(leave_cls_lbl, 0)
        lcf = make_line("class_at_leaving_num", "अंकी / Figures  e.g. 7 (2022)")
        lcw = make_line("class_at_leaving_words", "अक्षरी / Words  e.g. सातवी (दोन हजार बावीस)")
        for f in (lcf, lcw):
            apply_field_expanding(f)
            leave_cls_row.addWidget(f, 1)
        form_card_layout.addLayout(leave_cls_row)
        form_card_layout.addSpacing(10)

        add_row(make_label("शाळा सोडण्याचे कारण\nReason for Leaving School"),
                make_line("leaving_reason", "कारण / Reason"))

        # ══════════════════════════════════════════════════════════
        # 8. शेरा / Remarks
        # ══════════════════════════════════════════════════════════
        add_section("⑧ शेरा / Remarks")

        add_row(make_label("शेरा\nRemarks"),
                make_line("remark", "इतर माहिती / Any other info"))

        layout.addWidget(form_card)
        layout.addSpacing(20)

        # Save button
        save_btn = QPushButton("💾 विद्यार्थी जतन करा / Save Student")
        save_btn.setMinimumHeight(48)
        save_btn.setMinimumWidth(220)
        save_btn.setMaximumWidth(420)
        save_btn.setSizePolicy(SIZE_EXPANDING, QSizePolicy.Fixed)
        save_btn.setFont(QFont("Arial", 14, QFont.Bold))
        save_btn.clicked.connect(self.save_student)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 27px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover { background-color: #388E3C; }
            QPushButton:pressed { background-color: #2e7d32; }
        """)
        layout.addWidget(save_btn, alignment=Qt.AlignCenter)
        layout.addSpacing(30)

        scroll.setWidget(container)
        main_layout.addWidget(scroll)
        return page

    def _on_class_track_changed(self):
        is_kg = self.class_track_combo.currentIndex() == 0
        self.class_rows_stack.setCurrentIndex(0 if is_kg else 1)

    def _on_status_changed(self):
        """Handle toggling between current and passout student."""
        is_current = self.current_radio.isChecked()

        # Show/hide the appropriate widgets
        self.current_widget.setVisible(is_current)
        self.passout_widget.setVisible(not is_current)

        # Update student_status in entries
        if is_current:
            self.entries["student_status"] = "current"
        else:
            self.entries["student_status"] = "passout"

    def save_student(self):
        # Get text values from all entry fields
        data = {}
        for k, v in self.entries.items():
            if hasattr(v, 'text'):
                data[k] = v.text().strip()
            else:
                data[k] = v

        # Combine first_name + father_name + surname → name_mr for DB
        full_name = " ".join(filter(None, [
            data.pop("first_name", ""),
            data.pop("father_name", ""),
            data.pop("surname", ""),
        ]))
        data["name_mr"] = full_name

        # Handle student status
        is_current = self.current_radio.isChecked()
        if is_current:
            if self.class_track_combo.currentIndex() == 0:
                kg = self.kg_level_combo.currentText().strip()
                selected_div = self.kg_div_combo.currentText().strip()
                if not kg or not selected_div:
                    QMessageBox.warning(
                        self, "❌ Error",
                        "कृपया बालवाडी पातळी आणि तुकडी निवडा!\nPlease select KG level and division!",
                    )
                    return
                data["current_class"] = f"{kg}-{selected_div}"
            else:
                selected_class = self.class_combo.currentText()
                selected_div = self.div_combo.currentText()
                if not selected_class or not selected_div:
                    QMessageBox.warning(self, "❌ Error",
                                        "कृपया चालू विद्यार्थ्यासाठी वर्ग आणि तुकडी निवडा!\nPlease select class and division for current student!")
                    return

                data["current_class"] = f"{selected_class}-{selected_div}"
            data["student_status"] = "current"
            data["passout_year"] = ""
        else:
            # Passout student - require passout year
            passout_year = self.passout_year_combo.currentText().strip()
            if not passout_year:
                QMessageBox.warning(self, "❌ Error",
                                    "कृपया पूर्व विद्यार्थ्यासाठी पासआउट वर्ष निवडा!\nPlease select passout year for passout student!")
                return

            data["current_class"] = ""  # No class for passout students
            data["student_status"] = "passout"
            data["passout_year"] = passout_year

        # Combine class_at_leaving figures + words → class_at_leaving for DB
        clf = data.pop("class_at_leaving_num", "")
        clw = data.pop("class_at_leaving_words", "")
        if clf or clw:
            data["class_at_leaving"] = f"{clf} | {clw}".strip(" |")
        else:
            data["class_at_leaving"] = ""

        # Required fields
        required = ["student_id", "name_mr"]
        missing = [f for f in required if not data.get(f)]
        if missing:
            QMessageBox.warning(self, "❌ Error",
                                "आवश्यक माहिती भरा / Required fields missing:\n" + ", ".join(missing))
            return

        # Auto-fill academic year from selection
        data["academic_year"] = self.selected_year

        # Extract residential status
        if hasattr(self, 'residential_combo'):
            data["residential_status"] = self.residential_combo.currentText().strip()

        # Set default values for optional fields if empty
        if not data.get("progress"):
            data["progress"] = "चांगली"
        if not data.get("behaviour"):
            data["behaviour"] = "चांगली"
        if not data.get("religion"):
            data["religion"] = ""
        if not data.get("remark"):
            data["remark"] = "खडाखोड नाही."

        # Remove any keys that don't match DB columns
        valid_db_fields = [
            "student_id", "aadhaar", "pen_number", "name_mr", "mother_name_mr", "surname",
            "caste", "subcaste", "religion", "birth_place", "birth_taluka",
            "birth_dist", "birth_date_num", "birth_date_words", "previous_school",
            "admission_date", "current_class", "progress", "behaviour", "leaving_date",
            "class_at_leaving", "leaving_reason", "remark", "academic_year",
            "student_status", "passout_year", "residential_status"
        ]

        filtered_data = {k: v for k, v in data.items() if k in valid_db_fields}

        if save_db_student(filtered_data):
            QMessageBox.information(self, "✅ यशस्वी / Success",
                                    f"विद्यार्थी '{filtered_data['name_mr']}' जतन झाले!\nStudent saved successfully!")
            self.main_app.load_students_from_db()

            if hasattr(self.main_app, 'dashboard_page'):
                self.main_app.dashboard_page.update_stats()

            # Clear form entries
            for entry in self.entries.values():
                if hasattr(entry, 'clear'):
                    entry.clear()

            # Reset radio button to current student
            self.current_radio.setChecked(True)

            # Reset class and division selections
            self.class_track_combo.setCurrentIndex(0)
            self._on_class_track_changed()
            self.kg_level_combo.setCurrentIndex(0)
            self.kg_div_combo.setCurrentIndex(0)
            self.class_combo.setCurrentIndex(0)
            self.div_combo.setCurrentIndex(0)
            self.passout_year_combo.setCurrentIndex(0)

            # Go back to year selection
            self.stack.setCurrentWidget(self.year_page)
        else:
            QMessageBox.critical(self, "❌ त्रुटी / Error",
                                 "विद्यार्थी जतन करताना त्रुटी आली!\nError saving student!\n\nPossible duplicate Student ID.")
