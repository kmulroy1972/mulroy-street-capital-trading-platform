#!/bin/bash
TIMESTAMP=$(date +%s)
URL="https://www.mulroystreetcap.com?v=$TIMESTAMP"

echo "Testing Enhanced Dashboard..."
echo "URL: $URL"
echo ""

# Test for enhanced components
echo -n "Enhanced Header: "
curl -s "$URL" | grep -q "MSC TERMINAL\|EnhancedHeader" && echo "✅ Found" || echo "❌ Not Found"

echo -n "Weather API calls: "
curl -s "$URL" | grep -q "weather" && echo "✅ Found" || echo "❌ Not Found"

echo -n "Market data: "
curl -s "$URL" | grep -q "market" && echo "✅ Found" || echo "❌ Not Found"

echo ""
echo "API Endpoints:"
curl -s https://mulroystreetcap.com/api/weather/dc | jq -r '"DC Weather: \(.temp_f)°F"'
curl -s https://mulroystreetcap.com/api/market-times | jq -r 'keys | "Market Times: \(join(", "))"'

echo ""
echo "Test in browser with cache bypass:"
echo "1. Open: $URL"
echo "2. Hard refresh: Cmd+Shift+R (Mac) or Ctrl+F5 (PC)"
echo "3. Or use Incognito/Private mode"