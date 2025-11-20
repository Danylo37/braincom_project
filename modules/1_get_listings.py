"""Product parser script using Selenium to extract product details from brain.com.ua"""

import load_django
from parser_app.models import Product
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging
import time
import random

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def simulate_user() -> None:
    """Simulate user behavior with a random delay."""
    time.sleep(random.uniform(1, 3))


def safe_find_by_xpath(driver, xpath: str, timeout: int = 10) -> str | None:
    """
    Safely find an element by XPath and return its text content.

    Args:
        driver: Selenium WebDriver instance.
        xpath: The XPath of the element to find.
        timeout: Maximum time to wait for the element.

    Returns:
        The text content of the element, or None if not found.
    """

    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )

        text = element.text.strip()
        if text:
            return text

        text_js = driver.execute_script("return arguments[0].innerText;", element)
        if text_js:
            return text_js.strip()

        return None

    except (NoSuchElementException, TimeoutException):
        return None


def get_by_label(driver: webdriver.Chrome, label_text: str, timeout: int = 10) -> str | None:
    """
    Get the text of a product detail by its label.

    Args:
        driver: Selenium WebDriver instance.
        label_text: The label text to search for.
        timeout: Maximum time to wait for the element.

    Returns:
        The text content of the detail, or None if not found.
    """
    try:
        xpath = f"//span[contains(text(), \"{label_text}\")]/following-sibling::span[1]"

        element = WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((By.XPATH, xpath))
        )

        text = element.text.strip()
        if text:
            return text

        text_js = driver.execute_script("return arguments[0].innerText;", element)
        if text_js:
            return text_js.strip()

        return None
    except (NoSuchElementException, TimeoutException):
        return None


def extract_basic_info(driver: webdriver.Chrome) -> dict:
    """
    Extract basic product information: title, prices, product code, review count.

    Args:
        driver: Selenium WebDriver instance.

    Returns:
        Dictionary with basic product information.
    """

    logging.info("Extracting basic product information")

    regular_price = safe_find_by_xpath(driver, "//div[@class='price-wrapper']//span")
    discount_price = safe_find_by_xpath(driver, "//span[@class='red-price']")

    basic_info = {
        'title': safe_find_by_xpath(driver, "//h1[@class='main-title']"),
        'regular_price': regular_price.replace(' ', '') if regular_price else None,
        'discount_price': discount_price.replace(' ', '') if discount_price else None,
        'product_code': safe_find_by_xpath(driver, "(//span[@class='br-pr-code-val'])[1]"),
        'review_count': safe_find_by_xpath(driver, "(//a[contains(@class, 'reviews-count')]//span)[1]"),
    }
    logging.info("Basic info extracted")
    return basic_info


def extract_product_details(driver: webdriver.Chrome) -> dict:
    """
    Extract specific product details: vendor, color, memory volume, series, screen diagonal, screen resolution.

    Args:
        driver: Selenium WebDriver instance.

    Returns:
        Dictionary with product details.
    """

    logging.info("Extracting product details")

    all_specs = driver.find_element(By.XPATH, "//div[@id='br-pr-7']//button[@class='br-prs-button']")

    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", all_specs)

    simulate_user()

    all_specs.click()

    details = {
        'vendor': get_by_label(driver, 'Виробник'),
        'color': get_by_label(driver, 'Колір'),
        'memory_volume': get_by_label(driver, 'Вбудована пам\'ять'),
        'series': get_by_label(driver, 'Модель'),
        'screen_diagonal': get_by_label(driver, 'Діагональ екрану'),
        'screen_resolution': get_by_label(driver, 'Роздільна здатність екрану')
    }

    logging.info(f"Product details extracted")

    return details


