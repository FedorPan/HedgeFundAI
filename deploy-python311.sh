#!/bin/bash

echo "=============================================="
echo "HedgeFundAI Python 3.11 Deployment Script"
echo "=============================================="
echo "This script creates a deployment using DigitalOcean's command line"
echo "with explicit Python 3.11 configuration"

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

# Check for API keys
if [ -z "$FINNHUB_API_KEY" ] || [ -z "$OPENAI_API_KEY" ] || [ -z "$ALPACA_API_KEY" ] || [ -z "$ALPACA_API_SECRET" ]; then
  echo "⚠️ One or more API keys are not set. Please set all required environment variables:"
  echo "  - FINNHUB_API_KEY"
  echo "  - OPENAI_API_KEY"
  echo "  - ALPACA_API_KEY" 
  echo "  - ALPACA_API_SECRET"
  echo ""
  read -p "Do you want to continue anyway? (y/n) " -n 1 -r
  echo ""
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
  fi
fi

# Create a temporary directory to create app from scratch
TEMP_DIR=$(mktemp -d)
echo "Creating temporary deployment directory: $TEMP_DIR"

# Copy necessary files
cp -r src $TEMP_DIR/
cp requirements.txt $TEMP_DIR/
cp runtime.txt $TEMP_DIR/
cp setup.py $TEMP_DIR/
cp Procfile $TEMP_DIR/
mkdir -p $TEMP_DIR/.do
cp .do/build-do.sh $TEMP_DIR/.do/

# Create a temporary app.yaml with explicit Python 3.11 configuration
cat > $TEMP_DIR/.do/app.yaml << EOL
name: hedgefundai
services:
  - name: api
    build_command: bash .do/build-do.sh
    run_command: cd src/api && python3.11 run_api.py --port \${PORT:-8080}
    envs:
      - key: PYTHONPATH
        value: /app
      - key: PYTHON_VERSION
        value: "3.11.7"
      - key: FINNHUB_API_KEY
        value: "${FINNHUB_API_KEY:-placeholder}"
        type: SECRET
      - key: OPENAI_API_KEY
        value: "${OPENAI_API_KEY:-placeholder}"
        type: SECRET
      - key: ALPACA_API_KEY
        value: "${ALPACA_API_KEY:-placeholder}"
        type: SECRET
      - key: ALPACA_API_SECRET
        value: "${ALPACA_API_SECRET:-placeholder}"
        type: SECRET
      - key: ALPACA_BASE_URL
        value: "https://paper-api.alpaca.markets/v2"
    http_port: 8080
    instance_count: 1
    instance_size_slug: basic-xxs
    routes:
      - path: /
    source_dir: /
    environment_slug: python
EOL

# Create explicit runtime.txt in the temp directory
echo "python-3.11.7" > $TEMP_DIR/runtime.txt

# Create a .python-version file to emphasize Python 3.11
echo "3.11.7" > $TEMP_DIR/.python-version

# Create app using doctl
echo "🚀 Creating app with doctl from directory: $TEMP_DIR"
cd $TEMP_DIR
doctl apps create --spec .do/app.yaml

echo ""
echo "✅ App creation initiated!"
echo "Next steps:"
echo "1. Upload code using the DigitalOcean web UI or CLI"
echo "2. Verify Python 3.11 is used by checking build logs"
echo "3. Access your app via the URL provided in the DigitalOcean App Platform dashboard"
echo "=============================================="

# Clean up
cd -
echo "Temporary directory created at: $TEMP_DIR"
echo "You can delete it when you no longer need it." 