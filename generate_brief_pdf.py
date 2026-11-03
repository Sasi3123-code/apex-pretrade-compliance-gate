"""
Generates the humanized 5-Page PDF (4-Page Written Brief + 1-Page Appendix)
at `c:/Tresata/TRESATA_WRITTEN_BRIEF.pdf` using `reportlab`, and validates layout
by rendering each page to PNG in `c:/Tresata/tmp/pdfs/` and checking extraction
via `pdfplumber` and `pypdf` (following `openai/skills/.curated/pdf/SKILL.md`).

Incorporates:
1. Exact Regulatory Precision: Distinguishes contractual Fund Mandate / IPS limits from
   compliance-program obligations under SEC Rule 206(4)-7 (Investment Advisers Act of 1940)
   and SEC Rule 38a-1 (Investment Company Act of 1940).
2. Full Financial & Operational Reconciliation: Explicitly separates incremental value added
   by our 4-step gate over the basic checker (2 unsafe approvals caught = +$102,000 unwind loss
   avoided; 1 false block corrected = +$82,500 spread cost avoided; 2 ambiguous trades escalated
   = $2.50M notional / $93,000 exposure held for CCO review) from the 3 baseline breaches caught
   by both systems ($98,000 baseline protection).
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import List

import pdfplumber
import pypdf
import pypdfium2 as pdfium
from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

# ---------------------------------------------------------------------------
# Brand Palette (AEGIS Warm Electric Orange + Slate + Cream)
# ---------------------------------------------------------------------------
ORANGE = colors.HexColor("#F04E14")
ORANGE_DARK = colors.HexColor("#C23805")
ORANGE_SOFT = colors.HexColor("#FFF4EE")

INK = colors.HexColor("#1D1D1F")
INK_2 = colors.HexColor("#3F3F46")
MUTED = colors.HexColor("#707075")
SURFACE = colors.HexColor("#F6F5F3")
BORDER = colors.HexColor("#E2E0DC")

GREEN = colors.HexColor("#11713F")
GREEN_BG = colors.HexColor("#EAFBF1")
RED = colors.HexColor("#C42329")
RED_BG = colors.HexColor("#FFF1F1")
AMBER = colors.HexColor("#92400E")
AMBER_BG = colors.HexColor("#FEF3C7")

PAGE_W, PAGE_H = A4
MARGIN_X = 12 * mm
MARGIN_TOP = 16 * mm
MARGIN_BOTTOM = 12 * mm
CONTENT_W = PAGE_W - 2 * MARGIN_X


def assert_ascii_safe(text: str) -> str:
    """Ensure only ASCII hyphens and characters are used per openai/skills/pdf/SKILL.md."""
    bad_chars = [ch for ch in text if ord(ch) > 127]
    if bad_chars:
        raise ValueError(f"Non-ASCII characters detected: {bad_chars} in {text[:80]!r}")
    return text


def p(text: str, style: ParagraphStyle) -> Paragraph:
    """Create an ASCII-verified ReportLab Paragraph."""
    return Paragraph(assert_ascii_safe(text), style)


def build_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "h1": ParagraphStyle(
            "H1",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10.0,
            leading=12.8,
            textColor=INK,
            spaceBefore=5,
            spaceAfter=2.5,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.25,
            leading=11.2,
            textColor=INK_2,
            alignment=TA_LEFT,
            spaceBefore=1.2,
            spaceAfter=2.6,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.15,
            leading=10.9,
            leftIndent=10,
            firstLineIndent=-7,
            textColor=INK_2,
            spaceBefore=0.8,
            spaceAfter=2.0,
        ),
        "callout": ParagraphStyle(
            "Callout",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.15,
            leading=11.0,
            textColor=INK,
        ),
        "th": ParagraphStyle(
            "TH",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=9.5,
            textColor=colors.white,
        ),
        "td": ParagraphStyle(
            "TD",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=7.45,
            leading=9.7,
            textColor=INK_2,
        ),
        "td_bold": ParagraphStyle(
            "TDBold",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.45,
            leading=9.7,
            textColor=INK,
        ),
        "badge_pass": ParagraphStyle(
            "BadgePass",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.1,
            leading=9.0,
            textColor=GREEN,
        ),
        "badge_breach": ParagraphStyle(
            "BadgeBreach",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.1,
            leading=9.0,
            textColor=RED,
        ),
        "badge_hold": ParagraphStyle(
            "BadgeHold",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.1,
            leading=9.0,
            textColor=AMBER,
        ),
        "badge_muted": ParagraphStyle(
            "BadgeMuted",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=7.1,
            leading=9.0,
            textColor=MUTED,
        ),
    }


def section_heading(title: str, tag: str, styles: dict[str, ParagraphStyle]) -> Table:
    """Render an AEGIS-styled section header with an orange square dot and right pill tag."""
    assert_ascii_safe(title)
    assert_ascii_safe(tag)
    dot = Drawing(8, 8)
    dot.add(Rect(0, 0.5, 6.5, 6.5, rx=1.5, ry=1.5, fillColor=ORANGE, strokeColor=None))
    left_p = Paragraph(f"<b>{title}</b>", styles["h1"])
    right_p = Paragraph(
        f'<font color="#C23805" size="7.3"><b>{tag}</b></font>',
        ParagraphStyle("RightTag", fontName="Helvetica-Bold", fontSize=7.3, alignment=2),
    )
    tbl = Table([[dot, left_p, right_p]], colWidths=[11, CONTENT_W - 135, 124])
    tbl.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
                ("LINEBELOW", (0, 0), (-1, 0), 0.8, BORDER),
            ]
        )
    )
    return tbl


def callout_box(text: str, styles: dict[str, ParagraphStyle], bg=ORANGE_SOFT, bar=ORANGE) -> Table:
    """Create a warm callout box with a thick left accent bar."""
    para = p(text, styles["callout"])
    tbl = Table([[para]], colWidths=[CONTENT_W])
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), bg),
                ("LINEBEFORE", (0, 0), (0, -1), 3.2, bar),
                ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 4.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
            ]
        )
    )
    return tbl


def draw_hero_banner() -> Drawing:
    """Draw the Page 1 AEGIS Warm Electric Orange Hero Band with Auditable Operational Metrics."""
    d = Drawing(CONTENT_W, 92)
    d.add(Rect(0, 0, CONTENT_W, 92, rx=8, ry=8, fillColor=ORANGE, strokeColor=ORANGE_DARK, strokeWidth=0.6))
    d.add(
        Rect(
            CONTENT_W - 148,
            69,
            134,
            15,
            rx=7,
            ry=7,
            fillColor=ORANGE_DARK,
            strokeColor=colors.HexColor("#FF8C61"),
            strokeWidth=0.5,
        )
    )
    d.add(
        String(
            CONTENT_W - 140,
            74,
            "10 / 10 ACCURACY vs 5 / 10 BASELINE",
            fontName="Helvetica-Bold",
            fontSize=6.6,
            fillColor=colors.white,
        )
    )

    d.add(
        String(
            14,
            75,
            "APEX PRE-TRADE COMPLIANCE GATE  |  INVESTMENT MANDATE & COMPLIANCE CONTROLS",
            fontName="Helvetica-Bold",
            fontSize=6.8,
            fillColor=colors.HexColor("#FFE4D6"),
        )
    )
    d.add(
        String(
            14,
            56,
            "2 Unsafe Approvals Caught  |  1 False Block Fixed  |  2 Gray Areas Escalated",
            fontName="Helvetica-Bold",
            fontSize=13.2,
            fillColor=colors.white,
        )
    )
    d.add(
        String(
            14,
            43,
            "Incremental value over basic checks: +$184,500 direct loss/cost avoided + $93,000 ambiguous exposure held for CCO review.",
            fontName="Helvetica",
            fontSize=7.85,
            fillColor=colors.HexColor("#FFF4EE"),
        )
    )

    cards = [
        ("+$102,000", "2 Hidden Breaches Blocked (TC-03/05)"),
        ("+$82,500", "1 False Block Fixed (TC-04 Ford)"),
        ("$93,000 Held", "2 Footnote Risks Held (TC-09/10)"),
        ("$98,000 Base", "3 Standard Breaches Caught by Both"),
    ]
    card_w = (CONTENT_W - 28 - 3 * 8) / 4.0
    for idx, (val, lbl) in enumerate(cards):
        cx = 14 + idx * (card_w + 8)
        d.add(
            Rect(
                cx,
                6,
                card_w,
                30,
                rx=5,
                ry=5,
                fillColor=colors.HexColor("#B83203"),
                strokeColor=colors.HexColor("#FF8C61"),
                strokeWidth=0.5,
            )
        )
        d.add(String(cx + 7, 21, val, fontName="Helvetica-Bold", fontSize=9.8, fillColor=colors.white))
        d.add(String(cx + 7, 10.5, lbl, fontName="Helvetica", fontSize=6.15, fillColor=colors.HexColor("#FFE4D6")))
    return d


def draw_architecture_diagram() -> Drawing:
    """Draw the 4-Step Hybrid Compliance Architecture & 4-Dashboard UI Flow."""
    d = Drawing(CONTENT_W, 136)
    d.add(Rect(0, 0, CONTENT_W, 136, rx=8, ry=8, fillColor=SURFACE, strokeColor=BORDER, strokeWidth=0.7))

    # Left Input Boxes (x=8..116, w=108)
    d.add(Rect(8, 74, 108, 52, rx=5, ry=5, fillColor=colors.white, strokeColor=BORDER, strokeWidth=0.8))
    d.add(String(13, 112, "1. Proposed Order Ticket", fontName="Helvetica-Bold", fontSize=7.5, fillColor=INK))
    d.add(String(13, 100, "- Company & Parent ID", fontName="Helvetica", fontSize=6.9, fillColor=INK_2))
    d.add(String(13, 90, "- Amount, Ratings, CCY", fontName="Helvetica", fontSize=6.9, fillColor=INK_2))
    d.add(String(13, 80, "- Deal Footnotes & Riders", fontName="Helvetica", fontSize=6.9, fillColor=INK_2))

    d.add(Rect(8, 12, 108, 52, rx=5, ry=5, fillColor=colors.white, strokeColor=BORDER, strokeWidth=0.8))
    d.add(String(13, 50, "2. Portfolio & Mandate", fontName="Helvetica-Bold", fontSize=7.5, fillColor=INK))
    d.add(String(13, 38, "- $100M Settled Holdings", fontName="Helvetica", fontSize=6.9, fillColor=INK_2))
    d.add(String(13, 28, "- fund_schema.yaml Pruner", fontName="Helvetica", fontSize=6.9, fillColor=INK_2))
    d.add(String(13, 18, "- Mandate IPS-APEX-2026-V4", fontName="Helvetica", fontSize=6.9, fillColor=INK_2))

    # Step 1 & Step 2 (x=128..270, w=142)
    d.add(Rect(128, 74, 142, 52, rx=5, ry=5, fillColor=ORANGE_SOFT, strokeColor=ORANGE, strokeWidth=1.0))
    d.add(String(134, 112, "Step 1: Mandate Search (Exact)", fontName="Helvetica-Bold", fontSize=7.5, fillColor=ORANGE_DARK))
    d.add(String(134, 100, "- BM25 + TF-IDF Keyword Search", fontName="Helvetica", fontSize=6.9, fillColor=INK))
    d.add(String(134, 90, "- Auto-follows linked definitions", fontName="Helvetica", fontSize=6.9, fillColor=INK))
    d.add(String(134, 80, "- Saves exact character offsets", fontName="Helvetica", fontSize=6.9, fillColor=ORANGE_DARK))

    d.add(Rect(128, 12, 142, 52, rx=5, ry=5, fillColor=GREEN_BG, strokeColor=GREEN, strokeWidth=1.0))
    d.add(String(134, 50, "Step 2: Exact Limit Calculator", fontName="Helvetica-Bold", fontSize=7.5, fillColor=GREEN))
    d.add(String(134, 38, "- Strips private account columns", fontName="Helvetica", fontSize=6.9, fillColor=INK))
    d.add(String(134, 28, "- Sums parent-company holdings", fontName="Helvetica", fontSize=6.9, fillColor=INK))
    d.add(String(134, 18, "- Resolves split credit ratings", fontName="Helvetica", fontSize=6.9, fillColor=GREEN))

    # Step 3 & Step 4 (x=282..416, w=134)
    d.add(Rect(282, 74, 134, 52, rx=5, ry=5, fillColor=colors.white, strokeColor=INK, strokeWidth=0.9))
    d.add(String(288, 112, "Step 3: Deal Note Reader (AI)", fontName="Helvetica-Bold", fontSize=7.5, fillColor=INK))
    d.add(String(288, 100, "- Reads unstructured footnotes", fontName="Helvetica", fontSize=6.9, fillColor=INK_2))
    d.add(String(288, 90, "- Flags hidden coal/SPV traps", fontName="Helvetica", fontSize=6.9, fillColor=INK_2))
    d.add(String(288, 80, "- Never touches portfolio math", fontName="Helvetica", fontSize=6.9, fillColor=ORANGE_DARK))

    d.add(Rect(282, 12, 134, 52, rx=5, ry=5, fillColor=AMBER_BG, strokeColor=AMBER, strokeWidth=1.0))
    d.add(String(288, 50, "Step 4: Final Safety Lock", fontName="Helvetica-Bold", fontSize=7.5, fillColor=AMBER))
    d.add(String(288, 38, "- Verifies exact mandate quote", fontName="Helvetica", fontSize=6.9, fillColor=INK))
    d.add(String(288, 28, "- AI can NEVER override a breach", fontName="Helvetica", fontSize=6.9, fillColor=INK))
    d.add(String(288, 18, "- Routes gray areas to Officer", fontName="Helvetica", fontSize=6.9, fillColor=AMBER))

    # Right Output Pills (x=430..518, w=88)
    d.add(Rect(430, 90, 88, 36, rx=5, ry=5, fillColor=GREEN_BG, strokeColor=GREEN, strokeWidth=1.0))
    d.add(String(437, 111, "APPROVED", fontName="Helvetica-Bold", fontSize=7.6, fillColor=GREEN))
    d.add(String(437, 98, "Safe to execute", fontName="Helvetica", fontSize=6.8, fillColor=INK_2))

    d.add(Rect(430, 50, 88, 36, rx=5, ry=5, fillColor=RED_BG, strokeColor=RED, strokeWidth=1.0))
    d.add(String(437, 71, "BLOCKED", fontName="Helvetica-Bold", fontSize=7.6, fillColor=RED))
    d.add(String(437, 58, "Stopped pre-trade", fontName="Helvetica", fontSize=6.8, fillColor=INK_2))

    d.add(Rect(430, 10, 88, 36, rx=5, ry=5, fillColor=AMBER_BG, strokeColor=AMBER, strokeWidth=1.0))
    d.add(String(437, 31, "HELD (CCO)", fontName="Helvetica-Bold", fontSize=7.6, fillColor=AMBER))
    d.add(String(437, 18, "Officer sign-off", fontName="Helvetica", fontSize=6.8, fillColor=INK_2))

    # Connectors
    for y_pos in (100, 38):
        d.add(Line(116, y_pos, 128, y_pos, strokeColor=INK_2, strokeWidth=1.0))
    d.add(Line(270, 100, 282, 100, strokeColor=INK_2, strokeWidth=1.0))
    d.add(Line(270, 38, 282, 38, strokeColor=INK_2, strokeWidth=1.0))
    d.add(Line(349, 74, 349, 64, strokeColor=INK_2, strokeWidth=1.0))
    d.add(Line(416, 38, 430, 108, strokeColor=GREEN, strokeWidth=1.0))
    d.add(Line(416, 38, 430, 68, strokeColor=RED, strokeWidth=1.0))
    d.add(Line(416, 38, 430, 28, strokeColor=AMBER, strokeWidth=1.0))
    return d


def draw_savings_chart() -> Drawing:
    """Draw a fully reconciled horizontal breakdown separating Incremental Value vs. Escalated vs. Baseline."""
    d = Drawing(CONTENT_W, 96)
    d.add(Rect(0, 0, CONTENT_W, 96, rx=7, ry=7, fillColor=SURFACE, strokeColor=BORDER, strokeWidth=0.7))
    d.add(
        String(
            12,
            80,
            "RECONCILIATION OF PRE-TRADE PROTECTION ACROSS ALL 10 TEST CASES (INCREMENTAL vs. ESCALATED vs. BASELINE)",
            fontName="Helvetica-Bold",
            fontSize=7.3,
            fillColor=INK,
        )
    )

    rows = [
        ("1. Incremental Unwind Loss Avoided (TC-03 $68k + TC-05 $34k caught by gate)", 102000, "+$102,000 (Realized)", ORANGE),
        ("2. Incremental False-Block Cost Avoided (TC-04 Ford split-rating fixed by gate)", 82500, "+$82,500 (Realized)", GREEN),
        ("3. Ambiguous Exposure Held for CCO Review (TC-09 $41k + TC-10 $52k escalated)", 93000, "$93,000 (Held for CCO)", AMBER),
        ("4. Baseline Breaches Blocked by Both (TC-02 $45k + TC-07 $38k + TC-08 $15k)", 98000, "$98,000 (Baseline)", MUTED),
    ]
    max_val = 120000.0
    bar_x = 286.0
    bar_max_w = 124.0
    for idx, (label, val, val_txt, col) in enumerate(rows):
        y = 62 - idx * 17
        d.add(String(12, y, label, fontName="Helvetica", fontSize=7.0, fillColor=INK_2))
        d.add(Rect(bar_x, y - 1, bar_max_w, 7.5, rx=3, ry=3, fillColor=BORDER, strokeColor=None))
        w = (val / max_val) * bar_max_w
        d.add(Rect(bar_x, y - 1, w, 7.5, rx=3, ry=3, fillColor=col, strokeColor=None))
        d.add(String(418, y, val_txt, fontName="Helvetica-Bold", fontSize=7.15, fillColor=INK))
    return d


def draw_page_chrome(canvas, doc):
    """Draw consistent top header bar and bottom footer on every page."""
    canvas.saveState()
    page_num = canvas.getPageNumber()

    canvas.setFillColor(ORANGE)
    canvas.rect(MARGIN_X, PAGE_H - 10 * mm, CONTENT_W, 1.6, fill=1, stroke=0)

    canvas.setFont("Helvetica-Bold", 7.2)
    canvas.setFillColor(INK)
    if page_num < 5:
        canvas.drawString(
            MARGIN_X,
            PAGE_H - 13.2 * mm,
            "APEX PRE-TRADE COMPLIANCE GATE  |  INVESTMENT MANDATE & COMPLIANCE CONTROLS",
        )
    else:
        canvas.drawString(
            MARGIN_X,
            PAGE_H - 13.2 * mm,
            "APPENDIX: WHAT I ADDED BEYOND THE AI  |  TRESATA WRITTEN BRIEF",
        )

    canvas.setFont("Helvetica", 7.2)
    canvas.setFillColor(MUTED)
    canvas.drawRightString(PAGE_W - MARGIN_X, PAGE_H - 13.2 * mm, "Darla Venkata Sasi Kumar (IIT Madras EP23B026)")

    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.6)
    canvas.line(MARGIN_X, 9.5 * mm, PAGE_W - MARGIN_X, 9.5 * mm)

    canvas.setFont("Helvetica", 7.2)
    canvas.setFillColor(MUTED)
    canvas.drawString(MARGIN_X, 6.2 * mm, "Prototype: app.py (4-Dashboard Orange Edition) & evaluate_10_cases.py")
    canvas.drawRightString(PAGE_W - MARGIN_X, 6.2 * mm, f"Page {page_num} of 5")
    canvas.restoreState()


def build_pdf(pdf_path: Path) -> None:
    styles = build_styles()
    doc = BaseDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=MARGIN_X,
        rightMargin=MARGIN_X,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
        title="Apex Pre-Trade Compliance Gate - Investment Mandate Enforcement & Compliance Controls",
        author="Darla Venkata Sasi Kumar",
    )
    frame = Frame(
        MARGIN_X,
        MARGIN_BOTTOM,
        CONTENT_W,
        PAGE_H - MARGIN_TOP - MARGIN_BOTTOM,
        id="main_frame",
        topPadding=0,
        bottomPadding=0,
        leftPadding=0,
        rightPadding=0,
    )
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=draw_page_chrome)])

    story: List = []

    # =========================================================================
    # PAGE 1: AREA EXPLORED, SURPRISES & THE REAL-WORLD PROBLEM
    # =========================================================================
    story.append(draw_hero_banner())
    story.append(Spacer(1, 5))

    story.append(section_heading("1. The Area I Explored & Three Things That Surprised Me", "Domain Discovery", styles))
    story.append(
        p(
            "When I interned as a Software Engineer at <b>Apollo Global Management</b>, I built data delivery pipelines and "
            "dashboards across <b>75,000+ holdings and 20,000+ trade records</b>, along with a natural-language query assistant "
            "for portfolio data. That experience got me interested in a deceptively simple question: <i>what actually happens in "
            "the 60 seconds between a portfolio manager clicking 'Buy' and the order hitting the market?</i> When I explored "
            "institutional <b>Investment Policy Statements (IPS)</b>, SEC Form N-1A registration statements, and compliance-program "
            "controls for this project, three things genuinely surprised me:",
            styles["body"],
        )
    )
    story.append(
        p(
            "<b>1. A rule on Page 12 is defined on Page 2:</b> In a fund's Investment Policy Statement, a limit looks straightforward "
            "at first glance -- for example, a synthetic fund mandate limit of <i>'No more than 5.00% of Fund NAV in any single issuer'</i> "
            "(Section 3.01a). But if you flip back to Section 1.04, 'Single Issuer' is redefined to aggregate every majority-owned "
            "subsidiary sharing an ultimate parent company. And if S&amp;P rates a bond BBB- (Investment Grade) while Moody's rates "
            "it Ba1 (High-Yield), Section 2.02b specifies that the higher rating governs. Reading the limit paragraph without pulling "
            "the cross-referenced definition paragraph gives the wrong answer.",
            styles["bullet"],
        )
    )
    story.append(
        p(
            "<b>2. Holding a stock above 5% is compliant, but buying $1 more violates the mandate:</b> If NVIDIA rallies and grows "
            "to 5.15% of the fund on its own (passive market drift), standard Market Drift Cure Provisions (Section 3.03) allow the "
            "fund to keep holding it passively. However, executing even a $50,000 active BUY order while NVIDIA sits above 5.00% "
            "is an immediate active-purchase breach.",
            styles["bullet"],
        )
    )
    story.append(
        p(
            "<b>3. Why neither SQL rules nor raw LLMs can do this alone:</b> Traditional database checks are great at summing "
            "columns, but they cannot read a 3-sentence deal footnote warning that a rail company gets 22% of its revenue from "
            "mixed coal corridors, or that a Cayman Islands trust is backed by an undisclosed oil-and-gas swap basket. Conversely, "
            "pasting 75,000 holdings rows into an LLM burns ~3.6 million tokens, leaks private custodian account numbers, and "
            "routinely fumbles parent-company joins and basis-point math.",
            styles["bullet"],
        )
    )

    story.append(
        section_heading(
            "2. The Problem We Solve & Regulatory Compliance Context",
            "Mandate Controls",
            styles,
        )
    )
    story.append(
        callout_box(
            "<b>Why Pre-Trade Mandate Enforcement Matters:</b> If a trade violates the fund's investment mandate, it can create "
            "a mandate breach, trigger costly trade unwinding and remediation, and expose the adviser to compliance and fiduciary "
            "risks (including reimbursing the fund for resulting unwind losses). The firm's compliance program -- including its "
            "written controls under <b>SEC Rule 206(4)-7</b> (under the Investment Advisers Act of 1940 for registered investment "
            "advisers) and <b>SEC Rule 38a-1</b> (under the Investment Company Act of 1940 for registered investment companies) -- "
            "must be designed to prevent, detect, and address such mandate violations before execution.",
            styles,
        )
    )
    story.append(Spacer(1, 2.5))
    story.append(
        p(
            "<b>- Who uses this &amp; how often:</b> Pre-trade compliance officers and middle-office desks at multi-asset credit and "
            "equity funds ($500M to $50B AUM), screening <b>50 to 300+ proposed allocation tickets every trading day</b> against fund-specific "
            "IPS limits, prospectus disclosures (Form N-1A), and institutional client side letters.",
            styles["bullet"],
        )
    )
    story.append(
        p(
            "<b>- What it costs today:</b> Checking a complex bond or swap across PDF rulebooks and side letters takes <b>15 to 30 "
            "minutes of manual lookup</b>. Missing a parent-group link or sub-cap forces an open-market trade unwind (costing "
            "3% to 5% in bid-ask/illiquidity slippage plus external review fees), while misreading a split-rating rule causes "
            "false blocks on valid trades (costing ~55 bps in replacement spread).",
            styles["bullet"],
        )
    )
    story.append(
        p(
            "<b>- Why now:</b> As private credit and bespoke Separately Managed Accounts (SMAs) grow, firms manage hundreds of "
            "custom client mandates. Hard-coding every new prose side letter into legacy SQL engines takes 3 to 6 weeks. Combining "
            "exact Python portfolio math with a constrained AI footnote reader cuts verification to seconds with zero math drift.",
            styles["bullet"],
        )
    )

    scope_tbl = Table(
        [
            [
                p("<b>What Is In Scope (Pre-Trade Mandate Gate)</b>", styles["th"]),
                p("<b>What Is Explicitly Out of Scope</b>", styles["th"]),
            ],
            [
                p(
                    "- Exact post-trade NAV % math across direct issuers and parent groups (Sec 1.04 / 3.01) under synthetic IPS thresholds.<br/>"
                    "- Split credit rating tie-breakers (Sec 2.02b), High-Yield Energy sub-limits (3.02b), and OECD sovereign FX carve-outs (4.01b).<br/>"
                    "- Screening deal footnotes for coal freight ambiguity (5.01b) and orphan SPV swaps (5.02), and auditing incremental loss avoidance.",
                    styles["td"],
                ),
                p(
                    "- Broker order-book routing, execution slicing, and FIX protocol market connectivity.<br/>"
                    "- Post-trade T+1 custodian bank wire settlement and cash reconciliation.<br/>"
                    "- Predicting security returns or offering automated legal advice without CCO review.",
                    styles["td"],
                ),
            ],
        ],
        colWidths=[CONTENT_W / 2.0, CONTENT_W / 2.0],
    )
    scope_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 0), INK),
                ("BACKGROUND", (1, 0), (1, 0), ORANGE_DARK),
                ("BACKGROUND", (0, 1), (-1, 1), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 3.8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3.8),
            ]
        )
    )
    story.append(Spacer(1, 2))
    story.append(scope_tbl)
    story.append(PageBreak())

    # =========================================================================
    # PAGE 2: SOLUTION DESIGN, KNOWLEDGE BOUNDARIES & 4-DASHBOARD PROTOTYPE
    # =========================================================================
    story.append(section_heading("2.1 How the System Works: Exact Math First, AI Reading Second", "4-Step Pipeline", styles))
    story.append(
        p(
            "The core design principle of our system is simple: <b>never let a language model do portfolio arithmetic, and never "
            "expect a SQL query to read a legal footnote</b>. In <code>src/agent_graph.py</code>, every proposed trade passes "
            "through four distinct steps where exact calculation and AI reading are kept strictly separate:",
            styles["body"],
        )
    )
    story.append(Spacer(1, 2))
    story.append(draw_architecture_diagram())
    story.append(Spacer(1, 4))

    story.append(section_heading("2.2 Where Knowledge Lives & How Rules Stay Up to Date", "System Boundaries", styles))
    boundary_tbl = Table(
        [
            [
                p("<b>System Step</b>", styles["th"]),
                p("<b>Exact or AI?</b>", styles["th"]),
                p("<b>Where Knowledge Lives</b>", styles["th"]),
                p("<b>Why It Works &amp; How We Verify It</b>", styles["th"]),
            ],
            [
                p("<b>1. Mandate Search</b><br/>(<code>src/retriever.py</code>)", styles["td"]),
                p("<b>100% Exact</b><br/>(BM25 + Graph)", styles["td_bold"]),
                p("Versioned mandate file (<code>fund_mandate_ips.md</code>)", styles["td"]),
                p("Finds exact section numbers and automatically pulls linked definitions (e.g., Sec 3.01 -> Sec 1.04) with character offsets.", styles["td"]),
            ],
            [
                p("<b>2. Limit Calculator</b><br/>(<code>deterministic_engine.py</code>)", styles["td"]),
                p("<b>100% Exact</b><br/>(Python Math)", styles["td_bold"]),
                p("<code>holdings_nport.json</code> + <code>fund_schema.yaml</code>", styles["td"]),
                p("Strips private account numbers locally (99.993% token cut) and calculates exact parent-group, credit, and currency percentages.", styles["td"]),
            ],
            [
                p("<b>3. Footnote Reader</b><br/>(<code>src/agent_graph.py</code>)", styles["td"]),
                p("<b>Probabilistic</b><br/>(OpenRouter LLM)", styles["td_bold"]),
                p("Retrieved IPS clauses + deal supplement notes", styles["td"]),
                p("Reads unstructured deal prose to spot gray areas (mixed coal rail corridors in Sec 5.01b or opaque Cayman SPVs in Sec 5.02).", styles["td"]),
            ],
            [
                p("<b>4. Final Safety Gate</b><br/>(<code>src/agent_graph.py</code>)", styles["td"]),
                p("<b>100% Exact</b><br/>(State Lock)", styles["td_bold"]),
                p("<code>verify_verbatim_quote()</code> + Asymmetric Lock", styles["td"]),
                p("Checks that the cited quote exists character-for-character in the mandate. The AI can never turn a math breach into an approval.", styles["td"]),
            ],
        ],
        colWidths=[98, 72, 118, CONTENT_W - 288],
    )
    boundary_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), INK),
                ("BACKGROUND", (0, 1), (-1, 1), colors.white),
                ("BACKGROUND", (0, 2), (-1, 2), SURFACE),
                ("BACKGROUND", (0, 3), (-1, 3), colors.white),
                ("BACKGROUND", (0, 4), (-1, 4), SURFACE),
                ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 3.3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3.3),
            ]
        )
    )
    story.append(boundary_tbl)
    story.append(Spacer(1, 2.5))

    story.append(
        p(
            "<b>- What happens when a fund mandate rule is amended or expires:</b> No rules or limits are baked into model weights. "
            "Every contractual threshold lives in <code>fund_schema.yaml</code> and <code>fund_mandate_ips.md</code> (tagged with "
            "Document ID <code>IPS-APEX-2026-V4</code>). When a fund board amends an IPS cap or adds a client side letter, updating "
            "the file immediately updates Step 1 and Step 2 with zero retraining. Past audit logs remain bound to the Mandate ID "
            "active at trade time (supporting annual compliance reviews under Advisers Act Rule 206(4)-7 and 1940 Act Rule 38a-1).",
            styles["bullet"],
        )
    )
    story.append(
        p(
            "<b>- Adapting to another regulatory regime (e.g., EU UCITS or India SEBI):</b> Our testbed models a US institutional "
            "fund mandate alongside SEC Form N-1A/N-PORT schemas. Moving to European UCITS funds (which enforce statutory '5/10/40' "
            "issuer concentration rules) requires only swapping the mandate file and adding a 4-line summation check in Step 2.",
            styles["bullet"],
        )
    )

    story.append(section_heading("2.3 The 4-Dashboard Prototype (Plain-English Orange Edition)", "Frontend Design", styles))
    story.append(
        p(
            "Compliance officers should not have to read raw JSON or backend code on screen. Modeled after the <b>AEGIS</b> visual "
            "system and <b>Emil Kowalski's</b> motion engineering principles, our Streamlit app (<code>app.py</code>) uses a "
            "<b>Warm Electric Orange (<code>#F04E14</code>)</b> theme and organizes the workflow into four plain-English dashboards:",
            styles["body"],
        )
    )
    dash_tbl = Table(
        [
            [
                p("<b>01 - Pre-Trade Gate</b>", styles["td_bold"]),
                p("Features the signature 'Needs You' Split-Card with 30px tabular numerals (<i>Before trade -> After trade</i>), a 2-segment overshoot bar showing the exact red breach segment past the limit tick mark, a 4-step pulsing checkpoint stepper, a conic-gradient score ring, and a What-If simulator.", styles["td"]),
            ],
            [
                p("<b>02 - Losses vs. Savings</b>", styles["td_bold"]),
                p("Separates <b>Incremental Value Added by Our Gate (+$184,500 realized across TC-03, TC-04, TC-05)</b> from <b>Ambiguous Exposure Held for CCO Review ($93,000 in TC-09, TC-10)</b> and <b>Baseline Protection ($98,000 caught by both systems in TC-02, TC-07, TC-08)</b>.", styles["td"]),
            ],
            [
                p("<b>03 - All Activity &amp; Protection</b>", styles["td_bold"]),
                p("A dedicated visual Bento dashboard across all 10 orders ($10.70M screened: 3 approved, 5 blocked, 2 held for CCO review), complete with an outcome donut ring, interactive decision filters, inline SVG icons, and transparent per-trade attribution.", styles["td"]),
            ],
            [
                p("<b>04 - Fund Portfolio ($100M)</b>", styles["td_bold"]),
                p("Displays the $100.0M settled Form N-PORT portfolio ($82.35M across 12 holdings + $17.65M cash) with parent-group concentration bars, 5.00% IPS limit markers, and passive market-drift indicators (e.g., NVIDIA at 5.15%).", styles["td"]),
            ],
        ],
        colWidths=[115, CONTENT_W - 115],
    )
    dash_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), ORANGE_SOFT),
                ("BACKGROUND", (1, 0), (1, -1), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 3.0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3.0),
            ]
        )
    )
    story.append(dash_tbl)
    story.append(PageBreak())

    # =========================================================================
    # PAGE 3: REJECTED ALTERNATIVES, WEAKEST POINT & RISK GOVERNANCE
    # =========================================================================
    story.append(section_heading("3.1 Four Approaches We Tested and Rejected", "Architectural Trade-Offs", styles))
    story.append(
        p(
            "Before settling on our 4-step hybrid design, we evaluated four common ways teams try to build compliance tools and "
            "rejected each one for specific, practical reasons:",
            styles["body"],
        )
    )
    rej_tbl = Table(
        [
            [
                p("<b>Rejected Approach</b>", styles["th"]),
                p("<b>Why It Fails on Real Institutional Trades</b>", styles["th"]),
            ],
            [
                p("<b>1. One Big LLM Call Over All Holdings + Mandate</b>", styles["td_bold"]),
                p("Sending 75,000 holdings rows (~3.6M tokens) to an LLM costs $10-$30 per trade check, takes 30+ seconds, exposes private custodian bank codes to external APIs, and routinely miscalculates parent-company sums and 5.00% vs. 5.01% boundary math.", styles["td"]),
            ],
            [
                p("<b>2. Pure Vector Embedding Search (Dense RAG Only)</b>", styles["td_bold"]),
                p("Legal mandates rely on exact section numbers (<code>Section 3.01(b)</code>) and rating symbols (<code>Ba1</code>, <code>BBB-</code>). Dense embeddings blur negations and miss multi-hop definitions (pulling Section 3.01 without pulling Section 1.04). Our BM25 + TF-IDF + Cross-Reference Graph fixes both.", styles["td"]),
            ],
            [
                p("<b>3. 100% Hard-Coded SQL Rules (No AI Reader)</b>", styles["td_bold"]),
                p("Fails silently on <b>TC-09 and TC-10</b>: when database columns look clean (<code>coal_revenue = 4.2% &lt;= 10%</code>, <code>rating = A-</code>), SQL auto-approves the trade and misses the footnote revealing 22% mixed coal rail freight or an undisclosed Cayman swap basket.", styles["td"]),
            ],
            [
                p("<b>4. Letting an LLM Write SQL Queries on the Fly</b>", styles["td_bold"]),
                p("If a Text-to-SQL agent forgets <code>GROUP BY ultimate_parent_id</code> on just one run out of a hundred, a $1.3M subsidiary breach (like Florida Power &amp; Light under NextEra Energy) slips through. Compliance math must be locked in tested code, not generated dynamically.", styles["td"]),
            ],
        ],
        colWidths=[145, CONTENT_W - 145],
    )
    rej_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), INK),
                ("BACKGROUND", (0, 1), (-1, 1), colors.white),
                ("BACKGROUND", (0, 2), (-1, 2), SURFACE),
                ("BACKGROUND", (0, 3), (-1, 3), colors.white),
                ("BACKGROUND", (0, 4), (-1, 4), SURFACE),
                ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(rej_tbl)
    story.append(Spacer(1, 4))

    story.append(section_heading("3.2 The Weakest Point in Our Design (And What Would Break It)", "Honest Fragility Analysis", styles))
    story.append(
        callout_box(
            "<b>Our Biggest Vulnerability -- Stale Parent-Company Links in the Security Master (<code>ultimate_parent_id</code>):</b><br/>"
            "Step 2 catches parent-subsidiary breaches (like knowing NextEra Energy owns Florida Power &amp; Light) by grouping "
            "holdings on <code>ultimate_parent_id</code>. That math is 100% exact, but it trusts that the upstream corporate tree "
            "table is up to date.",
            styles,
            bg=AMBER_BG,
            bar=AMBER,
        )
    )
    story.append(Spacer(1, 3))
    story.append(
        p(
            "<b>- How to break it (Scenario 1 -- Same-Day Spin-Off or New Financing Shell):</b> Suppose an existing portfolio company "
            "creates a brand-new Delaware financing subsidiary this morning to issue bonds, and our data vendor has not linked the new "
            "subsidiary's <code>ultimate_parent_id</code> yet. Step 2 will see 0% existing exposure and approve the trade unless the "
            "deal footnote explicitly names the parent company for Step 3 to catch.",
            styles["bullet"],
        )
    )
    story.append(
        p(
            "<b>- How to break it (Scenario 2 -- Chained Side-Letter Waivers):</b> Our cross-reference expander follows 1-hop links "
            "(e.g., Section 3.01 -> Section 1.04). If an institutional client signs three sequential side-letter riders that modify "
            "each other conditionally (<i>'Rider 3 pauses Rider 1 during Q4 unless High-Yield exceeds 12%'</i>), a 1-hop lookup can "
            "miss the interaction between Rider 3 and Rider 1.",
            styles["bullet"],
        )
    )

    story.append(section_heading("3.3 Managing Real-World Risks & Human-in-the-Loop Governance", "Risk & Governance", styles))
    risk_tbl = Table(
        [
            [
                p("<b>Risk Category</b>", styles["th"]),
                p("<b>What Happens If Something Goes Wrong</b>", styles["th"]),
                p("<b>How Our Architecture Protects the Firm</b>", styles["th"]),
            ],
            [
                p("<b>1. Unequal Cost of Errors</b><br/>(False Positive vs. False Negative)", styles["td_bold"]),
                p("Pausing a good trade costs 2 minutes of officer review. Approving a mandate breach triggers forced market unwinds, remediation, and adviser reimbursement risk.", styles["td"]),
                p("<b>One-Way Safety Lock:</b> Step 4 is biased strictly toward safety. The AI can escalate a clean math check to <code>HELD FOR OFFICER</code>, but it can <b>never</b> override a Step 2 math breach.", styles["td"]),
            ],
            [
                p("<b>2. Outdated Mandates</b><br/>(Stale IPS Thresholds)", styles["td_bold"]),
                p("Checking today's trade against a superseded IPS cap or an expired client side-letter carve-out.", styles["td"]),
                p("Every trade decision stamps the active Mandate ID (<code>IPS-APEX-2026-V4</code>), effective date, and exact character span <code>[char_start..char_end]</code> into the audit record.", styles["td"]),
            ],
            [
                p("<b>3. Data Privacy Leakage</b><br/>(Confidential Holdings)", styles["td_bold"]),
                p("Exposing full fund positions, prime-broker codes, or internal desk notes to external LLM providers.", styles["td"]),
                p("<b>YAML Schema Pruning (<code>fund_schema.yaml</code>):</b> Strips private columns locally and sends only pre-summed numbers (<b>240 tokens instead of 3.6M tokens -- a 99.993% cut</b>).", styles["td"]),
            ],
            [
                p("<b>4. Fiduciary &amp; CCO Governance</b><br/>(Advisers Act 206(4)-7 / 1940 Act 38a-1)", styles["td_bold"]),
                p("Under SEC Rule 206(4)-7 (advisers) and Rule 38a-1 (registered funds), oversight responsibility rests on a designated human Chief Compliance Officer (CCO), never an AI.", styles["td"]),
                p("<b>Mandatory Officer Sign-Off Queue:</b> Quantitative breaches are blocked automatically; qualitative gray areas (<code>TC-09</code>, <code>TC-10</code>) are held until a human officer records written sign-off.", styles["td"]),
            ],
        ],
        colWidths=[115, 162, CONTENT_W - 277],
    )
    risk_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), INK),
                ("BACKGROUND", (0, 1), (-1, 1), colors.white),
                ("BACKGROUND", (0, 2), (-1, 2), SURFACE),
                ("BACKGROUND", (0, 3), (-1, 3), colors.white),
                ("BACKGROUND", (0, 4), (-1, 4), SURFACE),
                ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 3.6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3.6),
            ]
        )
    )
    story.append(risk_tbl)
    story.append(PageBreak())

    # =========================================================================
    # PAGE 4: 10-CASE BENCHMARK, RECONCILED FINANCIAL ATTRIBUTION & AI FAILURES
    # =========================================================================
    story.append(
        section_heading(
            "4.1 10-Trade Benchmark & Transparent Financial Attribution",
            "Reconciled Evaluation",
            styles,
        )
    )
    story.append(
        p(
            "We evaluated our 4-step gate across <b>10 proposed trades ($10.70M order flow)</b> against a $100.0M settled portfolio. "
            "To avoid over-claiming savings on trades that a basic single-ticket checker already catches, the table below explicitly "
            "separates: (1) <b>Incremental Savings Realized by Our Gate (+$184,500)</b> on the 2 unsafe approvals caught (<code>TC-03</code>, "
            "<code>TC-05</code>) and 1 false block fixed (<code>TC-04</code>); (2) <b>Ambiguous Exposure Held for CCO Review ($93,000)</b> "
            "on the 2 escalated trades (<code>TC-09</code>, <code>TC-10</code>, which are paused for human decision, not claimed as "
            "auto-realized savings); and (3) <b>Baseline Protection ($98,000)</b> on the 3 breaches blocked by both systems (<code>$0</code> incremental):",
            styles["body"],
        )
    )

    eval_rows = [
        [
            p("<b>ID</b>", styles["th"]),
            p("<b>Proposed Order &amp; Mandate Rule Tested</b>", styles["th"]),
            p("<b>Basic Check</b>", styles["th"]),
            p("<b>Our Gate</b>", styles["th"]),
            p("<b>Baseline / At-Risk</b>", styles["th"]),
            p("<b>Incremental Value (Ours)</b>", styles["th"]),
        ],
        [
            p("<b>TC-01</b>", styles["td_bold"]),
            p("<b>Microsoft Corp</b> ($1.20M AAA Bond) -- Clean; 3.10% -> 4.30% (&lt;= 5% IPS cap).", styles["td"]),
            p("APPROVED", styles["badge_pass"]),
            p("APPROVED", styles["badge_pass"]),
            p("$0", styles["td"]),
            p("$0 (Both pass)", styles["badge_muted"]),
        ],
        [
            p("<b>TC-02</b>", styles["td_bold"]),
            p("<b>Apple Inc</b> ($1.25M AA+ Bond) -- Direct company breach: 4.20% -> 5.45% (&gt; 5%).", styles["td"]),
            p("BLOCKED", styles["badge_breach"]),
            p("BLOCKED", styles["badge_breach"]),
            p("$45,000 base", styles["td"]),
            p("$0 (Both block)", styles["badge_muted"]),
        ],
        [
            p("<b>TC-03</b>", styles["td_bold"]),
            p("<b>Florida Power &amp; Light</b> ($1.30M) -- 0% direct, but parent NextEra hits 5.40% (&gt; 5%).", styles["td"]),
            p("APPROVED (Miss!)", styles["badge_breach"]),
            p("BLOCKED", styles["badge_breach"]),
            p("-$68,000 loss", styles["badge_breach"]),
            p("<b>+$68,000 Saved</b>", styles["badge_pass"]),
        ],
        [
            p("<b>TC-04</b>", styles["td_bold"]),
            p("<b>Ford Motor Credit</b> ($1.50M BBB-/Ba1) -- Higher rating governs (Sec 2.02b); IG.", styles["td"]),
            p("BLOCKED (False!)", styles["badge_breach"]),
            p("APPROVED", styles["badge_pass"]),
            p("-$82,500 cost", styles["badge_breach"]),
            p("<b>+$82,500 Saved</b>", styles["badge_pass"]),
        ],
        [
            p("<b>TC-05</b>", styles["td_bold"]),
            p("<b>Permian Resources</b> ($700k BB Energy) -- Total HY 14.9%, but HY Energy 5.20% (&gt; 5%).", styles["td"]),
            p("APPROVED (Miss!)", styles["badge_breach"]),
            p("BLOCKED", styles["badge_breach"]),
            p("-$34,000 loss", styles["badge_breach"]),
            p("<b>+$34,000 Saved</b>", styles["badge_pass"]),
        ],
        [
            p("<b>TC-06</b>", styles["td_bold"]),
            p("<b>UK Treasury Gilt</b> ($1.20M GBP Gov Bond) -- Valid OECD sovereign carve-out (8.70%).", styles["td"]),
            p("APPROVED", styles["badge_pass"]),
            p("APPROVED", styles["badge_pass"]),
            p("$0", styles["td"]),
            p("$0 (Both pass)", styles["badge_muted"]),
        ],
        [
            p("<b>TC-07</b>", styles["td_bold"]),
            p("<b>Siemens AG</b> ($1.00M Unhedged EUR Corp) -- OECD FX carve-out is for sovereigns only.", styles["td"]),
            p("BLOCKED", styles["badge_breach"]),
            p("BLOCKED", styles["badge_breach"]),
            p("$38,000 base", styles["td"]),
            p("$0 (Both block)", styles["badge_muted"]),
        ],
        [
            p("<b>TC-08</b>", styles["td_bold"]),
            p("<b>NVIDIA Corp</b> ($50k Stock Buy) -- At 5.15% passive drift; active BUY is prohibited.", styles["td"]),
            p("BLOCKED", styles["badge_breach"]),
            p("BLOCKED", styles["badge_breach"]),
            p("$15,000 base", styles["td"]),
            p("$0 (Both block)", styles["badge_muted"]),
        ],
        [
            p("<b>TC-09</b>", styles["td_bold"]),
            p("<b>Heartland Rail</b> ($1.00M Bond) -- 4.2% coal, but footnote shows 22% mixed coal rail.", styles["td"]),
            p("APPROVED (Miss!)", styles["badge_breach"]),
            p("HELD (CCO)", styles["badge_hold"]),
            p("$41,000 at-risk", styles["badge_hold"]),
            p("<b>Escalated ($1.0M)</b>", styles["badge_hold"]),
        ],
        [
            p("<b>TC-10</b>", styles["td_bold"]),
            p("<b>Cayman Emerald Trust</b> ($1.50M SPV) -- Footnote shows undisclosed oil/gas swap basket.", styles["td"]),
            p("APPROVED (Miss!)", styles["badge_breach"]),
            p("HELD (CCO)", styles["badge_hold"]),
            p("$52,000 at-risk", styles["badge_hold"]),
            p("<b>Escalated ($1.5M)</b>", styles["badge_hold"]),
        ],
    ]
    eval_tbl = Table(eval_rows, colWidths=[33, CONTENT_W - 285, 62, 54, 62, 74])
    eval_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), INK),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, SURFACE]),
                ("GRID", (0, 0), (-1, -1), 0.45, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3.8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3.8),
                ("TOPPADDING", (0, 0), (-1, -1), 2.1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.1),
            ]
        )
    )
    story.append(eval_tbl)
    story.append(Spacer(1, 3.5))
    story.append(draw_savings_chart())
    story.append(Spacer(1, 3.5))

    story.append(section_heading("4.2 Honest Report: Three Places Where the AI Struggled in Testing", "Failure Modes & Fixes", styles))
    story.append(
        p(
            "<b>1. Free-tier reasoning models running out of tokens inside <code>&lt;think&gt;</code> tags:</b> On our first live "
            "OpenRouter test run, a reasoning model spent its entire 500-token budget thinking inside "
            "<code>&lt;think&gt;...&lt;/think&gt;</code> tags and cut off before outputting JSON. We fixed this by stripping "
            "<code>&lt;think&gt;</code> blocks in <code>src/agent_graph.py</code> and routing to instruction-tuned models first.",
            styles["bullet"],
        )
    )
    story.append(
        p(
            "<b>2. Minor quote paraphrasing on 4 out of 10 live runs:</b> Smaller free-tier models occasionally dropped a comma or "
            "paraphrased a word when copying the mandate quote. Our Step 4 verifier (<code>verify_verbatim_quote()</code>) caught "
            "all 4 instances and automatically anchored the citation to the exact character span <code>[char_start..char_end]</code>.",
            styles["bullet"],
        )
    )
    story.append(
        p(
            "<b>3. Free-tier API latency swings (7.5s to 68.6s) &amp; Two-Tier Fast Path:</b> While Steps 1, 2, and 4 finish "
            "locally in <b>under 5 milliseconds</b>, waiting on a free-tier LLM for every trade is too slow for a high-speed desk. "
            "In production, 90% of standard bond and stock orders have no special deal footnotes or SPV wrappers, so they clear "
            "Steps 1 &amp; 2 in <b>&lt; 5 ms</b>, calling Step 3 (AI) only when unstructured rider prose is attached.",
            styles["bullet"],
        )
    )
    story.append(PageBreak())

    # =========================================================================
    # PAGE 5: ONE-PAGE APPENDIX -- WHAT I ADDED BEYOND THE AI
    # =========================================================================
    story.append(section_heading("A.1 How I Used AI (And Three Prompts That Actually Helped)", "One-Page Appendix", styles))
    story.append(
        p(
            "I treated AI as a fast sparring partner for legal edge-case brainstorming and UI layout iteration, while keeping all "
            "architecture, retrieval math, and compliance state locks in my own hands. Three prompts that were genuinely useful:",
            styles["body"],
        )
    )
    story.append(
        p(
            "<b>1. Finding real-world compliance traps:</b> <i>'Give me concrete examples of how institutional bond funds accidentally "
            "violate their Investment Policy Statement (IPS) or Form N-1A mandate even when basic SQL checks on single-issuer % pass.'</i>",
            styles["bullet"],
        )
    )
    story.append(
        p(
            "<b>2. Drafting realistic cross-referenced mandate clauses:</b> <i>'Draft an institutional Investment Policy Statement "
            "(IPS) where the 5% single-issuer cap in Article III depends on a parent-group definition in Article I, a split-rating "
            "tie-breaker in Article II, an OECD sovereign currency exception in Article IV, and qualitative coal/SPV rules in Article V.'</i>",
            styles["bullet"],
        )
    )
    story.append(
        p(
            "<b>3. Locking down the Step 3 footnote reader prompt:</b> <i>'You are a Senior Fund Compliance Auditor. Analyze the "
            "proposed trade using ONLY the retrieved IPS clauses, the exact numbers from the Deterministic Calculator, and the "
            "deal footnotes. NEVER invent math or override the Deterministic Calculator.'</i>",
            styles["bullet"],
        )
    )

    story.append(section_heading("A.2 Three AI Suggestions I Rejected (And How I Knew Better)", "Human Engineering Judgment", styles))
    app_tbl = Table(
        [
            [
                p("<b>What the AI Suggested</b>", styles["th"]),
                p("<b>Why I Rejected It &amp; Where My Judgment Came From</b>", styles["th"]),
            ],
            [
                p("<b>1. 'Use a Text-to-SQL agent to query the holdings table dynamically on every trade.'</b>", styles["td_bold"]),
                p("<b>How I knew:</b> At <b>Apollo Global Management</b>, I built a natural-language-to-DB assistant over 75K+ holdings and 20K+ trades. For ad-hoc analyst questions, a 98% query accuracy rate is great. For pre-trade compliance, if an LLM forgets <code>GROUP BY ultimate_parent_id</code> even once, the fund executes a mandate breach. I replaced dynamic query generation with fixed, tested aggregation code in Step 2.", styles["td"]),
            ],
            [
                p("<b>2. 'Chunk the rulebook into 500-token slices and use vector embeddings.'</b>", styles["td_bold"]),
                p("<b>How I knew:</b> From building my <b>Vector Space Retrieval Engine</b> (benchmarking BM25, TF-IDF, LSA, and WordNet expansion on the Cranfield corpus), I knew dense embeddings struggle with exact section codes (<code>Section 3.01(b)</code>) and sever cross-references when a limit in Article III relies on a definition in Article I. I built a hybrid BM25 + TF-IDF retriever with a 1-hop cross-reference graph expander instead.", styles["td"]),
            ],
            [
                p("<b>3. 'Claim all blocked trades as incremental AI savings and label IPS caps as SEC statutory limits.'</b>", styles["td_bold"]),
                p("<b>How I knew:</b> Basic SQL checks already block simple breaches (<code>TC-02</code>, <code>TC-07</code>, <code>TC-08</code>), and <code>TC-09</code>/<code>TC-10</code> are held for officer review rather than auto-blocked. I separated <b>+$184,500 in incremental value</b> (<code>TC-03</code>, <code>TC-04</code>, <code>TC-05</code>) from <b>$93,000 held for review</b> and <b>$98,000 baseline</b>, and distinguished synthetic IPS caps from SEC Rule 206(4)-7 (Advisers Act) and Rule 38a-1 (1940 Act).", styles["td"]),
            ],
        ],
        colWidths=[148, CONTENT_W - 148],
    )
    app_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), INK),
                ("BACKGROUND", (0, 1), (-1, 1), colors.white),
                ("BACKGROUND", (0, 2), (-1, 2), SURFACE),
                ("BACKGROUND", (0, 3), (-1, 3), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 3.8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3.8),
            ]
        )
    )
    story.append(app_tbl)
    story.append(Spacer(1, 3))

    story.append(section_heading("A.3 What Came Directly From Me", "Practitioner Contributions", styles))
    story.append(
        p(
            "<b>- Auditable Incremental Attribution (+$184,500 Incremental / $93,000 Escalated / $98,000 Baseline):</b> Instead of "
            "lumping all 10 test cases into a single un-reconciled total, I broke down every dollar by case and counterfactual "
            "baseline: 2 hidden breaches blocked (+$102,000), 1 false block fixed (+$82,500), 2 ambiguous trades escalated ($2.50M "
            "notional / $93,000 exposure paused for CCO sign-off), and 3 baseline breaches excluded from incremental claims ($98,000).",
            styles["bullet"],
        )
    )
    story.append(
        p(
            "<b>- Schema-pruned context budgeting (<code>data/fund_schema.yaml</code>):</b> Inspired by my work at Apollo optimizing "
            "token budgets across fund schemas, I designed <code>fund_schema.yaml</code> to strip sensitive custodian and broker "
            "fields locally and reduce LLM prompt context from ~3.6M tokens to 240 tokens (<b>99.993% reduction</b>).",
            styles["bullet"],
        )
    )
    story.append(
        p(
            "<b>- Modeling the passive market-drift vs. active purchase lockout (TC-08):</b> Most prototypes check <code>weight &lt;= 5%</code> "
            "statically. I explicitly modeled the transition where holding a drifted position (NVIDIA at 5.15%) is compliant under "
            "Section 3.03, but adding a $50,000 active BUY order is blocked.",
            styles["bullet"],
        )
    )

    story.append(section_heading("A.4 What I Will Happily Defend Live on a Whiteboard Without AI", "Live Defense Commitment", styles))
    story.append(
        callout_box(
            "With zero AI or notes, I am ready to derive, code, and walk through the entire retrieval and compliance engine live:<br/>"
            "<b>1. The Hybrid BM25 + Cross-Reference Graph Retriever (<code>src/retriever.py</code>):</b> Inverted index construction, "
            "Okapi BM25 scoring <code>IDF(q) * [tf * (k1 + 1)] / [tf + k1 * (1 - b + b * dl / avgdl)]</code>, TF-IDF cosine fusion, "
            "1-hop regex graph expansion across legal sections, and character-offset substring verification.<br/>"
            "<b>2. The Pro-Forma Compliance Calculator &amp; Safety Gate (<code>src/deterministic_engine.py</code>):</b> Parent-group "
            "relational aggregation on <code>ultimate_parent_id</code>, split-rating ordinal rank resolution "
            "(<code>min(rank_SP, rank_Moodys) &lt;= 10</code>), and the one-way safety state machine in Step 4.",
            styles,
        )
    )

    doc.build(story)


def verify_and_render_pngs(pdf_path: Path, tmp_dir: Path) -> None:
    """Verify PDF text extraction via pypdf & pdfplumber and render PNGs via pypdfium2."""
    tmp_dir.mkdir(parents=True, exist_ok=True)
    for old_png in tmp_dir.glob("*.png"):
        old_png.unlink()

    reader = pypdf.PdfReader(str(pdf_path))
    num_pages = len(reader.pages)
    print(f"pypdf page count: {num_pages}")
    assert num_pages == 5, f"Expected exactly 5 pages, got {num_pages}"

    with pdfplumber.open(str(pdf_path)) as pdf:
        for idx, page in enumerate(pdf.pages, start=1):
            txt = page.extract_text() or ""
            print(f"Page {idx} extracted chars: {len(txt)}")
            assert len(txt) > 800, f"Page {idx} has unexpectedly little text ({len(txt)} chars)"

    pdf_doc = pdfium.PdfDocument(str(pdf_path))
    for i in range(len(pdf_doc)):
        page = pdf_doc[i]
        bitmap = page.render(scale=2.2)
        pil_image = bitmap.to_pil()
        out_png = tmp_dir / f"page_{i + 1}.png"
        pil_image.save(str(out_png))
        print(f"Rendered {out_png} ({pil_image.size[0]}x{pil_image.size[1]})")


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    pdf_path = base_dir / "TRESATA_WRITTEN_BRIEF.pdf"
    output_pdf_dir = base_dir / "output" / "pdf"
    output_pdf_dir.mkdir(parents=True, exist_ok=True)
    output_pdf_path = output_pdf_dir / "TRESATA_WRITTEN_BRIEF.pdf"
    tmp_dir = base_dir / "tmp" / "pdfs"

    build_pdf(pdf_path)
    shutil.copy2(pdf_path, output_pdf_path)
    print(f"Generated {pdf_path} and {output_pdf_path} ({pdf_path.stat().st_size:,} bytes)")
    verify_and_render_pngs(pdf_path, tmp_dir)


if __name__ == "__main__":
    main()
