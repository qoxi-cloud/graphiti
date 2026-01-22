# Graphiti gRPC Server Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast package management
RUN pip install uv

# Create app directory
WORKDIR /app

# Copy project files
COPY pyproject.toml .
COPY Makefile .

# Install dependencies
RUN uv sync

# Copy proto files and generate Python code
COPY protos/ protos/
RUN mkdir -p src/generated && \
    uv run python -m grpc_tools.protoc \
        -I protos \
        --python_out=src/generated \
        --pyi_out=src/generated \
        --grpc_python_out=src/generated \
        protos/graphiti/v1/*.proto && \
    find src/generated -name "*.py" -exec sed -i 's/from graphiti\.v1 import/from . import/g' {} \; && \
    find src/generated -name "*.py" -exec sed -i 's/import graphiti\.v1\./from . import /g' {} \; && \
    touch src/generated/__init__.py

# Copy source code
COPY src/ src/
COPY config/ config/

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose gRPC port
EXPOSE 50051

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import grpc; channel = grpc.insecure_channel('localhost:50051'); grpc.channel_ready_future(channel).result(timeout=5)" || exit 1

# Run the server
CMD ["uv", "run", "python", "-m", "src.main"]
