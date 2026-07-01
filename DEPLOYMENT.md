# Deployment Guide for SHL Recommender

## Overview

This guide covers deploying the SHL Recommender to various free/low-cost platforms. The API is stateless and containerizable, making it suitable for serverless platforms.

## Prerequisites

- Anthropic API key (get free credits at https://console.anthropic.com)
- Git repository (GitHub, GitLab, etc.)
- Docker installed locally (for testing)

## Option 1: Render (Recommended for FastAPI)

### Setup

1. Push your code to a Git repository
2. Go to https://render.com and sign up
3. Click "Create new" → "Web Service"
4. Select your repository
5. Configure:
   - **Environment**: Python 3.11
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Add environment variables:
   - `ANTHROPIC_API_KEY`: Your API key
7. Click "Deploy"

Your API will be available at `https://<service-name>.onrender.com`

### Monitoring

- Check logs in the Render dashboard
- Set up alerts for deployment failures
- Monitor memory usage and response times

## Option 2: Fly.io

### Setup

1. Install Fly CLI: https://fly.io/docs/getting-started/installing-flyctl/
2. Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

3. Create `fly.toml`:

```toml
app = "shl-recommender"
primary_region = "iad"

[build]
  image = "shl-recommender:latest"

[env]
  PYTHONUNBUFFERED = "true"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true

[env]
  ANTHROPIC_API_KEY = "your-api-key"
```

4. Deploy:

```bash
fly auth login
fly launch
fly deploy
```

## Option 3: Railway

### Setup

1. Go to https://railway.app
2. Click "Start a New Project"
3. Select "GitHub repo" or upload directly
4. Railway auto-detects FastAPI
5. Add environment variables in the Railway dashboard:
   - `ANTHROPIC_API_KEY`: Your API key
6. Railway automatically builds and deploys

Your API will be at `https://<project>.railway.app`

## Option 4: Modal (Serverless Functions)

### Setup

1. Install Modal: `pip install modal`
2. Create `modal_app.py`:

```python
import modal

app = modal.App(name="shl-recommender")

@app.function(timeout=300, cpu=1, memory=512, allow_concurrent_requests=10)
@modal.asgi_app()
def fastapi_app():
    from main import app
    return app

@app.local_entrypoint()
def main():
    fastapi_app.deploy()
```

3. Deploy:

```bash
modal token new  # Get API token
modal deploy modal_app.py
```

## Option 5: Hugging Face Spaces (with Docker)

### Setup

1. Create a new Space: https://huggingface.co/spaces
2. Select "Docker" as the SDK
3. Create `Dockerfile` (as above)
4. Create `README.md` with descriptions
5. Add `HF_SPACE_SECRETS` for `ANTHROPIC_API_KEY`
6. Push code to the Space repository

## Docker Setup (Local Testing)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
docker build -t shl-recommender .
docker run -p 8000:8000 -e ANTHROPIC_API_KEY="your-key" shl-recommender
```

## Environment Variables

Required:

- `ANTHROPIC_API_KEY`: Your Anthropic API key

Optional:

- `HOST`: Default `0.0.0.0`
- `PORT`: Default `8000`
- `ENVIRONMENT`: Default `development`

## Performance Tuning

### For High Load

1. **Increase worker count** (Render, Railway):
   - Render: Set `numProcesses` in `render.yaml`
   - Railway: Scale up instances

2. **Use caching** (optional):
   - Cache catalog in Redis
   - Cache recent recommendations

3. **Add CDN** (optional):
   - Put behind Cloudflare for edge caching
   - Reduces latency for health checks

### Request Optimization

- Set timeout to 30 seconds (matches assignment limit)
- Use connection pooling in httpx
- Batch catalog fetches

## Monitoring and Debugging

### Logs

All platforms provide log access:

- **Render**: Dashboard → Logs
- **Fly**: `fly logs`
- **Railway**: Dashboard → Logs
- **Spaces**: Check Space logs

### Error Tracking (Optional)

Add Sentry for error tracking:

```python
import sentry_sdk
sentry_sdk.init(dsn="your-sentry-dsn")
```

### Health Check

The `/health` endpoint is used for readiness checking:

- Render: Automatic checks
- Fly: Configured in `fly.toml`
- Railway: Automatic

## Security

1. **API Key**: Never commit `.env` files
2. **CORS**: Configure if needed in `main.py`
3. **Rate Limiting** (optional):
   ```python
   from slowapi import Limiter
   limiter = Limiter(key_func=get_remote_address)
   ```

## Cost Estimation

- **Render**: Free tier (500 hrs/month), then $7+
- **Fly**: Free tier generous, ~$5/month for small apps
- **Railway**: Free tier, then pay-as-you-go
- **Modal**: Free tier with limits, then $0.00002 per GB-second
- **Spaces**: Free tier with limited CPU, paid tier $7/month

## Deployment Checklist

- [ ] Code pushed to Git
- [ ] `requirements.txt` complete and tested
- [ ] `.env.example` provided (no secrets)
- [ ] `Dockerfile` created and tested locally
- [ ] API tested locally: `python test_api.py`
- [ ] Platform account created
- [ ] Environment variables configured
- [ ] Deployment successful
- [ ] Health check returning `{"status": "ok"}`
- [ ] Sample chat request working
- [ ] Monitoring set up

## Troubleshooting

### Cold Start Issues

- Symptom: First request times out
- Solution: Ensure timeout > 30 seconds in platform config
- Render: First cold start can take up to 2 minutes

### API Key Errors

- Symptom: `ANTHROPIC_API_KEY not set`
- Solution: Verify environment variable in platform dashboard
- Check: `echo $ANTHROPIC_API_KEY` in production

### Memory Issues

- Symptom: Out of memory errors
- Solution: Increase memory allocation in platform config
- Catalog caching: Disable if memory constrained

### Response Time

- Symptom: Requests timing out
- Check: LLM API latency (Anthropic status page)
- Optimize: Reduce catalog size or add caching
