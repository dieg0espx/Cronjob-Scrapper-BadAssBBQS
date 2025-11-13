#!/usr/bin/env python3
"""
Upload products.json to Supabase database
"""

import json
import os
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# Get Supabase credentials
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: Missing Supabase credentials in .env file")
    exit(1)

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_products(json_file='products.json'):
    """Upload products from JSON file to database"""

    # Load products from JSON
    print(f"Loading products from {json_file}...")
    with open(json_file, 'r', encoding='utf-8') as f:
        products = json.load(f)

    print(f"Found {len(products)} products to upload")

    # Upload each product
    successful = 0
    failed = 0

    for i, product in enumerate(products, 1):
        try:
            # Insert product into database
            response = supabase.table('scrapped_products2').insert(product).execute()

            print(f"[{i}/{len(products)}] ✓ Uploaded: {product.get('Title', 'Unknown')}")
            successful += 1

        except Exception as e:
            print(f"[{i}/{len(products)}] ✗ Failed: {product.get('Title', 'Unknown')}")
            print(f"  Error: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print("UPLOAD COMPLETE")
    print("=" * 60)
    print(f"✓ Successful: {successful}")
    print(f"✗ Failed: {failed}")
    print(f"Total: {len(products)}")
    print("=" * 60)

if __name__ == "__main__":
    upload_products()
