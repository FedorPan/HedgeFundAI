#!/bin/bash
set -e

echo "DigitalOcean Build Script Starting"
echo "====================================="

# Check current Python version
echo "Current Python version:"
python --version

# Try to find or install Python 3.11
if command -v python3.11 &> /dev/null; then
    echo "Python 3.11 is already installed"
    PYTHON_CMD="python3.11"
else
    echo "Python 3.11 not found, trying to install via apt..."
    
    # Remove sudo if we're already root (likely in DigitalOcean)
    if [ "$(id -u)" -eq 0 ]; then
        APT_PREFIX=""
    else
        APT_PREFIX="sudo"
    fi
    
    # Update package lists
    $APT_PREFIX apt-get update -y
    
    # Add deadsnakes PPA if needed
    $APT_PREFIX apt-get install -y software-properties-common
    $APT_PREFIX add-apt-repository -y ppa:deadsnakes/ppa
    $APT_PREFIX apt-get update -y
    
    # Install Python 3.11
    $APT_PREFIX apt-get install -y python3.11 python3.11-dev python3.11-distutils python3.11-venv
    
    if command -v python3.11 &> /dev/null; then
        echo "Python 3.11 installed successfully"
        PYTHON_CMD="python3.11"
    else
        echo "Failed to install Python 3.11, exiting"
        exit 1
    fi
fi

# Install pip for Python 3.11 if needed
if ! $PYTHON_CMD -m pip --version &> /dev/null; then
    echo "Installing pip for Python 3.11..."
    curl -sS https://bootstrap.pypa.io/get-pip.py | $PYTHON_CMD
fi

echo "Using Python at: $($PYTHON_CMD -c 'import sys; print(sys.executable)')"
$PYTHON_CMD --version

echo "====================================="
echo "Installing dependencies..."
$PYTHON_CMD -m pip install --upgrade pip setuptools wheel
$PYTHON_CMD -m pip install -r requirements.txt
$PYTHON_CMD -m pip install -e .

echo "Build completed successfully" 