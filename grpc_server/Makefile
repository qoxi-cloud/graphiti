.PHONY: all proto format lint test test-integration check clean run docker-build docker-run

# Default target
all: proto format lint test

# Generate Python code from proto files
proto:
	@echo "Generating Python code from proto files..."
	@mkdir -p src/generated
	@uv run python -m grpc_tools.protoc \
		-I protos \
		--python_out=src/generated \
		--pyi_out=src/generated \
		--grpc_python_out=src/generated \
		protos/graphiti/v1/*.proto
	@# Fix imports in generated files
	@find src/generated -name "*.py" -exec sed -i.bak 's/from graphiti\.v1 import/from . import/g' {} \;
	@find src/generated -name "*.py" -exec sed -i.bak 's/import graphiti\.v1\./from . import /g' {} \;
	@find src/generated -name "*.bak" -delete
	@# Create __init__.py files
	@touch src/generated/__init__.py
	@touch src/generated/graphiti/__init__.py 2>/dev/null || true
	@touch src/generated/graphiti/v1/__init__.py 2>/dev/null || true
	@echo "Proto generation complete."

# Format code
format:
	@echo "Formatting code..."
	@uv run ruff format src tests
	@uv run ruff check --fix src tests
	@echo "Formatting complete."

# Lint code
lint:
	@echo "Linting code..."
	@uv run ruff check src tests
	@uv run pyright src
	@echo "Linting complete."

# Run unit tests (excludes integration tests)
test:
	@echo "Running unit tests..."
	@uv run pytest tests/ -v --cov=src --cov-report=term-missing
	@echo "Tests complete."

# Run integration tests
# Requires: running gRPC server with OPENAI_API_KEY and database (FalkorDB/Neo4j)
test-integration:
	@echo "Running integration tests..."
	@uv run pytest tests/integration/ -m integration -v
	@echo "Integration tests complete."

# Run all checks (format, lint, test)
check: format lint test
	@echo "All checks passed."

# Clean generated files
clean:
	@echo "Cleaning generated files..."
	@rm -rf src/generated/*.py src/generated/*.pyi
	@rm -rf __pycache__ .pytest_cache .coverage
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "Clean complete."

# Run the gRPC server
run:
	@echo "Starting gRPC server..."
	@uv run python -m src.main

# Build Docker image
docker-build:
	@echo "Building Docker image..."
	@docker build -t graphiti-grpc-server:latest -f docker/Dockerfile .
	@echo "Docker build complete."

# Run with Docker Compose
docker-run:
	@echo "Starting services with Docker Compose..."
	@docker-compose -f docker/docker-compose.yml up -d
	@echo "Services started."

# Stop Docker Compose services
docker-stop:
	@echo "Stopping services..."
	@docker-compose -f docker/docker-compose.yml down
	@echo "Services stopped."

# Install dependencies
install:
	@echo "Installing dependencies..."
	@uv sync --extra dev
	@echo "Dependencies installed."

# Help
help:
	@echo "Available targets:"
	@echo "  all              - Generate protos, format, lint, and test"
	@echo "  proto            - Generate Python code from proto files"
	@echo "  format           - Format code with ruff"
	@echo "  lint             - Lint code with ruff and pyright"
	@echo "  test             - Run unit tests with pytest"
	@echo "  test-integration - Run integration tests (requires running server)"
	@echo "  check            - Run all checks (format, lint, test)"
	@echo "  clean            - Clean generated files"
	@echo "  run              - Run the gRPC server"
	@echo "  docker-build     - Build Docker image"
	@echo "  docker-run       - Start services with Docker Compose"
	@echo "  docker-stop      - Stop Docker Compose services"
	@echo "  install          - Install dependencies"
	@echo "  help             - Show this help message"
	@echo ""
	@echo "Integration test environment variables:"
	@echo "  OPENAI_API_KEY         - Required for LLM"
	@echo "  FALKORDB_URI           - Database URI (default: redis://localhost:6379)"
	@echo "  GRPC_SERVER_ADDRESS    - Server address (default: localhost:50051)"
