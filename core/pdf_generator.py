"""
Generates a client-facing PDF report with key career insights and recommended roles.
Uses fpdf2 + python-bidi for Hebrew RTL support.
"""
from __future__ import annotations
import io
import base64
from pathlib import Path
from datetime import date

from fpdf import FPDF
from bidi.algorithm import get_display

ASSETS = Path(__file__).parent.parent / "assets"
FONT_PATH = ASSETS / "Alef-Regular.ttf"
LOGO_PATH = ASSETS / "logo.png"

# Brand colors
DARK_BLUE = (10, 32, 61)
TEAL = (82, 196, 205)
LIGHT_GRAY = (242, 242, 242)
WHITE = (255, 255, 255)
TEXT_GRAY = (80, 80, 80)


def h(text: str) -> str:
    """Apply bidi algorithm for proper Hebrew RTL rendering."""
    if not text:
        return ""
    try:
        return get_display(str(text), base_dir="R")
    except Exception:
        return str(text)


class ReportPDF(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(auto=True, margin=20)
        self.add_font("Alef", style="", fname=str(FONT_PATH))
        self.set_font("Alef", size=12)
        self._client_name = ""

    def header(self):
        if self.page_no() == 1:
            return
        # Minimal header on subsequent pages
        self.set_fill_color(*DARK_BLUE)
        self.rect(0, 0, 210, 12, "F")
        self.set_font("Alef", size=8)
        self.set_text_color(*WHITE)
        self.set_xy(10, 3)
        self.cell(190, 6, h(f"CORE Blueprint — {self._client_name}"), align="R")
        self.set_text_color(0, 0, 0)
        self.ln(14)

    def footer(self):
        self.set_y(-15)
        self.set_font("Alef", size=8)
        self.set_text_color(*TEXT_GRAY)
        self.cell(0, 10, h(f"© 2026 יואב פלד — כל הזכויות שמורות  |  עמוד {self.page_no()}"), align="C")
        self.set_text_color(0, 0, 0)

    def cover_page(self, client_name: str, track_name: str):
        self._client_name = client_name
        self.add_page()

        # Dark blue background top block
        self.set_fill_color(*DARK_BLUE)
        self.rect(0, 0, 210, 100, "F")

        # Logo
        if LOGO_PATH.exists():
            self.image(str(LOGO_PATH), x=65, y=12, w=80)

        # Teal accent line
        self.set_fill_color(*TEAL)
        self.rect(0, 95, 210, 4, "F")

        # Client name
        self.set_xy(10, 108)
        self.set_font("Alef", size=22)
        self.set_text_color(*DARK_BLUE)
        self.cell(190, 12, h(f"דוח קריירה אישי — {client_name}"), align="C")
        self.ln(10)

        # Subtitle
        self.set_font("Alef", size=13)
        self.set_text_color(*TEAL)
        self.cell(190, 8, h("מסלול CORE Blueprint — ניתוח וכיוון מקצועי"), align="C")
        self.ln(8)

        # Track
        self.set_font("Alef", size=11)
        self.set_text_color(*TEXT_GRAY)
        self.cell(190, 6, h(f"מסלול מומלץ: {track_name}"), align="C")
        self.ln(4)
        self.cell(190, 6, h(f"תאריך: {date.today().strftime('%d.%m.%Y')}"), align="C")

        # Divider
        self.ln(16)
        self.set_draw_color(*TEAL)
        self.set_line_width(0.5)
        self.line(20, self.get_y(), 190, self.get_y())
        self.ln(10)

        # Intro paragraph
        self.set_font("Alef", size=10)
        self.set_text_color(*TEXT_GRAY)
        intro = h("דוח זה נוצר על בסיס הנתונים שמסרת בשאלון, ניתוח קורות החיים שלך, ומתודולוגיית CORE Blueprint של יואב פלד. הוא מיועד עבורך אישית ומכיל תובנות, כיוונים מומלצים ותפקידים שיכולים להתאים לפרופיל הייחודי שלך.")
        self.set_x(15)
        self.multi_cell(180, 6, intro, align="R")

    def section_title(self, title: str, icon: str = ""):
        self.ln(6)
        self.set_fill_color(*DARK_BLUE)
        self.set_text_color(*WHITE)
        self.set_font("Alef", size=13)
        full = h(f"{title}  {icon}") if icon else h(title)
        self.set_x(10)
        self.cell(190, 10, full, fill=True, align="R")
        self.set_text_color(0, 0, 0)
        self.ln(4)

    def body_text(self, text: str, indent: int = 15):
        self.set_font("Alef", size=10)
        self.set_text_color(*TEXT_GRAY)
        self.set_x(indent)
        self.multi_cell(210 - indent * 2, 6, h(text), align="R")
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def bullet(self, text: str):
        self.set_font("Alef", size=10)
        self.set_text_color(*TEXT_GRAY)
        self.set_x(15)
        self.cell(5, 6, "-")
        self.set_x(20)
        self.multi_cell(170, 6, h(text), align="R")
        self.set_text_color(0, 0, 0)

    def role_card(self, rank: int, role: dict):
        """Render a single recommended role card."""
        self.ln(4)
        timeframe = role.get("timeframe", "short")
        color = TEAL if timeframe == "short" else DARK_BLUE
        label = "טווח קצר" if timeframe == "short" else "טווח ארוך"

        # Card background
        self.set_fill_color(*LIGHT_GRAY)
        card_y = self.get_y()
        card_h = 38
        self.rect(10, card_y, 190, card_h, "F")

        # Rank circle (teal bar on right)
        self.set_fill_color(*color)
        self.rect(185, card_y, 15, card_h, "F")
        self.set_font("Alef", size=16)
        self.set_text_color(*WHITE)
        self.set_xy(186, card_y + card_h / 2 - 5)
        self.cell(13, 10, str(rank), align="C")

        # Title
        self.set_font("Alef", size=12)
        self.set_text_color(*DARK_BLUE)
        self.set_xy(10, card_y + 4)
        title = role.get("title_he", "")
        self.cell(170, 8, h(title), align="R")

        # Timeframe + salary
        self.set_font("Alef", size=9)
        self.set_text_color(*color)
        self.set_xy(10, card_y + 13)
        salary = role.get("salary_range_ils", "")
        tag = f"{label}  |  {salary} ₪" if salary else label
        self.cell(170, 6, h(tag), align="R")

        # Reasoning
        self.set_font("Alef", size=9)
        self.set_text_color(*TEXT_GRAY)
        self.set_xy(10, card_y + 20)
        reasoning = role.get("reasoning_he", role.get("description_he", ""))
        # Truncate if too long
        if len(reasoning) > 160:
            reasoning = reasoning[:157] + "..."
        self.multi_cell(170, 5, h(reasoning), align="R")

        self.set_y(card_y + card_h + 2)
        self.set_text_color(0, 0, 0)


def generate_client_pdf(report: dict, client_name: str) -> bytes:
    """Generate and return PDF bytes for client download."""
    pdf = ReportPDF()
    track_key = report.get("track", "A")
    track_name = report.get("track_reason_he", "")[:60] if report.get("track_reason_he") else ("מסלול א" if track_key == "A" else "מסלול ב")

    # ── Cover page ────────────────────────────────────────────────────────────
    pdf.cover_page(client_name, "מסלול A - שינוי קריירה" if track_key == "A" else "מסלול B - חוסן תעסוקתי")

    # ── Executive Summary ─────────────────────────────────────────────────────
    if report.get("executive_summary_he"):
        pdf.add_page()
        pdf.section_title("סיכום מנהלים", "📋")
        pdf.body_text(report["executive_summary_he"])

    # ── 5 Recommended Roles ───────────────────────────────────────────────────
    roles = report.get("recommended_roles", [])
    if roles:
        pdf.add_page()
        pdf.section_title("5 התפקידים המומלצים עבורך", "🎯")
        pdf.ln(2)
        pdf.set_font("Alef", size=9)
        pdf.set_text_color(*TEXT_GRAY)
        pdf.set_x(15)
        pdf.cell(180, 5, h("תפקידים בטווח קצר ניתן להשיג תוך 12 חודשים. תפקידי טווח ארוך דורשים 1-3 שנות התפתחות."), align="R")
        pdf.ln(6)
        for i, role in enumerate(roles[:5], 1):
            if pdf.get_y() > 240:
                pdf.add_page()
            pdf.role_card(i, role)

    # ── Key Insights ──────────────────────────────────────────────────────────
    insights = report.get("insights", [])
    if insights:
        pdf.add_page()
        pdf.section_title("תובנות מרכזיות", "🔍")
        for insight in insights[:4]:
            pdf.bullet(str(insight))
            pdf.ln(1)

    # ── Quick Wins ────────────────────────────────────────────────────────────
    quick_wins = report.get("quick_wins", [])
    if quick_wins:
        pdf.ln(4)
        pdf.section_title("פעולות מיידיות - לעשות השבוע", "⚡")
        for win in quick_wins[:3]:
            pdf.bullet(str(win))
            pdf.ln(1)

    # ── CORE Blueprint CTA ────────────────────────────────────────────────────
    pdf.ln(8)
    pdf.set_fill_color(*TEAL)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Alef", size=11)
    pdf.set_x(10)
    pdf.cell(190, 8, h("המסע מתחיל כאן — CORE Blueprint עם יואב פלד"), fill=True, align="C")
    pdf.ln(6)
    pdf.set_font("Alef", size=9)
    pdf.set_text_color(*TEXT_GRAY)
    pdf.set_x(15)
    pdf.multi_cell(180, 5, h("תהליך ה-CORE Blueprint מלווה אותך ב-10 מפגשים מובנים לבניית בהירות, כיוון ומנוף מקצועי. הדוח שלפניך הוא נקודת הפתיחה."), align="R")

    return bytes(pdf.output())
