#!/bin/bash

echo "Component Update Tool"
echo "===================="
echo ""
echo "Available components:"
echo "1. Header (weather, times, branding)"
echo "2. AccountCards (portfolio, cash, power)"
echo "3. PortfolioChart (performance graph)"
echo "4. MarketData (SPY, QQQ, etc)"
echo "5. PositionsTable (current positions)"
echo "6. StatusBar (footer status)"
echo ""
read -p "Which component to update? (1-6): " choice

COMPONENTS=("Header" "AccountCards" "PortfolioChart" "MarketData" "PositionsTable" "StatusBar")
COMPONENT=${COMPONENTS[$choice-1]}

if [ -z "$COMPONENT" ]; then
  echo "Invalid choice"
  exit 1
fi

echo "Editing: components/modules/${COMPONENT}.tsx"
echo "Current version: $(jq -r ".components.${COMPONENT}" components/versions.json)"

# Open in editor
code components/modules/${COMPONENT}.tsx

echo ""
echo "After editing, run:"
echo "  npm run dev    # Test locally"
echo "  npm run build  # Build for production"
echo ""