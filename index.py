#!/usr/bin/env python3
"""
Main entry point - Runs scraper and uploads to database
"""

import subprocess
import sys
import os
import json
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def run_scraper():
    """Run the light_scraper.py script"""
    try:
        subprocess.run([sys.executable, 'light_scraper.py'], check=True, capture_output=False, text=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Scraper failed: {e.returncode}")
        return False

def upload_to_database(json_file='products.json'):
    """Upload products from JSON file to Supabase database with deduplication"""
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY')

    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("Missing Supabase credentials")
        return False, [], {}, []

    if not os.path.exists(json_file):
        logger.error(f"{json_file} not found")
        return False, [], {}, []

    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        logger.error(f"Supabase connection failed: {e}")
        return False, [], {}, []

    with open(json_file, 'r', encoding='utf-8') as f:
        products = json.load(f)

    brands_scraped = set()
    new_products = 0
    updated_products = 0
    skipped_products = 0
    failed = 0

    for product in products:
        try:
            brand = product.get('brand', '')
            product_id = product.get('Id', '')
            model = product.get('Model', '')

            if brand:
                brands_scraped.add(brand)

            query = supabase.table('scrapped_products2').select('*')
            if brand:
                query = query.eq('brand', brand)
            if product_id:
                query = query.eq('Id', product_id)
            if model:
                query = query.eq('Model', model)

            existing = query.execute()

            if existing.data and len(existing.data) > 0:
                existing_product = existing.data[0]
                needs_update = False
                for field in ['Title', 'Price', 'Image', 'Description', 'Specifications', 'category']:
                    if product.get(field) != existing_product.get(field):
                        needs_update = True
                        break

                if needs_update:
                    product['updated_at'] = 'now()'
                    supabase.table('scrapped_products2').update(product).eq('id', existing_product['id']).execute()
                    updated_products += 1
                else:
                    skipped_products += 1
            else:
                supabase.table('scrapped_products2').insert(product).execute()
                new_products += 1

        except Exception as e:
            logger.error(f"DB error: {e}")
            failed += 1

    logger.info(f"DB: {new_products} new, {updated_products} updated, {skipped_products} skipped, {failed} failed")

    stats = {
        'new': new_products,
        'updated': updated_products,
        'skipped': skipped_products,
        'failed': failed,
        'total': len(products)
    }

    return failed == 0, list(brands_scraped), stats, []

def main():
    """Main execution flow"""
    try:
        if not run_scraper():
            logger.error("Scraper failed")
            sys.exit(1)

        success, _, _, _ = upload_to_database()
        if not success:
            logger.error("DB upload failed")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