def extract_photos(driver: webdriver.Chrome) -> list:
    """
    Extract product photo URLs.

    Args:
        driver: Selenium WebDriver instance.

    Returns:
        List of photo URLs.
    """

    logging.info("Extracting product photos")
    photos = []

    try:
        img_elements = driver.find_elements(By.XPATH, "//img[@class='br-main-img']")
        for img in img_elements:
            img_url = img.get_attribute('src')
            if img_url:
                photos.append(img_url)
    except (NoSuchElementException, TimeoutException):
        logging.warning("No photos found")

    logging.info(f"Extracted {len(photos)} photos")
    return photos


def extract_specifications(driver: webdriver.Chrome) -> dict:
    """
    Extract product specifications.

    Args:
        driver: Selenium WebDriver instance.

    Returns:
        Dictionary with product specifications.
    """

    logging.info("Extracting product specifications")
    specifications = dict()

    try:
        categories = driver.find_elements(By.XPATH, "//div[@class='br-pr-chr-item']")
        for category in categories:
            items = category.find_elements(By.XPATH, ".//div/div")
            for item in items:
                spans = item.find_elements(By.XPATH, "./span")
                if len(spans) == 2:
                    label = spans[0].text.strip()
                    value = spans[1].text.strip()

                    cleaned_value = ', '.join(x.strip() for x in value.replace('\xa0', ' ').split(',') if x.strip())

                    specifications[label] = cleaned_value
                elif len(spans) == 1:
                    label = spans[0].text.strip()
                    specifications[label] = None
    except (NoSuchElementException, TimeoutException):
        logging.warning("No specifications found")

    logging.info(f"Extracted {len(specifications)} specifications")
    return specifications


def search_product(driver: webdriver.Chrome, search_query: str, url: str, timeout: int = 10) -> str | None:
    """
    Search for a product and return the URL of the first search result.

    Args:
        driver: Selenium WebDriver instance.
        search_query: The product search query.
        url: The URL of the website to search on.
        timeout: Maximum time to wait for elements.

    Returns:
        URL of the first search result, or None if not found.
    """

    logging.info(f"Opening page: {url}")
    driver.get(url)

    logging.info(f"Entering search query: {search_query}")

    header_bottom_div = "//div[@class='header-bottom']"

    search_input = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.XPATH, f"{header_bottom_div}//input[@class='quick-search-input']"))
    )
    search_input.clear()
    search_input.send_keys(search_query)

    simulate_user()

    logging.info("Clicking search button")
    search_button = driver.find_element(By.XPATH, f"{header_bottom_div}//input[@type='submit' and contains(@class, 'search-button-first-form')]")
    search_button.submit()

    simulate_user()

    logging.info("Clicking on the first search result")
    first_result = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.XPATH, "//div[@class='br-pp-desc br-pp-ipd-hidden ']//a"))
    )
    product_url = first_result.get_attribute('href')
    logging.info(f"First result URL: {product_url}")

    simulate_user()

    first_result.click()

    return product_url


def parse_product_page(driver: webdriver.Chrome) -> dict:
    """
    Parse the product page to extract all relevant information.

    Args:
        driver: Selenium WebDriver instance.

    Returns:
        Dictionary with all extracted product information.
    """

    logging.info("Collecting product information")

    product = {}
    product.update(extract_basic_info(driver))
    product.update(extract_product_details(driver))
    product['photos'] = extract_photos(driver)
    product['specifications'] = extract_specifications(driver)

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

    logging.info("SCRIPT STARTED: Product parser with Selenium")

    driver = webdriver.Chrome()
    driver.maximize_window()

    search_query = "Apple iPhone 15 128GB Black"
    url = "https://brain.com.ua/"

    try:
        product_url = search_product(driver, search_query, url)

        if product_url:
            data = parse_product_page(driver)
            save_product(product_url, data)

            logging.info("SCRIPT COMPLETED SUCCESSFULLY")
        else:
            logging.error("No product URL found from search results")

    except Exception as e:
        logging.error(f"Script failed with error: {e}")
        logging.error("SCRIPT TERMINATED WITH ERRORS")
        raise
    finally:
        driver.quit()
        logging.info("Browser closed")


if __name__ == '__main__':
    main()
