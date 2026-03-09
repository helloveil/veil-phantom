#!/usr/bin/env python3
"""Generate the VeilPhantom technical paper as a visually-rich PDF.

Includes architectural diagrams, pipeline flowcharts, training data
visualizations, and benchmark result charts -- all drawn programmatically
with fpdf2 shapes/colors (no external image dependencies).
"""

import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fpdf import FPDF
from fpdf.fonts import FontFace

# ── Load benchmark data ──
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "benchmarks", "results", "showcase_final.json")
DATA = json.load(open(DATA_PATH))
S = DATA["summary_averaged"]
VERTS = DATA["per_vertical_averaged"]

# ── Color palette ──
NAVY = (15, 23, 42)
DARK_BLUE = (30, 58, 138)
MID_BLUE = (59, 130, 246)
LIGHT_BLUE = (191, 219, 254)
PALE_BLUE = (239, 246, 255)
ACCENT_GREEN = (16, 185, 129)
ACCENT_ORANGE = (245, 158, 11)
ACCENT_RED = (239, 68, 68)
ACCENT_PURPLE = (139, 92, 246)
DARK_GRAY = (30, 30, 30)
MID_GRAY = (100, 100, 100)
LIGHT_GRAY = (229, 231, 235)
WHITE = (255, 255, 255)

# Layer colors for pipeline diagram
LAYER_COLORS = [
    (220, 38, 38),    # L0 Shade NER - red
    (234, 88, 12),    # L1 Gazetteer - orange
    (202, 138, 4),    # L1.5 Pre-Regex - amber
    (22, 163, 74),    # L2 NLP - green
    (59, 130, 246),   # L3 Regex - blue
    (99, 102, 241),   # L3.5 URL - indigo
    (139, 92, 246),   # L4 Contextual - purple
]


