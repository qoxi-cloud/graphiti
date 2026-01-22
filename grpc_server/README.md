# Graphiti gRPC Server

Graphiti is a framework for building and querying temporally-aware knowledge graphs, specifically tailored for AI agents
operating in dynamic environments. Unlike traditional retrieval-augmented generation (RAG) methods, Graphiti
continuously integrates user interactions, structured and unstructured enterprise data, and external information into a
coherent, queryable graph. The framework supports incremental data updates, efficient retrieval, and precise historical
queries without requiring complete graph recomputation, making it suitable for developing interactive, context-aware AI
applications.

This is a high-performance gRPC server implementation for Graphiti. The gRPC server exposes Graphiti's key functionality
through the gRPC protocol, enabling efficient communication with low latency and support for streaming operations.

## Features

The Graphiti gRPC server provides comprehensive knowledge graph capabilities:

- **Episode Management**: Add, retrieve, and delete episodes (text, messages, or JSON data)
- **Entity Management**: Search and manage entity nodes and relationships in the knowledge graph
- **Search Capabilities**: Search for facts (edges) and node summaries using semantic and hybrid search
- **Group Management**: Organize and manage groups of related data with group_id filtering
- **Graph Maintenance**: Clear the graph and rebuild indices
- **Graph Database Support**: Multiple backend options including FalkorDB (default) and Neo4j
- **Multiple LLM Providers**: Support for OpenAI, Anthropic, Gemini, Groq, and Azure OpenAI
- **Multiple Embedding Providers**: Support for OpenAI, Voyage, and Gemini embeddings
- **Streaming Support**: Server streaming for bulk operations and bidirectional streaming for continuous ingestion
- **Health Checking**: gRPC health protocol support for load balancers and orchestrators
- **Reflection**: Service discovery for tools like grpcurl
- **TLS/SSL**: Secure communication with certificate support
- **Authentication**: API key and JWT token authentication
- **Rate Limiting**: Per-client rate limiting with sliding window algorithm
- **Compression**: gzip/deflate compression for large payloads
- **Configurable Timeouts**: Per-service and per-method timeout configuration
- **OpenTelemetry**: Distributed tracing integration

## Quick Start

### Clone the Graphiti GitHub repo

```bash
git clone https://github.com/getzep/graphiti.git
```

or

```bash
gh repo clone getzep/graphiti
```

### Using Docker Compose (Recommended)

1. Change directory to the `grpc_server` directory

```bash
cd graphiti/grpc_server
```

2. Start the combined FalkorDB + gRPC server using Docker Compose

```bash
docker compose -f docker/docker-compose.yml up
```

This starts both FalkorDB and the gRPC server in a single container.

**Alternative**: Run with separate containers:
```bash
# FalkorDB as separate service
docker compose -f docker/docker-compose-falkordb.yml up

# Or with Neo4j
docker compose -f docker/docker-compose-neo4j.yml up
```

3. Verify the server is running

```bash
grpcurl -plaintext localhost:50051 list
```

## Installation

### Prerequisites

1. Docker and Docker Compose (for the default FalkorDB setup)
2. OpenAI API key for LLM operations (or API keys for other supported LLM providers)
3. (Optional) Python 3.10+ if running the gRPC server standalone with an external database

### Setup

1. Clone the repository and navigate to the grpc_server directory
2. Use `uv` to create a virtual environment and install dependencies:

```bash
# Install uv if you don't have it already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create a virtual environment and install dependencies
uv sync

# Optional: Install development dependencies
uv sync --extra dev
```

3. Generate proto files

```bash
make proto
```

## Configuration

The server can be configured using a `config.yaml` file, environment variables, or command-line arguments (in order of precedence).

### Default Configuration

The gRPC server comes with sensible defaults:
- **Port**: 50051
- **Database**: FalkorDB (combined in single container with gRPC server)
- **LLM**: OpenAI with model gpt-4o-mini
- **Embedder**: OpenAI text-embedding-3-small

### Database Configuration

#### FalkorDB (Default)

FalkorDB is a Redis-based graph database that comes bundled with the gRPC server in a single Docker container.

```yaml
database:
  provider: "falkordb"
  providers:
    falkordb:
      uri: "redis://localhost:6379"
      password: ""
      database: "default_db"
```

#### Neo4j

For production use or when you need a full-featured graph database:

```yaml
database:
  provider: "neo4j"
  providers:
    neo4j:
      uri: "bolt://localhost:7687"
      username: "neo4j"
      password: "your_password"
      database: "neo4j"
```

### Configuration File (config.yaml)

The server supports multiple LLM providers and embedders. Edit `config/config.yaml` to configure:

```yaml
grpc:
  host: "0.0.0.0"
  port: 50051
  max_workers: 10
  enable_reflection: true

llm:
  provider: "openai"  # or "anthropic", "gemini", "groq", "azure_openai"
  model: "gpt-4o-mini"

embedder:
  provider: "openai"
  model: "text-embedding-3-small"

database:
  provider: "falkordb"  # or "neo4j"
```

