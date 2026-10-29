from __future__ import annotations

from typing import Optional

from qt_compat import *
from qt_compat import configure_printer_a4, printer_document_page_size
import os
import sys
import sqlite3
from datetime import datetime
from html import escape

from config import DB_PATH, is_grade_class_1_to_12, resource_path

# ══════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════

def _logo_html(w=82, h=82):
    path = resource_path("logof.png")
    if os.path.exists(path):
        path = path.replace("\\", "/")
        return (
            f'<img src="file:///{path}" width="{w}" height="{h}" '
            f'style="display:block;"/>'
        )
    # placeholder box so layout still works without logo
    return (
        f'<div style="width:{w}px;height:{h}px;border:1px solid #aaa;'
        f'display:inline-block;"></div>'
    )


def _esc(val, default=""):
    text = str(val or default).strip()
    return escape(text) if text else escape(str(default))


_SEARCH_STYLE = """
    QLineEdit{background:white;color:black;border:1px solid #dce1e7;
              border-radius:8px;padding:6px 10px;font-size:13px;}
    QLineEdit::placeholder{color:#555555;}
"""


# ══════════════════════════════════════════════════════════════════
#  LC HTML  — matches Image 1 exactly
# ══════════════════════════════════════════════════════════════════

def build_lc_html(student: dict, copy_number: int = 1, lc_no=None) -> str:
    s = student

    # ── combined fields ──
    dharma_jat = (
        f"{_esc(s.get('religion', ''))} – {_esc(s.get('caste', ''))}"
    ).strip(" –")
    if s.get('subcaste', ''):
        dharma_jat += f" – {_esc(s.get('subcaste', ''))}"

    birth_place = (
        f"{_esc(s.get('birth_place', ''))} , "
        f"ता.{_esc(s.get('birth_taluka', ''))} , "
        f"जि.{_esc(s.get('birth_dist', ''))}"
    ).strip(" ,")

    admission = (
        f"{_esc(s.get('admission_date', ''))} – "
        f"इ.{_esc(s.get('current_class', ''))}"
    ).strip(" –")

    cert_no = _esc(lc_no if lc_no is not None else s.get("lc_no", ""), "")
    reg_no = _esc(s.get("general_reg_no") or s.get("id") or "", "")
    udise_no = _esc(s.get("udise_no", "27350902608"), "27350902608")

    # ── duplicate label ──
    dup_html = ""
    if copy_number > 1:
        dup_html = (
            f'<p style="text-align:left;color:#b00000;font-weight:bold;'
            f'font-size:9pt;margin:0 0 3px 0;">'
            f'Duplicate Copy No. {copy_number}</p>'
        )

    # ── row builder ──
    def row(num, label, value, tall=False):
        h = "36px" if tall else "21px"
        return (
            f'<tr style="height:{h};">'
            f'<td style="width:30px;text-align:center;border:1px solid #000;'
            f'padding:1px 3px;font-size:9pt;vertical-align:middle;">{num}</td>'
            f'<td style="width:46%;border:1px solid #000;'
            f'padding:1px 5px;font-size:9pt;vertical-align:middle;">{label}</td>'
            f'<td style="border:1px solid #000;'
            f'padding:1px 5px;font-size:9pt;vertical-align:middle;">{value}</td>'
            f'</tr>'
        )

    rows = (
            row("1)", "विद्यार्थी आयडी क्रमांक.", _esc(s.get("student_id", "")))
            + row("2)", "आधार कार्ड क्रमांक.", _esc(s.get("aadhaar", "")))
            + row("3)", "पेन नंबर(Permanent Education Number)", _esc(s.get("pen_number", "")))
            + row("4)", "विद्यार्थ्याचे नांव, वडिलांचे नांव, आडनांव",
                  f"<b>{_esc(s.get('name_mr', ''))}</b>")
            + row("5)", "आईचे नांव", _esc(s.get("mother_name_mr", "")))
            + row("6)", "धर्म व जात", dharma_jat)
            + row("7)", "राष्ट्रीयत्व",
                  _esc(s.get("religion", "भारतीय"), "भारतीय"))
            + row("8)", "जन्मस्थळ, तालुका, जिल्हा", birth_place)
            + row("9)",
                  "इसवि सनाप्रमाणे जन्मतारीख<br>(अंकी व अक्षरी)",
                  f"{_esc(s.get('birth_date_num', ''))}<br>"
                  f"{_esc(s.get('birth_date_words', ''))}",
                  tall=True)
            + row("10)", "यापूर्वी शिकत असलेली शाळा",
                  _esc(s.get("previous_school", "")))
            + row("11)", "या शाळेत प्रवेश दिल्याची तारीख व इयत्ता", admission)
            + row("12)", "अभ्यासातील प्रगती",
                  _esc(s.get("progress", "चांगली."), "चांगली."))
            + row("13)", "वर्तणूक",
                  _esc(s.get("behaviour", "चांगली."), "चांगली."))
            + row("14)", "शाळा सोडल्याची तारीख",
                  _esc(s.get("leaving_date", "")))
            + row("15)",
                  "कोणत्या इयत्तेत शिकत होता<br>कधीपासून (अंकी व अक्षरी)",
                  _esc(s.get("class_at_leaving", "")),
                  tall=True)
            + row("16)", "शाळा सोडल्याचे कारण",
                  _esc(s.get("leaving_reason", "")))
            + row("17)", "शेरा",
                  _esc(s.get("remark", "खाडाखोड नाही."), "खाडाखोड नाही."))
    )

    printable_date_blank = "&nbsp;&nbsp;&nbsp;&nbsp;/&nbsp;&nbsp;&nbsp;/&nbsp;&nbsp;&nbsp;&nbsp;"

    # ══ NOTE ═════════════════════════════════════════════════════
    # QTextDocument (Qt's HTML renderer) does NOT support:
    #   • CSS flexbox / grid
    #   • position:absolute / position:fixed
    #   • CSS @page
    # We use only TABLE-based layout + inline styles.
    # ═════════════════════════════════════════════════════════════

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"/>
<style>
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{
    font-family:'Nirmala UI','Mangal',Arial,sans-serif;
    font-size:9pt;
    color:#000;
    background:#fff;
    line-height:1.2;
  }}
