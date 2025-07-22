from playwright.sync_api import sync_playwright
import pandas as pd
import re

flipkartUrl = "https://www.flipkart.com"

def clean_price(price_str):
    """Remove non-numeric characters from price string."""
    return re.sub(r'[^\d.]', '', price_str) if price_str else "N/A"

def parse_rating(card):
    """Extract stars, ratings count, and reviews count from card."""
    # Stars are often in a separate div with class like '_3LWZlK'
    star_element = card.query_selector('div.XQDdHH')
    stars = star_element.inner_text().strip() if star_element else "N/A"

    # Ratings & reviews are in a sibling element
    rating_info_element = card.query_selector('span.Wphh3N')
    rating_info_text = rating_info_element.inner_text().strip() if rating_info_element else ""

    ratings_match = re.search(r'([\d,]+)\s+Ratings', rating_info_text)
    reviews_match = re.search(r'([\d,]+)\s+Reviews', rating_info_text)

    ratings = ratings_match.group(1).replace(',', '') if ratings_match else "N/A"
    reviews = reviews_match.group(1).replace(',', '') if reviews_match else "N/A"

    return stars, ratings, reviews

def scrapeFlipkart():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(flipkartUrl)

        page.wait_for_timeout(4000)
        page.screenshot(path='flipkart.png', full_page=True)

        # Search for laptops
        searchInput = page.query_selector('input.Pke_EE')
        searchInput.fill('laptop')
        page.wait_for_timeout(1000)
        searchBt = page.query_selector('button._2iLD__')
        searchBt.click()

        page.wait_for_load_state('domcontentloaded')
        page.wait_for_timeout(4000)
        page.screenshot(path='laptop_flipkart.png', full_page=True)

        # Scroll to load more products
        for _ in range(5):
            page.mouse.wheel(0, 3000)
            page.wait_for_timeout(2000)

        products = []
        allCards = page.query_selector_all('div._75nlfW')

        for card in allCards:
            title = card.query_selector('div.KzDlHZ')
            spec = card.query_selector('ul.G4BRas')

            price_container = card.query_selector('div.cN1yYO')
            original_price_text = price_container.query_selector('div.yRaY8j.ZYYwLA').inner_text() if price_container else None
            discounted_price_text = price_container.query_selector('div.Nx9bqj._4b5DiR').inner_text() if price_container else None
            discount_percent = price_container.query_selector('div.UkUFwK span')

            image_element = card.query_selector('img')
            image_url = image_element.get_attribute('src') if image_element else "N/A"

            # Parse rating details
            stars, ratings_count, reviews_count = parse_rating(card)

            products.append({
                'Title': title.inner_text().strip() if title else "N/A",
                'Stars': stars,
                'Ratings Count': ratings_count,
                'Reviews Count': reviews_count,
                'Specifications': spec.inner_text().strip() if spec else "N/A",
                'Original Price': clean_price(original_price_text),
                'Discounted Price': clean_price(discounted_price_text),
                'Discount Percent': discount_percent.inner_text().strip() if discount_percent else "N/A",
                'Image URL': image_url
            })

        # Save to CSV
        df = pd.DataFrame(products)
        df.to_csv('flipkart_data_laptop.csv', index=False)
        print(f"✅ Saved {len(products)} laptop entries to flipkart_data_laptop.csv")

scrapeFlipkart()