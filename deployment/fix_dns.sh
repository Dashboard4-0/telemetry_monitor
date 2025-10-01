#!/bin/bash

# Script to restart Docker container after DNS change

echo "======================================"
echo "   Restarting Docker Container"
echo "======================================"
echo ""

cd /Users/tomcotham/telemetry_monitor/deployment

echo "Stopping container..."
docker-compose down

echo ""
echo "Starting container..."
docker-compose up -d

echo ""
echo "Waiting for container to start..."
sleep 3

echo ""
echo "Container logs:"
docker-compose logs --tail=20

echo ""
echo "======================================"
echo "   Container Restarted!"
echo "======================================"
echo ""
echo "If Supabase connection still fails, try:"
echo "  1. Flush DNS cache: sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder"
echo "  2. Restart Docker Desktop"
echo ""