</style>
</head>
<body style="margin:4mm 6mm 4mm 6mm;">
<!-- ═══════════════════════════════════════════════════
     HEADER TABLE
     Col-L (18%) : स्थापना label  +  logo image
     Col-C (64%) : trust name  /  school name  /  address
     Col-R (18%) : intentionally blank (mirrors left → keeps center truly centred)
════════════════════════════════════════════════════ -->
<table width="100%" cellspacing="0" cellpadding="0"
       style="border-collapse:collapse; margin-bottom:6px;">
  <tr>

    <!-- LEFT : estd + logo -->
    <td width="18%" valign="top" style="padding:0;">
      <div style="font-size:9pt;font-weight:bold;margin-bottom:3px;">
        स्थापना : २००२
      </div>
      {_logo_html(82, 82)}
    </td>

    <!-- CENTER : school info -->
    <td width="64%" valign="middle" align="center"
        style="padding:0 6px;">
      <div style="font-size:7.5pt;font-weight:600;margin-bottom:2px;">
        श्री कपिलेश्वर शिक्षण संस्था, ईश्वरपूर संचलित,
      </div>
      <div style="font-size:11pt;font-weight:900;line-height:1.12;
                  margin:3px 0 2px 0;">
        एकलव्य गुरुकुल स्कुल &amp; स्पोर्ट्स अकॅडमी कापुरवाडी,ईश्वरपूर
      </div>
      <div style="font-size:7.5pt;font-weight:600;">
        ता. वाळवा, जि. सांगली. 415407
      </div>
    </td>

    <!-- RIGHT : blank mirror -->
    <td width="18%" valign="top" style="padding:0;"></td>

  </tr>
</table>

<!-- ═══════════════════════════════════════════════════
     META ROW
     Col-L : युडायस नं
     Col-C : [शाळा सोडल्याचे प्रमाणपत्र]  ← BOXED
     Col-R : No. xxx  /  ज.र.नंबर :-  yyy
════════════════════════════════════════════════════ -->
<table width="100%" cellspacing="0" cellpadding="0"
       style="border-collapse:collapse; margin:2px 0 4px 0;">
  <tr>
    <td width="28%" valign="bottom"
        style="font-size:9.5pt;font-weight:bold;padding:0;">
      युडायस नं - {udise_no}
    </td>
    <td width="44%" valign="bottom" align="center" >
      <!-- BOXED certificate title — enhanced border styling -->
      <span style="display:inline-block;
                   border:2px solid #000;
                   padding:8px 25px;
                   font-size:12pt;
                   font-weight:900;
                   background-color:#fff;
                   line-height:1.4;">
        शाळा सोडल्याचे<br>प्रमाणपत्र
      </span>
    </td>
    <td width="28%" valign="bottom" align="right"
        style="font-size:9.5pt;font-weight:bold;
               line-height:1.7;padding:0;">
      No.&nbsp;{cert_no}<br>
      ज.र.नंबर :-&nbsp;{reg_no}
    </td>
  </tr>
</table>

<!-- ═══════════════════════════════════════════════════
     MAIN DATA TABLE  (rows 1–17)
════════════════════════════════════════════════════ -->
<table width="100%" cellspacing="0" cellpadding="0"
       style="border-collapse:collapse;
              border:1.5px solid #000;
              margin-bottom:10px;">
  {rows}
</table>

<!-- ═══════════════════════════════════════════════════
     VERIFICATION LINE
════════════════════════════════════════════════════ -->
<p style="text-align:center;font-size:7pt;font-weight:600;
          margin:6px 0 10px 0;">
  असे प्रमाणित करण्यात येते कि, वर दिलेली माहिती
  शाळेच्या रजिस्टर बरहुकूम आहे.
</p>
<!-- ═══════════════════════════════════════════════════
     DATE  (left-aligned, below signatures)
════════════════════════════════════════════════════ -->
<p style="font-size:9pt;font-weight:bold;margin:4px 0 10px 0;">
  दिनांक :{printable_date_blank}
</p>
<!-- ═══════════════════════════════════════════════════
     SIGNATURE ROW
     Three equal columns, labels below space
════════════════════════════════════════════════════ -->
<table width="100%" cellspacing="0" cellpadding="0"
       style="border-collapse:collapse; margin-top:40px;">
  <tr>
    <td width="33%" align="center" valign="bottom" style="padding:0 4px;">
      <div style="height:30px;"></div>
      <div style="font-size:9pt;font-weight:bold;">वर्गशिक्षक</div>
    </td>
    <td width="33%" align="center" valign="bottom" style="padding:0 4px;">
      <div style="height:30px;"></div>
      <div style="font-size:9pt;font-weight:bold;">लेखनिक</div>
    </td>
    <td width="33%" align="center" valign="bottom" style="padding:0 4px;">
      <div style="height:30px;"></div>
      <div style="font-size:9pt;font-weight:bold;">मुख्याध्यापक</div>

      </div>
    </td>
  </tr>
</table>



<!-- ═══════════════════════════════════════════════════
     FINAL WARNING
════════════════════════════════════════════════════ -->
<div style="border-top:1.5px solid #000;
            text-align:center;
            font-size:6pt;
            font-weight:bold;
            padding-top:4px;
            line-height:1.4;
          ">
        
  या प्रमाणपत्रातील कोणत्याही नोंदीत मुख्याध्यापकाशिवाय
  कोणासही बदल करता येणार नाही.<br>
  याचे उल्लंघन केल्यास कायदेशीर कारवाई करण्यास पात्र राहील.
</div>

