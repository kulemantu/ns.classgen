"""Printable worksheet generator for ClassGen.

Generates layout-aware PDFs optimized for classroom printing:
- Game board grids (bingo, path games)
- Fill-in-the-blank with answer lines
- Cut-out cards (top trumps, flashcards)
- Answer keys (separate page)

These are different from lesson PDFs -- they're designed for students
to write on, cut out, or play with.
"""

import os
import uuid
from fpdf import FPDF
from fpdf.enums import XPos, YPos

static_dir = os.path.join(os.path.dirname(__file__), "static")


def _sanitize(text: str) -> str:
    """Quick latin-1 sanitization."""
    return text.encode('latin-1', 'ignore').decode('latin-1')


class WorksheetPDF(FPDF):
    def __init__(self, title: str = "ClassGen Worksheet"):
        super().__init__()
        self._ws_title = _sanitize(title)

    def header(self):
        self.set_font("helvetica", "B", 14)
        self.cell(0, 8, self._ws_title, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        self.set_font("helvetica", size=8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 5, "Name: _________________________  Class: __________  Date: __________",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(0, 0, 0)
        self.ln(4)

    def footer(self):
        self.set_y(-12)
        self.set_font("helvetica", "I", 7)
        self.cell(0, 8, f"ClassGen Worksheet - Page {self.page_no()}", align="C")


def generate_bingo_grid(title: str, words: list[str], grid_size: int = 4) -> str:
    """Generate a bingo-style vocabulary grid worksheet."""
    pdf = WorksheetPDF(title=_sanitize(title))
    pdf.add_page()
    epw = pdf.w - pdf.l_margin - pdf.r_margin

    pdf.set_font("helvetica", "I", 10)
    pdf.multi_cell(epw, 5, _sanitize(
        "Instructions: Your teacher (or a classmate) reads a definition. "
        "Find and cross out the matching word. First to get a row wins!"
    ))
    pdf.ln(6)

    # Draw the grid
    cell_w = epw / grid_size
    cell_h = 18
    pdf.set_font("helvetica", size=11)

    needed = grid_size * grid_size
    grid_words = (words * ((needed // len(words)) + 1))[:needed] if words else ["?"] * needed

    for row in range(grid_size):
        for col in range(grid_size):
            x = pdf.l_margin + col * cell_w
            y = pdf.get_y()
            pdf.rect(x, y, cell_w, cell_h)
            word = _sanitize(grid_words[row * grid_size + col])
            pdf.set_xy(x + 2, y + 5)
            pdf.cell(cell_w - 4, 8, word, align="C")
        pdf.ln(cell_h)

    filename = f"worksheet_bingo_{uuid.uuid4().hex[:8]}.pdf"
    pdf.output(os.path.join(static_dir, filename))
    return filename


def generate_fill_in_blank(title: str, paragraphs: list[str],
                           answer_key: list[str] | None = None) -> str:
    """Generate a fill-in-the-blank worksheet.

    Paragraphs should contain _______ (underscores) for blanks.
    """
    pdf = WorksheetPDF(title=_sanitize(title))
    pdf.add_page()
    epw = pdf.w - pdf.l_margin - pdf.r_margin

    pdf.set_font("helvetica", "I", 10)
    pdf.multi_cell(epw, 5, _sanitize(
        "Instructions: Fill in the blanks using what you learned in class."
    ))
    pdf.ln(4)

    pdf.set_font("helvetica", size=11)
    for i, para in enumerate(paragraphs, 1):
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(epw, 7, _sanitize(f"{i}. {para}"))
        pdf.ln(3)

    # Answer key on a new page
    if answer_key:
        pdf.add_page()
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(epw, 8, "Answer Key", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(3)
        pdf.set_font("helvetica", size=10)
        for i, ans in enumerate(answer_key, 1):
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(epw, 6, _sanitize(f"{i}. {ans}"))

    filename = f"worksheet_fillin_{uuid.uuid4().hex[:8]}.pdf"
    pdf.output(os.path.join(static_dir, filename))
    return filename


def generate_flashcards(title: str, cards: list[dict]) -> str:
    """Generate cut-out flashcards.

    Each card dict has: {front, back}
    """
    pdf = WorksheetPDF(title=_sanitize(title + " -- Cut along the lines"))
    pdf.add_page()
    epw = pdf.w - pdf.l_margin - pdf.r_margin

    card_w = epw / 2
    card_h = 40
    pdf.set_font("helvetica", size=10)

    for i, card in enumerate(cards):
        col = i % 2
        if col == 0 and i > 0:
            pdf.ln(card_h + 2)

        x = pdf.l_margin + col * (card_w + 2)
        y = pdf.get_y()

        # Card border (dashed would be nice but FPDF doesn't do dashed easily)
        pdf.rect(x, y, card_w, card_h)

        # Front text (bold, larger)
        pdf.set_xy(x + 3, y + 3)
        pdf.set_font("helvetica", "B", 11)
        pdf.multi_cell(card_w - 6, 6, _sanitize(card.get("front", "")))

        # Back text (smaller, italic)
        pdf.set_xy(x + 3, y + card_h / 2 + 2)
        pdf.set_font("helvetica", "I", 9)
        pdf.multi_cell(card_w - 6, 5, _sanitize(card.get("back", "")))

    filename = f"worksheet_cards_{uuid.uuid4().hex[:8]}.pdf"
    pdf.output(os.path.join(static_dir, filename))
    return filename
