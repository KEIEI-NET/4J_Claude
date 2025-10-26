#!/bin/bash
# Quick API Test Script
# バックエンドAPIの簡易動作確認スクリプト

API_URL="${1:-http://localhost:8000}"

echo "========================================="
echo "Quick API Test"
echo "API URL: $API_URL"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Health Check
echo "1. Testing Health Check..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}/health")
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Health check passed (HTTP $HTTP_CODE)${NC}"
    curl -s "${API_URL}/health" | python3 -m json.tool
else
    echo -e "${RED}✗ Health check failed (HTTP $HTTP_CODE)${NC}"
fi
echo ""

# Test 2: Impact Analysis (will fail if no data, but tests endpoint)
echo "2. Testing Impact Analysis Endpoint..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "${API_URL}/api/impact-analysis" \
    -H "Content-Type: application/json" \
    -d '{
        "target_type": "file",
        "target_path": "src/main/java/com/example/User.java",
        "depth": 3,
        "include_indirect": true
    }')

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Impact analysis succeeded (HTTP $HTTP_CODE)${NC}"
elif [ "$HTTP_CODE" = "404" ]; then
    echo -e "${YELLOW}⚠ File not found - expected if no data loaded (HTTP $HTTP_CODE)${NC}"
else
    echo -e "${RED}✗ Impact analysis failed (HTTP $HTTP_CODE)${NC}"
fi
echo ""

# Test 3: Circular Dependencies
echo "3. Testing Circular Dependencies Endpoint..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}/api/circular-dependencies")
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Circular dependencies check succeeded (HTTP $HTTP_CODE)${NC}"
    curl -s "${API_URL}/api/circular-dependencies" | python3 -m json.tool | head -20
else
    echo -e "${RED}✗ Circular dependencies check failed (HTTP $HTTP_CODE)${NC}"
fi
echo ""

# Test 4: CORS
echo "4. Testing CORS Configuration..."
CORS_HEADER=$(curl -s -I -X OPTIONS \
    -H "Origin: http://localhost:5173" \
    -H "Access-Control-Request-Method: POST" \
    "${API_URL}/api/impact-analysis" \
    | grep -i "access-control-allow-origin")

if [ -n "$CORS_HEADER" ]; then
    echo -e "${GREEN}✓ CORS configured${NC}"
    echo "  $CORS_HEADER"
else
    echo -e "${YELLOW}⚠ CORS headers not found${NC}"
fi
echo ""

echo "========================================="
echo "Test completed"
echo "========================================="
