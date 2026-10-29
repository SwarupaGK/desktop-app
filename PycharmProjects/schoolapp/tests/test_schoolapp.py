import os
import shutil
import sqlite3
import sys
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
TEST_TMP_ROOT = ROOT / ".test_tmp"
TEST_TMP_ROOT.mkdir(exist_ok=True)


def make_test_dir():
    path = TEST_TMP_ROOT / f"case_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    return path

from qt_compat import QApplication, QMessageBox

import backup
import certificates
import config
import db
import login
from add_student import AddStudentPage
from view_students import ViewStudentsPage


class DummyDashboard:
    def update_stats(self):
        pass


class DummyMainApp:
    def __init__(self):
        self.dashboard_page = DummyDashboard()
        self.students = []
        self.dashboard_visible = False

    def load_students_from_db(self):
        self.students = db.get_all_students()

    def show_dashboard(self):
        self.dashboard_visible = True


class DummyDialog:
    def __init__(self):
        self.accepted = False

    def accept(self):
        self.accepted = True


class SchoolAppTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp_path = make_test_dir()
        self.db_path = self.tmp_path / "data" / "students.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.originals = {
            "db.DB_PATH": db.DB_PATH,
            "backup.DB_PATH": backup.DB_PATH,
            "certificates.DB_PATH": certificates.DB_PATH,
            "login.CREDENTIALS_PATH": login.CREDENTIALS_PATH,
        }
        db.DB_PATH = str(self.db_path)
        backup.DB_PATH = str(self.db_path)
        certificates.DB_PATH = str(self.db_path)
        login.CREDENTIALS_PATH = str(self.tmp_path / "data" / "admin_credentials.json")
        db.init_db()

    def tearDown(self):
        db.DB_PATH = self.originals["db.DB_PATH"]
        backup.DB_PATH = self.originals["backup.DB_PATH"]
        certificates.DB_PATH = self.originals["certificates.DB_PATH"]
        login.CREDENTIALS_PATH = self.originals["login.CREDENTIALS_PATH"]
        shutil.rmtree(self.tmp_path, ignore_errors=True)

    def seed_students(self):
        self.assertTrue(db.add_academic_year("2026-2027"))
        self.assertTrue(db.add_academic_year("2027-2028"))
        rows = [
            {
                "student_id": "S001",
                "name_mr": "Grade One",
                "current_class": "1-A",
                "academic_year": "2026-2027",
                "student_status": "current",
                "birth_date_num": "01/01/2018",
            },
            {
                "student_id": "S002",
                "name_mr": "Passout Student",
                "current_class": "",
                "academic_year": "2026-2027",
                "student_status": "passout",
                "passout_year": "2026",
            },
            {
                "student_id": "S003",
                "name_mr": "Nursery Student",
                "current_class": "Nursery-A",
                "academic_year": "2027-2028",
                "student_status": "current",
            },
            {
                "student_id": "S004",
                "name_mr": "Class Twelve",
                "current_class": "12-B",
                "academic_year": "2027-2028",
                "student_status": "current",
            },
        ]
        for row in rows:
            self.assertTrue(db.save_student(row))


class DatabaseTests(SchoolAppTestCase):
    def test_init_db_creates_required_tables_and_columns(self):
        with sqlite3.connect(db.DB_PATH) as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            columns = {
                row[1]
                for row in conn.execute("PRAGMA table_info(students)").fetchall()
            }

        self.assertIn("students", tables)
        self.assertIn("academic_years", tables)
        self.assertIn("residential_status", columns)
        self.assertIn("lc_no", columns)

    def test_academic_year_persists_without_students(self):
        self.assertTrue(db.add_academic_year("2030-2031"))
        self.assertIn("2030-2031", db.get_academic_years())
        self.assertTrue(db.add_academic_year("2030-2031"))
        self.assertEqual(db.get_academic_years().count("2030-2031"), 1)

    def test_save_fetch_duplicate_delete_student(self):
        student = {
            "student_id": "S100",
            "name_mr": "Test Student",
            "current_class": "2-A",
            "academic_year": "2029-2030",
            "student_status": "current",
        }
        self.assertTrue(db.save_student(student))
        self.assertFalse(db.save_student(student))
        self.assertIn("2029-2030", db.get_academic_years())
        self.assertEqual(len(db.get_students_by_academic_year("2029-2030")), 1)
        self.assertEqual(db.get_student_status("S100"), "Current")

        saved = db.get_all_students()[0]
        self.assertTrue(db.delete_student_by_id(saved["id"]))
        self.assertEqual(db.get_all_students(), [])

    def test_counts_status_and_promotion_helpers(self):
        self.seed_students()
        grade = next(s for s in db.get_all_students() if s["student_id"] == "S001")

        self.assertEqual(db.get_lc_count(grade["id"]), 0)
        self.assertEqual(db.get_lc_number_for_print(grade["id"]), 1)
        self.assertEqual(db.increment_lc_count(grade["id"]), 1)
        self.assertEqual(db.get_lc_no(grade["id"]), 1)
        other = next(s for s in db.get_all_students() if s["student_id"] == "S004")
        self.assertEqual(db.get_lc_number_for_print(other["id"]), 2)
        self.assertEqual(db.increment_bonafide_count(grade["id"]), 1)
        self.assertTrue(db.mark_student_as_passout(grade["id"], "2027"))
        self.assertEqual(db.get_student_status("S001"), "Passout")

        passout = next(s for s in db.get_all_students() if s["student_id"] == "S001")
        self.assertEqual(passout["passout_year"], "2027")

    def test_promote_student_returns_true_when_year_already_exists(self):
        self.seed_students()
        grade = next(s for s in db.get_all_students() if s["student_id"] == "S001")

        self.assertIn("2027-2028", db.get_academic_years())
        self.assertTrue(db.promote_student(grade["id"], "2-A", "2027-2028"))

        updated = next(s for s in db.get_all_students() if s["student_id"] == "S001")
        self.assertEqual(updated["current_class"], "2-A")
        self.assertEqual(updated["academic_year"], "2027-2028")


