# BBQ Scraper - Railway Deployment Guide

A lightweight web scraper for BBQGuys.com that extracts product information and stores it in Supabase.

## Features

- Scrapes 21 BBQ brands from BBQGuys.com
- Extracts product details (title, price, images, specs, etc.)
- Stores data in Supabase database
- Configurable test modes
- Rate limiting to be respectful
- Runs as daily cron job on Railway

## Prerequisites

1. **Railway account** - Sign up at https://railway.app
2. **Supabase account** - Sign up at https://supabase.com
3. **GitHub account** - To deploy from repository

## Step 1: Set up Supabase Database

1. Create a new project in Supabase
2. Go to SQL Editor and run this query:

```sql
CREATE TABLE products (
  id SERIAL PRIMARY KEY,
  url TEXT UNIQUE,
  "Title" TEXT,
  "Price" NUMERIC,
  brand TEXT,
  "Image" TEXT,
  "Other_image" JSONB,
  "Id" TEXT,
  "Model" TEXT,
  category JSONB,
  "Description" TEXT,
  "Specifications" JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add index for better query performance
CREATE INDEX idx_products_brand ON products(brand);
CREATE INDEX idx_products_url ON products(url);
```

3. Get your credentials from Settings > API:
   - `SUPABASE_URL` (Project URL)
   - `SUPABASE_KEY` (anon/public key)

## Step 2: Push to GitHub

```bash
cd light
git init
git add .
git commit -m "Initial commit - BBQ scraper"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

## Step 3: Deploy to Railway

### Method A: GitHub Integration (Recommended)

1. Go to https://railway.app/new
2. Click "Deploy from GitHub repo"
3. Select your repository
4. Railway will auto-detect Python and deploy

### Method B: Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to project
railway link

# Deploy
railway up
```

## Step 4: Configure Environment Variables

In Railway Dashboard > Variables, add:

```
TEST_MODE=0
USE_SUPABASE=true
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your_anon_key_here
```

## Step 5: Set up Cron Schedule

**Option A: Railway Cron Service (Recommended)**

1. In Railway dashboard, click "+ New"
2. Select "Cron Job"
3. Set schedule: `0 0 * * *` (daily at midnight UTC)
4. Connect to your deployed service

**Option B: Environment Variable**

Add to Variables:
```
RAILWAY_CRON_SCHEDULE=0 0 * * *
```

## Cron Schedule Examples

```bash
# Daily at midnight UTC
0 0 * * *

# Daily at 2 AM UTC
0 2 * * *

# Every 12 hours
0 */12 * * *

# Every Monday at 9 AM UTC
0 9 * * 1

# Twice daily (6 AM and 6 PM UTC)
0 6,18 * * *
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TEST_MODE` | `0` | `0`=Full scrape, `1`=1 product/1 brand, `2`=2 products/brand |
| `USE_SUPABASE` | `true` | Enable Supabase storage |
| `SUPABASE_URL` | - | Your Supabase project URL |
| `SUPABASE_KEY` | - | Your Supabase anon key |

## Testing Before Production

1. Set `TEST_MODE=2` for initial testing
2. Monitor Railway logs:
   ```bash
   railway logs
   ```
3. Check Supabase table for scraped data
4. Once verified, set `TEST_MODE=0` for full scraping

## Project Structure

```
light/
├── light_scraper.py    # Main scraper script
├── url_list.json       # List of 21 brands to scrape
├── requirements.txt    # Python dependencies
├── railway.json        # Railway configuration
├── Procfile           # Process definition
├── runtime.txt        # Python version
├── .env.example       # Environment template
├── .gitignore         # Git ignore rules
└── DEPLOY.md          # This file
```

## Monitoring & Logs

**View logs in Railway:**
- Dashboard > Deployments > Logs
- Or use CLI: `railway logs --follow`

**Check Supabase data:**
```sql
-- Count products by brand
SELECT brand, COUNT(*)
FROM products
GROUP BY brand
ORDER BY COUNT(*) DESC;

-- View recent scrapes
SELECT brand, "Title", "Price"
FROM products
ORDER BY created_at DESC
LIMIT 10;
```

## Troubleshooting

### "ModuleNotFoundError"
- Railway should auto-install from requirements.txt
- Check deployment logs for build errors

### Supabase Connection Failed
- Verify `SUPABASE_URL` and `SUPABASE_KEY` are correct
- Ensure table exists with correct schema
- Check Supabase project is active (not paused)

### Scraping Timeouts
- Increase delays in scraper
- Split brands into multiple cron jobs
- Use `TEST_MODE=2` to reduce load

### No Data in Supabase
- Check Railway logs for errors
- Verify `USE_SUPABASE=true`
- Test Supabase connection manually

### File Not Found (url_list.json)
- Ensure file is committed to git
- Check Railway build logs for file structure

## Cost Estimation

**Railway (as of 2024):**
- Hobby: $5/month (500 hours)
- Pro: $20/month (more resources)
- Daily scraping (~1-2 hours) = ~30-60 hours/month ✅

**Supabase:**
- Free tier: 500MB database, 2GB bandwidth
- Should be sufficient for this use case ✅

## Support

For issues or questions:
- Check Railway logs first
- Verify all environment variables are set
- Test with `TEST_MODE=2` before full scraping
- Ensure Supabase table schema matches

## License

MIT
