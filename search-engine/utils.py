from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://openrouter.ai/models?fmt=table&input_modalities=text&max_price=0&order=context-high-to-low")
    page.wait_for_selector("code.text-xs")
    codes = "\n".join([c.inner_text() for c in page.query_selector_all("code.text-xs")])
    # print(codes)
    browser.close()


codes = open("models.txt", "w", encoding="utf-8").write(codes)