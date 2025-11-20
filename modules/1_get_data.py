"""Product parser script using Playwright to extract product details from brain.com.ua"""



import load_django
import os
from parser_app.models import Product
from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeoutError
import logging
import time
import random

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def simulate_user() -> None:
    """Simulate user behavior with a random delay."""
    time.sleep(random.uniform(1, 3))


def safe_find_by_xpath(page: Page, xpath: str, timeout: int = 10000) -> str | None:
    """
    Safely find an element by XPath and return its text content.

    Args:
        page: Playwright Page instance.
        xpath: The XPath of the element to find.
        timeout: Maximum time to wait for the element (in milliseconds).

    Returns:
        The text content of the element, or None if not found.
    """

    try:
        element = page.locator(f"xpath={xpath}").first
        element.wait_for(state="attached", timeout=timeout)

        text = element.inner_text(timeout=timeout)
        if text:
            return text.strip()

        return None

    except (PlaywrightTimeoutError, Exception):
        return None


def get_by_label(page: Page, label_text: str, timeout: int = 10000) -> str | None:
    """
    Get the text of a product detail by its label.

    Args:
        page: Playwright Page instance.
        label_text: The label text to search for.
        timeout: Maximum time to wait for the element (in milliseconds).

    Returns:
        The text content of the detail, or None if not found.
    """
    try:
        xpath = f"//span[contains(text(), \"{label_text}\")]/following-sibling::span[1]"
        element = page.locator(f"xpath={xpath}").first
        element.wait_for(state="visible", timeout=timeout)

        text = element.inner_text(timeout=timeout)
        if text:
            return text.strip()

        return None
    except (PlaywrightTimeoutError, Exception):
        return None


def extract_basic_info(page: Page) -> dict:
    """
    Extract basic product information: title, prices, product code, review count.

    Args:
        page: Playwright Page instance.

    Returns:
        Dictionary with basic product information.
    """

    logging.info("Extracting basic product information")

    regular_price = safe_find_by_xpath(page, "//div[@class='price-wrapper']//span")
    discount_price = safe_find_by_xpath(page, "//span[@class='red-price']")

    basic_info = {
        'title': safe_find_by_xpath(page, "//h1[@class='main-title']"),
        'regular_price': regular_price.replace(' ', '') if regular_price else None,
        'discount_price': discount_price.replace(' ', '') if discount_price else None,
        'product_code': safe_find_by_xpath(page, "(//span[@class='br-pr-code-val'])[1]"),
        'review_count': safe_find_by_xpath(page, "(//a[contains(@class, 'reviews-count')]//span)[1]"),
    }
    logging.info("Basic info extracted")
    return basic_info


def extract_product_details(page: Page) -> dict:
    """
    Extract specific product details: vendor, color, memory volume, series, screen diagonal, screen resolution.

    Args:
        page: Playwright Page instance.

    Returns:
        Dictionary with product details.
    """

    logging.info("Extracting product details")

    all_specs_button = page.locator("xpath=//div[@id='br-pr-7']//button[@class='br-prs-button']")
    all_specs_button.scroll_into_view_if_needed()

    simulate_user()

    all_specs_button.click()

    details = {
        'vendor': get_by_label(page, 'Виробник'),
        'color': get_by_label(page, 'Колір'),
        'memory_volume': get_by_label(page, 'Вбудована пам\'ять'),
        'series': get_by_label(page, 'Модель'),
        'screen_diagonal': get_by_label(page, 'Діагональ екрану'),
        'screen_resolution': get_by_label(page, 'Роздільна здатність екрану')
    }

    logging.info(f"Product details extracted")

    return details


def extract_photos(page: Page) -> list:
    """
    Extract product photo URLs.

    Args:
        page: Playwright Page instance.

    Returns:
        List of photo URLs.
    """

    logging.info("Extracting product photos")
    photos = []

    try:
        img_elements = page.locator("xpath=//img[@class='br-main-img']").all()
        for img in img_elements:
            img_url = img.get_attribute('src')
            if img_url:
                photos.append(img_url)
    except Exception as e:
        logging.warning(f"No photos found: {e}")

    logging.info(f"Extracted {len(photos)} photos")
    return photos


