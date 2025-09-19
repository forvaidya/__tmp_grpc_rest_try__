# TLS/SSL Configuration Guide

This document explains how to enable TLS/SSL encryption for both the gRPC server and FastAPI REST gateway.

## Quick Start with Self-Signed Certificates (Development)

For development and testing purposes, you can generate self-signed certificates:

```bash
./generate_certs.sh
```

This will create certificates in the `certs/` directory.

## Running with TLS/SSL

### gRPC Server with TLS

```bash
# Using environment variables
export GRPC_CERT_FILE=certs/server.crt
export GRPC_KEY_FILE=certs/server.key
python grpc_server.py

# Or inline
GRPC_CERT_FILE=certs/server.crt GRPC_KEY_FILE=certs/server.key python grpc_server.py
```

### FastAPI with HTTPS

```bash
# Using environment variables
export SSL_CERT_FILE=certs/server.crt
export SSL_KEY_FILE=certs/server.key
python fastapi_gateway.py

# Or using uvicorn directly
uvicorn fastapi_gateway:app --host 0.0.0.0 --port 8000 --ssl-keyfile certs/server.key --ssl-certfile certs/server.crt
```

### gRPC Client with TLS

```bash
# Enable TLS for gRPC client
export GRPC_USE_TLS=true
export GRPC_CLIENT_CERT_FILE=certs/server.crt
python example_grpc_client.py
```

### REST Client with HTTPS

```bash
# Point to HTTPS endpoint
export REST_API_URL=https://127.0.0.1:8000
python example_rest_client.py
```

## Production Considerations

### Certificate Management

For production environments:

1. **Use certificates from a trusted CA** (Let's Encrypt, DigiCert, etc.)
2. **Store private keys securely** with appropriate file permissions (600)
3. **Implement certificate rotation** before expiration
4. **Use certificate monitoring** to track expiration dates

### Recommended Environment Variables

```bash
# Production gRPC TLS
export GRPC_CERT_FILE=/path/to/production/server.crt
export GRPC_KEY_FILE=/path/to/production/server.key

# Production FastAPI HTTPS
export SSL_CERT_FILE=/path/to/production/server.crt
export SSL_KEY_FILE=/path/to/production/server.key

# Client configuration
export GRPC_USE_TLS=true
export GRPC_CLIENT_CERT_FILE=/path/to/ca-bundle.crt
export REST_API_URL=https://your-api-domain.com
```

### Certificate Formats

- **PEM Format**: Most common, human-readable, used by default
- **DER Format**: Binary format, more compact
- **PKCS#12**: Contains both certificate and private key

### TLS Best Practices

1. **Use TLS 1.2 or higher**
2. **Disable weak cipher suites**
3. **Enable Perfect Forward Secrecy (PFS)**
4. **Use strong key lengths** (2048-bit RSA minimum, 256-bit ECDSA recommended)
5. **Implement certificate pinning** for high-security applications
6. **Monitor certificate expiration**
7. **Use HSTS headers** for web applications

### Example Production Setup

```bash
# Production deployment script
#!/bin/bash

# Set production certificates
export GRPC_CERT_FILE=/etc/ssl/certs/api.example.com.crt
export GRPC_KEY_FILE=/etc/ssl/private/api.example.com.key
export SSL_CERT_FILE=/etc/ssl/certs/api.example.com.crt
export SSL_KEY_FILE=/etc/ssl/private/api.example.com.key

# Start gRPC server
python grpc_server.py &

# Start FastAPI gateway
uvicorn fastapi_gateway:app \
    --host 0.0.0.0 \
    --port 8000 \
    --ssl-keyfile $SSL_KEY_FILE \
    --ssl-certfile $SSL_CERT_FILE \
    --workers 4 &
```

## Troubleshooting

### Common Issues

1. **Certificate not found**: Check file paths and permissions
2. **Permission denied**: Ensure private key has correct permissions (600)
3. **Certificate validation failed**: Check certificate chain and CA trust
4. **Connection refused**: Verify TLS is enabled on both client and server

### Debugging Commands

```bash
# Test certificate validity
openssl x509 -in certs/server.crt -text -noout

# Test gRPC TLS connection
openssl s_client -connect localhost:50051

# Test HTTPS connection
curl -k https://localhost:8000/health
```

### Certificate Expiration Monitoring

```bash
# Check certificate expiration
openssl x509 -in certs/server.crt -enddate -noout

# Automated monitoring script
#!/bin/bash
CERT_FILE="certs/server.crt"
EXPIRY_DATE=$(openssl x509 -in $CERT_FILE -enddate -noout | cut -d= -f2)
EXPIRY_EPOCH=$(date -d "$EXPIRY_DATE" +%s)
CURRENT_EPOCH=$(date +%s)
DAYS_UNTIL_EXPIRY=$(( ($EXPIRY_EPOCH - $CURRENT_EPOCH) / 86400 ))

if [ $DAYS_UNTIL_EXPIRY -lt 30 ]; then
    echo "⚠️  Certificate expires in $DAYS_UNTIL_EXPIRY days!"
fi
```

## Security Headers

The FastAPI gateway automatically includes security headers. For additional security, consider:

- **Content Security Policy (CSP)**
- **X-Frame-Options**
- **X-Content-Type-Options**
- **Strict-Transport-Security (HSTS)**

These can be added using FastAPI middleware or a reverse proxy like nginx.