#!/bin/bash

# Fix script for ubuntu_deploy.sh permission issues
# Run this script to fix the backup.sh permission error

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_info "Fixing ubuntu_deploy.sh permission issues..."

# Check if we're in the right directory
if [ ! -f "deployment/ubuntu_deploy.sh" ]; then
    log_error "Please run this script from the project root directory"
    exit 1
fi

# Make sure backup.sh and health_check.sh exist and are executable
if [ ! -f "deployment/backup.sh" ]; then
    log_error "backup.sh not found in deployment directory"
    exit 1
fi

if [ ! -f "deployment/health_check.sh" ]; then
    log_error "health_check.sh not found in deployment directory"
    exit 1
fi

# Make scripts executable
chmod +x deployment/backup.sh
chmod +x deployment/health_check.sh
chmod +x deployment/ubuntu_deploy.sh

log_success "Scripts made executable"

# Check if PROJECT_DIR exists and create it if needed
PROJECT_DIR="/opt/plc-data-collector"
if [ ! -d "$PROJECT_DIR" ]; then
    log_info "Creating project directory: $PROJECT_DIR"
    sudo mkdir -p "$PROJECT_DIR"
    sudo chown "$USER:$USER" "$PROJECT_DIR"
fi

# Create necessary subdirectories
sudo mkdir -p "$PROJECT_DIR"/{configs/plc_configs,configs/tag_lists,data,logs}
sudo chown -R "$USER:$USER" "$PROJECT_DIR"

log_success "Project directory structure created"

# Test if we can write to the project directory
if [ -w "$PROJECT_DIR" ]; then
    log_success "Project directory is writable"
else
    log_warning "Project directory may not be writable, fixing permissions..."
    sudo chown -R "$USER:$USER" "$PROJECT_DIR"
fi

log_success "Permission fixes completed!"
echo ""
log_info "You can now run the ubuntu_deploy.sh script:"
echo "  ./deployment/ubuntu_deploy.sh"
echo ""
log_info "Or if you prefer to run it with sudo:"
echo "  sudo ./deployment/ubuntu_deploy.sh"
