"""Unit tests for utils.extract."""

import unittest
from unittest.mock import MagicMock, patch

import requests
from bs4 import BeautifulSoup

from utils.extract import extract_product_data, fetching_content, scrape_product

# Sample HTML for a normal product card.
VALID_CARD_HTML = """
<div class="collection-card">
    <div style="position: relative;">
        <img src="x" class="collection-image" alt="T-shirt 2">
    </div>
    <div class="product-details">
        <h3 class="product-title">T-shirt 2</h3>
        <div class="price-container"><span class="price">$102.15</span></div>
        <p style="font-size: 14px; color: #777;">Rating: &#11088; 3.9 / 5</p>
        <p style="font-size: 14px; color: #777;">3 Colors</p>
        <p style="font-size: 14px; color: #777;">Size: M</p>
        <p style="font-size: 14px; color: #777;">Gender: Women</p>
    </div>
</div>
"""

# Sample HTML for a card with an unavailable price (different tag).
UNAVAILABLE_CARD_HTML = """
<div class="collection-card">
    <div class="product-details">
        <h3 class="product-title">Pants 46</h3>
        <p class="price">Price Unavailable</p>
        <p style="font-size: 14px; color: #777;">Rating: Not Rated</p>
        <p style="font-size: 14px; color: #777;">8 Colors</p>
        <p style="font-size: 14px; color: #777;">Size: S</p>
        <p style="font-size: 14px; color: #777;">Gender: Men</p>
    </div>
</div>
"""

# A full page with two cards plus surrounding markup.
PAGE_HTML = f"""
<html><body>
<div class="collection-grid" id="collectionList">
    {VALID_CARD_HTML}
    {UNAVAILABLE_CARD_HTML}
</div>
</body></html>
"""


class TestFetchingContent(unittest.TestCase):
    @patch("utils.extract.requests.Session")
    def test_fetching_content_success(self, mock_session_cls):
        mock_response = MagicMock()
        mock_response.content = b"<html>ok</html>"
        mock_response.raise_for_status.return_value = None
        mock_session_cls.return_value.get.return_value = mock_response

        result = fetching_content("https://example.com")
        self.assertEqual(result, b"<html>ok</html>")

    @patch("utils.extract.requests.Session")
    def test_fetching_content_failure(self, mock_session_cls):
        mock_session_cls.return_value.get.side_effect = (
            requests.exceptions.RequestException("boom")
        )
        result = fetching_content("https://example.com")
        self.assertIsNone(result)


class TestExtractProductData(unittest.TestCase):
    def _card(self, html):
        return BeautifulSoup(html, "html.parser").find("div", class_="collection-card")

    def test_extract_valid_card(self):
        product = extract_product_data(self._card(VALID_CARD_HTML))
        self.assertEqual(product["Title"], "T-shirt 2")
        self.assertEqual(product["Price"], "$102.15")
        self.assertIn("3.9", product["Rating"])
        self.assertEqual(product["Colors"], "3 Colors")
        self.assertEqual(product["Size"], "Size: M")
        self.assertEqual(product["Gender"], "Gender: Women")

    def test_extract_unavailable_price_card(self):
        product = extract_product_data(self._card(UNAVAILABLE_CARD_HTML))
        self.assertEqual(product["Title"], "Pants 46")
        self.assertEqual(product["Price"], "Price Unavailable")
        self.assertEqual(product["Rating"], "Not Rated")

    def test_extract_malformed_card_returns_none(self):
        bad = BeautifulSoup("<div class='collection-card'></div>", "html.parser").find("div")
        self.assertIsNone(extract_product_data(bad))


class TestScrapeProduct(unittest.TestCase):
    @patch("utils.extract.time.sleep", return_value=None)
    @patch("utils.extract.fetching_content")
    def test_scrape_collects_products_with_timestamp(self, mock_fetch, _mock_sleep):
        mock_fetch.return_value = PAGE_HTML.encode("utf-8")
        data = scrape_product("https://example.com/", start_page=1, end_page=2)
        # 2 cards per page * 2 pages = 4 records
        self.assertEqual(len(data), 4)
        self.assertIn("timestamp", data[0])
        self.assertEqual(data[0]["Title"], "T-shirt 2")

    @patch("utils.extract.time.sleep", return_value=None)
    @patch("utils.extract.fetching_content", return_value=None)
    def test_scrape_skips_failed_pages(self, _mock_fetch, _mock_sleep):
        data = scrape_product("https://example.com/", start_page=1, end_page=3)
        self.assertEqual(data, [])

    @patch("utils.extract.time.sleep", return_value=None)
    @patch("utils.extract.fetching_content", return_value=b"<not valid html")
    def test_scrape_handles_unparseable_content(self, _mock_fetch, _mock_sleep):
        # BeautifulSoup is lenient, so this simply yields no cards.
        data = scrape_product("https://example.com/", start_page=1, end_page=1)
        self.assertEqual(data, [])


if __name__ == "__main__":
    unittest.main()
