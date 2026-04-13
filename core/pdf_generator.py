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

    def section_title(self, title: str):
        self.ln(6)
        self.set_fill_color(*DARK_BLUE)
        self.set_text_color(*WHITE)
        self.set_font("Alef", size=13)
        self.set_x(10)
        self.cell(190, 10, h(title), fill=True, align="R")
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
        """Render a single recommended role card with full detail."""
        self.ln(3)
        timeframe = role.get("timeframe", "short")
        color = TEAL if timeframe == "short" else DARK_BLUE
        label = "טווח קצר (עד 12 חודשים)" if timeframe == "short" else "טווח ארוך (1–3 שנים)"

        card_y = self.get_y()

        # ── Measure text height first to determine card height ──
        title = role.get("title_he", "")
        reasoning = role.get("reasoning_he") or role.get("why_good_fit_he") or role.get("description_he", "")
        why_desc = role.get("description_he", "") if role.get("reasoning_he") or role.get("why_good_fit_he") else ""
        skills_gap = role.get("skills_gap_he", [])
        fit_score = role.get("fit_score")
        market_demand = role.get("market_demand", "")
        demand_he = {"high": "גבוהה", "medium": "בינונית", "low": "נמוכה"}.get(market_demand, "")

        # Estimate card height
        reasoning_lines = max(1, len(reasoning) // 70 + 1)
        card_h = 14 + 8 + (reasoning_lines * 5) + (6 if why_desc else 0) + (8 if skills_gap else 0) + 4

        # Card background
        self.set_fill_color(*LIGHT_GRAY)
        self.rect(10, card_y, 190, card_h, "F")

        # Colored rank bar on right side
        self.set_fill_color(*color)
        self.rect(185, card_y, 15, card_h, "F")
        self.set_font("Alef", size=18)
        self.set_text_color(*WHITE)
        self.set_xy(186, card_y + card_h / 2 - 6)
        self.cell(13, 12, str(rank), align="C")

        # ── Title ──
        self.set_font("Alef", size=13)
        self.set_text_color(*DARK_BLUE)
        self.set_xy(12, card_y + 3)
        self.cell(168, 9, h(title), align="R")

        # ── Timeframe | Salary | Fit score ──
        self.set_font("Alef", size=9)
        self.set_text_color(*color)
        self.set_xy(12, card_y + 12)
        salary = role.get("salary_range_ils", "")
        parts = [label]
        if salary:
            parts.append(f"{salary} ₪")
        if fit_score:
            parts.append(f"התאמה: {fit_score}/10")
        if demand_he:
            parts.append(f"ביקוש: {demand_he}")
        self.cell(168, 5, h("  |  ".join(parts)), align="R")

        # ── Reasoning (why this role fits) ──
        self.set_font("Alef", size=9)
        self.set_text_color(*TEXT_GRAY)
        self.set_xy(12, card_y + 19)
        self.multi_cell(168, 5, h(reasoning), align="R")

        # ── Short description if separate ──
        if why_desc:
            self.set_font("Alef", size=8)
            self.set_text_color(120, 120, 120)
            self.set_x(12)
            self.multi_cell(168, 4, h(why_desc), align="R")

        # ── Skills gap ──
        if skills_gap:
            self.set_font("Alef", size=8)
            self.set_text_color(*DARK_BLUE)
            self.set_x(12)
            gap_text = "פערים לסגירה: " + " • ".join(str(s) for s in skills_gap[:3])
            self.cell(168, 5, h(gap_text), align="R")

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
        pdf.section_title("סיכום מנהלים")
        pdf.body_text(report["executive_summary_he"])

    # ── 5 Recommended Roles ───────────────────────────────────────────────────
    # Prefer dedicated recommended_roles; fall back to recommended_directions
    roles = report.get("recommended_roles", [])
    if not roles:
        directions = report.get("recommended_directions", [])
        for i, d in enumerate(directions[:5]):
            roles.append({
                "title_he": d.get("title_he", d.get("title", "")),
                "timeframe": "short" if i < 3 else "long",
                "reasoning_he": d.get("why_good_fit_he", ""),
                "description_he": d.get("description_he", ""),
                "salary_range_ils": d.get("salary_range_ils", ""),
                "fit_score": d.get("fit_score"),
                "market_demand": d.get("market_demand", ""),
                "skills_gap_he": d.get("skills_gap_he", []),
            })

    if roles:
        pdf.add_page()
        pdf.section_title("התפקידים המומלצים עבורך", "")
        pdf.ln(2)
        pdf.set_font("Alef", size=9)
        pdf.set_text_color(*TEXT_GRAY)
        pdf.set_x(15)
        pdf.cell(180, 5, h("תפקידים בטווח קצר ניתן להשיג תוך 12 חודשים. תפקידי טווח ארוך דורשים 1–3 שנות התפתחות."), align="R")
        pdf.ln(6)
        for i, role in enumerate(roles[:5], 1):
            if pdf.get_y() > 230:
                pdf.add_page()
            pdf.role_card(i, role)

    # ── Key Insights ──────────────────────────────────────────────────────────
    insights = report.get("insights", [])
    if insights:
        pdf.add_page()
        pdf.section_title("תובנות מרכזיות")
        for insight in insights[:4]:
            pdf.bullet(str(insight))
            pdf.ln(1)

    # ── Quick Wins ────────────────────────────────────────────────────────────
    quick_wins = report.get("quick_wins", [])
    if quick_wins:
        pdf.ln(4)
        pdf.section_title("פעולות מיידיות - לעשות השבוע")
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
