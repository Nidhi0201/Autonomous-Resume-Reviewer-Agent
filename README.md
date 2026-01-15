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
- **LangGraph** for multi-step reasoning pipeline
- **Anthropic Claude 3.5** for LLM-powered improvements
- **sentence-transformers** for embeddings (JD ↔ Resume mapping)
- **Postgres + pgvector** (ready for vector storage)

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
│   │   ├── llm.py           # Anthropic client & prompts
│   │   ├── embeddings.py   # Vector embeddings & JD mapping
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
   # Edit .env and add your ANTHROPIC_API_KEY
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

## Next Steps

- [ ] Add PDF/DOCX file upload support
- [ ] Integrate Postgres + pgvector for persistent storage
- [ ] Add user authentication
- [ ] Implement iterative improvement loops
- [ ] Add evaluation metrics dashboard
- [ ] Support multiple resume formats

## License

MIT
