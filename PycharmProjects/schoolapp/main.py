import sys
import os
import time
import traceback
from qt_compat import QApplication, QMainWindow, QStackedWidget, QWidget, QVBoxLayout, QMessageBox
from qt_compat import Qt, QFont, QPixmap, qt_binding_name
from db import init_db
from config import app_base_path, SCHOOL_NAME, ensure_data_file
from login import LoginPage
from dashboard import Dashboard
from ui_responsive import apply_main_window_geometry

def handle_exception(exc_type, exc_value, exc_traceback):
    """Global exception handler for .exe errors."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))

    # Log error to file

    try:
        error_log_path = os.path.join(app_base_path(), "error.log")
        with open(error_log_path, 'w', encoding='utf-8') as f:
            f.write(f"Error occurred at {time.ctime()}:\n")
            f.write(error_msg)
    except:
        pass

    # Show error dialog

    if QApplication.instance():
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Application Error")
        msg.setText("An error occurred while starting the application.")
        msg.setDetailedText(error_msg)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()

# Set global exception handler
sys.excepthook = handle_exception

def initialize_app():
    """Initialize application with error handling."""
    debug_log = []

    try:
        debug_log.append("Starting initialization...")

        # Test basic imports

        debug_log.append("Testing imports...")
        from qt_compat import QApplication, QMessageBox
        debug_log.append(f"✓ {qt_binding_name()} imports OK")
        
        # Test config functions

        debug_log.append("Testing config functions...")
        base_path = app_base_path()
        debug_log.append(f"✓ Base path: {base_path}")
        
        # Test data directory creation

        debug_log.append("Creating data directory...")
        data_dir = os.path.join(app_base_path(), "data")
        os.makedirs(data_dir, exist_ok=True)
        debug_log.append(f"✓ Data directory: {data_dir}")
        
        # Test database file

        debug_log.append("Testing database file...")
        db_file = ensure_data_file("students.db")
        debug_log.append(f"✓ Database file: {db_file}")
        
        # Test database initialization

        debug_log.append("Initializing database...")
        init_db()
        debug_log.append("✓ Database initialized")
        
        # Write debug log

        try:
            debug_path = os.path.join(app_base_path(), "debug.log")
            with open(debug_path, 'w', encoding='utf-8') as f:
                f.write("Application Debug Log\n")
                f.write("=" * 50 + "\n")
                for entry in debug_log:
                    f.write(entry + "\n")
        except:
            pass
        
        return True
        
    except Exception as e:
        error_msg = f"Failed to initialize application: {str(e)}"
        debug_log.append(f"✗ ERROR: {error_msg}")
        
        # Write debug log with error

        try:
            debug_path = os.path.join(app_base_path(), "debug.log")
            with open(debug_path, 'w', encoding='utf-8') as f:
                f.write("Application Debug Log\n")
                f.write("=" * 50 + "\n")
                for entry in debug_log:
                    f.write(entry + "\n")
                f.write(f"\nFull Error:\n{traceback.format_exc()}")
        except:
            pass
        
        print(error_msg)
        
        # Try to show error dialog

        try:
            if not QApplication.instance():
                app = QApplication(sys.argv)
            
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Initialization Error")
            msg.setText("Application failed to start properly.")
            msg.setDetailedText(f"{error_msg}\n\nDebug log saved to debug.log")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec()
        except Exception as dialog_error:
            print(f"Failed to show error dialog: {dialog_error}")
        
        return False


class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🏫 StudentHub - Eklavya Gurukul School & Sports Academy")
        apply_main_window_geometry(self, preferred=(1024, 720), minimum=(640, 480))
        self.school_name = SCHOOL_NAME
        self.students = []

        # Central widget

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        # Apply theme

        self.apply_theme()

        # Stack widget

        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        # Create pages
        self.login_page = LoginPage(self)
        self.dashboard_page = Dashboard(self)
        self.stack.addWidget(self.login_page)
        self.stack.addWidget(self.dashboard_page)

        # Load data from DB
        self.load_students_from_db()

        # Show login first
        self.stack.setCurrentWidget(self.login_page)

    def load_students_from_db(self):
        from db import get_all_students
        self.students = get_all_students()

    def switch_to_dashboard(self):
        self.load_students_from_db()
        self.dashboard_page.update_stats()
        self.stack.setCurrentWidget(self.dashboard_page)

    def logout(self):
        self.stack.setCurrentWidget(self.login_page)

    # background
    def apply_theme(self):
        theme = """
        QWidget {
            background-color: #DEEBF7;
            font-family: Arial;
        }

        QLineEdit {
            background: black;
            border: 2px solid #ddd;
            border-radius: 10px;
            padding: 12px;
            font-size: 14px;
            color: #71797E;
        }

        QLineEdit:focus {
            border-color: #151B54;
            background: #151B54;
        }

        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #4682B4, stop:1 #4682B4);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 14px 24px;
            font-weight: bold;
            font-size: 14px;
        }

        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #45a049, stop:1 #4682B4);
        }

        QPushButton:pressed {
            background: #2e7d32;
        }

        QTableWidget {
            background: black;
            gridline-color: #eee;
            border-radius: 6px;
            color: #2c3e50;
        }
        QHeaderView::section {
            background: #2c3e50;
            color: black;
            padding: 8px;
            font-weight: bold;
            border: none;
        }

        QComboBox {
            background: black;
            border: 1px solid #ccc;
            border-radius: 4px;
            padding: 6px 10px;
            color: #2c3e50;
            font-size: 14px;
        }

        QComboBox QAbstractItemView {
            background: black;
            color: #2c3e50;
            selection-background-color: #4CAF50;
            selection-color: white;
        }

        QScrollArea {
            border: none;
            background: transparent;
        }

        QMessageBox {
            color: black;
            background: white;
        }

        QMessageBox QLabel {
            color: black;
        }

        QMessageBox QPushButton {
            color: black;
            background: white;
            border: 1px solid #bfc6ce;
            border-radius: 8px;
            padding: 8px 16px;
            min-width: 90px;
        }
        
        QMessageBox QPushButton:hover {
            background: #f3f4f6;
        }
        """
        self.setStyleSheet(theme)
if __name__ == "__main__":
    # Initialize application with error handling
    if not initialize_app():
        sys.exit(1)
    
    # Continue with GUI startup
    debug_log = []
    
    try:
        debug_log.append("Starting GUI...")

        # Create QApplication

        debug_log.append("Creating QApplication...")
        app = QApplication(sys.argv)
        debug_log.append("✓ QApplication created")
        
        # Create MainApp window

        debug_log.append("Creating MainApp window...")
        window = MainApp()
        debug_log.append("✓ MainApp window created")
        
        # Show window
        debug_log.append("Showing window...")
        window.showMaximized()
        debug_log.append("✓ Window shown maximized")
        
        # Write GUI debug log
        try:
            debug_path = os.path.join(app_base_path(), "debug.log")
            with open(debug_path, 'a', encoding='utf-8') as f:
                f.write("\nGUI Debug Log\n")
                f.write("=" * 50 + "\n")
                for entry in debug_log:
                    f.write(entry + "\n")
        except:
            pass
        # Start application event loop
        debug_log.append("Starting event loop...")
        sys.exit(app.exec())

    except Exception as e:
        error_msg = f"Failed to start GUI: {str(e)}"
        debug_log.append(f"✗ GUI ERROR: {error_msg}")

        # Write GUI debug log with error
        try:
            debug_path = os.path.join(app_base_path(), "debug.log")
            with open(debug_path, 'a', encoding='utf-8') as f:
                f.write("\nGUI Debug Log\n")
                f.write("=" * 50 + "\n")
                for entry in debug_log:
                    f.write(entry + "\n")
                f.write(f"\nFull GUI Error:\n{traceback.format_exc()}")
        except:
            pass
        print(error_msg)
        # Try to show error dialog
        try:
            if not QApplication.instance():
                app = QApplication(sys.argv)
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("GUI Error")
            msg.setText("Application GUI failed to start.")
            msg.setDetailedText(f"{error_msg}\n\nDebug log saved to debug.log")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec()
        except Exception as dialog_error:
            print(f"Failed to show GUI error dialog: {dialog_error}")
        sys.exit(1)