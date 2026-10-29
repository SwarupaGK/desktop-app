from __future__ import annotations

from typing import Optional

from qt_compat import *

from config import SCHOOL_NAME, resource_path
from ui_responsive import is_compact_screen
import add_student
import view_students
import certificates
import backup


class Dashboard(QWidget):
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.is_marathi = True
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(8)

        # ===== LEFT SIDEBAR =====
        sidebar = QVBoxLayout()
        sidebar.setSpacing(10)
        sidebar.setContentsMargins(4, 4, 4, 4)

        self.module_buttons = []

        modules = [
            ("➕ विद्यार्थी जोडा", "➕ Add Student"),
            ("📋 विद्यार्थी पहा", "📋 View Students"),
            ("📄 प्रमाणपत्र", "📄 Certificates"),
            ("💾 सुरक्षित प्रत", "💾 Backup"),
            ("🔄 पुनर्संचयित", "🔄 Restore"),
        ]

        colors = ["#696969", "#696969", "#696969", "#696969", "#696969"]

        for i, (marathi, english) in enumerate(modules):
            btn = QPushButton(marathi)
            btn.setFixedHeight(54)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {colors[i]};
                    color: white;
                    border-radius: 10px;
                    font-size: 17px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background: {self.darken_color(colors[i])};
                }}
            """)
            btn.clicked.connect(lambda checked, idx=i: self.show_module(idx))
            self.module_buttons.append(btn)
            sidebar.addWidget(btn)

        sidebar.addStretch()

        # Logout button at bottom of sidebar
        logout_btn = QPushButton("🚪 Logout")
        logout_btn.setFixedHeight(45)
        logout_btn.setStyleSheet("""
            QPushButton {
                background: #e74c3c;
                color: white;
                border-radius: 8px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background: #c0392b; }
        """)
        logout_btn.clicked.connect(self.logout)
        sidebar.addWidget(logout_btn)

        sidebar_widget = QWidget()
        sidebar_widget.setLayout(sidebar)
        sidebar_widget.setMinimumWidth(180 if is_compact_screen() else 200)
        sidebar_widget.setMaximumWidth(260)
        sidebar_widget.setSizePolicy(SIZE_FIXED, SIZE_EXPANDING)
        sidebar_widget.setStyleSheet("""
            QWidget {
                background: #2c3e50;
                border-radius: 15px;
            }
        """)

        # ===== RIGHT CONTENT =====
        right_layout = QVBoxLayout()
        right_layout.setSpacing(10)

        # Header (single back_btn defined here only)
        header = self.create_header()
        right_layout.addWidget(header)

        # Content Area
        self.content_area = QStackedWidget()
        right_layout.addWidget(self.content_area)

        right_widget = QWidget()
        right_widget.setLayout(right_layout)

        # ===== ADD TO MAIN =====
        main_layout.addWidget(sidebar_widget)
        main_layout.addWidget(right_widget, 1)

        self.setLayout(main_layout)

        # ===== LOAD PAGES =====
        self.load_pages()

        # Set initial school name
        self.update_school_name()

    # ===== HEADER (single definition, no duplicate back_btn) =====
    def create_header(self):
        header = QWidget()
        header.setMinimumHeight(100 if is_compact_screen() else 110)
        header.setSizePolicy(SIZE_EXPANDING, QSizePolicy.Minimum)
        header.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2c3e50, stop:1 #34495e);
                border-radius: 15px;
            }
        """)

        header_layout = QHBoxLayout()
        hm = 12 if is_compact_screen() else 15
        header_layout.setContentsMargins(16, hm, 16, hm)
        header_layout.setSpacing(15)

        # Back to Dashboard button (single definition)
        self.back_btn = QPushButton("⬅ Home")
        self.back_btn.setMinimumSize(100, 50)
        self.back_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.2);
                color: white;
                border-radius: 10px;
                font-size: 13px;
                font-weight: bold;
                border: 1px solid rgba(255,255,255,0.3);
                padding: 5px;
            }
            QPushButton:hover { background: rgba(255,255,255,0.35); }
        """)
        self.back_btn.clicked.connect(self.go_to_dashboard)

        # Logo
        logo = QLabel()
        pixmap = QPixmap(resource_path("logof.png"))
        if pixmap.isNull():
            logo.setText("🏫")
            logo.setFont(QFont("Arial", 40, QFont.Bold))
            logo.setStyleSheet("color: white; background: transparent;")
        else:
            logo_px = 80 if is_compact_screen() else 100
            logo.setPixmap(pixmap.scaled(logo_px, logo_px, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo.setFixedSize(80 if is_compact_screen() else 100, 80 if is_compact_screen() else 90)
        logo.setStyleSheet(
            "background: rgba(255,255,255,0.15); border-radius: 5px;"
            " border: 2px solid rgba(255,255,255,0.3);"
        )
        logo.setAlignment(Qt.AlignCenter)

        # School name label
        self.school_label = QLabel()
        self.school_label.setWordWrap(True)
        hdr_font = 15 if is_compact_screen() else 18
        self.school_label.setStyleSheet(f"""
            color: white;
            font-size: {hdr_font}px;
            font-weight: bold;
            background: rgba(255,255,255,0.12);
            border-radius: 12px;
            padding: 10px;
        """)

        # Language toggle
        self.lang_toggle = QPushButton("EN")
        self.lang_toggle.setMinimumSize(100, 50)
        self.lang_toggle.clicked.connect(self.toggle_language)
        self.lang_toggle.setStyleSheet("""
            QPushButton {
                background: #4682B4;
                color: white;
                border-radius: 18px;
                font-weight: bold;
                font-size: 13px;
                border: 2px solid rgba(255,255,255,0.3);
            }
            QPushButton:hover { background: #2ecc71; }
        """)

        header_layout.addWidget(self.back_btn)
        header_layout.addWidget(logo)
        header_layout.addWidget(self.school_label, 1)
        header_layout.addWidget(self.lang_toggle)
        header.setLayout(header_layout)
        return header

    # ===== PAGES =====
    def load_pages(self):
        self.welcome_page = self.create_welcome_page()
        self.add_student_page = add_student.AddStudentPage(self.main_app)
        self.view_students_page = view_students.ViewStudentsPage(self.main_app)
        self.certificate_page = certificates.CertificatePage(self.main_app)

        self.content_area.addWidget(self.welcome_page)       # index 0
        self.content_area.addWidget(self.add_student_page)   # index 1
        self.content_area.addWidget(self.view_students_page) # index 2
        self.content_area.addWidget(self.certificate_page)   # index 3

        self.content_area.setCurrentWidget(self.welcome_page)

    def create_welcome_page(self):
        page = QWidget()
        page.setStyleSheet("QWidget { background: #f0f2f5; border-radius: 12px; }")
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)

        # Logo
        logo = QLabel()
        pixmap = QPixmap(resource_path("logof.png"))
        if not pixmap.isNull():
            logo.setPixmap(pixmap.scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo.setAlignment(Qt.AlignCenter)

        # School name
        school_name = QLabel("Eklavya Gurukul School & Sports Academy")
        school_name.setAlignment(Qt.AlignCenter)
        school_name.setStyleSheet("""
            font-size: 26px;
            font-weight: bold;
            color: #2c3e50;
            background: transparent;
        """)

        # Welcome text
        welcome = QLabel("Welcome to Student Management System")
        welcome.setAlignment(Qt.AlignCenter)
        welcome.setStyleSheet("""
            font-size: 16px;
            color: #7f8c8d;
            background: transparent;
        """)

        # Stats card
        stats_card = QFrame()
        stats_card.setMinimumWidth(240)
        stats_card.setMaximumWidth(360)
        stats_card.setSizePolicy(SIZE_PREFERRED, QSizePolicy.Fixed)
        stats_card.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 15px;
                border: 1px solid #dce1e7;
            }
        """)
        stats_layout = QVBoxLayout()
        stats_layout.setContentsMargins(25, 20, 25, 20)

        self.total_students_label = QLabel(f"👨‍🎓 Total Students: {len(self.main_app.students)}")
        self.total_students_label.setAlignment(Qt.AlignCenter)
        self.total_students_label.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #2c3e50;
            background: transparent;
        """)

        stats_layout.addWidget(self.total_students_label)
        stats_card.setLayout(stats_layout)

        layout.addStretch()
        layout.addWidget(logo, alignment=Qt.AlignCenter)
        layout.addWidget(school_name)
        layout.addWidget(welcome)
        layout.addSpacing(10)
        layout.addWidget(stats_card, alignment=Qt.AlignCenter)
        layout.addStretch()

        page.setLayout(layout)
        return page

    # ===== LANGUAGE =====
    def toggle_language(self):
        self.is_marathi = not self.is_marathi
        self.update_all_ui()

    def update_all_ui(self):
        self.update_school_name()
        self.update_language_toggle()
        self.update_module_buttons()

    def update_school_name(self):
        if self.is_marathi:
            self.school_label.setText("एकलव्य गुरुकुल स्कूल & स्पोर्ट्स अकॅडमी, ईश्वरपूर")
        else:
            self.school_label.setText("Eklavya Gurukul School & Sports Academy, Ishwarpur")

    def update_language_toggle(self):
        self.lang_toggle.setText("मराठी" if self.is_marathi else "English")

    def update_module_buttons(self):
        texts = [
            ("➕ विद्यार्थी जोडा", "➕ Add Student"),
            ("📋 विद्यार्थी पहा", "📋 View Students"),
            ("📄 प्रमाणपत्र", "📄 Certificates"),
            ("💾 सुरक्षित प्रत", "💾 Backup"),
            ("🔄 पुनर्संचयित", "🔄 Restore"),
        ]
        for i, btn in enumerate(self.module_buttons):
            btn.setText(texts[i][0] if self.is_marathi else texts[i][1])

    # ===== STATS =====
    def update_stats(self):
        if hasattr(self, "total_students_label"):
            from db import get_all_students
            total = len(get_all_students())
            self.total_students_label.setText(f"👨‍🎓 Total Students: {total}")

    # ===== NAVIGATION =====
    def show_module(self, index):
        if index == 0:
            self.content_area.setCurrentWidget(self.add_student_page)
        elif index == 1:
            self.view_students_page.load_students()
            self.content_area.setCurrentWidget(self.view_students_page)
        elif index == 2:
            self.content_area.setCurrentWidget(self.certificate_page)
        elif index == 3:
            backup.BackupModule(self.main_app).backup()
        elif index == 4:
            backup.BackupModule(self.main_app).restore()

    def open_lc_module_for(self, student: Optional[dict] = None):
        self.content_area.setCurrentWidget(self.certificate_page)
        self.certificate_page.open_lc_search(student)

    def go_to_dashboard(self):
        self.update_stats()
        self.content_area.setCurrentWidget(self.welcome_page)

    def logout(self):
        self.main_app.logout()

    # ===== HELPERS =====
    def darken_color(self, color):
        mapping = {
            "#4CAF50": "#388E3C",
            "#2196F3": "#1565C0",
            "#FF9800": "#E65100",
            "#9C27B0": "#6A1B9A",
        }
        return mapping.get(color, color)
