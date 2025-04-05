#!/bin/bash
set -e

echo "Python version before modification:"
python --version

# Try to install Python 3.11 if it's not the current version
PYTHON_VERSION=$(python --version 2>&1)
if [[ $PYTHON_VERSION != *"3.11"* ]]; then
  echo "Current Python version is not 3.11, attempting to install Python 3.11..."
  
  # Check if we're on Ubuntu/Debian
  if command -v apt-get &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y python3.11 python3.11-venv python3.11-dev
    
    # Create symbolic links if needed
    if [ ! -f /usr/bin/python3.11 ]; then
      echo "Python 3.11 not found after installation attempt."
      exit 1
    fi
    
    # Use Python 3.11 for the build
    sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1
    sudo update-alternatives --set python /usr/bin/python3.11
  else
    echo "Unsupported OS for Python version installation."
    exit 1
  fi
fi

echo "Python version after modification:"
python --version

echo "Installing dependencies..."
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
python -m pip install -e .

echo "Build completed successfully" 