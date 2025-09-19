"""
Example REST client demonstrating how to interact with the FastAPI gateway.
"""

import requests
import json
import os


class RestClient:
    """REST client for the Product Service API."""
    
    def __init__(self, base_url: str = None, api_key: str = None):
        """Initialize the REST client."""
        self.base_url = base_url or os.environ.get('REST_API_URL', 'http://127.0.0.1:8000')
        self.api_key = api_key or os.environ.get('API_KEY')
        self.session = requests.Session()
        
        # Set up authentication if API key is provided
        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}'
            })
        
        print(f"🚀 REST client initialized for: {self.base_url}")
    
    def create_product(self, product_data: dict) -> dict:
        """Create a product via REST API."""
        url = f"{self.base_url}/products/"
        response = self.session.post(url, json=product_data)
        response.raise_for_status()
        return response.json()
    
    def get_product(self, product_id: int) -> dict:
        """Get a product by ID via REST API."""
        url = f"{self.base_url}/products/{product_id}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def list_products(self, limit: int = 100, offset: int = 0) -> dict:
        """List products via REST API."""
        url = f"{self.base_url}/products/"
        params = {'limit': limit, 'offset': offset}
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def delete_product(self, product_id: int) -> dict:
        """Delete a product via REST API."""
        url = f"{self.base_url}/products/{product_id}"
        response = self.session.delete(url)
        response.raise_for_status()
        return response.json()
    
    def health_check(self) -> dict:
        """Check API health."""
        url = f"{self.base_url}/health"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()


def main():
    """Demonstrate REST client operations."""
    print("=== REST Product Service Client Example ===\n")
    
    # Create client
    client = RestClient()
    
    try:
        # Example 0: Health check
        print("0. Health check...")
        try:
            health = client.health_check()
            print(f"   API Status: {health['status']}")
            print(f"   gRPC Service: {health['grpc_service']}")
        except Exception as e:
            print(f"   Health check failed: {e}")
        print()
        
        # Example 1: Create a product
        print("1. Creating a product via REST...")
        product_data = {
            "id": 1,
            "stock": 10,
            "price": 99.99,
            "name": "Sample Product",
            "description": "This is a sample product for testing"
        }
        
        try:
            response = client.create_product(product_data)
            print(f"   Success: {response['success']}")
            print(f"   Message: {response['message']}")
            if response['success'] and response['product']:
                product = response['product']
                print(f"   Product ID: {product['id']}")
                print(f"   Stock: {product['stock']}")
                print(f"   Price: ${product['price']}")
        except requests.exceptions.HTTPError as e:
            print(f"   HTTP Error: {e}")
            if e.response.text:
                print(f"   Error details: {e.response.text}")
        print()
        
        # Example 2: Create another product
        print("2. Creating another product via REST...")
        product_data2 = {
            "id": 2,
            "stock": 5,
            "price": 149.99,
            "name": "Premium Product",
            "description": "This is a premium product"
        }
        
        try:
            response = client.create_product(product_data2)
            print(f"   Success: {response['success']}")
            print(f"   Message: {response['message']}")
        except requests.exceptions.HTTPError as e:
            print(f"   HTTP Error: {e}")
        print()
        
        # Example 3: Get a product
        print("3. Getting product by ID via REST...")
        try:
            response = client.get_product(1)
            print(f"   Success: {response['success']}")
            print(f"   Message: {response['message']}")
            if response['success'] and response['product']:
                product = response['product']
                print(f"   Product: {product['name']}")
                print(f"   Price: ${product['price']}")
                print(f"   Stock: {product['stock']}")
        except requests.exceptions.HTTPError as e:
            print(f"   HTTP Error: {e}")
        print()
        
        # Example 4: List all products
        print("4. Listing all products via REST...")
        try:
            response = client.list_products(limit=10, offset=0)
            print(f"   Success: {response['success']}")
            print(f"   Message: {response['message']}")
            print(f"   Total products: {response['total']}")
            for i, product in enumerate(response['products'], 1):
                print(f"   Product {i}: ID={product['id']}, Name='{product['name']}', Price=${product['price']}")
        except requests.exceptions.HTTPError as e:
            print(f"   HTTP Error: {e}")
        print()
        
        # Example 5: Update a product
        print("5. Updating a product via REST...")
        updated_product = {
            "id": 1,
            "stock": 15,  # Updated stock
            "price": 89.99,  # Updated price
            "name": "Updated Sample Product",  # Updated name
            "description": "This product has been updated"
        }
        
        try:
            response = client.create_product(updated_product)
            print(f"   Success: {response['success']}")
            print(f"   Message: {response['message']}")
        except requests.exceptions.HTTPError as e:
            print(f"   HTTP Error: {e}")
        print()
        
        # Example 6: Get the updated product
        print("6. Getting updated product via REST...")
        try:
            response = client.get_product(1)
            print(f"   Success: {response['success']}")
            if response['success'] and response['product']:
                product = response['product']
                print(f"   Updated Name: {product['name']}")
                print(f"   Updated Price: ${product['price']}")
                print(f"   Updated Stock: {product['stock']}")
        except requests.exceptions.HTTPError as e:
            print(f"   HTTP Error: {e}")
        print()
        
        # Example 7: Try to get a non-existent product
        print("7. Trying to get non-existent product via REST...")
        try:
            response = client.get_product(999)
            print(f"   Success: {response['success']}")
            print(f"   Message: {response['message']}")
        except requests.exceptions.HTTPError as e:
            print(f"   HTTP Error: {e.response.status_code} - {e.response.reason}")
            if e.response.text:
                error_data = json.loads(e.response.text)
                print(f"   Error details: {error_data.get('detail', 'Unknown error')}")
        print()
        
        # Example 8: Delete a product
        print("8. Deleting a product via REST...")
        try:
            response = client.delete_product(2)
            print(f"   Success: {response['success']}")
            print(f"   Message: {response['message']}")
        except requests.exceptions.HTTPError as e:
            print(f"   HTTP Error: {e}")
        print()
        
        # Example 9: List products after deletion
        print("9. Listing products after deletion via REST...")
        try:
            response = client.list_products(limit=10, offset=0)
            print(f"   Total products: {response['total']}")
            for i, product in enumerate(response['products'], 1):
                print(f"   Product {i}: ID={product['id']}, Name='{product['name']}'")
        except requests.exceptions.HTTPError as e:
            print(f"   HTTP Error: {e}")
        print()
        
        # Example 10: Test with invalid data
        print("10. Testing validation with invalid data...")
        invalid_product = {
            "id": 3,
            "stock": -5,  # Invalid: negative stock
            "price": -10.0,  # Invalid: negative price
            "name": "Invalid Product"
        }
        
        try:
            response = client.create_product(invalid_product)
            print(f"   Unexpected success: {response}")
        except requests.exceptions.HTTPError as e:
            print(f"   Expected validation error: {e.response.status_code}")
            if e.response.text:
                error_data = json.loads(e.response.text)
                print(f"   Validation details: {error_data.get('detail', 'Unknown error')}")
        print()
        
    except Exception as e:
        print(f"Error: {e}")
    
    print("REST client example completed.")


if __name__ == '__main__':
    main()