### Environment Variables

The `config.yaml` file supports environment variable expansion using `${VAR_NAME}` or `${VAR_NAME:default}` syntax. Key variables:

- `OPENAI_API_KEY`: OpenAI API key (required for OpenAI LLM/embedder)
- `ANTHROPIC_API_KEY`: Anthropic API key (for Claude models)
- `GOOGLE_API_KEY`: Google API key (for Gemini models)
- `GROQ_API_KEY`: Groq API key (for Groq models)
- `AZURE_OPENAI_API_KEY`: Azure OpenAI API key
- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI endpoint URL
- `NEO4J_URI`: URI for the Neo4j database (default: `bolt://localhost:7687`)
- `NEO4J_USER`: Neo4j username (default: `neo4j`)
- `NEO4J_PASSWORD`: Neo4j password
- `FALKORDB_URI`: URI for FalkorDB (default: `redis://localhost:6379`)
- `FALKORDB_PASSWORD`: FalkorDB password
- `SEMAPHORE_LIMIT`: Episode processing concurrency (default: 10)

You can set these variables in a `.env` file in the project directory.

## Running the Server

### Default Setup (FalkorDB Combined Container)

```bash
cd grpc_server
docker compose -f docker/docker-compose.yml up
```

This starts a single container with:
- gRPC server on `localhost:50051`
- FalkorDB graph database on `localhost:6379`
- FalkorDB web UI on `http://localhost:3000`

### Running with Separate FalkorDB

```bash
docker compose -f docker/docker-compose-falkordb.yml up
```

### Running with Neo4j

```bash
docker compose -f docker/docker-compose-neo4j.yml up
```

Default Neo4j credentials:
- Username: `neo4j`
- Password: `demodemo`
- Bolt URI: `bolt://neo4j:7687`
- Browser UI: `http://localhost:7474`

### Running Standalone

If you have a database already running:

```bash
# Set environment variables
export OPENAI_API_KEY="your-api-key"
export FALKORDB_URI="redis://localhost:6379"

# Run the server
uv run python -m src.main
```

### Available Command-Line Arguments

- `--host`: Server host (default: 0.0.0.0)
- `--port`: Server port (default: 50051)
- `--max-workers`: Maximum worker threads (default: 10)
- `--llm-provider`: LLM provider (openai, anthropic, gemini, groq)
- `--model`: LLM model name
- `--embedder-provider`: Embedder provider (openai, voyage, gemini)
- `--database-provider`: Database provider (falkordb, neo4j)
- `--group-id`: Default group ID
- `--user-id`: Default user ID

## Services

### IngestService

| Method | Description |
|--------|-------------|
| `AddEpisode` | Add a single episode to the knowledge graph |
| `AddEpisodeBulk` | Bulk add episodes with streaming progress |
| `AddMessages` | Add chat messages asynchronously |
| `AddEntityNode` | Add entity node directly |
| `AddTriplet` | Add subject-predicate-object triplet |
| `StreamEpisodes` | Bidirectional streaming for continuous ingestion |

### RetrieveService

| Method | Description |
|--------|-------------|
| `Search` | Simple fact search |
| `AdvancedSearch` | Full search configuration support |
| `StreamSearch` | Streaming search results |
| `GetEntityEdge` | Get edge by UUID |
| `GetEntityEdges` | Get multiple edges by UUIDs |
| `GetEpisodes` | Get episodes for group |
| `GetMemory` | Contextual retrieval for conversations |
| `GetEntityNode` | Get entity node by UUID |
| `GetEntityNodes` | Get nodes by group with pagination |
| `GetCommunities` | Get communities by group |
| `SearchNodes` | Search nodes by query and entity types |
| `SearchFacts` | Search facts with optional center node |

### AdminService

| Method | Description |
|--------|-------------|
| `HealthCheck` | Health status |
| `GetStatus` | Server status with uptime and provider info |
| `DeleteEntityEdge` | Delete edge by UUID |
| `DeleteEntityEdges` | Batch delete edges |
| `DeleteGroup` | Delete entire group |
| `DeleteEpisode` | Delete episode by UUID |
| `DeleteEpisodes` | Batch delete episodes |
| `DeleteEntityNode` | Delete entity node |
| `ClearData` | Clear all data (requires confirmation) |
| `BuildIndices` | Build indices and constraints |
| `BuildCommunities` | Build communities for groups |

## Docker Deployment

### Environment Configuration

Before running Docker Compose, configure your API keys using a `.env` file:

1. **Create a .env file in the grpc_server directory**:
   ```bash
   cd graphiti/grpc_server
   cp .env.example .env
   ```

2. **Edit the .env file** to set your API keys:
   ```bash
   OPENAI_API_KEY=your_openai_api_key_here
   ```

### Docker Compose Options

| File | Description |
|------|-------------|
| `docker/docker-compose.yml` | Combined image (FalkorDB embedded) |
| `docker/docker-compose-falkordb.yml` | Separate FalkorDB service |
| `docker/docker-compose-neo4j.yml` | Neo4j database |
| `docker/docker-compose.tls.yml` | TLS overlay |

