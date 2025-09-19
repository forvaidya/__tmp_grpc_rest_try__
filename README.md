# __tmp_grpc_rest_try__

# Python gRPC + REST (FastAPI) Gateway Prototype

This repository demonstrates a Python backend system with both **gRPC** and **REST** (FastAPI) interfaces, built as a prototype for modern microservice architectures.

## **Architecture Overview**

- **gRPC Server**: Implements business logic and data storage (e.g., via Redis), exposes gRPC endpoints using Protocol Buffers.
- **REST Gateway (FastAPI)**: Provides a RESTful HTTP/JSON API for web clients, translating REST requests into gRPC calls under the hood.
- **Shared Backend**: Both interfaces share the same business logic and storage, ensuring a single source of truth.

```
      [ REST Client ]        [ gRPC Client ]
             |                      |
       [ FastAPI REST ]     [ gRPC Server ]
                \           /
                 [ Redis / Data Store ]
```

## **Features**

- **Dual API Support**: Both REST and gRPC interfaces for maximum flexibility.
- **Strict Data Validation**: Uses Pydantic (REST) and Protobuf (gRPC) schemas for type-safe communication.
- **Pluggable Storage**: Example uses Redis, easily adaptable.
- **Transport Security**: Supports TLS for gRPC, HTTPS for REST.
- **Clear Example**: Suitable for learning, prototyping, and as a template for production services.

## **Getting Started**

### **Prerequisites**
- Python 3.8+
- Redis (for storage)
- `grpcio`, `grpcio-tools`, `fastapi`, `uvicorn`, `pydantic` (see `requirements.txt`)

### **Run the gRPC Server**
```bash
python grpc_server.py
```

### **Run the REST Gateway**
```bash
uvicorn fastapi_gateway:app --reload
```

### **Example REST Request**
```bash
curl -X POST -H "Content-Type: application/json" \
    -d '{"id":1,"stock":10,"price":100}' \
    http://127.0.0.1:8000/products/
```

### **Example gRPC Client Call**
```python
import grpc
import product_pb2, product_pb2_grpc
channel = grpc.insecure_channel('localhost:50051')
stub = product_pb2_grpc.ProductServiceStub(channel)
response = stub.CreateProduct(product_pb2.Product(id=1, stock=10, price=100))
```

## **TLS/Encryption**
- gRPC and REST endpoints can be secured with TLS/SSL. See documentation in this repo for enabling secure channels.

## **Why This Pattern?**
- **Microservices ready**: Ideal for environments where both RESTful and high-performance binary APIs are needed.
- **One backend, many clients**: Easily support browsers, mobile, and other services.
- **Strong typing and validation**: Reduces bugs and boosts reliability.

---

## **License**
MIT

---

**Contributions and feedback welcome!**