</body>
</html>"""
# ══════════════════════════════════════════════════════════════════
#  BONAFIDE HTML
# ══════════════════════════════════════════════════════════════════
def _format_aadhar(aadhar: str) -> str:
    """Display Aadhaar number horizontally in boxes."""

    aadhar = str(aadhar or "").replace(" ", "").replace("-", "")

    if not aadhar:
        aadhar = "123456789012"

    if len(aadhar) < 12:
        aadhar = aadhar.ljust(12, "0")

    if len(aadhar) > 12:
        aadhar = aadhar[:12]

    boxes = ""

    for digit in aadhar:
        boxes += f"""
        <td style="
            border:1px solid black;
            width:22px;
            height:22px;
            text-align:center;
            font-size:9pt;
            font-weight:bold;
        ">
            {digit}
        </td>
        """

    return f"""
    <table style="border-collapse:collapse; margin-top:5px;">
        <tr>
            {boxes}
        </tr>
    </table>
    """


def build_bonafide_html(student: dict) -> str:
    s = student
    logo = _logo_html()
    aadhar_formatted = _format_aadhar(s.get("aadhaar", ""))

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
    * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }}

    body {{
        font-family: 'Nirmala UI','Mangal',Arial,sans-serif;
        font-size: 10pt;
        color: #000;
        background: white;
    }}

    .certificate {{
        width: 105mm;
        margin: 20mm auto;
        border: 1px solid #000;
        padding: 10mm;
    }}

    .header-text-container {{
        display: block;
        width: 100%;
        text-align: center !important;
    }}

    .trust-name {{
        font-size: 7pt;
        text-align: center;
        margin: 2px 0;
    }}

    .school-name {{
        font-size: 11pt;
        font-weight: bold;
        text-align: center;
        margin: 3px 0;
    }}

    .address {{
        font-size: 7pt;
        text-align: center;
        margin: 2px 0;
    }}

    .divider {{
        border: none;
        border-top: 1px solid #000;
        margin: 8px 0;
    }}

    .cert-title-box {{
        border: 2px solid #000;
        display: inline-block;
        padding: 4px 20px;
        font-size: 11pt;
        font-weight: bold;
    }}

    .line {{
        border-bottom: 1px solid #000;
        display: inline-block;
        min-width: 100px;
    }}

    .logo-cell img {{
        max-width: 60px;
        max-height: 60px;
        display: block;
        margin: 0 auto;
    }}
</style>
</head>

<body>

<div class="certificate">

    <!-- HEADER -->
    <table style="width:100%; border-collapse:collapse; table-layout:fixed; margin-bottom:5px;">
        <tr>
            <td style="width:15%; text-align:center; vertical-align:middle;" class="logo-cell">
                स्थापना : २००२<br>
                {logo}
            </td>

            <td style="width:70%; text-align:center; vertical-align:middle;">
                <div class="header-text-container">
                    <div class="trust-name" style="margin-left:50 px;">श्री कपिलेश्वर शिक्षण संस्था, ईश्वरपूर संचलित</div>
                    <div class="school-name" style="margin-left:50 px;">एकलव्य गुरुकुल स्कुल &amp; स्पोर्ट्स अकॅडमी</div>
                    <div class="address" style="margin-left:50 px;">कापुरवाडी, ईश्वरपूर ता. वाळवा, जि. सांगली</div>
                </div>
            </td>

            <td style="width:15%;"></td>
        </tr>
    </table>

    <p class="divider">

    <!-- TITLE -->
    <div style="text-align:center; margin:12px 0;">
        <span class="cert-title-box">बोनाफाईड सर्टिफिकेट</span>
    </div>

    <!-- DATE & REF NO: Fixed spacing & syntax -->
    <table style="width:100%; margin-bottom:18px; border-collapse:collapse;">
        <tr>
            <td style="width:40%; text-align:left;">
                <b>ज.र.क्र.</b> <span class="line">{s.get('ref_no', 'BON/2024/001')}</span>
            </td>
            <td style="width:20%;"></td> <!-- Guaranteed spacer column -->
            <td style="width:40%; text-align:right;">
            <div class="date=issue" style="margin-left:260px;">
                <b>दि.</b> <span class="line">&nbsp;&nbsp;/&nbsp;&nbsp;/&nbsp;&nbsp;&nbsp;&nbsp;</span>
                </div>
            </td>
        </tr>
    </table>

    <!-- CONTENT -->
    <div style="line-height:1.8; text-align:justify; margin-bottom:18px;">
        प्रमाणित करण्यात येते की, कुमार / कुमारी
        <span class="line"><b>{s.get('name_mr', '')}</b></span>
        या विद्यालयाचा अधिकृत विद्यार्थी असून त्याची / तिची जन्मतारीख
        <span class="line"><b>{s.get('birth_date_num', '')}</b></span>
        अक्षरी
        <span class="line"><b>{s.get('birth_date_words', '')}</b></span>
        असे शाळेच्या जनरल रजिस्टर प्रमाणे आहे.
        तो / ती इयत्ता
        <span class="line"><b>{s.get('current_class', '')}</b></span>
        मध्ये शिकत आहे / होता / होती.
        त्याची / तिची जात
        <span class="line"><b>{s.get('caste', '')}</b></span>
        आहे.
        त्याची / तिची वर्तणूक चांगली आहे.
    </div>

    <!-- FOOTER -->
    <table style="width:100%; margin-top:15px; border-collapse:collapse;">
        <tr>
            <td style="width:50%; vertical-align:top;">
                <b>स्टुडंट आय.डी.</b> <b><u>{s.get('student_id', '')}</u></b><br><br>
                <b>आधारकार्ड क्र.</b> <u>{aadhar_formatted}</u>
            </td>

            <td style="width:50%; text-align:right; vertical-align:bottom;">
            <div class="principle-signature" style="margin-left:210px;">
                <br>
                <b>मुख्याध्यापक</b>
                </div>
            </td>
        </tr>
    </table>

</div>

</body>
</html>"""


# ══════════════════════════════════════════════════════════════════
#  LC FIELD VALIDATION
# ══════════════════════════════════════════════════════════════════

LC_REQUIRED_FIELDS = [
    ("student_id",       "1) विद्यार्थी आयडी क्रमांक"),
    ("aadhaar",          "2) आधार कार्ड क्रमांक"),
    ("name_mr",          "4) विद्यार्थ्याचे नांव"),
    ("mother_name_mr",   "5) आईचे नांव"),
    ("caste",            "6) जात"),
    ("religion",         "7) राष्ट्रीयत्व"),
    ("birth_place",      "8) जन्मस्थळ"),
    ("birth_date_num",   "9) जन्मतारीख (अंकी)"),
    ("birth_date_words", "9) जन्मतारीख (अक्षरी)"),
    ("previous_school",  "10) यापूर्वीची शाळा"),
    ("admission_date",   "11) प्रवेश तारीख"),
    ("progress",         "12) अभ्यासातील प्रगती"),
    ("behaviour",        "13) वर्तणूक"),
    ("leaving_date",     "14) शाळा सोडल्याची तारीख"),
    ("class_at_leaving", "15) शाळा सोडली ती इयत्ता"),
    ("leaving_reason",   "16) शाळा सोडल्याचे कारण"),
]


