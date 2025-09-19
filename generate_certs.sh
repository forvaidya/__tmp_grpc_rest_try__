#!/bin/bash

# Script to generate self-signed TLS/SSL certificates for development
# DO NOT use these certificates in production!

echo "🔐 Generating self-signed TLS/SSL certificates for development..."

# Create certificates directory
mkdir -p certs

# Generate private key for the server
openssl genrsa -out certs/server.key 4096

# Generate certificate signing request
openssl req -new -key certs/server.key -out certs/server.csr -subj "/C=US/ST=Dev/L=Dev/O=Dev/OU=Dev/CN=localhost"

# Generate self-signed certificate
openssl x509 -req -days 365 -in certs/server.csr -signkey certs/server.key -out certs/server.crt

# Generate combined certificate file for some applications
cat certs/server.crt certs/server.key > certs/server.pem

# Set appropriate permissions
chmod 600 certs/server.key
chmod 644 certs/server.crt
chmod 644 certs/server.pem

echo "✅ Certificates generated in ./certs/ directory:"
echo "   - server.key (private key)"
echo "   - server.crt (certificate)"
echo "   - server.pem (combined)"
echo ""
echo "⚠️  These are self-signed certificates for development only!"
echo "   For production, use certificates from a trusted CA."
echo ""
echo "To use these certificates:"
echo "  gRPC Server: GRPC_CERT_FILE=certs/server.crt GRPC_KEY_FILE=certs/server.key python grpc_server.py"
echo "  FastAPI: SSL_CERT_FILE=certs/server.crt SSL_KEY_FILE=certs/server.key python fastapi_gateway.py"
echo "  gRPC Client: GRPC_USE_TLS=true GRPC_CLIENT_CERT_FILE=certs/server.crt python example_grpc_client.py"
echo "  REST Client: REST_API_URL=https://127.0.0.1:8000 python example_rest_client.py"