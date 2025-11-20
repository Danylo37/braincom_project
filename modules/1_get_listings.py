"""Script to parse product details from a given URL and store them in the database using Django ORM."""

import load_django
from parser_app.models import Product
import requests
from bs4 import BeautifulSoup
from collections.abc import Callable
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def safe(find_func: Callable) -> str | None:
    """Safely execute a function to find an element and return its text, or None if not found.

    Args:
        find_func: A callable that returns a BeautifulSoup element or raises AttributeError.

    Returns:
        The stripped text of the element, or None if not found.
    """

    try:
        return find_func().text.strip()
    except AttributeError:
        return None


def get_by_label(soup: BeautifulSoup, label_text: str) -> str | None:
    """Get the text of the span following the span with the given label text.

    Args:
        soup: BeautifulSoup object containing parsed HTML.
        label_text: The text to search for in span elements.

    Returns:
        The text of the next span element, or None if not found.
    """

    label = soup.find('span', string=label_text)
    if label:
        next_span = label.find_next('span')
        return next_span.text.strip() if next_span else None
    return None


def fetch_page(url: str) -> BeautifulSoup:
    """Fetch page content and return BeautifulSoup object.

    Args:
        url: The URL of the page to fetch.

    Returns:
        BeautifulSoup object containing parsed HTML.
    """

    logging.info(f"Fetching page from URL: {url}")
    r = requests.get(url)
    r.raise_for_status()
    logging.info("Page fetched successfully")
    return BeautifulSoup(r.text, 'html.parser')


def extract_basic_info(soup: BeautifulSoup) -> dict:
    """Extract basic product information: title, prices, product code, review count.

    Args:
        soup: BeautifulSoup object containing parsed HTML.

    Returns:
        Dictionary with basic product information.
    """

    logging.info("Extracting basic product information")
    regular_price = safe(lambda: soup.find('div', class_='price-wrapper').find('span'))
    discount_price = safe(lambda: soup.find('span', class_='red-price'))

    basic_info = {
        'title': safe(lambda: soup.find('h1', class_='main-title')),
        'regular_price': regular_price.replace(' ', '') if regular_price else None,
        'discount_price': discount_price.replace(' ', '') if discount_price else None,
        'product_code': safe(lambda: soup.find('span', class_='br-pr-code-val')),
        'review_count': safe(lambda: soup.find('a', class_='scroll-to-element reviews-count').find('span')),
    }
    logging.info("Basic info extracted")
    return basic_info


def extract_product_details(soup: BeautifulSoup) -> dict:
    """Extract product details: vendor, color, memory, series, screen info.

    Args:
        soup: BeautifulSoup object containing parsed HTML.

    Returns:
        Dictionary with product details.
    """

    logging.info("Extracting product details")
    details = {'vendor': get_by_label(soup, 'Виробник'),
               'color': get_by_label(soup, 'Колір'),
               'memory_volume': get_by_label(soup, 'Вбудована пам\'ять'),
               'series': get_by_label(soup, 'Модель'),
               'screen_diagonal': get_by_label(soup, 'Діагональ екрану'),
               'screen_resolution': get_by_label(soup, 'Роздільна здатність екрану')}

    logging.info("Product details extracted")
    return details


def extract_photos(soup: BeautifulSoup) -> list:
    """Extract product photos URLs.

    Args:
        soup: BeautifulSoup object containing parsed HTML.

    Returns:
        List of photo URLs.
    """

    logging.info("Extracting product photos")
    photos = []

    img_tags = soup.find_all('img', class_='br-main-img')
    for img in img_tags:
        img_url = img.get('src')
        if img_url:
            photos.append(img_url)

    logging.info(f"Extracted {len(photos)} photos")
    return photos


def extract_specifications(soup: BeautifulSoup) -> dict:
    """Extract detailed product specifications.

    Args:
        soup: BeautifulSoup object containing parsed HTML.

    Returns:
        Dictionary with product specifications.
    """

    logging.info("Extracting product specifications")
    specifications = {}

    categories = soup.find_all('div', class_='br-pr-chr-item')
    for category in categories:
        items = category.find('div').find_all('div', recursive=False)
        for item in items:
            spans = item.find_all('span', recursive=False)
            if len(spans) == 2:
                label = spans[0].text.strip()
                value = spans[1].text.strip()

                cleaned_value = ', '.join(x.strip() for x in value.replace('\xa0', ' ').split(',') if x.strip())

                specifications[label] = cleaned_value
            elif len(spans) == 1:
                label = spans[0].text.strip()
                specifications[label] = None

    logging.info(f"Extracted {len(specifications)} specifications")
    return specifications


def parse(url: str) -> dict:
    """Parse product details from the given URL.

    Args:
        url: The URL of the product page to parse.

    Returns:
        Dictionary containing all parsed product information.
    """

    logging.info("Starting product parsing")
    soup = fetch_page(url)

    product = {}
    product.update(extract_basic_info(soup))
    product.update(extract_product_details(soup))
    product['photos'] = extract_photos(soup)
    product['specifications'] = extract_specifications(soup)

    logging.info("Product parsing completed successfully")
    return product


def save_product(link: str, data: dict) -> None:
    """Save product data to database.

    Args:
        link: The URL of the product page.
        data: Dictionary containing product information to save.
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
    """Main function to parse a product and save it.

    This function serves as the entry point for the script. It defines a product URL,
    parses the product data, and saves it to the database.
    """

    logging.info("SCRIPT STARTED: Product parser")

    url = 'https://brain.com.ua/ukr/Mobilniy_telefon_Apple_iPhone_16_Pro_Max_256GB_Black_Titanium-p1145443.html'

    try:
        data = parse(url)
        save_product(url, data)
        logging.info("SCRIPT COMPLETED SUCCESSFULLY")
    except Exception as e:
        logging.error(f"Script failed with error: {e}")
        logging.error("SCRIPT TERMINATED WITH ERRORS")
        raise


if __name__ == '__main__':
    main()