def validate_lc_fields(student: dict) -> list:
    missing = []
    for field, label in LC_REQUIRED_FIELDS:
        val = student.get(field, "")
        if not val or str(val).strip() == "":
            missing.append(label)
    return missing


def show_lc_fill_dialog(parent, student: dict, missing_fields: list):
    dialog = QDialog(parent)
    dialog.setWindowTitle("⚠️ LC साठी माहिती अपूर्ण / Missing LC Fields")
    from ui_responsive import apply_main_window_geometry, configure_scroll_area, apply_label_constraints

    apply_main_window_geometry(dialog, preferred=(800, 620), minimum=(520, 400))

    ml = QVBoxLayout(dialog)

    warn = QLabel(
        f"⚠️  खालील {len(missing_fields)} माहिती रकाने रिकामे आहेत. "
        f"LC तयार करण्यापूर्वी भरा.\n"
        f"The following {len(missing_fields)} fields are empty."
    )
    warn.setWordWrap(True)
    warn.setStyleSheet(
        "background:#fff3cd;color:#856404;border-radius:8px;"
        "padding:12px;font-size:13px;font-weight:bold;"
    )
    ml.addWidget(warn)

    scroll = QScrollArea()
    configure_scroll_area(scroll)
    scroll.setStyleSheet("QScrollArea{border:none;}")
    cont = QWidget()
    cont.setStyleSheet("background:white;border-radius:10px;")
    form = QFormLayout(cont)
    form.setFieldGrowthPolicy(FORM_EXPAND_FIELDS)
    form.setLabelAlignment(ALIGN_LEFT_TOP)
    form.setContentsMargins(20, 16, 20, 16)
    form.setSpacing(12)

    all_fields = [
        ("student_id",       "1) विद्यार्थी आयडी क्रमांक *"),
        ("aadhaar",          "2) आधार कार्ड क्रमांक *"),
        ("pen_number",       "3) पेन  नंबर "),
        ("name_mr",          "4) विद्यार्थ्याचे नांव (मराठी) *"),
        ("mother_name_mr",   "5) आईचे नांव *"),
        ("caste",            "6) जात *"),
        ("subcaste",         "6b) पोटजात"),
        ("religion",         "7) राष्ट्रीयत्व *"),
        ("nationality",      "7b) e.g. भारतीय"),
        ("birth_place",      "8) जन्मस्थळ *"),
        ("birth_taluka",     "8b) तालुका"),
        ("birth_dist",       "8c) जिल्हा"),
        ("birth_date_num",   "9) जन्मतारीख (अंकी) * e.g. 03/07/2016"),
        ("birth_date_words", "9) जन्मतारीख (अक्षरी) *"),
        ("previous_school",  "10) यापूर्वीची शाळा *"),
        ("admission_date",   "11) प्रवेश तारीख * e.g. 06/09/2024"),
        ("current_class",    "11b) इयत्ता e.g. 2-A"),
        ("progress",         "12) अभ्यासातील प्रगती *"),
        ("behaviour",        "13) वर्तणूक *"),
        ("leaving_date",     "14) शाळा सोडल्याची तारीख *"),
        ("class_at_leaving", "15) शाळा सोडली ती इयत्ता *"),
        ("leaving_reason",   "16) शाळा सोडल्याचे कारण *"),
        ("remark",           "17) शेरा"),
    ]

    missing_keys = {f for f, _ in LC_REQUIRED_FIELDS}
    entries = {}

    for key, lbl_text in all_fields:
        lbl = QLabel(lbl_text)
        apply_label_constraints(lbl, max_w=300)
        is_missing = key in missing_keys and not (student.get(key,"") or "").strip()
        lbl.setStyleSheet(
            f"font-weight:bold;font-size:12px;background:transparent;"
            f"color:{'#123456' if is_missing else '#123456'};"
        )
        ent = QLineEdit(str(student.get(key,"") or ""))
        ent.setFixedHeight(34)
        bc = "#e74c3c" if is_missing else "#ccc"
        ent.setStyleSheet(
            f"QLineEdit{{padding:4px 10px;border:2px solid {bc};"
            f"border-radius:5px;color:#2c3e50;background:white;font-size:12px;}}"
            f"QLineEdit:focus{{border:2px solid #123456;}}"
        )
        form.addRow(lbl, ent)
        entries[key] = ent

    scroll.setWidget(cont)
    ml.addWidget(scroll)

    br = QHBoxLayout()
    cancel_btn = QPushButton("रद्द करा / Cancel")
    cancel_btn.setMinimumSize(150, 42)
    cancel_btn.setStyleSheet(
        "QPushButton{background:#123456;color:white;border-radius:8px;"
        "font-weight:bold;border:none;font-size:14px;padding:0 20px;}"
        "QPushButton:hover{background:#1a252f;}"
    )
    cancel_btn.clicked.connect(dialog.reject)

    save_btn = QPushButton("💾 जतन करा व LC तयार करा / Save & Generate LC")
    save_btn.setMinimumHeight(42)
    save_btn.setStyleSheet(
        "QPushButton{background:#123456;color:white;border-radius:8px;"
        "font-weight:bold;border:none;padding:0 20px;font-size:14px;}"
        "QPushButton:hover{background:#1a252f;}"
    )

    br.addStretch()
    br.addWidget(cancel_btn)
    br.addWidget(save_btn)
    ml.addLayout(br)

    result = {"accepted": False, "student": None}

    def _save():
        updated = dict(student)
        for key, ent in entries.items():
            updated[key] = ent.text().strip()

        still_missing = validate_lc_fields(updated)
        if still_missing:
            QMessageBox.warning(
                dialog, "❌ अजूनही रकाने रिकामे",
                "खालील अनिवार्य रकाने अजूनही रिकामे आहेत:\n\n" +
                "\n".join(still_missing) +
                "\n\nकृपया सर्व * चिन्हित रकाने भरा."
            )
            return

        conn = sqlite3.connect(DB_PATH)
        cur  = conn.cursor()
        try:
            set_parts = [f"{k}=?" for k in entries]
            vals      = [ent.text().strip() for ent in entries.values()]
            vals.append(updated["id"])
            cur.execute(
                f"UPDATE students SET {', '.join(set_parts)} WHERE id=?", vals
            )
            conn.commit()
            result["accepted"] = True
            result["student"]  = updated
            dialog.accept()
        except Exception as e:
            QMessageBox.critical(dialog, "❌ Error", str(e))
        finally:
            conn.close()

    save_btn.clicked.connect(_save)
    dialog.exec()
    return result["student"] if result["accepted"] else None


