"""
Example gRPC client demonstrating how to interact with the Product Service.
"""

import grpc
import product_pb2
import product_pb2_grpc
import os


def create_grpc_client():
    """Create a gRPC client with optional TLS support."""
    grpc_host = os.environ.get('GRPC_HOST', 'localhost')
    grpc_port = os.environ.get('GRPC_PORT', '50051')
    
    # Check for TLS configuration
    cert_file = os.environ.get('GRPC_CLIENT_CERT_FILE')
    use_tls = os.environ.get('GRPC_USE_TLS', 'false').lower() == 'true'
    
    target = f'{grpc_host}:{grpc_port}'
    
    if use_tls and cert_file and os.path.exists(cert_file):
        print(f"🔒 Connecting to gRPC server with TLS: {target}")
        with open(cert_file, 'rb') as f:
            credentials = grpc.ssl_channel_credentials(f.read())
        channel = grpc.secure_channel(target, credentials)
    else:
        print(f"🚀 Connecting to gRPC server (insecure): {target}")
        channel = grpc.insecure_channel(target)
    
    return product_pb2_grpc.ProductServiceStub(channel), channel


def main():
    """Demonstrate gRPC client operations."""
    print("=== gRPC Product Service Client Example ===\n")
    
    # Create client
    stub, channel = create_grpc_client()
    
    try:
        # Example 1: Create a product
        print("1. Creating a product...")
        product = product_pb2.Product(
            id=1,
            stock=10,
            price=99.99,
            name="Sample Product",
            description="This is a sample product for testing"
        )
        
        response = stub.CreateProduct(product)
        print(f"   Success: {response.success}")
        print(f"   Message: {response.message}")
        if response.success:
            print(f"   Product ID: {response.product.id}")
            print(f"   Stock: {response.product.stock}")
            print(f"   Price: ${response.product.price}")
        print()
        
        # Example 2: Create another product
        print("2. Creating another product...")
        product2 = product_pb2.Product(
            id=2,
            stock=5,
            price=149.99,
            name="Premium Product",
            description="This is a premium product"
        )
        
        response = stub.CreateProduct(product2)
        print(f"   Success: {response.success}")
        print(f"   Message: {response.message}")
        print()
        
        # Example 3: Get a product
        print("3. Getting product by ID...")
        get_request = product_pb2.GetProductRequest(id=1)
        response = stub.GetProduct(get_request)
        print(f"   Success: {response.success}")
        print(f"   Message: {response.message}")
        if response.success:
            print(f"   Product: {response.product.name}")
            print(f"   Price: ${response.product.price}")
            print(f"   Stock: {response.product.stock}")
        print()
        
        # Example 4: List all products
        print("4. Listing all products...")
        list_request = product_pb2.ListProductsRequest(limit=10, offset=0)
        response = stub.ListProducts(list_request)
        print(f"   Success: {response.success}")
        print(f"   Message: {response.message}")
        print(f"   Total products: {response.total}")
        for i, product in enumerate(response.products, 1):
            print(f"   Product {i}: ID={product.id}, Name='{product.name}', Price=${product.price}")
        print()
        
        # Example 5: Update a product
        print("5. Updating a product...")
        updated_product = product_pb2.Product(
            id=1,
            stock=15,  # Updated stock
            price=89.99,  # Updated price
            name="Updated Sample Product",  # Updated name
            description="This product has been updated"
        )
        
        response = stub.CreateProduct(updated_product)
        print(f"   Success: {response.success}")
        print(f"   Message: {response.message}")
        print()
        
        # Example 6: Get the updated product
        print("6. Getting updated product...")
        get_request = product_pb2.GetProductRequest(id=1)
        response = stub.GetProduct(get_request)
        print(f"   Success: {response.success}")
        if response.success:
            print(f"   Updated Name: {response.product.name}")
            print(f"   Updated Price: ${response.product.price}")
            print(f"   Updated Stock: {response.product.stock}")
        print()
        
        # Example 7: Try to get a non-existent product
        print("7. Trying to get non-existent product...")
        try:
            get_request = product_pb2.GetProductRequest(id=999)
            response = stub.GetProduct(get_request)
            print(f"   Success: {response.success}")
            print(f"   Message: {response.message}")
        except grpc.RpcError as e:
            print(f"   gRPC Error: {e.code()} - {e.details()}")
        print()
        
        # Example 8: Delete a product
        print("8. Deleting a product...")
        delete_request = product_pb2.DeleteProductRequest(id=2)
        response = stub.DeleteProduct(delete_request)
        print(f"   Success: {response.success}")
        print(f"   Message: {response.message}")
        print()
        
        # Example 9: List products after deletion
        print("9. Listing products after deletion...")
        list_request = product_pb2.ListProductsRequest(limit=10, offset=0)
        response = stub.ListProducts(list_request)
        print(f"   Total products: {response.total}")
        for i, product in enumerate(response.products, 1):
            print(f"   Product {i}: ID={product.id}, Name='{product.name}'")
        print()
        
    except grpc.RpcError as e:
        print(f"gRPC Error: {e.code()} - {e.details()}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Close the channel
        channel.close()
        print("Connection closed.")


if __name__ == '__main__':
    main()