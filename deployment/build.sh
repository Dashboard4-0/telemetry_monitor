#!/bin/bash

# PLC Data Collector - Docker Build Script

echo "======================================"
echo "   PLC Data Collector Docker Build    "
echo "======================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "✗ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "✗ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✓ Docker and Docker Compose are available"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.sample .env
    echo "✓ Created .env file"
    echo ""
    echo "IMPORTANT: Edit the .env file with your Supabase credentials:"
    echo "  - SUPABASE_URL"
    echo "  - SUPABASE_KEY"
    echo ""
    read -p "Would you like to edit .env now? (y/n): " edit_env
    if [ "$edit_env" = "y" ]; then
        ${EDITOR:-nano} .env
    fi
else
    echo "✓ .env file already exists"
fi

# Build the Docker image
echo ""
echo "Building Docker image..."
cd ..
docker-compose -f deployment/docker-compose.yml build

if [ $? -eq 0 ]; then
    echo "✓ Docker image built successfully"
else
    echo "✗ Docker build failed"
    exit 1
fi

echo ""
echo "======================================"
echo "        Build Complete!               "
echo "======================================"
echo ""
echo "Next steps (choose one):"
echo ""
echo "📍 From deployment/ directory:"
echo "  docker-compose up -d                    # Start in background"
echo "  docker-compose run --rm plc-collector  # Run interactively"
echo "  docker-compose down                    # Stop container"
echo ""
echo "📍 From project root directory:"
echo "  docker-compose -f deployment/docker-compose.yml up -d"
echo "  docker-compose -f deployment/docker-compose.yml run --rm plc-collector"
echo "  docker-compose -f deployment/docker-compose.yml down"
echo ""