def mark_student_as_passout(student_db_id: int, leaving_date: str = ""):
    passout_year = ""
    if leaving_date:
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
            try:
                passout_year = str(datetime.strptime(leaving_date, fmt).year)
                break
            except ValueError:
                continue
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    try:
        cur.execute(
            "UPDATE students SET student_status='passout', passout_year=? WHERE id=?",
            (passout_year or None, student_db_id)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"[mark_passout] Error: {e}")
        return False
    finally:
        conn.close()


# ══════════════════════════════════════════════════════════════════
#  PRINTER HELPERS
# ══════════════════════════════════════════════════════════════════

def _make_printer(output_path: str = None) -> QPrinter:
    printer = QPrinter(QPrinter.HighResolution)
    return configure_printer_a4(printer, output_path)


def _load_doc(html: str, printer: QPrinter) -> QTextDocument:
    doc = QTextDocument()
    doc.setHtml(html)
    doc.setPageSize(printer_document_page_size(printer))

    from config import resource_path
    
    font_db = QFontDatabase()
    
    # Try to load Marathi fonts from system and bundled fonts
    marathi_fonts = ['Nirmala UI', 'Mangal', 'Devanagari UI', 'Arial Unicode MS']
    
    # Try to load bundled Marathi fonts first (for .exe compatibility)
    font_loaded = False
    for font_name in marathi_fonts:
        # Check if font file exists in bundled resources
        font_file = resource_path(f"{font_name}.ttf")
        if os.path.exists(font_file):
            font_id = font_db.addApplicationFont(font_file)
            if font_id != -1:
                font_loaded = True
                doc.setDefaultFont(QFont(font_name, 10))
                break
        elif font_db.hasFamily(font_name):
            font_loaded = True
            doc.setDefaultFont(QFont(font_name, 10))
            break
    
    # Fallback to system fonts if no Marathi fonts found
    if not font_loaded:
        # Try common system fonts that support Marathi
        system_fonts = ['Arial', 'Times New Roman', 'Segoe UI']
        for font_name in system_fonts:
            if font_db.hasFamily(font_name):
                doc.setDefaultFont(QFont(font_name, 10))
                break
    
    return doc


def show_preview(html: str, parent=None, title: str = "प्रमाणपत्र पूर्वावलोकन"):
    printer = _make_printer()
    preview = QPrintPreviewDialog(printer, parent)
    preview.setWindowTitle(title)
    # Remove minimize option and keep only the close (cancel) option
    preview.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
    preview.resize(960, 760)
    preview.setAttribute(Qt.WA_QuitOnClose, False)
    preview.paintRequested.connect(lambda p: _load_doc(html, p).print_(p))
    preview.exec()


def save_as_pdf(html: str, output_path: str):
    try:
        printer = _make_printer(output_path)
        _load_doc(html, printer).print_(printer)
        return True, output_path
    except Exception as e:
        return False, str(e)


def _is_current(s: dict) -> bool:
    status = s.get("student_status", None)
    return status is None or status == "current"


def _in_general_register(s: dict) -> bool:
    if (s.get("student_status") or "") == "passout":
        return True
    return is_grade_class_1_to_12(s.get("current_class"))


# ══════════════════════════════════════════════════════════════════
#  CERTIFICATE PAGE  (UI)
# ══════════════════════════════════════════════════════════════════

