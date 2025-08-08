import sys
import random
import time
import json
import os
import requests
from bs4 import BeautifulSoup
import certifi
import urllib3
from duckduckgo_search import DDGS
from typing import List, Dict, Any, Optional
import logging
from dataclasses import dataclass
import backoff

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
CONFIG = {
    'request_timeout': 15,  # seconds
    'max_retries': 3,
    'min_delay': 2,  # Minimum delay between requests
    'max_delay': 5,  # Maximum delay between requests
    'search_results_per_query': 3,
    'user_agents': [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15"
    ]
}

province_dict = {
    "THÀNH PHỐ HÀ NỘI": 1,
    "THÀNH PHỐ HỒ CHÍ MINH": 2,
    "THÀNH PHỐ HẢI PHÒNG": 3,
    "THÀNH PHỐ ĐÀ NẴNG": 4,
    "TỈNH HÀ GIANG": 5,
    "TỈNH CAO BẰNG": 6,
    "TỈNH LAI CHÂU": 7,
    "TỈNH LÀO CAI": 8,
    "TỈNH TUYÊN QUANG": 9,
    "TỈNH LẠNG SƠN": 10,
    "TỈNH BẮC KẠN": 11,
    "TỈNH THÁI NGUYÊN": 12,
    "TỈNH YÊN BÁI": 13,
    "TỈNH SƠN LA": 14,
    "TỈNH PHÚ THỌ": 15,
    "TỈNH VĨNH PHÚC": 16,
    "TỈNH QUẢNG NINH": 17,
    "TỈNH BẮC GIANG": 18,
    "TỈNH BẮC NINH": 19,
    "TỈNH HẢI DƯƠNG": 21,
    "TỈNH HƯNG YÊN": 22,
    "TỈNH HÒA BÌNH": 23,
    "TỈNH HÀ NAM": 24,
    "TỈNH NAM ĐỊNH": 25,
    "TỈNH THÁI BÌNH": 26,
    "TỈNH NINH BÌNH": 27,
    "TỈNH THANH HÓA": 28,
    "TỈNH NGHỆ AN": 29,
    "TỈNH HÀ TĨNH": 30,
    "TỈNH QUẢNG BÌNH": 31,
    "TỈNH QUẢNG TRỊ": 32,
    "TỈNH THỪA THIÊN": 33,
    "TỈNH QUẢNG NAM": 34,
    "TỈNH QUẢNG NGÃI": 35,
    "TỈNH KON TUM": 36,
    "TỈNH BÌNH ĐỊNH": 37,
    "TỈNH GIA LAI": 38,
    "TỈNH PHÚ YÊN": 39,
    "TỈNH ĐẮK LẮK": 40,
    "TỈNH KHÁNH HÒA": 41,
    "TỈNH LÂM ĐỒNG": 42,
    "TỈNH BÌNH PHƯỚC": 43,
    "TỈNH BÌNH DƯƠNG": 44,
    "TỈNH NINH THUẬN": 45,
    "TỈNH TÂY NINH": 46,
    "TỈNH BÌNH THUẬN": 47,
    "TỈNH ĐỒNG NAI": 48,
    "TỈNH LONG AN": 49,
    "TỈNH ĐỒNG THÁP": 50,
    "TỈNH AN GIANG": 51,
    "TỈNH BÀ RỊA": 52,
    "TỈNH TIỀN GIANG": 53,
    "TỈNH KIÊN GIANG": 54,
    "THÀNH PHỐ CẦN THƠ": 55,
    "TỈNH BẾN TRE": 56,
    "TỈNH VĨNH LONG": 57,
    "TỈNH TRÀ VINH": 58,
    "TỈNH SÓC TRĂNG": 59,
    "TỈNH BẠC LIÊU": 60,
    "TỈNH CÀ MAU": 61,
    "TỈNH ĐIỆN BIÊN": 62,
    "TỈNH ĐĂK NÔNG": 63,
    "TỈNH HẬU GIANG": 64,
}
# category: travel (in general), food with popular keywords to search
category_dict = {
    "travel": ["du lịch không thể bỏ qua", "must visit"],
    "food": ["ăn uống ngon nổi tiếng", "favourite food"],
}

@dataclass
class SearchResult:
    title: str
    url: str
    content: str
    tag_content: str

class RateLimitError(Exception):
    """Custom exception for rate limiting"""
    pass

class WebCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.session.verify = certifi.where()
        self.session.headers.update(self._get_headers())
        self.ddgs = DDGS()

    def _get_headers(self) -> dict:
        """Get random headers for requests"""
        return {
            "User-Agent": random.choice(CONFIG['user_agents']),
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer": "https://www.google.com/",
        }

    @backoff.on_exception(
        backoff.expo,
        (requests.RequestException, RateLimitError),
        max_tries=CONFIG['max_retries'],
        max_time=300  # 5 minutes max retry time
    )
    def search_with_retry(self, query: str, max_results: int = 3) -> List[Dict[str, str]]:
        """Search with retry logic and rate limiting"""
        time.sleep(random.uniform(CONFIG['min_delay'], CONFIG['max_delay']))
        
        try:
            results = list(self.ddgs.text(query, max_results=max_results))
            if not results:
                logger.warning(f"No results found for query: {query}")
            return results
        except Exception as e:
            if "Ratelimit" in str(e):
                logger.warning("Rate limit hit, backing off...")
                raise RateLimitError("DuckDuckGo rate limit reached")
            logger.error(f"Search error for query {query}: {str(e)}")
            raise

    @backoff.on_exception(
        backoff.expo,
        requests.RequestException,
        max_tries=CONFIG['max_retries'],
        max_time=300
    )
    def fetch_page(self, url: str) -> str:
        """Fetch page content with retry logic"""
        time.sleep(random.uniform(CONFIG['min_delay'], CONFIG['max_delay']))
        
        try:
            response = self.session.get(
                url,
                timeout=CONFIG['request_timeout'],
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {str(e)}")
            raise

    def parse_page(self, html: str, url: str) -> SearchResult:
        """Parse the HTML content of a page"""
        try:
            soup = BeautifulSoup(html, "html.parser")
            title = soup.title.string.strip() if soup.title else url
            
            # Get main content (more robust content extraction)
            for unwanted in soup(["script", "style", "nav", "footer", "header"]):
                unwanted.decompose()
                
            # Extract text from important elements
            elements = []
            for tag in soup.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
                if tag.text.strip():
                    elements.append(f"[{tag.name.upper()}] {tag.get_text(strip=True)}")
            
            tag_content = "\n".join(elements)
            
            return SearchResult(
                title=title,
                url=url,
                content=" ".join(soup.stripped_strings),
                tag_content=tag_content
            )
        except Exception as e:
            logger.error(f"Error parsing {url}: {str(e)}")
            return SearchResult(
                title=url,
                url=url,
                content="",
                tag_content=""
            )

    def save_result(self, result: SearchResult, base_path: str, idx: int) -> Dict[str, str]:
        """Save search result to files"""
        os.makedirs(base_path, exist_ok=True)
        
        # Save as JSON
        json_path = os.path.join(base_path, f"{idx}.json").replace("\\", "/")
        # with open(json_path, "w", encoding="utf-8") as f:
        #     json.dump({
        #         "title": result.title,
        #         "url": result.url,
        #         "content": result.content,
        #         "tag_content": result.tag_content
        #     }, f, ensure_ascii=False, indent=2)
        
        # Save as TXT
        txt_path = os.path.join(base_path, f"{idx}.txt").replace("\\", "/")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"Title: {result.title}\n")
            f.write(f"URL: {result.url}\n\n")
            f.write("Content:\n")
            f.write(result.content)

        tag_txt_path = os.path.join(base_path, f"{idx}_tag.txt").replace("\\", "/")
        with open(tag_txt_path, "w", encoding="utf-8") as f:
            f.write(f"Title: {result.title}\n")
            f.write(f"URL: {result.url}\n\n")
            f.write("Content with tag:\n")
            f.write(result.tag_content)
        
        return {
            "json_path": json_path,
            "txt_path": txt_path,
            "tag_txt_path": tag_txt_path
        }

def main():
    # Your existing province_dict and category_dict
    # province_dict = {...}  # Your existing province dictionary
    # category_dict = {...}  # Your existing category dictionary

    

    crawler = WebCrawler()
    metadata = {"provinces": []}

    for province_name, province_id in province_dict.items():
    
        # expect no website visited more than once
        visited_urls = set()
        province_data = {
            "id": province_id,
            "name": province_name,
            "content": []
        }
        
        # Create base directory for province
        province_dir = f"data/{province_id}"
        os.makedirs(province_dir, exist_ok=True)
        
        for category_name, search_terms in category_dict.items():
            category_data = {
                "category": category_name,
                "items": []
            }
            
            category_dir = os.path.join(province_dir, category_name).replace("\\", "/")
            os.makedirs(category_dir, exist_ok=True)
            
            for search_term in search_terms:
                query = f"{search_term} {province_name}"
                logger.info(f"Searching for: {query}")
                
                try:
                    search_results = crawler.search_with_retry(
                        query, 
                        max_results=CONFIG['search_results_per_query']
                    )

                    # remove visited urls
                    search_results = [
                        result for result in search_results 
                        if result['href'] not in visited_urls
                    ]
                    
                    for idx, result in enumerate(search_results, 1):
                        try:
                            logger.info(f"Processing: {result['href']}")
                            html = crawler.fetch_page(result['href'])
                            parsed = crawler.parse_page(html, result['href'])
                            
                            # Save the result
                            file_paths = crawler.save_result(
                                parsed,
                                category_dir,
                                len(category_data["items"]) + 1
                            )
                            
                            # Update metadata
                            category_data["items"].append({
                                "idx": len(category_data["items"]) + 1,
                                "title": parsed.title,
                                "url": parsed.url,
                                **file_paths
                            })
                            
                        except Exception as e:
                            logger.error(f"Error processing {result.get('href', 'unknown')}: {str(e)}")
                            continue
                            
                except Exception as e:
                    logger.error(f"Error searching for '{query}': {str(e)}")
                    continue
            
            province_data["content"].append(category_data)
        
        metadata["provinces"].append(province_data)
    
    # Save metadata
    with open("data/metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    logger.info("Crawling completed successfully!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Crawling interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)