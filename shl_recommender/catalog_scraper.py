"""Enhanced catalog scraper with multiple strategies."""

import json
import re
from typing import List, Dict, Optional

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

try:
    import httpx
except ImportError:
    httpx = None


class CatalogScraper:
    """Enhanced scraper for SHL catalog."""
    
    CATALOG_URL = "https://www.shl.com/solutions/products/product-catalog/"
    
    @staticmethod
    async def scrape_catalog() -> List[Dict[str, str]]:
        """Scrape the SHL product catalog."""
        if not BeautifulSoup or not httpx:
            print("Scraper dependencies missing; using seed catalog")
            return []
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                assessments = []
                for start in range(0, 1000, 12):
                    response = await client.get(
                        CatalogScraper.CATALOG_URL,
                        params={"start": start, "type": 1},
                        headers={
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                        }
                    )
                    response.raise_for_status()

                    soup = BeautifulSoup(response.content, 'html.parser')
                    page_assessments = []
                    page_assessments.extend(CatalogScraper._parse_product_tables(soup))
                    page_assessments.extend(CatalogScraper._parse_product_cards(soup))
                    page_assessments.extend(CatalogScraper._parse_product_links(soup))
                    if not page_assessments:
                        break

                    before = len(assessments)
                    assessments.extend(page_assessments)
                    unique_names = {item.get("name", "").lower() for item in assessments}
                    if len(unique_names) == before:
                        break
                
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
                    link = row.find("a", href=True)
                    url = link.get("href", "") if link else ""
                    name = link.get_text(strip=True) if link else cols[0].get_text(strip=True)
                    
                    if name and url:
                        cells_text = [col.get_text(" ", strip=True) for col in cols]
                        assessment = {
                            "name": name,
                            "url": url if url.startswith("http") else f"https://www.shl.com{url}",
                            "description": " | ".join(cells_text),
                            "test_type": cells_text[-1] if cells_text else ""
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
    "Java 8": "https://www.shl.com/solutions/products/java-8/",
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
    "SQL Server": "https://www.shl.com/solutions/products/sql-server/",
    "HTML/CSS": "https://www.shl.com/solutions/products/html-css/",
    "C#": "https://www.shl.com/solutions/products/c-sharp/",
    ".NET Framework": "https://www.shl.com/solutions/products/net-framework/",
    "Project Management": "https://www.shl.com/solutions/products/project-management/",
    "Sales Achievement Predictor": "https://www.shl.com/solutions/products/sales-achievement-predictor/",
    "Customer Service Assessment": "https://www.shl.com/solutions/products/customer-service-assessment/",
}
