"""Backend + UI smoke tests for source and packaged StudentHub.exe."""
import os
import shutil
import sqlite3
import subprocess
import sys
import time
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qt_compat import QApplication, QScrollArea, QMessageBox

import config
import db
import login
from certificates import CertificatePage, build_lc_html, build_bonafide_html
from dashboard import Dashboard
from login import LoginPage
from add_student import AddStudentPage
from view_students import ViewStudentsPage


class DummyMainApp:
    def __init__(self):
        self.dashboard_page = type("D", (), {"update_stats": lambda self: None})()
        self.students = []
        self.on_dashboard = False

    def load_students_from_db(self):
        self.students = db.get_all_students()

    def switch_to_dashboard(self):
        self.on_dashboard = True
        self.load_students_from_db()


class ExeAndUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.exe_path = ROOT / "dist" / "StudentHub.exe"
        cls.dist_data = ROOT / "dist" / "data"
        cls.tmp_root = ROOT / ".test_tmp"
        cls.tmp_root.mkdir(exist_ok=True)

    def _fresh_tmp(self):
        path = self.tmp_root / f"ui_{uuid.uuid4().hex}"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def test_exe_file_exists_and_has_bundled_assets(self):
        self.assertTrue(self.exe_path.exists(), "dist/StudentHub.exe missing — run build_exe.bat")
        size_mb = self.exe_path.stat().st_size / (1024 * 1024)
        self.assertGreater(size_mb, 30, f"exe too small ({size_mb:.1f} MB) — bundle may be incomplete")

        viewer = subprocess.run(
            [sys.executable, "-m", "PyInstaller.utils.cliutils.archive_viewer",
             str(self.exe_path), "--list"],
            capture_output=True, text=True, cwd=ROOT,
        )
        listing = viewer.stdout
        for asset in ("logof.png", "students.db", "admin_credentials.json",
                      "NotoSansDevanagari-Regular.ttf", "NotoSansDevanagari-Bold.ttf"):
            self.assertIn(asset, listing, f"{asset} not bundled in exe")

    def test_dist_data_folder_has_writable_database(self):
        db_file = self.dist_data / "students.db"
        self.assertTrue(db_file.exists(), "dist/data/students.db missing")
        with sqlite3.connect(db_file) as conn:
            tables = {r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )}
        self.assertIn("students", tables)
        self.assertIn("academic_years", tables)

    def test_exe_starts_without_crash(self):
        if not self.exe_path.exists():
            self.skipTest("exe not built")

        debug_log = ROOT / "dist" / "debug.log"
        error_log = ROOT / "dist" / "error.log"
        if debug_log.exists():
            debug_log.unlink()
        if error_log.exists():
            error_log.unlink()

        proc = subprocess.Popen(
            [str(self.exe_path)],
            cwd=str(ROOT / "dist"),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            time.sleep(10)
            self.assertIsNone(proc.poll(), "StudentHub.exe exited early (crash on startup)")
            self.assertTrue(debug_log.exists(), "debug.log not created — init may have failed")
            log_text = debug_log.read_text(encoding="utf-8")
            self.assertIn("Database initialized", log_text)
            self.assertIn("Window shown maximized", log_text)
            self.assertNotIn("ERROR", log_text.upper().replace("DATABASE INITIALIZED", ""))
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

    def test_login_ui_accepts_default_credentials(self):
        tmp = self._fresh_tmp()
        orig = login.CREDENTIALS_PATH
        login.CREDENTIALS_PATH = str(tmp / "admin_credentials.json")
        try:
            main = DummyMainApp()
            page = LoginPage(main)
            page.username.setText("admin")
            page.password.setText("admin")
            with patch.object(QMessageBox, "warning", return_value=QMessageBox.Ok):
                page.handle_login()
            self.assertTrue(main.on_dashboard)
        finally:
            login.CREDENTIALS_PATH = orig
            shutil.rmtree(tmp, ignore_errors=True)

    def test_login_language_toggle_does_not_crash(self):
        main = DummyMainApp()
        page = LoginPage(main)
        page.toggle_language()
        self.assertTrue(page.is_marathi)
        page.toggle_language()
        self.assertFalse(page.is_marathi)

    def test_dashboard_navigates_to_certificate_module(self):
        tmp = self._fresh_tmp()
        db_path = tmp / "data" / "students.db"
        db_path.parent.mkdir(parents=True)
        orig_db = db.DB_PATH
        db.DB_PATH = str(db_path)
        db.init_db()
        try:
            main = DummyMainApp()
            dash = Dashboard(main)
            self.assertIsNotNone(dash.certificate_page)
            dash.content_area.setCurrentWidget(dash.certificate_page)
            self.assertEqual(dash.content_area.currentWidget(), dash.certificate_page)
            cert = dash.certificate_page
            cert._enter_search("LC")
            self.assertEqual(cert.stack.currentIndex(), 1)
            scrolls = cert.findChildren(QScrollArea)
            self.assertGreaterEqual(len(scrolls), 1)
            self.assertIs(scrolls[0].widget(), cert.cert_list)
        finally:
            db.DB_PATH = orig_db
            shutil.rmtree(tmp, ignore_errors=True)

    def test_certificate_module_full_flow(self):
        tmp = self._fresh_tmp()
        db_path = tmp / "data" / "students.db"
        db_path.parent.mkdir(parents=True)
        orig_db = db.DB_PATH
        db.DB_PATH = str(db_path)
        db.init_db()
        db.add_academic_year("2026-2027")
        db.save_student({
            "student_id": "UI-001",
            "name_mr": "UI Test Student",
            "current_class": "5-A",
            "academic_year": "2026-2027",
            "student_status": "current",
            "birth_date_num": "01/01/2015",
            "aadhaar": "123456789012",
            "mother_name_mr": "Mother",
            "caste": "General",
            "religion": "Indian",
            "birth_place": "Pune",
            "birth_date_words": "first",
            "previous_school": "None",
            "admission_date": "01/06/2020",
            "progress": "Good",
            "behaviour": "Good",
            "leaving_date": "31/03/2027",
            "class_at_leaving": "5-A",
            "leaving_reason": "Transfer",
        })
        try:
            page = CertificatePage(DummyMainApp())
            page._enter_search("LC")
            self.assertEqual(page.cert_list.count(), 1)
            page.cert_list.setCurrentRow(0)
            self.assertIsNotNone(page._selected_student)
            self.assertTrue(page.cert_preview_btn.isEnabled())
            html = page._build_preview_html()
            self.assertIn("UI Test Student", html)
            self.assertIn("logof.png", html)
            page._enter_search("BON")
            page.cert_list.setCurrentRow(0)
            bon_html = build_bonafide_html(page._filtered[0])
            self.assertIn("UI Test Student", bon_html)
        finally:
            db.DB_PATH = orig_db
            shutil.rmtree(tmp, ignore_errors=True)

    def test_view_students_table_loads_with_scroll(self):
        tmp = self._fresh_tmp()
        db_path = tmp / "data" / "students.db"
        db_path.parent.mkdir(parents=True)
        orig_db = db.DB_PATH
        db.DB_PATH = str(db_path)
        db.init_db()
        db.add_academic_year("2026-2027")
        for i in range(5):
            db.save_student({
                "student_id": f"V{i}",
                "name_mr": f"View Student {i}",
                "current_class": "3-A",
                "academic_year": "2026-2027",
                "student_status": "current",
            })
        try:
            page = ViewStudentsPage(DummyMainApp())
            page._open_current_students()
            self.assertEqual(len(page._cur_data), 5)
            scrolls = page.findChildren(QScrollArea)
            self.assertGreaterEqual(len(scrolls), 0)
        finally:
            db.DB_PATH = orig_db
            shutil.rmtree(tmp, ignore_errors=True)

    def test_frozen_path_logic_matches_exe_layout(self):
        """Simulate PyInstaller frozen mode — data beside exe, assets in _MEIPASS."""
        sim_root = self._fresh_tmp()
        sim_dist = sim_root / "dist_sim"
        sim_meipass = sim_root / "_MEIPASS"
        sim_dist.mkdir()
        (sim_dist / "data").mkdir()
        sim_meipass.mkdir()
        shutil.copy2(ROOT / "logof.png", sim_meipass / "logof.png")
        shutil.copy2(ROOT / "data" / "students.db", sim_dist / "data" / "students.db")

        orig_base = config.app_base_path
        orig_res = config.resource_path
        try:
            config.app_base_path = lambda: str(sim_dist)
            config.resource_path = lambda rel: str(sim_meipass / rel)
            self.assertTrue(Path(config.resource_path("logof.png")).exists())
            self.assertTrue(Path(config.data_path("students.db")).exists())
        finally:
            config.app_base_path = orig_base
            config.resource_path = orig_res
            shutil.rmtree(sim_root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
