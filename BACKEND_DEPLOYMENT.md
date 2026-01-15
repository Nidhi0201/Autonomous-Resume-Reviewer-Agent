# Backend Deployment on Netlify Functions

## How It Works

Your backend is deployed as **Netlify Functions** (serverless functions) alongside your frontend. This means:

- ✅ **No separate backend deployment needed**
- ✅ **Everything runs on Netlify**
- ✅ **Automatic scaling**
- ✅ **Free tier: 125K invocations/month**

## Function Endpoints

After deployment, your backend endpoints will be available at:

- `https://your-site.netlify.app/.netlify/functions/analyze`
- `https://your-site.netlify.app/.netlify/functions/improve-bullet`
- `https://your-site.netlify.app/.netlify/functions/health`

The frontend automatically detects Netlify and uses these URLs.

## Configuration

### 1. Functions Directory

Functions are located at: `frontend/netlify/functions/`

- `analyze.py` - Main analysis endpoint
- `improve-bullet.py` - Iterative improvement endpoint
- `health.py` - Health check
- `requirements.txt` - Python dependencies

### 2. Netlify Settings

In `frontend/netlify.toml`:
```toml
[functions]
  directory = "netlify/functions"
```

### 3. Environment Variables

Set in Netlify Dashboard → Site settings → Environment variables:

- `GROQ_API_KEY` - Your Groq API key (required)
- `PYTHON_VERSION` - Set to `3.11` (optional, defaults to 3.11)

### 4. How Functions Access Backend Code

Functions access backend code via `sys.path` manipulation:
- Functions look for `backend/` directory relative to the project root
- Backend code is imported: `from app.graph import ...`
- All backend dependencies must be in `netlify/functions/requirements.txt`

## Testing Locally

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Run locally (starts both frontend and functions)
cd frontend
netlify dev
```

This will:
- Start Next.js dev server on `http://localhost:8888`
- Start Netlify Functions locally
- Proxy requests to functions automatically

## Troubleshooting

### Functions Not Found

**Error**: `404 Function not found`

**Solution**:
- Check `netlify.toml` has `[functions]` section with correct `directory`
- Verify functions are in `frontend/netlify/functions/`
- Ensure function files are named correctly (e.g., `analyze.py` → `/.netlify/functions/analyze`)

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'app'`

**Solution**:
- Check that `backend/` directory exists at project root
- Verify `sys.path` manipulation in function files
- Ensure all dependencies in `requirements.txt` are installed

### Timeout Errors

**Error**: `Function execution timeout`

**Solution**:
- Netlify free tier: 10 second timeout
- Paid tier: 26 second timeout
- Your functions should complete in < 10 seconds for typical resumes
- If timing out, optimize LangGraph pipeline or upgrade plan

### Environment Variables Not Available

**Error**: `GROQ_API_KEY not found`

**Solution**:
- Set `GROQ_API_KEY` in Netlify Dashboard → Environment variables
- Redeploy after adding environment variables
- Functions access env vars via `os.getenv("GROQ_API_KEY")`

## Deployment Checklist

- [ ] Functions are in `frontend/netlify/functions/`
- [ ] `requirements.txt` includes all backend dependencies
- [ ] `netlify.toml` has `[functions]` section
- [ ] `GROQ_API_KEY` environment variable is set
- [ ] Frontend auto-detects Netlify Functions URLs
- [ ] Test health endpoint: `/.netlify/functions/health`

## Function Structure

Each function follows this pattern:

```python
def handler(event, context):
    """
    Netlify Function handler.
    event['body'] contains request body (string or dict)
    """
    try:
        # Parse request
        body = json.loads(event.get("body", "{}"))
        
        # Process request using backend code
        # ...
        
        # Return response
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(result),
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)}),
        }
```

## Monitoring

View function logs:
- Netlify Dashboard → Functions → View logs
- Or: `netlify logs:functions`

Check function performance:
- Netlify Dashboard → Analytics → Functions
- Monitor execution time and invocations

---

## Alternative: Separate Backend Deployment

If Netlify Functions don't work for you, you can deploy backend separately:

- **Railway**: `$5/month`, no timeout limits
- **Render**: Free tier available, may sleep after inactivity
- **Fly.io**: Free tier available
- **Google Cloud Run**: Pay per use

See `DEPLOYMENT.md` for details on separate backend deployment.
