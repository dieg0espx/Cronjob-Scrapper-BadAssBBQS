# Brand Scraping Schedule

When `USE_SCHEDULE=true` in `.env`, brands are distributed across the week to reduce server load and respect rate limits.

## Weekly Schedule (3 brands per day)

### Monday
- Alfresco Grills
- American Made Grills
- American Outdoor Grill

### Tuesday
- Artisan Grills
- Blackstone Grills
- Blaze Grills

### Wednesday
- Breeo
- Bromic Heating
- Coyote Outdoor Living

### Thursday
- Delta Heat
- Fire Magic Grills
- Fontana Forni

### Friday
- Green Mountain Grills
- Napoleon
- Twin Eagles Grills

### Saturday
- Primo Ceramic Grills
- Summerset Grills
- Mont Alpi

### Sunday
- American Fyre Designs
- The Outdoor Plus - Top Fires
- Ledge Lounger

## Configuration

To enable daily scheduling:
```bash
USE_SCHEDULE=true
TEST_MODE=0
```

To run all brands at once:
```bash
USE_SCHEDULE=false
TEST_MODE=0
```

## Cron Job Setup

Add this to your cron or Railway configuration to run daily at midnight:
```
0 0 * * * python3 index.py
```

This will automatically scrape today's assigned brands and upload to the database.
