#!/bin/bash
#
# Generate self-signed TLS certificates for development/testing
#
# This script generates:
#   - CA certificate (ca.crt, ca.key)
#   - Server certificate signed by CA (server.crt, server.key)
#   - Client certificate for mTLS (client.crt, client.key) - optional
#
# Usage:
#   ./generate-certs.sh                    # Generate server certs only
#   ./generate-certs.sh --with-client      # Also generate client certs for mTLS
#   ./generate-certs.sh --clean            # Remove all generated certificates
#
# WARNING: These certificates are for development only.
# For production, use certificates from a trusted CA.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Certificate configuration
DAYS_VALID=365
KEY_SIZE=4096
COUNTRY="US"
STATE="California"
LOCALITY="San Francisco"
ORGANIZATION="Graphiti Development"
ORGANIZATIONAL_UNIT="Development"
COMMON_NAME="localhost"

# Subject Alternative Names for server certificate
# Add your hostnames and IPs here
SAN="DNS:localhost,DNS:graphiti-grpc,DNS:*.local,IP:127.0.0.1,IP:0.0.0.0"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Parse arguments
WITH_CLIENT=false
CLEAN=false

for arg in "$@"; do
    case $arg in
        --with-client)
            WITH_CLIENT=true
            shift
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --with-client    Also generate client certificates for mTLS"
            echo "  --clean          Remove all generated certificates"
            echo "  --help, -h       Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $arg"
            exit 1
            ;;
    esac
done

# Clean up certificates
if [ "$CLEAN" = true ]; then
    print_info "Removing generated certificates..."
    rm -f ca.key ca.crt ca.srl
    rm -f server.key server.csr server.crt
    rm -f client.key client.csr client.crt
    rm -f openssl-san.cnf
    print_info "Certificates removed."
    exit 0
fi

# Check if openssl is available
if ! command -v openssl &> /dev/null; then
    print_error "openssl is required but not installed."
    exit 1
fi

print_info "Generating self-signed certificates for development..."
print_warn "These certificates are for development only. Use proper CA-signed certificates in production."
echo ""

# Create OpenSSL config with SAN extension
cat > openssl-san.cnf << EOF
[req]
default_bits = ${KEY_SIZE}
distinguished_name = req_distinguished_name
req_extensions = req_ext
x509_extensions = v3_ca
prompt = no

[req_distinguished_name]
C = ${COUNTRY}
ST = ${STATE}
L = ${LOCALITY}
O = ${ORGANIZATION}
OU = ${ORGANIZATIONAL_UNIT}
CN = ${COMMON_NAME}

[req_ext]
subjectAltName = ${SAN}

[v3_ca]
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer:always
basicConstraints = critical, CA:true
keyUsage = critical, digitalSignature, cRLSign, keyCertSign

[v3_server]
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid,issuer
basicConstraints = CA:FALSE
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = ${SAN}

[v3_client]
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid,issuer
basicConstraints = CA:FALSE
keyUsage = critical, digitalSignature
extendedKeyUsage = clientAuth
EOF

# Generate CA key and certificate
print_info "Generating CA certificate..."
openssl genrsa -out ca.key ${KEY_SIZE} 2>/dev/null
openssl req -x509 -new -nodes \
    -key ca.key \
    -sha256 \
    -days ${DAYS_VALID} \
    -out ca.crt \
    -config openssl-san.cnf \
    -extensions v3_ca

print_info "CA certificate generated: ca.crt"

# Generate server key and CSR
print_info "Generating server certificate..."
openssl genrsa -out server.key ${KEY_SIZE} 2>/dev/null
openssl req -new \
    -key server.key \
    -out server.csr \
    -config openssl-san.cnf

# Sign server certificate with CA
openssl x509 -req \
    -in server.csr \
    -CA ca.crt \
    -CAkey ca.key \
    -CAcreateserial \
    -out server.crt \
    -days ${DAYS_VALID} \
    -sha256 \
    -extfile openssl-san.cnf \
    -extensions v3_server 2>/dev/null

print_info "Server certificate generated: server.crt"

# Generate client certificate if requested (for mTLS)
if [ "$WITH_CLIENT" = true ]; then
    print_info "Generating client certificate for mTLS..."

    openssl genrsa -out client.key ${KEY_SIZE} 2>/dev/null
    openssl req -new \
        -key client.key \
        -out client.csr \
        -subj "/C=${COUNTRY}/ST=${STATE}/L=${LOCALITY}/O=${ORGANIZATION}/OU=Client/CN=graphiti-client"

    openssl x509 -req \
        -in client.csr \
        -CA ca.crt \
        -CAkey ca.key \
        -CAcreateserial \
        -out client.crt \
        -days ${DAYS_VALID} \
        -sha256 \
        -extfile openssl-san.cnf \
        -extensions v3_client 2>/dev/null

    print_info "Client certificate generated: client.crt"
fi

# Clean up temporary files
rm -f server.csr client.csr openssl-san.cnf

# Set proper permissions
chmod 600 *.key
chmod 644 *.crt

echo ""
print_info "Certificate generation complete!"
echo ""
echo "Generated files:"
echo "  - ca.crt       : CA certificate (share with clients for verification)"
echo "  - ca.key       : CA private key (keep secure, for signing only)"
echo "  - server.crt   : Server certificate"
echo "  - server.key   : Server private key"
if [ "$WITH_CLIENT" = true ]; then
    echo "  - client.crt   : Client certificate (for mTLS)"
    echo "  - client.key   : Client private key (for mTLS)"
fi
echo ""
echo "To verify the server certificate:"
echo "  openssl verify -CAfile ca.crt server.crt"
echo ""
echo "To view certificate details:"
echo "  openssl x509 -in server.crt -text -noout"
echo ""
echo "To test with grpcurl:"
echo "  grpcurl -cacert certs/ca.crt localhost:50051 list"
echo ""
if [ "$WITH_CLIENT" = true ]; then
    echo "To test with grpcurl using mTLS:"
    echo "  grpcurl -cacert certs/ca.crt -cert certs/client.crt -key certs/client.key localhost:50051 list"
    echo ""
fi
