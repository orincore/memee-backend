# Render.com Deployment Guide

## Overview
This guide will help you deploy your Memee backend to Render.com successfully.

## Files Created for Deployment

1. **`render_startup.py`** - Startup script that properly handles Render's PORT environment variable
2. **`render.yaml`** - Render configuration file (optional, for automatic deployment)
3. **`Procfile`** - Alternative deployment method

## Deployment Steps

### Method 1: Manual Deployment (Recommended)

1. **Push your code to GitHub** (if not already done)
   ```bash
   git add .
   git commit -m "Add Render deployment files"
   git push origin main
   ```

2. **Create a new Web Service on Render.com**
   - Go to [render.com](https://render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select your repository

3. **Configure the service:**
   - **Name**: `memee-backend` (or any name you prefer)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python render_startup.py`
   - **Plan**: Free (or paid if you prefer)

4. **Set Environment Variables**
   Add all your environment variables in the Render dashboard:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `CLOUDINARY_CLOUD_NAME`
   - `CLOUDINARY_API_KEY`
   - `CLOUDINARY_API_SECRET`
   - `REDDIT_CLIENT_ID`
   - `REDDIT_CLIENT_SECRET`
   - `REDDIT_USER_AGENT`
   - `GEMINI_API_KEY`
   - `INSTA_USERNAME`
   - `INSTA_PASSWORD`
   - `SMTP_HOST`
   - `SMTP_PORT`
   - `SMTP_USER`
   - `SMTP_PASSWORD`
   - `EMAIL_FROM`
   - `ALLOWED_ORIGINS` (set to `*` for now)
   - `SCHEDULER_ENABLED` (set to `true`)

5. **Deploy**
   - Click "Create Web Service"
   - Render will automatically build and deploy your app

### Method 2: Using render.yaml (Automatic)

If you want automatic deployment configuration:

1. **Push the `render.yaml` file to your repository**
2. **Create a new Web Service**
3. **Select "Use render.yaml"** when creating the service
4. **Set your environment variables** (they won't be auto-configured for security)

## Troubleshooting

### Port Binding Issues
If you still get port binding errors:

1. **Check the logs** in Render dashboard
2. **Verify the startup command** is `python render_startup.py`
3. **Ensure uvicorn is installed** (it's in requirements.txt)

### Environment Variables
- Make sure all required environment variables are set
- Check that sensitive values are correct
- Verify Supabase and Cloudinary credentials work

### Build Issues
- Check that `requirements.txt` is in the root directory
- Verify Python version compatibility
- Check build logs for dependency conflicts

## Testing Your Deployment

Once deployed, test these endpoints:

1. **Health Check**: `https://your-app-name.onrender.com/`
2. **API Docs**: `https://your-app-name.onrender.com/docs`
3. **Feed**: `https://your-app-name.onrender.com/memes/feed`

## Important Notes

1. **Free Tier Limitations**:
   - Services sleep after 15 minutes of inactivity
   - Limited bandwidth and compute
   - Consider upgrading for production use

2. **Environment Variables**:
   - Never commit sensitive data to your repository
   - Use Render's environment variable system
   - Test locally with `.env` file

3. **Database**:
   - Ensure your Supabase database is accessible from Render
   - Check IP restrictions if any

4. **Scheduler**:
   - The meme scheduler will run on Render
   - Free tier may have limitations on background tasks

## Next Steps

After successful deployment:

1. **Update your frontend** to use the new API URL
2. **Test all endpoints** thoroughly
3. **Monitor logs** for any issues
4. **Set up custom domain** if needed
5. **Configure SSL** (automatic on Render)

## Support

If you encounter issues:
1. Check Render's documentation
2. Review the build and runtime logs
3. Test locally to isolate issues
4. Contact Render support if needed 