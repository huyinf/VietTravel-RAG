# --- Parse text only --
import random
import time
import sys
import os
import requests
from bs4 import BeautifulSoup
import json
import certifi
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ─── CONFIG ────────────────────────────────────────────────────────────────
seed = 81
random.seed(seed)
TIMEOUT = 10  # seconds for HTTP requests
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
# ───────────────────────────────────────────────────────────────────────────

from duckduckgo_search import DDGS


def search(query, max_results=5):
    time.sleep(random.randint(1, 5))
    with DDGS() as ddgs:
        return [r for r in ddgs.text(query, max_results=max_results)]


# 1. Use realistic headers
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/114.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    # "Referer": "https://vinpearl.com/",
}


def fetch_page(url: str, i: int) -> str:
    """Download the raw HTML of the page."""
    # (Optional) Use a session to persist cookies
    session = requests.Session()
    resp = session.get(url, headers=HEADERS, timeout=10, verify=certifi.where())
    # resp = requests.get(url, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.text


def parse_page(html: str, url: str, i: int) -> dict:
    """Parse title and all visible text from the HTML."""
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string.strip() if soup.title else url
    # get all text, collapse whitespace
    content = " ".join(soup.stripped_strings)
    extracted_content = "\n".join(
        [
            f"[{tag.name.upper()}] {tag.get_text(strip=True)}"
            for tag in soup.find_all(["h1", "h2", "h3", "p"])
        ]
    )
    return {
        "url": url,
        "title": title,
        "content": content,
        "extracted_content": extracted_content,
    }


def main():
    # if len(sys.argv) != 2:
    #     print("Usage: python fetch_and_index.py <URL>")
    #     sys.exit(1)

    # record all metadata
    metadata = {
        "provinces": [  # List to store multiple provinces
            {
                "id": 1,  # Province ID as a value
                "name": "Province Name",  # Province name
                "content": [  # List to store multiple categories
                    {
                        "category": "Category Name",  # Category name
                        "items": [  # List to store multiple content items
                            {
                                "idx": 1,  # Content ID
                                "title": "Content Title",
                                "url": "https://example.com",
                                "json_path": "path/to/file.json",  # Renamed for clarity
                                "txt_path": "path/to/file.txt",  # Renamed for clarity
                                "_txt_path": "path/to/_file.txt",  # Renamed for clarity
                                "body_html_path": "path/to/body.html",  # Renamed for consistency
                            }
                            # Add more content items here
                        ],
                    }
                    # Add more categories here
                ],
            }
            # Add more provinces here
        ]
    }

    for i, (k, v) in enumerate(province_dict.items()):
        metadata["provinces"].append({"id": v, "name": k, "content": []})
        # make dir to store data
        os.makedirs(f"data/{v}", exist_ok=True)
        for j, (cat_k, cat_v) in enumerate(category_dict.items()):
            os.makedirs(f"data/{v}/{cat_k}", exist_ok=True)
            metadata["provinces"][i]["content"].append({"category": cat_k, "items": []})
            # general index for all files
            idx = 1
            for cat in cat_v:
                query = f"{cat} {k}"
                results = search(query, 3)
                urls = [r["href"] for r in results]

                for url in urls:
                    try:
                        html = fetch_page(url, idx)
                        doc = parse_page(html, url, idx)
                        with open(
                            f"data/{v}/{cat_k}/{idx}.json", "w", encoding="utf-8"
                        ) as f:
                            json.dump(doc, f, ensure_ascii=False, indent=2)
                        print(f"Saved → {idx}.json")
                        with open(
                            f"data/{v}/{cat_k}/{idx}.txt", "w", encoding="utf-8"
                        ) as f:
                            f.write(doc["extracted_content"])
                        print(f"Saved → {idx}.txt")
                        with open(
                            f"data/{v}/{cat_k}/_{idx}.txt", "w", encoding="utf-8"
                        ) as f:
                            f.write(doc["content"])
                        print(f"Saved → _{idx}.txt")
                        # print(metadata)
                        metadata["provinces"][i]["content"][j]["items"].append(
                            {
                                "idx": idx,
                                "title": doc["title"],
                                "url": doc["url"],
                                "json": f"data/{v}/{cat_k}/{idx}.json",
                                "txt": f"data/{v}/{cat_k}/{idx}.txt",
                                "_txt": f"data/{v}/{cat_k}/_{idx}.txt",
                                "body-html": f"data/{v}/{cat_k}/{idx}.html",
                            }
                        )
                        idx += 1
                    except Exception as e:
                        print(f"[ERROR] {e}")

    # export this metadata at the top level
    with open("data/metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()

# # --- For dynamic JavaScript-rendered content ---

# from selenium import webdriver

# options = webdriver.ChromeOptions()
# options.add_argument("--headless")  # Run in background
# driver = webdriver.Chrome(options=options)
# driver.get("https://vnexpress.net/cam-nang-du-lich-nha-trang-tu-a-den-z-4127199.html")
# # Extract dynamic content
# print(driver.page_source)
# # write content to file
# with open("du-lich.html", "w", encoding="utf-8") as f:
#     f.write(driver.page_source)
# driver.quit()
