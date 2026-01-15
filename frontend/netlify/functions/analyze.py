"""
Netlify Function for /analyze endpoint.
"""
import sys
import os
import json
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent.parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.graph import PipelineState, build_pipeline_graph
from app.schemas import AnalyzeResponse, ImprovedBullet


def handler(event, context):
    """
    Handle /analyze POST requests.
    """
    try:
        # Parse request body
        if isinstance(event.get("body"), str):
            body = json.loads(event["body"])
        else:
            body = event.get("body", {})
        
        resume_text = body.get("resume_text", "")
        job_description = body.get("job_description", "")
        
        if not resume_text or not job_description:
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Allow-Methods": "POST, OPTIONS",
                },
                "body": json.dumps({"error": "resume_text and job_description are required"}),
            }
        
        # Run the pipeline
        graph = build_pipeline_graph().compile()
        initial_state = PipelineState(
            resume_text=resume_text,
            job_description=job_description,
            bullets=[],
            improved_payloads=[],
        )
        
        final_state = graph.invoke(initial_state)
        
        # Extract results
        payloads = final_state.get("critique_payloads") or final_state.get("improved_payloads") or []
        
        bullets = []
        for payload in payloads:
            bullets.append({
                "original": payload.get("original", ""),
                "improved": payload.get("improved", ""),
                "explanation": payload.get("explanation", ""),
                "why_it_works": payload.get("why_it_works", ""),
                "self_critique": payload.get("self_critique", ""),
                "is_supported_by_resume": bool(payload.get("is_supported_by_resume", True)),
                "issues": list(payload.get("issues", []) or []),
                "evidence_snippets": list(payload.get("evidence_snippets", []) or []),
                "relevance_score": float(payload.get("relevance_score", 0.0)),
                "matched_jd_snippet": payload.get("matched_jd_snippet", ""),
            })
        
        response = {
            "bullets": bullets,
            "notes": f"Processed {len(bullets)} bullets through extract → map → improve → self-critique pipeline.",
        }
        
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
            },
            "body": json.dumps(response),
        }
        
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({"error": str(e)}),
        }
