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
from email_notifier import send_scraping_notification, send_error_notification

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
    """Upload products from JSON file to Supabase database

    Returns:
        tuple: (success: bool, brands_scraped: list, total_products: int, failed_brands: list)
    """
    logger.info("\n" + "=" * 80)
    logger.info("STEP 2: UPLOADING TO DATABASE")
    logger.info("=" * 80)

    # Get Supabase credentials
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY')

    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("✗ Missing Supabase credentials in .env file")
        return False, [], 0, []

    # Check if products file exists
    if not os.path.exists(json_file):
        logger.error(f"✗ {json_file} not found")
        return False, [], 0, []

    # Initialize Supabase client
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        logger.error(f"✗ Failed to connect to Supabase: {e}")
        return False, [], 0, []

    # Load products from JSON
    logger.info(f"Loading products from {json_file}...")
    with open(json_file, 'r', encoding='utf-8') as f:
        products = json.load(f)

    logger.info(f"Found {len(products)} products to upload")

    # Track brands
    brands_scraped = set()

    # Upload each product
    successful = 0
    failed = 0

    for i, product in enumerate(products, 1):
        try:
            # Insert product into database
            response = supabase.table('scrapped_products2').insert(product).execute()

            logger.info(f"[{i}/{len(products)}] ✓ Uploaded: {product.get('Title', 'Unknown')}")
            successful += 1

            # Track brand
            if 'brand' in product:
                brands_scraped.add(product['brand'])

        except Exception as e:
            logger.error(f"[{i}/{len(products)}] ✗ Failed: {product.get('Title', 'Unknown')}")
            logger.error(f"  Error: {e}")
            failed += 1

    logger.info("\n" + "=" * 80)
    logger.info("DATABASE UPLOAD COMPLETE")
    logger.info("=" * 80)
    logger.info(f"✓ Successful: {successful}")
    logger.info(f"✗ Failed: {failed}")
    logger.info(f"Total: {len(products)}")
    logger.info("=" * 80)

    return failed == 0, list(brands_scraped), successful, []

def main():
    """Main execution flow"""
    logger.info("\n" + "=" * 80)
    logger.info("BBQ SCRAPER - FULL PIPELINE")
    logger.info("=" * 80)
    logger.info("")

    try:
        # Step 1: Run scraper
        if not run_scraper():
            error_msg = "Pipeline failed at scraping stage"
            logger.error(f"\n✗ {error_msg}")
            send_error_notification(error_msg)
            sys.exit(1)

        # Step 2: Upload to database
        success, brands_scraped, total_products, failed_brands = upload_to_database()

        if not success:
            error_msg = "Pipeline failed at database upload stage"
            logger.error(f"\n✗ {error_msg}")
            send_error_notification(error_msg)
            sys.exit(1)

        # Success
        logger.info("\n" + "=" * 80)
        logger.info("✓ PIPELINE COMPLETE - ALL STEPS SUCCESSFUL")
        logger.info("=" * 80)

        # Step 3: Send email notification
        logger.info("\n" + "=" * 80)
        logger.info("STEP 3: SENDING EMAIL NOTIFICATION")
        logger.info("=" * 80)

        success_rate = 100.0 if total_products > 0 else 0.0
        send_scraping_notification(
            brands_scraped=brands_scraped,
            total_products=total_products,
            success_rate=success_rate,
            failed_brands=failed_brands
        )

    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(f"\n✗ {error_msg}")
        send_error_notification(error_msg)
        sys.exit(1)

if __name__ == "__main__":
    main()
