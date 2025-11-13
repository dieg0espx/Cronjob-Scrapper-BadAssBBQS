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
    """Upload products from JSON file to Supabase database"""
    logger.info("\n" + "=" * 80)
    logger.info("STEP 2: UPLOADING TO DATABASE")
    logger.info("=" * 80)

    # Get Supabase credentials
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY')

    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("✗ Missing Supabase credentials in .env file")
        return False

    # Check if products file exists
    if not os.path.exists(json_file):
        logger.error(f"✗ {json_file} not found")
        return False

    # Initialize Supabase client
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        logger.error(f"✗ Failed to connect to Supabase: {e}")
        return False

    # Load products from JSON
    logger.info(f"Loading products from {json_file}...")
    with open(json_file, 'r', encoding='utf-8') as f:
        products = json.load(f)

    logger.info(f"Found {len(products)} products to upload")

    # Upload each product
    successful = 0
    failed = 0

    for i, product in enumerate(products, 1):
        try:
            # Insert product into database
            response = supabase.table('scrapped_products2').insert(product).execute()

            logger.info(f"[{i}/{len(products)}] ✓ Uploaded: {product.get('Title', 'Unknown')}")
            successful += 1

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

    return failed == 0

def main():
    """Main execution flow"""
    logger.info("\n" + "=" * 80)
    logger.info("BBQ SCRAPER - FULL PIPELINE")
    logger.info("=" * 80)
    logger.info("")

    # Step 1: Run scraper
    if not run_scraper():
        logger.error("\n✗ Pipeline failed at scraping stage")
        sys.exit(1)

    # Step 2: Upload to database
    if not upload_to_database():
        logger.error("\n✗ Pipeline failed at database upload stage")
        sys.exit(1)

    # Success
    logger.info("\n" + "=" * 80)
    logger.info("✓ PIPELINE COMPLETE - ALL STEPS SUCCESSFUL")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()
