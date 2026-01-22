"""Main entry point for the Graphiti gRPC server."""

import argparse
import asyncio
import logging
import signal
import sys
import time
from concurrent import futures

import grpc
from graphiti_core import Graphiti
from grpc_health.v1 import health, health_pb2, health_pb2_grpc
from grpc_reflection.v1alpha import reflection

from src.config.schema import GraphitiGRPCConfig
from src.generated.graphiti.v1 import (
    admin_service_pb2,
    admin_service_pb2_grpc,
    ingest_service_pb2,
    ingest_service_pb2_grpc,
    retrieve_service_pb2,
    retrieve_service_pb2_grpc,
)
from src.interceptors import (
    AuthInterceptor,
    ErrorInterceptor,
    LoggingInterceptor,
    RateLimitInterceptor,
    TimeoutInterceptor,
    TracingInterceptor,
)
from src.services import AdminServiceServicer, IngestServiceServicer, RetrieveServiceServicer
from src.utils.factories import DatabaseDriverFactory, EmbedderFactory, LLMClientFactory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Graphiti gRPC Server')

    # Server options
    parser.add_argument('--host', type=str, help='Server host')
    parser.add_argument('--port', type=int, help='Server port')
    parser.add_argument('--max-workers', type=int, help='Maximum number of worker threads')

    # LLM options
    parser.add_argument('--llm-provider', type=str, help='LLM provider')
    parser.add_argument('--model', type=str, help='LLM model name')
    parser.add_argument('--temperature', type=float, help='LLM temperature')

    # Embedder options
    parser.add_argument('--embedder-provider', type=str, help='Embedder provider')
    parser.add_argument('--embedder-model', type=str, help='Embedder model name')

    # Database options
    parser.add_argument('--database-provider', type=str, help='Database provider')

    # Graphiti options
    parser.add_argument('--group-id', type=str, help='Default group ID')
    parser.add_argument('--user-id', type=str, help='Default user ID')

    return parser.parse_args()


async def create_graphiti_client(config: GraphitiGRPCConfig) -> Graphiti:
    """Create and initialize a Graphiti client."""
    logger.info('Creating Graphiti client...')

    # Create LLM client
    llm_client = LLMClientFactory.create(config.llm)

    # Create embedder
    embedder = EmbedderFactory.create(config.embedder)

    # Get database configuration
    db_config = DatabaseDriverFactory.create_config(config.database)

    # Create Graphiti client based on database provider
    db_provider = config.database.provider.lower()
    if db_provider == 'neo4j':
        graphiti = Graphiti(
            uri=db_config['uri'],
            user=db_config['user'],
            password=db_config['password'],
            llm_client=llm_client,
            embedder=embedder,
        )
    elif db_provider == 'falkordb':
        from graphiti_core.driver.falkordb_driver import FalkorDriver

        driver = FalkorDriver(
            host=db_config['host'],
            port=db_config['port'],
            password=db_config['password'],
            database=db_config['database'],
        )
        graphiti = Graphiti(
            graph_driver=driver,
            llm_client=llm_client,
            embedder=embedder,
        )
    else:
        raise ValueError(f'Unsupported database provider: {db_provider}')

    # Build indices and constraints
    logger.info('Building indices and constraints...')
    await graphiti.build_indices_and_constraints()

    logger.info('Graphiti client created successfully')
    return graphiti


