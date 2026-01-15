from __future__ import annotations

from typing import List, Tuple

from langgraph.graph import END, StateGraph
from pydantic import BaseModel

from .embeddings import map_bullets_to_jd
from .llm import call_bullet_improvement, call_self_critique
from .parser import extract_resume_bullets


class PipelineState(BaseModel):
    resume_text: str
    job_description: str
    bullets: List[str] = []
    mapped_bullets: List[Tuple[str, float, str]] = []  # (bullet, relevance_score, jd_snippet)
    improved_payloads: List[dict] = []
    critique_payloads: List[dict] = []


def extract_bullets_node(state: PipelineState) -> PipelineState:
    """
    Node 1: Extract structured bullets from resume text.
    Uses the parser to identify achievement bullets and experience points.
    """
    bullets = extract_resume_bullets(state.resume_text)
    return state.model_copy(update={"bullets": bullets})


def map_to_jd_node(state: PipelineState) -> PipelineState:
    """
    Node 2: Map resume bullets to relevant job description sections.
    Uses embeddings to find which JD requirements each bullet addresses.
    """
    if not state.bullets:
        return state
    
    mappings = map_bullets_to_jd(
        resume_bullets=state.bullets,
        job_description=state.job_description,
        top_k=len(state.bullets)  # Map all bullets
    )
    
    return state.model_copy(update={"mapped_bullets": mappings})


def improve_bullets_node(state: PipelineState) -> PipelineState:
    """
    Node 3: Improve each bullet using LLM, tailored to the job description.
    Uses the mapped JD context to make improvements more relevant.
    """
    improved_payloads: list[dict] = []
    
    for bullet, relevance_score, jd_snippet in state.mapped_bullets:
        # Enhance job description context with the most relevant snippet
        enhanced_jd = f"{state.job_description}\n\n[Most Relevant Section]: {jd_snippet}"
        
        payload = call_bullet_improvement(
            bullet=bullet,
            resume_text=state.resume_text,
            job_description=enhanced_jd,
        )
        payload["original"] = bullet
        payload["relevance_score"] = relevance_score
        payload["matched_jd_snippet"] = jd_snippet
        improved_payloads.append(payload)
    
    return state.model_copy(update={"improved_payloads": improved_payloads})


def self_critique_node(state: PipelineState) -> PipelineState:
    """
    Node 4: Self-critique pass - check for hallucinations and weak claims.
    Validates each improved bullet against the original resume facts.
    """
    critique_payloads: list[dict] = []
    
    for improved_payload in state.improved_payloads:
        critique = call_self_critique(
            original_bullet=improved_payload["original"],
            improved_bullet=improved_payload.get("improved", ""),
            resume_text=state.resume_text,
            job_description=state.job_description,
        )
        
        # Merge critique results into the improved payload
        improved_payload.update({
            "self_critique": critique.get("self_critique", ""),
            "is_supported_by_resume": critique.get("is_supported_by_resume", True),
            "issues": critique.get("issues", []),
            "evidence_snippets": critique.get("evidence_snippets", []),
        })
        
        critique_payloads.append(improved_payload)
    
    return state.model_copy(update={"critique_payloads": critique_payloads})


def build_pipeline_graph() -> StateGraph:
    """
    Build the complete LangGraph pipeline:
    1. extract_bullets - Parse resume and extract achievement bullets
    2. map_to_jd - Use embeddings to map bullets to JD requirements
    3. improve_bullets - LLM improves each bullet with JD context
    4. self_critique - Validate improvements for hallucinations/weak claims
    """
    workflow = StateGraph(PipelineState)
    
    workflow.add_node("extract_bullets", extract_bullets_node)
    workflow.add_node("map_to_jd", map_to_jd_node)
    workflow.add_node("improve_bullets", improve_bullets_node)
    workflow.add_node("self_critique", self_critique_node)
    
    # Define the flow
    workflow.set_entry_point("extract_bullets")
    workflow.add_edge("extract_bullets", "map_to_jd")
    workflow.add_edge("map_to_jd", "improve_bullets")
    workflow.add_edge("improve_bullets", "self_critique")
    workflow.add_edge("self_critique", END)
    
    return workflow

