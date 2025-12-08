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
    logger.info("=" * 80)
    logger.info("STEP 1: RUNNING SCRAPER")
    logger.info("=" * 80)

    try:
        result = subprocess.run(
            [sys.executable, 'light_scraper.py'],
            check=True,
            capture_output=False,
            text=True
        )
        logger.info("✓ Scraper completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"✗ Scraper failed with exit code {e.returncode}")
        return False

def upload_to_database(json_file='products.json'):
    """Upload products from JSON file to Supabase database with deduplication

    Returns:
        tuple: (success: bool, brands_scraped: list, stats: dict, failed_brands: list)
    """
    logger.info("\n" + "=" * 80)
    logger.info("STEP 2: UPLOADING TO DATABASE")
    logger.info("=" * 80)

    # Get Supabase credentials
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY')

    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("✗ Missing Supabase credentials in .env file")
        return False, [], {}, []

    # Check if products file exists
    if not os.path.exists(json_file):
        logger.error(f"✗ {json_file} not found")
        return False, [], {}, []

    # Initialize Supabase client
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        logger.error(f"✗ Failed to connect to Supabase: {e}")
        return False, [], {}, []

    # Load products from JSON
    logger.info(f"Loading products from {json_file}...")
    with open(json_file, 'r', encoding='utf-8') as f:
        products = json.load(f)

    logger.info(f"Found {len(products)} products to process")
    logger.info("Checking for duplicates and updates...")

    # Track brands and stats
    brands_scraped = set()
    new_products = 0
    updated_products = 0
    skipped_products = 0
    failed = 0

    # Detailed tracking for email
    product_details = []

    for i, product in enumerate(products, 1):
        try:
            brand = product.get('brand', '')
            product_id = product.get('Id', '')
            model = product.get('Model', '')
            title = product.get('Title', 'Unknown')

            # Track brand
            if brand:
                brands_scraped.add(brand)

            # Check if product exists by brand, Id, and Model
            query = supabase.table('scrapped_products2').select('*')

            if brand:
                query = query.eq('brand', brand)
            if product_id:
                query = query.eq('Id', product_id)
            if model:
                query = query.eq('Model', model)

            existing = query.execute()

            if existing.data and len(existing.data) > 0:
                # Product exists, check if data is different
                existing_product = existing.data[0]

                # Compare relevant fields to see if update is needed
                needs_update = False
                fields_to_compare = ['Title', 'Price', 'Image', 'Description', 'Specifications', 'category']

                for field in fields_to_compare:
                    if product.get(field) != existing_product.get(field):
                        needs_update = True
                        break

                if needs_update:
                    # Update existing product
                    product['updated_at'] = 'now()'
                    supabase.table('scrapped_products2').update(product).eq('id', existing_product['id']).execute()
                    logger.info(f"[{i}/{len(products)}] 🔄 Updated: {title}")
                    updated_products += 1
                    product_details.append({
                        'title': title,
                        'brand': brand,
                        'action': 'updated'
                    })
                else:
                    # Skip - data is identical
                    logger.info(f"[{i}/{len(products)}] ⏭️  Skipped (no changes): {title}")
                    skipped_products += 1
                    product_details.append({
                        'title': title,
                        'brand': brand,
                        'action': 'skipped'
                    })
            else:
                # New product - insert
                supabase.table('scrapped_products2').insert(product).execute()
                logger.info(f"[{i}/{len(products)}] ✅ New: {title}")
                new_products += 1
                product_details.append({
                    'title': title,
                    'brand': brand,
                    'action': 'new'
                })

        except Exception as e:
            logger.error(f"[{i}/{len(products)}] ✗ Failed: {product.get('Title', 'Unknown')}")
            logger.error(f"  Error: {e}")
            failed += 1
            product_details.append({
                'title': product.get('Title', 'Unknown'),
                'brand': product.get('brand', 'Unknown'),
                'action': 'failed',
                'error': str(e)
            })

    logger.info("\n" + "=" * 80)
    logger.info("DATABASE UPLOAD COMPLETE")
    logger.info("=" * 80)
    logger.info(f"✅ New products: {new_products}")
    logger.info(f"🔄 Updated products: {updated_products}")
    logger.info(f"⏭️  Skipped (no changes): {skipped_products}")
    logger.info(f"✗ Failed: {failed}")
    logger.info(f"Total processed: {len(products)}")
    logger.info("=" * 80)

    stats = {
        'new': new_products,
        'updated': updated_products,
        'skipped': skipped_products,
        'failed': failed,
        'total': len(products),
        'details': product_details
    }

    return failed == 0, list(brands_scraped), stats, []

def main():
    """Main execution flow"""
    logger.info("\n" + "=" * 80)
    logger.info("BBQ SCRAPER - FULL PIPELINE")
    logger.info("=" * 80)
    logger.info("")

    try:
        # Step 1: Run scraper
        if not run_scraper():
            logger.error("Pipeline failed at scraping stage")
            sys.exit(1)

        # Step 2: Upload to database
        success, brands_scraped, stats, failed_brands = upload_to_database()

        if not success:
            logger.error("Pipeline failed at database upload stage")
            sys.exit(1)

        logger.info("Pipeline complete")

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
