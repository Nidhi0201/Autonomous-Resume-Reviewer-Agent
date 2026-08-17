# Autonomous Resume Reviewer Agent

An AI-powered resume improvement system that:
- **Reads** resumes and job descriptions
- **Maps** resume bullets to JD requirements using embeddings
- **Iteratively improves** bullets with explanations
- **Self-critiques** to catch hallucinations and weak claims
- **Shows reasoning** and evaluation loops

## Tech Stack

### Backend
- **Python 3.11+** with FastAPI
- **LangGraph** for the multi-step reasoning pipeline
- **Groq** (`openai/gpt-oss-20b`) for LLM-powered bullet improvement and self-critique
- **sentence-transformers** (`all-MiniLM-L6-v2`) for JD ↔ resume embedding matching
- **Postgres + pgvector** for cached JD embeddings (see [Evaluation](#evaluation))

### Frontend
- **Next.js 15** with TypeScript
- **Tailwind CSS** + **shadcn/ui** components
- Modern, responsive UI

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI app & routes
│   │   ├── graph.py         # LangGraph pipeline (extract → map → improve → critique)
│   │   ├── llm.py           # Groq client & prompts (improve + self-critique)
│   │   ├── embeddings.py   # sentence-transformers embeddings & JD mapping
│   │   ├── embedding_cache.py # pgvector cache for JD embeddings
│   │   ├── parser.py        # Resume parsing (PDF/DOCX)
│   │   ├── config.py        # Settings & env vars
│   │   └── schemas.py       # Pydantic models
│   ├── requirements.txt
│   ├── run.py              # Server entry point
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── app/
    │   │   ├── page.tsx     # Main UI
    │   │   ├── layout.tsx
    │   │   └── globals.css
    │   ├── components/
    │   │   └── ui/          # shadcn/ui components
    │   └── lib/
    │       └── utils.ts
    └── package.json
```

## Setup

### Backend

1. **Create virtual environment:**
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your GROQ_API_KEY
   ```

4. **Run the server:**
   ```bash
   python run.py
   # Or: uvicorn app.main:app --reload
   ```

   Server runs at `http://localhost:8000`

### Frontend

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Set environment variable (optional):**
   ```bash
   # Create .env.local if backend is not on localhost:8000
   echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
   ```

3. **Run the dev server:**
   ```bash
   npm run dev
   ```

   Frontend runs at `http://localhost:3000`

## How It Works

### Pipeline Flow

1. **Extract Bullets** (`extract_bullets_node`)
   - Parses resume text to identify achievement bullets
   - Extracts structured experience points

2. **Map to JD** (`map_to_jd_node`)
   - Uses sentence-transformers to generate embeddings
   - Maps each resume bullet to relevant JD sections
   - Calculates relevance scores

3. **Improve Bullets** (`improve_bullets_node`)
   - LLM improves each bullet with JD context
   - Provides explanations for changes
   - Explains why improvements work

4. **Self-Critique** (`self_critique_node`)
   - Validates improvements against original resume
   - Flags hallucinations or exaggerations
   - Provides evidence snippets

### API Endpoints

- `GET /health` - Health check
- `POST /analyze` - Main analysis endpoint
  ```json
  {
    "resume_text": "...",
    "job_description": "..."
  }
  ```

## Features

✅ **Resume Parsing** - Extracts bullets from text  
✅ **JD Mapping** - Semantic matching using embeddings  
✅ **Bullet Improvement** - LLM-powered enhancements  
✅ **Self-Critique** - Hallucination detection  
✅ **Reasoning Display** - Shows why changes were made  
✅ **Evidence Validation** - Checks claims against resume  

## Evaluation

The self-critique node is measured, not assumed. `backend/eval/run_eval.py` runs
the critique over a **labeled set of 30 resume-bullet rewrites** (15 faithful, 15
with deliberately injected hallucinations — invented metrics, fabricated tools,
inflated scope) and reports how often it catches a hallucination (recall) and how
often it wrongly flags a faithful rewrite (false-positive rate). It runs at
temperature 0 so the numbers regenerate when the prompt changes.

Using the harness to improve the critique prompt (`--compare` runs both):

| Critique prompt | Hallucination recall | False-positive rate | Accuracy |
|-----------------|:--------------------:|:-------------------:|:--------:|
| baseline (original) | 86.7% (13/15) | 6.7% | 90.0% |
| **improved** (now in `llm.py`) | **100% (15/15)** | 13.3% | **93.3%** |

The stricter prompt catches every injected hallucination; the tradeoff is a
higher false-positive rate (it occasionally flags a truthful rewrite). Reproduce:

```bash
cd backend && python -m eval.run_eval --compare   # needs GROQ_API_KEY
```

**JD embedding cache (pgvector).** JD embeddings are cached in Postgres/pgvector
keyed by content hash, so repeated analyses of the same JD reuse the vector
instead of recomputing it. Measured with `scripts/bench_embeddings.py`:

| | latency |
|--|--|
| cold (sentence-transformers compute + store) | ~147 ms |
| warm (pgvector cache hit) | ~1.2 ms |

→ cached lookup is **~125× faster** than recomputing (and skips the ~6.8 s
one-time model load on cache-only paths).

## Next Steps

- [ ] Add PDF/DOCX file upload support
- [x] Integrate Postgres + pgvector for persistent storage (JD embedding cache)
- [ ] Add user authentication
- [ ] Implement iterative improvement loops
- [ ] Add evaluation metrics dashboard
- [ ] Support multiple resume formats

## License

MIT
