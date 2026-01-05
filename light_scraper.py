#!/usr/bin/env python3
"""
Light BBQ Scraper - Simplified version that outputs products.json only
No database, no cleanup - just scrape and save to JSON
Iterates through all brands in url_list.json
"""

from bs4 import BeautifulSoup
import json
import time
import random
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse
import logging
import sys
import re
import os
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv
from curl_cffi import requests

# Load environment variables
load_dotenv()

# ===== CONFIGURATION =====
# TEST_MODE options:
#   0 = Full scrape (all products from all brands)
#   1 = Quick test (1 product from 1 random brand)
#   2 = Standard test (2 products from each brand)
TEST_MODE = int(os.getenv('TEST_MODE', '1'))

# Schedule mode - distribute brands across days of the week
USE_SCHEDULE = os.getenv('USE_SCHEDULE', 'false').lower() == 'true'

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
USE_SUPABASE = os.getenv('USE_SUPABASE', 'true').lower() == 'true'

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_brands_for_today(brands_by_day):
    """
    Get brands for current day of the week from day-keyed dictionary.

    Expected format:
    {
        "monday": [...],
        "tuesday": [...],
        ...
    }
    """
    day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    today_idx = datetime.now().weekday()  # 0=Monday, 6=Sunday
    today_name = day_names[today_idx]

    selected_brands = brands_by_day.get(today_name, [])

    logger.info(f"Today is {today_name.capitalize()}")
    logger.info(f"Brands for today: {', '.join([b.get('brand', 'Unknown') for b in selected_brands])}")
    logger.info("")

    return selected_brands


