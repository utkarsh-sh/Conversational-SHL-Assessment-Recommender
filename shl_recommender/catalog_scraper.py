"""Enhanced catalog scraper with multiple strategies."""

import json
import re
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import httpx


class CatalogScraper:
    """Enhanced scraper for SHL catalog."""
    
    CATALOG_URL = "https://www.shl.com/solutions/products/productcatalog/"
    
    @staticmethod
    async def scrape_catalog() -> List[Dict[str, str]]:
        """Scrape the SHL product catalog."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    CatalogScraper.CATALOG_URL,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    }
                )
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                assessments = []
                
                # Try multiple parsing strategies
                assessments.extend(CatalogScraper._parse_product_cards(soup))
                assessments.extend(CatalogScraper._parse_product_links(soup))
                assessments.extend(CatalogScraper._parse_product_tables(soup))
                
                # Remove duplicates
                unique_assessments = {}
                for assessment in assessments:
                    key = assessment.get("name", "").lower()
                    if key and key not in unique_assessments:
                        unique_assessments[key] = assessment
                
                return list(unique_assessments.values())
        
        except Exception as e:
            print(f"Error scraping catalog: {e}")
            return []
    
    @staticmethod
    def _parse_product_cards(soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Parse product cards from catalog page."""
        assessments = []
        
        # Look for common card structures
        card_selectors = [
            {"class": ["product-card", "assessment-card"]},
            {"class": "card"},
            {"class": "product"}
        ]
        
        for selector in card_selectors:
            cards = soup.find_all(class_=selector.get("class", []))
            for card in cards:
                assessment = CatalogScraper._extract_from_card(card)
                if assessment:
                    assessments.append(assessment)
        
        return assessments
    
    @staticmethod
    def _parse_product_links(soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Parse product links from catalog page."""
        assessments = []
        
        # Find all links that might be products
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            text = link.get_text(strip=True)
            
            # Filter to product-related links
            if "/products/" in href and len(text) > 2:
                assessment = {
                    "name": text,
                    "url": href if href.startswith("http") else f"https://www.shl.com{href}",
                    "description": text
                }
                assessments.append(assessment)
        
        return assessments
    
    @staticmethod
    def _parse_product_tables(soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Parse products from table format."""
        assessments = []
        
        for table in soup.find_all("table"):
            rows = table.find_all("tr")
            for row in rows:
                cols = row.find_all(["td", "th"])
                if len(cols) >= 2:
                    name = cols[0].get_text(strip=True)
                    
                    # Look for link
                    link = cols[0].find("a")
                    url = link.get("href", "") if link else ""
                    
                    if name and url:
                        assessment = {
                            "name": name,
                            "url": url if url.startswith("http") else f"https://www.shl.com{url}",
                            "description": cols[1].get_text(strip=True) if len(cols) > 1 else name
                        }
                        assessments.append(assessment)
        
        return assessments
    
    @staticmethod
    def _extract_from_card(card) -> Optional[Dict[str, str]]:
        """Extract assessment info from a card element."""
        try:
            # Find name (in heading or title)
            name_elem = card.find(["h2", "h3", "h4", ".name", ".title"])
            if not name_elem:
                name_elem = card.find("a")
            
            if not name_elem:
                return None
            
            name = name_elem.get_text(strip=True)
            
            # Find link
            link = card.find("a", href=True)
            if not link:
                return None
            
            url = link.get("href", "")
            if not url.startswith("http"):
                url = f"https://www.shl.com{url}" if url.startswith("/") else url
            
            # Find description
            desc_elem = card.find(["p", ".description", ".desc"])
            description = desc_elem.get_text(strip=True) if desc_elem else name
            
            if name and url:
                return {
                    "name": name,
                    "url": url,
                    "description": description
                }
        except Exception as e:
            print(f"Error extracting from card: {e}")
        
        return None


# Common SHL assessments for fallback/seed data
SEED_ASSESSMENTS = {
    "Java 8 (New)": "https://www.shl.com/solutions/products/java-8-new/",
    "OPQ32r": "https://www.shl.com/solutions/products/opq32r/",
    "GSA": "https://www.shl.com/solutions/products/gsa/",
    "Verify General Ability": "https://www.shl.com/solutions/products/verify-general-ability/",
    "Verify Logical": "https://www.shl.com/solutions/products/verify-logical/",
    "Verify Mechanical": "https://www.shl.com/solutions/products/verify-mechanical/",
    "Verify Numerical": "https://www.shl.com/solutions/products/verify-numerical/",
    "Verify Verbal": "https://www.shl.com/solutions/products/verify-verbal/",
    "Verify Professional Interaction": "https://www.shl.com/solutions/products/verify-professional-interaction/",
    "Python": "https://www.shl.com/solutions/products/python/",
    "C++": "https://www.shl.com/solutions/products/cpp/",
    "JavaScript": "https://www.shl.com/solutions/products/javascript/",
}
