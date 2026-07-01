import json
import re
from typing import List, Dict, Optional, Any
import os
from pathlib import Path
from catalog_scraper import CatalogScraper, SEED_ASSESSMENTS


class CatalogManager:
    """Manages the SHL assessment catalog."""
    
    CATALOG_URL = "https://www.shl.com/solutions/products/product-catalog/"
    CACHE_FILE = Path(__file__).with_name("catalog_cache.json")
    MIN_CATALOG_SIZE = int(os.getenv("MIN_CATALOG_SIZE", "50"))
    MAX_NAME_LENGTH = 100
    
    def __init__(self):
        self.assessments: Dict[str, Dict[str, Any]] = {}
        self.assessment_by_name: Dict[str, Dict[str, Any]] = {}
        
    async def load_catalog(self):
        """Load catalog from cache or fetch from SHL website."""
        cached_items = []
        cached_count = 0

        # Try to load from cache first
        if self.CACHE_FILE.exists():
            try:
                with self.CACHE_FILE.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                    cached_items = list(data.get("assessments", {}).values())
                    self._load_items(cached_items)
                    cached_count = len(self.assessments)
                    print(f"Loaded {cached_count} assessments from cache")

                    # Keep cache only if it looks complete enough for retrieval quality.
                    if cached_count >= self.MIN_CATALOG_SIZE:
                        return

                    print(
                        f"Cache appears stale/small ({cached_count} < {self.MIN_CATALOG_SIZE}), attempting fresh scrape"
                    )
            except Exception as e:
                print(f"Cache load failed: {e}, fetching fresh")
        
        # Fetch and parse catalog
        await self._fetch_and_parse_catalog()

        # Do not replace a better cache with a smaller fallback result.
        if len(self.assessments) < max(cached_count, 10) and cached_items:
            print("Fresh scrape produced fewer records than cache; keeping cached catalog")
            self._load_items(cached_items)
            return

        self._save_cache()
    
    async def _fetch_and_parse_catalog(self):
        """Fetch and parse the SHL product catalog."""
        try:
            # Use the enhanced scraper
            assessments_data = await CatalogScraper.scrape_catalog()
            
            if assessments_data:
                self._load_items(assessments_data)
                print(f"Scraped {len(self.assessments)} assessments from SHL catalog")
                return
            
            # If scraping failed or returned empty, use seed data
            print("Scraping returned empty results, using seed data")
            self._load_fallback_catalog()
            
        except Exception as e:
            print(f"Error fetching catalog: {e}")
            self._load_fallback_catalog()
    
    def _load_items(self, items):
        """Load normalized catalog records into lookup maps."""
        self.assessments = {}
        self.assessment_by_name = {}

        for item in items:
            name = self._clean_text(item.get("name", ""))
            url = item.get("url", "")
            if not name or not url:
                continue

            if not self._is_individual_assessment_record(name, url):
                continue

            description = self._clean_text(item.get("description") or name)
            test_type = item.get("test_type") or self._infer_test_type(name, description)
            assessment_id = self._make_id(name)
            record = {
                "name": name,
                "url": url,
                "description": description,
                "test_type": test_type,
                "id": assessment_id,
            }
            self.assessments[assessment_id] = record
            self.assessment_by_name[name] = record

    def _is_individual_assessment_record(self, name: str, url: str) -> bool:
        """Keep only records that are likely individual SHL assessments in scope."""
        lowered_url = url.lower()
        lowered_name = name.lower()

        # Assignment scope: individual test solutions only.
        allowed_url_patterns = [
            "/solutions/products/",
            "/products/assessments/",
        ]
        if not any(pattern in lowered_url for pattern in allowed_url_patterns):
            return False

        blocked_url_terms = [
            "job-solutions",
            "/products/video-interviews/",
            "/products/platform",
            "/products/technology/",
            "/products/services/",
            "/products/job-focused-assessments/",
            "/products/assessment-center/",
            "/products/development/",
        ]
        if any(term in lowered_url for term in blocked_url_terms):
            return False

        blocked_name_terms = [
            "discover",
            "screen thousands of candidates",
            "products",
            "solution",
        ]
        if any(term in lowered_name for term in blocked_name_terms):
            return False

        if len(name) > self.MAX_NAME_LENGTH:
            return False

        return True

    def _make_id(self, name: str) -> str:
        value = name.lower()
        value = value.replace("c++", "cpp")
        value = value.replace("c#", "csharp")
        value = value.replace(".net", "dotnet")
        return re.sub(r"[^a-z0-9]+", "_", value).strip("_")

    def _clean_text(self, value: str) -> str:
        return re.sub(r"\s+", " ", value or "").strip()
    
    def _infer_test_type(self, name: str, description: str) -> str:
        """Infer test type from name and description."""
        text = (name + " " + description).lower()
        # K = Knowledge/Technical
        if any(word in text for word in ["java", "javascript", "python", "c++", "c#", ".net", "html", "css", "sql", "coding", "technical", "knowledge", "skill"]):
            return "K"
        
        # P = Personality
        if any(word in text for word in ["personality", "behavioural", "behavior", "opq"]):
            return "P"
        
        # V = Verbal
        if any(word in text for word in ["verbal", "english", "language", "communication"]):
            return "V"
        
        # N = Numerical
        if any(word in text for word in ["numerical", "numeric", "math", "calculation"]):
            return "N"
        
        # Default to generic
        return "G"
    
    def _load_fallback_catalog(self):
        """Load a minimal fallback catalog for development/testing."""
        self._load_items(
            {
                "name": name,
                "url": url,
                "description": f"SHL {name} assessment",
            }
            for name, url in SEED_ASSESSMENTS.items()
        )
        print(f"Loaded {len(self.assessments)} assessments from seed data")
    
    def _save_cache(self):
        """Save catalog to cache file."""
        try:
            cache_data = {
                "assessments": self.assessments,
                "by_name": self.assessment_by_name
            }
            with self.CACHE_FILE.open("w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            print(f"Error saving cache: {e}")
    
    def get_all_assessments(self) -> List[Dict[str, Any]]:
        """Get all available assessments."""
        return list(self.assessments.values())
    
    def get_assessment_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific assessment by name."""
        if not name:
            return None
        exact = self.assessment_by_name.get(name)
        if exact:
            return exact

        lowered = name.lower().strip()
        for assessment_name, assessment in self.assessment_by_name.items():
            candidate = assessment_name.lower()
            if lowered == candidate:
                return assessment
            if lowered and (lowered in candidate or candidate in lowered):
                return assessment

        normalized = self._make_id(name)
        return self.assessments.get(normalized)
    
    def validate_assessment(self, name: str) -> bool:
        """Validate that an assessment exists in the catalog."""
        return self.get_assessment_by_name(name) is not None

    def canonicalize_recommendation(self, rec: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Return the catalog-owned recommendation record, ignoring model URLs."""
        assessment = self.get_assessment_by_name(rec.get("name", ""))
        if not assessment:
            return None
        return {
            "name": assessment["name"],
            "url": assessment["url"],
            "test_type": assessment["test_type"],
        }

    def validate_recommendation(self, rec: Dict[str, Any]) -> bool:
        """Validate both name and URL against the catalog."""
        assessment = self.get_assessment_by_name(rec.get("name", ""))
        return bool(assessment and rec.get("url") == assessment.get("url"))
    
    def search_assessments(self, query: str, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Search for assessments based on query and filters."""
        query_terms = self._query_terms(query)
        scored = []
        
        for assessment in self.assessments.values():
            if filters and "test_type" in filters:
                allowed = set(filters["test_type"])
                actual = set(assessment["test_type"].split(","))
                if not actual & allowed:
                    continue

            text = f"{assessment['name']} {assessment['description']}".lower()
            score = 0
            for term in query_terms:
                if term in assessment["name"].lower():
                    score += 4
                elif term in text:
                    score += 1
            if score:
                scored.append((score, assessment["name"], assessment))
        
        scored.sort(key=lambda item: (-item[0], item[1]))
        return [item[2] for item in scored]

    def _query_terms(self, query: str) -> List[str]:
        stop_words = {
            "a", "an", "and", "are", "for", "i", "in", "is", "need", "of",
            "the", "to", "with", "who", "we", "hire", "hiring", "assessment",
            "assessments", "test", "tests", "candidate", "candidates",
        }
        terms = re.findall(r"[a-z0-9+#.]+", query.lower())
        return [term for term in terms if len(term) > 1 and term not in stop_words]
    
    def get_assessments_by_type(self, test_type: str) -> List[Dict[str, Any]]:
        """Get assessments by test type (K, P, V, N, G)."""
        return [a for a in self.assessments.values() if a["test_type"] == test_type]
