# Quick Deployment Guide

## Option 1: Deploy to Render (Recommended)

### Steps:
1. **Push to GitHub**:
   ```bash
   cd /home/parvat-khattak/Downloads/Product-Importer
   git remote add origin https://github.com/YOUR_USERNAME/Product-Importer.git
   git branch -M main
   git push -u origin main
   ```

2. **Deploy on Render**:
   - Go to https://render.com
   - Sign up/login with GitHub
   - Click "New +" → "Blueprint"
   - Select your `Product-Importer` repository
   - Render will detect `render.yaml` automatically
   - Click "Apply"

3. **Wait for deployment** (~5-10 minutes)
   - Render will create:
     - Web service (FastAPI)
     - Worker service (Celery)
     - PostgreSQL database
     - Redis instance
   
4. **Access your app**: 
   - URL will be: `https://product-importer-web.onrender.com`

### Notes:
- Free tier services may take 30-60s to wake up from sleep
- Migrations run automatically during build
- Check logs in Render dashboard if issues occur

---

## Option 2: Deploy to Heroku

### Steps:
```bash
# Install Heroku CLI first
heroku login
heroku create product-importer-yourname

# Add databases
heroku addons:create heroku-postgresql:essential-0
heroku addons:create heroku-redis:mini

# Deploy
git push heroku main

# Run migrations
heroku run alembic upgrade head

# Scale worker
heroku ps:scale web=1 worker=1

# Open app
heroku open
```

---

## Option 3: Deploy to Railway

1. Go to https://railway.app
2. Click "New Project" → "Deploy from GitHub repo"
3. Select Product-Importer
4. Add PostgreSQL and Redis plugins
5. Set environment variables:
   - `DATABASE_URL` (auto-filled by PostgreSQL plugin)
   - `REDIS_URL` (auto-filled by Redis plugin)
6. Deploy!

---

## Local Testing First (Recommended)

Before deploying, test locally:

```bash
# Start services
docker-compose up -d

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Terminal 1: Start FastAPI
uvicorn backend.main:app --reload --port 8000

# Terminal 2: Start Celery worker
celery -A backend.celery_app worker --loglevel=info

# Open browser
# http://localhost:8000
```

### Test the application:
1. Upload `sample_products.csv`
2. Watch real-time progress
3. Browse products
4. Create a test webhook using https://webhook.site
5. Delete all products

---

## Environment Variables Needed

For deployment, set these:

```bash
DATABASE_URL=postgresql://user:pass@host:5432/dbname
REDIS_URL=redis://host:6379/0
ENVIRONMENT=production
CORS_ORIGINS=https://your-deployed-url.com
MAX_UPLOAD_SIZE_MB=100
CHUNK_SIZE=10000
```

Most platforms auto-set `DATABASE_URL` and `REDIS_URL`.

---

## Troubleshooting

### Build Fails
- Check Python version (3.11+)
- Verify requirements.txt is committed
- Check build logs for specific errors

### Database Connection Error
- Ensure DATABASE_URL is set correctly
- Run migrations: `alembic upgrade head`
- Check PostgreSQL is running

### Worker Not Processing
- Verify REDIS_URL is correct
- Check worker is running (`heroku ps` or Render dashboard)
- Look at worker logs

### Upload Progress Not Working
- Check browser console for SSE connection
- Verify CORS settings
- Ensure Redis is accessible

---

## Next Steps After Deployment

1. Test CSV upload with large file
2. Configure webhooks
3. Monitor performance in platform dashboard
4. Set up custom domain (optional)
5. Enable SSL (usually automatic)

---

**Ready to deploy!** Choose your platform and follow the steps above.
