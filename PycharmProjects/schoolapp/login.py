import json
import os
import sys
from qt_compat import *
from config import ADMIN_CREDENTIALS, SCHOOL_NAME, data_path, resource_path
from ui_responsive import (
    configure_scroll_area,
    is_compact_screen,
    layout_margins,
    available_screen_size,
)


CREDENTIALS_PATH = data_path("admin_credentials.json")


def get_admin_credentials():
    credentials = dict(ADMIN_CREDENTIALS)
    
    # For .exe files, prioritize bundled credentials over saved ones
    if getattr(sys, "frozen", False):
        # In .exe, use bundled credentials first
        bundled_credentials = resource_path("data/admin_credentials.json")
        if os.path.exists(bundled_credentials):
            try:
                with open(bundled_credentials, "r", encoding="utf-8") as fh:
                    saved = json.load(fh)
                if isinstance(saved, dict):
                    credentials["username"] = saved.get("username", credentials["username"])
                    credentials["password"] = saved.get("password", credentials["password"])
            except Exception:
                pass
        # Then check local saved credentials (for password changes in .exe)
        elif os.path.exists(CREDENTIALS_PATH):
            try:
                with open(CREDENTIALS_PATH, "r", encoding="utf-8") as fh:
                    saved = json.load(fh)
                if isinstance(saved, dict):
                    credentials["username"] = saved.get("username", credentials["username"])
                    credentials["password"] = saved.get("password", credentials["password"])
            except Exception:
                pass
    else:
        # In development, use saved credentials
        if os.path.exists(CREDENTIALS_PATH):
            try:
                with open(CREDENTIALS_PATH, "r", encoding="utf-8") as fh:
                    saved = json.load(fh)
                if isinstance(saved, dict):
                    credentials["username"] = saved.get("username", credentials["username"])
                    credentials["password"] = saved.get("password", credentials["password"])
            except Exception:
                pass
    
    return credentials