class CertificatePage(QWidget):
    def __init__(self, main_app):
        super().__init__()
        self.main_app          = main_app
        self.cert_type         = "LC"
        self._all_students     = []
        self._filtered         = []
        self._selected_student = None

        self.stack = QStackedWidget()
        self.stack.addWidget(self._page_select())
        self.stack.addWidget(self._page_search())

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stack)
        self.setLayout(layout)

    def _format_student_details(self, student: dict) -> str:
        """Return a formatted multiline string of student fields for display."""
        lines = []
        for key, value in student.items():
            lines.append(f"{key}: {value}")
        return "\n".join(lines)

    def open_lc_search(self, student: Optional[dict] = None):
        self._enter_search("LC")
        if not student:
            return

        target_id = student.get("id")
        if target_id is None:
            return

        for idx, row in enumerate(self._filtered):
            if row.get("id") == target_id:
                self.cert_list.setCurrentRow(idx)
                item = self.cert_list.item(idx)
                if item is not None:
                    self.cert_list.scrollToItem(item)
                break

    def _card(self, width=680):
        f = QFrame()
        f.setFixedWidth(width)
        f.setStyleSheet(
            "QFrame{background:white;border-radius:15px;border:1px solid #dce1e7;}"
        )
        return f

    def _btn(self, color, hover_color="#1a252f"):
        return (
            f"QPushButton{{background:{color};color:white;border-radius:10px;"
            f"padding:10px;font-size:14px;font-weight:bold;border:none;}}"
            f"QPushButton:hover{{background:{hover_color};}}"
            f"QPushButton:disabled{{background:{color};color:rgba(255,255,255,0.6);}}"
        )

    def _combo(self):
        return (
            "QComboBox{padding:7px;font-size:13px;border-radius:8px;"
            "border:1px solid #ccc;background:white;color:#123456;}"
            "QComboBox QAbstractItemView{background:white;color:#123456;"
            "selection-background-color:#123456;selection-color:white;}"
        )

    def _page_select(self):
        page   = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        card = self._card(600)
        c    = QVBoxLayout()
        c.setContentsMargins(35, 35, 35, 35)
        c.setSpacing(18)

        title = QLabel("📄 प्रमाणपत्र / Certificate Module")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color:#123456;background:transparent;")

        sub = QLabel("प्रमाणपत्र प्रकार निवडा / Select Certificate Type")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("color:#123456;font-size:15px;background:transparent;")

        lc_btn = QPushButton("📜  शाळा सोडल्याचे प्रमाणपत्र (LC)")
        lc_btn.setMinimumHeight(54)
        lc_btn.setStyleSheet(self._btn("#123456", "#123456"))
        lc_btn.clicked.connect(lambda: self._enter_search("LC"))

        bon_btn = QPushButton("📄  बोनाफाईड प्रमाणपत्र (Bonafide)")
        bon_btn.setMinimumHeight(54)
        bon_btn.setStyleSheet(self._btn("#123456", "#123456"))
        bon_btn.clicked.connect(lambda: self._enter_search("BON"))
        bon_btn.setVisible(True)  # Ensure button is visible

        info = QLabel(
            "📌 LC: सर्व विद्यार्थी मधून शोधा — वर्षाने फिल्टर\n"
            "    LC नंतर विद्यार्थी Passout होईल\n\n"
            "📌 Bonafide: फक्त वर्तमान विद्यार्थी — वर्ग/तुकडीने फिल्टर"
        )
        info.setAlignment(Qt.AlignCenter)
        info.setWordWrap(True)
        info.setStyleSheet(
            "color:#555;background:white;border-radius:8px;"
            "padding:14px;font-size:12px;"
        )

        # Add widgets to layout with explicit order
        c.addWidget(title)
        c.addWidget(sub)
        c.addWidget(lc_btn)
        c.addWidget(bon_btn)  # Ensure bonafide button is added
        c.addWidget(info)
        card.setLayout(c)
        layout.addWidget(card)
        page.setLayout(layout)
        return page

    def _page_search(self):
        page   = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        card = self._card(740)
        c    = QVBoxLayout()
        c.setContentsMargins(26, 22, 26, 22)
        c.setSpacing(10)

        self.search_title = QLabel("")
        self.search_title.setFont(QFont("Arial", 15, QFont.Bold))
        self.search_title.setAlignment(Qt.AlignCenter)
        self.search_title.setWordWrap(True)
        self.search_title.setStyleSheet("color:#123456;background:transparent;")
        c.addWidget(self.search_title)

        fr = QHBoxLayout()
        fr.setSpacing(8)
        fr.addWidget(QLabel("🔍"))
        self.cert_search = QLineEdit()
        self.cert_search.setPlaceholderText("नाव, Student ID, जन्मतारीख ने शोधा...")
        self.cert_search.setFixedHeight(36)
        self.cert_search.setStyleSheet(_SEARCH_STYLE)
        self.cert_search.textChanged.connect(self._filter_students)
        fr.addWidget(self.cert_search, 1)

        self.cert_year_lbl = QLabel("Year:")
        fr.addWidget(self.cert_year_lbl)
        self.cert_year_filter = QComboBox()
        self.cert_year_filter.setStyleSheet(self._combo())
        self.cert_year_filter.addItem("All Years")
        self.cert_year_filter.setFixedWidth(130)
        self.cert_year_filter.currentTextChanged.connect(self._filter_students)
        fr.addWidget(self.cert_year_filter)

        self.cert_class_lbl = QLabel("Class:")
        fr.addWidget(self.cert_class_lbl)
        self.cert_class_filter = QComboBox()
        self.cert_class_filter.setStyleSheet(self._combo())
        self.cert_class_filter.addItems(
            ["All"] + [str(i) for i in range(1, 13)])
        self.cert_class_filter.setFixedWidth(70)
        self.cert_class_filter.currentTextChanged.connect(self._filter_students)
        fr.addWidget(self.cert_class_filter)

        self.cert_div_lbl = QLabel("Div:")
        fr.addWidget(self.cert_div_lbl)
        self.cert_div_filter = QComboBox()
        self.cert_div_filter.setStyleSheet(self._combo())
        self.cert_div_filter.addItems(["All","A","B","C","D"])
        self.cert_div_filter.setFixedWidth(65)
        self.cert_div_filter.currentTextChanged.connect(self._filter_students)
        fr.addWidget(self.cert_div_filter)
        c.addLayout(fr)

        # Student list with improved scroll area
        self.cert_list = QListWidget()
        self.cert_list.setMinimumHeight(200)
        self.cert_list.setMaximumHeight(300)
        self.cert_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.cert_list.setStyleSheet("""
            QListWidget{
                border-radius:10px;
                border:1px solid #dce1e7;
                background:#fafafa;
                font-size:13px;
                color:#123456;
                padding:4px;
            }
            QListWidget::item{
                padding:8px;
                border-radius:5px;
                margin:1px;
            }
            QListWidget::item:selected{
                background:#d5f5e3;
                color:#123456;
            }
            QListWidget::item:hover{
                background:#e8f5e8;
            }
            QScrollBar:vertical {
                border: none;
                background: #f1f1f1;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #c1c1c1;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a8a8a8;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        self.cert_list.setVerticalScrollBarPolicy(SCROLLBAR_AS_NEEDED)
        self.cert_list.setHorizontalScrollBarPolicy(SCROLLBAR_ALWAYS_OFF)
        self.cert_list.currentRowChanged.connect(self._on_student_selected)
        
        # Wrap in scroll area for better scrolling behavior
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.cert_list)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(SCROLLBAR_AS_NEEDED)
        scroll_area.setHorizontalScrollBarPolicy(SCROLLBAR_ALWAYS_OFF)
        scroll_area.setMinimumHeight(200)
        scroll_area.setMaximumHeight(300)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #dce1e7;
                border-radius: 10px;
                background: #fafafa;
            }
        """)
        c.addWidget(scroll_area)



        self.cert_info_lbl = QLabel("")
        self.cert_info_lbl.setAlignment(Qt.AlignCenter)
        self.cert_info_lbl.setWordWrap(True)
        self.cert_info_lbl.setStyleSheet(
            "font-size:12px;font-weight:bold;color:#123456;background:transparent;"
        )
        c.addWidget(self.cert_info_lbl)

        self.cert_preview_btn = QPushButton("👁️  पूर्वावलोकन / Preview")
        self.cert_preview_btn.setMinimumHeight(44)
        self.cert_preview_btn.setStyleSheet(self._btn("#123456", "#123456"))
        self.cert_preview_btn.setEnabled(False)
        self.cert_preview_btn.clicked.connect(self._preview)
        c.addWidget(self.cert_preview_btn)

        self.lc_container = QWidget()
        self.lc_container.setStyleSheet("background:transparent;")
        lc_row = QHBoxLayout(self.lc_container)
        lc_row.setContentsMargins(0, 0, 0, 0)
        lc_row.setSpacing(8)

        self.gen_btn = QPushButton("📜  LC तयार करा / Generate 1st LC")
        self.gen_btn.setMinimumHeight(44)
        self.gen_btn.setStyleSheet(self._btn("#123456", "#123456"))
        self.gen_btn.setEnabled(False)
        self.gen_btn.clicked.connect(lambda: self._generate_lc(duplicate=False))
        lc_row.addWidget(self.gen_btn)

        self.dup_btn = QPushButton("🔁  Duplicate LC")
        self.dup_btn.setMinimumHeight(44)
        self.dup_btn.setStyleSheet(self._btn("#123456", "#123456"))
        self.dup_btn.setEnabled(False)
        self.dup_btn.clicked.connect(lambda: self._generate_lc(duplicate=True))
        lc_row.addWidget(self.dup_btn)
        c.addWidget(self.lc_container)

        self.bon_btn = QPushButton("📄  बोनाफाईड तयार करा / Generate Bonafide")
        self.bon_btn.setMinimumHeight(44)
        self.bon_btn.setStyleSheet(self._btn("#123456", "#123456"))
        self.bon_btn.setEnabled(False)
        self.bon_btn.clicked.connect(self._generate_bonafide)
        c.addWidget(self.bon_btn)

        self.cert_save_btn = QPushButton("💾  PDF जतन करा / Save as PDF")
        self.cert_save_btn.setMinimumHeight(44)
        self.cert_save_btn.setStyleSheet(self._btn("#123456", "#123456"))
        self.cert_save_btn.setEnabled(False)
        self.cert_save_btn.clicked.connect(self._save_pdf)
        c.addWidget(self.cert_save_btn)

        back = QPushButton("⬅️  मागे / Back")
        back.setMinimumHeight(38)
        back.setStyleSheet(self._btn("#123456", "#123456"))
        back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        c.addWidget(back)

        card.setLayout(c)
        layout.addWidget(card)
        page.setLayout(layout)
        return page

    def _reset_cert_buttons(self):
        """Reset all certificate buttons to disabled state."""
        self.cert_preview_btn.setEnabled(False)
        self.cert_save_btn.setEnabled(False)
        self.gen_btn.setEnabled(False)
        self.dup_btn.setEnabled(False)
        self.bon_btn.setEnabled(False)
        self.cert_info_lbl.setText("")

    def _refresh_student_data(self):
        """Refresh student data from database to show new records."""
        from db import get_all_students
        self._all_students = get_all_students()

    def _enter_search(self, typ: str):
        self.cert_type         = typ
        self._selected_student = None
        self.cert_search.clear()
        self._reset_cert_buttons()
        
        # Refresh data to show new records
        self._refresh_student_data()

        from db import get_academic_years

        if typ == "LC":
            self._all_students = [s for s in self._all_students if _in_general_register(s)]
            self.search_title.setText(
                "📜 LC — विद्यार्थी शोधा\n"
                "(सर्व विद्यार्थी — नाव / ID / जन्मतारीख)"
            )
            self.cert_year_lbl.setVisible(True)
            self.cert_year_filter.setVisible(True)
            self.cert_class_lbl.setVisible(False)
            self.cert_class_filter.setVisible(False)
            self.cert_div_lbl.setVisible(False)
            self.cert_div_filter.setVisible(False)
            years = get_academic_years()
            self.cert_year_filter.blockSignals(True)
            self.cert_year_filter.clear()
            self.cert_year_filter.addItem("All Years")
            self.cert_year_filter.addItems(years)
            self.cert_year_filter.blockSignals(False)
            self.lc_container.setVisible(True)
            self.bon_btn.setVisible(False)
        else:
            self._all_students = [
                s for s in self._all_students
                if _is_current(s) and is_grade_class_1_to_12(s.get("current_class"))
            ]
            self.search_title.setText(
                "📄 Bonafide — विद्यार्थी शोधा\n(केवळ वर्तमान विद्यार्थी)"
            )
            self.cert_year_lbl.setVisible(False)
            self.cert_year_filter.setVisible(False)
            self.cert_class_lbl.setVisible(True)
            self.cert_class_filter.setVisible(True)
            self.cert_div_lbl.setVisible(True)
            self.cert_div_filter.setVisible(True)
            self.cert_class_filter.setCurrentIndex(0)
            self.cert_div_filter.setCurrentIndex(0)
            self.lc_container.setVisible(False)
            self.bon_btn.setVisible(True)

        self._filter_students()
        self.stack.setCurrentIndex(1)

    def _filter_students(self):
        search   = self.cert_search.text().strip().lower()
        filtered = []

        for s in self._all_students:
            if self.cert_type == "LC":
                yr = self.cert_year_filter.currentText()
                if yr and yr != "All Years":
                    if (s.get("academic_year","") or "") != yr:
                        continue
            else:
                cls = self.cert_class_filter.currentText()
                div = self.cert_div_filter.currentText()
                fc  = s.get("current_class","") or ""
                if cls != "All" and not fc.startswith(f"{cls}-"): continue
                if div != "All" and not fc.endswith(f"-{div}"):   continue

            txt = (
                (s.get("name_mr") or "").lower() + " " +
                (s.get("student_id") or "").lower() + " " +
                (s.get("birth_date_num") or "").lower()
            )
            if search and search not in txt:
                continue
            filtered.append(s)

        self._filtered = filtered
        self.cert_list.clear()

        from db import get_lc_count, get_bonafide_count

        for s in filtered:
            name   = s.get("name_mr") or "Unknown"
            sid    = s.get("student_id","") or ""
            cls    = s.get("current_class","") or ""
            yr     = s.get("academic_year","") or ""

            if self.cert_type == "LC":
                lc     = get_lc_count(s["id"])
                badge  = f"  ✓ LC×{lc}" if lc > 0 else ""
                status = "Passout" if s.get("student_status") == "passout" else "Current"
                text   = (
                    f"{'🟠' if lc>0 else '🟢'}  {name}  "
                    f"[{sid}]  {cls}  {yr}{badge}  ({status})"
                )
                item = QListWidgetItem(text)
                if lc > 0:
                    item.setBackground(QColor("#fff3cd"))
                    item.setForeground(QColor("#7d4e00"))
            else:
                bon   = get_bonafide_count(s["id"])
                badge = f"  ✓ Bon×{bon}" if bon > 0 else ""
                text  = f"{'🟦' if bon>0 else '🟢'}  {name}  [{sid}]  {cls}{badge}"
                item  = QListWidgetItem(text)
                if bon > 0:
                    item.setBackground(QColor("#e8f4fd"))
            self.cert_list.addItem(item)

        self._selected_student = None
        self._reset_cert_buttons()

    def _on_student_selected(self, row: int):
        if row < 0 or row >= len(self._filtered):
            self._reset_cert_buttons()
            return

        # Set selected student and enable relevant buttons
        self._selected_student = self._filtered[row]
        self.cert_preview_btn.setEnabled(True)
        self.cert_save_btn.setEnabled(True)

        from db import get_lc_count, get_bonafide_count

        if self.cert_type == "LC":
            lc = get_lc_count(self._selected_student["id"])
            missing = validate_lc_fields(self._selected_student)
            if lc == 0:
                self.gen_btn.setEnabled(True)
                self.dup_btn.setEnabled(False)
                self.cert_info_lbl.setText(
                    f"⚠️  {len(missing)} रकाने रिकामे — Generate दाबल्यावर फॉर्म उघडेल."
                    if missing else
                    "ℹ️  सर्व माहिती भरली आहे. LC तयार करता येईल."
                )
            else:
                self.gen_btn.setEnabled(False)
                self.dup_btn.setEnabled(True)
                self.cert_info_lbl.setText(
                    f"⚠️  या विद्यार्थ्याचे आधीच {lc} LC तयार झाले आहे."
                )
        else:
            self.bon_btn.setEnabled(True)
            bon = get_bonafide_count(self._selected_student["id"])
            self.cert_info_lbl.setText(
                f"ℹ️  आधीच {bon} Bonafide तयार झाले आहे." if bon > 0 else ""
            )


    def _preview(self):
        if not self._selected_student:
            return
        html = self._build_preview_html()
        name = self._selected_student.get("name_mr","") or ""
        cert = "LC" if self.cert_type == "LC" else "Bonafide"
        show_preview(html, parent=self, title=f"{cert} पूर्वावलोकन — {name}")

    def _build_preview_html(self) -> str:
        if self.cert_type == "LC":
            from db import get_lc_count, get_lc_number_for_print
            cnt = get_lc_count(self._selected_student["id"])
            lc_no = get_lc_number_for_print(self._selected_student["id"])
            return build_lc_html(
                self._selected_student, copy_number=max(cnt, 1), lc_no=lc_no
            )
        return build_bonafide_html(self._selected_student)

    def _generate_lc(self, duplicate: bool = False):
        if not self._selected_student:
            return
        from db import (
            get_lc_count,
            increment_lc_count,
            get_all_students,
            get_lc_number_for_print,
        )

        student = self._selected_student
        missing = validate_lc_fields(student)
        if missing:
            updated = show_lc_fill_dialog(self, student, missing)
            if updated is None:
                return
            student = updated
            self._selected_student = updated

        lc_count    = get_lc_count(student["id"])
        copy_number = lc_count + 1
        lc_no       = get_lc_number_for_print(student["id"])
        html        = build_lc_html(student, copy_number=copy_number, lc_no=lc_no)
        name        = student.get("name_mr","") or ""

        show_preview(html, parent=self,
                     title=f"LC Print — Copy {copy_number} — {name}")

        confirm = QMessageBox.question(
            self, "✅ LC नोंद करा / Record LC?",
            "LC यशस्वीरित्या प्रिंट झाले का?\nWas the LC printed successfully?\n\n"
            "होय → LC नोंद होईल + विद्यार्थी Passout होईल\n"
            "Yes → Record LC + mark student as Passout",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            new_count = increment_lc_count(student["id"])
            mark_student_as_passout(
                student["id"], student.get("leaving_date","") or ""
            )
            QMessageBox.information(
                self, "✅ नोंद झाली / Recorded",
                f"LC Copy No. {new_count} नोंदवली गेली.\n"
                f"विद्यार्थी '{name}' आता Passout म्हणून नोंदला गेला आहे."
            )
            self._all_students = get_all_students()
            self._filter_students()

    def _generate_bonafide(self):
        if not self._selected_student:
            return
        html = build_bonafide_html(self._selected_student)
        name = self._selected_student.get("name_mr","") or ""
        show_preview(html, parent=self, title=f"Bonafide Print — {name}")

        confirm = QMessageBox.question(
            self, "✅ Bonafide नोंद करा / Record?",
            "Bonafide यशस्वीरित्या प्रिंट झाले का?\n\nहोय → नोंद होईल.",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            from db import increment_bonafide_count
            new_count = increment_bonafide_count(self._selected_student["id"])
            QMessageBox.information(
                self, "✅ नोंद झाली",
                f"Bonafide Copy No. {new_count} नोंदवली गेली."
            )
            self._filter_students()

    def _save_pdf(self):
        if not self._selected_student:
            return
        name       = (
            self._selected_student.get("name_mr","") or "student"
        ).replace(" ","_")
        cert_label = "LC" if self.cert_type == "LC" else "Bonafide"

        if self.cert_type == "LC":
            missing = validate_lc_fields(self._selected_student)
            if missing:
                updated = show_lc_fill_dialog(
                    self, self._selected_student, missing
                )
                if updated is None:
                    return
                self._selected_student = updated
            from db import get_lc_count
            from db import get_lc_number_for_print
            copy_number  = get_lc_count(self._selected_student["id"]) + 1
            lc_no        = get_lc_number_for_print(self._selected_student["id"])
            html         = build_lc_html(
                self._selected_student, copy_number=copy_number, lc_no=lc_no
            )
            default_name = f"{cert_label}_{name}_copy{copy_number}.pdf"
        else:
            html         = build_bonafide_html(self._selected_student)
            default_name = f"{cert_label}_{name}.pdf"

        save_path, _ = QFileDialog.getSaveFileName(
            self, f"{cert_label} PDF जतन करा",
            default_name, "PDF Files (*.pdf)"
        )
        if not save_path:
            return

        ok, result = save_as_pdf(html, save_path)
        if ok:
            reply = QMessageBox.question(
                self, "✅ जतन झाले / Saved",
                f"PDF जतन झाले!\nSaved at:\n{save_path}\n\n"
                f"आता उघडायचे का? / Open now?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                import subprocess
                if sys.platform == "win32":
                    os.startfile(save_path)
                elif sys.platform == "darwin":
                    subprocess.call(["open", save_path])
                else:
                    subprocess.call(["xdg-open", save_path])
        else:
            QMessageBox.critical(
                self, "❌ Error", f"PDF तयार झाले नाही!\n{result}"
            )
