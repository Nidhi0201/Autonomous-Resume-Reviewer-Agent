from typing import List, Optional

from pydantic import BaseModel


class ResumeJobRequest(BaseModel):
    """Incoming payload with raw resume text and job description text."""

    resume_text: str
    job_description: str


class ImprovedBullet(BaseModel):
    original: str
    improved: str
    explanation: str
    why_it_works: str
    self_critique: str
    is_supported_by_resume: bool
    issues: List[str] = []
    evidence_snippets: List[str] = []
    relevance_score: float = 0.0  # JD mapping relevance score
    matched_jd_snippet: str = ""  # Most relevant JD section


class AnalyzeResponse(BaseModel):
    bullets: List[ImprovedBullet]
    notes: Optional[str] = None


class ImproveBulletRequest(BaseModel):
    """Request to improve a single bullet further."""
    current_bullet: str  # The current improved version
    original_bullet: str  # The original bullet from resume
    resume_text: str
    job_description: str
    current_relevance: float = 0.0
    target_relevance: float = 0.8  # Default target is 80%


class ImproveBulletResponse(BaseModel):
    """Response with further improved bullet."""
    improved: str
    explanation: str
    why_it_works: str
    relevance_improvements: str
    self_critique: str
    is_supported_by_resume: bool
    issues: List[str] = []
    evidence_snippets: List[str] = []
    new_relevance_score: float = 0.0  # Updated relevance score after improvement

