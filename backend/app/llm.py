from __future__ import annotations

import json
from typing import Any, Dict

from groq import Groq

from .config import settings


def _get_groq_client() -> Groq | None:
    """Return a Groq client if API key is configured."""
    if not settings.groq_api_key:
        return None
    return Groq(api_key=settings.groq_api_key)


SYSTEM_PROMPT_IMPROVE = """You are an expert resume coach focused on software engineering and tech internships.

You improve resume bullets so they:
- Are tailored to a specific job description
- Are concrete, quantified where honest
- Avoid exaggeration or hallucinated achievements

You must:
- Preserve factual correctness based on the original bullet and resume context.
- Explain why each change was made.
- Explain why the final bullet works better for this job.
- Perform a self-critique pass checking for hallucinations or weak claims."""


def call_bullet_improvement(
    bullet: str,
    resume_text: str,
    job_description: str,
    model_name: str = "llama-3.3-70b-versatile",
) -> Dict[str, Any]:
    """
    Call Groq API to improve a single bullet with explanation and self-critique.
    
    Returns a dict that matches the expected JSON schema.
    """
    client = _get_groq_client()
    
    user_prompt = f"""
ORIGINAL BULLET:
{bullet}

FULL RESUME CONTEXT:
{resume_text}

JOB DESCRIPTION:
{job_description}

TASK:
1. Improve this bullet for this specific job.
2. Explain each change you make.
3. Explain why the final bullet is stronger for this job (relevance, clarity, impact).
4. Do a self-critique pass:
   - Check if the improved bullet is fully supported by the original resume.
   - Flag any hallucinated or exaggerated claims.
   - Suggest a safer alternative if needed.

Respond in strict JSON with this shape:
{{
  "improved": "string",
  "explanation": "string",
  "why_it_works": "string",
  "self_critique": "string",
  "is_supported_by_resume": true,
  "issues": ["string", "..."],
  "evidence_snippets": ["string", "..."]
}}
"""

    if client is None:
        return {
            "improved": bullet.strip(),
            "explanation": "No Groq API key configured; returned the original bullet.",
            "why_it_works": "Acts as a placeholder until real LLM integration is enabled.",
            "self_critique": "Cannot evaluate hallucinations without model access.",
            "is_supported_by_resume": True,
            "issues": [],
            "evidence_snippets": [],
        }

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_IMPROVE},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
            max_tokens=800,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content.strip()

        try:
            data = json.loads(content)
            return data
        except json.JSONDecodeError:
            data = {
                "improved": bullet.strip(),
                "explanation": "Model returned non-JSON output; keeping original bullet.",
                "why_it_works": "N/A due to parsing error.",
                "self_critique": content,
                "is_supported_by_resume": True,
                "issues": ["model_output_not_json"],
                "evidence_snippets": [],
            }
            return data
    except Exception as exc:  # noqa: BLE001
        return {
            "improved": bullet.strip(),
            "explanation": f"Groq API call failed: {exc}; returned original bullet.",
            "why_it_works": "Acts as a safe fallback when the model is unavailable.",
            "self_critique": "Unable to run self-critique due to model error.",
            "is_supported_by_resume": True,
            "issues": ["groq_api_error"],
            "evidence_snippets": [],
        }


SYSTEM_PROMPT_CRITIQUE = """You are a rigorous fact-checker. You validate resume improvements against original facts
and flag any hallucinations or exaggerations."""


SYSTEM_PROMPT_IMPROVE_RELEVANCE = """You are an expert resume coach specializing in improving job description relevance.

Your goal is to significantly increase how well a resume bullet matches a job description while:
- Staying truthful to the original resume content
- Emphasizing skills/experiences that directly align with JD requirements
- Using JD-specific terminology and keywords naturally
- Making the connection to JD requirements more explicit and clear"""


