# Ubuntu Deployment Plan - PLC Data Collector

## Overview

This guide provides detailed instructions for deploying the PLC Data Collector with dual database support (Supabase/SQLite) on Ubuntu systems. The deployment supports both Docker and native Python installations.

## Prerequisites

### System Requirements
- **Ubuntu**: 20.04 LTS or later (recommended: 22.04 LTS)
- **RAM**: Minimum 2GB, Recommended 4GB+
- **Storage**: Minimum 10GB free space
- **Network**: Access to PLCs and internet (for Supabase option)

### Hardware Requirements
- **CPU**: x86_64 architecture
- **Network**: Ethernet connection to PLC network
- **Optional**: Serial/USB connections for direct PLC communication

## Deployment Options

Choose the deployment method that best fits your environment:

1. **[Docker Deployment](#docker-deployment)** - Recommended for production
2. **[Native Python Deployment](#native-python-deployment)** - Recommended for development
3. **[Systemd Service Deployment](#systemd-service-deployment)** - Recommended for servers

---

## Docker Deployment

### Step 1: Install Docker and Docker Compose

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add user to docker group (logout/login required)
sudo usermod -aG docker $USER

# Verify installation
docker --version
docker compose version
```

### Step 2: Clone and Setup Project

```bash
# Clone repository (adjust URL as needed)
git clone <repository-url> plc-data-collector
cd plc-data-collector

# Make scripts executable
chmod +x deployment/*.sh

# Create necessary directories
mkdir -p deployment/{configs,logs,data}
mkdir -p deployment/configs/{plc_configs,tag_lists}
```

### Step 3: Configure Database

#### Option A: SQLite (Simple Setup)
```bash
# Create .env file for SQLite
cat > deployment/.env << EOF
# SQLite Configuration
SQLITE_DB_PATH=/app/data/plc_data.db

# Application Settings
DEFAULT_SCAN_RATE=1.0
HISTORICAL_DATA_RETENTION_DAYS=30
DOCKER_ENV=true
EOF
```

#### Option B: Supabase (Cloud Setup)
```bash
# Create .env file for Supabase
cat > deployment/.env << EOF
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-key-here

# Application Settings
DEFAULT_SCAN_RATE=1.0
HISTORICAL_DATA_RETENTION_DAYS=30
DOCKER_ENV=true
EOF
```

### Step 4: Build and Deploy

```bash
# Build Docker image
cd deployment
./build.sh

# Start application in background
docker compose up -d

# View logs
docker compose logs -f plc-collector

# Stop application
docker compose down
```

### Step 5: Configure PLCs (Interactive)

```bash
# Run interactive setup
docker compose run --rm plc-collector

# Or attach to running container
docker compose exec plc-collector python main.py
```

---

## Native Python Deployment

### Step 1: Install Python and Dependencies

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Python 3.10+ and pip
sudo apt install -y python3 python3-pip python3-venv python3-dev

# Install system dependencies
sudo apt install -y gcc build-essential libffi-dev libssl-dev

# Verify Python version (should be 3.8+)
python3 --version
```

### Step 2: Setup Project Environment

```bash
# Clone repository
git clone <repository-url> plc-data-collector
cd plc-data-collector

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
pip install -r deployment/requirements.txt
```

### Step 3: Configure Database

#### Option A: SQLite Setup
```bash
# Create data directory
mkdir -p data

# Create .env file
cat > .env << EOF
# SQLite Configuration
SQLITE_DB_PATH=./data/plc_data.db

# Application Settings
DEFAULT_SCAN_RATE=1.0
HISTORICAL_DATA_RETENTION_DAYS=30
EOF
```

#### Option B: Supabase Setup
```bash
# Create .env file
cat > .env << EOF
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-key-here

# Application Settings
DEFAULT_SCAN_RATE=1.0
HISTORICAL_DATA_RETENTION_DAYS=30
EOF
```

### Step 4: Run Application

```bash
# Activate virtual environment
source venv/bin/activate

# Run application
python "Core Application/main.py"

# Or run with specific commands
python "Core Application/main.py" --collect  # Start data collection
python "Core Application/main.py" --list      # List configured PLCs
```

---

## Systemd Service Deployment

### Step 1: Create Service User

```bash
# Create dedicated user for the service
sudo useradd -r -s /bin/false plc-collector
sudo mkdir -p /opt/plc-data-collector
sudo chown plc-collector:plc-collector /opt/plc-data-collector
```

### Step 2: Install Application

```bash
# Clone and setup application
sudo git clone <repository-url> /opt/plc-data-collector
cd /opt/plc-data-collector

# Install Python dependencies
sudo python3 -m venv venv
sudo venv/bin/pip install -r deployment/requirements.txt

# Set ownership
sudo chown -R plc-collector:plc-collector /opt/plc-data-collector
```

### Step 3: Create Systemd Service

```bash
# Create service file
sudo tee /etc/systemd/system/plc-collector.service > /dev/null << EOF
[Unit]
Description=PLC Data Collector Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=plc-collector
Group=plc-collector
WorkingDirectory=/opt/plc-data-collector
Environment=PATH=/opt/plc-data-collector/venv/bin
ExecStart=/opt/plc-data-collector/venv/bin/python "Core Application/main.py" --collect
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/plc-data-collector

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
sudo systemctl daemon-reload
```

### Step 4: Configure Database

```bash
# Create configuration as service user
sudo -u plc-collector bash -c 'cd /opt/plc-data-collector && cat > .env << EOF
# SQLite Configuration (adjust as needed)
SQLITE_DB_PATH=/opt/plc-data-collector/data/plc_data.db

# Application Settings
DEFAULT_SCAN_RATE=1.0
HISTORICAL_DATA_RETENTION_DAYS=30
EOF'
```

### Step 5: Start Service

```bash
# Enable and start service
sudo systemctl enable plc-collector
sudo systemctl start plc-collector

# Check status
sudo systemctl status plc-collector

# View logs
sudo journalctl -u plc-collector -f

# Stop service
sudo systemctl stop plc-collector
```

---

## Database-Specific Setup

### Supabase Database Setup

#### 1. Create Supabase Project
```bash
# Visit https://supabase.com and create new project
# Note down your project URL and API key
```

#### 2. Setup Database Schema
```bash
# Copy schema file content
cat deployment/supabase_schema.sql

# Paste and run in Supabase SQL Editor
# Or use Supabase CLI (if installed)
supabase db reset
```

#### 3. Configure Environment
```bash
# Add to .env file
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-key-here
```

### SQLite Database Setup

#### 1. Create Data Directory
```bash
# Create directory for SQLite database
mkdir -p data
chmod 755 data
```

#### 2. Configure Environment
```bash
# Add to .env file
SQLITE_DB_PATH=./data/plc_data.db
```

#### 3. Test Database Creation
```bash
# Run application to create database
python "Core Application/main.py"
# Database will be created automatically on first run
```

---

## Network Configuration

### PLC Network Access

#### 1. Configure Network Interface
```bash
# Check network interfaces
ip addr show

# Configure static IP (if needed)
sudo tee /etc/netplan/01-netcfg.yaml > /dev/null << EOF
network:
  version: 2
  renderer: networkd
  ethernets:
    eth0:
      dhcp4: false
      addresses: [192.168.1.100/24]  # Adjust IP/subnet
      gateway4: 192.168.1.1
      nameservers:
        addresses: [8.8.8.8, 8.8.4.4]
EOF

# Apply configuration
sudo netplan apply
```

#### 2. Test PLC Connectivity
```bash
# Test network connectivity to PLCs
ping 192.168.1.10  # Replace with PLC IP

# Test specific ports (if needed)
telnet 192.168.1.10 44818  # EtherNet/IP port
```

### Firewall Configuration

```bash
# Configure UFW firewall
sudo ufw enable

# Allow SSH (if needed)
sudo ufw allow ssh

# Allow PLC communication (adjust ports as needed)
sudo ufw allow from 192.168.1.0/24 to any port 44818
sudo ufw allow from 192.168.1.0/24 to any port 2222

# Check status
sudo ufw status
```

---

## Monitoring and Maintenance

### Log Management

#### Docker Deployment
```bash
# View application logs
docker compose logs -f plc-collector

# View logs with timestamps
docker compose logs -t plc-collector

# Rotate logs (add to crontab)
echo "0 0 * * * docker compose logs --since 24h plc-collector > /var/log/plc-collector-\$(date +\%Y\%m\%d).log" | sudo crontab -
```

#### Native Python Deployment
```bash
# Create log directory
mkdir -p logs

# Run with logging
python "Core Application/main.py" --collect 2>&1 | tee logs/plc-collector.log

# Setup log rotation
sudo tee /etc/logrotate.d/plc-collector > /dev/null << EOF
/opt/plc-data-collector/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 plc-collector plc-collector
}
EOF
```

### Database Maintenance

#### SQLite Maintenance
```bash
# Backup SQLite database
cp data/plc_data.db data/plc_data_backup_$(date +%Y%m%d).db

# Optimize database
sqlite3 data/plc_data.db "VACUUM;"

# Check database integrity
sqlite3 data/plc_data.db "PRAGMA integrity_check;"
```

#### Supabase Maintenance
```bash
# Use Supabase dashboard for maintenance
# Or use Supabase CLI
supabase db dump --data-only > backup_$(date +%Y%m%d).sql
```

### Performance Monitoring

```bash
# Monitor system resources
htop

# Monitor disk usage
df -h

# Monitor network traffic
iftop

# Monitor application processes
ps aux | grep python
```

---

## Troubleshooting

### Common Issues

#### 1. Permission Errors
```bash
# Fix file permissions
sudo chown -R $USER:$USER /opt/plc-data-collector
chmod +x deployment/*.sh
```

#### 2. Network Connectivity Issues
```bash
# Test network connectivity
ping 8.8.8.8
ping your-plc-ip

# Check routing table
ip route show

# Test DNS resolution
nslookup supabase.com
```

#### 3. Database Connection Issues

**SQLite Issues:**
```bash
# Check file permissions
ls -la data/plc_data.db

# Check disk space
df -h

# Test database integrity
sqlite3 data/plc_data.db "PRAGMA integrity_check;"
```

**Supabase Issues:**
```bash
# Test API connectivity
curl -H "apikey: YOUR_KEY" https://your-project.supabase.co/rest/v1/

# Check environment variables
echo $SUPABASE_URL
echo $SUPABASE_KEY
```

#### 4. Service Issues (Systemd)
```bash
# Check service status
sudo systemctl status plc-collector

# View detailed logs
sudo journalctl -u plc-collector -n 50

# Restart service
sudo systemctl restart plc-collector

# Check service configuration
sudo systemctl cat plc-collector
```

### Debug Mode

```bash
# Run with debug output
python "Core Application/main.py" --collect --verbose

# Enable Python debug mode
export PYTHONPATH="Core Application:$PYTHONPATH"
python -c "import logging; logging.basicConfig(level=logging.DEBUG)"
```

---

## Security Considerations

### 1. User Permissions
```bash
# Run as non-root user
sudo useradd -r -s /bin/false plc-collector
sudo chown -R plc-collector:plc-collector /opt/plc-data-collector
```

### 2. File Permissions
```bash
# Secure configuration files
chmod 600 .env
chmod 600 deployment/.env

# Secure data directory
chmod 755 data/
chmod 644 data/*.db
```

### 3. Network Security
```bash
# Use VPN for remote access
# Configure firewall rules
# Use HTTPS for Supabase connections
# Implement network segmentation
```

### 4. Backup Strategy
```bash
# Automated backup script
cat > backup.sh << EOF
#!/bin/bash
DATE=\$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups/plc-collector"

mkdir -p \$BACKUP_DIR

# Backup SQLite database
if [ -f "data/plc_data.db" ]; then
    cp data/plc_data.db \$BACKUP_DIR/plc_data_\$DATE.db
fi

# Backup configuration
tar -czf \$BACKUP_DIR/config_\$DATE.tar.gz configs/ .env

# Keep only last 7 days of backups
find \$BACKUP_DIR -name "*.db" -mtime +7 -delete
find \$BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
EOF

chmod +x backup.sh

# Add to crontab
echo "0 2 * * * /opt/plc-data-collector/backup.sh" | sudo crontab -
```

---

## Performance Optimization

### 1. System Optimization
```bash
# Increase file descriptor limits
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# Optimize kernel parameters
echo "net.core.rmem_max = 16777216" | sudo tee -a /etc/sysctl.conf
echo "net.core.wmem_max = 16777216" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### 2. Database Optimization

**SQLite Optimization:**
```bash
# Configure SQLite for better performance
sqlite3 data/plc_data.db << EOF
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = 10000;
PRAGMA temp_store = MEMORY;
EOF
```

**Supabase Optimization:**
- Use connection pooling
- Implement proper indexing
- Monitor query performance in Supabase dashboard

### 3. Application Optimization
```bash
# Set optimal environment variables
export PYTHONUNBUFFERED=1
export PYTHONOPTIMIZE=1

# Use Python optimization flags
python -O "Core Application/main.py"
```

---

## Backup and Recovery

### 1. Automated Backup Script
```bash
#!/bin/bash
# /opt/plc-data-collector/backup.sh

BACKUP_DIR="/opt/backups/plc-collector"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup SQLite database
if [ -f "data/plc_data.db" ]; then
    sqlite3 data/plc_data.db ".backup $BACKUP_DIR/plc_data_$DATE.db"
fi

# Backup configuration files
tar -czf $BACKUP_DIR/config_$DATE.tar.gz configs/ .env database_config.json

# Backup logs
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz logs/

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

### 2. Recovery Procedures

**SQLite Recovery:**
```bash
# Restore from backup
cp /opt/backups/plc-collector/plc_data_YYYYMMDD_HHMMSS.db data/plc_data.db

# Verify integrity
sqlite3 data/plc_data.db "PRAGMA integrity_check;"
```

**Configuration Recovery:**
```bash
# Restore configuration
tar -xzf /opt/backups/plc-collector/config_YYYYMMDD_HHMMSS.tar.gz
```

---

## Monitoring and Alerting

### 1. Health Check Script
```bash
#!/bin/bash
# /opt/plc-data-collector/health_check.sh

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
DISK_USAGE=$(df /opt/plc-data-collector | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 90 ]; then
    echo "WARNING: Disk usage is ${DISK_USAGE}%"
fi

echo "OK: All checks passed"
```

### 2. Log Monitoring
```bash
# Monitor for errors in logs
tail -f logs/plc-collector.log | grep -i error

# Setup log monitoring with fail2ban
sudo apt install fail2ban
sudo tee /etc/fail2ban/jail.local > /dev/null << EOF
[plc-collector]
enabled = true
port = 22
filter = plc-collector
logpath = /opt/plc-data-collector/logs/plc-collector.log
maxretry = 3
bantime = 3600
EOF
```

This comprehensive deployment plan covers all aspects of deploying the PLC Data Collector on Ubuntu, from basic installation to advanced monitoring and maintenance. Choose the deployment method that best fits your environment and requirements.
