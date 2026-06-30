#!/bin/bash
# Quick Start Guide for SHL Recommender

echo "======================================"
echo "SHL Recommender - Quick Start"
echo "======================================"
echo ""

# Check Python version
echo "1. Checking Python..."
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "   Python version: $python_version"

# Install dependencies
echo ""
echo "2. Installing dependencies..."
pip install -q -r requirements.txt
echo "   ✓ Dependencies installed"

# Check for API key
echo ""
echo "3. Checking API key..."
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "   ⚠️  ANTHROPIC_API_KEY not set"
    echo "   Set it before running:"
    echo "   export ANTHROPIC_API_KEY='your-key-here'"
else
    echo "   ✓ ANTHROPIC_API_KEY is set"
fi

# Create .env if needed
echo ""
echo "4. Setting up environment..."
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    cp .env.example .env
    echo "   ✓ Created .env from .env.example"
else
    echo "   ✓ .env already exists"
fi

echo ""
echo "======================================"
echo "Ready to start the server!"
echo "======================================"
echo ""
echo "Run the following command:"
echo "  python main.py"
echo ""
echo "Then in another terminal, test with:"
echo "  python test_api.py"
echo ""
