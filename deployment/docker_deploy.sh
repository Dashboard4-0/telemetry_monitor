#!/bin/bash

# Docker Deployment Script for PLC Data Collector on Ubuntu
# Automated Docker setup and deployment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="plc-data-collector"
COMPOSE_FILE="deployment/docker-compose.yml"

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

check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        log_info "Run: curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh"
        exit 1
    fi
    
    if ! command -v docker compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    log_success "Docker and Docker Compose are available"
}

setup_directories() {
    log_info "Setting up directories..."
    
    mkdir -p deployment/{configs,logs,data}
    mkdir -p deployment/configs/{plc_configs,tag_lists}
    
    log_success "Directories created"
}

configure_environment() {
    log_info "Configuring environment..."
    
    if [ -f "deployment/.env" ]; then
        log_warning "Environment file already exists. Backing up..."
        cp deployment/.env deployment/.env.backup.$(date +%Y%m%d_%H%M%S)
    fi
    
    echo ""
    echo "Choose your database configuration:"
    echo "1) SQLite (Local file database - Simple setup)"
    echo "2) Supabase (Cloud database - Requires internet)"
    echo "3) Skip configuration (configure manually later)"
    echo ""
    read -p "Enter your choice (1, 2, or 3): " db_choice
    
    case $db_choice in
        1)
            log_info "Configuring SQLite database..."
            cat > deployment/.env << EOF
# SQLite Configuration
SQLITE_DB_PATH=/app/data/plc_data.db

# Application Settings
DEFAULT_SCAN_RATE=1.0
HISTORICAL_DATA_RETENTION_DAYS=30
DOCKER_ENV=true
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
            
            cat > deployment/.env << EOF
# Supabase Configuration
SUPABASE_URL=$supabase_url
SUPABASE_KEY=$supabase_key

# Application Settings
DEFAULT_SCAN_RATE=1.0
HISTORICAL_DATA_RETENTION_DAYS=30
DOCKER_ENV=true
EOF
            log_success "Supabase configuration created"
            ;;
        3)
            log_info "Skipping environment configuration"
            ;;
        *)
            log_error "Invalid choice"
            exit 1
            ;;
    esac
}

build_image() {
    log_info "Building Docker image..."
    
    cd deployment
    docker compose build
    
    if [ $? -eq 0 ]; then
        log_success "Docker image built successfully"
    else
        log_error "Docker build failed"
        exit 1
    fi
    
    cd ..
}

start_services() {
    log_info "Starting services..."
    
    cd deployment
    
    # Start in background
    docker compose up -d
    
    # Wait for services to start
    sleep 5
    
    # Check if services are running
    if docker compose ps | grep -q "Up"; then
        log_success "Services started successfully"
    else
        log_error "Services failed to start"
        docker compose logs
        exit 1
    fi
    
    cd ..
}

show_status() {
    log_info "Service Status:"
    cd deployment
    docker compose ps
    cd ..
    
    echo ""
    log_info "Recent logs:"
    cd deployment
    docker compose logs --tail=20
    cd ..
    
    echo ""
    log_info "Useful commands:"
    echo "  View logs:     cd deployment && docker compose logs -f"
    echo "  Restart:       cd deployment && docker compose restart"
    echo "  Stop:          cd deployment && docker compose down"
    echo "  Interactive:   cd deployment && docker compose run --rm plc-collector"
    echo "  Shell access:  cd deployment && docker compose exec plc-collector bash"
}

setup_monitoring() {
    log_info "Setting up monitoring..."
    
    # Create monitoring script
    cat > monitor.sh << 'EOF'
#!/bin/bash

# PLC Data Collector Docker Monitoring Script

COMPOSE_FILE="deployment/docker-compose.yml"

check_services() {
    echo "=== Service Status ==="
    docker compose -f $COMPOSE_FILE ps
    
    echo ""
    echo "=== Resource Usage ==="
    docker stats --no-stream
    
    echo ""
    echo "=== Recent Logs ==="
    docker compose -f $COMPOSE_FILE logs --tail=10
}

check_database() {
    echo "=== Database Check ==="
    
    # Check if SQLite database exists and is accessible
    if docker compose -f $COMPOSE_FILE exec plc-collector test -f /app/data/plc_data.db; then
        echo "✓ SQLite database file exists"
        
        # Check database integrity
        if docker compose -f $COMPOSE_FILE exec plc-collector sqlite3 /app/data/plc_data.db "PRAGMA integrity_check;" | grep -q "ok"; then
            echo "✓ SQLite database integrity check passed"
        else
            echo "✗ SQLite database integrity check failed"
        fi
    else
        echo "⚠ SQLite database file not found"
    fi
}

check_disk_space() {
    echo "=== Disk Space ==="
    df -h | grep -E "(Filesystem|/dev/)"
    
    # Check Docker disk usage
    echo ""
    echo "=== Docker Disk Usage ==="
    docker system df
}

# Main monitoring function
case "${1:-all}" in
    services)
        check_services
        ;;
    database)
        check_database
        ;;
    disk)
        check_disk_space
        ;;
    all)
        check_services
        echo ""
        check_database
        echo ""
        check_disk_space
        ;;
    *)
        echo "Usage: $0 [services|database|disk|all]"
        exit 1
        ;;
