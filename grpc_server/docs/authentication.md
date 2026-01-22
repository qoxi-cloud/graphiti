# gRPC Authentication

The Graphiti gRPC server supports authentication via API keys or JWT tokens to secure your endpoints.

## Authentication Methods

### 1. API Key Authentication

API key authentication uses the `x-api-key` metadata header. This is the simplest authentication method and is suitable for server-to-server communication.

#### Configuration

**Via YAML config file (`config/config.yaml`):**

```yaml
grpc:
  auth:
    enabled: true
    api_keys:
      - "your-api-key-1"
      - "your-api-key-2"
      - "your-api-key-3"
```

**Via Environment Variables:**

```bash
GRPC__AUTH__ENABLED=true
GRPC__AUTH__API_KEYS='["key1", "key2"]'
```

#### Client Usage

**Python (using grpcio):**

```python
import grpc
from generated.graphiti.v1 import ingest_service_pb2_grpc, ingest_service_pb2

# Create channel
channel = grpc.insecure_channel('localhost:50051')

# Create stub with API key metadata
stub = ingest_service_pb2_grpc.IngestServiceStub(channel)

# Add API key to metadata
metadata = [('x-api-key', 'your-api-key-1')]

# Make authenticated request
request = ingest_service_pb2.AddEpisodeRequest(
    group_id='my-group',
    content='Episode content...'
)
response = stub.AddEpisode(request, metadata=metadata)
```

**grpcurl:**

```bash
grpcurl \
  -H "x-api-key: your-api-key-1" \
  -d '{"group_id": "my-group", "content": "Episode content..."}' \
  localhost:50051 \
  graphiti.v1.IngestService/AddEpisode
```

### 2. JWT Token Authentication

JWT (JSON Web Token) authentication uses the `authorization` metadata header with a Bearer token. This method supports token expiration and is suitable for user authentication.

#### Configuration

**Via YAML config file:**

```yaml
grpc:
  auth:
    enabled: true
    jwt_secret: "your-secret-key-here"
    jwt_algorithm: "HS256"  # Optional, defaults to HS256
```

**Via Environment Variables:**

```bash
GRPC__AUTH__ENABLED=true
GRPC__AUTH__JWT_SECRET="your-secret-key-here"
GRPC__AUTH__JWT_ALGORITHM="HS256"
```

#### Token Generation

Tokens must include `exp` (expiration) and `iat` (issued at) claims:

```python
import jwt
import time

secret = 'your-secret-key-here'

# Create JWT token
payload = {
    'user_id': '12345',
    'group_id': 'my-group',
    'exp': time.time() + 3600,  # Expires in 1 hour
    'iat': time.time(),          # Issued now
}

token = jwt.encode(payload, secret, algorithm='HS256')
print(f"Token: {token}")
```

#### Client Usage

**Python:**

```python
import grpc
from generated.graphiti.v1 import ingest_service_pb2_grpc, ingest_service_pb2

# Create channel
channel = grpc.insecure_channel('localhost:50051')
stub = ingest_service_pb2_grpc.IngestServiceStub(channel)

# Add Bearer token to metadata
token = "eyJ0eXAiOiJKV1QiLCJhbGc..."  # Your JWT token
metadata = [('authorization', f'Bearer {token}')]

# Make authenticated request
request = ingest_service_pb2.AddEpisodeRequest(
    group_id='my-group',
    content='Episode content...'
)
response = stub.AddEpisode(request, metadata=metadata)
```

**grpcurl:**

```bash
grpcurl \
  -H "authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
  -d '{"group_id": "my-group", "content": "Episode content..."}' \
  localhost:50051 \
  graphiti.v1.IngestService/AddEpisode
```

## Configuration Options

### Complete Configuration Example

```yaml
grpc:
  host: "0.0.0.0"
  port: 50051
  auth:
    enabled: true                    # Enable/disable authentication
    api_keys:                        # List of valid API keys
      - "api-key-for-service-a"
      - "api-key-for-service-b"
    jwt_secret: "your-jwt-secret"    # Secret for JWT verification
    jwt_algorithm: "HS256"           # JWT algorithm (HS256, HS512, RS256, etc.)
    skip_health_check: true          # Skip auth for health checks
```

### Configuration Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | boolean | `false` | Enable or disable authentication |
| `api_keys` | list[string] | `[]` | List of valid API keys |
| `jwt_secret` | string | `null` | Secret key for JWT token verification |
| `jwt_algorithm` | string | `"HS256"` | Algorithm for JWT verification |
| `skip_health_check` | boolean | `true` | Whether to skip auth for health check endpoints |

