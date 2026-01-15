# Netlify Functions

This directory contains serverless functions that run your FastAPI backend on Netlify.

## Structure

- `analyze.py` - Main analysis endpoint (`POST /.netlify/functions/analyze`)
- `improve-bullet.py` - Iterative improvement endpoint (`POST /.netlify/functions/improve-bullet`)
- `health.py` - Health check endpoint (`GET /.netlify/functions/health`)
- `requirements.txt` - Python dependencies for functions

## How It Works

1. Netlify automatically detects Python functions in `netlify/functions/`
2. Each `.py` file becomes a serverless function
3. Functions have access to backend code via `sys.path`
4. Environment variables are available via `os.getenv()`

## Local Testing

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Run locally
cd frontend
netlify dev
```

This will:
- Start Next.js dev server
- Start Netlify Functions locally
- Proxy requests to functions

## Deployment

Functions are automatically deployed when you deploy to Netlify.

## Environment Variables

Set in Netlify Dashboard → Site settings → Environment variables:
- `GROQ_API_KEY` - Your Groq API key

## Function Format

Each function exports a `handler(event, context)` function:

```python
def handler(event, context):
    # event['body'] contains request body
    # Return dict with statusCode, headers, body
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"result": "ok"})
    }
```

## Accessing Backend Code

Functions access backend code by adding it to `sys.path`:

```python
import sys
from pathlib import Path
backend_path = Path(__file__).parent.parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))
```

This allows importing from `app.main`, `app.llm`, etc.
