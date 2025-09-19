# Getting Started Guide

This guide will help you set up and run the Python gRPC + REST Gateway system.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Interactive Demo

The easiest way to get started is with the interactive demo script:

```bash
./run_demo.sh
```

This script will:
- Check dependencies and ports
- Start both gRPC and REST servers
- Offer options to run example clients
- Clean up automatically when done

### 3. Manual Setup

If you prefer to run services manually:

#### Start the gRPC Server

```bash
python grpc_server.py
```

The gRPC server will start on `localhost:50051`

#### Start the REST Gateway

```bash
python fastapi_gateway.py
# OR
uvicorn fastapi_gateway:app --reload
```

The REST API will be available at `http://localhost:8000`

## API Documentation

Once the REST server is running, you can access:

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Example Usage

### REST API Examples

```bash
# Create a product
curl -X POST -H "Content-Type: application/json" \
    -d '{"id":1,"stock":10,"price":100,"name":"Test Product"}' \
    http://127.0.0.1:8000/products/

# Get a product
curl http://127.0.0.1:8000/products/1

# List all products
curl http://127.0.0.1:8000/products/

# Delete a product
curl -X DELETE http://127.0.0.1:8000/products/1
```

### gRPC Examples

```python
import grpc
import product_pb2, product_pb2_grpc

# Connect to server
channel = grpc.insecure_channel('localhost:50051')
stub = product_pb2_grpc.ProductServiceStub(channel)

# Create a product
product = product_pb2.Product(id=1, stock=10, price=100, name="Test Product")
response = stub.CreateProduct(product)
print(f"Success: {response.success}")

# Get a product
request = product_pb2.GetProductRequest(id=1)
response = stub.GetProduct(request)
print(f"Product: {response.product.name}")
```

### Run Example Clients

```bash
# Test gRPC functionality
python example_grpc_client.py

# Test REST functionality
python example_rest_client.py
```

## Data Storage

The system uses Redis for data persistence. If Redis is not available, it automatically falls back to in-memory storage.

### Installing Redis

**Ubuntu/Debian:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis-server
```

**macOS:**
```bash
brew install redis
brew services start redis
```

**Docker:**
```bash
docker run -d -p 6379:6379 redis:alpine
```

## Security / TLS Configuration

### Generate Development Certificates

```bash
./generate_certs.sh
```

### Run with TLS/SSL

**gRPC Server with TLS:**
```bash
GRPC_CERT_FILE=certs/server.crt GRPC_KEY_FILE=certs/server.key python grpc_server.py
```

**FastAPI with HTTPS:**
```bash
SSL_CERT_FILE=certs/server.crt SSL_KEY_FILE=certs/server.key python fastapi_gateway.py
```

**Client with TLS:**
```bash
# gRPC client
GRPC_USE_TLS=true GRPC_CLIENT_CERT_FILE=certs/server.crt python example_grpc_client.py

# REST client  
REST_API_URL=https://127.0.0.1:8000 python example_rest_client.py
```

For detailed TLS configuration, see [TLS_CONFIGURATION.md](TLS_CONFIGURATION.md).

## Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   REST Client   │    │   gRPC Client   │
│  (HTTP/JSON)    │    │   (Binary)      │
└─────────┬───────┘    └─────────┬───────┘
          │                      │
          ▼                      ▼
┌─────────────────┐    ┌─────────────────┐
│  FastAPI REST   │────│   gRPC Server   │
│    Gateway      │    │                 │
│  (Port 8000)    │    │   (Port 50051)  │
└─────────┬───────┘    └─────────┬───────┘
          │                      │
          └──────────┬───────────┘
                     ▼
          ┌─────────────────┐
          │      Redis      │
          │   Data Store    │
          │  (Port 6379)    │
          └─────────────────┘
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GRPC_HOST` | gRPC server host | `localhost` |
| `GRPC_PORT` | gRPC server port | `50051` |
| `GRPC_CERT_FILE` | gRPC TLS certificate | None (insecure) |
| `GRPC_KEY_FILE` | gRPC TLS private key | None (insecure) |
| `GRPC_USE_TLS` | Enable TLS for gRPC client | `false` |
| `GRPC_CLIENT_CERT_FILE` | Client certificate for TLS | None |
| `SSL_CERT_FILE` | FastAPI HTTPS certificate | None (HTTP) |
| `SSL_KEY_FILE` | FastAPI HTTPS private key | None (HTTP) |
| `REST_API_URL` | REST client base URL | `http://127.0.0.1:8000` |
| `API_KEY` | Optional API authentication | None (disabled) |

## Production Deployment

For production environments:

1. **Use a proper Redis cluster** or managed Redis service
2. **Deploy with proper TLS certificates** from a trusted CA
3. **Enable API authentication** by configuring `API_KEY`
4. **Use a reverse proxy** (nginx, traefik) for load balancing
5. **Monitor both services** with health checks
6. **Scale horizontally** by running multiple instances

## Troubleshooting

### Common Issues

**Port already in use:**
```bash
# Check what's using the port
lsof -i :50051  # gRPC
lsof -i :8000   # FastAPI

# Kill the process
kill -9 <PID>
```

**gRPC connection failed:**
- Ensure the gRPC server is running on the correct port
- Check firewall settings
- Verify TLS configuration if using secure connections

**Redis connection failed:**
- The system will automatically use in-memory storage as fallback
- Install and start Redis for persistent storage
- Check Redis is running: `redis-cli ping`

**Import errors:**
```bash
# Regenerate protobuf files
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. product.proto

# Reinstall dependencies
pip install -r requirements.txt
```

## Development

### File Structure

```
├── README.md                    # Project overview
├── requirements.txt             # Python dependencies
├── product.proto               # Protocol Buffer schema
├── storage.py                  # Shared storage layer
├── grpc_server.py             # gRPC service implementation
├── fastapi_gateway.py         # REST API gateway
├── example_grpc_client.py     # gRPC client examples
├── example_rest_client.py     # REST client examples
├── run_demo.sh                # Interactive demo script
├── generate_certs.sh          # TLS certificate generation
└── TLS_CONFIGURATION.md       # Detailed TLS setup guide
```

### Making Changes

1. **Modify the Protocol Buffer schema** in `product.proto`
2. **Regenerate Python files**:
   ```bash
   python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. product.proto
   ```
3. **Update the storage layer** in `storage.py` if needed
4. **Update both servers** to handle new fields/operations
5. **Test with example clients**

### Adding New Operations

1. Add new RPC methods to `product.proto`
2. Implement the methods in `grpc_server.py`
3. Add corresponding REST endpoints in `fastapi_gateway.py`
4. Update example clients to demonstrate usage

## Support

For issues and questions:

1. Check this documentation
2. Review the example client code
3. Check server logs for error messages
4. Verify all dependencies are installed correctly

The system is designed to be robust with comprehensive error handling and automatic fallbacks where possible.