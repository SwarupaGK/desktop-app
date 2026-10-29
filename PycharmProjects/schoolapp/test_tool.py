import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPORT_DIR = ROOT / "test_reports"

MANUAL_CHECKLIST = [
    "LOGIN-01 to LOGIN-06: Verify login, invalid login, reset password, and login with new password.",
    "DASH-01 to DASH-08: Verify dashboard navigation, logo, count, language toggle, and logout.",
    "ADD-01 to ADD-14: Verify Add Student validations and save flows in the visible app.",
    "VIEW-01 to VIEW-23: Verify table display, filters, edit/delete, and promotion flows.",
    "CERT-01 to CERT-13: Verify previews, printing/PDF flow, and logo visibility.",
    "BACKUP-01 to BACKUP-05: Verify backup dialog behavior and backup file contents.",
    "EXE-01 to EXE-12: Rebuild exe, run dist\\StudentHub.exe, verify logos/data/year persistence.",
]


def run_command(command):
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    return subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
    )


def write_report(title, command, result):
    REPORT_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = REPORT_DIR / f"test_report_{stamp}.txt"
    status = "PASS" if result.returncode == 0 else "FAIL"

    report = [
        title,
        "=" * len(title),
        "",
        f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Command: {' '.join(command)}",
        f"Status: {status}",
        f"Exit code: {result.returncode}",
        "",
        "Automated Test Output",
        "-" * 21,
        result.stdout.strip() or "(no stdout)",
        "",
        "Errors / Warnings",
        "-" * 17,
        result.stderr.strip() or "(no stderr)",
        "",
        "Manual / Visual Checklist",
        "-" * 25,
    ]
    report.extend(f"- {item}" for item in MANUAL_CHECKLIST)
    report.extend(
        [
            "",
            "Note: Automated tests protect database logic, add/view student flows, backup, certificate helpers,",
            "packaging paths, and the promotion bug. The checklist items require opening the app/exe because",
            "they depend on visible UI, dialogs, print previews, or the packaged executable.",
            "",
        ]
    )

    report_path.write_text("\n".join(report), encoding="utf-8")
    return report_path, status


def main():
    parser = argparse.ArgumentParser(description="StudentHub test runner")
    parser.add_argument(
        "--compile-only",
        action="store_true",
        help="Only run Python compile checks.",
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Print output only; do not write a report file.",
    )
    args = parser.parse_args()

    if args.compile_only:
        command = [
            sys.executable,
            "-m",
            "py_compile",
            "config.py",
            "db.py",
            "add_student.py",
            "view_students.py",
            "dashboard.py",
            "login.py",
            "certificates.py",
            "Db_lc.py",
            "main.py",
            "check_db.py",
            "tests\\test_schoolapp.py",
        ]
        title = "StudentHub Compile Check Report"
    else:
        command = [sys.executable, "-m", "unittest", "discover", "-v"]
        title = "StudentHub Automated Test Report"

    result = run_command(command)
    print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)

    if args.no_report:
        return result.returncode

    report_path, status = write_report(title, command, result)
    print()
    print(f"Status: {status}")
    print(f"Report saved: {report_path}")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
