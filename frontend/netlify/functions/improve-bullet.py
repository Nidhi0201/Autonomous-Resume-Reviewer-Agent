"""
Netlify Function for /improve-bullet endpoint.
"""
import sys
import os
import json
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent.parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.llm import call_bullet_improvement_for_relevance
from app.embeddings import _calculate_simple_relevance


def handler(event, context):
    """
    Handle /improve-bullet POST requests.
    """
    try:
        # Parse request body
        if isinstance(event.get("body"), str):
            body = json.loads(event["body"])
        else:
            body = event.get("body", {})
        
        current_bullet = body.get("current_bullet", "")
        original_bullet = body.get("original_bullet", "")
        resume_text = body.get("resume_text", "")
        job_description = body.get("job_description", "")
        current_relevance = float(body.get("current_relevance", 0.0))
        target_relevance = float(body.get("target_relevance", 0.8))
        
        if not all([current_bullet, original_bullet, resume_text, job_description]):
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
                "body": json.dumps({"error": "All fields are required"}),
            }
        
        # Call improvement function
        result = call_bullet_improvement_for_relevance(
            current_bullet=current_bullet,
            original_bullet=original_bullet,
            resume_text=resume_text,
            job_description=job_description,
            target_relevance=target_relevance,
            current_relevance=current_relevance,
        )
        
        # Calculate new relevance score
        new_relevance = _calculate_simple_relevance(
            result.get("improved", current_bullet),
            job_description
        )
        
        response = {
            "improved": result.get("improved", current_bullet),
            "explanation": result.get("explanation", ""),
            "why_it_works": result.get("why_it_works", ""),
            "relevance_improvements": result.get("relevance_improvements", ""),
            "self_critique": result.get("self_critique", ""),
            "is_supported_by_resume": bool(result.get("is_supported_by_resume", True)),
            "issues": list(result.get("issues", []) or []),
            "evidence_snippets": list(result.get("evidence_snippets", []) or []),
            "new_relevance_score": new_relevance,
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
