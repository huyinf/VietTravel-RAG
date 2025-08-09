## **Notes on Crawling Dynamic Web Pages**

### 1. **The Core Problem**

When using simple HTTP libraries (`requests`, `urllib`), you only get the **initial HTML** sent by the server.
For modern JavaScript-driven sites (React, Vue, Angular, etc.), the content is **rendered client-side** *after* the initial page load.
Result:

* Static HTML contains only the “shell” (layout, design scripts, placeholders).
* Actual data (`<code>`, tables, text) is missing.

---

### 2. **Why This Happens**

* The browser downloads the HTML shell.
* JavaScript (bundled in `.js` files) fetches the real data via API calls and injects it into the DOM.
* Without a JS engine, the raw HTTP fetch never runs that JavaScript.

---

### 3. **Solutions**

#### **Option A – Direct API Access (Preferred)**

* Inspect **Network** tab in browser DevTools.
* Find the JSON/XHR request that delivers the data.
* Replicate that request in Python and parse the JSON.
* **Pros:** Fast, lightweight, no browser emulation.
* **Cons:** Requires the API to be open and discoverable.

#### **Option B – JavaScript Rendering**

* Use a headless browser (Playwright, Selenium, Pyppeteer).
* Let the page fully render before scraping.
* Example (Playwright, Python):

  ```python
  from playwright.sync_api import sync_playwright

  with sync_playwright() as p:
      browser = p.chromium.launch(headless=True)
      page = browser.new_page()
      page.goto("https://example.com")
      page.wait_for_selector("css=selector")
      elements = page.query_selector_all("css=selector")
      for el in elements:
          print(el.inner_text())
      browser.close()
  ```
* **Pros:** Works for any JS-rendered page.
* **Cons:** Slower, heavier resource usage.

---

### 4. **Best Practice in Experiments**

* **Check the page source** vs **Inspect element**: if content is in “Inspect” but missing from “View Source,” it’s JS-generated.
* Always look for an API endpoint first; use headless browsers only when API access isn’t possible.
* Keep both scraping and API logic in your toolbox for flexibility.

---

### 5. **Key Takeaway**

> “Static crawlers see the frame, not the picture.
> JavaScript renders the picture after the fact.”
