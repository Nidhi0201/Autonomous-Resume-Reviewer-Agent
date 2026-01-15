import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .graph import PipelineState, build_pipeline_graph
from .schemas import (
    AnalyzeResponse,
    ImprovedBullet,
    ImproveBulletRequest,
    ImproveBulletResponse,
    ResumeJobRequest,
)
from .llm import call_bullet_improvement_for_relevance
from .embeddings import _calculate_simple_relevance

app = FastAPI(
    title="Autonomous Resume Reviewer Agent",
    version="0.1.0",
)

# CORS middleware for frontend
# Allow Netlify and localhost for development
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Add Netlify domain from environment variable if set
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    # Support multiple URLs separated by comma
    for url in frontend_url.split(","):
        allowed_origins.append(url.strip())

# For production, you can add specific Netlify domains:
# allowed_origins.append("https://your-site-name.netlify.app")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: ResumeJobRequest) -> AnalyzeResponse:
    """
    Main entrypoint:
    - Extract bullets from resume text
    - Map & improve bullets using the LangGraph pipeline
    - Return improved bullets + explanations + self-critique
    """

    graph = build_pipeline_graph().compile()
    initial_state = PipelineState(
        resume_text=request.resume_text,
        job_description=request.job_description,
        bullets=[],
        improved_payloads=[],
    )

    final_state = graph.invoke(initial_state)

    # LangGraph returns a dict-like object, so access fields as dict keys
    payloads = final_state.get("critique_payloads") or final_state.get("improved_payloads") or []

    bullets: list[ImprovedBullet] = []
    for payload in payloads:
        bullets.append(
            ImprovedBullet(
                original=payload.get("original", ""),
                improved=payload.get("improved", ""),
                explanation=payload.get("explanation", ""),
                why_it_works=payload.get("why_it_works", ""),
                self_critique=payload.get("self_critique", ""),
                is_supported_by_resume=bool(
                    payload.get("is_supported_by_resume", True)
                ),
                issues=list(payload.get("issues", []) or []),
                evidence_snippets=list(payload.get("evidence_snippets", []) or []),
                relevance_score=float(payload.get("relevance_score", 0.0)),
                matched_jd_snippet=payload.get("matched_jd_snippet", ""),
            )
        )

    return AnalyzeResponse(
        bullets=bullets,
        notes=f"Processed {len(bullets)} bullets through extract → map → improve → self-critique pipeline.",
    )


@app.post("/improve-bullet", response_model=ImproveBulletResponse)
def improve_bullet(request: ImproveBulletRequest) -> ImproveBulletResponse:
    """
    Iterative improvement endpoint: Improve a single bullet to increase JD relevance.
    Useful when a bullet has low relevance (e.g., 20%) and user wants it improved to higher relevance (e.g., 80%).
    """
    result = call_bullet_improvement_for_relevance(
        current_bullet=request.current_bullet,
        original_bullet=request.original_bullet,
        resume_text=request.resume_text,
        job_description=request.job_description,
        target_relevance=request.target_relevance,
        current_relevance=request.current_relevance,
    )
    
    # Calculate new relevance score
    new_relevance = _calculate_simple_relevance(
        result.get("improved", request.current_bullet),
        request.job_description
    )
    
    return ImproveBulletResponse(
        improved=result.get("improved", request.current_bullet),
        explanation=result.get("explanation", ""),
        why_it_works=result.get("why_it_works", ""),
        relevance_improvements=result.get("relevance_improvements", ""),
        self_critique=result.get("self_critique", ""),
        is_supported_by_resume=bool(result.get("is_supported_by_resume", True)),
        issues=list(result.get("issues", []) or []),
        evidence_snippets=list(result.get("evidence_snippets", []) or []),
        new_relevance_score=new_relevance,
    )