esac
EOF
    
    chmod +x monitor.sh
    
    log_success "Monitoring script created: ./monitor.sh"
}

setup_backup() {
    log_info "Setting up backup..."
    
    # Create backup script
    cat > backup.sh << 'EOF'
#!/bin/bash

# PLC Data Collector Docker Backup Script

BACKUP_DIR="/opt/backups/plc-collector"
DATE=$(date +%Y%m%d_%H%M%S)
COMPOSE_FILE="deployment/docker-compose.yml"

mkdir -p $BACKUP_DIR

echo "Starting backup: $DATE"

# Backup SQLite database
if docker compose -f $COMPOSE_FILE exec plc-collector test -f /app/data/plc_data.db; then
    echo "Backing up SQLite database..."
    docker compose -f $COMPOSE_FILE exec plc-collector sqlite3 /app/data/plc_data.db ".backup /tmp/plc_data_$DATE.db"
    docker compose -f $COMPOSE_FILE cp plc-collector:/tmp/plc_data_$DATE.db $BACKUP_DIR/
    docker compose -f $COMPOSE_FILE exec plc-collector rm /tmp/plc_data_$DATE.db
    echo "✓ Database backup completed"
else
    echo "⚠ SQLite database not found, skipping database backup"
fi

# Backup configuration files
echo "Backing up configuration files..."
tar -czf $BACKUP_DIR/config_$DATE.tar.gz deployment/configs/ deployment/.env deployment/database_config.json 2>/dev/null || true
echo "✓ Configuration backup completed"

# Backup logs
echo "Backing up logs..."
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz deployment/logs/ 2>/dev/null || true
echo "✓ Logs backup completed"

# Cleanup old backups (keep 30 days)
echo "Cleaning up old backups..."
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
echo "Backup location: $BACKUP_DIR"
EOF
    
    chmod +x backup.sh
    
    # Setup cron job for automated backup
    echo "0 2 * * * $(pwd)/backup.sh" | sudo crontab -
    
    log_success "Backup script created: ./backup.sh"
}

setup_network() {
    log_info "Setting up network configuration..."
    
    # Check if running in host network mode
    if grep -q "network_mode: host" deployment/docker-compose.yml; then
        log_info "Container is configured to use host network mode"
        log_info "This allows direct access to PLC network interfaces"
        
        # Check network interfaces
        echo ""
        echo "Available network interfaces:"
        ip addr show | grep -E "^[0-9]+:|inet " | grep -v "127.0.0.1"
        
        echo ""
        log_info "Make sure your PLCs are accessible from this network interface"
    else
        log_warning "Container is not using host network mode"
        log_warning "You may need to configure port forwarding for PLC communication"
    fi
}

# Main deployment function
deploy() {
    log_info "Starting Docker deployment for PLC Data Collector..."
    
    check_docker
    setup_directories
    configure_environment
    build_image
    start_services
    setup_monitoring
    setup_backup
    setup_network
    show_status
    
    log_success "Docker deployment completed successfully!"
    
    echo ""
    log_info "Next steps:"
    echo "1. Configure your PLCs using the interactive mode:"
    echo "   cd deployment && docker compose run --rm plc-collector"
    echo ""
    echo "2. Monitor the application:"
    echo "   ./monitor.sh"
    echo ""
    echo "3. View logs:"
    echo "   cd deployment && docker compose logs -f"
    echo ""
    echo "4. Backup data:"
    echo "   ./backup.sh"
}

# Handle command line arguments
case "${1:-deploy}" in
    deploy)
        deploy
        ;;
    status)
        show_status
        ;;
    restart)
        log_info "Restarting services..."
        cd deployment
        docker compose restart
        cd ..
        log_success "Services restarted"
        ;;
    stop)
        log_info "Stopping services..."
        cd deployment
        docker compose down
        cd ..
        log_success "Services stopped"
        ;;
    logs)
        cd deployment
        docker compose logs -f
        ;;
    shell)
        cd deployment
        docker compose exec plc-collector bash
        ;;
    *)
        echo "Usage: $0 [deploy|status|restart|stop|logs|shell]"
        echo ""
        echo "Commands:"
        echo "  deploy   - Full deployment (default)"
        echo "  status   - Show service status"
        echo "  restart  - Restart services"
        echo "  stop     - Stop services"
        echo "  logs     - View logs"
        echo "  shell    - Access container shell"
        exit 1
        ;;
esac
