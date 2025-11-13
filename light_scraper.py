#!/usr/bin/env python3
"""
Light BBQ Scraper - Simplified version that outputs products.json only
No database, no cleanup - just scrape and save to JSON
Iterates through all brands in url_list.json
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import random
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse
import logging
import sys
import re
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ===== CONFIGURATION =====
# TEST_MODE options:
#   0 = Full scrape (all products from all brands)
#   1 = Quick test (1 product from 1 random brand)
#   2 = Standard test (2 products from each brand)
TEST_MODE = int(os.getenv('TEST_MODE', '0'))

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


class LightScraper:
    def __init__(self, delay_range=(1, 3)):
        """Initialize the light scraper with rate limiting"""
        self.delay_range = delay_range
        self.session = requests.Session()
        self.base_url = 'https://www.bbqguys.com'

        # Initialize Supabase client if configured
        self.supabase = None
        if USE_SUPABASE and SUPABASE_URL and SUPABASE_KEY:
            try:
                self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
                logger.info("✓ Connected to Supabase")
            except Exception as e:
                logger.error(f"Failed to connect to Supabase: {e}")
                logger.info("Will fall back to JSON file storage")

        # Set headers to avoid being blocked
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })

    def get_page(self, url):
        """Fetch a webpage and return BeautifulSoup object"""
        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            # Add delay to be respectful
            delay = random.uniform(*self.delay_range)
            time.sleep(delay)

            return BeautifulSoup(response.content, 'html.parser')
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    # ===== STEP 1: PAGINATION DETECTION =====

    def get_page_count(self, brand_url):
        """Detect total number of pages for a brand"""
        logger.info("STEP 1: Detecting pagination...")
        soup = self.get_page(brand_url)

        if not soup:
            logger.error("Failed to fetch brand page")
            return 1

        max_page = 1

        # Method 1: BBQGuys Material-UI pagination
        pagination_nav = soup.select_one('nav[aria-label*="pagination"]')
        if pagination_nav:
            page_buttons = pagination_nav.select('button[aria-label*="page"]')
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
            for button in number_buttons:
                text = button.get_text(strip=True)
                if text.isdigit():
                    try:
                        max_page = max(max_page, int(text))
                    except ValueError:
                        pass

        logger.info(f"✓ Found {max_page} pages")
        return max_page

    # ===== STEP 2: URL EXTRACTION =====

    def extract_product_urls(self, brand_url, total_pages, test_mode=0):
        """Extract all product URLs from all pages

        Args:
            brand_url: URL of the brand page
            total_pages: Total number of pages to scrape
            test_mode: 0 = all products, 1 = 1 product, 2 = 2 products
        """
        logger.info(f"STEP 2: Extracting product URLs from {total_pages} pages...")
        if test_mode == 1:
            logger.info("  TEST MODE: Will limit to 1 product only")
            max_products = 1
        elif test_mode == 2:
            logger.info("  TEST MODE: Will limit to 2 products only")
            max_products = 2
        else:
            max_products = None

        all_urls = []

        for page_num in range(1, total_pages + 1):
            # If in test mode and we already have enough products, stop
            if max_products and len(all_urls) >= max_products:
                logger.info(f"  TEST MODE: Reached limit of {max_products} products")
                break

            # Generate page URL
            if page_num == 1:
                page_url = brand_url
            else:
                parsed = urlparse(brand_url)
                query_params = parse_qs(parsed.query) if parsed.query else {}
                query_params['page'] = [str(page_num)]
                new_query = urlencode(query_params, doseq=True)
                page_url = urlunparse((
                    parsed.scheme, parsed.netloc, parsed.path,
                    parsed.params, new_query, ''
                ))

            logger.info(f"  Processing page {page_num}/{total_pages}...")
            soup = self.get_page(page_url)

            if not soup:
                logger.warning(f"  Failed to fetch page {page_num}")
                continue

            # Extract product URLs (products have /i/ in path)
            links = soup.select('a[href*="/i/"]')
            for link in links:
                href = link.get('href')
                if href:
                    full_url = urljoin(self.base_url, href)
                    # Clean URL (remove query params)
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

            logger.info(f"  Found {len(all_urls)} total unique URLs so far")

            # If in test mode and we have enough, stop
            if max_products and len(all_urls) >= max_products:
                break

        logger.info(f"✓ Total unique products found: {len(all_urls)}")
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
        logger.info(f"STEP 3: Scraping {len(product_urls)} products...")
        products = []

        for i, url in enumerate(product_urls, 1):
            progress = (i / len(product_urls)) * 100
            logger.info(f"[{i}/{len(product_urls)}] ({progress:.1f}%) Scraping: {url}")

            product = self.scrape_product(url)
            if product:
                products.append(product)
                logger.info(f"  ✓ Success: {product.get('Title', 'Unknown')}")
            else:
                logger.warning(f"  ✗ Failed")

            # Progress indicator every 10 products
            if i % 10 == 0 or i == len(product_urls):
                logger.info(f"  Progress: {len(products)} successful, {i - len(products)} failed")

        logger.info(f"✓ Scraping complete: {len(products)}/{len(product_urls)} successful")
        return products

    # ===== MAIN WORKFLOW =====

    def run(self, brand_url, brand_name=None, test_mode=0):
        """Run the complete scraping workflow for a single brand

        Args:
            brand_url: URL of the brand page
            brand_name: Name of the brand
            test_mode: 0 = all products, 1 = 1 product, 2 = 2 products
        """
        logger.info("=" * 60)
        logger.info(f"SCRAPING BRAND: {brand_name or brand_url}")
        logger.info("=" * 60)
        logger.info(f"Target: {brand_url}")

        if test_mode == 0:
            mode_str = "FULL (all products)"
        elif test_mode == 1:
            mode_str = "TEST (1 product)"
        else:
            mode_str = "TEST (2 products)"

        logger.info(f"Mode: {mode_str}")
        logger.info("")

        # Step 1: Get page count
        total_pages = self.get_page_count(brand_url)
        logger.info("")

        # Step 2: Extract URLs
        product_urls = self.extract_product_urls(brand_url, total_pages, test_mode)
        logger.info("")

        # Step 3: Scrape products
        products = self.scrape_all_products(product_urls)
        logger.info("")

        logger.info("=" * 60)
        logger.info(f"BRAND COMPLETE: {brand_name or brand_url}")
        logger.info("=" * 60)
        logger.info(f"✓ Total products scraped: {len(products)}")
        logger.info(f"✓ Success rate: {len(products)}/{len(product_urls)} ({len(products)/len(product_urls)*100:.1f}%)")
        logger.info("")

        return products

    def save_to_supabase(self, products):
        """Save products to Supabase database"""
        if not self.supabase:
            logger.warning("Supabase not configured, skipping database save")
            return False

        try:
            logger.info(f"Saving {len(products)} products to Supabase...")

            # Insert products in batches of 100 to avoid timeouts
            batch_size = 100
            for i in range(0, len(products), batch_size):
                batch = products[i:i + batch_size]
                self.supabase.table('products').upsert(batch).execute()
                logger.info(f"  Saved batch {i//batch_size + 1}/{(len(products)-1)//batch_size + 1}")

            logger.info("✓ Successfully saved all products to Supabase")
            return True
        except Exception as e:
            logger.error(f"Error saving to Supabase: {e}")
            return False

    def run_all_brands(self, url_list_file='url_list.json', output_file='products.json', test_mode=0):
        """Run scraping for all brands in the url_list.json file

        Args:
            url_list_file: Path to JSON file with brand URLs
            output_file: Path to output JSON file
            test_mode: 0 = all products from all brands,
                      1 = 1 product from 1 random brand,
                      2 = 2 products from each brand
        """
        logger.info("=" * 80)
        logger.info("LIGHT BBQ SCRAPER - MULTI-BRAND MODE")
        logger.info("=" * 80)

        if test_mode == 0:
            mode_str = "FULL (all products from all brands)"
        elif test_mode == 1:
            mode_str = "QUICK TEST (1 product from 1 random brand)"
        else:
            mode_str = "STANDARD TEST (2 products from each brand)"

        logger.info(f"Mode: {mode_str}")
        logger.info(f"Input file: {url_list_file}")
        logger.info(f"Output file: {output_file}")
        logger.info(f"Supabase enabled: {USE_SUPABASE and self.supabase is not None}")
        logger.info("")

        # Load brands from JSON
        try:
            with open(url_list_file, 'r', encoding='utf-8') as f:
                brands = json.load(f)
            logger.info(f"✓ Loaded {len(brands)} brands from {url_list_file}")
            logger.info("")
        except FileNotFoundError:
            logger.error(f"Error: {url_list_file} not found!")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Error: Failed to parse {url_list_file}: {e}")
            return []

        # If test_mode is 1, select only one random brand
        if test_mode == 1:
            import random as rand
            brands = [rand.choice(brands)]
            logger.info(f"✓ Selected random brand: {brands[0].get('brand', 'Unknown')}")
            logger.info("")

        all_products = []
        successful_brands = 0
        failed_brands = []

        # Process each brand
        for i, brand_data in enumerate(brands, 1):
            brand_name = brand_data.get('brand', 'Unknown')
            brand_url = brand_data.get('url', '')

            if not brand_url:
                logger.warning(f"[{i}/{len(brands)}] Skipping brand '{brand_name}' - no URL provided")
                failed_brands.append(brand_name)
                continue

            logger.info("")
            logger.info("*" * 80)
            logger.info(f"PROCESSING BRAND {i}/{len(brands)}: {brand_name}")
            logger.info("*" * 80)

            try:
                products = self.run(brand_url, brand_name, test_mode)
                if products:
                    all_products.extend(products)
                    successful_brands += 1
                    logger.info(f"✓ Successfully scraped {len(products)} products from {brand_name}")
                else:
                    logger.warning(f"✗ No products found for {brand_name}")
                    failed_brands.append(brand_name)
            except Exception as e:
                logger.error(f"✗ Error processing {brand_name}: {e}")
                failed_brands.append(brand_name)

            logger.info("")
            logger.info(f"Progress: {i}/{len(brands)} brands processed")
            logger.info(f"Total products so far: {len(all_products)}")
            logger.info("")

        # Save all products
        logger.info("=" * 80)
        logger.info("SAVING RESULTS")
        logger.info("=" * 80)

        # Save to Supabase if configured
        if self.supabase:
            self.save_to_supabase(all_products)

        # Always save to JSON as backup
        logger.info(f"Saving {len(all_products)} products to {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_products, f, indent=2, ensure_ascii=False)

        logger.info("")
        logger.info("=" * 80)
        logger.info("ALL BRANDS COMPLETE!")
        logger.info("=" * 80)
        logger.info(f"✓ Total brands processed: {len(brands)}")
        logger.info(f"✓ Successful brands: {successful_brands}")
        logger.info(f"✓ Failed brands: {len(failed_brands)}")
        if failed_brands:
            logger.info(f"  Failed: {', '.join(failed_brands)}")
        logger.info(f"✓ Total products scraped: {len(all_products)}")
        logger.info(f"✓ Output file: {output_file}")
        logger.info("")

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
        logger.error("Please create url_list.json with brand URLs in the same directory")
        sys.exit(1)

    # Run scraper for all brands
    mode_descriptions = {
        0: "FULL SCRAPE - All products from all brands",
        1: "QUICK TEST - 1 product from 1 random brand",
        2: "STANDARD TEST - 2 products from each brand"
    }
    logger.info(f"Starting scraper with TEST_MODE = {TEST_MODE}")
    logger.info(f"  ({mode_descriptions.get(TEST_MODE, 'Unknown mode')})")
    logger.info("")

    scraper.run_all_brands(
        url_list_file=url_list_file,
        output_file=output_file,
        test_mode=TEST_MODE
    )


if __name__ == "__main__":
    main()
