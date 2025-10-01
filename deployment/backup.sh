#!/bin/bash

# PLC Data Collector Backup Script
# Automated backup for SQLite database and configuration files

BACKUP_DIR="/opt/backups/plc-collector"
DATE=$(date +%Y%m%d_%H%M%S)
PROJECT_DIR="/opt/plc-data-collector"

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

# Change to project directory
cd "$PROJECT_DIR" || {
    log_error "Cannot access project directory: $PROJECT_DIR"
    exit 1
}

log_info "Starting backup: $DATE"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup SQLite database
if [ -f "data/plc_data.db" ]; then
    log_info "Backing up SQLite database..."
    if command -v sqlite3 &> /dev/null; then
        sqlite3 data/plc_data.db ".backup $BACKUP_DIR/plc_data_$DATE.db"
        if [ $? -eq 0 ]; then
            log_success "Database backup completed"
        else
            log_error "Database backup failed"
        fi
    else
        log_warning "sqlite3 not found, copying database file instead"
        cp data/plc_data.db "$BACKUP_DIR/plc_data_$DATE.db"
    fi
else
    log_warning "SQLite database not found, skipping database backup"
fi

# Backup configuration files
log_info "Backing up configuration files..."
if [ -d "configs" ] || [ -f ".env" ] || [ -f "database_config.json" ]; then
    tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" configs/ .env database_config.json 2>/dev/null || {
        log_warning "Some configuration files may not exist, continuing..."
    }
    log_success "Configuration backup completed"
else
    log_warning "No configuration files found to backup"
fi

# Backup logs
log_info "Backing up logs..."
if [ -d "logs" ] && [ "$(ls -A logs 2>/dev/null)" ]; then
    tar -czf "$BACKUP_DIR/logs_$DATE.tar.gz" logs/ 2>/dev/null
    log_success "Logs backup completed"
else
    log_warning "No logs found to backup"
fi

# Cleanup old backups (keep 30 days)
log_info "Cleaning up old backups..."
find "$BACKUP_DIR" -name "*.db" -mtime +30 -delete 2>/dev/null
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete 2>/dev/null

# Show backup summary
echo ""
log_info "Backup Summary:"
echo "  Backup location: $BACKUP_DIR"
echo "  Backup date: $DATE"
echo "  Database backup: $([ -f "$BACKUP_DIR/plc_data_$DATE.db" ] && echo "✓ Success" || echo "✗ Failed")"
echo "  Config backup: $([ -f "$BACKUP_DIR/config_$DATE.tar.gz" ] && echo "✓ Success" || echo "✗ Failed")"
echo "  Logs backup: $([ -f "$BACKUP_DIR/logs_$DATE.tar.gz" ] && echo "✓ Success" || echo "✗ Failed")"

log_success "Backup completed: $DATE"
