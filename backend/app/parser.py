"""
Resume and document parsing utilities.
Extracts text from PDF and DOCX files, and structures resume bullets.
"""
from typing import List
import pdfplumber
from docx import Document


def parse_pdf(file_path: str) -> str:
    """Extract text from a PDF file."""
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text


def parse_docx(file_path: str) -> str:
    """Extract text from a DOCX file."""
    doc = Document(file_path)
    text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
    return text


def extract_resume_bullets(resume_text: str) -> List[str]:
    """
    Extract bullet points from resume text.
    Looks for lines that start with bullets (-, •, *) or are indented.
    Also extracts experience/achievement sections.
    """
    bullets: List[str] = []
    lines = resume_text.splitlines()
    
    for line in lines:
        stripped = line.strip()
        # Skip empty lines
        if not stripped:
            continue
        
        # Check if it's a bullet point
        if stripped.startswith(("-", "•", "*", "·")) or stripped[0].isdigit():
            bullet = stripped.lstrip("-•*·0123456789. ").strip()
            if bullet and len(bullet) >= 3:  # Reduced minimum length
                bullets.append(bullet)
        # Also capture lines that look like achievements (contain action verbs)
        elif any(verb in stripped.lower()[:20] for verb in [
            "developed", "created", "built", "implemented", "designed",
            "managed", "led", "improved", "optimized", "reduced", "increased",
            "used", "worked", "designed", "wrote", "tested"
        ]):
            if len(stripped) >= 5:  # More lenient for action verbs
                bullets.append(stripped)
    
    # If no bullets found, treat any non-empty line as a bullet (more lenient fallback)
    if not bullets:
        bullets = [line.strip() for line in lines if line.strip() and len(line.strip()) >= 3]
    
    return bullets
