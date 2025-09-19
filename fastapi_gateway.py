#!/usr/bin/env python3
"""
FastAPI REST Gateway for Product Management Service

This FastAPI application provides a RESTful HTTP/JSON interface that
translates REST requests into gRPC calls to the backend product service.

Features:
- RESTful endpoints for product management
- Pydantic models for request/response validation
- Automatic gRPC connection management
- Comprehensive error handling and logging
- OpenAPI/Swagger documentation
"""

import logging
from typing import Optional

import grpc
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

import product_pb2
import product_pb2_grpc

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app instance
app = FastAPI(
    title="Product Management REST API",
    description="RESTful gateway for Product Management gRPC service",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


# Pydantic models for request/response validation
class ProductRequest(BaseModel):
    """Request model for creating a product."""
    id: int = Field(..., gt=0, description="Product ID (must be positive)")
    stock: int = Field(..., ge=0, description="Product stock (cannot be negative)")
    price: float = Field(..., gt=0, description="Product price (must be positive)")
    
    @validator('price')
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('Price must be positive')
        return round(v, 2)  # Round to 2 decimal places
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "stock": 10,
                "price": 99.99
            }
        }


class ProductResponse(BaseModel):
    """Response model for product operations."""
    id: int
    stock: int
    price: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "stock": 10,
                "price": 99.99
            }
        }


class StockUpdateRequest(BaseModel):
    """Request model for updating product stock."""
    new_stock: int = Field(..., ge=0, description="New stock level (cannot be negative)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "new_stock": 25
            }
        }


class ApiResponse(BaseModel):
    """Generic API response model."""
    success: bool
    message: str
    data: Optional[ProductResponse] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "data": {
                    "id": 1,
                    "stock": 10,
                    "price": 99.99
                }
            }
        }


class GrpcClient:
    """gRPC client manager for product service connections."""
    
    def __init__(self, grpc_host: str = 'localhost', grpc_port: int = 50051):
        """
        Initialize gRPC client.
        
        Args:
            grpc_host: gRPC server hostname
            grpc_port: gRPC server port
        """
        self.grpc_host = grpc_host
        self.grpc_port = grpc_port
        self.channel = None
        self.stub = None
    
    def connect(self):
        """Establish connection to gRPC server."""
        try:
            # For production, use secure channel:
            # credentials = grpc.ssl_channel_credentials()
            # self.channel = grpc.secure_channel(f'{self.grpc_host}:{self.grpc_port}', credentials)
            
            self.channel = grpc.insecure_channel(f'{self.grpc_host}:{self.grpc_port}')
            self.stub = product_pb2_grpc.ProductServiceStub(self.channel)
            
            # Test connection with a quick call (with timeout)
            try:
                # This will raise an exception if the server is not available
                grpc.channel_ready_future(self.channel).result(timeout=5)
                logger.info(f"Connected to gRPC server at {self.grpc_host}:{self.grpc_port}")
            except grpc.FutureTimeoutError:
                logger.warning("gRPC server connection timeout")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="gRPC service unavailable"
                )
        except Exception as e:
            logger.error(f"Failed to connect to gRPC server: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to connect to backend service"
            )
    
    def close(self):
        """Close gRPC connection."""
        if self.channel:
            self.channel.close()
            logger.info("gRPC connection closed")
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def convert_grpc_error_to_http(e: grpc.RpcError) -> HTTPException:
    """
    Convert gRPC errors to appropriate HTTP status codes.
    
    Args:
        e: gRPC RpcError
        
    Returns:
        HTTPException with appropriate status code
    """
    status_code_map = {
        grpc.StatusCode.NOT_FOUND: status.HTTP_404_NOT_FOUND,
        grpc.StatusCode.ALREADY_EXISTS: status.HTTP_409_CONFLICT,
        grpc.StatusCode.INVALID_ARGUMENT: status.HTTP_400_BAD_REQUEST,
        grpc.StatusCode.INTERNAL: status.HTTP_500_INTERNAL_SERVER_ERROR,
        grpc.StatusCode.UNAVAILABLE: status.HTTP_503_SERVICE_UNAVAILABLE,
    }
    
    http_status = status_code_map.get(e.code(), status.HTTP_500_INTERNAL_SERVER_ERROR)
    return HTTPException(status_code=http_status, detail=e.details())


def product_pb_to_response(product: product_pb2.Product) -> ProductResponse:
    """Convert gRPC Product message to Pydantic ProductResponse."""
    return ProductResponse(
        id=product.id,
        stock=product.stock,
        price=product.price
    )


