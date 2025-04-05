#!/bin/bash

echo "=============================================="
echo "HedgeFundAI Deployment Script"
echo "=============================================="
echo "This script will guide you through the process of deploying the HedgeFundAI application to DigitalOcean App Platform."
echo ""

# Check for API keys
if [ -z "$FINNHUB_API_KEY" ]; then
  echo "⚠️ FINNHUB_API_KEY is not set. Please set this environment variable before deploying."
  echo "You can get an API key from https://finnhub.io/"
  echo "export FINNHUB_API_KEY=your_key_here"
  echo ""
fi

if [ -z "$OPENAI_API_KEY" ]; then
  echo "⚠️ OPENAI_API_KEY is not set. Please set this environment variable before deploying."
  echo "You can get an API key from https://platform.openai.com/api-keys"
  echo "export OPENAI_API_KEY=your_key_here"
  echo ""
fi

if [ -z "$ALPACA_API_KEY" ] || [ -z "$ALPACA_API_SECRET" ]; then
  echo "⚠️ ALPACA_API_KEY or ALPACA_API_SECRET is not set. Please set these environment variables before deploying."
  echo "You can get API keys from https://app.alpaca.markets/paper/dashboard/overview"
  echo "export ALPACA_API_KEY=your_key_here"
  echo "export ALPACA_API_SECRET=your_secret_here"
  echo ""
fi

echo "IMPORTANT: This application requires Python 3.11 due to pandas compatibility issues with Python 3.13."
echo "We've configured the deployment to use Python 3.11, but if you encounter issues,"
echo "please check the logs and make sure Python 3.11 is being used."
echo ""

# Check if doctl is installed
if ! command -v doctl &> /dev/null; then
  echo "❌ 'doctl' command not found. Please install the DigitalOcean CLI tool."
  echo "Installation instructions: https://docs.digitalocean.com/reference/doctl/how-to/install/"
  exit 1
fi

# Check if doctl is authenticated
if ! doctl account get &> /dev/null; then
  echo "❌ 'doctl' is not authenticated. Please run 'doctl auth init' and follow the instructions."
  exit 1
fi

# Deploy the app
echo "🚀 Deploying to DigitalOcean App Platform..."
doctl apps create --spec .do/app.yaml

echo ""
echo "✅ Deployment initiated! Check the DigitalOcean dashboard for build progress."
echo "You'll be able to access your application once the build completes."
echo "Remember: The app uses Python 3.11 with our custom build script to ensure compatibility."
echo "==============================================" 