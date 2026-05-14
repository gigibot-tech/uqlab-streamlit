#!/bin/bash

# Test script for CIFAR-10N dataset stats API endpoint
# This verifies the backend route is accessible and returns valid data

API_URL="http://localhost:8000/api/v1/datasets/cifar10n/stats?noise_type=worse_label"

echo "=========================================="
echo "Testing CIFAR-10N Dataset Stats API"
echo "=========================================="
echo ""
echo "Endpoint: $API_URL"
echo ""

# Test the API endpoint
echo "Making request..."
response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "$API_URL")

# Extract HTTP status code
http_status=$(echo "$response" | grep "HTTP_STATUS:" | cut -d: -f2)
body=$(echo "$response" | sed '/HTTP_STATUS:/d')

echo ""
echo "HTTP Status: $http_status"
echo ""

if [ "$http_status" = "200" ]; then
    echo "✅ SUCCESS - API endpoint is working!"
    echo ""
    echo "Response body:"
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
    echo ""
    echo "=========================================="
    echo "Summary:"
    echo "- Backend route: ✅ Working"
    echo "- Expected URL: ✅ Correct (/api/v1/datasets/cifar10n/stats)"
    echo "- Frontend should now work after cache clear"
    echo "=========================================="
elif [ "$http_status" = "404" ]; then
    echo "❌ ERROR - 404 Not Found"
    echo ""
    echo "The endpoint is not accessible. Check:"
    echo "1. Backend container is running: docker-compose ps backend"
    echo "2. Route is registered in datasets.py"
    echo "3. Router prefix is correct in main.py"
    echo ""
    echo "Response:"
    echo "$body"
else
    echo "❌ ERROR - HTTP $http_status"
    echo ""
    echo "Response:"
    echo "$body"
fi

echo ""

# Made with Bob
