# Quick Start Guide

## Prerequisites

- Python 3.11+ installed
- Node.js 18+ and npm installed (for frontend)
- Groq API key (free, get from https://console.groq.com/)

## Setup (5 minutes)

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
# Create .env file with:
echo "GROQ_API_KEY=your_groq_api_key_here" > .env
echo "ENVIRONMENT=local" >> .env

# Run the server
python run.py
```

Backend will run at `http://localhost:8000`

### 2. Frontend Setup

```bash
# In a new terminal
cd frontend

# Install dependencies
npm install

# Run the dev server
npm run dev
```

Frontend will run at `http://localhost:3000`

## Usage

1. Open `http://localhost:3000` in your browser
2. Paste your resume text in the left textarea
3. Paste the job description in the right textarea
4. Click "Analyze & Improve"
5. View improved bullets with explanations, self-critique, and JD mapping scores

## Getting a Groq API Key

1. Go to https://console.groq.com/
2. Sign up (free, no credit card needed)
3. Go to "API Keys" in the dashboard
4. Click "Create API Key"
5. Copy the key and paste it in `backend/.env` file

## Testing the API

You can test the backend directly:

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "Developed a web application using React and Node.js",
    "job_description": "Looking for a full-stack developer with React experience"
  }'
```

## Project Structure

- **Backend**: FastAPI + LangGraph pipeline
  - `app/graph.py` - Main pipeline (extract → map → improve → critique)
  - `app/llm.py` - Groq API client & prompts
  - `app/embeddings.py` - Simple keyword matching for JD mapping
  - `app/parser.py` - Resume parsing utilities

- **Frontend**: Next.js + shadcn/ui
  - `src/app/page.tsx` - Main UI component
  - `src/components/ui/` - Reusable UI components

## Features

✅ **Resume Parsing** - Extracts bullets from text  
✅ **JD Mapping** - Simple keyword matching for relevance  
✅ **Bullet Improvement** - Groq LLM-powered enhancements  
✅ **Self-Critique** - Hallucination detection  
✅ **Reasoning Display** - Shows why changes were made  
✅ **Evidence Validation** - Checks claims against resume  

## Troubleshooting

**Backend won't start:**
- Check Python version: `python --version` (should be 3.11+)
- Ensure virtual environment is activated
- Check if port 8000 is available
- Make sure `.env` file exists with `GROQ_API_KEY`

**Frontend won't start:**
- Check Node version: `node --version` (should be 18+)
- Delete `node_modules` and run `npm install` again
- Check if port 3000 is available

**API calls fail:**
- Ensure backend is running on port 8000
- Check if Groq API key is set correctly in `.env`
- Check backend logs for API errors
- The system will show fallback responses if API key is missing

**No improvements shown:**
- Check if Groq API key is set correctly
- Check backend logs for API errors
- The system will show fallback responses if API key is missing

## Next Steps

- Add PDF/DOCX file upload support
- Deploy to a simple platform (Railway, Render, etc.)
- Add user authentication
- Implement iterative improvement loops
