import os
import shutil
import sqlite3
from datetime import datetime

from qt_compat import QFileDialog, QMessageBox

from db import DB_PATH


class BackupModule:
    def __init__(self, main_app):
        self.main_app = main_app

    def backup(self):
        source_path = os.path.abspath(DB_PATH)
        if not os.path.exists(source_path):
            QMessageBox.warning(
                self.main_app,
                "Backup Error",
                "Database file was not found."
            )
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"students_backup_{timestamp}.sqlite"
        save_path, _ = QFileDialog.getSaveFileName(
            self.main_app,
            "Save Backup",
            default_name,
            "SQLite Database (*.sqlite);;All Files (*)"
        )
        if not save_path:
            return

        if not save_path.lower().endswith(".sqlite"):
            save_path += ".sqlite"

        try:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            shutil.copy2(source_path, save_path)
        except Exception as e:
            QMessageBox.critical(
                self.main_app,
                "Backup Error",
                f"Could not create backup.\n\n{e}"
            )
            return

        QMessageBox.information(
            self.main_app,
            "Backup Created",
            f"Database backup saved successfully.\n\n{save_path}"
        )

    def restore(self):
        """Restore database from a .sqlite backup file."""
        # Ask user to select a backup file
        file_path, _ = QFileDialog.getOpenFileName(
            self.main_app,
            "Select Backup File to Restore",
            "",
            "SQLite Database (*.sqlite *.db);;SQL Files (*.sql);;All Files (*)"
        )
        if not file_path:
            return

        # Check if user selected a .sql file (MySQL dump) — not supported
        if file_path.lower().endswith(".sql"):
            QMessageBox.warning(
                self.main_app,
                "Unsupported File",
                "This application uses SQLite database, not MySQL.\n\n"
                ".sql files (MySQL dumps) cannot be directly restored.\n\n"
                "Please select a .sqlite or .db backup file that was "
                "created by this application's Backup feature."
            )
            return

        # Validate the selected file is a proper SQLite database
        try:
            test_conn = sqlite3.connect(file_path)
            test_cur = test_conn.cursor()
            # Check that the 'students' table exists
            test_cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='students'"
            )
            if not test_cur.fetchone():
                test_conn.close()
                QMessageBox.warning(
                    self.main_app,
                    "Invalid Backup",
                    "The selected file does not contain a valid students database.\n\n"
                    "Please select a backup file created by this application."
                )
                return
            test_conn.close()
        except sqlite3.DatabaseError:
            QMessageBox.critical(
                self.main_app,
                "Invalid File",
                "The selected file is not a valid SQLite database.\n\n"
                "Please select a proper .sqlite backup file."
            )
            return

        # Confirm with user before overwriting
        reply = QMessageBox.question(
            self.main_app,
            "Confirm Restore",
            "⚠️ WARNING: Restoring will REPLACE all current data "
            "with the data from the backup file.\n\n"
            "A safety backup of your current database will be created first.\n\n"
            "Do you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        target_path = os.path.abspath(DB_PATH)

        # Create a safety backup of current database before overwriting
        if os.path.exists(target_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safety_backup = target_path.replace(
                ".db", f"_before_restore_{timestamp}.db"
            )
            try:
                shutil.copy2(target_path, safety_backup)
                print(f"💾 Safety backup created: {safety_backup}")
            except Exception as e:
                QMessageBox.critical(
                    self.main_app,
                    "Restore Error",
                    f"Could not create safety backup.\n\n{e}\n\n"
                    "Restore cancelled for safety."
                )
                return

        # Copy the backup file over the current database
        try:
            shutil.copy2(file_path, target_path)
        except Exception as e:
            QMessageBox.critical(
                self.main_app,
                "Restore Error",
                f"Could not restore database.\n\n{e}"
            )
            return

        # Run migration to ensure all columns exist in the restored database
        try:
            from db import init_db
            init_db()
        except Exception as e:
            print(f"[Restore] Migration after restore: {e}")

        # Reload application data
        try:
            from db import get_all_students
            self.main_app.students = get_all_students()
            # Refresh dashboard if available
            if hasattr(self.main_app, 'dashboard') and self.main_app.dashboard:
                self.main_app.dashboard.update_stats()
                # Reload view students page if it exists
                if hasattr(self.main_app.dashboard, 'view_students_page'):
                    self.main_app.dashboard.view_students_page.load_students()
        except Exception as e:
            print(f"[Restore] Error refreshing data: {e}")

        QMessageBox.information(
            self.main_app,
            "Restore Complete",
            f"Database restored successfully from:\n\n{file_path}\n\n"
            f"Total students loaded: {len(self.main_app.students)}\n\n"
            "The application data has been refreshed."
        )
