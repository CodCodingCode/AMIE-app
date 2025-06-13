# Backend Deployment Guide

## Quick Start with Railway (Recommended)

1. **Sign up for Railway**
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub

2. **Deploy Your Backend**
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Set the root directory to `3d/Backend`
   - Railway will automatically detect it's a Python app

3. **Set Environment Variables**
   - In Railway dashboard, go to your project
   - Click "Variables" tab
   - Add these variables:
     ```
     OPENAI_API_KEY=your_openai_api_key_here
     FLASK_ENV=production
     ```

4. **Get Your Backend URL**
   - After deployment, Railway will provide a URL like: `https://your-app-name.railway.app`
   - Copy this URL for the next step

## Alternative: Deploy with Render

1. **Sign up for Render**
   - Go to [render.com](https://render.com)
   - Sign up with GitHub

2. **Create Web Service**
   - Click "New" → "Web Service"
   - Connect your GitHub repository
   - Set these settings:
     - Root Directory: `3d/Backend`
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `python app.py`

3. **Set Environment Variables**
   - In Render dashboard, add:
     ```
     OPENAI_API_KEY=your_openai_api_key_here
     FLASK_ENV=production
     ```

## Update Frontend Configuration

After deploying your backend:

1. **Update API Configuration**
   - Open `3d/Frontend/src/app/lib/api-config.ts`
   - Replace `https://your-backend-app.railway.app` with your actual backend URL

2. **Update CORS Settings**
   - Open `3d/Backend/app.py`
   - Replace the placeholder domains in CORS configuration with your actual Vercel domain

3. **Set Environment Variables in Vercel**
   - In Vercel dashboard, go to your project settings
   - Add environment variable:
     ```
     NEXT_PUBLIC_API_URL=https://your-backend-url.railway.app
     ```

## Testing the Connection

1. **Local Testing**
   ```bash
   # Terminal 1 - Start backend
   cd 3d/Backend
   python app.py
   
   # Terminal 2 - Start frontend
   cd 3d/Frontend
   npm run dev
   ```

2. **Production Testing**
   - Deploy both frontend and backend
   - Test file upload functionality
   - Check browser console for any CORS errors

## Troubleshooting

### CORS Errors
- Make sure your Vercel domain is added to CORS origins in backend
- Check that FLASK_ENV is set to 'production' in your backend deployment

### Environment Variables
- Ensure OPENAI_API_KEY is set in backend
- Ensure NEXT_PUBLIC_API_URL is set in frontend

### File Upload Issues
- Check that your backend URL is correct
- Verify the backend is running and accessible
- Test the API endpoint directly: `https://your-backend-url.railway.app/api/process-file`

## Security Notes

- Never commit API keys to version control
- Use environment variables for all sensitive data
- Consider implementing rate limiting for production use
- Monitor your OpenAI API usage to avoid unexpected costs 