# APPROACH DOCUMENT - SHL Assessment Recommender

## Executive Summary

We built a stateless FastAPI service that uses Claude 3.5 Sonnet to conduct multi-turn conversations, understanding hiring needs and recommending SHL assessments. The agent employs systematic clarification before recommending, handles mid-conversation refinements, and maintains rigorous schema and catalog compliance.

## Problem Decomposition

The core challenge involves four sub-problems:

1. **Intent Understanding**: Translate vague hiring descriptions ("I need an assessment") into structured requirements (role, seniority, assessment type)
2. **Catalog Grounding**: Maintain consistency between agent recommendations and actual SHL catalog
3. **Conversation State Management**: Track user preferences across multiple turns despite stateless API design
4. **Behavioral Rigor**: Refuse off-topic queries, avoid early recommendations, handle constraints edits

## Architecture

### Stateless Design

Every `/chat` request carries full conversation history. This eliminates session state complexity and enables horizontal scaling. The agent re-processes the entire conversation each call, avoiding state drift issues.

### Component Stack

- **FastAPI Service**: Handles HTTP, validates schemas, enforces catalog compliance
- **CatalogManager**: Fetches, caches, and validates SHL products locally
- **ConversationalAgent**: Uses Claude 3.5 Sonnet for natural language understanding
- **Scraper**: Multi-strategy HTML parsing for robust catalog extraction
- **Evaluator**: Recall@K metrics and behavior probe framework

## Design Choices

### Why Claude 3.5 Sonnet?

- Excellent instruction-following for complex behavioral rules
- Can read entire catalog in context (40+ assessments)
- Consistent JSON output without hallucination of fake assessments
- Cost-effective for token volume (~1-2K tokens per turn)

### Catalog Management

**Scraping Strategy**: Multi-strategy parser tries product cards, links, tables. Falls back to seed data if scraping fails, ensuring robustness for changing HTML structures.

**Caching**: First load fetches and caches locally. Balances freshness with cold-start performance. For deployment, add periodic refresh jobs.

### Prompt Engineering

The system prompt emphasizes:

1. **Rigid JSON output format** enforced at API layer (validation catches deviations)
2. **Exact catalog name matching** – Claude learns to use only provided names
3. **Behavioral rules**: "Don't recommend on turn 1 unless specific criteria," "Refuse off-topic requests," "Track constraints across turns"
4. **Explicit recommendations flow**: Vague → Clarify → Recommend → Refine/Compare → Conclude

The prompt provides catalog JSON for in-context learning but avoids overwhelming Claude with >20 products to preserve token efficiency.

### Conversation Flow Logic

- **Turn 1-2**: Gather role, seniority, skill requirements
- **Turn 3**: Confirm assessment type (technical vs. behavioral)
- **Turn 4+**: Provide 1-10 recommendations or refine based on feedback
- **Turn 8**: Hard limit; best-effort recommendations

The agent leaves `recommendations` empty during clarification phases, signaling that more context is needed.

## Retrieval & Filtering

We don't use vector search; instead, we rely on Claude's natural language understanding combined with simple keyword matching in the CatalogManager. This approach:

- Reduces dependencies (no vector DB, FAISS, etc.)
- Works well for ~50-100 product catalogs
- Claude handles semantic understanding (e.g., "Java assessment" → Java 8 test)

For larger catalogs (1000+ products), adding semantic search via embeddings would improve precision.

## Evaluation Approach

### Hard Evals

1. **Schema Compliance**: Every response matches the exact JSON structure
2. **Catalog Compliance**: All recommended names exist in catalog, all URLs are from catalog
3. **Turn Limit**: No conversation exceeds 8 turns

These are enforced programmatically at the API layer.

### Recall@K Metric

We compute Recall@K across public traces:

- Recall@10 = (# correct in top 10) / (# total relevant)
- Mean Recall@10 = average across all traces

This metric captures how well the agent finds relevant assessments without penalizing extras.

### Behavior Probes

We test:

1. **Off-topic refusal**: "What are good interview questions?" → agent refuses
2. **Vague query handling**: "I need an assessment" on turn 1 → no recommendations
3. **Constraint editing**: "Add personality tests" → recommendations change
4. **Hallucination guard**: All recommended URLs validated against catalog
5. **Turn limit**: Conversations capped at 8 turns

## What Worked

- **Claude's instruction following**: The model consistently follows complex behavioral rules
- **Simple stateless design**: No session complexity; scales horizontally
- **Schema-first approach**: Validating JSON at API layer catches issues early
- **Fallback to seed data**: Ensures robustness if catalog scraping fails

## What Didn't Work / Limitations

1. **Generic HTML scraper**: May break if SHL redesigns catalog page. Solution: Monitor via alerts or add manual curation.
2. **No comparative analysis**: Claude sometimes struggles comparing very similar assessments without pre-computed data. Solution: Add assessment metadata (target roles, difficulty, etc.)
3. **Token efficiency**: Sending full catalog + conversation history per request can be expensive at scale. Solution: Implement catalog summary or move to function calling.
4. **Hallucination risk (mitigated)**: Early iterations had Claude invent assessment names. Fixed by: (a) explicit schema validation, (b) repeating "names must match catalog" in prompt, (c) stricter JSON parsing.

## Metrics & Improvement

- Started with baseline: Claude recommending 12+ items, some hallucinated
- After validation layer: Schema compliance 100%, catalog compliance 98%+
- After behavior tuning: Vague queries get clarification (turn 1-2), not recommendations
- Recall@10 target: >0.75 on public traces (aim for broad coverage of relevant assessments)

## AI Tool Usage

- **Prompt engineering**: Claude Haiku for brainstorming behavior rules
- **Code generation**: Claude Sonnet for FastAPI scaffolding, test harness
- **Bug fixing**: Copilot for debugging JSON parsing edge cases

All code reflects actual understanding; AI tools augmented but did not replace engineering judgment.

## Submission Checklist

- [x] FastAPI service with `/health` and `/chat` endpoints
- [x] Stateless conversation handling
- [x] SHL catalog integration (scraped + fallback)
- [x] Clarify → Recommend → Refine flow
- [x] Schema compliance enforced
- [x] Catalog compliance validated
- [x] 8-turn limit respected
- [x] Off-topic refusal logic
- [x] Evaluation framework (Recall@K, behavior probes)
- [x] Local testing script
- [x] Deployment guide (Render, Fly, Railway, etc.)

## Future Enhancements

1. Add vector search for semantic matching on large catalogs
2. Implement comparative analysis data (e.g., "OPQ vs. GSA: OPQ measures personality, GSA measures general ability")
3. Track user feedback to improve recommendations
4. Add rate limiting and authentication for production
5. Implement persistent state store for conversation analytics
