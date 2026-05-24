"""Extract stage: scrape fashion product data from fashion-studio.dicoding.dev."""

import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


def fetching_content(url):
    """Fetch the raw HTML content of a URL.

    Returns the response content (bytes) on success, or None on failure.
    """
    session = requests.Session()
    try:
        response = session.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as error:
        print(f"Error fetching {url}: {error}")
        return None


def extract_product_data(card):
    """Parse a single ``div.collection-card`` element into a dict.

    Returns a dict with Title, Price, Rating, Colors, Size, Gender,
    or None when the card cannot be parsed.
    """
    try:
        title = card.find("h3", class_="product-title").text.strip()

        # Price lives in <div class="price-container"><span class="price">$xxx</span></div>
        # but falls back to <p class="price">Price Unavailable</p> when missing.
        price_container = card.find("div", class_="price-container")
        if price_container:
            price = price_container.find("span", class_="price").text.strip()
        else:
            price_tag = card.find("p", class_="price")
            price = price_tag.text.strip() if price_tag else None

        product = {
            "Title": title,
            "Price": price,
            "Rating": None,
            "Colors": None,
            "Size": None,
            "Gender": None,
        }

        # The remaining details are <p> tags; classify each by its text prefix.
        for paragraph in card.find_all("p", style=True):
            text = paragraph.text.strip()
            if text.startswith("Rating:"):
                product["Rating"] = text.replace("Rating:", "").strip()
            elif "Colors" in text:
                product["Colors"] = text
            elif text.startswith("Size:"):
                product["Size"] = text
            elif text.startswith("Gender:"):
                product["Gender"] = text

        return product
    except (AttributeError, TypeError) as error:
        print(f"Error parsing a product card: {error}")
        return None


def scrape_product(base_url, start_page=1, end_page=50, delay=0.2):
    """Scrape products from page ``start_page`` to ``end_page``.

    Page 1 is the base URL; subsequent pages are ``<base_url>page{n}``.
    Each product is tagged with the extraction ``timestamp``.
    Returns a list of product dicts (possibly empty).
    """
    data = []
    for page_number in range(start_page, end_page + 1):
        if page_number == 1:
            url = base_url
        else:
            url = f"{base_url.rstrip('/')}/page{page_number}"

        print(f"Scraping page {page_number}: {url}")
        content = fetching_content(url)
        if content is None:
            continue

        try:
            soup = BeautifulSoup(content, "html.parser")
            cards = soup.find_all("div", class_="collection-card")
            for card in cards:
                product = extract_product_data(card)
                if product:
                    product["timestamp"] = datetime.now().isoformat()
                    data.append(product)
        except Exception as error:  # noqa: BLE001 - keep scraping resilient
            print(f"Error processing page {page_number}: {error}")
            continue

        time.sleep(delay)

    return data
