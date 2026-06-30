#!/usr/bin/env python3
"""
Comprehensive validation script for SHL Recommender submission.
Tests all requirements before deployment.
"""

import subprocess
import sys
import json
from pathlib import Path


class SubmissionValidator:
    """Validate submission meets all requirements."""
    
    def __init__(self):
        self.checks = []
        self.passed = 0
        self.failed = 0
    
    def check(self, name: str, condition: bool, details: str = ""):
        """Record a check result."""
        status = "✓ PASS" if condition else "✗ FAIL"
        self.checks.append({
            "name": name,
            "status": status,
            "condition": condition,
            "details": details
        })
        
        if condition:
            self.passed += 1
        else:
            self.failed += 1
        
        print(f"{status}: {name}")
        if details:
            print(f"       {details}")
    
    def print_summary(self):
        """Print validation summary."""
        print("\n" + "=" * 70)
        print("SUBMISSION VALIDATION SUMMARY")
        print("=" * 70)
        
        print(f"\nPassed: {self.passed}/{len(self.checks)}")
        print(f"Failed: {self.failed}/{len(self.checks)}")
        
        if self.failed > 0:
            print("\n⚠️  FAILED CHECKS:")
            for check in self.checks:
                if not check["condition"]:
                    print(f"   • {check['name']}")
                    if check["details"]:
                        print(f"     {check['details']}")
        
        print("\n" + "=" * 70)
        
        return self.failed == 0
    
    def validate_files(self):
        """Validate all required files exist."""
        print("\n[1/6] Checking Required Files...")
        
        required_files = [
            "main.py",
            "catalog_manager.py",
            "agent_logic.py",
            "requirements.txt",
            "README.md",
            "APPROACH.md",
            "Dockerfile"
        ]
        
        for file in required_files:
            path = Path(file)
            self.check(f"File: {file}", path.exists(), 
                      f"Found at {path}")
    
    def validate_endpoints(self):
        """Validate API endpoints are correctly defined."""
        print("\n[2/6] Checking API Endpoints...")
        
        # Check main.py has required endpoints
        main_path = Path("main.py")
        if main_path.exists():
            content = main_path.read_text()
            
            has_health = "@app.get(\"/health\")" in content
            has_chat = "@app.post(\"/chat\")" in content
            has_chat_request = "class ChatRequest" in content
            has_chat_response = "class ChatResponse" in content
            
            self.check("Has /health endpoint", has_health)
            self.check("Has /chat endpoint", has_chat)
            self.check("Has ChatRequest model", has_chat_request)
            self.check("Has ChatResponse model", has_chat_response)
    
    def validate_schema(self):
        """Validate response schema."""
        print("\n[3/6] Checking Response Schema...")
        
        main_path = Path("main.py")
        if main_path.exists():
            content = main_path.read_text()
            
            has_reply = '"reply"' in content
            has_recommendations = '"recommendations"' in content
            has_end_of_conversation = '"end_of_conversation"' in content
            has_recommendation_model = "class Recommendation" in content
            
            self.check("Response has 'reply' field", has_reply)
            self.check("Response has 'recommendations' field", has_recommendations)
            self.check("Response has 'end_of_conversation' field", has_end_of_conversation)
            self.check("Recommendation model defined", has_recommendation_model)
    
    def validate_agent(self):
        """Validate agent logic."""
        print("\n[4/6] Checking Agent Logic...")
        
        agent_path = Path("agent_logic.py")
        if agent_path.exists():
            content = agent_path.read_text()
            
            has_class = "class ConversationalAgent" in content
            has_claude = "Anthropic" in content or "claude" in content.lower()
            has_catalog_validation = "validate_assessment" in content
            has_json_parsing = "json" in content
            
            self.check("ConversationalAgent class exists", has_class)
            self.check("Uses Claude LLM", has_claude)
            self.check("Validates against catalog", has_catalog_validation)
            self.check("Parses JSON responses", has_json_parsing)
    
    def validate_catalog(self):
        """Validate catalog handling."""
        print("\n[5/6] Checking Catalog Management...")
        
        catalog_path = Path("catalog_manager.py")
        if catalog_path.exists():
            content = catalog_path.read_text()
            
            has_class = "class CatalogManager" in content
            has_load = "load_catalog" in content
            has_validate = "validate_assessment" in content
            has_scraper = "CatalogScraper" in content or "scrape" in content.lower()
            has_cache = "cache" in content.lower()
            
            self.check("CatalogManager class exists", has_class)
            self.check("Has load_catalog method", has_load)
            self.check("Has validate_assessment method", has_validate)
            self.check("Has scraping strategy", has_scraper)
            self.check("Has caching strategy", has_cache)
    
    def validate_testing(self):
        """Validate testing infrastructure."""
        print("\n[6/6] Checking Testing Infrastructure...")
        
        files = {
            "test_api.py": "Basic API tests",
            "run_tests.py": "Comprehensive test suite",
            "evaluation.py": "Evaluation metrics",
            "APPROACH.md": "Design approach document"
        }
        
        for file, desc in files.items():
            path = Path(file)
            self.check(f"{desc}", path.exists(), f"File: {file}")


def validate_docker():
    """Validate Docker setup."""
    print("\n[OPTIONAL] Validating Docker Setup...")
    
    validator = SubmissionValidator()
    
    dockerfile = Path("Dockerfile")
    compose = Path("docker-compose.yml")
    
    validator.check("Dockerfile exists", dockerfile.exists())
    validator.check("docker-compose.yml exists", compose.exists())
    
    if dockerfile.exists():
        content = dockerfile.read_text()
        validator.check("Dockerfile builds for Python", "python" in content.lower())
        validator.check("Dockerfile exposes port 8000", "8000" in content)
        validator.check("Dockerfile has HEALTHCHECK", "HEALTHCHECK" in content)


def validate_deployment():
    """Check deployment readiness."""
    print("\n[OPTIONAL] Checking Deployment Readiness...")
    
    validator = SubmissionValidator()
    
    deployment_guide = Path("DEPLOYMENT.md")
    requirements = Path("requirements.txt")
    
    validator.check("DEPLOYMENT.md exists", deployment_guide.exists())
    validator.check("requirements.txt exists", requirements.exists())
    
    if requirements.exists():
        content = requirements.read_text()
        validator.check("Has fastapi", "fastapi" in content)
        validator.check("Has uvicorn", "uvicorn" in content)
        validator.check("Has anthropic SDK", "anthropic" in content)


def main():
    """Run all validations."""
    print("\n" + "=" * 70)
    print("SHL RECOMMENDER - SUBMISSION VALIDATOR")
    print("=" * 70)
    
    validator = SubmissionValidator()
    
    # Run core validations
    validator.validate_files()
    validator.validate_endpoints()
    validator.validate_schema()
    validator.validate_agent()
    validator.validate_catalog()
    validator.validate_testing()
    
    # Optional validations
    validate_docker()
    validate_deployment()
    
    # Print summary
    success = validator.print_summary()
    
    if success:
        print("\n✓ All core requirements met!")
        print("\nNext steps:")
        print("  1. Set your ANTHROPIC_API_KEY")
        print("  2. Run: python main.py")
        print("  3. Test: python test_api.py")
        print("  4. Deploy: See DEPLOYMENT.md")
    else:
        print("\n✗ Some requirements not met. Please fix issues above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