async def serve(config: GraphitiGRPCConfig):
    """Start the gRPC server."""
    start_time = time.time()

    # Create Graphiti client
    graphiti = await create_graphiti_client(config)

    # Create interceptors
    interceptors = [
        LoggingInterceptor(),
        ErrorInterceptor(),
        TracingInterceptor('graphiti-grpc-server'),
    ]

    # Add authentication interceptor if enabled
    if config.grpc.auth.enabled:
        from src.interceptors.auth_interceptor import AuthConfig as AuthInterceptorConfig

        auth_config = AuthInterceptorConfig(
            enabled=True,
            api_keys=set(config.grpc.auth.api_keys),
            jwt_secret=config.grpc.auth.jwt_secret,
            jwt_algorithm=config.grpc.auth.jwt_algorithm,
            skip_health_check=config.grpc.auth.skip_health_check,
        )
        auth_interceptor = AuthInterceptor(auth_config)
        interceptors.insert(0, auth_interceptor)
        logger.info('Authentication interceptor enabled')

    # Add rate limiting interceptor if enabled
    if config.grpc.rate_limit.enabled:
        rate_limit_interceptor = RateLimitInterceptor(
            enabled=True,
            window_seconds=config.grpc.rate_limit.window_seconds,
            max_requests=config.grpc.rate_limit.max_requests,
            read_max_requests=config.grpc.rate_limit.read_max_requests,
            write_max_requests=config.grpc.rate_limit.write_max_requests,
            skip_methods=config.grpc.rate_limit.skip_methods,
        )
        interceptors.insert(1 if config.grpc.auth.enabled else 0, rate_limit_interceptor)
        logger.info('Rate limiting interceptor enabled')

    # Add timeout interceptor if enabled
    if config.grpc.timeouts.enabled:
        timeout_interceptor = TimeoutInterceptor(config.grpc.timeouts)
        # Insert timeout interceptor after error interceptor but before tracing
        # This ensures timeouts are logged and errors are properly handled
        error_idx = next(
            (i for i, x in enumerate(interceptors) if isinstance(x, ErrorInterceptor)), -1
        )
        if error_idx >= 0:
            interceptors.insert(error_idx + 1, timeout_interceptor)
        else:
            interceptors.append(timeout_interceptor)
        logger.info(f'Timeout interceptor enabled (default={config.grpc.timeouts.default}s)')

    # Build server options with compression if enabled
    server_options = []
    if config.grpc.compression.enabled:
        compression_config = config.grpc.compression
        algorithm = compression_config.algorithm.lower()

        if algorithm == 'gzip':
            # Set default compression algorithm to gzip
            server_options.append(('grpc.default_compression_algorithm', grpc.Compression.Gzip))
            # Set compression level (0-9)
            server_options.append(('grpc.default_compression_level', compression_config.level))
            logger.info(
                f'Compression enabled: algorithm={algorithm}, level={compression_config.level}'
            )
        elif algorithm == 'deflate':
            server_options.append(('grpc.default_compression_algorithm', grpc.Compression.Deflate))
            server_options.append(('grpc.default_compression_level', compression_config.level))
            logger.info(
                f'Compression enabled: algorithm={algorithm}, level={compression_config.level}'
            )
        elif algorithm == 'none':
            server_options.append(
                ('grpc.default_compression_algorithm', grpc.Compression.NoCompression)
            )
            logger.info('Compression explicitly disabled via algorithm=none')
        else:
            logger.warning(f'Unknown compression algorithm: {algorithm}, using gzip')
            server_options.append(('grpc.default_compression_algorithm', grpc.Compression.Gzip))
            server_options.append(('grpc.default_compression_level', compression_config.level))

    # Determine compression type for server initialization
    server_compression = None
    if config.grpc.compression.enabled:
        algorithm = config.grpc.compression.algorithm.lower()
        if algorithm == 'gzip':
            server_compression = grpc.Compression.Gzip
        elif algorithm == 'deflate':
            server_compression = grpc.Compression.Deflate
        elif algorithm != 'none':
            # Default to gzip for unknown algorithms (warning already logged above)
            server_compression = grpc.Compression.Gzip

    # Create server
    server = grpc.aio.server(
        futures.ThreadPoolExecutor(max_workers=config.grpc.max_workers),
        interceptors=interceptors,
        options=server_options if server_options else None,
        compression=server_compression,
    )

    # Add services
    ingest_servicer = IngestServiceServicer(graphiti)
    ingest_service_pb2_grpc.add_IngestServiceServicer_to_server(ingest_servicer, server)

    retrieve_servicer = RetrieveServiceServicer(graphiti)
    retrieve_service_pb2_grpc.add_RetrieveServiceServicer_to_server(retrieve_servicer, server)

    admin_servicer = AdminServiceServicer(graphiti, config, start_time)
    admin_service_pb2_grpc.add_AdminServiceServicer_to_server(admin_servicer, server)

    # Add health checking service
    health_servicer = health.HealthServicer()
    health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)

    # Set initial health status
    health_servicer.set('', health_pb2.HealthCheckResponse.SERVING)
    health_servicer.set('graphiti.v1.IngestService', health_pb2.HealthCheckResponse.SERVING)
    health_servicer.set('graphiti.v1.RetrieveService', health_pb2.HealthCheckResponse.SERVING)
    health_servicer.set('graphiti.v1.AdminService', health_pb2.HealthCheckResponse.SERVING)

    # Add reflection service (for grpcurl, etc.)
    if config.grpc.enable_reflection:
        SERVICE_NAMES = (
            ingest_service_pb2.DESCRIPTOR.services_by_name['IngestService'].full_name,
            retrieve_service_pb2.DESCRIPTOR.services_by_name['RetrieveService'].full_name,
            admin_service_pb2.DESCRIPTOR.services_by_name['AdminService'].full_name,
            health_pb2.DESCRIPTOR.services_by_name['Health'].full_name,
            reflection.SERVICE_NAME,
        )
        reflection.enable_server_reflection(SERVICE_NAMES, server)
        logger.info('gRPC reflection enabled')

    # Configure TLS if enabled
    address = f'{config.grpc.host}:{config.grpc.port}'
    if config.grpc.enable_tls and config.grpc.cert_path and config.grpc.key_path:
        with open(config.grpc.key_path, 'rb') as key_file:
            private_key = key_file.read()
        with open(config.grpc.cert_path, 'rb') as cert_file:
            certificate_chain = cert_file.read()

        server_credentials = grpc.ssl_server_credentials([(private_key, certificate_chain)])
        server.add_secure_port(address, server_credentials)
        logger.info(f'gRPC server starting with TLS on {address}')
    else:
        server.add_insecure_port(address)
        logger.info(f'gRPC server starting on {address}')

    # Start server
    await server.start()
    logger.info(f'gRPC server started on {address}')

    # Handle shutdown signals
    shutdown_event = asyncio.Event()

    def signal_handler():
        logger.info('Received shutdown signal')
        shutdown_event.set()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)

    # Wait for shutdown
    await shutdown_event.wait()

    # Graceful shutdown
    logger.info('Shutting down gRPC server...')
    health_servicer.set('', health_pb2.HealthCheckResponse.NOT_SERVING)
    await server.stop(grace=5)
    logger.info('gRPC server stopped')


