# Quick Start - Railway Deployment

## 🚀 Deploy in 5 Minutes

### Step 1: Supabase Setup (2 min)
1. Go to https://supabase.com and create a project
2. Run this SQL in SQL Editor:
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
```
3. Copy your credentials from Settings > API:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY` (anon/public key)

### Step 2: Deploy to Railway (1 min)
1. Go to https://railway.app/new
2. Click "Deploy from GitHub repo"
3. Select: `dieg0espx/Cronjob-Scrapper-BadAssBBQS`
4. Railway will automatically deploy!

### Step 3: Set Environment Variables (1 min)
In Railway Dashboard > Variables, add:
```
TEST_MODE=0
USE_SCHEDULE=true
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOi...your_key_here
```

### Step 4: Configure Cron (1 min)
In Railway Dashboard > Settings > Cron:
- Schedule: `0 0 * * *` (daily at midnight UTC)
- Save

## ✅ Done!

Your scraper will now run automatically every day at midnight UTC and scrape 3 brands per day.

## 📅 Schedule

- **Monday:** Alfresco, American Made, American Outdoor
- **Tuesday:** Artisan, Blackstone, Blaze
- **Wednesday:** Breeo, Bromic, Coyote
- **Thursday:** Delta, Fire Magic, Fontana
- **Friday:** Green Mountain, Napoleon, Twin Eagles
- **Saturday:** Primo, Summerset, Mont Alpi
- **Sunday:** American Fyre, Outdoor Plus, Ledge Lounger

## 🔍 Verify It's Working

**Check Railway Logs:**
- Go to Railway Dashboard > Deployments > Logs
- You should see the scraper running and uploading products

**Check Supabase:**
```sql
SELECT brand, COUNT(*) as products
FROM scrapped_products2
GROUP BY brand
ORDER BY products DESC;
```

## 🛠️ Troubleshooting

**No products in database?**
- Check Railway logs for errors
- Verify environment variables are set correctly
- Make sure the cron schedule is configured

**Need help?**
See detailed guides:
- `RAILWAY_DEPLOYMENT_CHECKLIST.md` - Complete checklist
- `DEPLOY.md` - Full deployment guide
- `SCHEDULE.md` - Weekly brand schedule

## 💰 Cost

- **Railway Hobby:** $5/month (500 hours included)
- **Supabase Free:** Perfect for this use case
- **Monthly usage:** ~15-30 hours ✅
