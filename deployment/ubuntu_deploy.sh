#!/bin/bash

# Ubuntu Deployment Script for PLC Data Collector
# This script automates the deployment process on Ubuntu systems

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/opt/plc-data-collector"
SERVICE_USER="plc-collector"
SERVICE_NAME="plc-collector"
REPO_URL="https://github.com/your-org/plc-data-collector.git"  # Update this URL

# Functions
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

check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "This script should not be run as root"
        exit 1
    fi
}

check_ubuntu() {
    if ! grep -q "Ubuntu" /etc/os-release; then
        log_error "This script is designed for Ubuntu systems"
        exit 1
    fi
    
    UBUNTU_VERSION=$(grep VERSION_ID /etc/os-release | cut -d'"' -f2)
    log_info "Detected Ubuntu $UBUNTU_VERSION"
}

install_dependencies() {
    log_info "Installing system dependencies..."
    
    sudo apt update
    sudo apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        git \
        curl \
        wget \
        gcc \
        build-essential \
        libffi-dev \
        libssl-dev \
        ca-certificates \
        gnupg \
        lsb-release
    
    log_success "System dependencies installed"
}

install_docker() {
    log_info "Installing Docker and Docker Compose..."
    
    # Add Docker's official GPG key
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Add Docker repository
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker
    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # Add user to docker group
    sudo usermod -aG docker $USER
    
    log_success "Docker installed (logout/login required for group changes)"
}

