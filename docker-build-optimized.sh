#!/bin/bash

# Optimized Docker build script with BuildKit and caching
# This script significantly speeds up rebuilds by using advanced Docker features

set -e

echo "🚀 Starting optimized Docker Compose build..."
echo "Using BuildKit with cache mounts and multi-stage builds"
echo ""

# Enable Docker BuildKit for advanced caching
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Set build arguments for faster builds
export BUILDKIT_PROGRESS=plain

# Function to print colored output
print_status() {
    echo "🔧 $1"
}

# Pre-build steps
print_status "Setting up build environment..."

# Create cache directories if they don't exist
mkdir -p ./cache/pip
mkdir -p ./cache/huggingface
mkdir -p ./cache/torch

# Clean up any dangling images to free space (optional)
print_status "Cleaning up dangling images..."
docker image prune -f > /dev/null 2>&1 || true

# Build with cache optimization
print_status "Building services with optimized caching..."

# Use docker-compose with BuildKit
docker-compose build \
    --parallel \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    "$@"

print_status "Build completed!"
echo ""
echo "📊 Build optimizations enabled:"
echo "  ✅ Multi-stage builds for smaller images"
echo "  ✅ Shared pip cache across all Python services"
echo "  ✅ HuggingFace model cache for recipe-service"
echo "  ✅ PyTorch cache for ML models"
echo "  ✅ BuildKit cache mounts for faster pip installs"
echo "  ✅ Health checks for better container monitoring"
echo ""
echo "🚀 To start services:"
echo "  docker-compose up -d"
echo ""
echo "📈 Subsequent builds will be much faster due to caching!"

# Optional: Show cache usage
if command -v docker system df &> /dev/null; then
    echo ""
    echo "💾 Docker cache usage:"
    docker system df
fi