class LoginTests(SchoolAppTestCase):
    def test_default_and_saved_admin_credentials(self):
        self.assertEqual(login.get_admin_credentials()["username"], "admin")
        self.assertTrue(login.save_admin_password("new-secret"))
        self.assertEqual(login.get_admin_credentials()["password"], "new-secret")


class AddStudentTests(SchoolAppTestCase):
    def test_add_academic_year_validation_and_persistence(self):
        page = AddStudentPage(DummyMainApp())

        with patch.object(QMessageBox, "warning", return_value=QMessageBox.Ok), \
             patch.object(QMessageBox, "critical", return_value=QMessageBox.Ok), \
             patch.object(QMessageBox, "information", return_value=QMessageBox.Ok):
            invalid_dialog = DummyDialog()
            page._save_academic_year("2030", invalid_dialog)
            self.assertFalse(invalid_dialog.accepted)
            self.assertNotIn("2030", db.get_academic_years())

            valid_dialog = DummyDialog()
            page._save_academic_year("2030-2031", valid_dialog)
            self.assertTrue(valid_dialog.accepted)
            self.assertIn("2030-2031", db.get_academic_years())
            self.assertGreaterEqual(page.year_combo.findText("2030-2031"), 0)

    def test_save_current_student_from_form(self):
        db.add_academic_year("2026-2027")
        main_app = DummyMainApp()
        page = AddStudentPage(main_app)
        page.selected_year = "2026-2027"

        page.entries["student_id"].setText("FORM-1")
        page.entries["first_name"].setText("Form")
        page.entries["father_name"].setText("Student")
        page.entries["surname"].setText("One")
        page.class_track_combo.setCurrentIndex(1)
        page.class_combo.setCurrentText("3")
        page.div_combo.setCurrentText("B")

        with patch.object(QMessageBox, "information", return_value=QMessageBox.Ok), \
             patch.object(QMessageBox, "warning", return_value=QMessageBox.Ok), \
             patch.object(QMessageBox, "critical", return_value=QMessageBox.Ok):
            page.save_student()

        saved = db.get_all_students()
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0]["student_id"], "FORM-1")
        self.assertEqual(saved[0]["name_mr"], "Form Student One")
        self.assertEqual(saved[0]["current_class"], "3-B")
        self.assertEqual(saved[0]["academic_year"], "2026-2027")
        self.assertEqual(len(main_app.students), 1)


class ViewStudentsTests(SchoolAppTestCase):
    def test_view_student_loaders_and_filters(self):
        self.seed_students()
        page = ViewStudentsPage(DummyMainApp())

        page._open_general_all()
        self.assertEqual({s["student_id"] for s in page._gen_data}, {"S001", "S002", "S004"})

        page.gen_year_filter.setCurrentText("2026-2027")
        page._load_general_students()
        self.assertEqual({s["student_id"] for s in page._gen_data}, {"S001", "S002"})

        page.gen_search.setText("passout")
        page._load_general_students()
        self.assertEqual([s["student_id"] for s in page._gen_data], ["S002"])

        page._open_current_students()
        self.assertEqual({s["student_id"] for s in page._cur_data}, {"S001", "S004"})

        page.cur_class_filter.setCurrentText("12")
        page._load_current_students()
        self.assertEqual([s["student_id"] for s in page._cur_data], ["S004"])

        page._open_kindergarten()
        self.assertEqual([s["student_id"] for s in page._kg_data], ["S003"])

    def test_year_selection_refreshes_new_year(self):
        page = ViewStudentsPage(DummyMainApp())
        self.assertEqual(page.year_combo.findText("2035-2036"), -1)

        db.add_academic_year("2035-2036")
        page._open_year_select()
        self.assertGreaterEqual(page.year_combo.findText("2035-2036"), 0)

    def test_next_academic_year_helper(self):
        page = ViewStudentsPage(DummyMainApp())
        self.assertEqual(page._next_academic_year("2026-2027"), "2027-2028")
        self.assertEqual(page._next_academic_year("bad-year"), "bad-year")


