#!/bin/bash

# PLC Data Collector Health Check Script
# Monitors service status, database integrity, and system resources

PROJECT_DIR="/opt/plc-data-collector"
SERVICE_NAME="plc-collector"

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

check_services() {
    echo "=== Service Status ==="
    
    # Check systemd service
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log_success "PLC Collector service is running"
        systemctl status "$SERVICE_NAME" --no-pager -l
    else
        log_error "PLC Collector service is not running"
        systemctl status "$SERVICE_NAME" --no-pager -l
    fi
    
    echo ""
    echo "=== Docker Services (if applicable) ==="
    if command -v docker &> /dev/null; then
        cd "$PROJECT_DIR/deployment" 2>/dev/null && {
            if docker compose ps 2>/dev/null | grep -q "plc-collector"; then
                docker compose ps
            else
                log_info "No Docker services found"
            fi
        } || log_info "Docker deployment directory not found"
    else
        log_info "Docker not installed"
    fi
}

check_database() {
    echo ""
    echo "=== Database Check ==="
    
    cd "$PROJECT_DIR" || {
        log_error "Cannot access project directory: $PROJECT_DIR"
        return 1
    }
    
    # Check SQLite database
    if [ -f "data/plc_data.db" ]; then
        log_success "SQLite database file exists"
        
        # Check database integrity
        if command -v sqlite3 &> /dev/null; then
            if sqlite3 data/plc_data.db "PRAGMA integrity_check;" | grep -q "ok"; then
                log_success "SQLite database integrity check passed"
                
                # Get database statistics
                echo ""
                echo "Database Statistics:"
                sqlite3 data/plc_data.db "SELECT 'Historical Records:', COUNT(*) FROM plc_data_historical;"
                sqlite3 data/plc_data.db "SELECT 'Real-time Records:', COUNT(*) FROM plc_data_realtime;"
            else
                log_error "SQLite database integrity check failed"
            fi
        else
            log_warning "sqlite3 command not found, cannot check database integrity"
        fi
        
        # Check file permissions
        echo ""
        echo "Database file info:"
        ls -la data/plc_data.db
    else
        log_warning "SQLite database file not found"
    fi
    
    # Check database configuration
    if [ -f "database_config.json" ]; then
        log_success "Database configuration file exists"
        echo "Database type: $(jq -r '.database_type // "unknown"' database_config.json 2>/dev/null || echo "unknown")"
    else
        log_warning "Database configuration file not found"
    fi
}

check_system_resources() {
    echo ""
    echo "=== System Resources ==="
    
    # Check disk space
    echo "Disk Usage:"
    df -h | grep -E "(Filesystem|/dev/)" | head -5
    
    # Check if project directory disk usage is high
    PROJECT_USAGE=$(df "$PROJECT_DIR" | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$PROJECT_USAGE" -gt 90 ]; then
        log_error "Disk usage is ${PROJECT_USAGE}% - CRITICAL"
    elif [ "$PROJECT_USAGE" -gt 80 ]; then
        log_warning "Disk usage is ${PROJECT_USAGE}% - WARNING"
    else
        log_success "Disk usage is ${PROJECT_USAGE}% - OK"
    fi
    
    echo ""
    echo "Memory Usage:"
    free -h
    
    echo ""
    echo "CPU Load:"
    uptime
}

check_logs() {
    echo ""
    echo "=== Recent Logs ==="
    
    # Check systemd logs
    echo "Systemd Service Logs (last 10 lines):"
    journalctl -u "$SERVICE_NAME" -n 10 --no-pager
    
    # Check application logs
    if [ -d "$PROJECT_DIR/logs" ] && [ "$(ls -A "$PROJECT_DIR/logs" 2>/dev/null)" ]; then
        echo ""
        echo "Application Logs (last 5 lines):"
        tail -5 "$PROJECT_DIR/logs"/*.log 2>/dev/null || log_info "No application log files found"
    fi
    
    # Check Docker logs if applicable
    if command -v docker &> /dev/null; then
        cd "$PROJECT_DIR/deployment" 2>/dev/null && {
            if docker compose ps 2>/dev/null | grep -q "plc-collector"; then
                echo ""
                echo "Docker Container Logs (last 5 lines):"
                docker compose logs --tail=5 plc-collector 2>/dev/null
            fi
        }
    fi
}

check_network() {
    echo ""
    echo "=== Network Check ==="
    
    # Check network interfaces
    echo "Network Interfaces:"
    ip addr show | grep -E "^[0-9]+:|inet " | grep -v "127.0.0.1"
    
    # Check if service is listening on expected ports
    echo ""
    echo "Listening Ports:"
    ss -tlnp | grep -E ":(22|44818|2222)" || log_info "No expected ports found listening"
}

# Main health check function
main() {
    case "${1:-all}" in
        services)
            check_services
            ;;
        database)
            check_database
            ;;
        resources)
            check_system_resources
            ;;
        logs)
            check_logs
            ;;
        network)
            check_network
            ;;
        all)
            check_services
            check_database
            check_system_resources
            check_logs
            check_network
            ;;
        *)
            echo "Usage: $0 [services|database|resources|logs|network|all]"
            echo ""
            echo "Health check options:"
            echo "  services  - Check service status"
            echo "  database  - Check database integrity"
            echo "  resources - Check system resources"
            echo "  logs      - Check recent logs"
            echo "  network   - Check network status"
            echo "  all       - Run all checks (default)"
            exit 1
            ;;
    esac
    
    echo ""
    log_info "Health check completed at $(date)"
}

# Run main function
main "$@"
