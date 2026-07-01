# SHL Assessment Recommender

A conversational AI agent that helps hiring managers and recruiters find the right SHL assessments through natural dialogue.

## Quick Start

### Prerequisites

- Python 3.10+
- Anthropic API key

### Setup

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   - Copy `.env.example` to `.env`
   - Add your Anthropic API key to `.env`

3. **Run the server:**
   ```bash
   python main.py
   ```

The API will start at `http://localhost:8000`

### API Endpoints

#### Health Check

```
GET /health
```

Returns: `{"status": "ok"}`

#### Chat

```
POST /chat
Content-Type: application/json

{
  "messages": [
    {"role": "user", "content": "I need a Java assessment"},
    {"role": "assistant", "content": "What seniority level?"}
  ]
}
```

Returns:

```json
{
  "reply": "Your response here",
  "recommendations": [
    {
      "name": "Assessment Name",
      "url": "https://...",
      "test_type": "K"
    }
  ],
  "end_of_conversation": false
}
```

## Testing

Run the local test script:

```bash
python test_api.py
```

## Project Structure

- `main.py` - FastAPI application and endpoints
- `catalog_manager.py` - SHL catalog management and scraping
- `agent_logic.py` - Conversational agent using Claude
- `test_api.py` - Local testing utilities
- `requirements.txt` - Python dependencies

## Architecture

### Catalog Manager

- Fetches SHL product catalog from https://www.shl.com/solutions/products/productcatalog/
- Caches locally to avoid repeated requests
- Validates assessment names and URLs

### Agent Logic

- Uses Claude 3.5 Sonnet for natural language understanding
- Maintains conversation context across turns
- Parses JSON recommendations from Claude
- Enforces schema compliance

### FastAPI Service

- Stateless endpoint design (all context passed per request)
- Respects conversation turn limits (max 8)
- Validates recommendations against catalog
- 30-second timeout per request

## Design Decisions

### Why Stateless?

The assignment requires stateless endpoints. All conversation history is passed with each request, allowing for simple horizontal scaling and no session management overhead.

### Why Claude?

Claude provides excellent instruction-following and can handle complex clarification logic. The model can read the full catalog in its context and consistently return valid recommendations.

### Catalog Caching

First load fetches from SHL website and caches locally. Subsequent runs use the cache for faster startup. This balances freshness with performance.

### Agent Behavior

The agent:

1. Asks clarifying questions for vague queries
2. Avoids recommendations until it has sufficient context
3. Supports mid-conversation refinements
4. Can compare assessments based on catalog data
5. Refuses off-topic requests

## Limitations and Future Improvements

- Catalog parser is generic; may need HTML structure adjustments for SHL website
- Vector search not yet implemented (could improve matching)
- No fine-tuning on assessment-specific examples
- Limited handling of comparative queries

## Deployment

For production deployment:

1. Use a FastAPI server like Gunicorn with Uvicorn workers
2. Configure CORS for your frontend
3. Use environment variables for secrets
4. Consider adding request logging and monitoring
5. Set up database or persistent cache for catalog updates