class CertificateTests(SchoolAppTestCase):
    def test_certificate_logo_html_uses_resolved_logo_path(self):
        html = certificates._logo_html()
        self.assertIn("<img", html)
        self.assertIn("file:///", html)
        self.assertIn("logof.png", html)

    def test_bonafide_date_is_blank_for_manual_writing(self):
        html = certificates.build_bonafide_html({})
        self.assertNotIn("17/04/2024", html)
        self.assertIn("&nbsp;&nbsp;/&nbsp;&nbsp;/&nbsp;&nbsp;&nbsp;&nbsp;", html)

    def test_lc_signature_date_is_blank_but_leaving_date_stays_filled(self):
        html = certificates.build_lc_html({"leaving_date": "31/03/2027"})
        self.assertIn("31/03/2027", html)
        self.assertIn("दिनांक :", html)
        self.assertIn("/&nbsp;&nbsp;&nbsp;/&nbsp;&nbsp;&nbsp;&nbsp;", html)

    def test_lc_header_uses_lc_no_and_general_register_record_id(self):
        html = certificates.build_lc_html(
            {"id": 440, "student_id": "S848", "lc_no": 7},
            lc_no=7,
        )
        self.assertIn("No.&nbsp;7", html)
        self.assertNotIn("No.&nbsp;S848", html)
        self.assertIn(":-&nbsp;440", html)

    def test_mark_student_as_passout_extracts_year_from_leaving_date(self):
        db.save_student(
            {
                "student_id": "LC1",
                "name_mr": "LC Student",
                "current_class": "4-A",
                "academic_year": "2026-2027",
                "student_status": "current",
            }
        )
        student = db.get_all_students()[0]

        self.assertTrue(certificates.mark_student_as_passout(student["id"], "31/03/2027"))
        updated = db.get_all_students()[0]
        self.assertEqual(updated["student_status"], "passout")
        self.assertEqual(updated["passout_year"], "2027")

    def test_validate_lc_fields_reports_missing_required_data(self):
        missing = certificates.validate_lc_fields({"student_id": "S1"})
        self.assertTrue(missing)


class BackupTests(SchoolAppTestCase):
    def test_backup_creates_sqlite_copy_and_adds_extension(self):
        db.save_student(
            {
                "student_id": "B1",
                "name_mr": "Backup Student",
                "current_class": "5-A",
                "academic_year": "2026-2027",
                "student_status": "current",
            }
        )
        target_without_ext = self.tmp_path / "backup-output"
        module = backup.BackupModule(DummyMainApp())

        with patch.object(
            backup.QFileDialog,
            "getSaveFileName",
            return_value=(str(target_without_ext), "SQLite Database (*.sqlite)"),
        ), patch.object(backup.QMessageBox, "information", return_value=QMessageBox.Ok):
            module.backup()

        copied = self.tmp_path / "backup-output.sqlite"
        self.assertTrue(copied.exists())
        with sqlite3.connect(copied) as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM students").fetchone()[0], 1)

    def test_backup_cancel_does_not_create_file(self):
        module = backup.BackupModule(DummyMainApp())
        with patch.object(
            backup.QFileDialog,
            "getSaveFileName",
            return_value=("", ""),
        ):
            module.backup()
        self.assertFalse((self.tmp_path / "cancel.sqlite").exists())


class PackagingPathTests(unittest.TestCase):
    def test_resource_paths_and_seed_data_copy(self):
        root = make_test_dir()
        try:
            app_dir = root / "app"
            bundle_dir = root / "bundle"
            app_dir.mkdir()
            (bundle_dir / "data").mkdir(parents=True)
            seed = bundle_dir / "data" / "students.db"
            seed.write_bytes(b"seed-db")

            original_app_base = config.app_base_path
            original_resource_path = config.resource_path
            try:
                config.app_base_path = lambda: str(app_dir)
                config.resource_path = lambda rel: str(bundle_dir / rel)
                target = Path(config.ensure_data_file("students.db"))
            finally:
                config.app_base_path = original_app_base
                config.resource_path = original_resource_path

            self.assertEqual(target, app_dir / "data" / "students.db")
            self.assertEqual(target.read_bytes(), b"seed-db")
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_build_script_includes_required_packaged_assets(self):
        build_script = (ROOT / "build_exe.bat").read_text(encoding="utf-8")
        for expected in [
            'logof.png;.',
            'data\\students.db;data',
            'data\\admin_credentials.json;data',
        ]:
            self.assertIn(expected, build_script)

    def test_main_spec_includes_required_packaged_assets(self):
        main_spec = (ROOT / "StudentHub.spec").read_text(encoding="utf-8")
        for expected in [
            "('logof.png', '.')",
            "('data\\\\students.db', 'data')",
            "('data\\\\admin_credentials.json', 'data')",
        ]:
            self.assertIn(expected, main_spec)


if __name__ == "__main__":
    unittest.main()