# REST API Endpoints

@app.get("/", response_model=dict)
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Product Management REST API",
        "version": "1.0.0",
        "documentation": "/docs",
        "endpoints": {
            "create_product": "POST /products/",
            "get_product": "GET /products/{product_id}",
            "update_stock": "PUT /products/{product_id}/stock"
        }
    }


@app.post("/products/", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductRequest):
    """
    Create a new product.
    
    Args:
        product: Product data
        
    Returns:
        ApiResponse with created product data
        
    Raises:
        HTTPException: If product creation fails
    """
    logger.info(f"Creating product with ID: {product.id}")
    
    try:
        with GrpcClient() as client:
            # Create gRPC request
            grpc_product = product_pb2.Product(
                id=product.id,
                stock=product.stock,
                price=product.price
            )
            request = product_pb2.CreateProductRequest(product=grpc_product)
            
            # Make gRPC call
            response = client.stub.CreateProduct(request)
            
            if response.success:
                return ApiResponse(
                    success=True,
                    message=response.message,
                    data=product_pb_to_response(response.product)
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=response.message
                )
    
    except grpc.RpcError as e:
        logger.error(f"gRPC error creating product: {e}")
        raise convert_grpc_error_to_http(e)
    except Exception as e:
        logger.error(f"Unexpected error creating product: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.get("/products/{product_id}", response_model=ApiResponse)
async def get_product(product_id: int):
    """
    Retrieve a product by ID.
    
    Args:
        product_id: Product ID to retrieve
        
    Returns:
        ApiResponse with product data
        
    Raises:
        HTTPException: If product not found or retrieval fails
    """
    logger.info(f"Retrieving product with ID: {product_id}")
    
    if product_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product ID must be positive"
        )
    
    try:
        with GrpcClient() as client:
            # Create gRPC request
            request = product_pb2.GetProductRequest(id=product_id)
            
            # Make gRPC call
            response = client.stub.GetProduct(request)
            
            if response.success:
                return ApiResponse(
                    success=True,
                    message=response.message,
                    data=product_pb_to_response(response.product)
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=response.message
                )
    
    except grpc.RpcError as e:
        logger.error(f"gRPC error retrieving product: {e}")
        raise convert_grpc_error_to_http(e)
    except Exception as e:
        logger.error(f"Unexpected error retrieving product: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.put("/products/{product_id}/stock", response_model=ApiResponse)
async def update_product_stock(product_id: int, stock_update: StockUpdateRequest):
    """
    Update product stock level.
    
    Args:
        product_id: Product ID to update
        stock_update: New stock level data
        
    Returns:
        ApiResponse with updated product data
        
    Raises:
        HTTPException: If product not found or update fails
    """
    logger.info(f"Updating stock for product ID: {product_id} to {stock_update.new_stock}")
    
    if product_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product ID must be positive"
        )
    
    try:
        with GrpcClient() as client:
            # Create gRPC request
            request = product_pb2.UpdateStockRequest(
                id=product_id,
                new_stock=stock_update.new_stock
            )
            
            # Make gRPC call
            response = client.stub.UpdateStock(request)
            
            if response.success:
                return ApiResponse(
                    success=True,
                    message=response.message,
                    data=product_pb_to_response(response.product)
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=response.message
                )
    
    except grpc.RpcError as e:
        logger.error(f"gRPC error updating stock: {e}")
        raise convert_grpc_error_to_http(e)
    except Exception as e:
        logger.error(f"Unexpected error updating stock: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# Health check endpoint
@app.get("/health", response_model=dict)
async def health_check():
    """
    Health check endpoint to verify service status.
    
    Returns:
        Service health status
    """
    try:
        with GrpcClient() as client:
            # Test gRPC connection
            return {
                "status": "healthy",
                "grpc_service": "connected",
                "timestamp": "2024-01-01T00:00:00Z"  # In production, use actual timestamp
            }
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "grpc_service": "disconnected",
                "timestamp": "2024-01-01T00:00:00Z"  # In production, use actual timestamp
            }
        )


# Exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle validation errors."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)}
    )


# TLS/HTTPS Configuration Placeholder
# In production, configure HTTPS by running uvicorn with SSL:
# uvicorn fastapi_gateway:app --host 0.0.0.0 --port 8000 --ssl-keyfile key.pem --ssl-certfile cert.pem


if __name__ == "__main__":
    import uvicorn
    
    # For development
    uvicorn.run(
        "fastapi_gateway:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )