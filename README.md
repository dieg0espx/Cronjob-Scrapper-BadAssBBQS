# Light BBQ Scraper

A simplified, single-file BBQ product scraper that outputs data to JSON. No database, no cleanup - just scrape and save.

## Features

- ✅ Single Python file - easy to understand and modify
- ✅ Automatic pagination detection
- ✅ Extracts all products from a brand
- ✅ Outputs clean JSON file
- ✅ Rate limiting to be respectful
- ✅ Progress tracking with detailed logging
- ✅ No database dependencies
- ✅ Minimal requirements

## What It Does

1. **Step 1:** Detects how many pages a brand has
2. **Step 2:** Extracts all product URLs from all pages
3. **Step 3:** Scrapes detailed product data
4. **Output:** Saves everything to `products.json`

## Installation

### 1. Create Virtual Environment

```bash
cd light
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

That's it! Only 3 lightweight dependencies:
- `requests` - HTTP client
- `beautifulsoup4` - HTML parsing
- `lxml` - Fast parser

## Usage

### Basic Usage

```bash
python light_scraper.py '<brand_url>'
```

### Example

```bash
python light_scraper.py 'https://www.bbqguys.com/d/22965/brands/fontana-forni/shop-all'
```

### Custom Output File

```bash
python light_scraper.py '<brand_url>' my_custom_output.json
```

### Example with Custom Output

```bash
python light_scraper.py 'https://www.bbqguys.com/d/22965/brands/fontana-forni/shop-all' fontana_products.json
```

## Output Format

The scraper generates a JSON file with this structure:

```json
[
  {
    "url": "https://www.bbqguys.com/i/12345/product-name",
    "Title": "Product Name",
    "Price": 1234.56,
    "brand": "Brand Name",
    "Image": "https://...",
    "Other_images": ["https://...", "https://..."],
    "Id": "12345",
    "Model": "MODEL-123",
    "Category": ["Home", "Grills", "Gas Grills"],
    "Description": "Full product description with features...",
    "Specifications": [
      {"Width": "48 inches"},
      {"Height": "36 inches"}
    ],
    "configurations": [
      {"label": "Size", "value": "Large"}
    ]
  }
]
```

## What's Extracted

| Field | Description |
|-------|-------------|
| **url** | Product page URL |
| **Title** | Product name |
| **Price** | Price as number (e.g., 1234.56) |
| **brand** | Brand name |
| **Image** | Main product image URL |
| **Other_images** | Array of all product images |
| **Id** | Product ID |
| **Model** | Model number |
| **Category** | Breadcrumb categories (array) |
| **Description** | Full description with key features |
| **Specifications** | Technical specs (array of objects) |
| **configurations** | Product configuration options |

## Configuration

### Adjust Rate Limiting

Edit `light_scraper.py` line 27:

```python
scraper = LightScraper(delay_range=(1, 3))  # Default: 1-3 seconds
scraper = LightScraper(delay_range=(2, 5))  # Slower (safer)
scraper = LightScraper(delay_range=(0.5, 1))  # Faster (riskier)
```

## Example Workflow

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Scrape Fontana Forni products
python light_scraper.py 'https://www.bbqguys.com/d/22965/brands/fontana-forni/shop-all'

# 3. Check output
cat products.json | head -50

# 4. Count products
cat products.json | jq '. | length'
```

## Output Example

```
============================================================
LIGHT BBQ SCRAPER - START
============================================================
Target: https://www.bbqguys.com/d/22965/brands/fontana-forni/shop-all
Output: products.json

STEP 1: Detecting pagination...
✓ Found 3 pages

STEP 2: Extracting product URLs from 3 pages...
  Processing page 1/3...
  Processing page 2/3...
  Processing page 3/3...
✓ Total unique products found: 42

STEP 3: Scraping 42 products...
[1/42] (2.4%) Scraping: https://...
  ✓ Success: Fontana Forni Pizza Oven
[2/42] (4.8%) Scraping: https://...
  ✓ Success: Fontana Forni Grill
...
✓ Scraping complete: 42/42 successful

Saving 42 products to products.json...
============================================================
COMPLETE!
============================================================
✓ Total products scraped: 42
✓ Output file: products.json
✓ Success rate: 42/42 (100.0%)
```

## Differences from Full Version

| Feature | Full Version | Light Version |
|---------|--------------|---------------|
| **Files** | 5 separate steps + orchestrator | Single file |
| **Database** | Supabase upload (Step 4) | ❌ None - JSON only |
| **Cleanup** | Deletes temp files (Step 5) | ❌ Not needed |
| **Scheduling** | Daily brand rotation | ❌ Manual execution |
| **Dependencies** | 7+ packages | 3 packages |
| **Complexity** | ~1000 lines across files | ~350 lines single file |
| **Output** | PostgreSQL database | JSON file |
| **Use Case** | Production automation | Quick data extraction |

## Advantages of Light Version

- ✅ **Simple:** Single file, easy to understand
- ✅ **Portable:** Just copy one file + requirements.txt
- ✅ **No Database:** No setup required
- ✅ **Flexible:** Easy to modify for different sites
- ✅ **Transparent:** See exactly what it's doing
- ✅ **Fast Setup:** Install and run in 2 minutes

## Troubleshooting

### Issue: No products found

**Solution:** Website structure may have changed. Check CSS selectors in `scrape_product()` method.

### Issue: Rate limited / blocked

**Solution:** Increase delay range:
```python
scraper = LightScraper(delay_range=(3, 6))
```

### Issue: Import errors

**Solution:** Ensure dependencies are installed:
```bash
pip install -r requirements.txt
```

## Common Brand URLs

Here are some BBQGuys brand URLs to try:

```bash
# Fontana Forni
python light_scraper.py 'https://www.bbqguys.com/d/22965/brands/fontana-forni/shop-all'

# Blaze Grills
python light_scraper.py 'https://www.bbqguys.com/d/17960/brands/blaze-grills/shop-all'

# Napoleon
python light_scraper.py 'https://www.bbqguys.com/d/17946/brands/napoleon-shop-all'

# Fire Magic
python light_scraper.py 'https://www.bbqguys.com/d/17978/brands/fire-magic-grills/shop-all'
```

## Best Practices

1. **Test First:** Start with a small brand (1-2 pages)
2. **Be Respectful:** Don't lower delay too much
3. **Check Output:** Verify JSON structure after scraping
4. **Handle Errors:** Check logs if scraping fails
5. **Backup Data:** Save different brands to different files

## Support

For issues or questions, refer to the main project documentation in `bmad/output/`.

---

**Created:** 2025-11-10
**Version:** 1.0
**License:** Same as parent project