class LightScraper:
    def __init__(self, delay_range=(1, 3)):
        """Initialize the light scraper with rate limiting"""
        self.delay_range = delay_range
        self.base_url = 'https://www.bbqguys.com'
        self.session = requests.Session()

        # Initialize Supabase client if configured
        self.supabase = None
        if USE_SUPABASE and SUPABASE_URL and SUPABASE_KEY:
            try:
                self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            except Exception as e:
                logger.error(f"Failed to connect to Supabase: {e}")

    def get_page(self, url):
        """Fetch a webpage and return BeautifulSoup object using curl_cffi"""
        try:
            response = self.session.get(url, impersonate='chrome', timeout=30)
            response.raise_for_status()

            # Add delay to be respectful
            delay = random.uniform(*self.delay_range)
            time.sleep(delay)

            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    # ===== STEP 1: PAGINATION DETECTION =====

    def get_page_count(self, brand_url):
        """Detect total number of pages for a brand"""
        soup = self.get_page(brand_url)

        if not soup:
            logger.error("Failed to fetch brand page")
            return 1

        max_page = 1

        # Method 1: BBQGuys Material-UI pagination
        pagination_nav = soup.select_one('nav[aria-label*="pagination"]')
        logger.debug(f"  Pagination nav found: {pagination_nav is not None}")

        if pagination_nav:
            page_buttons = pagination_nav.select('button[aria-label*="page"]')
            logger.debug(f"  Found {len(page_buttons)} page buttons")
            for button in page_buttons:
                aria_label = button.get('aria-label', '').lower()
                page_matches = re.findall(r'(?:go to )?page (\d+)', aria_label)
                for match in page_matches:
                    try:
                        max_page = max(max_page, int(match))
                    except ValueError:
                        pass

            # Check button text content for numbers
            number_buttons = pagination_nav.select('button.MuiPaginationItem-page')
            logger.debug(f"  Found {len(number_buttons)} number buttons")
            for button in number_buttons:
                text = button.get_text(strip=True)
                if text.isdigit():
                    try:
                        max_page = max(max_page, int(text))
                    except ValueError:
                        pass

        logger.info(f"  Detected {max_page} pages")
        return max_page

    # ===== STEP 2: URL EXTRACTION =====

    def extract_product_urls(self, brand_url, total_pages, test_mode=0):
        """Extract all product URLs from page 1 (JS-rendered pages beyond page 1 are blocked by Akamai)

        Args:
            brand_url: URL of the brand page
            total_pages: Total number of pages (currently only page 1 is accessible)
            test_mode: 0 = all products, 1 = 1 product, 2 = 2 products
        """
        if test_mode == 1:
            max_products = 1
        elif test_mode == 2:
            max_products = 2
        else:
            max_products = None

        all_urls = []

        # Note: BBQGuys uses JS-rendered pagination which requires browser automation.
        # Akamai bot protection blocks Playwright/Selenium, so we can only get page 1.
        # Page 1 typically contains 40 products per brand.
        logger.info(f"    Fetching products (page 1 only - JS pagination blocked by Akamai)")
        soup = self.get_page(brand_url)

        if not soup:
            logger.warning(f"    Failed to fetch brand page")
            return all_urls

        # Extract product URLs (products have /i/ in path)
        links = soup.select('a[href*="/i/"]')
        for link in links:
            href = link.get('href')
            if href and 'gift-card' not in href:
                full_url = urljoin(self.base_url, href)
                # Clean URL (remove query params and anchors)
                parsed = urlparse(full_url)
                clean_url = urlunparse((
                    parsed.scheme, parsed.netloc, parsed.path,
                    '', '', ''
                ))
                if clean_url not in all_urls:
                    all_urls.append(clean_url)

                    # If in test mode and we have enough, stop
                    if max_products and len(all_urls) >= max_products:
                        break

        logger.info(f"    Found {len(all_urls)} products")
        return all_urls

    # ===== STEP 3: PRODUCT SCRAPING =====

    def scrape_product(self, url):
        """Scrape detailed product information"""
        soup = self.get_page(url)
        if not soup:
            return None

        product = {'url': url}

        try:
            # Title
            title_elem = soup.select_one('h1')
            product['Title'] = title_elem.get_text(strip=True) if title_elem else ''

            # Price
            price_elem = soup.select_one('span.MuiBox-root.bbq-0')
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                try:
                    price_clean = price_text.replace('$', '').replace(',', '').strip()
                    product['Price'] = float(price_clean)
                except ValueError:
                    product['Price'] = price_text
            else:
                product['Price'] = None

            # Brand - look for link with MuiLink-underlineAlways class that contains brand info
            brand_elem = soup.select_one('a.MuiTypography-root.MuiLink-root.MuiLink-underlineAlways[href*="/brands/"]')
            if not brand_elem:
                # Fallback to original selector
                brand_elem = soup.select_one('a.MuiTypography-root.MuiLink-root')
            product['brand'] = brand_elem.get_text(strip=True) if brand_elem else ''

            # Image
            image_links = soup.select('.carousel__images a')
            product['Image'] = image_links[0].get('href') if image_links else ''
            product['Other_image'] = [link.get('href') for link in image_links if link.get('href')]

            # ID and Model
            id_spans = soup.select('span.MuiTypography-root.MuiTypography-body2.bbq-131zxzk')

            # Extract ID and Model from the spans
            product['Id'] = ''
            product['Model'] = ''

            for span in id_spans:
                text = span.get_text(strip=True)
                if 'ID #' in text:
                    product['Id'] = text.split('#')[-1].strip()
                elif 'Model #' in text:
                    product['Model'] = text.split('#')[-1].strip()

            # Category (breadcrumbs)
            breadcrumbs = soup.select('ol.MuiBreadcrumbs-ol a')
            product['category'] = [bc.get_text(strip=True) for bc in breadcrumbs]

            # Description (combine key features and full description)
            description_parts = []

            # Get the main key feature bullet
            key_feature_bullet = soup.select_one('span.MuiTypography-keyFeatureBullet')
            if key_feature_bullet:
                description_parts.append(key_feature_bullet.get_text(strip=True))

            # Get key features list
            key_features = soup.select('ul.bullets li')
            for kf in key_features:
                description_parts.append(kf.get_text(strip=True))

            # Get the full description content
            desc_div = soup.select_one('div.MuiTypography-root.MuiTypography-body1.bbq-ywiv8x')
            if desc_div:
                # Get all text content from the div, preserving structure
                description_parts.append(desc_div.get_text(separator=' ', strip=True))

            product['Description'] = ' '.join(description_parts).strip()

            # Specifications
            spec_rows = soup.select('tbody.MuiTableBody-root tr')
            specifications = []
            for row in spec_rows:
                header = row.select_one('th')
                value = row.select_one('td')
                if header and value:
                    # Remove button elements
                    header_copy = BeautifulSoup(str(header), 'html.parser')
                    for btn in header_copy.find_all('button'):
                        btn.decompose()
                    spec_name = header_copy.get_text(strip=True)
                    spec_value = value.get_text(strip=True)
                    specifications.append({spec_name: spec_value})
            product['Specifications'] = specifications


        except Exception as e:
            logger.error(f"Error extracting data from {url}: {e}")
            return None

        return product

    def scrape_all_products(self, product_urls):
        """Scrape all products and return list"""
        products = []

        for i, url in enumerate(product_urls, 1):
            product = self.scrape_product(url)
            if product:
                products.append(product)

        return products

    # ===== MAIN WORKFLOW =====

    def run(self, brand_url, brand_name=None, test_mode=0):
        """Run the complete scraping workflow for a single brand

        Args:
            brand_url: URL of the brand page
            brand_name: Name of the brand
            test_mode: 0 = all products, 1 = 1 product, 2 = 2 products
        """
        total_pages = self.get_page_count(brand_url)
        product_urls = self.extract_product_urls(brand_url, total_pages, test_mode)
        products = self.scrape_all_products(product_urls)
        return products

    def save_to_supabase(self, products):
        """Save products to Supabase database"""
        if not self.supabase:
            return False

        try:
            batch_size = 100
            for i in range(0, len(products), batch_size):
                batch = products[i:i + batch_size]
                self.supabase.table('scrapped_products2').insert(batch).execute()
            return True
        except Exception as e:
            logger.error(f"Error saving to Supabase: {e}")
            return False

    def run_all_brands(self, url_list_file='url_list.json', output_file='products.json', test_mode=0):
        """Run scraping for all brands in the url_list.json file

        Args:
            url_list_file: Path to JSON file with brand URLs (day-keyed format)
            output_file: Path to output JSON file
            test_mode: 0 = all products from all brands,
                      1 = 1 product from 1 random brand,
                      2 = 2 products from each brand
        """
        # Load brands from JSON
        try:
            with open(url_list_file, 'r', encoding='utf-8') as f:
                brands_data = json.load(f)
        except FileNotFoundError:
            logger.error(f"Error: {url_list_file} not found!")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Error: Failed to parse {url_list_file}: {e}")
            return []

        # Get brands for today (or all brands if USE_SCHEDULE is disabled)
        if USE_SCHEDULE and test_mode == 0:
            brands = get_brands_for_today(brands_data)
        else:
            # Flatten all days into a single list
            brands = []
            for day_brands in brands_data.values():
                brands.extend(day_brands)

        # If test_mode is 1, select only one random brand
        if test_mode == 1:
            import random as rand
            brands = [rand.choice(brands)]

        all_products = []

        # Process each brand
        for i, brand_data in enumerate(brands, 1):
            brand_name = brand_data.get('brand', 'Unknown')
            brand_url = brand_data.get('url', '')

            if not brand_url:
                continue

            logger.info(f"[{i}/{len(brands)}] {brand_name}")

            try:
                products = self.run(brand_url, brand_name, test_mode)
                if products:
                    all_products.extend(products)
                    logger.info(f"  -> {len(products)} products")
            except Exception as e:
                logger.error(f"  -> Error: {e}")

        # Save to Supabase if configured
        if self.supabase:
            self.save_to_supabase(all_products)

        # Always save to JSON as backup
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_products, f, indent=2, ensure_ascii=False)

        logger.info(f"Done: {len(all_products)} products saved to {output_file}")
        return all_products


def main():
    """Main entry point"""
    scraper = LightScraper()

    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    url_list_file = os.path.join(script_dir, 'url_list.json')
    output_file = os.path.join(script_dir, 'products.json')

    # Check if url_list.json exists
    if not os.path.exists(url_list_file):
        logger.error(f"Error: {url_list_file} not found!")
        sys.exit(1)

    scraper.run_all_brands(
        url_list_file=url_list_file,
        output_file=output_file,
        test_mode=TEST_MODE
    )


if __name__ == "__main__":
    main()
