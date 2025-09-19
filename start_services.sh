#!/bin/bash

# Startup script for gRPC + REST Gateway System
# This script helps you start both services for development

echo "🚀 Starting gRPC + REST Gateway System"
echo "======================================"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Check if requirements are installed
if ! python3 -c "import grpc, fastapi, redis" &> /dev/null; then
    echo "📦 Installing requirements..."
    pip install -r requirements.txt
fi

echo "📍 Starting services..."
echo "  - gRPC Server will run on localhost:50051"
echo "  - REST Gateway will run on localhost:8000"
echo ""

# Function to cleanup on exit
cleanup() {
    echo "🛑 Stopping services..."
    kill $GRPC_PID $REST_PID 2>/dev/null
    exit 0
}

# Set trap for cleanup
trap cleanup SIGINT SIGTERM

# Start gRPC server in background
echo "🔧 Starting gRPC server..."
python3 grpc_server.py &
GRPC_PID=$!

# Wait a moment for gRPC server to start
sleep 3

# Start REST gateway in background
echo "🌐 Starting REST gateway..."
uvicorn fastapi_gateway:app --host 0.0.0.0 --port 8000 --reload &
REST_PID=$!

# Wait a moment for services to start
sleep 3

echo ""
echo "✅ Services are running!"
echo "========================"
echo "🔧 gRPC Server: localhost:50051"
echo "🌐 REST API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo "🩺 Health Check: http://localhost:8000/health"
echo ""
echo "📝 Example commands:"
echo "  # REST API:"
echo "  curl -X POST -H 'Content-Type: application/json' \\"
echo "    -d '{\"id\":1,\"stock\":10,\"price\":100}' \\"
echo "    http://127.0.0.1:8000/products/"
echo ""
echo "  # Test script:"
echo "  python3 test_system.py"
echo ""
echo "Press Ctrl+C to stop both services..."

# Wait for services
wait