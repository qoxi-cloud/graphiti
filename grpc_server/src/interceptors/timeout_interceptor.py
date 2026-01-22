"""Timeout interceptor for gRPC requests.

Implements configurable per-service and per-method timeout enforcement.
Returns DEADLINE_EXCEEDED status when timeouts are exceeded.
"""

import asyncio
import logging
from typing import Any, Callable

import grpc

from src.config.schema import TimeoutConfig

logger = logging.getLogger(__name__)


class TimeoutInterceptor(grpc.aio.ServerInterceptor):
    """Interceptor that enforces configurable timeouts on gRPC requests.

    Supports hierarchical timeout configuration:
    - Global default timeout
    - Per-service default timeout
    - Per-method timeout overrides

    A timeout value of 0 means no timeout (useful for streaming endpoints).

    Features:
    - Configurable per-service and per-method timeouts
    - Respects client-provided deadlines (uses the shorter of server/client timeout)
    - Skips timeout enforcement for methods with timeout=0
    - Returns DEADLINE_EXCEEDED when timeouts are exceeded
    - Logs timeout events for monitoring

    Example configuration:
        timeouts:
          enabled: true
          default: 30
          services:
            IngestService:
              default: 120
              methods:
                AddEpisodeBulk: 600
                StreamEpisodes: 0  # No timeout for streaming
            RetrieveService:
              default: 30
            AdminService:
              default: 60
              methods:
                BuildCommunities: 300
    """

    # Methods that should skip timeout by default (streaming endpoints, health checks)
    DEFAULT_SKIP_METHODS = frozenset([
        '/grpc.health.v1.Health/Watch',
        '/grpc.reflection.v1alpha.ServerReflection/ServerReflectionInfo',
    ])

    def __init__(self, config: TimeoutConfig | None = None):
        """Initialize the timeout interceptor.

        Args:
            config: TimeoutConfig instance with timeout settings.
                   If None, uses default configuration (30s default timeout).
        """
        self._config = config or TimeoutConfig()

    @property
    def config(self) -> TimeoutConfig:
        """Get the timeout configuration."""
        return self._config

    def _parse_method_path(self, method: str) -> tuple[str, str]:
        """Parse the gRPC method path into service and method names.

        Args:
            method: Full gRPC method path (e.g., '/graphiti.v1.IngestService/AddEpisode')

        Returns:
            Tuple of (service_name, method_name)
        """
        # Method format: /package.ServiceName/MethodName
        parts = method.strip('/').split('/')
        if len(parts) >= 2:
            # Extract service name from the fully qualified name
            service_full = parts[-2]  # e.g., 'graphiti.v1.IngestService'
            service_name = service_full.split('.')[-1]  # e.g., 'IngestService'
            method_name = parts[-1]  # e.g., 'AddEpisode'
            return service_name, method_name
        return '', method

    def _get_timeout(self, method: str) -> float:
        """Get the configured timeout for a method.

        Args:
            method: Full gRPC method path

        Returns:
            Timeout in seconds, or 0 for no timeout
        """
        service_name, method_name = self._parse_method_path(method)
        return self._config.get_timeout(service_name, method_name)

    def _should_skip_timeout(self, method: str, timeout: float) -> bool:
        """Check if timeout should be skipped for this method.

        Args:
            method: Full gRPC method path
            timeout: Configured timeout value

        Returns:
            True if timeout should be skipped
        """
        # Skip if timeouts are disabled
        if not self._config.enabled:
            return True

        # Skip if timeout is 0 (explicitly disabled)
        if timeout == 0:
            return True

        # Skip default skip methods
        if method in self.DEFAULT_SKIP_METHODS:
            return True

        return False

    async def intercept_service(
        self,
        continuation: Callable[[grpc.HandlerCallDetails], Any],
        handler_call_details: grpc.HandlerCallDetails,
    ) -> Any:
        """Intercept and apply timeout to service calls."""
        method = handler_call_details.method
        timeout = self._get_timeout(method)

        # Check if we should skip timeout for this method
        if self._should_skip_timeout(method, timeout):
            return await continuation(handler_call_details)

        # Get the handler
        handler = await continuation(handler_call_details)

        if handler is None:
            return handler

        # Wrap handlers to apply timeout
        if handler.unary_unary:
            return self._wrap_unary_unary(handler, method, timeout)
        elif handler.unary_stream:
            return self._wrap_unary_stream(handler, method, timeout)
        elif handler.stream_unary:
            return self._wrap_stream_unary(handler, method, timeout)
        elif handler.stream_stream:
            return self._wrap_stream_stream(handler, method, timeout)
        else:
            return handler

    def _wrap_unary_unary(self, handler, method: str, timeout: float):
        """Wrap a unary-unary handler with timeout."""
        original_handler = handler.unary_unary

        async def wrapped_handler(request, context):
            effective_timeout = self._get_effective_timeout(context, timeout)

            if effective_timeout == 0:
                # No timeout
                return await original_handler(request, context)

            try:
                return await asyncio.wait_for(
                    original_handler(request, context),
                    timeout=effective_timeout,
                )
            except asyncio.TimeoutError:
                logger.warning(
                    f'Request timeout exceeded for {method} '
                    f'(timeout={effective_timeout}s)'
                )
                await context.abort(
                    grpc.StatusCode.DEADLINE_EXCEEDED,
                    f'Request timeout exceeded ({effective_timeout}s)',
                )

        return grpc.unary_unary_rpc_method_handler(
            wrapped_handler,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )

    def _wrap_unary_stream(self, handler, method: str, timeout: float):
        """Wrap a unary-stream handler with timeout.

        Note: For streaming responses, the timeout applies to the entire stream,
        not individual messages. Consider using timeout=0 for long-running streams.
        """
        original_handler = handler.unary_stream

        async def wrapped_handler(request, context):
            effective_timeout = self._get_effective_timeout(context, timeout)

            if effective_timeout == 0:
                # No timeout
                async for response in original_handler(request, context):
                    yield response
                return

            try:
                # Wrap the entire stream with a timeout
                async def stream_with_timeout():
                    async for response in original_handler(request, context):
                        yield response

                async for response in self._stream_with_timeout(
                    stream_with_timeout(), effective_timeout, method, context
                ):
                    yield response
            except asyncio.TimeoutError:
                logger.warning(
                    f'Stream timeout exceeded for {method} '
                    f'(timeout={effective_timeout}s)'
                )
                await context.abort(
                    grpc.StatusCode.DEADLINE_EXCEEDED,
                    f'Stream timeout exceeded ({effective_timeout}s)',
                )

        return grpc.unary_stream_rpc_method_handler(
            wrapped_handler,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )

    def _wrap_stream_unary(self, handler, method: str, timeout: float):
        """Wrap a stream-unary handler with timeout."""
        original_handler = handler.stream_unary

        async def wrapped_handler(request_iterator, context):
            effective_timeout = self._get_effective_timeout(context, timeout)

            if effective_timeout == 0:
                # No timeout
                return await original_handler(request_iterator, context)

            try:
                return await asyncio.wait_for(
                    original_handler(request_iterator, context),
                    timeout=effective_timeout,
                )
            except asyncio.TimeoutError:
                logger.warning(
                    f'Request timeout exceeded for {method} '
                    f'(timeout={effective_timeout}s)'
                )
                await context.abort(
                    grpc.StatusCode.DEADLINE_EXCEEDED,
                    f'Request timeout exceeded ({effective_timeout}s)',
                )

        return grpc.stream_unary_rpc_method_handler(
            wrapped_handler,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )

    def _wrap_stream_stream(self, handler, method: str, timeout: float):
        """Wrap a stream-stream handler with timeout.

        Note: For bidirectional streaming, the timeout applies to the entire stream,
        not individual messages. Consider using timeout=0 for long-running streams.
        """
        original_handler = handler.stream_stream

        async def wrapped_handler(request_iterator, context):
            effective_timeout = self._get_effective_timeout(context, timeout)

            if effective_timeout == 0:
                # No timeout
                async for response in original_handler(request_iterator, context):
                    yield response
                return

            try:
                async def stream_with_timeout():
                    async for response in original_handler(request_iterator, context):
                        yield response

                async for response in self._stream_with_timeout(
                    stream_with_timeout(), effective_timeout, method, context
                ):
                    yield response
            except asyncio.TimeoutError:
                logger.warning(
                    f'Bidirectional stream timeout exceeded for {method} '
                    f'(timeout={effective_timeout}s)'
                )
                await context.abort(
                    grpc.StatusCode.DEADLINE_EXCEEDED,
                    f'Bidirectional stream timeout exceeded ({effective_timeout}s)',
                )

        return grpc.stream_stream_rpc_method_handler(
            wrapped_handler,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )

    def _get_effective_timeout(
        self, context: grpc.aio.ServicerContext, server_timeout: float
    ) -> float:
        """Get the effective timeout considering both server and client deadlines.

        The effective timeout is the minimum of:
        - Server-configured timeout
        - Client-provided deadline (if any)

        Args:
            context: The gRPC servicer context
            server_timeout: Server-configured timeout in seconds

        Returns:
            Effective timeout in seconds, or 0 for no timeout
        """
        if server_timeout == 0:
            return 0

        try:
            # Check if client provided a deadline
            time_remaining = context.time_remaining()
            if time_remaining is not None and time_remaining > 0:
                # Use the shorter of server timeout or client deadline
                return min(server_timeout, time_remaining)
        except Exception:
            # time_remaining() may not be available in all contexts
            pass

        return server_timeout

    async def _stream_with_timeout(
        self,
        stream,
        timeout: float,
        method: str,
        context: grpc.aio.ServicerContext,
    ):
        """Wrap an async generator with a total timeout.

        Args:
            stream: The async generator to wrap
            timeout: Total timeout for the stream in seconds
            method: Method name for logging
            context: gRPC context for aborting on timeout

        Yields:
            Items from the stream until timeout or completion
        """
        try:
            async with asyncio.timeout(timeout):
                async for item in stream:
                    yield item
        except asyncio.TimeoutError:
            logger.warning(
                f'Stream timeout exceeded for {method} (timeout={timeout}s)'
            )
            await context.abort(
                grpc.StatusCode.DEADLINE_EXCEEDED,
                f'Stream timeout exceeded ({timeout}s)',
            )
