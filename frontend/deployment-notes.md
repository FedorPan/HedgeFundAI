# Deployment to Vercel

Follow these steps to deploy your HedgeFundAI frontend to Vercel:

## Prerequisites

1. Create a [Vercel account](https://vercel.com/signup) if you don't have one
2. Install the Vercel CLI:
   ```bash
   npm install -g vercel
   ```

## Backend API Deployment

Before deploying the frontend, you need to deploy your backend API to a service like:
- Heroku
- DigitalOcean
- AWS
- Railway
- Render

Once your backend API is deployed, note down the URL (e.g., `https://your-api.herokuapp.com`).

## Frontend Deployment

### Step 1: Update configuration

Edit the `vercel.json` file to update the API URL:

```json
{
  "rewrites": [
    {
      "source": "/api/backend/:path*",
      "destination": "https://your-api.herokuapp.com/:path*"
    }
  ],
  "env": {
    "NEXT_PUBLIC_API_URL": "https://your-api.herokuapp.com"
  },
  "buildCommand": "npm run build",
  "installCommand": "npm install",
  "framework": "nextjs"
}
```

### Step 2: Deploy with Vercel CLI

Run the following commands from the frontend directory:

```bash
# Login to Vercel
vercel login

# Deploy to Vercel
vercel
```

Follow the prompts to complete the deployment.

### Step 3: Verify deployment

Once deployed, verify that:
1. The frontend is accessible at the Vercel URL
2. The frontend can connect to your API via the `/api/backend` proxy
3. All data is loading correctly

## Environment Variables

If you need to configure additional environment variables, you can do so:

1. Via the Vercel dashboard
2. By adding them to the `vercel.json` file
3. Through the Vercel CLI when deploying

## Troubleshooting

- If you see CORS errors, ensure your backend API allows requests from your Vercel domain
- If API requests fail, check the browser's network tab to see the exact error messages
- For issues with the API proxy, check the Vercel logs for detailed error information

## Local Development After Deployment

To test locally with the deployed API:

1. Update `.env.local` file:
   ```
   NEXT_PUBLIC_API_URL=https://your-api.herokuapp.com
   ```

2. Run development server:
   ```bash
   npm run dev
   ``` 