setup_project() {
    log_info "Setting up project directory..."
    
    # Create project directory
    sudo mkdir -p $PROJECT_DIR
    sudo chown $USER:$USER $PROJECT_DIR
    
    # Clone repository (or copy files)
    if [ -d ".git" ]; then
        log_info "Copying current project to $PROJECT_DIR"
        cp -r . $PROJECT_DIR/
    else
        log_info "Cloning repository to $PROJECT_DIR"
        git clone $REPO_URL $PROJECT_DIR
    fi
    
    cd $PROJECT_DIR
    
    # Create necessary directories
    mkdir -p {configs/plc_configs,configs/tag_lists,data,logs}
    
    # Make scripts executable
    chmod +x deployment/*.sh
    
    log_success "Project setup complete"
}

setup_python_environment() {
    log_info "Setting up Python environment..."
    
    cd $PROJECT_DIR
    
    # Create virtual environment
    python3 -m venv venv
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install Python dependencies
    pip install -r deployment/requirements.txt
    
    log_success "Python environment setup complete"
}

configure_database() {
    log_info "Configuring database..."
    
    cd $PROJECT_DIR
    
    echo ""
    echo "Choose your database option:"
    echo "1) SQLite (Local file database - Simple setup)"
    echo "2) Supabase (Cloud database - Requires internet)"
    echo ""
    read -p "Enter your choice (1 or 2): " db_choice
    
    case $db_choice in
        1)
            log_info "Configuring SQLite database..."
            cat > .env << EOF
# SQLite Configuration
SQLITE_DB_PATH=$PROJECT_DIR/data/plc_data.db

# Application Settings
DEFAULT_SCAN_RATE=1.0
HISTORICAL_DATA_RETENTION_DAYS=30
EOF
            log_success "SQLite configuration created"
            ;;
        2)
            log_info "Configuring Supabase database..."
            echo ""
            echo "You'll need your Supabase project URL and API key."
            echo "Get these from: https://app.supabase.com → Your Project → Settings → API"
            echo ""
            read -p "Enter Supabase URL: " supabase_url
            read -p "Enter Supabase API Key: " supabase_key
            
            cat > .env << EOF
# Supabase Configuration
SUPABASE_URL=$supabase_url
SUPABASE_KEY=$supabase_key

# Application Settings
DEFAULT_SCAN_RATE=1.0
HISTORICAL_DATA_RETENTION_DAYS=30
EOF
            log_success "Supabase configuration created"
            ;;
        *)
            log_error "Invalid choice"
            exit 1
            ;;
    esac
}

create_service_user() {
    log_info "Creating service user..."
    
    # Create service user if it doesn't exist
    if ! id "$SERVICE_USER" &>/dev/null; then
        sudo useradd -r -s /bin/false -d $PROJECT_DIR $SERVICE_USER
        log_success "Service user created: $SERVICE_USER"
    else
        log_info "Service user already exists: $SERVICE_USER"
    fi
    
    # Set ownership
    sudo chown -R $SERVICE_USER:$SERVICE_USER $PROJECT_DIR
}

create_systemd_service() {
    log_info "Creating systemd service..."
    
    sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null << EOF
[Unit]
Description=PLC Data Collector Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python "Core Application/main.py" --collect
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$PROJECT_DIR

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    log_success "Systemd service created"
}

setup_logging() {
    log_info "Setting up log rotation..."
    
    sudo tee /etc/logrotate.d/$SERVICE_NAME > /dev/null << EOF
$PROJECT_DIR/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 $SERVICE_USER $SERVICE_USER
}
EOF
    
    log_success "Log rotation configured"
}

setup_backup() {
    log_info "Setting up automated backup..."
    
    # Create backup script
    cat > $PROJECT_DIR/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups/plc-collector"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup SQLite database
if [ -f "data/plc_data.db" ]; then
    sqlite3 data/plc_data.db ".backup $BACKUP_DIR/plc_data_$DATE.db"
fi

# Backup configuration
tar -czf $BACKUP_DIR/config_$DATE.tar.gz configs/ .env database_config.json

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
EOF
    
    chmod +x $PROJECT_DIR/backup.sh
    
    # Setup cron job
    echo "0 2 * * * $PROJECT_DIR/backup.sh" | sudo crontab -u $SERVICE_USER -
    
    log_success "Automated backup configured"
}

setup_monitoring() {
    log_info "Setting up monitoring..."
    
    # Create health check script
    cat > $PROJECT_DIR/health_check.sh << 'EOF'
#!/bin/bash

# Check if service is running
if ! systemctl is-active --quiet plc-collector; then
    echo "ERROR: PLC Collector service is not running"
    exit 1
fi

# Check database connectivity
if [ -f "data/plc_data.db" ]; then
    if ! sqlite3 data/plc_data.db "SELECT 1;" > /dev/null 2>&1; then
        echo "ERROR: SQLite database is not accessible"
        exit 1
    fi
fi

# Check disk space
DISK_USAGE=$(df $PROJECT_DIR | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 90 ]; then
    echo "WARNING: Disk usage is ${DISK_USAGE}%"
fi

echo "OK: All checks passed"
EOF
    
    chmod +x $PROJECT_DIR/health_check.sh
    
    log_success "Monitoring configured"
}

start_service() {
    log_info "Starting PLC Data Collector service..."
    
    # Enable and start service
    sudo systemctl enable $SERVICE_NAME
    sudo systemctl start $SERVICE_NAME
    
    # Wait a moment and check status
    sleep 3
    if systemctl is-active --quiet $SERVICE_NAME; then
        log_success "Service started successfully"
    else
        log_error "Service failed to start"
        sudo systemctl status $SERVICE_NAME
        exit 1
    fi
}

show_status() {
    log_info "Service Status:"
    sudo systemctl status $SERVICE_NAME --no-pager
    
    echo ""
    log_info "Recent logs:"
    sudo journalctl -u $SERVICE_NAME -n 10 --no-pager
    
    echo ""
    log_info "Useful commands:"
    echo "  View logs:     sudo journalctl -u $SERVICE_NAME -f"
    echo "  Restart:       sudo systemctl restart $SERVICE_NAME"
    echo "  Stop:          sudo systemctl stop $SERVICE_NAME"
    echo "  Status:        sudo systemctl status $SERVICE_NAME"
    echo "  Health check:  $PROJECT_DIR/health_check.sh"
}

# Main deployment function
deploy() {
    log_info "Starting PLC Data Collector deployment on Ubuntu..."
    
    check_root
    check_ubuntu
    
    echo ""
    echo "Choose deployment method:"
    echo "1) Native Python installation (Recommended for servers)"
    echo "2) Docker installation (Recommended for development)"
    echo ""
    read -p "Enter your choice (1 or 2): " deploy_choice
    
    case $deploy_choice in
        1)
            install_dependencies
            setup_project
            setup_python_environment
            configure_database
            create_service_user
            create_systemd_service
            setup_logging
            setup_backup
            setup_monitoring
            start_service
            show_status
            ;;
        2)
            install_dependencies
            install_docker
            setup_project
            configure_database
            log_warning "Docker installation complete. Please logout/login to use Docker commands."
            log_info "To start the application:"
            echo "  cd $PROJECT_DIR/deployment"
            echo "  docker compose up -d"
            ;;
        *)
            log_error "Invalid choice"
            exit 1
            ;;
    esac
    
    log_success "Deployment completed successfully!"
}

# Run deployment
deploy
