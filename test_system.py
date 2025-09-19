#!/usr/bin/env python3
"""
Test script for gRPC + REST Gateway System

This script demonstrates both gRPC and REST interfaces working together.
It includes tests for product creation, retrieval, and stock updates.
"""

import time
import json
import asyncio
import requests
import grpc
import product_pb2
import product_pb2_grpc


def test_grpc_client():
    """Test direct gRPC client calls."""
    print("\n=== Testing gRPC Client ===")
    
    try:
        # Connect to gRPC server
        channel = grpc.insecure_channel('localhost:50051')
        stub = product_pb2_grpc.ProductServiceStub(channel)
        
        # Test 1: Create a product
        print("1. Creating product via gRPC...")
        product = product_pb2.Product(id=1, stock=10, price=99.99)
        request = product_pb2.CreateProductRequest(product=product)
        response = stub.CreateProduct(request)
        print(f"   Response: {response.success}, {response.message}")
        
        # Test 2: Get the product
        print("2. Retrieving product via gRPC...")
        get_request = product_pb2.GetProductRequest(id=1)
        response = stub.GetProduct(get_request)
        print(f"   Response: {response.success}, Product: ID={response.product.id}, Stock={response.product.stock}, Price={response.product.price}")
        
        # Test 3: Update stock
        print("3. Updating stock via gRPC...")
        update_request = product_pb2.UpdateStockRequest(id=1, new_stock=25)
        response = stub.UpdateStock(update_request)
        print(f"   Response: {response.success}, New Stock: {response.product.stock}")
        
        channel.close()
        print("✅ gRPC tests completed successfully")
        
    except grpc.RpcError as e:
        print(f"❌ gRPC error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def test_rest_client():
    """Test REST API calls."""
    print("\n=== Testing REST API ===")
    
    base_url = "http://127.0.0.1:8000"
    
    try:
        # Test 1: Health check
        print("1. Checking API health...")
        response = requests.get(f"{base_url}/health")
        print(f"   Status: {response.status_code}, Response: {response.json()}")
        
        # Test 2: Create a product
        print("2. Creating product via REST...")
        product_data = {"id": 2, "stock": 15, "price": 149.99}
        response = requests.post(
            f"{base_url}/products/",
            json=product_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"   Status: {response.status_code}, Response: {response.json()}")
        
        # Test 3: Get the product
        print("3. Retrieving product via REST...")
        response = requests.get(f"{base_url}/products/2")
        print(f"   Status: {response.status_code}, Response: {response.json()}")
        
        # Test 4: Update stock
        print("4. Updating stock via REST...")
        stock_data = {"new_stock": 30}
        response = requests.put(
            f"{base_url}/products/2/stock",
            json=stock_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"   Status: {response.status_code}, Response: {response.json()}")
        
        # Test 5: Try to get non-existent product
        print("5. Testing error handling (non-existent product)...")
        response = requests.get(f"{base_url}/products/999")
        print(f"   Status: {response.status_code}, Response: {response.json()}")
        
        print("✅ REST API tests completed successfully")
        
    except requests.RequestException as e:
        print(f"❌ REST API error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def main():
    """Run all tests."""
    print("🚀 Starting gRPC + REST Gateway Tests")
    print("Make sure both servers are running:")
    print("  - gRPC Server: python grpc_server.py")
    print("  - REST Gateway: uvicorn fastapi_gateway:app --reload")
    
    # Wait a moment for potential server startup
    time.sleep(2)
    
    # Test gRPC directly
    test_grpc_client()
    
    # Test REST API (which calls gRPC internally)
    test_rest_client()
    
    print("\n🎉 All tests completed!")
    print("\nYou can also test manually:")
    print("  - gRPC: Use the examples in this script")
    print("  - REST: curl -X POST -H 'Content-Type: application/json' -d '{\"id\":3,\"stock\":5,\"price\":29.99}' http://127.0.0.1:8000/products/")
    print("  - Docs: http://127.0.0.1:8000/docs")


if __name__ == "__main__":
    main()