#!/usr/bin/env python3
"""Pre-submission checks for the SHL recommender."""

import json
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


class SubmissionValidator:
    """Validate files and hard-eval guardrails before deployment."""

    def __init__(self):
        self.checks = []
        self.passed = 0
        self.failed = 0

    def check(self, name: str, condition: bool, details: str = ""):
        status = "[PASS]" if condition else "[FAIL]"
        self.checks.append(
            {
                "name": name,
                "status": status,
                "condition": condition,
                "details": details,
            }
        )
        self.passed += int(condition)
        self.failed += int(not condition)
        print(f"{status}: {name}")
        if details:
            print(f"       {details}")

    def print_summary(self) -> bool:
        print("\n" + "=" * 70)
        print("SUBMISSION VALIDATION SUMMARY")
        print("=" * 70)
        print(f"\nPassed: {self.passed}/{len(self.checks)}")
        print(f"Failed: {self.failed}/{len(self.checks)}")
        if self.failed:
            print("\nFAILED CHECKS:")
            for check in self.checks:
                if not check["condition"]:
                    print(f"   - {check['name']}")
                    if check["details"]:
                        print(f"     {check['details']}")
        print("\n" + "=" * 70)
        return self.failed == 0

    def validate_files(self):
        print("\n[1/6] Checking required files...")
        for filename in [
            "main.py",
            "catalog_manager.py",
            "catalog_scraper.py",
            "agent_logic.py",
            "requirements.txt",
            "README.md",
            "APPROACH.md",
            "Dockerfile",
        ]:
            path = BASE_DIR / filename
            self.check(f"File: {filename}", path.exists(), str(path))

    def validate_endpoints(self):
        print("\n[2/6] Checking API endpoints...")
        content = (BASE_DIR / "main.py").read_text(encoding="utf-8")
        self.check("Has /health endpoint", '@app.get("/health")' in content)
        self.check("Has /chat endpoint", '@app.post("/chat")' in content)
        self.check("Has ChatRequest model", "class ChatRequest" in content)
        self.check("Has ChatResponse model", "class ChatResponse" in content)

    def validate_schema(self):
        print("\n[3/6] Checking response schema...")
        content = (BASE_DIR / "main.py").read_text(encoding="utf-8")
        for field in ["reply", "recommendations", "end_of_conversation"]:
            self.check(f"Response has {field}", field in content)
        self.check("Recommendation model defined", "class Recommendation" in content)

    def validate_agent(self):
        print("\n[4/6] Checking agent logic...")
        content = (BASE_DIR / "agent_logic.py").read_text(encoding="utf-8")
        self.check("ConversationalAgent class exists", "class ConversationalAgent" in content)
        self.check("Has deterministic fallback", "_deterministic_response" in content)
        self.check("Canonicalizes recommendations", "canonicalize_recommendation" in content)
        self.check("Handles vague first turn", "_is_vague" in content)
        self.check("Handles comparison requests", "_compare_assessments" in content)

    def validate_catalog(self):
        print("\n[5/6] Checking catalog management...")
        content = (BASE_DIR / "catalog_manager.py").read_text(encoding="utf-8")
        self.check("CatalogManager class exists", "class CatalogManager" in content)
        self.check("Loads catalog", "load_catalog" in content)
        self.check("Validates assessment names", "validate_assessment" in content)
        self.check("Validates canonical URLs", "validate_recommendation" in content)
        self.check("Uses file-local cache", "Path(__file__).with_name" in content)

        cache_path = BASE_DIR / "catalog_cache.json"
        if cache_path.exists():
            data = json.loads(cache_path.read_text(encoding="utf-8"))
            count = len(data.get("assessments", {}))
            self.check("Catalog cache has usable records", count >= 10, f"Found {count} records")
        else:
            self.check("Catalog cache exists", False, str(cache_path))

    def validate_testing(self):
        print("\n[6/6] Checking testing infrastructure...")
        for filename in ["test_api.py", "run_tests.py", "evaluation.py"]:
            path = BASE_DIR / filename
            self.check(f"Test file: {filename}", path.exists(), str(path))


def validate_docker():
    print("\n[OPTIONAL] Checking Docker setup...")
    validator = SubmissionValidator()
    dockerfile = BASE_DIR / "Dockerfile"
    validator.check("Dockerfile exists", dockerfile.exists(), str(dockerfile))
    if dockerfile.exists():
        content = dockerfile.read_text(encoding="utf-8")
        validator.check("Dockerfile exposes port 8000", "8000" in content)
        validator.check("Dockerfile has healthcheck", "HEALTHCHECK" in content)


def main():
    print("\n" + "=" * 70)
    print("SHL RECOMMENDER - SUBMISSION VALIDATOR")
    print("=" * 70)

    validator = SubmissionValidator()
    validator.validate_files()
    validator.validate_endpoints()
    validator.validate_schema()
    validator.validate_agent()
    validator.validate_catalog()
    validator.validate_testing()
    validate_docker()

    if validator.print_summary():
        print("\n[PASS] Core submission checks passed.")
        return

    print("\n[FAIL] Some checks failed. Fix the issues above before submitting.")
    sys.exit(1)


if __name__ == "__main__":
    main()
