#!/usr/bin/env python3
"""
gRPC Server Implementation for Product Management Service

This server implements the ProductService defined in product.proto,
using Redis as the data store for persistent storage.

Features:
- Product creation, retrieval, and stock updates
- Redis-backed storage with proper serialization
- TLS/SSL support placeholders
- Comprehensive error handling and logging
"""

import asyncio
import logging
import json
from concurrent import futures
from typing import Optional

import grpc
import redis
import product_pb2
import product_pb2_grpc

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProductService(product_pb2_grpc.ProductServiceServicer):
    """
    Implementation of the ProductService gRPC service.
    
    This service provides CRUD operations for products, using Redis
    as the backing store for persistence.
    """
    
    def __init__(self, redis_host: str = 'localhost', redis_port: int = 6379):
        """
        Initialize the ProductService with Redis connection.
        
        Args:
            redis_host: Redis server hostname
            redis_port: Redis server port
        """
        try:
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {redis_host}:{redis_port}")
        except redis.ConnectionError:
            logger.warning("Redis connection failed. Using in-memory storage.")
            self.redis_client = None
            self._memory_store = {}
    
    def _get_product_key(self, product_id: int) -> str:
        """Generate Redis key for a product."""
        return f"product:{product_id}"
    
    def _serialize_product(self, product: product_pb2.Product) -> str:
        """Serialize product to JSON string for Redis storage."""
        return json.dumps({
            'id': product.id,
            'stock': product.stock,
            'price': product.price
        })
    
    def _deserialize_product(self, data: str) -> Optional[product_pb2.Product]:
        """Deserialize JSON string to Product object."""
        try:
            product_data = json.loads(data)
            return product_pb2.Product(
                id=product_data['id'],
                stock=product_data['stock'],
                price=product_data['price']
            )
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error deserializing product data: {e}")
            return None
    
    def _store_product(self, product: product_pb2.Product) -> bool:
        """Store product in Redis or memory store."""
        try:
            key = self._get_product_key(product.id)
            data = self._serialize_product(product)
            
            if self.redis_client:
                self.redis_client.set(key, data)
            else:
                self._memory_store[key] = data
            
            logger.info(f"Stored product {product.id}")
            return True
        except Exception as e:
            logger.error(f"Error storing product {product.id}: {e}")
            return False
    
    def _get_product(self, product_id: int) -> Optional[product_pb2.Product]:
        """Retrieve product from Redis or memory store."""
        try:
            key = self._get_product_key(product_id)
            
            if self.redis_client:
                data = self.redis_client.get(key)
            else:
                data = self._memory_store.get(key)
            
            if data:
                return self._deserialize_product(data)
            return None
        except Exception as e:
            logger.error(f"Error retrieving product {product_id}: {e}")
            return None

    def CreateProduct(self, request, context):
        """
        Create a new product.
        
        Args:
            request: CreateProductRequest containing the product to create
            context: gRPC context
            
        Returns:
            ProductResponse with success status and product data
        """
        logger.info(f"Creating product with ID: {request.product.id}")
        
        # Validate input
        if request.product.id <= 0:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Product ID must be positive")
            return product_pb2.ProductResponse(
                success=False,
                message="Product ID must be positive"
            )
        
        if request.product.stock < 0:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Stock cannot be negative")
            return product_pb2.ProductResponse(
                success=False,
                message="Stock cannot be negative"
            )
        
        if request.product.price <= 0:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Price must be positive")
            return product_pb2.ProductResponse(
                success=False,
                message="Price must be positive"
            )
        
        # Check if product already exists
        existing_product = self._get_product(request.product.id)
        if existing_product:
            context.set_code(grpc.StatusCode.ALREADY_EXISTS)
            context.set_details(f"Product with ID {request.product.id} already exists")
            return product_pb2.ProductResponse(
                success=False,
                message=f"Product with ID {request.product.id} already exists"
            )
        
        # Store the product
        if self._store_product(request.product):
            return product_pb2.ProductResponse(
                success=True,
                message=f"Product {request.product.id} created successfully",
                product=request.product
            )
        else:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Failed to store product")
            return product_pb2.ProductResponse(
                success=False,
                message="Failed to store product"
            )

    def GetProduct(self, request, context):
        """
        Retrieve a product by ID.
        
        Args:
            request: GetProductRequest containing the product ID
            context: gRPC context
            
        Returns:
            ProductResponse with product data if found
        """
        logger.info(f"Retrieving product with ID: {request.id}")
        
        if request.id <= 0:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Product ID must be positive")
            return product_pb2.ProductResponse(
                success=False,
                message="Product ID must be positive"
            )
        
        product = self._get_product(request.id)
        if product:
            return product_pb2.ProductResponse(
                success=True,
                message=f"Product {request.id} retrieved successfully",
                product=product
            )
        else:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Product with ID {request.id} not found")
            return product_pb2.ProductResponse(
                success=False,
                message=f"Product with ID {request.id} not found"
            )

    def UpdateStock(self, request, context):
        """
        Update product stock.
        
        Args:
            request: UpdateStockRequest containing product ID and new stock
            context: gRPC context
            
        Returns:
            ProductResponse with updated product data
        """
        logger.info(f"Updating stock for product ID: {request.id} to {request.new_stock}")
        
        if request.id <= 0:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Product ID must be positive")
            return product_pb2.ProductResponse(
                success=False,
                message="Product ID must be positive"
            )
        
        if request.new_stock < 0:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Stock cannot be negative")
            return product_pb2.ProductResponse(
                success=False,
                message="Stock cannot be negative"
            )
        
        # Get existing product
        product = self._get_product(request.id)
        if not product:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Product with ID {request.id} not found")
            return product_pb2.ProductResponse(
                success=False,
                message=f"Product with ID {request.id} not found"
            )
        
        # Update stock
        product.stock = request.new_stock
        
        # Store updated product
        if self._store_product(product):
            return product_pb2.ProductResponse(
                success=True,
                message=f"Stock for product {request.id} updated successfully",
                product=product
            )
        else:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Failed to update product stock")
            return product_pb2.ProductResponse(
                success=False,
                message="Failed to update product stock"
            )


def serve(port: int = 50051, use_tls: bool = False):
    """
    Start the gRPC server.
    
    Args:
        port: Port to listen on
        use_tls: Whether to enable TLS (placeholder for future implementation)
    """
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    product_pb2_grpc.add_ProductServiceServicer_to_server(ProductService(), server)
    
    if use_tls:
        # TLS configuration placeholder
        # In production, load your TLS credentials here:
        # with open('server.key', 'rb') as f:
        #     private_key = f.read()
        # with open('server.crt', 'rb') as f:
        #     certificate_chain = f.read()
        # credentials = grpc.ssl_server_credentials([(private_key, certificate_chain)])
        # server.add_secure_port(f'[::]:{port}', credentials)
        logger.warning("TLS requested but not implemented. Starting insecure server.")
        server.add_insecure_port(f'[::]:{port}')
    else:
        server.add_insecure_port(f'[::]:{port}')
    
    logger.info(f"Starting gRPC server on port {port}")
    server.start()
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down gRPC server...")
        server.stop(0)


if __name__ == '__main__':
    # Start the server
    serve()