```bash
# All-in-one (recommended for development)
docker compose -f docker/docker-compose.yml up

# Separate FalkorDB
docker compose -f docker/docker-compose-falkordb.yml up

# Neo4j
docker compose -f docker/docker-compose-neo4j.yml up

# With TLS
docker compose -f docker/docker-compose-falkordb.yml -f docker/docker-compose.tls.yml up
```

## TLS/SSL Configuration

For production deployments, enable TLS encryption.

### Generate Certificates

```bash
cd docker/certs
./generate-certs.sh
```

### Start with TLS

```bash
docker compose -f docker/docker-compose-falkordb.yml -f docker/docker-compose.tls.yml up
```

### Connect with TLS

```bash
# Using grpcurl
grpcurl -cacert docker/certs/ca.crt localhost:50051 list

# Python client
import grpc
with open('docker/certs/ca.crt', 'rb') as f:
    ca_cert = f.read()
credentials = grpc.ssl_channel_credentials(root_certificates=ca_cert)
channel = grpc.secure_channel('localhost:50051', credentials)
```

See `docker/README.md` for detailed TLS setup instructions.

## Authentication

The gRPC server supports API key and JWT token authentication.

### Configuration

```yaml
grpc:
  auth:
    enabled: true
    api_keys:
      - "your-api-key"
    jwt_secret: "your-jwt-secret"
    jwt_algorithm: "HS256"
    skip_health_check: true
```

### Client Usage

```python
# API Key
metadata = [('x-api-key', 'your-api-key')]
response = stub.AddEpisode(request, metadata=metadata)

# JWT
metadata = [('authorization', 'Bearer your-jwt-token')]
response = stub.AddEpisode(request, metadata=metadata)
```

## Rate Limiting

Per-client rate limiting with sliding window algorithm.

### Configuration

```yaml
grpc:
  rate_limit:
    enabled: true
    window_seconds: 60
    max_requests: 100
    read_max_requests: 200  # Higher limit for read operations
    write_max_requests: 50  # Lower limit for write operations
```

## Compression

Enable gzip or deflate compression for large payloads (bulk operations, large search results).

### Configuration

```yaml
grpc:
  compression:
    enabled: true
    algorithm: "gzip"  # gzip, deflate, or none
    level: 2           # 0-9 (0=no compression, 9=maximum)
```

Compression is enabled by default. Clients can also request compression per-call.

## Timeouts

Configure per-service and per-method timeouts for fine-grained control.

### Configuration

```yaml
grpc:
  timeouts:
    enabled: true
    default: 30  # Global default (seconds)
    services:
      IngestService:
        default: 120
        methods:
          AddEpisodeBulk: 600    # 10 minutes for bulk operations
          StreamEpisodes: 0      # No timeout for streaming
      RetrieveService:
        default: 30
        methods:
          StreamSearch: 0
          RetrieveEpisodes: 0
      AdminService:
        default: 60
        methods:
          BuildCommunities: 300  # 5 minutes
          ClearData: 120
```

Timeout resolution order: Method → Service → Global default. Set to `0` to disable timeout (useful for streaming).

## Client Examples

### Python (Async)

```python
import grpc
from generated.graphiti.v1 import ingest_service_pb2, ingest_service_pb2_grpc

async with grpc.aio.insecure_channel('localhost:50051') as channel:
    stub = ingest_service_pb2_grpc.IngestServiceStub(channel)

    request = ingest_service_pb2.AddEpisodeRequest(
        name="Test Episode",
        episode_body="This is a test episode content.",
        source_description="Test source",
        group_id="main",
    )

    response = await stub.AddEpisode(request)
    print(f"Episode UUID: {response.episode.uuid}")
```

### grpcurl

```bash
# List services
grpcurl -plaintext localhost:50051 list

# Health check
grpcurl -plaintext localhost:50051 graphiti.v1.AdminService/HealthCheck

# Add episode
grpcurl -plaintext -d '{
  "name": "Test Episode",
  "episode_body": "This is test content",
  "source_description": "grpcurl test",
  "group_id": "main"
}' localhost:50051 graphiti.v1.IngestService/AddEpisode

# Search
grpcurl -plaintext -d '{
  "query": "test",
  "group_ids": ["main"],
  "num_results": 10
}' localhost:50051 graphiti.v1.RetrieveService/Search
```

## Development

### Building

```bash
# Install dependencies
uv sync --extra dev

# Generate proto files
make proto

# Run linter
make lint

# Run tests
make test

# Format code
make format
```

### Proto Generation

Proto files are located in `protos/graphiti/v1/`. To regenerate:

```bash
make proto
```

Generated files are placed in `src/generated/`.

## Requirements

- Python 3.10 or higher
- OpenAI API key (or other LLM provider API keys)
- Docker and Docker Compose (for the default FalkorDB setup)
- (Optional) Neo4j database (version 5.26 or later)

## License

Apache-2.0
