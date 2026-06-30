import asyncio
import json
from typing import List, Dict, Optional, Any
from bs4 import BeautifulSoup
import httpx
import os
from pathlib import Path
from catalog_scraper import CatalogScraper, SEED_ASSESSMENTS


class CatalogManager:
    """Manages the SHL assessment catalog."""
    
    CATALOG_URL = "https://www.shl.com/solutions/products/productcatalog/"
    CACHE_FILE = "catalog_cache.json"
    
    def __init__(self):
        self.assessments: Dict[str, Dict[str, Any]] = {}
        self.assessment_by_name: Dict[str, Dict[str, Any]] = {}
        
    async def load_catalog(self):
        """Load catalog from cache or fetch from SHL website."""
        # Try to load from cache first
        if os.path.exists(self.CACHE_FILE):
            try:
                with open(self.CACHE_FILE, 'r') as f:
                    data = json.load(f)
                    self.assessments = data.get("assessments", {})
                    self.assessment_by_name = data.get("by_name", {})
                    print(f"Loaded {len(self.assessments)} assessments from cache")
                    return
            except Exception as e:
                print(f"Cache load failed: {e}, fetching fresh")
        
        # Fetch and parse catalog
        await self._fetch_and_parse_catalog()
        self._save_cache()
    
    async def _fetch_and_parse_catalog(self):
        """Fetch and parse the SHL product catalog."""
        try:
            # Use the enhanced scraper
            assessments_data = await CatalogScraper.scrape_catalog()
            
            if assessments_data:
                for item in assessments_data:
                    assessment_id = item["name"].lower().replace(" ", "_").replace("(", "").replace(")", "")
                    description = item.get("description", item["name"])
                    
                    self.assessments[assessment_id] = {
                        "name": item["name"],
                        "url": item["url"],
                        "description": description,
                        "test_type": self._infer_test_type(item["name"], description),
                        "id": assessment_id
                    }
                    self.assessment_by_name[item["name"]] = self.assessments[assessment_id]
                
                print(f"Scraped {len(self.assessments)} assessments from SHL catalog")
                return
            
            # If scraping failed or returned empty, use seed data
            print("Scraping returned empty results, using seed data")
            self._load_fallback_catalog()
            
        except Exception as e:
            print(f"Error fetching catalog: {e}")
            self._load_fallback_catalog()
    
    def _parse_catalog_html(self, soup: BeautifulSoup):
        """Parse HTML to extract assessment information."""
        # This will depend on the actual HTML structure of the SHL catalog
        # For now, implementing a structure that can be filled with real data
        
        # Look for products in the catalog
        product_sections = soup.find_all(class_=["product", "assessment", "solution"])
        
        for section in product_sections:
            try:
                # Extract key information
                name_elem = section.find(class_=["product-name", "title", "heading"])
                url_elem = section.find("a")
                desc_elem = section.find(class_=["description", "product-desc"])
                
                if name_elem and url_elem:
                    name = name_elem.get_text(strip=True)
                    url = url_elem.get("href", "")
                    description = desc_elem.get_text(strip=True) if desc_elem else ""
                    
                    # Determine test type based on name/description
                    test_type = self._infer_test_type(name, description)
                    
                    # Make URL absolute if needed
                    if url and not url.startswith("http"):
                        url = "https://www.shl.com" + url if url.startswith("/") else url
                    
                    if name and url:
                        assessment_id = name.lower().replace(" ", "_").replace("(", "").replace(")", "")
                        self.assessments[assessment_id] = {
                            "name": name,
                            "url": url,
                            "description": description,
                            "test_type": test_type,
                            "id": assessment_id
                        }
                        self.assessment_by_name[name] = self.assessments[assessment_id]
            except Exception as e:
                print(f"Error parsing product section: {e}")
    
    def _infer_test_type(self, name: str, description: str) -> str:
        """Infer test type from name and description."""
        text = (name + " " + description).lower()
        
        # K = Knowledge/Technical
        if any(word in text for word in ["java", "javascript", "python", "coding", "technical", "knowledge", "skill"]):
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
        for name, url in SEED_ASSESSMENTS.items():
            assessment_id = name.lower().replace(" ", "_").replace("(", "").replace(")", "")
            description = f"SHL {name} assessment"
            
            self.assessments[assessment_id] = {
                "name": name,
                "url": url,
                "description": description,
                "test_type": self._infer_test_type(name, description),
                "id": assessment_id
            }
            self.assessment_by_name[name] = self.assessments[assessment_id]
        
        print(f"Loaded {len(self.assessments)} assessments from seed data")
    
    def _save_cache(self):
        """Save catalog to cache file."""
        try:
            cache_data = {
                "assessments": self.assessments,
                "by_name": self.assessment_by_name
            }
            with open(self.CACHE_FILE, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            print(f"Error saving cache: {e}")
    
    def get_all_assessments(self) -> List[Dict[str, Any]]:
        """Get all available assessments."""
        return list(self.assessments.values())
    
    def get_assessment_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific assessment by name."""
        return self.assessment_by_name.get(name)
    
    def validate_assessment(self, name: str) -> bool:
        """Validate that an assessment exists in the catalog."""
        return name in self.assessment_by_name
    
    def search_assessments(self, query: str, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Search for assessments based on query and filters."""
        query_lower = query.lower()
        results = []
        
        for assessment in self.assessments.values():
            # Check query match in name and description
            name_match = query_lower in assessment["name"].lower()
            desc_match = query_lower in assessment["description"].lower()
            
            if name_match or desc_match:
                # Apply filters if provided
                if filters:
                    if "test_type" in filters and assessment["test_type"] not in filters["test_type"]:
                        continue
                    if "seniority" in filters and "seniority" not in assessment:
                        continue
                
                results.append(assessment)
        
        return results
    
    def get_assessments_by_type(self, test_type: str) -> List[Dict[str, Any]]:
        """Get assessments by test type (K, P, V, N, G)."""
        return [a for a in self.assessments.values() if a["test_type"] == test_type]