def extract_specifications(page: Page) -> dict:
    """
    Extract product specifications.

    Args:
        page: Playwright Page instance.

    Returns:
        Dictionary with product specifications.
    """

    logging.info("Extracting product specifications")
    specifications = dict()

    try:
        categories = page.locator("xpath=//div[@class='br-pr-chr-item']").all()
        for category in categories:
            items = category.locator("xpath=.//div/div").all()
            for item in items:
                spans = item.locator("xpath=./span").all()
                if len(spans) == 2:
                    label = spans[0].inner_text().strip()
                    value = spans[1].inner_text().strip()

                    cleaned_value = ', '.join(x.strip() for x in value.replace('\xa0', ' ').split(',') if x.strip())

                    specifications[label] = cleaned_value
                elif len(spans) == 1:
                    label = spans[0].inner_text().strip()
                    specifications[label] = None
    except Exception as e:
        logging.warning(f"No specifications found: {e}")

    logging.info(f"Extracted {len(specifications)} specifications")
    return specifications


def search_product(page: Page, search_query: str, url: str, timeout: int = 10000) -> str | None:
    """
    Search for a product and return the URL of the first search result.

    Args:
        page: Playwright Page instance.
        search_query: The product search query.
        url: The URL of the website to search on.
        timeout: Maximum time to wait for elements (in milliseconds).

    Returns:
        URL of the first search result, or None if not found.
    """

    logging.info(f"Opening page: {url}")
    page.goto(url)

    logging.info(f"Entering search query: {search_query}")

    header_bottom_div = "//div[@class='header-bottom']"

    search_input = page.locator(f"xpath={header_bottom_div}//input[@class='quick-search-input']")
    search_input.wait_for(state="attached", timeout=timeout)
    search_input.fill(search_query)

    logging.info("Clicking search button")
    search_button = page.locator(f"xpath=//input[@type='submit' and @class='qsr-submit']")
    search_button.wait_for(state="visible", timeout=timeout)
    search_button.click()

    simulate_user()

    logging.info("Clicking on the first search result")
    first_result = page.locator("xpath=(//div[@class='row br-row br-row-main br-row-main-s']//div[@class='br-pp-desc br-pp-ipd-hidden ']//a)[1]")
    first_result.wait_for(state="visible", timeout=timeout)
    product_url = first_result.get_attribute('href')
    logging.info(f"First result URL: {product_url}")

    simulate_user()

    first_result.click()

    return product_url


def parse_product_page(page: Page) -> dict:
    """
    Parse the product page to extract all relevant information.

    Args:
        page: Playwright Page instance.

    Returns:
        Dictionary with all extracted product information.
    """

    logging.info("Collecting product information")

    product = {}
    product.update(extract_basic_info(page))
    product.update(extract_product_details(page))
    product['photos'] = extract_photos(page)
    product['specifications'] = extract_specifications(page)

    logging.info("Product parsing completed successfully")
    return product


def save_product(link: str, data: dict) -> None:
    """
    Save the extracted product data to the database.

    Args:
        link: The product link.
        data: Dictionary with product data.
    """

    logging.info(f"Saving product to database: {data.get('title', 'Unknown')}")
    product, created = Product.objects.update_or_create(
        link=link,
        defaults={
            'title': data['title'],
            'regular_price': data['regular_price'],
            'discount_price': data['discount_price'],
            'product_code': data['product_code'],
            'vendor': data['vendor'],
            'color': data['color'],
            'memory_volume': data['memory_volume'],
            'review_count': data['review_count'],
            'series': data['series'],
            'screen_diagonal': data['screen_diagonal'],
            'screen_resolution': data['screen_resolution'],
            'photos': data['photos'],
            'specifications': data['specifications'],
        }
    )

    if created:
        logging.info(f"Product created in database with ID: {product.id}")
    else:
        logging.info(f"Product updated in database with ID: {product.id}")


def main() -> None:
    """Main function to run the product parser script."""

    logging.info("SCRIPT STARTED: Product parser with Playwright")

    search_query = "Apple iPhone 15 128GB Black"
    url = "https://brain.com.ua/"

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        try:
            product_url = search_product(page, search_query, url)

            if product_url:
                data = parse_product_page(page)
                save_product(product_url, data)

                logging.info("SCRIPT COMPLETED SUCCESSFULLY")
            else:
                logging.error("No product URL found from search results")

        except Exception as e:
            logging.error(f"Script failed with error: {e}")
            logging.error("SCRIPT TERMINATED WITH ERRORS")
            raise
        finally:
            context.close()
            browser.close()
            logging.info("Browser closed")


if __name__ == '__main__':
    main()
