# Deploying HedgeFundAI with Python 3.11 on DigitalOcean

Follow these steps to deploy HedgeFundAI through the DigitalOcean web UI:

## Prerequisites
1. A DigitalOcean account
2. Your API keys:
   - FINNHUB_API_KEY
   - OPENAI_API_KEY
   - ALPACA_API_KEY
   - ALPACA_API_SECRET

## Step 1: Create a New App

1. Log in to your DigitalOcean account
2. Go to the App Platform section
3. Click "Create App"
4. Choose your source (GitHub, GitLab, etc.)
5. Select your repository
6. Select the branch you want to deploy

## Step 2: Configure the App

1. Make sure "Autodeploy code changes" is selected (optional)
2. Edit the app name if needed
3. Select "Dockerfile" as the deployment method
4. Choose a basic plan (Basic or Professional) and instance size (Basic XXS is enough for testing)
5. Add the following environment variables:
   - `PYTHONPATH` = `/app`
   - `FINNHUB_API_KEY` = Your Finnhub API key (mark as encrypted)
   - `OPENAI_API_KEY` = Your OpenAI API key (mark as encrypted)
   - `ALPACA_API_KEY` = Your Alpaca API key (mark as encrypted)
   - `ALPACA_API_SECRET` = Your Alpaca API secret (mark as encrypted)
   - `ALPACA_BASE_URL` = `https://paper-api.alpaca.markets/v2`

6. Configure the HTTP port as `8080`

## Step 3: Deploy

1. Review your settings
2. Click "Create Resources"
3. Wait for the deployment to complete

## Step 4: Verify Deployment

1. Check the build logs to ensure Python 3.11 is being used
2. Once deployment is complete, click on the app URL
3. Add `/health` to the URL to verify the API is working (e.g., `https://your-app-url.ondigitalocean.app/health`)

## Troubleshooting

If you encounter issues:

1. Check the build logs for errors
2. Verify that the Dockerfile is being used (it specifies Python 3.11.7)
3. Make sure all required environment variables are set
4. If needed, adjust the configuration and redeploy

## Need to Update API Keys?

1. Go to your app in the DigitalOcean App Platform
2. Click on Settings
3. Navigate to the Environment Variables section
4. Update the values as needed
5. Click "Save" and redeploy if necessary 