def call_bullet_improvement_for_relevance(
    current_bullet: str,
    original_bullet: str,
    resume_text: str,
    job_description: str,
    target_relevance: float = 0.8,
    current_relevance: float = 0.2,
    model_name: str = "llama-3.3-70b-versatile",
) -> Dict[str, Any]:
    """
    Specifically improve a bullet to increase JD relevance score.
    Takes the current improved bullet and refines it further.
    """
    client = _get_groq_client()
    
    user_prompt = f"""
CURRENT BULLET (Relevance: {current_relevance*100:.0f}%):
{current_bullet}

ORIGINAL BULLET:
{original_bullet}

FULL RESUME CONTEXT:
{resume_text}

JOB DESCRIPTION:
{job_description}

TASK:
This bullet currently has a {current_relevance*100:.0f}% relevance to the job description. Your goal is to improve it to ~{target_relevance*100:.0f}% relevance.

To increase relevance:
1. Identify key requirements, skills, and keywords from the job description
2. Find connections in the original resume that relate to those requirements
3. Rewrite the bullet to explicitly highlight those connections
4. Use terminology from the job description naturally
5. Emphasize the most relevant aspects while staying truthful to the original

IMPORTANT:
- DO NOT invent achievements or metrics not in the resume
- DO NOT exaggerate your role or impact
- DO focus on making existing relevant experiences more prominent
- DO use JD keywords naturally in context
- DO emphasize transferable skills that match JD requirements

Respond in strict JSON:
{{
  "improved": "string - the new improved bullet",
  "explanation": "string - why these changes improve JD relevance",
  "why_it_works": "string - how this version better matches JD requirements",
  "relevance_improvements": "string - specific JD requirements addressed"
}}
"""

    if client is None:
        return {
            "improved": current_bullet.strip(),
            "explanation": "No Groq API key configured; returned current bullet.",
            "why_it_works": "Cannot improve without API access.",
            "relevance_improvements": "",
        }

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_IMPROVE_RELEVANCE},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.5,
            max_tokens=800,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content.strip()

        try:
            data = json.loads(content)
            # Re-run self-critique to ensure no hallucinations
            critique = call_self_critique(
                original_bullet=original_bullet,
                improved_bullet=data.get("improved", current_bullet),
                resume_text=resume_text,
                job_description=job_description,
            )
            
            data.update({
                "self_critique": critique.get("self_critique", ""),
                "is_supported_by_resume": critique.get("is_supported_by_resume", True),
                "issues": critique.get("issues", []),
                "evidence_snippets": critique.get("evidence_snippets", []),
            })
            return data
        except json.JSONDecodeError:
            return {
                "improved": current_bullet.strip(),
                "explanation": "Model returned non-JSON output; keeping current bullet.",
                "why_it_works": "N/A due to parsing error.",
                "relevance_improvements": "",
                "self_critique": "Unable to parse model response.",
                "is_supported_by_resume": True,
                "issues": ["model_output_not_json"],
                "evidence_snippets": [],
            }
    except Exception as exc:  # noqa: BLE001
        return {
            "improved": current_bullet.strip(),
            "explanation": f"API call failed: {exc}; returned current bullet.",
            "why_it_works": "Acts as a safe fallback when the model is unavailable.",
            "relevance_improvements": "",
            "self_critique": "Unable to run critique due to model error.",
            "is_supported_by_resume": True,
            "issues": ["improve_relevance_api_error"],
            "evidence_snippets": [],
        }


def call_self_critique(
    original_bullet: str,
    improved_bullet: str,
    resume_text: str,
    job_description: str,
    model_name: str = "llama-3.3-70b-versatile",
) -> Dict[str, Any]:
    """
    Dedicated self-critique pass to check for hallucinations and weak claims.
    """
    client = _get_groq_client()

    user_prompt = f"""
ORIGINAL BULLET:
{original_bullet}

IMPROVED BULLET:
{improved_bullet}

FULL RESUME CONTEXT:
{resume_text}

JOB DESCRIPTION:
{job_description}

TASK: Perform a rigorous self-critique of the improved bullet.

Check:
1. Is every claim in the improved bullet supported by the original resume?
2. Are there any hallucinated achievements, metrics, or technologies?
3. Are there any exaggerated or unsupported claims?
4. What evidence from the resume supports (or contradicts) the improved bullet?
5. Should any parts be toned down or made more accurate?

Respond in strict JSON:
{{
  "self_critique": "Detailed critique analysis",
  "is_supported_by_resume": true/false,
  "issues": ["list of specific issues found"],
  "evidence_snippets": ["quotes from resume that support/contradict claims"]
}}
"""

    if client is None:
        return {
            "self_critique": "No Groq API key configured; skipping critique.",
            "is_supported_by_resume": True,
            "issues": [],
            "evidence_snippets": [],
        }

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_CRITIQUE},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=600,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content.strip()

        try:
            data = json.loads(content)
            return data
        except json.JSONDecodeError:
            return {
                "self_critique": content,
                "is_supported_by_resume": True,
                "issues": ["critique_output_not_json"],
                "evidence_snippets": [],
            }
    except Exception as exc:  # noqa: BLE001
        return {
            "self_critique": f"Critique API call failed: {exc}",
            "is_supported_by_resume": True,
            "issues": ["critique_api_error"],
            "evidence_snippets": [],
        }
