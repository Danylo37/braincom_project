"""Module to retrieve and display information about a product in the database."""

import load_django
from parser_app.models import Product
from pprint import pprint


def display_product_info(product: Product) -> None:
    """
    Display detailed information about a product.

    Args:
        product (Product): The product instance to display information for.
    """
    product_data = {
        "Title": product.title,
        "Regular price": product.regular_price,
        "Discount price": product.discount_price,
        "Product code": product.product_code,
        "Vendor": product.vendor,
        "Color": product.color,
        "Memory volume": product.memory_volume,
        "Review count": product.review_count,
        "Series": product.series,
        "Screen diagonal": product.screen_diagonal,
        "Screen resolution": product.screen_resolution,
        "Link": product.link,
        "Photos": product.photos,
        "Specifications": product.specifications if product.specifications else "No specifications"
    }

    pprint(product_data, sort_dicts=False, width=200)


def main() -> None:
    """Get and display information about the first product in the database."""
    product = Product.objects.first()

    if product:
        display_product_info(product)
    else:
        print("No products found in the database.")


if __name__ == "__main__":
    main()

