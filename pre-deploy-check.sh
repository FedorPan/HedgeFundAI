#!/bin/bash

echo "=============================================="
echo "HedgeFundAI Pre-Deployment Check"
echo "=============================================="
echo "This script will check your environment for compatibility issues before deployment."

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python --version 2>&1)

if [[ $PYTHON_VERSION == *"3.11"* ]]; then
  echo "✅ Python 3.11 detected, which is compatible with this project."
elif [[ $PYTHON_VERSION == *"3.13"* ]]; then
  echo "❌ Python 3.13 detected. This version is NOT compatible with pandas 2.0.3 used in this project."
  echo "Please install Python 3.11 for development or use our deployment script which handles this automatically."
  echo "For local development: pyenv install 3.11.7 && pyenv local 3.11.7"
else
  echo "⚠️ Python version $PYTHON_VERSION detected."
  echo "This project is developed and tested with Python 3.11."
  echo "Other versions may work but are not officially supported."
fi

# Check API keys
echo ""
echo "Checking required API keys..."

if [ -z "$FINNHUB_API_KEY" ]; then
  echo "❌ FINNHUB_API_KEY is not set."
  echo "Get an API key from https://finnhub.io/"
else
  echo "✅ FINNHUB_API_KEY is set."
fi

if [ -z "$OPENAI_API_KEY" ]; then
  echo "❌ OPENAI_API_KEY is not set."
  echo "Get an API key from https://platform.openai.com/api-keys"
else
  echo "✅ OPENAI_API_KEY is set."
fi

if [ -z "$ALPACA_API_KEY" ] || [ -z "$ALPACA_API_SECRET" ]; then
  echo "❌ ALPACA_API_KEY or ALPACA_API_SECRET is not set."
  echo "Get API keys from https://app.alpaca.markets/paper/dashboard/overview"
else
  echo "✅ ALPACA API keys are set."
fi

# Check required files for deployment
echo ""
echo "Checking deployment files..."

if [ -f ".do/app.yaml" ]; then
  echo "✅ DigitalOcean app configuration (.do/app.yaml) exists."
else
  echo "❌ DigitalOcean app configuration (.do/app.yaml) is missing."
fi

if [ -f ".do/build-do.sh" ]; then
  echo "✅ Custom build script (.do/build-do.sh) exists."
else
  echo "❌ Custom build script (.do/build-do.sh) is missing."
fi

if [ -f "runtime.txt" ]; then
  echo "✅ Python runtime specification (runtime.txt) exists."
else
  echo "❌ Python runtime specification (runtime.txt) is missing."
fi

if [ -f "requirements.txt" ]; then
  echo "✅ Python dependencies (requirements.txt) exist."
else
  echo "❌ Python dependencies (requirements.txt) are missing."
fi

echo ""
echo "Pre-deployment check complete. Address any issues before deploying."
echo "Run ./deploy.sh when you're ready to deploy to DigitalOcean."
echo "==============================================" 