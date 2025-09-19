"""
FastAPI REST Gateway that translates REST requests into gRPC calls.
Provides a RESTful HTTP/JSON API for web clients.
"""

import grpc
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Optional
import product_pb2
import product_pb2_grpc
import os
import ssl
from storage import ProductModel


# Pydantic models for REST API
class ProductCreateRequest(BaseModel):
    """Request model for creating/updating a product."""
    id: int = Field(..., description="Unique product ID")
    stock: int = Field(..., ge=0, description="Stock quantity (must be >= 0)")
    price: float = Field(..., gt=0, description="Product price (must be > 0)")
    name: str = Field("", description="Product name")
    description: str = Field("", description="Product description")


class ProductResponse(BaseModel):
    """Response model for product operations."""
    product: Optional[ProductModel] = None
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Operation result message")


class ProductListResponse(BaseModel):
    """Response model for listing products."""
    products: List[ProductModel] = Field(default_factory=list)
    total: int = Field(..., description="Total number of products")
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Operation result message")


class SimpleResponse(BaseModel):
    """Simple response model."""
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Operation result message")


# FastAPI app
app = FastAPI(
    title="Product Service REST API",
    description="RESTful HTTP/JSON API that translates requests into gRPC calls",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Optional security (uncomment to enable)
security = HTTPBearer(auto_error=False)


class gRPCClient:
    """gRPC client for connecting to the Product Service."""
    
    def __init__(self):
        self.channel = None
        self.stub = None
        self._connect()
    
    def _connect(self):
        """Establish connection to gRPC server."""
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
            self.channel = grpc.secure_channel(target, credentials)
        else:
            print(f"🚀 Connecting to gRPC server (insecure): {target}")
            self.channel = grpc.insecure_channel(target)
        
        self.stub = product_pb2_grpc.ProductServiceStub(self.channel)
        
        # Test connection
        try:
            # Make a simple call to test connectivity
            response = self.stub.ListProducts(
                product_pb2.ListProductsRequest(limit=1, offset=0),
                timeout=5
            )
            print(f"✓ Connected to gRPC Product Service")
        except grpc.RpcError as e:
            print(f"⚠️  Warning: Could not connect to gRPC server: {e}")
    
    def close(self):
        """Close the gRPC channel."""
        if self.channel:
            self.channel.close()


# Global gRPC client
grpc_client = gRPCClient()


async def get_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Optional API key validation. Uncomment to enable security."""
    # if credentials is None:
    #     raise HTTPException(status_code=401, detail="API key required")
    # 
    # expected_key = os.environ.get("API_KEY", "your-secret-api-key")
    # if credentials.credentials != expected_key:
    #     raise HTTPException(status_code=401, detail="Invalid API key")
    return credentials


@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup."""
    print("🚀 FastAPI REST Gateway starting up...")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up connections on shutdown."""
    print("🛑 FastAPI REST Gateway shutting down...")
    grpc_client.close()


@app.get("/", response_model=dict)
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Product Service REST API",
        "version": "1.0.0",
        "description": "RESTful gateway that translates HTTP requests to gRPC calls",
        "endpoints": {
            "create_product": "POST /products/",
            "get_product": "GET /products/{product_id}",
            "list_products": "GET /products/",
            "delete_product": "DELETE /products/{product_id}"
        },
        "docs": "/docs"
    }


@app.post("/products/", response_model=ProductResponse)
async def create_product(
    product: ProductCreateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(get_api_key)
):
    """Create or update a product."""
    try:
        # Convert to gRPC message
        grpc_product = product_pb2.Product(
            id=product.id,
            stock=product.stock,
            price=product.price,
            name=product.name,
            description=product.description
        )
        
        # Call gRPC service
        response = grpc_client.stub.CreateProduct(grpc_product)
        
        if response.success:
            # Convert response back to Pydantic model
            product_model = ProductModel(
                id=response.product.id,
                stock=response.product.stock,
                price=response.product.price,
                name=response.product.name,
                description=response.product.description
            )
            return ProductResponse(
                product=product_model,
                success=True,
                message=response.message
            )
        else:
            raise HTTPException(status_code=400, detail=response.message)
            
    except grpc.RpcError as e:
        raise HTTPException(
            status_code=503,
            detail=f"gRPC service unavailable: {e.details()}"
        )


@app.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(get_api_key)
):
    """Get a product by ID."""
    try:
        # Call gRPC service
        request = product_pb2.GetProductRequest(id=product_id)
        response = grpc_client.stub.GetProduct(request)
        
        if response.success:
            # Convert response to Pydantic model
            product_model = ProductModel(
                id=response.product.id,
                stock=response.product.stock,
                price=response.product.price,
                name=response.product.name,
                description=response.product.description
            )
            return ProductResponse(
                product=product_model,
                success=True,
                message=response.message
            )
        else:
            raise HTTPException(status_code=404, detail=response.message)
            
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
        else:
            raise HTTPException(
                status_code=503,
                detail=f"gRPC service unavailable: {e.details()}"
            )


@app.get("/products/", response_model=ProductListResponse)
async def list_products(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of products to return"),
    offset: int = Query(0, ge=0, description="Number of products to skip"),
    credentials: HTTPAuthorizationCredentials = Depends(get_api_key)
):
    """List all products with pagination."""
    try:
        # Call gRPC service
        request = product_pb2.ListProductsRequest(limit=limit, offset=offset)
        response = grpc_client.stub.ListProducts(request)
        
        if response.success:
            # Convert response to Pydantic models
            products = []
            for grpc_product in response.products:
                product_model = ProductModel(
                    id=grpc_product.id,
                    stock=grpc_product.stock,
                    price=grpc_product.price,
                    name=grpc_product.name,
                    description=grpc_product.description
                )
                products.append(product_model)
            
            return ProductListResponse(
                products=products,
                total=response.total,
                success=True,
                message=response.message
            )
        else:
            raise HTTPException(status_code=500, detail=response.message)
            
    except grpc.RpcError as e:
        raise HTTPException(
            status_code=503,
            detail=f"gRPC service unavailable: {e.details()}"
        )


@app.delete("/products/{product_id}", response_model=SimpleResponse)
async def delete_product(
    product_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(get_api_key)
):
    """Delete a product by ID."""
    try:
        # Call gRPC service
        request = product_pb2.DeleteProductRequest(id=product_id)
        response = grpc_client.stub.DeleteProduct(request)
        
        if response.success:
            return SimpleResponse(
                success=True,
                message=response.message
            )
        else:
            raise HTTPException(status_code=404, detail=response.message)
            
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
        else:
            raise HTTPException(
                status_code=503,
                detail=f"gRPC service unavailable: {e.details()}"
            )


@app.get("/health", response_model=dict)
async def health_check():
    """Health check endpoint."""
    try:
        # Test gRPC connection
        response = grpc_client.stub.ListProducts(
            product_pb2.ListProductsRequest(limit=1, offset=0),
            timeout=5
        )
        grpc_status = "healthy"
    except:
        grpc_status = "unhealthy"
    
    return {
        "status": "healthy" if grpc_status == "healthy" else "degraded",
        "grpc_service": grpc_status,
        "timestamp": "2024-01-01T00:00:00Z"  # In real app, use datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    
    # TLS/SSL configuration for HTTPS
    ssl_keyfile = os.environ.get('SSL_KEY_FILE')
    ssl_certfile = os.environ.get('SSL_CERT_FILE')
    
    if ssl_keyfile and ssl_certfile and os.path.exists(ssl_keyfile) and os.path.exists(ssl_certfile):
        print("🔒 Starting FastAPI with HTTPS")
        uvicorn.run(
            "fastapi_gateway:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            ssl_keyfile=ssl_keyfile,
            ssl_certfile=ssl_certfile
        )
    else:
        print("🚀 Starting FastAPI with HTTP (insecure)")
        print("   To enable HTTPS, set SSL_KEY_FILE and SSL_CERT_FILE environment variables")
        uvicorn.run(
            "fastapi_gateway:app",
            host="0.0.0.0",
            port=8000,
            reload=True
        )