#!/usr/bin/env bash
# SHL Recommender - Running Locally

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║      SHL Assessment Recommender - Local Development Guide                 ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if in correct directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: Please run this from the shl_recommender directory"
    echo "   cd shl_recommender/"
    exit 1
fi

echo "✓ In correct directory"
echo ""

# Step 1: Install dependencies
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1: Install Dependencies"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment exists"
fi

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✓ Virtual environment activated"
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
    echo "✓ Virtual environment activated"
fi

# Install requirements
echo ""
echo "Installing Python packages..."
pip install -q -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Step 2: Setup environment
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2: Configure Environment"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo ""
    echo "⚠️  ANTHROPIC_API_KEY environment variable not set"
    echo ""
    echo "Set it with:"
    echo "  export ANTHROPIC_API_KEY='sk-ant-...'"
    echo ""
    echo "Or edit .env file and run:"
    echo "  source .env"
    echo ""
else
    echo "✓ ANTHROPIC_API_KEY is set"
fi

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✓ Created .env from .env.example"
    fi
fi

echo ""

# Step 3: Run pre-flight checks
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3: Pre-flight Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python validate_submission.py
if [ $? -ne 0 ]; then
    echo ""
    echo "⚠️  Some validation checks failed"
    echo "Please review the output above"
fi

echo ""

# Step 4: Start the server
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 4: Start Server"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Starting FastAPI server..."
echo "API will be available at: http://localhost:8000"
echo ""
echo "Available endpoints:"
echo "  GET  http://localhost:8000/health  (health check)"
echo "  POST http://localhost:8000/chat    (conversation)"
echo "  GET  http://localhost:8000/docs    (API docs - Swagger UI)"
echo ""
echo "To test in another terminal:"
echo "  python test_api.py"
echo ""
echo "To run comprehensive tests:"
echo "  python run_tests.py"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python main.py
