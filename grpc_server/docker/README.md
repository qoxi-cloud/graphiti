# Graphiti gRPC Server Docker Deployment

This directory contains Docker configuration for deploying the Graphiti gRPC server.

## Quick Start

### Running with Combined Image (All-in-One)

```bash
# Set your OpenAI API key
export OPENAI_API_KEY="your-api-key"

# Start the server (FalkorDB embedded)
docker-compose up -d

# View logs
docker-compose logs -f graphiti-grpc

# Stop the server
docker-compose down
```

### Running with Separate FalkorDB Service

```bash
export OPENAI_API_KEY="your-api-key"
docker-compose -f docker-compose-falkordb.yml up -d
```

### Running with Neo4j

```bash
export OPENAI_API_KEY="your-api-key"
docker-compose -f docker-compose-neo4j.yml up -d
```

The server will be available at `localhost:50051`.

## Configuration Files

| File | Description |
|------|-------------|
| `docker-compose.yml` | Combined image (FalkorDB embedded) |
| `docker-compose-falkordb.yml` | Separate FalkorDB service |
| `docker-compose-neo4j.yml` | Neo4j database |
| `docker-compose.tls.yml` | TLS overlay (use with -falkordb.yml) |
| `certs/generate-certs.sh` | Certificate generation script |
| `../config/config-tls.yaml` | Server config with TLS enabled |

## TLS/SSL Configuration

For production deployments or when security is required, enable TLS encryption.

### Step 1: Generate Certificates

For development/testing, generate self-signed certificates:

```bash
cd certs

# Generate server certificates only
./generate-certs.sh

# Or generate with client certificates for mTLS
./generate-certs.sh --with-client
```

This creates:
- `ca.crt` - CA certificate (share with clients)
- `ca.key` - CA private key (keep secure)
- `server.crt` - Server certificate
- `server.key` - Server private key
- `client.crt` - Client certificate (if using mTLS)
- `client.key` - Client private key (if using mTLS)

For production, use certificates from a trusted Certificate Authority.

### Step 2: Start with TLS

```bash
export OPENAI_API_KEY="your-api-key"
docker-compose -f docker-compose-falkordb.yml -f docker-compose.tls.yml up -d
```

### Step 3: Connect to the TLS-enabled Server

#### Using grpcurl

```bash
# List available services
grpcurl -cacert certs/ca.crt localhost:50051 list

# Call a method
grpcurl -cacert certs/ca.crt \
  -d '{"group_id": "test"}' \
  localhost:50051 graphiti.v1.RetrieveService/Search

# With reflection disabled, import protos
grpcurl -cacert certs/ca.crt \
  -import-path ../protos \
  -proto graphiti/v1/retrieve_service.proto \
  localhost:50051 list
```

#### Using grpcurl with mTLS

If you generated client certificates:

```bash
grpcurl \
  -cacert certs/ca.crt \
  -cert certs/client.crt \
  -key certs/client.key \
  localhost:50051 list
```

#### Python Client

```python
import grpc

# Load certificates
with open('certs/ca.crt', 'rb') as f:
    ca_cert = f.read()

# Create secure channel
credentials = grpc.ssl_channel_credentials(root_certificates=ca_cert)
channel = grpc.secure_channel('localhost:50051', credentials)

# For mTLS, also provide client certificate:
# with open('certs/client.crt', 'rb') as f:
#     client_cert = f.read()
# with open('certs/client.key', 'rb') as f:
#     client_key = f.read()
# credentials = grpc.ssl_channel_credentials(
#     root_certificates=ca_cert,
#     private_key=client_key,
#     certificate_chain=client_cert
# )
```

### Certificate Management

#### Verify Certificates

```bash
# Verify server certificate against CA
openssl verify -CAfile certs/ca.crt certs/server.crt

# View certificate details
openssl x509 -in certs/server.crt -text -noout

# Check certificate expiration
openssl x509 -in certs/server.crt -noout -dates
```

#### Clean Up Certificates

```bash
cd certs
./generate-certs.sh --clean
```

### TLS Configuration Options

The TLS configuration is controlled via the config file (`config/config-tls.yaml`) or environment variables:

| Config Key | Environment Variable | Description |
|------------|---------------------|-------------|
| `grpc.enable_tls` | `GRPC_ENABLE_TLS` | Enable/disable TLS |
| `grpc.cert_path` | `GRPC_CERT_PATH` | Path to server certificate |
| `grpc.key_path` | `GRPC_KEY_PATH` | Path to server private key |

## Troubleshooting

### Certificate Errors

**Error: "certificate signed by unknown authority"**
- Ensure you're using the correct CA certificate
- For grpcurl: use `-cacert certs/ca.crt`
- For code: load the CA certificate as root certificates

**Error: "certificate is valid for X, not Y"**
- The hostname doesn't match the certificate's SAN (Subject Alternative Name)
- Regenerate certificates with the correct hostname in `generate-certs.sh`
- Or use `localhost` as the hostname

### Connection Errors

**Error: "connection refused"**
- Check if the server is running: `docker-compose ps`
- Verify the port is correct (default: 50051)
- Check logs: `docker-compose logs graphiti-grpc`

**Error: "transport: authentication handshake failed"**
- Ensure TLS is enabled on both client and server
- Verify certificate paths are correct
- Check certificate validity: `openssl verify -CAfile certs/ca.crt certs/server.crt`

### Health Checks

With TLS enabled, the default health check may not work. You can manually check:

```bash
# Check if the container is running
docker-compose ps

# Check server logs
docker-compose logs graphiti-grpc | tail -20

# Use grpcurl for health check
grpcurl -cacert certs/ca.crt localhost:50051 grpc.health.v1.Health/Check
```

## Security Best Practices

1. **Production Certificates**: Use certificates from a trusted CA (Let's Encrypt, DigiCert, etc.)
2. **Key Protection**: Never commit private keys to version control
3. **Certificate Rotation**: Rotate certificates before expiration
4. **mTLS**: Consider mutual TLS for service-to-service communication
5. **Secrets Management**: Use Docker secrets or vault for production deployments

## File Structure

```
grpc_server/
├── config/
│   ├── config.yaml                 # Base configuration
│   ├── config-docker-falkordb.yaml # Docker FalkorDB config
│   ├── config-docker-neo4j.yaml    # Docker Neo4j config
│   └── config-tls.yaml             # TLS-enabled config
└── docker/
    ├── docker-compose.yml          # Combined image (all-in-one)
    ├── docker-compose-falkordb.yml # Separate FalkorDB service
    ├── docker-compose-neo4j.yml    # Neo4j variant
    ├── docker-compose.tls.yml      # TLS overlay
    ├── Dockerfile                  # Server image
    ├── README.md                   # This file
    └── certs/
        ├── generate-certs.sh       # Certificate generation script
        ├── .gitignore              # Ignore generated certs
        ├── ca.crt                  # CA certificate (generated)
        ├── ca.key                  # CA private key (generated)
        ├── server.crt              # Server certificate (generated)
        └── server.key              # Server private key (generated)
```
