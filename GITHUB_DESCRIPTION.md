# GitHub Repository Description

## Short Description (for GitHub repo)
```
AI-powered resume bullet improvement tool with self-critique and job description matching. Built with Next.js, FastAPI, LangGraph, and Groq.
```

## Full Description (for README or About section)

**Autonomous Resume Reviewer Agent** - An intelligent resume optimization tool that analyzes your resume bullets, maps them to job descriptions, and iteratively improves them using AI while ensuring factual accuracy through self-critique.

### Key Features
- 🎯 **JD Mapping**: Automatically matches resume bullets to job description requirements
- ✨ **AI-Powered Improvement**: Enhances bullets using Groq's LLM while maintaining truthfulness
- 🔍 **Self-Critique**: Validates improvements to prevent hallucinations and exaggerations
- 📊 **Relevance Scoring**: Shows how well each bullet matches the job description
- 🔄 **Iterative Refinement**: Improve low-relevance bullets to higher scores (e.g., 20% → 80%)
- 🎨 **Beautiful UI**: Modern, responsive interface with color-coded feedback

### Tech Stack
- **Frontend**: Next.js 15, React, TypeScript, Tailwind CSS, shadcn/ui
- **Backend**: FastAPI, LangGraph, Groq API
- **Deployment**: Netlify (frontend + serverless functions)

### Quick Start
1. Clone the repository
2. Set up backend: `cd backend && pip install -r requirements.txt`
3. Set `GROQ_API_KEY` in environment variables
4. Run backend: `python run.py`
5. Run frontend: `cd frontend && npm install && npm run dev`

### Live Demo
[Add your Netlify deployment URL here]

### License
MIT

---

## Tags/Keywords for GitHub
```
resume, resume-optimizer, ai-resume, job-application, resume-reviewer, 
langgraph, fastapi, nextjs, groq, ai-tools, career-tools, resume-builder,
job-description-matching, resume-improvement, ai-powered
```
