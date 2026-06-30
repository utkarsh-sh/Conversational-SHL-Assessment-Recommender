#!/usr/bin/env python3
"""
Pre-Submission Checklist for SHL Recommender
Run this checklist before submitting to ensure everything is ready
"""

checklist = """
╔══════════════════════════════════════════════════════════════════════════════╗
║         SHL RECOMMENDER - PRE-SUBMISSION CHECKLIST                          ║
║                Last check before sending to evaluators                       ║
╚══════════════════════════════════════════════════════════════════════════════╝


📋 CODE QUALITY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

☐ main.py
  ☐ Has @app.get("/health") endpoint
  ☐ Has @app.post("/chat") endpoint
  ☐ ChatRequest model defined
  ☐ ChatResponse model defined
  ☐ Recommendation model defined with name, url, test_type
  ☐ Response schema exactly matches specification
  ☐ Validates all recommendations against catalog
  ☐ No hardcoded test data in production code

☐ agent_logic.py
  ☐ ConversationalAgent class exists
  ☐ Uses Claude (not GPT or other LLM)
  ☐ Handles multi-turn conversations
  ☐ Validates output is valid JSON
  ☐ Enforces 8-turn limit
  ☐ Returns empty recommendations during clarification
  ☐ Includes turn-by-turn strategy in comments

☐ catalog_manager.py
  ☐ Loads SHL catalog (real or fallback)
  ☐ Caches catalog locally
  ☐ Validates assessments exist in catalog
  ☐ Returns assessment metadata (name, url, type)
  ☐ Handles missing/corrupt cache gracefully

☐ catalog_scraper.py
  ☐ Multi-strategy scraping approach
  ☐ Fallback to seed data if scraping fails
  ☐ Handles malformed HTML
  ☐ Returns consistent data format

☐ requirements.txt
  ☐ Includes fastapi
  ☐ Includes uvicorn
  ☐ Includes anthropic
  ☐ Includes all dependencies used in code
  ☐ No unnecessary packages
  ☐ Pinned versions (no wildcards)


🧪 TESTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

☐ Local testing completed
  ☐ python setup.py runs without errors
  ☐ python main.py starts successfully
  ☐ python test_api.py passes all tests
  ☐ python run_tests.py completes without errors
  ☐ python validate_submission.py shows no failures

☐ Test coverage
  ☐ Health check tested (/health returns 200)
  ☐ Chat with vague query tested (no recommendations on turn 1)
  ☐ Chat with specific query tested (gets recommendations)
  ☐ Multi-turn conversation tested
  ☐ Off-topic refusal tested
  ☐ Turn limit enforcement tested (max 8 turns)
  ☐ Hallucination test (no fake assessments)

☐ Schema validation
  ☐ Every response is valid JSON
  ☐ All responses have "reply" field
  ☐ All responses have "recommendations" array
  ☐ All responses have "end_of_conversation" boolean
  ☐ Recommendations are 0-10 items
  ☐ Each recommendation has name, url, test_type


🔐 ENVIRONMENT & SECRETS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

☐ .env.example exists and is complete
  ☐ No actual API keys in .env.example
  ☐ All required variables documented
  ☐ Comments explain each variable

☐ Source code has no secrets
  ☐ No API keys in Python files
  ☐ No hardcoded credentials
  ☐ API key only used from environment variable


📦 DEPLOYMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

☐ Dockerfile created and tested
  ☐ Builds successfully: docker build -t shl .
  ☐ Runs successfully: docker run -p 8000:8000 shl
  ☐ Has HEALTHCHECK configured
  ☐ Exposes port 8000
  ☐ Sets PYTHONUNBUFFERED

☐ Docker Compose created
  ☐ Works with docker-compose up
  ☐ Has volume mounts for development
  ☐ Has environment variables
  ☐ Has healthcheck

☐ Deployment platform chosen
  ☐ Render / Fly.io / Railway / Modal / HF Spaces selected
  ☐ DEPLOYMENT.md reviewed for chosen platform
  ☐ Cost estimates reviewed
  ☐ Deployment tested locally

☐ API deployed and tested
  ☐ Deployment successful (no errors in logs)
  ☐ Health endpoint working: curl https://api.../health
  ☐ Chat endpoint working: test with sample conversation
  ☐ API endpoint URL is stable (won't change)
  ☐ CORS configured if needed
  ☐ Logging configured


📖 DOCUMENTATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

☐ README.md exists and is comprehensive
  ☐ Quick start section (with working commands)
  ☐ API specification clearly documented
  ☐ Architecture explained
  ☐ Deployment instructions included
  ☐ Troubleshooting section present
  ☐ Project structure documented

☐ APPROACH.md exists and is exactly 2 pages
  ☐ Problem decomposition explained
  ☐ Architecture choices justified
  ☐ Prompt engineering approach described
  ☐ Catalog strategy documented
  ☐ Evaluation approach explained
  ☐ Trade-offs acknowledged
  ☐ What worked/didn't work section
  ☐ AI tool usage disclosed
  ☐ Well-organized and concise
  ☐ Spell-checked and proofread

☐ DEPLOYMENT.md exists with platform guides
  ☐ At least 3 platforms covered
  ☐ Step-by-step instructions
  ☐ Environment variable setup
  ☐ Cost estimates provided
  ☐ Troubleshooting section

☐ Code comments
  ☐ Complex functions documented
  ☐ Intent is clear
  ☐ No obvious bugs in comments


🎯 BEHAVIOR & CONSTRAINTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

☐ Conversation behavior correct
  ☐ Turn 1 vague query: Doesn't recommend, asks questions
  ☐ Turn 1 specific query: May recommend if detailed
  ☐ Turn 2-3: Gathers more context
  ☐ Turn 4+: Recommends 1-10 assessments
  ☐ Recommendations: All from catalog
  ☐ Refinements: Updates based on new constraints
  ☐ Comparisons: Answers based on catalog data
  ☐ Off-topic: Politely refuses

☐ Constraints enforced
  ☐ Max 8 turns per conversation
  ☐ Max 30 seconds per request (set on platform)
  ☐ Max 10 recommendations per response
  ☐ Min 0 recommendations during clarification
  ☐ All URLs from catalog (validated)

☐ Error handling
  ☐ Gracefully handles malformed requests
  ☐ Returns 400 for bad JSON
  ☐ Returns 503 if catalog not loaded
  ☐ Returns 500 with meaningful error messages
  ☐ Doesn't expose sensitive info in errors


🚀 FINAL CHECKS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

☐ All files in git repository
  ☐ README.md in root
  ☐ APPROACH.md in root
  ☐ Source code in shl_recommender/ directory
  ☐ .gitignore properly configured (no .env, __pycache__, etc.)

☐ API endpoint working live
  ☐ Health check returns 200: curl https://api/health
  ☐ Chat endpoint returns valid JSON
  ☐ No timeouts or 500 errors
  ☐ Recommendations contain only catalog items
  ☐ URL format correct (https://www.shl.com/...)

☐ Submission form completed
  ☐ API endpoint URL correct and accessible
  ☐ APPROACH.md file prepared (2 pages max)
  ☐ README.md link included
  ☐ GitHub repo link included (if applicable)


🔍 EVALUATOR PERSPECTIVE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Evaluators will check:
  ☐ Can call /health and get response
  ☐ Can call /chat and get valid JSON
  ☐ Schema compliance (exact format)
  ☐ All recommendations from real catalog
  ☐ Turn limits respected
  ☐ Vague queries don't get immediate recommendations
  ☐ Off-topic requests are refused
  ☐ Recall@10 metric on test traces
  ☐ APPROACH.md is well-written and concise
  ☐ Code is clean and maintainable


✅ SUBMISSION READY CHECKLIST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Only check this if ALL items above are complete:

☐ READY TO SUBMIT
  ✓ Code passes all local tests
  ✓ API deployed and publicly accessible
  ✓ APPROACH.md is 2 pages and well-written
  ✓ README.md is comprehensive
  ✓ No secrets in code or docs
  ✓ Deployment instructions clear
  ✓ All hard requirements met
  ✓ Behavior probes passing


📋 SUBMISSION FORM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Fields required:
  1. Public API endpoint URL
     Example: https://shl-recommender-xy123.onrender.com
     
  2. Approach document (APPROACH.md)
     2 pages max, covers:
     - Design choices
     - Retrieval setup  
     - Prompt design
     - Evaluation approach
     - What worked/didn't work

Optional:
  3. GitHub repository link
  4. Additional notes


═══════════════════════════════════════════════════════════════════════════════

Print this checklist and work through it systematically.
Ensure every item is checked before submitting.

Good luck! 🚀

═══════════════════════════════════════════════════════════════════════════════
"""

if __name__ == "__main__":
    print(checklist)
    
    # Optionally save to file
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "save":
        with open("PRE_SUBMISSION_CHECKLIST.txt", "w") as f:
            f.write(checklist)
        print("\n✓ Checklist saved to PRE_SUBMISSION_CHECKLIST.txt")