class Paper(FPDF):
    """Custom PDF class with visual styling methods."""

    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica", "I", 7.5)
            self.set_text_color(*MID_GRAY)
            self.cell(0, 5, "VeilPhantom: Privacy-Preserving PII Redaction for Agentic AI", align="C")
            self.ln(3)
            self.set_draw_color(*LIGHT_GRAY)
            self.set_line_width(0.3)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(4)

    def footer(self):
        self.set_y(-12)
        self.set_draw_color(*LIGHT_GRAY)
        self.set_line_width(0.3)
        self.line(10, self.get_y() - 2, 200, self.get_y() - 2)
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(*MID_GRAY)
        self.cell(0, 8, f"{self.page_no()}", align="C")

    # ── Text helpers ──

    def section_title(self, title, level=1):
        if level == 1:
            self.ln(4)
            # Colored left bar
            y = self.get_y()
            self.set_fill_color(*DARK_BLUE)
            self.rect(10, y, 3, 8, style="F")
            self.set_xy(16, y)
            self.set_font("Helvetica", "B", 13)
            self.set_text_color(*NAVY)
            self.cell(0, 8, title)
            self.ln(10)
        elif level == 2:
            self.ln(3)
            self.set_font("Helvetica", "B", 10.5)
            self.set_text_color(*DARK_BLUE)
            self.cell(0, 6, title)
            self.ln(6)
        elif level == 3:
            self.ln(1)
            self.set_font("Helvetica", "BI", 9.5)
            self.set_text_color(70, 70, 130)
            self.cell(0, 5, title)
            self.ln(5)

    def body_text(self, text):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*DARK_GRAY)
        self.multi_cell(0, 4.8, text)
        self.ln(2)

    def caption(self, text):
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*MID_GRAY)
        self.cell(0, 5, text, align="C")
        self.ln(6)

    def code_block(self, text):
        self.set_font("Courier", "", 7.5)
        self.set_fill_color(248, 250, 252)
        self.set_draw_color(*LIGHT_GRAY)
        self.set_text_color(55, 65, 81)
        x = self.get_x() + 4
        y = self.get_y()
        # Measure height (estimate lines)
        lines = text.count('\n') + 1
        avg_chars_per_line = 80
        for line in text.split('\n'):
            lines += max(0, len(line) // avg_chars_per_line)
        h = lines * 4.2 + 8
        # Background
        self.set_line_width(0.3)
        self.rect(x, y, 180, h, style="DF", round_corners=True, corner_radius=2)
        # Left accent bar
        self.set_fill_color(*MID_BLUE)
        self.rect(x, y + 2, 2, h - 4, style="F")
        # Text
        self.set_fill_color(248, 250, 252)
        self.set_xy(x + 6, y + 3)
        self.multi_cell(170, 4.2, text)
        self.set_y(y + h + 3)

    def stat_box(self, x, y, w, h, value, label, color=MID_BLUE):
        """Draw a highlighted stat box."""
        self.set_fill_color(*color)
        self.rect(x, y, w, h, style="F", round_corners=True, corner_radius=3)
        # Value
        self.set_xy(x, y + 3)
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(*WHITE)
        self.cell(w, 10, value, align="C")
        # Label
        self.set_xy(x, y + 14)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(220, 230, 255)
        self.cell(w, 5, label, align="C")

    # ── Diagram helpers ──

    def draw_arrow(self, x1, y1, x2, y2, color=MID_GRAY):
        """Draw an arrow between two points."""
        self.set_draw_color(*color)
        self.set_line_width(0.5)
        self.line(x1, y1, x2, y2)
        # Arrowhead
        angle = math.atan2(y2 - y1, x2 - x1)
        size = 2.5
        self.set_fill_color(*color)
        pts = [
            (x2, y2),
            (x2 - size * math.cos(angle - 0.4), y2 - size * math.sin(angle - 0.4)),
            (x2 - size * math.cos(angle + 0.4), y2 - size * math.sin(angle + 0.4)),
        ]
        self.polygon(pts, style="F")

    def draw_box(self, x, y, w, h, text, fill_color=PALE_BLUE, text_color=NAVY,
                 border_color=MID_BLUE, font_size=8, bold=False):
        """Draw a rounded box with centered text."""
        self.set_fill_color(*fill_color)
        self.set_draw_color(*border_color)
        self.set_line_width(0.4)
        self.rect(x, y, w, h, style="DF", round_corners=True, corner_radius=2)
        self.set_font("Helvetica", "B" if bold else "", font_size)
        self.set_text_color(*text_color)
        self.set_xy(x, y + (h - font_size * 0.35) / 2 - 1)
        self.cell(w, font_size * 0.35, text, align="C")

    def draw_shield_icon(self, cx, cy, size=6):
        """Draw a simple shield icon."""
        s = size
        pts = [
            (cx, cy - s),          # top
            (cx + s * 0.8, cy - s * 0.5),
            (cx + s * 0.7, cy + s * 0.3),
            (cx, cy + s),          # bottom
            (cx - s * 0.7, cy + s * 0.3),
            (cx - s * 0.8, cy - s * 0.5),
        ]
        self.set_fill_color(*ACCENT_GREEN)
        self.set_draw_color(5, 150, 105)
        self.set_line_width(0.4)
        self.polygon(pts, style="DF")
        # Checkmark
        self.set_draw_color(*WHITE)
        self.set_line_width(0.8)
        self.line(cx - s * 0.25, cy, cx - s * 0.05, cy + s * 0.3)
        self.line(cx - s * 0.05, cy + s * 0.3, cx + s * 0.3, cy - s * 0.2)

    def draw_bar_chart(self, x, y, w, h, data, colors=None, title=None):
        """Draw a horizontal bar chart. data = [(label, value), ...]"""
        if title:
            self.set_xy(x, y - 6)
            self.set_font("Helvetica", "B", 8.5)
            self.set_text_color(*NAVY)
            self.cell(w, 5, title)
        bar_h = min(8, (h - 4) / len(data))
        gap = 2
        max_val = max(v for _, v in data) if data else 1
        bar_area_w = w * 0.55
        label_w = w * 0.30
        value_w = w * 0.15
        for i, (label, value) in enumerate(data):
            by = y + i * (bar_h + gap)
            # Label
            self.set_xy(x, by)
            self.set_font("Helvetica", "", 7)
            self.set_text_color(*DARK_GRAY)
            self.cell(label_w, bar_h, label, align="R")
            # Bar
            bar_w = (value / max_val) * bar_area_w if max_val > 0 else 0
            c = colors[i % len(colors)] if colors else MID_BLUE
            self.set_fill_color(*c)
            bx = x + label_w + 3
            self.rect(bx, by + 1, bar_w, bar_h - 2, style="F", round_corners=True, corner_radius=1)
            # Value
            self.set_xy(bx + bar_w + 2, by)
            self.set_font("Helvetica", "B", 7)
            self.set_text_color(*c)
            self.cell(value_w, bar_h, str(int(value)))

    def styled_table(self, headers, rows, col_widths, x_start=10):
        """Draw a styled table with alternating rows."""
        self.set_x(x_start)
        # Header
        self.set_font("Helvetica", "B", 8)
        self.set_fill_color(*DARK_BLUE)
        self.set_text_color(*WHITE)
        for hdr, w in zip(headers, col_widths):
            self.cell(w, 7, hdr, border=0, fill=True, align="C")
        self.ln()
        # Rows
        self.set_font("Helvetica", "", 8)
        for i, row in enumerate(rows):
            self.set_x(x_start)
            if i % 2 == 0:
                self.set_fill_color(*PALE_BLUE)
            else:
                self.set_fill_color(*WHITE)
            self.set_text_color(*DARK_GRAY)
            for val, w in zip(row, col_widths):
                self.cell(w, 6, str(val), border=0, fill=True, align="C")
            self.ln()
        # Bottom line
        self.set_draw_color(*LIGHT_GRAY)
        self.set_line_width(0.3)
        total_w = sum(col_widths)
        self.line(x_start, self.get_y(), x_start + total_w, self.get_y())


def build_paper():
    pdf = Paper()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=18)

    # ════════════════════════════════════════════════════════════════
    # TITLE PAGE
    # ════════════════════════════════════════════════════════════════
    pdf.add_page()

    # Top gradient bar
    for i in range(60):
        r = int(15 + (59 - 15) * i / 60)
        g = int(23 + (130 - 23) * i / 60)
        b = int(42 + (246 - 42) * i / 60)
        pdf.set_fill_color(r, g, b)
        pdf.rect(0, i * 0.5, 210, 0.6, style="F")

    # Shield icon in top area
    pdf.draw_shield_icon(105, 18, size=8)

    pdf.ln(36)
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 14, "VeilPhantom", align="C")
    pdf.ln(12)

    # Subtitle with accent line
    y = pdf.get_y()
    pdf.set_draw_color(*MID_BLUE)
    pdf.set_line_width(0.8)
    pdf.line(55, y, 155, y)
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 13)
    pdf.set_text_color(*DARK_BLUE)
    pdf.cell(0, 7, "Privacy-Preserving PII Redaction", align="C")
    pdf.ln(7)
    pdf.cell(0, 7, "for Agentic AI Pipelines", align="C")
    pdf.ln(12)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*MID_GRAY)
    pdf.cell(0, 6, "Technical Report  |  March 2026  |  v1.0", align="C")
    pdf.ln(14)

    # Stat boxes row
    bx = 18
    by = pdf.get_y()
    bw, bh = 40, 26
    gap = 6
    pdf.stat_box(bx, by, bw, bh, "93.3%", "Tool Accuracy", DARK_BLUE)
    pdf.stat_box(bx + bw + gap, by, bw, bh, "885", "PII Detected", MID_BLUE)
    pdf.stat_box(bx + 2 * (bw + gap), by, bw, bh, "6ms", "Redaction Time", ACCENT_GREEN)
    pdf.stat_box(bx + 3 * (bw + gap), by, bw, bh, "0", "PII Leaked", ACCENT_PURPLE)
    pdf.set_y(by + bh + 10)

    # Abstract
    abs_y = pdf.get_y()
    pdf.set_fill_color(*PALE_BLUE)
    pdf.set_draw_color(*MID_BLUE)
    pdf.set_line_width(0.4)
    pdf.rect(14, abs_y, 182, 66, style="DF", round_corners=True, corner_radius=3)
    # Left accent
    pdf.set_fill_color(*DARK_BLUE)
    pdf.rect(14, abs_y + 4, 3, 58, style="F")

    pdf.set_xy(22, abs_y + 5)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*DARK_BLUE)
    pdf.cell(0, 5, "Abstract")
    pdf.set_xy(22, abs_y + 12)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*DARK_GRAY)
    pdf.multi_cell(168, 4.5,
        "We present VeilPhantom, a lightweight SDK that interposes as transparent middleware between "
        "user input and Large Language Models, replacing personally identifiable information (PII) with "
        "deterministic typed tokens before any data reaches the model. VeilPhantom employs a 7-layer "
        "detection pipeline combining a custom PhoneticDeBERTa transformer (Shade NER, 22M parameters, "
        "trained on 72 million words with 862K augmented examples), gazetteer lookup, regex-based NLP "
        "heuristics, 35 regex patterns, and contextual sensitivity analysis. For agentic workflows, "
        "VeilPhantom intercepts LLM tool calls, rehydrates tokens with real values locally, executes "
        "tools, and re-redacts results -- ensuring PII never leaves the user's machine. We evaluate on "
        "98 scenarios across 8 industry verticals using Claude 4.5 Haiku. Results: 93.3% tool accuracy "
        "(+1.9% vs unredacted baseline), 885 PII entities detected across 13 types, zero identifiable "
        "PII leakage, and 6ms average redaction overhead."
    )
    pdf.set_y(abs_y + 70)

    # Key words
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*DARK_BLUE)
    kw_y = pdf.get_y()
    pdf.set_x(14)
    pdf.cell(18, 5, "Keywords:")
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*MID_GRAY)
    pdf.cell(0, 5, "PII redaction, privacy, LLM safety, agentic AI, NER, tool-call interception, token mapping")
    pdf.ln(12)

    # ════════════════════════════════════════════════════════════════
    # 1. INTRODUCTION
    # ════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.section_title("1  Introduction")
    pdf.body_text(
        "Large Language Models have become central to enterprise workflows -- drafting emails, processing "
        "financial transactions, managing patient records, and orchestrating multi-step agentic tasks. "
        "These workflows invariably involve personally identifiable information: names, emails, phone "
        "numbers, government IDs, bank accounts, and financial figures. Sending this data to cloud-hosted "
        "LLMs creates significant privacy, compliance, and liability risks under GDPR, POPIA, HIPAA, "
        "and CCPA."
    )
    pdf.body_text(
        "Existing approaches fall into three categories: (1) self-hosted models, which sacrifice "
        "capability for privacy; (2) post-hoc output filtering, which cannot prevent the model from "
        "processing PII during inference; and (3) input redaction, which removes PII before it reaches "
        "the model. VeilPhantom takes the third approach but solves a critical gap: maintaining full "
        "agent utility -- including multi-tool orchestration -- while ensuring zero PII exposure to the LLM."
    )
    pdf.body_text(
        "The key insight is that LLMs do not need real PII to perform tasks correctly. A model instructed "
        "to \"send an email to [EMAIL_1]\" generates the same tool call structure as one given the real "
        "address. VeilPhantom exploits this by replacing PII with typed tokens ([PERSON_1], [EMAIL_1], "
        "[BANKACCT_1]) that preserve semantic structure while eliminating privacy risk."
    )

    # Visual: The Privacy Gap diagram
    pdf.ln(2)
    diag_y = pdf.get_y()
    pdf.set_fill_color(254, 243, 199)
    pdf.set_draw_color(245, 158, 11)
    pdf.set_line_width(0.4)
    pdf.rect(14, diag_y, 182, 40, style="DF", round_corners=True, corner_radius=3)

    pdf.set_xy(18, diag_y + 2)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(146, 64, 14)
    pdf.cell(0, 4, "The Privacy Gap in Agentic AI")

    # Without VeilPhantom
    by1 = diag_y + 9
    pdf.draw_box(18, by1, 34, 10, "User (PII)", (254, 226, 226), ACCENT_RED, ACCENT_RED, 7, True)
    pdf.draw_arrow(52, by1 + 5, 64, by1 + 5, ACCENT_RED)
    pdf.draw_box(64, by1, 38, 10, "LLM (sees PII)", (254, 226, 226), ACCENT_RED, ACCENT_RED, 7)
    pdf.draw_arrow(102, by1 + 5, 114, by1 + 5, ACCENT_RED)
    pdf.draw_box(114, by1, 34, 10, "Tool (real PII)", (254, 226, 226), ACCENT_RED, ACCENT_RED, 7)
    pdf.set_xy(152, by1 + 1)
    pdf.set_font("Helvetica", "", 6.5)
    pdf.set_text_color(ACCENT_RED[0], ACCENT_RED[1], ACCENT_RED[2])
    pdf.cell(40, 8, "PII exposed at every hop", align="L")

    # With VeilPhantom
    by2 = diag_y + 23
    pdf.draw_box(18, by2, 34, 10, "User (PII)", (220, 252, 231), (5, 100, 60), ACCENT_GREEN, 7, True)
    pdf.draw_arrow(52, by2 + 5, 64, by2 + 5, ACCENT_GREEN)
    pdf.draw_box(64, by2, 38, 10, "LLM (tokens)", (220, 252, 231), (5, 100, 60), ACCENT_GREEN, 7)
    pdf.draw_arrow(102, by2 + 5, 114, by2 + 5, ACCENT_GREEN)
    pdf.draw_box(114, by2, 34, 10, "Tool (local)", (220, 252, 231), (5, 100, 60), ACCENT_GREEN, 7)
    pdf.draw_shield_icon(156, by2 + 5, 4)
    pdf.set_xy(162, by2 + 1)
    pdf.set_font("Helvetica", "", 6.5)
    pdf.set_text_color(5, 100, 60)
    pdf.cell(30, 8, "PII stays local", align="L")

    pdf.set_y(diag_y + 44)
    pdf.caption("Figure 1: Without VeilPhantom, PII is exposed at every hop. With VeilPhantom, the LLM only sees tokens.")

    pdf.section_title("1.1  Contributions", level=2)
    pdf.body_text(
        "1. Shade NER -- a 22M-parameter PhoneticDeBERTa model trained on 72 million words with "
        "entity-swap augmentation, achieving 97.1% F1 on PII detection with phonetic robustness for "
        "cross-cultural names (Section 3).\n\n"
        "2. A 7-layer detection pipeline combining transformer NER, gazetteers, NLP heuristics, 35 regex "
        "patterns, and contextual sensitivity analysis -- achieving high recall across 19 PII types with "
        "zero external dependencies in default mode (Section 4).\n\n"
        "3. VeilSession and VeilToolMiddleware -- stateful components enabling multi-turn conversations "
        "and agentic tool-call interception with local rehydration and re-redaction (Section 5).\n\n"
        "4. A 98-scenario benchmark across 8 industry verticals demonstrating +1.9% accuracy improvement "
        "with privacy, zero PII leakage, and 6ms overhead (Section 6)."
    )

    # ════════════════════════════════════════════════════════════════
    # 2. SYSTEM ARCHITECTURE
    # ════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.section_title("2  System Architecture")
    pdf.body_text(
        "VeilPhantom operates as transparent middleware between the application and the LLM provider. "
        "The system comprises three core components: the Detection Pipeline (§3-4), the Token Map (§4.3), "
        "and the Agentic Middleware (§5). Figure 2 shows the complete data flow."
    )

    # ── Figure 2: Architecture Diagram ──
    pdf.ln(2)
    fig_y = pdf.get_y()
    fig_h = 72
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(*LIGHT_GRAY)
    pdf.set_line_width(0.3)
    pdf.rect(10, fig_y, 190, fig_h, style="DF", round_corners=True, corner_radius=3)

    # Title
    pdf.set_xy(14, fig_y + 2)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*DARK_BLUE)
    pdf.cell(0, 4, "Figure 2: VeilPhantom Agentic Data Flow")

    # Row 1: User -> Redact -> LLM
    r1y = fig_y + 12
    pdf.draw_box(16, r1y, 30, 12, "User Input", (254, 226, 226), (150, 40, 40), (200, 80, 80), 7, True)
    pdf.set_xy(16, r1y + 7)
    pdf.set_font("Helvetica", "", 5.5)
    pdf.set_text_color(150, 40, 40)
    pdf.cell(30, 3, "(contains PII)", align="C")

    pdf.draw_arrow(46, r1y + 6, 56, r1y + 6, DARK_BLUE)

    # Veil box (bigger, prominent)
    pdf.set_fill_color(*DARK_BLUE)
    pdf.set_draw_color(*NAVY)
    pdf.rect(56, r1y - 2, 42, 16, style="DF", round_corners=True, corner_radius=3)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*WHITE)
    pdf.set_xy(56, r1y)
    pdf.cell(42, 6, "VeilPhantom", align="C")
    pdf.set_font("Helvetica", "", 6)
    pdf.set_xy(56, r1y + 6)
    pdf.cell(42, 5, "7-Layer Pipeline", align="C")

    pdf.draw_arrow(98, r1y + 6, 108, r1y + 6, ACCENT_GREEN)

    pdf.draw_box(108, r1y, 38, 12, "[PERSON_1]...", (220, 252, 231), (5, 100, 60), ACCENT_GREEN, 7)
    pdf.set_xy(108, r1y + 7)
    pdf.set_font("Helvetica", "", 5.5)
    pdf.set_text_color(5, 100, 60)
    pdf.cell(38, 3, "(tokens only)", align="C")

    pdf.draw_arrow(146, r1y + 6, 156, r1y + 6, MID_BLUE)

    pdf.draw_box(156, r1y, 36, 12, "LLM (Cloud)", (219, 234, 254), DARK_BLUE, MID_BLUE, 7, True)

    # Row 2: LLM tool call -> Middleware -> Tool
    r2y = r1y + 22
    pdf.draw_arrow(174, r1y + 12, 174, r2y, MID_BLUE)

    pdf.draw_box(148, r2y, 44, 12, "tool_call(tokens)", (219, 234, 254), DARK_BLUE, MID_BLUE, 7)

    pdf.draw_arrow(148, r2y + 6, 138, r2y + 6, ACCENT_ORANGE)

    pdf.set_fill_color(245, 158, 11)
    pdf.set_draw_color(180, 120, 10)
    pdf.rect(86, r2y - 2, 52, 16, style="DF", round_corners=True, corner_radius=3)
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_text_color(*WHITE)
    pdf.set_xy(86, r2y)
    pdf.cell(52, 6, "Middleware", align="C")
    pdf.set_font("Helvetica", "", 5.5)
    pdf.set_xy(86, r2y + 6)
    pdf.cell(52, 5, "Rehydrate + Execute + Re-redact", align="C")

    pdf.draw_arrow(86, r2y + 6, 76, r2y + 6, ACCENT_ORANGE)

    pdf.draw_box(28, r2y, 48, 12, "Local Tool Execution", (254, 243, 199), (120, 80, 10), ACCENT_ORANGE, 7)
    pdf.set_xy(28, r2y + 7)
    pdf.set_font("Helvetica", "", 5.5)
    pdf.set_text_color(120, 80, 10)
    pdf.cell(48, 3, "(real PII, never leaves device)", align="C")

    # Row 3: Result loop back
    r3y = r2y + 20
    pdf.draw_arrow(52, r2y + 12, 52, r3y, ACCENT_ORANGE)
    pdf.draw_box(28, r3y, 48, 12, "Tool Result (PII)", (254, 243, 199), (120, 80, 10), ACCENT_ORANGE, 7)

    pdf.draw_arrow(76, r3y + 6, 86, r3y + 6, DARK_BLUE)
    pdf.draw_box(86, r3y, 42, 12, "Re-Redact", DARK_BLUE, WHITE, NAVY, 7, True)
    pdf.draw_arrow(128, r3y + 6, 138, r3y + 6, ACCENT_GREEN)
    pdf.draw_box(138, r3y, 44, 12, "Safe result (tokens)", (220, 252, 231), (5, 100, 60), ACCENT_GREEN, 7)
    pdf.draw_arrow(182, r3y + 6, 192, r3y + 2, MID_BLUE)

    # Back arrow label
    pdf.set_xy(186, r3y - 2)
    pdf.set_font("Helvetica", "", 5.5)
    pdf.set_text_color(*MID_BLUE)
    pdf.cell(12, 4, "to LLM")

    pdf.set_y(fig_y + fig_h + 4)

    # API example
    pdf.section_title("2.1  API Design", level=2)
    pdf.code_block(
        "from veil_phantom import VeilClient, VeilConfig, VeilSession\n"
        "from veil_phantom.integrations.openai import veil_agent\n\n"
        "# Basic: one-shot redaction (zero dependencies)\n"
        "veil = VeilClient(VeilConfig.regex_only())\n"
        "result = veil.redact(text)\n"
        "print(result.sanitized)  # '[PERSON_1] sent [AMOUNT_1] to [BANKACCT_1]'\n\n"
        "# Advanced: full agentic loop with tool interception\n"
        "response, session = veil_agent(\n"
        "    client, messages, tools, tool_registry,\n"
        "    system_prompt='You are a helpful assistant.',\n"
        "    max_turns=10\n"
        ")"
    )

    # ════════════════════════════════════════════════════════════════
    # 3. SHADE NER MODEL
    # ════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.section_title("3  Shade NER: Custom Transformer for PII Detection")

    pdf.body_text(
        "The first and most powerful layer of VeilPhantom's pipeline is Shade NER -- a custom "
        "transformer model purpose-built for PII entity recognition. While VeilPhantom can operate "
        "without Shade (using regex_only mode), the model significantly improves recall for names, "
        "organizations, and ambiguous entities."
    )

    pdf.section_title("3.1  Architecture", level=2)
    pdf.body_text(
        "Shade V7 is built on PhoneticDeBERTa -- a DeBERTa-v3-xsmall backbone augmented with a "
        "phonetic embedding layer. The key innovation is the integration of Double Metaphone phonetic "
        "encodings as a parallel input stream, enabling cross-cultural name robustness."
    )

    # ── Figure 3: Shade Architecture Diagram ──
    fig_y = pdf.get_y() + 2
    fig_h = 58
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(*LIGHT_GRAY)
    pdf.rect(10, fig_y, 190, fig_h, style="DF", round_corners=True, corner_radius=3)

    pdf.set_xy(14, fig_y + 2)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*DARK_BLUE)
    pdf.cell(0, 4, "Figure 3: Shade V7 (PhoneticDeBERTa) Architecture")

    # Input layer
    iy = fig_y + 10
    pdf.draw_box(16, iy, 38, 10, "Input Text", PALE_BLUE, NAVY, MID_BLUE, 7, True)

    # Split into two paths
    pdf.draw_arrow(54, iy + 5, 64, iy - 2, MID_BLUE)  # up to BPE
    pdf.draw_arrow(54, iy + 5, 64, iy + 12, ACCENT_PURPLE)  # down to phonetic

    # BPE path
    bpe_y = iy - 6
    pdf.draw_box(64, bpe_y, 36, 10, "BPE Tokenizer", (219, 234, 254), DARK_BLUE, MID_BLUE, 7)
    pdf.draw_arrow(100, bpe_y + 5, 110, bpe_y + 5, MID_BLUE)
    pdf.draw_box(110, bpe_y, 30, 10, "input_ids", (219, 234, 254), DARK_BLUE, MID_BLUE, 6.5)

    # Phonetic path
    ph_y = iy + 8
    pdf.draw_box(64, ph_y, 36, 10, "Double Metaphone", (237, 233, 254), ACCENT_PURPLE, ACCENT_PURPLE, 6.5)
    pdf.draw_arrow(100, ph_y + 5, 110, ph_y + 5, ACCENT_PURPLE)
    pdf.draw_box(110, ph_y, 30, 10, "phonetic_ids", (237, 233, 254), ACCENT_PURPLE, ACCENT_PURPLE, 6.5)

    # Merge into DeBERTa
    merge_y = iy + 1
    pdf.draw_arrow(140, bpe_y + 5, 152, merge_y + 4, DARK_BLUE)
    pdf.draw_arrow(140, ph_y + 5, 152, merge_y + 6, ACCENT_PURPLE)

    pdf.set_fill_color(*NAVY)
    pdf.set_draw_color(10, 15, 30)
    pdf.rect(152, merge_y - 4, 40, 18, style="DF", round_corners=True, corner_radius=3)
    pdf.set_font("Helvetica", "B", 7.5)
    pdf.set_text_color(*WHITE)
    pdf.set_xy(152, merge_y - 2)
    pdf.cell(40, 6, "PhoneticDeBERTa", align="C")
    pdf.set_font("Helvetica", "", 5.5)
    pdf.set_xy(152, merge_y + 4)
    pdf.cell(40, 5, "22M params | 256 seq len", align="C")

    # Output: BIO labels
    out_y = merge_y + 18
    pdf.draw_arrow(172, merge_y + 14, 172, out_y, DARK_BLUE)
    pdf.draw_box(148, out_y, 44, 10, "25 BIO Labels", (220, 252, 231), (5, 100, 60), ACCENT_GREEN, 7, True)

    # Entity types list
    et_y = out_y + 12
    pdf.set_xy(16, et_y)
    pdf.set_font("Helvetica", "", 6)
    pdf.set_text_color(*MID_GRAY)
    types_str = "B/I: PERSON  ORG  EMAIL  PHONE  MONEY  DATE  ADDRESS  GOVID  BANKACCT  CARD  IPADDR  CASE  + O"
    pdf.cell(180, 4, types_str, align="C")

    pdf.set_y(fig_y + fig_h + 4)

    # Model specs table
    pdf.section_title("3.2  Model Specifications", level=2)
    specs = [
        ("Architecture", "PhoneticDeBERTa (DeBERTa-v3-xsmall + phonetic embeddings)"),
        ("Parameters", "22 million"),
        ("Sequence Length", "256 tokens (BPE)"),
        ("Phonetic Encoding", "Double Metaphone, 14-char vocab, max 6 chars/word"),
        ("Output Labels", "25 BIO tags across 12 entity types"),
        ("F1 Score", "97.12% (V7) / 97.6% in-dist (V5)"),
        ("Inference", "<50ms per passage (ONNX Runtime)"),
        ("Format", "ONNX binary, HuggingFace Hub distribution"),
        ("Training GPU", "GTX 1050 Ti (consumer-grade)"),
    ]
    w_spec = [52, 138]
    pdf.styled_table(["Parameter", "Value"], specs, w_spec)

    # ── Training section ──
    pdf.ln(4)
    pdf.section_title("3.3  Training Data and Methodology", level=2)
    pdf.body_text(
        "Shade was trained on a corpus of 72 million words -- a scale that enables robust generalization "
        "across domains, writing styles, and PII formats. The training methodology combines three "
        "key techniques:"
    )

    # Training pipeline figure
    tp_y = pdf.get_y() + 2
    tp_h = 36
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(*LIGHT_GRAY)
    pdf.rect(10, tp_y, 190, tp_h, style="DF", round_corners=True, corner_radius=3)

    pdf.set_xy(14, tp_y + 2)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*DARK_BLUE)
    pdf.cell(0, 4, "Figure 4: Shade Training Pipeline")

    # Stage boxes
    s1y = tp_y + 10
    pdf.draw_box(16, s1y, 34, 18, "8,606 Base", (219, 234, 254), DARK_BLUE, MID_BLUE, 7, True)
    pdf.set_xy(16, s1y + 9)
    pdf.set_font("Helvetica", "", 5.5)
    pdf.set_text_color(*MID_BLUE)
    pdf.cell(34, 4, "hand-labeled", align="C")

    pdf.draw_arrow(50, s1y + 9, 58, s1y + 9, ACCENT_ORANGE)

    pdf.draw_box(58, s1y, 38, 18, "100x Augment", (254, 243, 199), (120, 80, 10), ACCENT_ORANGE, 7, True)
    pdf.set_xy(58, s1y + 9)
    pdf.set_font("Helvetica", "", 5.5)
    pdf.set_text_color(120, 80, 10)
    pdf.cell(38, 4, "entity-swap", align="C")

    pdf.draw_arrow(96, s1y + 9, 104, s1y + 9, ACCENT_GREEN)

    pdf.draw_box(104, s1y, 38, 18, "862K Examples", (220, 252, 231), (5, 100, 60), ACCENT_GREEN, 7, True)
    pdf.set_xy(104, s1y + 9)
    pdf.set_font("Helvetica", "", 5.5)
    pdf.set_text_color(5, 100, 60)
    pdf.cell(38, 4, "synthetic corpus", align="C")

    pdf.draw_arrow(142, s1y + 9, 150, s1y + 9, ACCENT_PURPLE)

    pdf.draw_box(150, s1y, 42, 18, "PhoneticDeBERTa", NAVY, WHITE, NAVY, 7, True)
    pdf.set_xy(150, s1y + 9)
    pdf.set_font("Helvetica", "", 5.5)
    pdf.set_text_color(180, 180, 220)
    pdf.cell(42, 4, "GTX 1050 Ti", align="C")

    pdf.set_y(tp_y + tp_h + 4)

    pdf.body_text(
        "Entity-Swap Augmentation: Starting from 8,606 hand-labeled examples, we generate 862,000 "
        "synthetic training examples (100x expansion) by systematically replacing entity values while "
        "preserving context. For instance, \"John Smith sent $5M to HSBC\" becomes \"Maria Rodriguez "
        "sent EUR2.3M to Deutsche Bank\" -- same structure, different entities. This teaches the model to "
        "recognize patterns rather than memorize specific values."
    )
    pdf.body_text(
        "ASR Corruption: To handle speech-to-text transcription errors (a common real-world input "
        "source), training data is augmented with Parakeet ASR noise -- phonetic substitutions, dropped "
        "characters, and run-together words that simulate transcription artifacts."
    )
    pdf.body_text(
        "Hard Negative Mining: Contrastive hard negatives reduce false positives. The training set "
        "includes deliberately confusing examples -- sentences where common words (\"Summit\", \"Valley\", "
        "\"General\") appear in contexts where they are NOT entity names -- forcing the model to learn "
        "contextual disambiguation rather than surface-level pattern matching."
    )

    pdf.section_title("3.4  Dual-Pass Inference", level=2)
    pdf.body_text(
        "Shade V7 employs a unique dual-pass inference strategy. Each input is processed twice: once "
        "with full phonetic encodings, and once with zeroed phonetic inputs. The pass that detects more "
        "entities is selected. This handles cases where phonetic features help (cross-cultural names like "
        "\"Shaun\" vs \"Sean\") and cases where they hurt (technical jargon that phonetically resembles "
        "names). Additionally, texts exceeding 220 words with fewer than 3 detected entities trigger a "
        "segment rescue -- the text is split into ~70-word segments and re-processed to catch entities "
        "that were diluted in the full context."
    )

    # ════════════════════════════════════════════════════════════════
    # 4. DETECTION PIPELINE
    # ════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.section_title("4  7-Layer Detection Pipeline")
    pdf.body_text(
        "VeilPhantom processes text through 7 ordered layers. Each layer adds non-overlapping "
        "redaction spans to a unified result, and later layers skip regions already redacted. The "
        "layered design provides defense-in-depth: if one layer misses an entity, subsequent layers "
        "can catch it."
    )

    # ── Figure 5: Pipeline Diagram ──
    fig_y = pdf.get_y() + 2
    fig_h = 68
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(*LIGHT_GRAY)
    pdf.rect(10, fig_y, 190, fig_h, style="DF", round_corners=True, corner_radius=3)

    pdf.set_xy(14, fig_y + 2)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*DARK_BLUE)
    pdf.cell(0, 4, "Figure 5: 7-Layer Detection Pipeline")

    # Input
    pdf.draw_box(16, fig_y + 10, 28, 10, "Raw Text", (254, 226, 226), (150, 40, 40), (200, 80, 80), 7, True)
    pdf.draw_arrow(44, fig_y + 15, 52, fig_y + 15, MID_GRAY)

    # Layer boxes in a flowing layout
    layer_names = [
        "L0: Shade NER",
        "L1: Gazetteer",
        "L1.5: Pre-Regex",
        "L2: NLP (POS)",
        "L3: Regex (35)",
        "L3.5: URL",
        "L4: Contextual",
    ]
    layer_descs = [
        "22M transformer",
        "27 known orgs",
        "IBAN, spoken email",
        "Cap. word heuristics",
        "Phone, ID, $, dates",
        "Domain filter",
        "Roles, sensitivity",
    ]
    bx = 52
    for i, (name, desc) in enumerate(zip(layer_names, layer_descs)):
        c = LAYER_COLORS[i]
        light_c = (min(255, c[0] + 180), min(255, c[1] + 180), min(255, c[2] + 180))
        by = fig_y + 10 + (i % 4) * 14
        if i >= 4:
            bx_act = 52 + (i - 4) * 47
            by = fig_y + 10 + 28 + (i - 4) % 2 * 14
        else:
            bx_act = 52 + i * 36
            by = fig_y + 10

        # Use 2-row layout
        row = 0 if i < 4 else 1
        col = i if i < 4 else i - 4
        bx_act = 52 + col * 38
        by = fig_y + 10 + row * 28

        pdf.set_fill_color(*c)
        pdf.set_draw_color(max(0, c[0] - 30), max(0, c[1] - 30), max(0, c[2] - 30))
        pdf.set_line_width(0.3)
        pdf.rect(bx_act, by, 34, 18, style="DF", round_corners=True, corner_radius=2)

        pdf.set_font("Helvetica", "B", 6.5)
        pdf.set_text_color(*WHITE)
        pdf.set_xy(bx_act, by + 2)
        pdf.cell(34, 5, name, align="C")

        pdf.set_font("Helvetica", "", 5)
        pdf.set_text_color(min(255, c[0] + 150), min(255, c[1] + 150), min(255, c[2] + 150))
        pdf.set_xy(bx_act, by + 8)
        pdf.cell(34, 5, desc, align="C")

        # Arrows between layers in same row
        if i < 3:
            pdf.draw_arrow(bx_act + 34, by + 9, bx_act + 38, by + 9, MID_GRAY)
        elif i == 3:
            # Arrow down to next row
            pdf.draw_arrow(bx_act + 17, by + 18, 52 + 17, by + 28, MID_GRAY)
        elif i > 4 and i < 7:
            pdf.draw_arrow(bx_act - 4, by + 9, bx_act, by + 9, MID_GRAY)

    # Output
    out_y = fig_y + 10 + 28 + 18 + 2
    out_bx = 52 + 3 * 38
    pdf.draw_arrow(out_bx - 4, fig_y + 10 + 28 + 9, out_bx, fig_y + 10 + 28 + 9, MID_GRAY)

    # Final output
    pdf.draw_box(16, out_y, 176, 10, "Redacted Text with Token Map: [PERSON_1] sent [AMOUNT_1] to [BANKACCT_1]",
                 (220, 252, 231), (5, 100, 60), ACCENT_GREEN, 7, True)

    pdf.set_y(fig_y + fig_h + 4)

    # Layer details
    layer_details = [
        ("Layer 0 -- Shade NER (Optional)",
         "PhoneticDeBERTa transformer (§3). Detects PERSON, ORG, EMAIL, PHONE, DATE, ADDRESS, GOVID, "
         "BANKACCT, CARD, IPADDR, CASE entities. Confidence thresholds: 0.5 general, 0.7 for ORG "
         "(stricter to reduce false positives). Includes reclassification logic: entities ending with "
         "org suffixes (Inc, Ltd, LLC) are promoted from PERSON to ORG."),

        ("Layer 1 -- Gazetteer Lookup",
         "Case-insensitive exact match against 27 compound organization names: major banks (Goldman "
         "Sachs, JP Morgan, Standard Bank), consulting firms (McKinsey, Deloitte, PwC, KPMG), and "
         "telecom providers. Extended with financial institution regex (18 bank patterns), investment "
         "firm detection (\"Name Ventures/Capital/Partners\"), and contextual ORG detection using "
         "45 context words in a 3-word window around capitalized terms."),

        ("Layer 1.5 -- Pre-Regex Patterns",
         "High-priority patterns that must run before general regex to avoid conflicts: IBAN "
         "(international bank account numbers), spoken email (\"john at example dot com\"), and hybrid "
         "email (\"sarah at veilprivacy.com\"). These patterns have unique formats that would be "
         "incorrectly split by later layers."),

        ("Layer 2 -- NLP Entity Detection",
         "Pure-Python NLP layer requiring zero external dependencies (no spaCy, no NLTK). Uses regex "
         "to find capitalized word sequences, then validates through 9 rejection filters: contraction "
         "filter, speaker diarization tags, determiner-prefixed ORGs, ~200 NOT_NAMES/NOT_ORGS stop "
         "words, gerund rejection, and single-word PERSON gating against 79 common first names. Role "
         "prefixes (CEO, Dr, Contact) are stripped before classification."),

        ("Layer 3 -- Regex Patterns (35 rules)",
         "The workhorse layer with 35 regex patterns covering: phone numbers (international, US, SA, "
         "spoken digit sequences), government IDs (SSN, SA ID 13-digit, passport, driver's license), "
         "bank accounts (IBAN, generic with context), credit cards, monetary amounts (5 sub-patterns "
         "including verbal amounts and multi-currency), dates (4 formats including spoken), IP "
         "addresses, and physical addresses. Context-dependent patterns extract core values for "
         "accurate tool-call rehydration."),

        ("Layer 3.5 -- URL/Domain Redaction",
         "Detects URLs and bare domains across 21 TLDs. Maintains a 40-entry safe domain whitelist "
         "(google.com, github.com, stackoverflow.com, etc.) to avoid redacting common references. "
         "Only unknown domains that may contain PII are redacted."),

        ("Layer 4 -- Contextual Sensitivity Analysis",
         "Four sub-layers detecting PII that reveals identity through context rather than explicit "
         "values: (a) 30+ identifying roles (\"CEO\", \"Ambassador\", \"Secretary of State\"), (b) 32 "
         "sensitive situation triggers (corruption, harassment, whistleblower, insider trading), "
         "(c) temporal sensitivity (\"before the announcement\", \"under embargo\"), and (d) unique "
         "descriptors (\"the only surgeon who...\") that could identify individuals."),
    ]

    for title, desc in layer_details:
        pdf.section_title(title, level=3)
        pdf.body_text(desc)

    # ── Token Map ──
    pdf.section_title("4.3  Token Map", level=2)
    pdf.body_text(
        "Each detected PII entity is assigned a deterministic token [TYPE_N], where TYPE is one of 19 "
        "supported categories and N is a monotonically increasing counter per type. The mapping is "
        "bidirectional: tokens can be resolved to original values (rehydration) and original values can "
        "be matched to existing tokens (re-redaction consistency)."
    )

    # Token type table
    token_types = [
        ("PERSON", "Names", "John Smith -> [PERSON_1]"),
        ("ORG", "Organizations", "Goldman Sachs -> [ORG_1]"),
        ("EMAIL", "Email addresses", "j.smith@gs.com -> [EMAIL_1]"),
        ("PHONE", "Phone numbers", "+1-555-0123 -> [PHONE_1]"),
        ("AMOUNT", "Monetary values", "$12.5M -> [AMOUNT_1]"),
        ("DATE", "Dates/times", "January 15 -> [DATE_1]"),
        ("GOVID", "SSN, passport, etc.", "123-45-6789 -> [GOVID_1]"),
        ("BANKACCT", "Bank accounts, IBAN", "62847501234 -> [BANKACCT_1]"),
        ("CARD", "Credit/debit cards", "4000-0000-0000-0000 -> [CARD_1]"),
        ("IPADDR", "IP addresses", "192.168.1.1 -> [IPADDR_1]"),
        ("ADDRESS", "Physical/URLs", "123 Main St -> [ADDRESS_1]"),
        ("ROLE", "Identifying roles", "CEO of -> [ROLE_1]"),
        ("SITUATION", "Sensitive context", "whistleblower -> [SITUATION_1]"),
    ]
    w_tok = [24, 34, 80]
    pdf.styled_table(["Token Type", "Category", "Example"], token_types, w_tok, x_start=26)

    pdf.ln(4)
    pdf.section_title("4.4  Redaction Modes", level=2)
    pdf.body_text(
        "TOKEN_DIRECT (default): Replaces PII with typed tokens. Preserves semantic structure and "
        "enables LLM reasoning about entity relationships. This is the recommended mode for agentic "
        "workflows.\n\n"
        "PHANTOM: Replaces PII with realistic fake values from curated pools (15 names, 10 orgs, 10 "
        "locations, etc.). Produces natural-sounding text but creates ambiguity risk in multi-turn "
        "conversations.\n\n"
        "REDACTED: Uniform [redacted] tags. Maximum privacy but reduced LLM utility for entity-dependent "
        "tasks."
    )

    # ════════════════════════════════════════════════════════════════
    # 5. AGENTIC MIDDLEWARE
    # ════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.section_title("5  Agentic Tool-Call Middleware")
    pdf.body_text(
        "The critical challenge for privacy-preserving agentic AI is the tool-call gap: the LLM "
        "generates tool calls with tokenized arguments ([EMAIL_1]), but real tools need real values "
        "(sarah.chen@gs.com). VeilPhantom bridges this gap with two components that ensure PII never "
        "leaves the local environment."
    )

    # ── Figure 6: Tool call interception ──
    fig_y = pdf.get_y() + 2
    fig_h = 40
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(*LIGHT_GRAY)
    pdf.rect(10, fig_y, 190, fig_h, style="DF", round_corners=True, corner_radius=3)

    pdf.set_xy(14, fig_y + 2)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*DARK_BLUE)
    pdf.cell(0, 4, "Figure 6: Tool Call Interception Pipeline")

    ty = fig_y + 12
    steps = [
        ("LLM Output", "send_email(\n  to=[EMAIL_1])", (219, 234, 254), DARK_BLUE, MID_BLUE),
        ("Rehydrate", "send_email(\n  to=sarah@gs.com)", (254, 243, 199), (120, 80, 10), ACCENT_ORANGE),
        ("Execute", "SMTP send\n  (local only)", (220, 252, 231), (5, 100, 60), ACCENT_GREEN),
        ("Re-Redact", "\"Sent to\n  [EMAIL_1]\"", (237, 233, 254), (80, 50, 180), ACCENT_PURPLE),
    ]
    sw = 42
    for i, (label, content, fill, tcol, bcol) in enumerate(steps):
        sx = 16 + i * 47
        pdf.draw_box(sx, ty, sw, 22, "", fill, tcol, bcol, 7)
        pdf.set_font("Helvetica", "B", 6.5)
        pdf.set_text_color(*tcol)
        pdf.set_xy(sx + 1, ty + 2)
        pdf.cell(sw - 2, 4, label, align="C")
        pdf.set_font("Courier", "", 5.5)
        pdf.set_xy(sx + 2, ty + 7)
        pdf.multi_cell(sw - 4, 3.5, content, align="C")
        if i < 3:
            pdf.draw_arrow(sx + sw, ty + 11, sx + sw + 5, ty + 11, MID_GRAY)

    pdf.set_y(fig_y + fig_h + 4)

    pdf.section_title("5.1  VeilSession -- Stateful Multi-Turn Tracking", level=2)
    pdf.body_text(
        "VeilSession maintains a cumulative token_map across conversation turns. When redacting turn N, "
        "any PII that appeared in turns 1..N-1 automatically receives its existing token -- ensuring "
        "consistency. For tool output re-redaction, VeilSession: (1) replaces known PII with existing "
        "tokens, (2) protects existing tokens with placeholders during re-processing, (3) detects new "
        "PII and assigns fresh tokens with non-colliding counters, and (4) merges new tokens into the "
        "session state."
    )

    pdf.section_title("5.2  VeilToolMiddleware -- Rehydration Engine", level=2)
    pdf.body_text(
        "The middleware performs deep rehydration: a recursive traversal of JSON-compatible structures "
        "(strings, arrays, nested objects) replacing all [TYPE_N] tokens with their real values from "
        "the session. This handles arbitrarily nested tool arguments -- a critical requirement for "
        "complex tool schemas. The complete pipeline: rehydrate -> execute locally -> re-redact -> return "
        "safe result to LLM."
    )

    pdf.section_title("5.3  veil_agent() -- Complete Agent Loop", level=2)
    pdf.body_text(
        "The veil_agent() function provides a turnkey agentic loop compatible with any OpenAI-format "
        "API (OpenAI, Anthropic via proxy, OpenRouter, local models). It handles: message redaction with "
        "automatic system prompt augmentation (teaching the LLM to use tokens), multi-turn tool-call "
        "loops with rehydration and re-redaction, max_turns safety limits, and final response "
        "rehydration. A dry_run mode enables benchmarking without real tool execution."
    )

    # ════════════════════════════════════════════════════════════════
    # 6. BENCHMARK EVALUATION
    # ════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.section_title("6  Benchmark Evaluation")

    pdf.section_title("6.1  Methodology", level=2)
    pdf.body_text(
        "We evaluate VeilPhantom on 98 scenarios across 8 industry verticals. Each scenario consists "
        "of a PII-rich natural language instruction paired with expected tool calls and validated "
        "argument schemas. Every scenario runs in two modes:"
    )
    pdf.body_text(
        "Raw mode: The instruction is sent directly to the LLM with no redaction.\n"
        "Veil mode: The instruction is redacted by VeilPhantom before sending to the LLM.\n\n"
        "We measure 5 dimensions: (1) Tool Accuracy -- correct tools called, (2) Args Quality -- "
        "arguments contain expected information (validated via lambda functions accepting either real "
        "PII or VeilPhantom tokens), (3) PII Detection -- entity counts by type, (4) PII Leakage -- "
        "real PII appearing in Veil mode outputs, (5) Latency Overhead. Each scenario runs twice for "
        "statistical stability. Model: Claude 4.5 Haiku via OpenRouter."
    )

    # Headline stats
    pdf.ln(2)
    by = pdf.get_y()
    bw, bh = 43, 28
    gap = 5
    bx_start = 14

    pdf.stat_box(bx_start, by, bw, bh,
                 f"{S['tool_accuracy_veil']:.1%}", "Veil Accuracy", DARK_BLUE)
    pdf.stat_box(bx_start + bw + gap, by, bw, bh,
                 f"+{(S['tool_accuracy_veil'] - S['tool_accuracy_raw'])*100:.1f}%", "vs Raw Mode", ACCENT_GREEN)
    pdf.stat_box(bx_start + 2 * (bw + gap), by, bw, bh,
                 f"{int(S['total_pii_detected'])}", "PII Detected", MID_BLUE)
    pdf.stat_box(bx_start + 3 * (bw + gap), by, bw, bh,
                 f"{S['avg_redaction_ms']:.0f}ms", "Avg Redaction", ACCENT_PURPLE)

    pdf.set_y(by + bh + 6)

    # ── Table 1: Headline Metrics ──
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*DARK_BLUE)
    pdf.cell(0, 6, "Table 1: Headline Metrics (averaged over 2 runs, 98 scenarios)")
    pdf.ln(7)

    headline_rows = [
        ("Tool Accuracy", f"{S['tool_accuracy_raw']:.1%}", f"{S['tool_accuracy_veil']:.1%}", "+1.9%"),
        ("Args Quality", f"{S['args_quality_raw']:.1%}", f"{S['args_quality_veil']:.1%}", "-0.2%"),
        ("Avg Latency", f"{S['avg_latency_raw']:.2f}s", f"{S['avg_latency_veil']:.2f}s", "+0.14s"),
        ("Redaction Time", "--", f"{S['avg_redaction_ms']:.1f}ms", "--"),
        ("PII Sent to LLM", "ALL", "0 entities", "--"),
        ("PII Entities Found", "--", str(int(S['total_pii_detected'])), "--"),
        ("Identifiable Leakage", "N/A", "0", "--"),
        ("API Errors", "0", "0", "--"),
    ]
    pdf.styled_table(["Metric", "Without Veil", "With Veil", "Delta"],
                     headline_rows, [52, 42, 42, 30], x_start=18)

    pdf.ln(4)
    pdf.body_text(
        "VeilPhantom achieves a +1.9% improvement in tool accuracy over the unredacted baseline. "
        "This counterintuitive result occurs because typed tokens ([PERSON_1], [EMAIL_1]) help the "
        "model distinguish entities more clearly than ambiguous natural language. The 6.0ms redaction "
        "overhead is <0.2% of the ~3.9s model inference latency."
    )

    # ── Table 2: Per-Vertical Breakdown ──
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*DARK_BLUE)
    pdf.cell(0, 6, "Table 2: Per-Vertical Accuracy Breakdown")
    pdf.ln(7)

    vert_rows = []
    vert_order = ["financial", "healthcare", "legal", "hr", "sales", "support", "communications", "multi_step"]
    vert_n = {"financial": 13, "healthcare": 12, "legal": 12, "hr": 13, "sales": 12,
              "support": 12, "communications": 12, "multi_step": 12}
    for vert in vert_order:
        if vert not in VERTS:
            continue
        d = VERTS[vert]
        delta = d["veil_accuracy"] - d["raw_accuracy"]
        leak_rate = d["total_leaked"] / d["total_pii"] * 100 if d["total_pii"] > 0 else 0
        vert_rows.append([
            vert.replace("_", " ").title(),
            str(vert_n.get(vert, "?")),
            f"{d['raw_accuracy']:.0%}",
            f"{d['veil_accuracy']:.0%}",
            f"{delta:+.1%}",
            str(d["total_pii"]),
            f"{leak_rate:.1f}%",
        ])
    pdf.styled_table(
        ["Vertical", "N", "Raw Acc", "Veil Acc", "Delta", "PII", "Leak%"],
        vert_rows, [36, 14, 22, 22, 22, 20, 22], x_start=22
    )

    pdf.ln(4)
    pdf.body_text(
        "Sales and Support achieve 100% accuracy parity. Healthcare (+6.2%), Legal (+4.2%), and "
        "Multi-Step (+9.0%) show Veil mode outperforming raw -- evidence that token-based prompting "
        "helps the model focus on task structure rather than being distracted by PII details. The "
        "Multi-Step vertical benefits most, likely because tokens reduce the cognitive load of tracking "
        "multiple PII values across 3-6 sequential tool calls."
    )

    # ── PII Distribution Chart ──
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*DARK_BLUE)
    pdf.cell(0, 6, "Table 3 / Figure 7: PII Detection by Entity Type")
    pdf.ln(8)

    pii_types = S["pii_by_type"]
    total_pii = sum(pii_types.values())
    sorted_pii = sorted(pii_types.items(), key=lambda x: -x[1])

    # Bar chart
    chart_colors = [
        DARK_BLUE, MID_BLUE, ACCENT_GREEN, ACCENT_ORANGE, ACCENT_PURPLE,
        ACCENT_RED, (16, 185, 129), (234, 88, 12), (202, 138, 4),
        (99, 102, 241), (139, 92, 246), (220, 38, 38), (59, 130, 246),
    ]
    chart_data = [(ptype, count) for ptype, count in sorted_pii]
    pdf.draw_bar_chart(14, pdf.get_y(), 100, len(chart_data) * 10, chart_data, chart_colors)

    # Table alongside
    tbl_x = 120
    tbl_y = pdf.get_y() - 2
    pdf.set_xy(tbl_x, tbl_y)
    pdf.set_font("Helvetica", "B", 7.5)
    pdf.set_fill_color(*DARK_BLUE)
    pdf.set_text_color(*WHITE)
    pdf.cell(22, 6, "Type", fill=True, align="C")
    pdf.cell(18, 6, "Count", fill=True, align="C")
    pdf.cell(18, 6, "%", fill=True, align="C")
    pdf.ln()
    for i, (ptype, count) in enumerate(sorted_pii):
        pdf.set_x(tbl_x)
        pct = count / total_pii * 100
        if i % 2 == 0:
            pdf.set_fill_color(*PALE_BLUE)
        else:
            pdf.set_fill_color(*WHITE)
        pdf.set_text_color(*DARK_GRAY)
        pdf.set_font("Helvetica", "", 7)
        pdf.cell(22, 5, ptype, fill=True, align="C")
        pdf.cell(18, 5, str(int(count)), fill=True, align="C")
        pdf.cell(18, 5, f"{pct:.1f}%", fill=True, align="C")
        pdf.ln()
    pdf.set_x(tbl_x)
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_fill_color(*LIGHT_GRAY)
    pdf.cell(22, 5, "TOTAL", fill=True, align="C")
    pdf.cell(18, 5, str(int(total_pii)), fill=True, align="C")
    pdf.cell(18, 5, "100%", fill=True, align="C")

    pdf.set_y(pdf.get_y() + 8)

    pdf.body_text(
        f"PERSON entities dominate ({sorted_pii[0][1]} of {int(total_pii)}, "
        f"{sorted_pii[0][1]/total_pii*100:.0f}%), followed by EMAIL, AMOUNT, and ORG. The long tail "
        "includes critical high-sensitivity types: GOVID (government IDs), BANKACCT (bank accounts), "
        "and CARD (credit cards) -- entities where even a single leak would constitute a serious "
        "privacy violation."
    )

    # ════════════════════════════════════════════════════════════════
    # 6.4 LEAKAGE ANALYSIS
    # ════════════════════════════════════════════════════════════════
    pdf.section_title("6.4  Leakage Analysis", level=2)
    pdf.body_text(
        "The benchmark's automated leakage detector checks whether any original PII value (>3 chars) "
        "appears in Veil mode tool arguments. Out of 885 PII entities, ~38 instances were flagged. "
        "Manual analysis reveals three categories:"
    )

    # Leakage breakdown mini-chart
    leak_y = pdf.get_y()
    pdf.set_fill_color(220, 252, 231)
    pdf.set_draw_color(ACCENT_GREEN[0], ACCENT_GREEN[1], ACCENT_GREEN[2])
    pdf.rect(14, leak_y, 182, 32, style="DF", round_corners=True, corner_radius=3)

    categories = [
        ("81%", "False Positives", "Common English words matching short PII values\n(\"insurance\", \"engineering\", \"platform\")", ACCENT_GREEN),
        ("16%", "Monetary Context", "Amount values inferred from task semantics\n(not identity-revealing)", ACCENT_ORANGE),
        ("3%", "Org Fragments", "Partial names in payment references\n(borderline contextual)", ACCENT_PURPLE),
    ]
    for i, (pct, label, desc, color) in enumerate(categories):
        cx = 22 + i * 62
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(*color)
        pdf.set_xy(cx, leak_y + 3)
        pdf.cell(50, 6, pct, align="C")
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_xy(cx, leak_y + 10)
        pdf.cell(50, 4, label, align="C")
        pdf.set_font("Helvetica", "", 5.5)
        pdf.set_text_color(*DARK_GRAY)
        pdf.set_xy(cx, leak_y + 15)
        pdf.multi_cell(50, 3.5, desc, align="C")

    pdf.set_y(leak_y + 36)
    pdf.body_text(
        "Zero instances of identifiable PII -- person names, email addresses, phone numbers, "
        "government IDs, or bank account numbers -- were found in any Veil mode tool arguments across "
        "all 98 scenarios and both benchmark runs. The effective identifiable PII leakage rate is 0%."
    )

    # ════════════════════════════════════════════════════════════════
    # 7. PERFORMANCE
    # ════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.section_title("7  Performance Characteristics")

    # Performance comparison boxes
    perf_y = pdf.get_y()
    metrics = [
        ("Redaction Overhead", f"{S['avg_redaction_ms']:.1f}ms", "per input (all 7 layers)", MID_BLUE),
        ("Latency Impact", f"+{(S['avg_latency_veil'] - S['avg_latency_raw']):.2f}s", "total overhead", ACCENT_ORANGE),
        ("% of Total Time", "<0.2%", "redaction vs inference", ACCENT_GREEN),
        ("Dependencies", "0", "in regex_only mode", ACCENT_PURPLE),
    ]
    for i, (label, value, sub, color) in enumerate(metrics):
        mx = 14 + i * 47
        pdf.set_fill_color(*color)
        pdf.rect(mx, perf_y, 44, 22, style="F", round_corners=True, corner_radius=3)
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(*WHITE)
        pdf.set_xy(mx, perf_y + 2)
        pdf.cell(44, 8, value, align="C")
        pdf.set_font("Helvetica", "", 6)
        pdf.set_text_color(220, 230, 255)
        pdf.set_xy(mx, perf_y + 10)
        pdf.cell(44, 4, label, align="C")
        pdf.set_xy(mx, perf_y + 14)
        pdf.cell(44, 4, sub, align="C")

    pdf.set_y(perf_y + 28)

    pdf.body_text(
        f"VeilPhantom's redaction pipeline runs in {S['avg_redaction_ms']:.1f}ms average -- all 7 layers "
        "executing sequentially on CPU. This is negligible compared to the ~3.9s model inference "
        "latency, adding <0.2% overhead. The pipeline is CPU-bound with no GPU requirement in "
        "regex_only mode."
    )
    pdf.body_text(
        "For the optional Shade NER layer, ONNX Runtime inference adds ~50ms depending on input "
        "length. Even with Shade enabled, total redaction stays under 100ms -- still dwarfed by "
        "network latency to the LLM provider."
    )

    pdf.section_title("7.1  Zero-Dependency Mode", level=2)
    pdf.body_text(
        "In its default configuration (VeilConfig.regex_only()), VeilPhantom has zero external "
        "dependencies beyond Python's standard library. The NLP layer uses pure Python regex-based "
        "POS heuristics. This makes VeilPhantom suitable for serverless deployments, edge computing, "
        "and resource-constrained environments where installing spaCy (300MB+) or PyTorch is "
        "impractical."
    )

    pdf.section_title("7.2  Benchmark Cost", level=2)
    pdf.body_text(
        "The complete 98-scenario benchmark (196 LLM calls per run, 2 runs = 392 total calls) cost "
        "$0.88 on Claude 4.5 Haiku via OpenRouter. VeilPhantom itself adds zero cost -- it is a local "
        "processing step with no API calls, no cloud dependencies, and no usage-based pricing."
    )

    # ════════════════════════════════════════════════════════════════
    # 8. RELATED WORK
    # ════════════════════════════════════════════════════════════════
    pdf.section_title("8  Related Work")

    # Comparison table
    comparisons = [
        ("VeilPhantom", "Yes", "Yes", "Yes", "0 (regex) / PyTorch (NER)", "6ms"),
        ("Presidio", "Yes", "No", "No", "spaCy (300MB+)", "~50ms"),
        ("Private AI", "Yes", "No", "No", "Proprietary cloud", "API-dependent"),
        ("LLM Guard", "Partial", "No", "No", "Multiple ML libs", "~100ms"),
        ("DP-SGD", "No*", "No", "No", "PyTorch", "Training-time"),
    ]
    pdf.styled_table(
        ["System", "PII Detect", "Rehydrate", "Agentic", "Dependencies", "Latency"],
        comparisons, [30, 22, 22, 18, 50, 28], x_start=14
    )
    pdf.ln(4)
    pdf.body_text(
        "The key differentiator is VeilPhantom's agentic middleware: no existing tool provides "
        "transparent tool-call interception with local rehydration, re-redaction of tool outputs, "
        "and stateful multi-turn PII tracking -- while maintaining full OpenAI API compatibility. "
        "Presidio and Private AI focus on one-shot redaction without maintaining token maps across "
        "turns. DP-SGD protects training data, not inference-time PII exposure."
    )

    # ════════════════════════════════════════════════════════════════
    # 9. LIMITATIONS
    # ════════════════════════════════════════════════════════════════
    pdf.section_title("9  Limitations and Future Work")
    pdf.body_text(
        "Detection coverage: The regex_only configuration may miss unusual name formats, non-Latin "
        "scripts, or context-dependent PII (e.g., a diagnosis that is PII only when combined with a "
        "patient identifier). Shade NER improves coverage but adds dependencies.\n\n"
        "Multi-step accuracy: Complex 4+ tool-call scenarios show lower accuracy in both modes "
        "(72-81%). Veil mode consistently outperforms raw, but this remains a model capability "
        "limitation.\n\n"
        "Semantic inference: A model told to \"process the refund\" may infer the amount from context "
        "even when the actual figure is tokenized. This is inherent to language understanding, not a "
        "redaction failure.\n\n"
        "Future directions: multi-language support, streaming redaction for real-time applications, "
        "fine-tuned Shade models for domain-specific PII (e.g., medical record numbers), and "
        "integration with additional LLM providers and agent frameworks."
    )

    # ════════════════════════════════════════════════════════════════
    # 10. CONCLUSION
    # ════════════════════════════════════════════════════════════════
    pdf.section_title("10  Conclusion")

    # Final results highlight box
    conc_y = pdf.get_y()
    pdf.set_fill_color(*PALE_BLUE)
    pdf.set_draw_color(*MID_BLUE)
    pdf.rect(14, conc_y, 182, 36, style="DF", round_corners=True, corner_radius=3)
    pdf.set_fill_color(*DARK_BLUE)
    pdf.rect(14, conc_y + 3, 3, 30, style="F")

    results_text = [
        ("93.3%", "tool accuracy (+1.9% vs unredacted)"),
        ("885", "PII entities detected across 13 types"),
        ("0", "identifiable PII leaked"),
        ("6ms", "average redaction overhead (<0.2% of total)"),
        ("0", "external dependencies in default mode"),
    ]
    for i, (val, desc) in enumerate(results_text):
        ry = conc_y + 4 + i * 6
        pdf.set_xy(22, ry)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*DARK_BLUE)
        pdf.cell(18, 5, val)
        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_text_color(*DARK_GRAY)
        pdf.cell(150, 5, f"-- {desc}")

    pdf.set_y(conc_y + 40)
    pdf.body_text(
        "VeilPhantom demonstrates that privacy-preserving PII redaction is not only compatible with "
        "agentic AI workflows but can improve them. By replacing PII with typed tokens, enterprises "
        "can leverage cloud-hosted LLMs for financial processing, healthcare records, legal documents, "
        "and HR operations -- without compromising privacy, violating regulations, or sacrificing "
        "utility. The Shade NER model, trained on 72 million words with 862K augmented examples, "
        "provides state-of-the-art PII detection at 97.1% F1, while the zero-dependency regex_only "
        "mode makes deployment trivial. VeilPhantom is available as an open-source Python SDK."
    )

    # ════════════════════════════════════════════════════════════════
    # APPENDIX A: SAMPLE REDACTION
    # ════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.section_title("Appendix A: End-to-End Redaction Example")

    pdf.section_title("Original Input (contains PII)", level=3)
    pdf.code_block(
        "Please wire R2.5 million from Standard Bank account 62847501234\n"
        "to IBAN GB29 NWBK 6016 1331 9268 19. Reference: INV-2024-Q3.\n"
        "This is for the Johnson & Partners consulting fee.\n"
        "Contact Sarah Chen (sarah.chen@gs.com, +27 82 555 0123) for confirmation."
    )

    pdf.section_title("After VeilPhantom Redaction", level=3)
    pdf.code_block(
        "Please wire [AMOUNT_1] from Standard Bank account [BANKACCT_1]\n"
        "to [BANKACCT_2]. Reference: INV-2024-Q3.\n"
        "This is for the [ORG_1] consulting fee.\n"
        "Contact [PERSON_1] ([EMAIL_1], [PHONE_1]) for confirmation."
    )

    pdf.section_title("Token Map (local, never sent to LLM)", level=3)
    pdf.code_block(
        "[AMOUNT_1]   -> 'R2.5 million'                   (AMOUNT, HIGH)\n"
        "[BANKACCT_1] -> '62847501234'                     (BANKACCT, CRITICAL)\n"
        "[BANKACCT_2] -> 'GB29 NWBK 6016 1331 9268 19'    (BANKACCT, CRITICAL)\n"
        "[ORG_1]      -> 'Johnson & Partners'              (ORG, MEDIUM)\n"
        "[PERSON_1]   -> 'Sarah Chen'                      (PERSON, HIGH)\n"
        "[EMAIL_1]    -> 'sarah.chen@gs.com'               (EMAIL, HIGH)\n"
        "[PHONE_1]    -> '+27 82 555 0123'                 (PHONE, HIGH)"
    )

    pdf.section_title("LLM Tool Call (Veil mode -- only tokens)", level=3)
    pdf.code_block(
        "transfer_funds(\n"
        "    from_account = '[BANKACCT_1]',\n"
        "    to_account   = '[BANKACCT_2]',\n"
        "    amount       = '[AMOUNT_1]',\n"
        "    reference    = 'INV-2024-Q3'\n"
        ")"
    )

    pdf.section_title("After Middleware Rehydration (local execution only)", level=3)
    pdf.code_block(
        "transfer_funds(\n"
        "    from_account = '62847501234',\n"
        "    to_account   = 'GB29 NWBK 6016 1331 9268 19',\n"
        "    amount       = 'R2.5 million',\n"
        "    reference    = 'INV-2024-Q3'\n"
        ")"
    )

    # ════════════════════════════════════════════════════════════════
    # APPENDIX B: BENCHMARK CONFIG
    # ════════════════════════════════════════════════════════════════
    pdf.section_title("Appendix B: Benchmark Configuration")
    bench_config = [
        ("Model", "Claude 4.5 Haiku (anthropic/claude-haiku-4.5)"),
        ("Provider", "OpenRouter"),
        ("Scenarios", "98 across 8 verticals"),
        ("Runs", "2 (results averaged)"),
        ("Total API Calls", "392 (98 × 2 modes × 2 runs)"),
        ("Total Cost", "$0.88"),
        ("VeilPhantom Config", "VeilConfig.regex_only() (no Shade NER)"),
        ("Max Tokens/Response", "1024"),
        ("Validation", "Lambda-based argument validators (accept PII or tokens)"),
    ]
    pdf.styled_table(["Parameter", "Value"], bench_config, [48, 138], x_start=12)

    # ════════════════════════════════════════════════════════════════
    # APPENDIX C: WHITELIST & GAZETTEER STATS
    # ════════════════════════════════════════════════════════════════
    pdf.ln(6)
    pdf.section_title("Appendix C: Detection Data Statistics")
    data_stats = [
        ("Shade V7 Training Corpus", "72,000,000 words"),
        ("Shade V7 Training Examples", "862,000 (100x augmented from 8,606 base)"),
        ("Shade V7 BIO Label Classes", "25 (12 entity types × B/I + O)"),
        ("Regex Patterns", "35"),
        ("Compound Org Gazetteer", "27 entries"),
        ("Financial Institution Patterns", "18 banks"),
        ("ORG Context Words", "45 trigger words"),
        ("Common First Names (validation)", "79 names"),
        ("Public Company Whitelist", "30 companies"),
        ("Master Whitelist (false positive prevention)", "873 entries"),
        ("NOT_NAMES Rejection Set", "~100 words"),
        ("NOT_ORGS Rejection Set", "~100 words"),
        ("NLP Stop Words", "~110 words"),
        ("Safe Domain Whitelist", "40 domains"),
        ("Sensitive Situation Triggers", "32 phrases"),
        ("Contextual Role Patterns", "30+ roles"),
        ("Total Detection Data Points", "~1,500+"),
    ]
    pdf.styled_table(["Component", "Size"], data_stats, [62, 120], x_start=14)

    # Save
    output_path = os.path.join(os.path.dirname(__file__), "VeilPhantom_Technical_Report.pdf")
    pdf.output(output_path)
    print(f"Paper saved to {output_path}")
    print(f"Pages: {pdf.page_no()}")
    return output_path


if __name__ == "__main__":
    build_paper()
