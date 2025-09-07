#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Alpaca Trading System Test Suite${NC}"
echo -e "${GREEN}================================${NC}"

# Check if we're in the right directory
if [ ! -f "test_alpaca_connection.py" ]; then
    echo -e "${RED}Error: test_alpaca_connection.py not found${NC}"
    echo "Make sure you're in the alpaca-trader directory"
    exit 1
fi

# Check Python installation
echo -e "\n${YELLOW}Checking Python installation...${NC}"
python3.11 --version

# Check required packages
echo -e "\n${YELLOW}Checking required packages...${NC}"
python3.11 -c "import alpaca; print('✅ alpaca-py installed')" 2>/dev/null || echo "❌ alpaca-py not installed"
python3.11 -c "import httpx; print('✅ httpx installed')" 2>/dev/null || echo "❌ httpx not installed"
python3.11 -c "import redis; print('✅ redis installed')" 2>/dev/null || echo "❌ redis not installed"

# Run the connection test
echo -e "\n${YELLOW}Running connection tests...${NC}"
python3.11 test_alpaca_connection.py

# Check exit code
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✅ Tests completed successfully${NC}"
else
    echo -e "\n${RED}❌ Tests failed${NC}"
    exit 1
fi