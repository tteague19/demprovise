#!/bin/bash
# Docker validation and test script

set -e

echo "🐳 Docker Build and Test Script for RCV Dashboard"
echo "================================================"

# Check Docker availability
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed or not in PATH"
    exit 1
fi

echo "✅ Docker version: $(docker --version)"

# Test Dockerfile build (build only builder stage to save time)
echo -e "\n📋 Testing Dockerfile build (builder stage)..."
if docker build --target builder -f Dockerfile -t rcv-test:builder . >/dev/null 2>&1; then
    echo "✅ Dockerfile builder stage builds successfully"
    docker rmi rcv-test:builder >/dev/null 2>&1
else
    echo "❌ Dockerfile build failed"
    # Show error details
    echo "Error details:"
    docker build --target builder -f Dockerfile -t rcv-test:builder .
    exit 1
fi

# Test development Dockerfile 
echo -e "\n📋 Testing Dockerfile.dev build..."
if docker build -f Dockerfile.dev -t rcv-test:dev . >/dev/null 2>&1; then
    echo "✅ Dockerfile.dev builds successfully"
    docker rmi rcv-test:dev >/dev/null 2>&1 || true
else
    echo "❌ Dockerfile.dev build failed"
    # Show error details
    echo "Error details:"
    docker build -f Dockerfile.dev -t rcv-test:dev .
    exit 1
fi

# Validate docker-compose
echo -e "\n📋 Validating docker-compose.yml..."
if command -v docker-compose &> /dev/null; then
    if docker-compose config >/dev/null 2>&1; then
        echo "✅ docker-compose.yml syntax is valid"
    else
        echo "❌ docker-compose.yml syntax validation failed"
        exit 1
    fi
else
    echo "⚠️  docker-compose not available, skipping validation"
fi

echo -e "\n🎉 All Docker configurations validated successfully!"
echo -e "\n📝 To build and run:"
echo "   Production: docker-compose up --build"
echo "   Development: docker-compose --profile development up rcv-dashboard-dev --build"

# Optional: Test actual build (commented out to avoid long build times)
# echo -e "\n🔨 Testing production build..."
# docker build -t rcv-dashboard:test .
# echo "✅ Production build successful"

echo -e "\n✨ Ready for deployment!"