def main():
    """Main entry point."""
    # Parse command line arguments
    args = parse_args()

    # Load configuration
    config = GraphitiGRPCConfig()
    config.apply_cli_overrides(args)

    # Log configuration
    logger.info('Configuration:')
    logger.info(f'  gRPC Host: {config.grpc.host}')
    logger.info(f'  gRPC Port: {config.grpc.port}')
    logger.info(f'  Max Workers: {config.grpc.max_workers}')
    logger.info(f'  TLS Enabled: {config.grpc.enable_tls}')
    logger.info(f'  Reflection Enabled: {config.grpc.enable_reflection}')
    logger.info(f'  Compression Enabled: {config.grpc.compression.enabled}')
    if config.grpc.compression.enabled:
        logger.info(f'  Compression Algorithm: {config.grpc.compression.algorithm}')
        logger.info(f'  Compression Level: {config.grpc.compression.level}')
    logger.info(f'  Auth Enabled: {config.grpc.auth.enabled}')
    logger.info(f'  Rate Limit Enabled: {config.grpc.rate_limit.enabled}')
    logger.info(f'  Timeouts Enabled: {config.grpc.timeouts.enabled}')
    if config.grpc.timeouts.enabled:
        logger.info(f'  Default Timeout: {config.grpc.timeouts.default}s')
    logger.info(f'  LLM Provider: {config.llm.provider}')
    logger.info(f'  LLM Model: {config.llm.model}')
    logger.info(f'  Embedder Provider: {config.embedder.provider}')
    logger.info(f'  Embedder Model: {config.embedder.model}')
    logger.info(f'  Database Provider: {config.database.provider}')

    # Run server
    try:
        asyncio.run(serve(config))
    except KeyboardInterrupt:
        logger.info('Server interrupted')
        sys.exit(0)
    except Exception as e:
        logger.exception(f'Server error: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()
