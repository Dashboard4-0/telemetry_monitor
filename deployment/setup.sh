#!/bin/bash

# PLC Data Collector - Setup Script

echo "======================================"
echo "   PLC Data Collector Setup Script   "
echo "======================================"
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then 
    echo "✓ Python $python_version is installed (minimum 3.8 required)"
else
    echo "✗ Python 3.8 or higher is required. Current version: $python_version"
    exit 1
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip --quiet

# Install requirements
echo "Installing required packages..."
pip install -r deployment/requirements.txt

if [ $? -eq 0 ]; then
    echo "✓ All packages installed successfully"
else
    echo "✗ Failed to install some packages"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env file from template..."
    cp deployment/env.sample .env
    echo "✓ Created .env file"
    echo ""
    echo "IMPORTANT: The application now supports both Supabase and SQLite databases."
    echo "You can either:"
    echo "  1. Configure database settings in the .env file, OR"
    echo "  2. Run the application and use the interactive setup wizard"
    echo ""
    echo "For Supabase, configure:"
    echo "  - SUPABASE_URL"
    echo "  - SUPABASE_KEY"
    echo ""
    echo "For SQLite, configure:"
    echo "  - SQLITE_DB_PATH (optional, defaults to ./data/plc_data.db)"
    echo ""
    read -p "Would you like to edit .env now? (y/n): " edit_env
    if [ "$edit_env" = "y" ]; then
        ${EDITOR:-nano} .env
    fi
else
    echo "✓ .env file already exists"
fi

# Create directories
echo ""
echo "Creating configuration directories..."
mkdir -p configs/plc_configs
mkdir -p configs/tag_lists
mkdir -p data  # For SQLite database
echo "✓ Configuration directories created"

# Test imports
echo ""
echo "Testing imports..."
python3 -c "
try:
    import pycomm3
    import supabase
    import pandas
    import yaml
    print('✓ All imports successful')
except ImportError as e:
    print(f'✗ Import error: {e}')
    exit(1)
"

# Display next steps
echo ""
echo "======================================"
echo "        Setup Complete!               "
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your Supabase credentials"
echo "2. Create the required tables in Supabase (see README.md)"
echo "3. Run the application:"
echo "   source venv/bin/activate"
echo "   python main.py"
echo ""
echo "For more information, see README.md"
