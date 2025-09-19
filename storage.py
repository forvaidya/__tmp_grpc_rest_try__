"""
Shared storage layer using Redis for the gRPC + REST gateway.
Provides abstraction for data storage and retrieval operations.
"""

import json
import redis
from typing import Dict, List, Optional
from pydantic import BaseModel


class ProductModel(BaseModel):
    """Pydantic model for product data validation."""
    id: int
    stock: int
    price: float
    name: str = ""
    description: str = ""


class StorageService:
    """Redis-based storage service for products."""
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        """Initialize Redis connection."""
        self.redis_client = redis.Redis(
            host=host, 
            port=port, 
            db=db, 
            decode_responses=True
        )
        # Test connection
        try:
            self.redis_client.ping()
            print(f"✓ Connected to Redis at {host}:{port}")
        except redis.ConnectionError:
            print(f"⚠️  Warning: Cannot connect to Redis at {host}:{port}")
            print("Using in-memory fallback storage (data will not persist)")
            self._fallback_storage = {}
            self._use_redis = False
        else:
            self._use_redis = True
    
    def _get_product_key(self, product_id: int) -> str:
        """Generate Redis key for a product."""
        return f"product:{product_id}"
    
    def create_product(self, product: ProductModel) -> bool:
        """Create or update a product."""
        try:
            product_data = product.model_dump()
            if self._use_redis:
                key = self._get_product_key(product.id)
                return self.redis_client.set(key, json.dumps(product_data))
            else:
                self._fallback_storage[product.id] = product_data
                return True
        except Exception as e:
            print(f"Error creating product: {e}")
            return False
    
    def get_product(self, product_id: int) -> Optional[ProductModel]:
        """Get a product by ID."""
        try:
            if self._use_redis:
                key = self._get_product_key(product_id)
                data = self.redis_client.get(key)
                if data:
                    product_dict = json.loads(data)
                    return ProductModel(**product_dict)
            else:
                data = self._fallback_storage.get(product_id)
                if data:
                    return ProductModel(**data)
            return None
        except Exception as e:
            print(f"Error getting product {product_id}: {e}")
            return None
    
    def list_products(self, limit: int = 100, offset: int = 0) -> List[ProductModel]:
        """List all products with pagination."""
        try:
            products = []
            if self._use_redis:
                # Get all product keys
                keys = self.redis_client.keys("product:*")
                # Sort by product ID
                keys.sort(key=lambda k: int(k.split(":")[1]))
                # Apply pagination
                paginated_keys = keys[offset:offset + limit]
                
                for key in paginated_keys:
                    data = self.redis_client.get(key)
                    if data:
                        product_dict = json.loads(data)
                        products.append(ProductModel(**product_dict))
            else:
                # Get all products from fallback storage
                all_products = list(self._fallback_storage.values())
                # Sort by ID
                all_products.sort(key=lambda p: p['id'])
                # Apply pagination
                paginated_products = all_products[offset:offset + limit]
                products = [ProductModel(**p) for p in paginated_products]
                
            return products
        except Exception as e:
            print(f"Error listing products: {e}")
            return []
    
    def delete_product(self, product_id: int) -> bool:
        """Delete a product by ID."""
        try:
            if self._use_redis:
                key = self._get_product_key(product_id)
                return bool(self.redis_client.delete(key))
            else:
                if product_id in self._fallback_storage:
                    del self._fallback_storage[product_id]
                    return True
                return False
        except Exception as e:
            print(f"Error deleting product {product_id}: {e}")
            return False
    
    def get_total_count(self) -> int:
        """Get total number of products."""
        try:
            if self._use_redis:
                return len(self.redis_client.keys("product:*"))
            else:
                return len(self._fallback_storage)
        except Exception as e:
            print(f"Error getting product count: {e}")
            return 0


# Global storage instance
storage = StorageService()