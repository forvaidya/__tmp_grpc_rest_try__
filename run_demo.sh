#!/bin/bash

# Comprehensive demo script for the gRPC + REST Gateway
# This script demonstrates running both servers and testing them

set -e  # Exit on any error

echo "🚀 Starting gRPC + REST Gateway Demo"
echo "===================================="

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "⚠️  Port $1 is already in use. Please stop the service or choose a different port."
        return 1
    fi
    return 0
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=1
    
    echo "⏳ Waiting for $name to be ready..."
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            echo "✅ $name is ready!"
            return 0
        fi
        echo "   Attempt $attempt/$max_attempts..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ $name failed to start within $((max_attempts * 2)) seconds"
    return 1
}

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "🛑 Cleaning up..."
    if [ ! -z "$GRPC_PID" ]; then
        echo "   Stopping gRPC server (PID: $GRPC_PID)..."
        kill $GRPC_PID 2>/dev/null || true
    fi
    if [ ! -z "$FASTAPI_PID" ]; then
        echo "   Stopping FastAPI server (PID: $FASTAPI_PID)..."
        kill $FASTAPI_PID 2>/dev/null || true
    fi
    echo "✅ Cleanup complete"
}

# Set up signal handlers for cleanup
trap cleanup EXIT INT TERM

# Check if required ports are available
echo "🔍 Checking port availability..."
check_port 50051 || exit 1  # gRPC port
check_port 8000 || exit 1   # FastAPI port

# Check if Redis is available (optional)
echo "🔍 Checking Redis availability..."
if redis-cli ping >/dev/null 2>&1; then
    echo "✅ Redis is available"
else
    echo "⚠️  Redis is not available. Using in-memory fallback storage."
    echo "   To install Redis: sudo apt-get install redis-server (Ubuntu/Debian)"
    echo "                     brew install redis (macOS)"
fi

# Install dependencies if not already installed
echo "📦 Checking Python dependencies..."
python -c "import grpc, fastapi, uvicorn, pydantic, redis" 2>/dev/null || {
    echo "⚠️  Some dependencies are missing. Installing..."
    pip install -r requirements.txt
}

# Generate protobuf files if they don't exist
if [ ! -f "product_pb2.py" ] || [ ! -f "product_pb2_grpc.py" ]; then
    echo "🔧 Generating protobuf files..."
    python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. product.proto
fi

echo ""
echo "🎯 Starting services..."

# Start gRPC server in the background
echo "🚀 Starting gRPC server on port 50051..."
python grpc_server.py &
GRPC_PID=$!
echo "   gRPC server started with PID: $GRPC_PID"

# Wait a moment for gRPC server to initialize
sleep 3

# Start FastAPI server in the background
echo "🚀 Starting FastAPI server on port 8000..."
python fastapi_gateway.py &
FASTAPI_PID=$!
echo "   FastAPI server started with PID: $FASTAPI_PID"

# Wait for services to be ready
wait_for_service "http://localhost:8000/health" "FastAPI server"

echo ""
echo "🎉 Both servers are running!"
echo "================================================"
echo "📊 Service Status:"
echo "   gRPC Server:  ✅ Running on localhost:50051"
echo "   REST API:     ✅ Running on http://localhost:8000"
echo "   API Docs:     📚 http://localhost:8000/docs"
echo "   Health Check: 🏥 http://localhost:8000/health"
echo ""

# Prompt user for demo choice
echo "🎮 What would you like to do?"
echo "1) Run gRPC client demo"
echo "2) Run REST client demo"
echo "3) Run both demos"
echo "4) Keep servers running (manual testing)"
echo "5) Exit"
echo ""

while true; do
    read -p "Enter your choice (1-5): " choice
    case $choice in
        1)
            echo ""
            echo "🔧 Running gRPC client demo..."
            echo "================================"
            python example_grpc_client.py
            break
            ;;
        2)
            echo ""
            echo "🔧 Running REST client demo..."
            echo "=============================="
            python example_rest_client.py
            break
            ;;
        3)
            echo ""
            echo "🔧 Running gRPC client demo first..."
            echo "==================================="
            python example_grpc_client.py
            echo ""
            echo "🔧 Now running REST client demo..."
            echo "================================="
            python example_rest_client.py
            break
            ;;
        4)
            echo ""
            echo "🎯 Servers are running! You can now:"
            echo ""
            echo "Test the REST API with curl:"
            echo "   curl -X POST -H 'Content-Type: application/json' \\"
            echo "        -d '{\"id\":1,\"stock\":10,\"price\":100,\"name\":\"Test Product\"}' \\"
            echo "        http://127.0.0.1:8000/products/"
            echo ""
            echo "   curl http://127.0.0.1:8000/products/1"
            echo ""
            echo "   curl http://127.0.0.1:8000/products/"
            echo ""
            echo "View API documentation:"
            echo "   Open http://localhost:8000/docs in your browser"
            echo ""
            echo "Run the example clients:"
            echo "   python example_grpc_client.py"
            echo "   python example_rest_client.py"
            echo ""
            echo "Press Ctrl+C to stop the servers..."
            
            # Wait for user to interrupt
            while true; do
                sleep 1
            done
            ;;
        5)
            echo "👋 Exiting..."
            break
            ;;
        *)
            echo "Invalid choice. Please enter 1-5."
            ;;
    esac
done

echo ""
echo "🏁 Demo completed!"