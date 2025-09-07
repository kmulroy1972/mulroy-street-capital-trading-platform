#!/bin/bash

echo "Monitoring Enhanced Dashboard..."
echo ""

# Check main page loads
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://www.mulroystreetcap.com)
echo "Dashboard HTTP: $HTTP_CODE"

# Check API endpoints
echo ""
echo "API Status:"
curl -s https://mulroystreetcap.com/api/weather/dc | jq '{location: "DC", temp: .temp_f}'
curl -s https://mulroystreetcap.com/api/market-times | jq 'keys'

echo ""
echo "If any issues, run: ./restore-stable.sh"