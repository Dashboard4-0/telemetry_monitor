# Ubuntu Deployment Quick Reference

## 🚀 Quick Start Commands

### Automated Deployment
```bash
# Make scripts executable
chmod +x deployment/*.sh

# Full automated deployment
./deployment/ubuntu_deploy.sh

# Docker-only deployment
./deployment/docker_deploy.sh
```

### Manual Docker Deployment
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Deploy application
cd deployment
./build.sh
docker compose up -d
```

### Manual Python Deployment
```bash
# Install dependencies
sudo apt update
sudo apt install -y python3 python3-pip python3-venv python3-dev

# Setup project
python3 -m venv venv
source venv/bin/activate
pip install -r deployment/requirements.txt

# Run application
python "Core Application/main.py"
```

## 📋 Database Configuration

### SQLite (Local)
```bash
# Create .env file
cat > .env << EOF
SQLITE_DB_PATH=./data/plc_data.db
DEFAULT_SCAN_RATE=1.0
HISTORICAL_DATA_RETENTION_DAYS=30
EOF
```

### Supabase (Cloud)
```bash
# Create .env file
cat > .env << EOF
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
DEFAULT_SCAN_RATE=1.0
HISTORICAL_DATA_RETENTION_DAYS=30
EOF
```

## 🔧 Service Management

### Systemd Service
```bash
# Start service
sudo systemctl start plc-collector

# Stop service
sudo systemctl stop plc-collector

# Restart service
sudo systemctl restart plc-collector

# View status
sudo systemctl status plc-collector

# View logs
sudo journalctl -u plc-collector -f
```

### Docker Service
```bash
# Start services
cd deployment && docker compose up -d

# Stop services
cd deployment && docker compose down

# Restart services
cd deployment && docker compose restart

# View logs
cd deployment && docker compose logs -f

# Interactive mode
cd deployment && docker compose run --rm plc-collector
```

## 📊 Monitoring Commands

### Health Checks
```bash
# Check service status
sudo systemctl is-active plc-collector

# Check Docker containers
docker compose ps

# Check database integrity (SQLite)
sqlite3 data/plc_data.db "PRAGMA integrity_check;"

# Check disk space
df -h

# Check memory usage
free -h
```

### Log Monitoring
```bash
# Systemd logs
sudo journalctl -u plc-collector -f

# Docker logs
docker compose logs -f plc-collector

# Application logs
tail -f logs/plc-collector.log
```

## 🔄 Backup & Recovery

### Backup Commands
```bash
# Manual backup
./backup.sh

# Database backup (SQLite)
sqlite3 data/plc_data.db ".backup data/plc_data_backup.db"

# Configuration backup
tar -czf config_backup.tar.gz configs/ .env
```

### Recovery Commands
```bash
# Restore SQLite database
cp data/plc_data_backup.db data/plc_data.db

# Restore configuration
tar -xzf config_backup.tar.gz

# Restart service
sudo systemctl restart plc-collector
```

## 🌐 Network Configuration

### PLC Network Setup
```bash
# Configure static IP
sudo tee /etc/netplan/01-netcfg.yaml > /dev/null << EOF
network:
  version: 2
  renderer: networkd
  ethernets:
    eth0:
      dhcp4: false
      addresses: [192.168.1.100/24]
      gateway4: 192.168.1.1
EOF

sudo netplan apply
```

### Firewall Configuration
```bash
# Enable firewall
sudo ufw enable

# Allow PLC communication
sudo ufw allow from 192.168.1.0/24 to any port 44818
sudo ufw allow from 192.168.1.0/24 to any port 2222

# Check status
sudo ufw status
```

## 🛠️ Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check service status
sudo systemctl status plc-collector

# Check logs
sudo journalctl -u plc-collector -n 50

# Check configuration
sudo systemctl cat plc-collector
```

#### Database Issues
```bash
# Check SQLite database
sqlite3 data/plc_data.db "PRAGMA integrity_check;"

# Check file permissions
ls -la data/plc_data.db

# Check disk space
df -h
```

#### Network Issues
```bash
# Test PLC connectivity
ping 192.168.1.10

# Test specific ports
telnet 192.168.1.10 44818

# Check routing
ip route show
```

#### Docker Issues
```bash
# Check container status
docker compose ps

# Check container logs
docker compose logs plc-collector

# Restart containers
docker compose restart
```

### Debug Mode
```bash
# Run with debug output
python "Core Application/main.py" --collect --verbose

# Enable Python debug mode
export PYTHONPATH="Core Application:$PYTHONPATH"
python -c "import logging; logging.basicConfig(level=logging.DEBUG)"
```

## 📁 Directory Structure

```
/opt/plc-data-collector/
├── Core Application/          # Application source code
├── deployment/               # Deployment files
│   ├── configs/             # PLC configurations
│   ├── logs/                # Application logs
│   └── data/                # SQLite database
├── venv/                    # Python virtual environment
├── .env                     # Environment configuration
└── database_config.json     # Database configuration
```

## 🔐 Security Checklist

- [ ] Service runs as non-root user
- [ ] Configuration files have restricted permissions (600)
- [ ] Firewall is configured
- [ ] Regular backups are scheduled
- [ ] Log rotation is configured
- [ ] Network access is restricted
- [ ] Database files are secured

## 📞 Support Commands

### System Information
```bash
# OS version
lsb_release -a

# Python version
python3 --version

# Docker version
docker --version

# Service status
sudo systemctl status plc-collector
```

### Application Information
```bash
# Check installed packages
pip list

# Check application version
python "Core Application/main.py" --version

# Check database statistics
python "Core Application/main.py" --stats
```

## 🚨 Emergency Procedures

### Service Recovery
```bash
# Stop all services
sudo systemctl stop plc-collector
docker compose down

# Check system resources
htop
df -h

# Restart services
sudo systemctl start plc-collector
docker compose up -d
```

### Data Recovery
```bash
# Restore from backup
cp /opt/backups/plc-collector/plc_data_*.db data/plc_data.db

# Verify integrity
sqlite3 data/plc_data.db "PRAGMA integrity_check;"

# Restart service
sudo systemctl restart plc-collector
```

This quick reference provides all the essential commands and procedures for deploying and managing the PLC Data Collector on Ubuntu systems.