## Health Check Exemption

By default, health check endpoints (`/grpc.health.v1.Health/Check` and `/grpc.health.v1.Health/Watch`) skip authentication. This allows load balancers and monitoring systems to check server health without credentials.

To require authentication for health checks:

```yaml
grpc:
  auth:
    enabled: true
    skip_health_check: false  # Require auth for health checks
    api_keys:
      - "monitoring-api-key"
```

## Authentication Priority

When both API key and JWT token are provided, the server attempts authentication in this order:

1. **API Key** (via `x-api-key` header)
2. **JWT Token** (via `authorization` header)

The first successful authentication method is used.

## Security Best Practices

### API Keys

1. **Generate Strong Keys**: Use cryptographically secure random strings (at least 32 characters)
   ```python
   import secrets
   api_key = secrets.token_urlsafe(32)
   ```

2. **Rotate Keys Regularly**: Change API keys periodically and when team members leave

3. **Use Different Keys per Client**: Assign unique API keys to each client for easier revocation

4. **Store Keys Securely**: Never commit API keys to source control. Use environment variables or secret management services

5. **Use TLS/SSL**: Always use TLS in production to prevent key interception

### JWT Tokens

1. **Use Strong Secrets**: JWT secrets should be at least 32 bytes of random data
   ```python
   import secrets
   jwt_secret = secrets.token_urlsafe(32)
   ```

2. **Set Appropriate Expiration**: Use short-lived tokens (15-60 minutes) and implement refresh tokens for longer sessions

3. **Include Required Claims**: Always include `exp` and `iat` claims for security

4. **Validate All Claims**: The server validates signature, expiration, and issued-at time

5. **Use Strong Algorithms**: Prefer HS256 or RS256. Avoid weak algorithms like HS1

## Error Responses

### Authentication Required

When no credentials are provided:

```
Code: UNAUTHENTICATED
Message: "Authentication required"
```

### Invalid API Key

When an invalid API key is provided:

```
Code: UNAUTHENTICATED
Message: "Invalid API key"
```

### Invalid Token

When an invalid or malformed JWT is provided:

```
Code: UNAUTHENTICATED
Message: "Invalid token"
```

### Expired Token

When an expired JWT is provided:

```
Code: UNAUTHENTICATED
Message: "Invalid token"
```

## Disabling Authentication

For development or testing, you can disable authentication:

```yaml
grpc:
  auth:
    enabled: false
```

Or via environment variable:

```bash
GRPC__AUTH__ENABLED=false
```

## Integration Example

### Using Auth Interceptor in Server Code

The auth interceptor is automatically integrated when configured. Here's how it works internally:

```python
from src.interceptors import AuthInterceptor, AuthConfig

# Create auth configuration from server config
auth_config = AuthConfig(
    enabled=config.grpc.auth.enabled,
    api_keys=set(config.grpc.auth.api_keys),
    jwt_secret=config.grpc.auth.jwt_secret,
    jwt_algorithm=config.grpc.auth.jwt_algorithm,
    skip_health_check=config.grpc.auth.skip_health_check,
)

# Create interceptor
auth_interceptor = AuthInterceptor(auth_config)

# Add to server interceptor chain
interceptors = [
    auth_interceptor,  # Authentication first
    LoggingInterceptor(),
    ErrorInterceptor(),
]

server = grpc.aio.server(
    futures.ThreadPoolExecutor(max_workers=10),
    interceptors=interceptors,
)
```

## Troubleshooting

### Authentication Always Fails

1. Check that `enabled: true` in configuration
2. Verify API key or JWT secret matches between client and server
3. Check metadata header names (`x-api-key` or `authorization`)
4. For JWT, ensure token includes `exp` and `iat` claims

### Health Checks Fail

If your monitoring system can't access health checks:

1. Set `skip_health_check: true` in auth configuration
2. Or provide authentication credentials to your monitoring system

### JWT Validation Fails

1. Ensure PyJWT is installed: `pip install pyjwt`
2. Verify token isn't expired
3. Check that `jwt_secret` matches the secret used to sign the token
4. Verify `jwt_algorithm` matches the algorithm used to sign the token

### Performance Concerns

The authentication interceptor uses:
- **Constant-time comparison** for API keys (prevents timing attacks)
- **Input validation** to reject excessively long keys/tokens (prevents DoS)
- **Efficient short-circuit** logic (API key checked before JWT)

For high-throughput systems, consider:
- Using API keys instead of JWT (faster validation)
- Caching JWT validation results with short TTL
- Using client-side TLS certificates for mutual TLS authentication
