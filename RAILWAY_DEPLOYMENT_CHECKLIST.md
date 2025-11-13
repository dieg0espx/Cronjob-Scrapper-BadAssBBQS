# Railway Deployment Checklist

## Pre-Deployment Checklist

### 1. Files Ready ✓
- [x] `index.py` - Main entry point
- [x] `light_scraper.py` - Scraper with scheduling
- [x] `upload_to_db.py` - Database uploader
- [x] `url_list.json` - 21 brands list
- [x] `requirements.txt` - Python dependencies
- [x] `Procfile` - Updated to run `index.py`
- [x] `railway.json` - Railway configuration
- [x] `runtime.txt` - Python 3.11
- [x] `.gitignore` - Excludes .env and products.json
- [x] `SCHEDULE.md` - Weekly brand schedule
- [x] `DEPLOY.md` - Deployment guide

### 2. Git Repository
```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Ready for Railway deployment with daily scheduling"

# Create GitHub repo and push
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

### 3. Supabase Setup
- [ ] Create Supabase project
- [ ] Create `scrapped_products2` table (see schema below)
- [ ] Copy `SUPABASE_URL` from Settings > API
- [ ] Copy `SUPABASE_ANON_KEY` from Settings > API

#### Database Schema
```sql
CREATE TABLE scrapped_products2 (
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

-- Indexes for performance
CREATE INDEX idx_scrapped_products2_brand ON scrapped_products2(brand);
CREATE INDEX idx_scrapped_products2_url ON scrapped_products2(url);
CREATE INDEX idx_scrapped_products2_created_at ON scrapped_products2(created_at);
```

### 4. Railway Deployment
1. Go to https://railway.app/new
2. Click "Deploy from GitHub repo"
3. Select your repository
4. Railway will auto-detect Python and deploy

### 5. Environment Variables in Railway
Go to Railway Dashboard > Variables and add:

```
TEST_MODE=0
USE_SCHEDULE=true
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGc...
EMAIL_FROM=noreplybadassbbqs@gmail.com
EMAIL_PASSWORD=muyyqzqzfswadrzz
EMAIL_TO=your_email@example.com
```

**Important:**
- Use `SUPABASE_ANON_KEY` (not `SUPABASE_KEY`)
- `EMAIL_PASSWORD` is a Gmail App Password (not your regular password)

### 6. Set Up Cron Job
In Railway Dashboard:
1. Click on your service
2. Go to "Settings" tab
3. Under "Cron", add schedule: `0 0 * * *`
   (Runs daily at midnight UTC)

### 7. Testing
After deployment:

1. **Check Logs:**
   - Railway Dashboard > Deployments > Logs
   - Should see: "BBQ SCRAPER - FULL PIPELINE"
   - Should see: "Schedule mode: ENABLED"
   - Should see: "Today is [Day]"
   - Should see: "Assigned brands for today: [brands]"

2. **Verify Database:**
   ```sql
   -- Check if data is being inserted
   SELECT brand, COUNT(*) as product_count, MAX(created_at) as last_scraped
   FROM scrapped_products2
   GROUP BY brand
   ORDER BY last_scraped DESC;
   ```

3. **Test Different Days:**
   The scraper automatically detects the day of the week:
   - **Monday:** Alfresco, American Made, American Outdoor
   - **Tuesday:** Artisan, Blackstone, Blaze
   - **Wednesday:** Breeo, Bromic, Coyote
   - **Thursday:** Delta, Fire Magic, Fontana
   - **Friday:** Green Mountain, Napoleon, Twin Eagles
   - **Saturday:** Primo, Summerset, Mont Alpi
   - **Sunday:** American Fyre, Outdoor Plus, Ledge Lounger

## Troubleshooting

### Issue: "ModuleNotFoundError"
**Solution:** Check that `requirements.txt` is in the repository

### Issue: "Missing Supabase credentials"
**Solution:** Verify environment variables are set correctly in Railway

### Issue: "No products scraped"
**Solution:**
- Check Railway logs for errors
- Verify `USE_SCHEDULE=true` is set
- Confirm today's brands exist in `url_list.json`

### Issue: Cron job not running
**Solution:**
- Check Railway Settings > Cron schedule is set
- Verify the cron expression is correct: `0 0 * * *`
- Check Railway logs at expected run time

## Monitoring

### Daily Checks
```sql
-- Today's scraping progress
SELECT brand, COUNT(*) as products_today
FROM scrapped_products2
WHERE created_at >= CURRENT_DATE
GROUP BY brand;

-- Total products per brand
SELECT brand, COUNT(*) as total_products
FROM scrapped_products2
GROUP BY brand
ORDER BY total_products DESC;
```

### Weekly Overview
```sql
-- Products scraped this week
SELECT
  DATE(created_at) as date,
  COUNT(*) as products_scraped,
  COUNT(DISTINCT brand) as brands_scraped
FROM scrapped_products2
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

## Cost Estimate

**Railway:**
- Runs ~30-60 minutes/day
- ~15-30 hours/month
- Hobby plan ($5/month) = 500 hours ✅

**Supabase:**
- Free tier sufficient for this use case ✅
- 500MB database
- 2GB bandwidth/month

## Support

If you encounter issues:
1. Check Railway logs first
2. Verify all environment variables
3. Test Supabase connection manually
4. Review `DEPLOY.md` for detailed troubleshooting