def save_admin_password(new_password: str) -> bool:
    credentials = get_admin_credentials()
    credentials["password"] = new_password
    os.makedirs(os.path.dirname(CREDENTIALS_PATH), exist_ok=True)
    try:
        with open(CREDENTIALS_PATH, "w", encoding="utf-8") as fh:
            json.dump(credentials, fh, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


class ResetPasswordDialog(QDialog):
    def __init__(self, parent=None, is_marathi=True):
        super().__init__(parent)
        self.is_marathi = is_marathi
        self.current_step = 0  # 0: Security Question, 1: New Password
        self.security_answer = ""
        self.new_password = ""
        self.setWindowTitle("पासवर्ड रीसेट" if is_marathi else "Reset Password")
        self.setFixedSize(450, 380)
        self.setModal(True)
        self.init_ui()

    def init_ui(self):
        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(25)
        self.main_layout.setContentsMargins(40, 40, 40, 40)

        # Title
        self.title_label = QLabel()
        self.update_title()
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont("Arial Unicode MS", 20, QFont.Bold))
        self.title_label.setStyleSheet("color: #2c3e50;")
        self.main_layout.addWidget(self.title_label)

        # Step content
        self.step_widget = QWidget()
        self.step_layout = QVBoxLayout(self.step_widget)
        self.step_layout.setSpacing(20)
        self.update_step_content()
        self.main_layout.addWidget(self.step_widget)

        # Buttons
        self.btn_layout = QHBoxLayout()
        self.next_btn = QPushButton()
        self.next_btn.clicked.connect(self.next_step)
        self.back_btn = QPushButton()
        self.back_btn.clicked.connect(self.prev_step)
        self.update_buttons()

        self.btn_layout.addWidget(self.back_btn)
        self.btn_layout.addStretch()
        self.btn_layout.addWidget(self.next_btn)
        self.main_layout.addLayout(self.btn_layout)

        self.setLayout(self.main_layout)
        self.setStyleSheet("""
            QDialog {
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.15);
            }
        """)

    def update_title(self):
        titles = [
            "🔐 सुरक्षितता प्रश्न" if self.is_marathi else "🔐 Security Question",
            "🔑 नवीन पासवर्ड" if self.is_marathi else "🔑 New Password"
        ]
        self.title_label.setText(titles[self.current_step])

    def update_step_content(self):
        # Clear previous content
        for i in reversed(range(self.step_layout.count())):
            self.step_layout.itemAt(i).widget().setParent(None)

        if self.current_step == 0:  # Security Question
            info = QLabel("स्कूल स्थापने वर्ष कोणते?" if self.is_marathi else "What year was the school established?")
            info.setWordWrap(True)
            info.setStyleSheet("color: #6c757d; font-size: 14px;")
            self.step_layout.addWidget(info)

            self.security_input = QLineEdit()
            self.security_input.setPlaceholderText("उदा: 1995" if self.is_marathi else "e.g: 1995")
            self.security_input.setMinimumHeight(50)
            self.security_input.setStyleSheet("""
                QLineEdit {
                    background-color: #f8f9fa;
                    border: 2px solid #ced4da;
                    border-radius: 10px;
                    padding: 10px 15px;
                    font-size: 16px;
                }
                QLineEdit:focus { border-color: #007bff; outline: none; }
                QLineEdit::placeholder { color: #6c757d; }
            """)
            self.step_layout.addWidget(self.security_input)

        else:  # New Password
            info = QLabel("किमान 6 अक्षरे" if self.is_marathi else "Minimum 6 characters")
            info.setAlignment(Qt.AlignCenter)
            info.setStyleSheet("color: #6c757d; font-size: 14px;")
            self.step_layout.addWidget(info)

            self.new_pass_input = QLineEdit()
            self.new_pass_input.setEchoMode(QLineEdit.Password)
            self.new_pass_input.setPlaceholderText("नवीन पासवर्ड" if self.is_marathi else "New Password")
            self.new_pass_input.setMinimumHeight(50)
            self.new_pass_input.setStyleSheet("""
                QLineEdit {
                    background-color: #f8f9fa;
                    border: 2px solid #ced4da;
                    border-radius: 10px;
                    padding: 10px 15px;
                    font-size: 16px;
                }
                QLineEdit:focus { border-color: #007bff; outline: none; }
                QLineEdit::placeholder { color: #6c757d; }
            """)
            self.step_layout.addWidget(self.new_pass_input)

            self.confirm_pass_input = QLineEdit()
            self.confirm_pass_input.setEchoMode(QLineEdit.Password)
            self.confirm_pass_input.setPlaceholderText("पासवर्ड पुन्हा टाका" if self.is_marathi else "Confirm Password")
            self.confirm_pass_input.setMinimumHeight(50)
            self.confirm_pass_input.setStyleSheet("""
                QLineEdit {
                    background-color: #f8f9fa;
                    border: 2px solid #ced4da;
                    border-radius: 10px;
                    padding: 10px 15px;
                    font-size: 16px;
                }
                QLineEdit:focus { border-color: #007bff; outline: none; }
                QLineEdit::placeholder { color: #6c757d; }
            """)
            self.step_layout.addWidget(self.confirm_pass_input)

    def update_buttons(self):
        if self.current_step == 0:
            self.next_btn.setText("पुढे" if self.is_marathi else "Next")
            self.back_btn.setText("रद्द करा" if self.is_marathi else "Cancel")
            self.back_btn.setEnabled(True)
        else:
            self.next_btn.setText("साठवा" if self.is_marathi else "Save")
            self.back_btn.setText("मागे" if self.is_marathi else "Back")
            self.back_btn.setEnabled(True)

        # Style buttons
        for btn in [self.next_btn, self.back_btn]:
            btn.setMinimumHeight(45)
            btn.setMinimumWidth(120)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #4863A0;
                    color: white;
                    border-radius: 10px;
                    font-size: 14px;
                    font-weight: bold;
                    padding: 8px 20px;
                }
                QPushButton:hover { background-color: #5a6eb8; }
                QPushButton:pressed { background-color: #3a4f80; }
                QPushButton:disabled {
                    background-color: #ccc;
                    color: #333;
                }
            """)

    def next_step(self):
        if self.current_step == 0:
            # Validate security answer (demo: accept "1995")
            self.security_answer = self.security_input.text().strip()
            if self.security_answer == "1995" or self.security_answer == "१९९५":
                self.current_step = 1
                self.update_step_content()
                self.update_title()
                self.update_buttons()
            else:
                QMessageBox.warning(self, "❌ चुकीचे उत्तर",
                                    "स्कूल स्थापने वर्ष: १९९५" if self.is_marathi else "School year: 1995")
        else:
            # Set new password
            self.new_password = self.new_pass_input.text()
            confirm = self.confirm_pass_input.text()

            if len(self.new_password) < 6:
                QMessageBox.warning(self, "❌ चुकीचे पासवर्ड",
                                    "किमान ६ अक्षरे आवश्यक" if self.is_marathi else "Minimum 6 characters required")

                return

            if self.new_password != confirm:
                QMessageBox.warning(self, "❌ पासवर्ड जुळत नाहीत",
                                    "पासवर्ड जुळवून पुन्हा टाका" if self.is_marathi else "Passwords don't match")
                return

            if not save_admin_password(self.new_password):
                QMessageBox.critical(
                    self,
                    "❌ Error",
                    "पासवर्ड जतन झाला नाही" if self.is_marathi else "Password could not be saved"
                )
                return

            QMessageBox.information(
                self, "✅ यश!",
                "पासवर्ड यशस्वीरित्या बदलला. आता नवीन पासवर्डने लॉगिन करा."
                if self.is_marathi else
                "Password changed successfully. Login now with the new password."
            )
            self.accept()

    def prev_step(self):
        if self.current_step == 0:
            self.reject()
            return
        if self.current_step > 0:
            self.current_step -= 1
            self.update_step_content()
            self.update_title()
            self.update_buttons()


class LoginPage(QWidget):
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.is_marathi = False  # Start with English
        self.init_ui()

    def init_ui(self):
        outer = QVBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        configure_scroll_area(scroll)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(24 if is_compact_screen() else 40)
        layout.setContentsMargins(*layout_margins((80, 60, 80, 60)))

        header = self.create_school_header()
        layout.addWidget(header)

        form_container = self.create_bilingual_login_form()
        layout.addWidget(form_container, alignment=Qt.AlignCenter)

        layout.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)
        self.setLayout(outer)

    def create_school_header(self):
        """Bilingual school header"""
        header = QWidget()
        header.setMinimumHeight(120 if is_compact_screen() else 140)
        header.setSizePolicy(SIZE_EXPANDING, QSizePolicy.Minimum)
        header.setStyleSheet("""
            background: #2F5D8A;
            border-radius: 15px;
            border: 2px solid rgba(255,255,255,255);
        """)

        header_layout = QHBoxLayout()
        m = 20 if is_compact_screen() else 30
        header_layout.setContentsMargins(m, m, m, m)
        header_layout.setSpacing(16 if is_compact_screen() else 30)

        logo_size = 90 if is_compact_screen() else 110
        logo_container = QWidget()
        logo_container.setFixedSize(logo_size, logo_size)

        logo_label = QLabel()
        pixmap = QPixmap(resource_path("logof.png"))
        if pixmap.isNull():
            logo_label.setText("🏫")
            logo_label.setFont(QFont("Arial", 50, QFont.Bold))
        else:
            scaled_pixmap = pixmap.scaled(
                logo_size, logo_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            logo_label.setPixmap(scaled_pixmap)
            logo_label.setStyleSheet("border-radius: 5px;")
        logo_label.setAlignment(Qt.AlignCenter)
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.addWidget(logo_label)

        # BILINGUAL SCHOOL NAME
        self.school_label = QLabel()
        self.update_school_name()

        self.school_label.setWordWrap(True)
        school_font = 22 if is_compact_screen() else 28
        self.school_label.setStyleSheet(f"""
            color: white;
            font-size: {school_font}px;
            font-weight: bold;
            line-height: 1.35;
            background: #123A63;
            border-radius: 15px;
            padding: 12px;
            border: 1px solid rgba(255,255,255,0.2);
        """)

        header_layout.addWidget(logo_container)
        header_layout.addWidget(self.school_label, 1)
        header_layout.addStretch()
        header.setLayout(header_layout)
        return header

    def create_bilingual_login_form(self):
        """Bilingual toggle login form"""
        sw, _ = available_screen_size()
        container = QWidget()
        container.setMaximumWidth(450)
        container.setMinimumWidth(min(280, int(sw * 0.85)))
        container.setSizePolicy(SIZE_EXPANDING, SIZE_PREFERRED)
        container.setStyleSheet("""
            background: white;
            border-radius: 25px;
            padding: 45px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.15);
        """)

        form_layout = QVBoxLayout()
        form_layout.setSpacing(18)

        # LANGUAGE TOGGLE BUTTON (Top)
        self.lang_toggle = QPushButton()
        self.lang_toggle.clicked.connect(self.toggle_language)
        self.update_language_toggle(self.lang_toggle)
        self.lang_toggle.setMinimumHeight(45)
        self.lang_toggle.setStyleSheet("""
            QPushButton {
                background-color: #123A63;
                color: white;
                border-radius: 20px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
                border: 2px solid rgba(255,255,255,0.2);
            }
            QPushButton:hover { background-color: #123A63; }
            QPushButton:pressed { background-color: #123A63; }
        """)
        form_layout.addWidget(self.lang_toggle)

        # Title
        self.title_label = QLabel()
        self.update_title()
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont("Arial", 20 if is_compact_screen() else 24, QFont.Bold))
        self.title_label.setMinimumHeight(36)
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet("color: #111111; background: transparent; padding: 0px;")
        form_layout.addWidget(self.title_label)

        # Username
        self.username = QLineEdit()
        self.update_username_placeholder()
        self.username.setText(get_admin_credentials()["username"])
        self.username.setMinimumHeight(55)
        self.username.setStyleSheet("""
            QLineEdit {
                background-color: #f8f9fa;
                border: 2px solid #ced4da;
                border-radius: 10px;
                padding: 8px 12px;
                font-size: 16px;
                color: #212529;
            }
            QLineEdit:focus { border-color: #007bff; outline: none; }
            QLineEdit::placeholder { color: #6c757d; font-style: italic; }
        """)
        form_layout.addWidget(self.username)

        # Password
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.update_password_placeholder()
        self.password.setMinimumHeight(55)
        self.password.setStyleSheet("""
            QLineEdit {
                background-color: #f8f9fa;
                border: 2px solid #ced4da;
                border-radius: 10px;
                padding: 8px 12px;
                font-size: 16px;
                color: #212529;
            }
            QLineEdit:focus { border-color: #007bff; outline: none; }
            QLineEdit::placeholder { color: #6c757d; font-style: italic; }
        """)
        form_layout.addWidget(self.password)

        # Login button
        self.login_btn = QPushButton()
        self.login_btn.clicked.connect(self.handle_login)
        self.update_login_button(self.login_btn)
        self.login_btn.setMinimumHeight(60)
        self.login_btn.setFont(QFont("Arial Unicode MS", 16, QFont.Bold))
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color:#123A63;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 12px;
                padding: 12px;
            }
            QPushButton:hover { background-color: #123A63; }
            QPushButton:pressed { background-color: #123A63; }
        """)
        form_layout.addWidget(self.login_btn)

        # FORGOT PASSWORD LINK
        self.forgot_link = QPushButton()
        self.forgot_link.clicked.connect(self.show_reset_password)
        self.update_forgot_password_text(self.forgot_link)
        self.forgot_link.setMinimumHeight(35)
        self.forgot_link.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: black;
                border: none;
                font-size: 14px;
                font-weight: 500;
                text-decoration: underline;
                padding: 0;
            }
            QPushButton:hover { color: #0056b3; }
        """)
        form_layout.addWidget(self.forgot_link, alignment=Qt.AlignCenter)

        container.setLayout(form_layout)
        return container

    def show_reset_password(self):
        """Show password reset dialog"""
        dialog = ResetPasswordDialog(self, self.is_marathi)
        if dialog.exec() == QDialog.Accepted:
            self.password.setText(dialog.new_password)

    def update_forgot_password_text(self, btn):
        if self.is_marathi:
            btn.setText("पासवर्ड विसरलात?")
        else:
            btn.setText("Forgot Password?")

    def toggle_language(self):
        """Switch between Marathi/English"""
        self.is_marathi = not self.is_marathi
        self.update_all_texts()

    def update_all_texts(self):
        """Update all text elements"""
        self.update_school_name()
        self.update_title()
        self.update_username_placeholder()
        self.update_password_placeholder()
        self.update_language_toggle(self.lang_toggle)
        self.update_login_button(self.login_btn)
        self.update_forgot_password_text(self.forgot_link)

    def update_school_name(self):
        if self.is_marathi:
            self.school_label.setText("एकलव्य गुरुकुल स्कूल & स्पोर्ट्स अकॅडमी")
            self.school_label.setStyleSheet("""color:white;background-color: #123A63;font-size: 35px;""")
        else:
            self.school_label.setText("Eaklavya Gurukul School & Sports Academy")
            self.school_label.setStyleSheet("""color:white;background-color: #123A63;font-size: 35px;""")

    def update_title(self):
        if self.is_marathi:
            self.title_label.setText("प्रवेश")
            self.title_label.setStyleSheet("color:#111111; background:transparent; padding:0px;")
        else:
            self.title_label.setText("Login")
            self.title_label.setStyleSheet("color:#111111; background:transparent; padding:0px;")

    def update_username_placeholder(self):
        if self.is_marathi:
            self.username.setPlaceholderText("वापरकर्ता नाव")
        else:
            self.username.setPlaceholderText("Username")

    def update_password_placeholder(self):
        if self.is_marathi:
            self.password.setPlaceholderText("पासवर्ड ")
        else:
            self.password.setPlaceholderText("Password")

    def update_language_toggle(self, btn):
        if self.is_marathi:
            btn.setText("मराठी | English")
        else:
            btn.setText("English | मराठी")

    def update_login_button(self, btn):
        if self.is_marathi:
            btn.setText("🚀 विद्यार्थी केंद्रात प्रवेश")
        else:
            btn.setText("🚀 Enter StudentHub")

    def handle_login(self):
        credentials = get_admin_credentials()
        username_ok = (self.username.text().strip() == credentials["username"])
        password_ok = (self.password.text() == credentials["password"])

        if username_ok and password_ok:
            self.main_app.switch_to_dashboard()
        else:
            if self.is_marathi:
                QMessageBox.warning(self, "❌ प्रवेश नाकारला",
                                    "चूक वापरकर्ता नाव किंवा परवलीचा शब्द!")
            else:
                QMessageBox.warning(self, "❌ Login Failed",
                                    "Invalid username or password!")
