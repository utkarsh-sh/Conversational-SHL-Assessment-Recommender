#!/usr/bin/env python3
"""Quick setup script for SHL Recommender."""

import os
import sys
import subprocess
from pathlib import Path


def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60 + "\n")


def check_python():
    """Check Python version."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("❌ Python 3.10+ required")
        sys.exit(1)
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")


def check_dependencies():
    """Check if required commands are available."""
    required = {
        "pip": "pip --version",
        "python": "python --version"
    }
    
    optional = {
        "docker": "docker --version",
        "curl": "curl --version"
    }
    
    print_header("Checking Dependencies")
    
    for tool, cmd in required.items():
        try:
            subprocess.run(cmd, shell=True, capture_output=True, check=True)
            print(f"✓ {tool}")
        except:
            print(f"❌ {tool} not found")
            sys.exit(1)
    
    for tool, cmd in optional.items():
        try:
            subprocess.run(cmd, shell=True, capture_output=True, check=True)
            print(f"✓ {tool} (optional)")
        except:
            print(f"⊘ {tool} not found (optional)")


def setup_env():
    """Set up environment file."""
    print_header("Setting Up Environment")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("✓ .env already exists")
        return
    
    if env_example.exists():
        # Copy example to .env
        with open(env_example) as f:
            content = f.read()
        with open(env_file, 'w') as f:
            f.write(content)
        print("✓ Created .env from .env.example")
    
    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("\n⚠️  ANTHROPIC_API_KEY not set!")
        print("   Set it before running:")
        print("   export ANTHROPIC_API_KEY='your-key-here'")
        print("   Or edit .env file")


def install_dependencies():
    """Install Python dependencies."""
    print_header("Installing Dependencies")
    
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
            check=True
        )
        print("✓ Upgraded pip")
        
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True
        )
        print("✓ Installed requirements")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        sys.exit(1)


def test_imports():
    """Test that imports work."""
    print_header("Testing Imports")
    
    imports = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("pydantic", "Pydantic"),
        ("anthropic", "Anthropic"),
        ("bs4", "BeautifulSoup4"),
    ]
    
    for module, name in imports:
        try:
            __import__(module)
            print(f"✓ {name}")
        except ImportError:
            print(f"❌ {name} not found")
            sys.exit(1)


def suggest_next_steps():
    """Suggest next steps."""
    print_header("Next Steps")
    
    print("""
1. Set your Anthropic API key:
   export ANTHROPIC_API_KEY='sk-ant-...'

2. Run the server locally:
   python main.py
   
3. In another terminal, test the API:
   python test_api.py

4. Run comprehensive tests:
   python run_tests.py

5. Deploy (see DEPLOYMENT.md):
   - Render: Connect GitHub repo
   - Fly: fly deploy
   - Docker: docker-compose up

6. Submit:
   - API endpoint URL
   - APPROACH.md (2 pages max)
""")


def main():
    """Run setup."""
    print("\n🚀 SHL Recommender - Setup Script")
    
    check_python()
    check_dependencies()
    setup_env()
    install_dependencies()
    test_imports()
    suggest_next_steps()
    
    print_header("Setup Complete!")
    print("Ready to run the SHL Recommender service.\n")


if __name__ == "__main__":
    main()
