"""
gRPC Server implementation for the Product Service.
Implements business logic and data storage using Redis.
"""

import grpc
from concurrent import futures
import product_pb2
import product_pb2_grpc
from storage import storage, ProductModel
import ssl
import os


class ProductServiceImpl(product_pb2_grpc.ProductServiceServicer):
    """Implementation of the ProductService gRPC service."""
    
    def CreateProduct(self, request: product_pb2.Product, context) -> product_pb2.ProductResponse:
        """Create or update a product."""
        try:
            # Convert gRPC message to Pydantic model
            product = ProductModel(
                id=request.id,
                stock=request.stock,
                price=request.price,
                name=request.name,
                description=request.description
            )
            
            # Store in backend
            success = storage.create_product(product)
            
            if success:
                return product_pb2.ProductResponse(
                    product=request,
                    success=True,
                    message=f"Product {request.id} created/updated successfully"
                )
            else:
                return product_pb2.ProductResponse(
                    success=False,
                    message=f"Failed to create/update product {request.id}"
                )
                
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error: {str(e)}")
            return product_pb2.ProductResponse(
                success=False,
                message=f"Internal error: {str(e)}"
            )
    
    def GetProduct(self, request: product_pb2.GetProductRequest, context) -> product_pb2.ProductResponse:
        """Get a product by ID."""
        try:
            product = storage.get_product(request.id)
            
            if product:
                grpc_product = product_pb2.Product(
                    id=product.id,
                    stock=product.stock,
                    price=product.price,
                    name=product.name,
                    description=product.description
                )
                return product_pb2.ProductResponse(
                    product=grpc_product,
                    success=True,
                    message=f"Product {request.id} found"
                )
            else:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Product {request.id} not found")
                return product_pb2.ProductResponse(
                    success=False,
                    message=f"Product {request.id} not found"
                )
                
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error: {str(e)}")
            return product_pb2.ProductResponse(
                success=False,
                message=f"Internal error: {str(e)}"
            )
    
    def ListProducts(self, request: product_pb2.ListProductsRequest, context) -> product_pb2.ListProductsResponse:
        """List all products with pagination."""
        try:
            limit = request.limit if request.limit > 0 else 100
            offset = request.offset if request.offset >= 0 else 0
            
            products = storage.list_products(limit=limit, offset=offset)
            total = storage.get_total_count()
            
            grpc_products = []
            for product in products:
                grpc_product = product_pb2.Product(
                    id=product.id,
                    stock=product.stock,
                    price=product.price,
                    name=product.name,
                    description=product.description
                )
                grpc_products.append(grpc_product)
            
            return product_pb2.ListProductsResponse(
                products=grpc_products,
                total=total,
                success=True,
                message=f"Found {len(grpc_products)} products"
            )
            
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error: {str(e)}")
            return product_pb2.ListProductsResponse(
                success=False,
                message=f"Internal error: {str(e)}"
            )
    
    def DeleteProduct(self, request: product_pb2.DeleteProductRequest, context) -> product_pb2.SimpleResponse:
        """Delete a product by ID."""
        try:
            success = storage.delete_product(request.id)
            
            if success:
                return product_pb2.SimpleResponse(
                    success=True,
                    message=f"Product {request.id} deleted successfully"
                )
            else:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Product {request.id} not found")
                return product_pb2.SimpleResponse(
                    success=False,
                    message=f"Product {request.id} not found"
                )
                
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error: {str(e)}")
            return product_pb2.SimpleResponse(
                success=False,
                message=f"Internal error: {str(e)}"
            )


def create_secure_server(port: int = 50051):
    """Create a gRPC server with TLS/SSL support."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    product_pb2_grpc.add_ProductServiceServicer_to_server(ProductServiceImpl(), server)
    
    # Check for TLS certificates
    cert_file = os.environ.get('GRPC_CERT_FILE', 'server.crt')
    key_file = os.environ.get('GRPC_KEY_FILE', 'server.key')
    
    if os.path.exists(cert_file) and os.path.exists(key_file):
        print(f"🔒 Loading TLS certificates: {cert_file}, {key_file}")
        with open(key_file, 'rb') as f:
            private_key = f.read()
        with open(cert_file, 'rb') as f:
            certificate_chain = f.read()
        
        credentials = grpc.ssl_server_credentials(
            [(private_key, certificate_chain)]
        )
        server.add_secure_port(f'[::]:{port}', credentials)
        print(f"🔒 gRPC server with TLS started on port {port}")
    else:
        print(f"⚠️  TLS certificates not found. Starting insecure server on port {port}")
        print(f"   To enable TLS, set GRPC_CERT_FILE and GRPC_KEY_FILE environment variables")
        print(f"   or place server.crt and server.key in the current directory")
        server.add_insecure_port(f'[::]:{port}')
        print(f"🚀 gRPC server started on port {port} (insecure)")
    
    return server


def main():
    """Main function to start the gRPC server."""
    print("Starting gRPC Product Service...")
    
    server = create_secure_server()
    
    try:
        server.start()
        print("gRPC server is running. Press Ctrl+C to stop.")
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\nShutting down gRPC server...")
        server.stop(grace=5)
        print("gRPC server stopped.")


if __name__ == '__main__':
    main()