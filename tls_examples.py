#!/usr/bin/env python3
"""
TLS/SSL Configuration Examples

This file provides examples and instructions for setting up TLS/SSL
encryption for both gRPC and REST endpoints in production.
"""

# =============================================================================
# gRPC TLS Configuration Example
# =============================================================================

"""
To enable TLS for the gRPC server, modify grpc_server.py as follows:

1. Generate server certificates:
   openssl genrsa -out server.key 2048
   openssl req -new -x509 -key server.key -out server.crt -days 365

2. Update the serve() function in grpc_server.py:

def serve(port: int = 50051, use_tls: bool = True):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    product_pb2_grpc.add_ProductServiceServicer_to_server(ProductService(), server)
    
    if use_tls:
        # Load TLS credentials
        with open('server.key', 'rb') as f:
            private_key = f.read()
        with open('server.crt', 'rb') as f:
            certificate_chain = f.read()
        
        credentials = grpc.ssl_server_credentials([(private_key, certificate_chain)])
        server.add_secure_port(f'[::]:{port}', credentials)
        logger.info(f"Starting secure gRPC server on port {port}")
    else:
        server.add_insecure_port(f'[::]:{port}')
        logger.info(f"Starting insecure gRPC server on port {port}")
    
    server.start()
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down gRPC server...")
        server.stop(0)

3. Update gRPC client connections to use SSL:

# In fastapi_gateway.py, update the GrpcClient.connect() method:
def connect(self):
    try:
        # Use secure channel with SSL
        credentials = grpc.ssl_channel_credentials()
        self.channel = grpc.secure_channel(
            f'{self.grpc_host}:{self.grpc_port}', 
            credentials
        )
        self.stub = product_pb2_grpc.ProductServiceStub(self.channel)
        
        # Test connection
        grpc.channel_ready_future(self.channel).result(timeout=5)
        logger.info(f"Connected to secure gRPC server")
    except Exception as e:
        logger.error(f"Failed to connect to gRPC server: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to connect to backend service"
        )
"""

# =============================================================================
# FastAPI HTTPS Configuration Example
# =============================================================================

"""
To enable HTTPS for the FastAPI server:

1. Generate SSL certificates (same as for gRPC or use Let's Encrypt):
   openssl genrsa -out key.pem 2048
   openssl req -new -x509 -key key.pem -out cert.pem -days 365

2. Start uvicorn with SSL options:
   uvicorn fastapi_gateway:app --host 0.0.0.0 --port 8000 \\
     --ssl-keyfile key.pem --ssl-certfile cert.pem

3. Or programmatically in fastapi_gateway.py:

if __name__ == "__main__":
    import uvicorn
    
    # For production with HTTPS
    uvicorn.run(
        "fastapi_gateway:app",
        host="0.0.0.0",
        port=8000,
        ssl_keyfile="key.pem",
        ssl_certfile="cert.pem",
        log_level="info"
    )
"""

# =============================================================================
# Production Deployment Notes
# =============================================================================

"""
For production deployment, consider:

1. Certificate Management:
   - Use Let's Encrypt for free SSL certificates
   - Set up automatic certificate renewal
   - Store certificates securely

2. Security Best Practices:
   - Use strong cipher suites
   - Enable HSTS for HTTPS
   - Implement proper authentication/authorization
   - Use environment variables for sensitive configuration

3. Load Balancing:
   - Place a load balancer (nginx, HAProxy) in front of services
   - Terminate SSL at the load balancer for better performance
   - Use internal HTTP/gRPC for backend communication

4. Monitoring:
   - Set up health checks
   - Monitor certificate expiration
   - Log security events

Example nginx configuration for SSL termination:

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
"""

if __name__ == "__main__":
    print("📖 TLS/SSL Configuration Examples")
    print("==================================")
    print("This file contains examples for setting up TLS/SSL encryption.")
    print("See the source code for detailed configuration examples.")
    print("")
    print("Quick setup for development:")
    print("1. Generate self-signed certificates")
    print("2. Update server configurations")
    print("3. Start services with TLS enabled")
    print("")
    print("For production, use proper CA-signed certificates!")