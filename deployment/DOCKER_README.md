# Docker Deployment Guide

## Overview

This guide explains how to deploy the PLC Data Collector using Docker and Docker Compose.

## Prerequisites

- Docker installed and running
- Docker Compose installed
- Network access to your PLCs
- Supabase account and project

## Quick Start

### 1. Build the Docker Image

```bash
# Navigate to deployment directory
cd deployment

# Run the build script
./build.sh
```

### 2. Configure Environment

The build script will create a `.env` file from the template. Edit it with your Supabase credentials:

```bash
nano .env
```

Required variables:
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase anon key

### 3. Run the Application

**From deployment/ directory:**
```bash
# Interactive mode
docker-compose run --rm plc-collector

# Background mode
docker-compose up -d

# View logs
docker-compose logs -f plc-collector

# Stop container
docker-compose down
```

**From project root directory:**
```bash
# Interactive mode
docker-compose -f deployment/docker-compose.yml run --rm plc-collector

# Background mode
docker-compose -f deployment/docker-compose.yml up -d

# View logs
docker-compose -f deployment/docker-compose.yml logs -f plc-collector

# Stop container
docker-compose -f deployment/docker-compose.yml down
```

## Manual Docker Commands

### Build Image

```bash
# From project root
docker build -f deployment/Dockerfile -t plc-data-collector .
```

### Run Container

```bash
# Interactive mode
docker run -it --rm \
  --network host \
  -v $(pwd)/configs:/app/configs \
  -v $(pwd)/logs:/app/logs \
  -e SUPABASE_URL=your_url \
  -e SUPABASE_KEY=your_key \
  plc-data-collector

# Background mode
docker run -d \
  --name plc-data-collector \
  --restart unless-stopped \
  --network host \
  -v $(pwd)/configs:/app/configs \
  -v $(pwd)/logs:/app/logs \
  -e SUPABASE_URL=your_url \
  -e SUPABASE_KEY=your_key \
  plc-data-collector
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SUPABASE_URL` | Supabase project URL | Required |
| `SUPABASE_KEY` | Supabase anon key | Required |
| `DEFAULT_SCAN_RATE` | Default scan rate (seconds) | 1.0 |
| `HISTORICAL_DATA_RETENTION_DAYS` | Data retention period | 30 |
| `LOG_LEVEL` | Logging level | INFO |

### Volumes

- `./configs:/app/configs` - PLC configurations and tag lists
- `./logs:/app/logs` - Application logs

### Network

The container uses `host` network mode to access PLCs on the local network.

## Troubleshooting

### Common Issues

1. **Docker daemon not running**
   ```bash
   # Start Docker Desktop or Docker daemon
   sudo systemctl start docker  # Linux
   ```

2. **Permission denied on volumes**
   ```bash
   # Fix volume permissions
   sudo chown -R $USER:$USER configs logs
   ```

3. **Cannot connect to PLCs**
   - Ensure PLCs are on the same network
   - Check firewall settings (port 44818 for EtherNet/IP)
   - Verify PLC IP addresses

4. **Supabase connection errors**
   - Verify SUPABASE_URL and SUPABASE_KEY
   - Ensure Supabase tables are created (see main README)
   - Check Supabase project status

5. **SSL Certificate Warning** ⚠️
   - You may see `[SSL: CERTIFICATE_VERIFY_FAILED]` warning on startup
   - This is a known issue in Docker containers with Python's httpx library
   - The application will still function normally despite this warning
   - The warning appears during the initial connection test but doesn't affect operations
   - For production, ensure proper SSL certificate configuration

### Debugging

**From deployment/ directory:**
```bash
# Check container logs
docker-compose logs plc-collector

# Access container shell
docker-compose exec plc-collector bash

# Test database connection
docker-compose exec plc-collector python -c "from database_manager import SupabaseManager; SupabaseManager().test_connection()"
```

**From project root directory:**
```bash
# Check container logs
docker-compose -f deployment/docker-compose.yml logs plc-collector

# Access container shell
docker-compose -f deployment/docker-compose.yml exec plc-collector bash

# Test database connection
docker-compose -f deployment/docker-compose.yml exec plc-collector python -c "from database_manager import SupabaseManager; SupabaseManager().test_connection()"
```

## Production Deployment

### Security Considerations

1. **Environment Variables**
   - Use Docker secrets or external secret management
   - Never commit `.env` files with real credentials

2. **Network Security**
   - Use VPN for remote PLC access
   - Implement network segmentation
   - Consider using read-only PLC access

3. **Data Security**
   - Enable Supabase RLS (Row Level Security)
   - Use service role key instead of anon key for production
   - Implement data encryption at rest

### Scaling

For multiple PLCs or high-frequency data collection:

```yaml
# docker-compose.override.yml
version: '3.8'
services:
  plc-collector:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
    environment:
      - DEFAULT_SCAN_RATE=0.5
```

### Monitoring

Consider adding monitoring services:

```yaml
# Add to docker-compose.yml
services:
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-storage:/var/lib/grafana

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
```

## File Structure

```
deployment/
├── Dockerfile              # Container definition
├── docker-compose.yml      # Multi-container setup
├── .env.sample            # Environment template
├── build.sh               # Build script
└── DOCKER_README.md       # This file
```

## Support

For issues with Docker deployment:
1. Check this guide and the main README.md
2. Verify Docker and Docker Compose versions
3. Check container logs for error messages
4. Ensure all prerequisites are met
