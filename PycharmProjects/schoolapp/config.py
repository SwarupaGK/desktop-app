# config.py

import os
import shutil
import sys
from datetime import datetime

SCHOOL_NAME = "Eklavya Gurukul School & Sports Academy, Ishwarpur"

SCHOOL_NAME_MR = "एकलव्य गुरुकुल शाळा व क्रीडा अकादमी, ईश्वरपूर"

ADMIN_CREDENTIALS = {"username": "admin", "password": "admin"}

def app_base_path():
    """Folder that contains app files when running from source or from an exe."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def resource_path(relative_path):
    """Resolve bundled read-only files such as images/fonts in PyInstaller."""
    if getattr(sys, "_MEIPASS", None):
        bundled_path = os.path.join(sys._MEIPASS, relative_path)
        if os.path.exists(bundled_path):
            return bundled_path

    base_path = app_base_path()
    app_path = os.path.join(base_path, relative_path)
    if os.path.exists(app_path):
        return app_path

    data_app_path = os.path.join(base_path, "data", relative_path)
    if os.path.exists(data_app_path):
        return data_app_path

    return app_path


def data_path(relative_path):
    """Resolve writable app data beside the exe/source files."""
    return os.path.join(app_base_path(), "data", relative_path)


def ensure_data_file(relative_path):
    """Create writable data file from bundled seed data when needed."""
    target = data_path(relative_path)
    
    # For .exe files, ensure data directory exists
    os.makedirs(os.path.dirname(target), exist_ok=True)
    
    # Check if this is a bundled executable
    if getattr(sys, "frozen", False):
        # Check if this is first run of .exe
        first_run_flag = data_path("first_run.flag")
        
        if not os.path.exists(first_run_flag):
            # First run of .exe - migrate development data if available
            if os.path.exists(target):
                # Backup existing database
                backup_path = target.replace('.db', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
                shutil.copy2(target, backup_path)
                print(f"💾 Backed up existing database: {backup_path}")
                
                # Try to migrate development data
                dev_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "students.db")
                if os.path.exists(dev_db_path):
                    # Copy development data to bundle location
                    shutil.copy2(dev_db_path, target)
                    print(f"🔄 Migrated development data to: {target}")
                else:
                    # No development data found, create fresh database (will be handled by main.py)
                    print(f"Fresh database will be created by main.py: {target}")
            else:
                # No existing database, create fresh one (will be handled by main.py)
                print(f"Fresh database will be created by main.py")
            
            # Create first run flag
            with open(first_run_flag, 'w') as f:
                f.write("first_run_completed")
            print(f"Database ready for .exe: {target}")
        else:
            # Subsequent runs - ensure database exists
            if not os.path.exists(target):
                # Create empty database if missing (will be handled by main.py)
                print(f"Missing database will be created by main.py: {target}")
        
            # Copy bundled database if available (for template/reference)
            bundled = resource_path(os.path.join("data", relative_path))
            if os.path.exists(bundled) and not os.path.exists(target):
                # Ensure target directory exists before copying
                os.makedirs(os.path.dirname(target), exist_ok=True)
                shutil.copy2(bundled, target)
                print(f"Copied bundled database to: {target}")
    else:
        # In development, use normal path
        bundled = resource_path(os.path.join("data", relative_path))
        if bundled != target and os.path.exists(bundled):
            shutil.copy2(bundled, target)
    
    return target


DB_PATH = data_path("students.db")

# All student field keys (matches DB columns and form entries)
STUDENT_FIELDS = [
    "student_id",
    "aadhaar",
    "pen_number",
    "name_mr",
    "mother_name_mr",
    "surname",
    "caste",
    "subcaste",
    "religion",
    "birth_place",
    "birth_taluka",
    "birth_dist",
    "birth_date_num",
    "birth_date_words",
    "previous_school",
    "admission_date",
    "current_class",
    "progress",
    "behaviour",
    "leaving_date",
    "class_at_leaving",
    "leaving_reason",
    "remark",
]

# Kindergarten + standard classes (stored as "Nursery-A", "1-B", "12-A", …)
KG_LEVELS = ("Nursery", "LKG", "UKG")


def class_prefix(current_class: str | None) -> str | None:
    if not current_class or not str(current_class).strip():
        return None
    s = str(current_class).strip()
    if "-" not in s:
        return None
    return s.split("-", 1)[0].strip() or None


def class_division(current_class: str | None) -> str:
    if not current_class or "-" not in str(current_class):
        return "A"
    return (str(current_class).split("-", 1)[1].strip() or "A")


def is_kindergarten_class(current_class: str | None) -> bool:
    pref = class_prefix(current_class)
    return pref in KG_LEVELS if pref else False


def is_grade_class_1_to_12(current_class: str | None) -> bool:
    pref = class_prefix(current_class)
    if not pref:
        return False
    try:
        n = int(pref)
        return 1 <= n <= 12
    except ValueError:
        return False


def next_kindergarten_or_first(current_class: str | None) -> str | None:
    pref = class_prefix(current_class)
    div = class_division(current_class)
    if pref == "Nursery":
        return f"LKG-{div}"
    if pref == "LKG":
        return f"UKG-{div}"
    if pref == "UKG":
        return f"1-{div}"
    return None
