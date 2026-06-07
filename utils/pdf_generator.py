from fpdf import FPDF
import datetime

class MeetingReportPDF(FPDF):
    def header(self):
        # Top banner styling
        self.set_fill_color(26, 26, 38)  # Deep dark slate
        self.rect(0, 0, 210, 35, 'F')
        
        # Header text
        self.set_text_color(255, 255, 255)
        self.set_font("helvetica", "B", 14)
        self.cell(0, 10, "AI MEETING ASSISTANT - EXECUTIVE REPORT", align="C", ln=True)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 4, f"Generated on {datetime.date.today().strftime('%B %d, %Y')}", align="C", ln=True)
        self.ln(16)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(112, 112, 160)
        # Page number
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

def clean_txt(text: str) -> str:
    """Clean text to prevent FPDF unicode/latin-1 crashes by replacing non-latin-1 characters."""
    if not text:
        return ""
    replacements = {
        "\u201c": '"', "\u201d": '"',  # double smart quotes
        "\u2018": "'", "\u2019": "'",  # single smart quotes/apostrophes
        "\u2013": "-", "\u2014": "-",  # dashes
        "\u2022": "* ",                # bullet point
        "\u2714": "[x]", "\u2611": "[x]", # checkmarks
        "\u2713": "[x]",
        "\u274c": "[ ]", "\u274e": "[ ]", # cross marks
        "\u26a0": "[!]",                # warnings
        "\u2192": "->",                # arrows
        "\u201f": '"',
        "\u2212": "-",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    
    # Strip out any high unicode emojis/characters that fail latin-1
    return text.encode("latin-1", "replace").decode("latin-1")

def generate_meeting_pdf(title: str, summary: str, action_items: str, decisions: str, questions: str, transcript: str) -> bytes:
    pdf = MeetingReportPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.alias_nb_pages()
    
    # Title Page/Main Info
    pdf.add_page()
    
    # Title header
    pdf.set_font("helvetica", "B", 18)
    pdf.set_text_color(124, 58, 237)  # Accent Purple (#7C3AED)
    pdf.multi_cell(0, 8, clean_txt(title))
    pdf.ln(4)
    
    # Divider line
    pdf.set_draw_color(124, 58, 237)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)
    
    # Executive Summary Card
    pdf.set_font("helvetica", "B", 13)
    pdf.set_text_color(26, 26, 38)
    pdf.cell(0, 8, "1. Executive Summary", ln=True)
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(50, 50, 65)
    pdf.multi_cell(0, 6, clean_txt(summary))
    pdf.ln(6)
    
    # Action Items Card
    pdf.set_font("helvetica", "B", 13)
    pdf.set_text_color(16, 185, 129)  # Green Success
    pdf.cell(0, 8, "2. Action Items & Owners", ln=True)
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(50, 50, 65)
    pdf.multi_cell(0, 6, clean_txt(action_items))
    pdf.ln(6)
    
    # Key Decisions Card
    pdf.set_font("helvetica", "B", 13)
    pdf.set_text_color(6, 182, 212)   # Cyan Accent
    pdf.cell(0, 8, "3. Key Decisions", ln=True)
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(50, 50, 65)
    pdf.multi_cell(0, 6, clean_txt(decisions))
    pdf.ln(6)
    
    # Open Questions Card
    pdf.set_font("helvetica", "B", 13)
    pdf.set_text_color(245, 158, 11)  # Orange Warning
    pdf.cell(0, 8, "4. Open Questions & Follow-ups", ln=True)
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(50, 50, 65)
    pdf.multi_cell(0, 6, clean_txt(questions))
    pdf.ln(8)
    
    # Transcript on new page
    pdf.add_page()
    pdf.set_font("helvetica", "B", 13)
    pdf.set_text_color(26, 26, 38)
    pdf.cell(0, 8, "5. Full Transcript", ln=True)
    
    pdf.set_draw_color(200, 200, 210)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    
    pdf.set_font("helvetica", "", 9)
    pdf.set_text_color(80, 80, 95)
    pdf.multi_cell(0, 5, clean_txt(transcript))
    
    # Return as bytes
    pdf_bytes = pdf.output()
    return bytes(pdf_bytes)
