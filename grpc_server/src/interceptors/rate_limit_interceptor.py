"""Rate limiting interceptor for gRPC requests.

Implements per-client rate limiting using a sliding window algorithm.
Returns RESOURCE_EXHAUSTED status when rate limits are exceeded.
"""

import asyncio
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable

import grpc

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    enabled: bool = True
    window_seconds: float = 60.0
    max_requests: int = 100
    # Separate limits for read vs write operations
    read_max_requests: int | None = None  # If None, uses max_requests
    write_max_requests: int | None = None  # If None, uses max_requests
    # Methods to skip rate limiting (e.g., health checks)
    skip_methods: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Set default skip methods for health checks."""
        if not self.skip_methods:
            self.skip_methods = [
                '/grpc.health.v1.Health/Check',
                '/grpc.health.v1.Health/Watch',
                '/grpc.reflection.v1alpha.ServerReflection/ServerReflectionInfo',
            ]


@dataclass
class ClientWindow:
    """Sliding window state for a single client."""

    timestamps: list[float] = field(default_factory=list)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class SlidingWindowRateLimiter:
    """Sliding window rate limiter implementation.

    Uses a sliding window algorithm that tracks request timestamps
    within a configurable time window. This provides smoother rate
    limiting compared to fixed window approaches.
    """

    def __init__(self, config: RateLimitConfig):
        self.config = config
        # Per-client sliding windows: client_id -> ClientWindow
        self._windows: dict[str, ClientWindow] = defaultdict(ClientWindow)
        self._cleanup_lock = asyncio.Lock()
        self._last_cleanup = time.monotonic()
        # Cleanup stale windows every 5 minutes
        self._cleanup_interval = 300.0

    async def is_allowed(self, client_id: str, is_read_operation: bool = True) -> bool:
        """Check if a request is allowed under the rate limit.

        Args:
            client_id: Unique identifier for the client (e.g., IP address)
            is_read_operation: Whether this is a read operation (more lenient limits)

        Returns:
            True if the request is allowed, False if rate limited
        """
        if not self.config.enabled:
            return True

        current_time = time.monotonic()

        # Determine the applicable limit
        if is_read_operation and self.config.read_max_requests is not None:
            max_requests = self.config.read_max_requests
        elif not is_read_operation and self.config.write_max_requests is not None:
            max_requests = self.config.write_max_requests
        else:
            max_requests = self.config.max_requests

        window = self._windows[client_id]

        async with window.lock:
            # Calculate window boundary
            window_start = current_time - self.config.window_seconds

            # Remove timestamps outside the window
            window.timestamps = [ts for ts in window.timestamps if ts > window_start]

            # Check if we're at the limit
            if len(window.timestamps) >= max_requests:
                return False

            # Record this request
            window.timestamps.append(current_time)
            return True

        # Periodically clean up stale client windows
        await self._maybe_cleanup()

    async def _maybe_cleanup(self):
        """Clean up stale client windows periodically."""
        current_time = time.monotonic()

        if current_time - self._last_cleanup < self._cleanup_interval:
            return

        async with self._cleanup_lock:
            # Double-check after acquiring lock
            if current_time - self._last_cleanup < self._cleanup_interval:
                return

            self._last_cleanup = current_time
            window_cutoff = current_time - self.config.window_seconds

            # Find and remove stale windows
            stale_clients = []
            for client_id, window in self._windows.items():
                # A window is stale if it has no recent timestamps
                if not window.timestamps or max(window.timestamps) < window_cutoff:
                    stale_clients.append(client_id)

            for client_id in stale_clients:
                del self._windows[client_id]

            if stale_clients:
                logger.debug(f'Cleaned up {len(stale_clients)} stale rate limit windows')

    def get_client_usage(self, client_id: str) -> tuple[int, int]:
        """Get current usage for a client.

        Args:
            client_id: Client identifier

        Returns:
            Tuple of (current_requests, max_requests)
        """
        window = self._windows.get(client_id)
        if not window:
            return 0, self.config.max_requests

        current_time = time.monotonic()
        window_start = current_time - self.config.window_seconds
        current_count = len([ts for ts in window.timestamps if ts > window_start])

        return current_count, self.config.max_requests


class RateLimitInterceptor(grpc.aio.ServerInterceptor):
    """Interceptor that enforces per-client rate limiting.

    Uses a sliding window algorithm to track and limit requests per client.
    Clients are identified by their peer address (IP) or authenticated identity.

    Features:
    - Per-client rate limiting based on peer identity
    - Sliding window algorithm for smooth rate limiting
    - Configurable window size and max requests
    - Different limits for read vs write operations
    - Skips health check endpoints
    - Returns RESOURCE_EXHAUSTED when limits exceeded
    """

    # Methods considered as read operations (more lenient limits)
    READ_METHODS = frozenset([
        # Retrieve service methods
        'Search',
        'GetEntity',
        'GetEntities',
        'GetRelation',
        'GetRelations',
        'GetEpisode',
        'GetEpisodes',
        'GetEntityEdge',
        'GetNode',
        'GetEdge',
        # Admin service read methods
        'GetServerStatus',
        'GetConfig',
    ])

    def __init__(
        self,
        config: RateLimitConfig | None = None,
        *,
        enabled: bool = True,
        window_seconds: float = 60.0,
        max_requests: int = 100,
        read_max_requests: int | None = None,
        write_max_requests: int | None = None,
        skip_methods: list[str] | None = None,
    ):
        """Initialize the rate limit interceptor.

        Args:
            config: RateLimitConfig instance. If provided, other parameters are ignored.
            enabled: Whether rate limiting is enabled
            window_seconds: Time window for rate limiting in seconds
            max_requests: Maximum requests allowed per window
            read_max_requests: Max requests for read operations (None = use max_requests)
            write_max_requests: Max requests for write operations (None = use max_requests)
            skip_methods: List of method names to skip rate limiting
        """
        if config is not None:
            self._config = config
        else:
            self._config = RateLimitConfig(
                enabled=enabled,
                window_seconds=window_seconds,
                max_requests=max_requests,
                read_max_requests=read_max_requests,
                write_max_requests=write_max_requests,
                skip_methods=skip_methods or [],
            )

        self._rate_limiter = SlidingWindowRateLimiter(self._config)

    @property
    def config(self) -> RateLimitConfig:
        """Get the rate limit configuration."""
        return self._config

    def _extract_client_id(self, context: grpc.aio.ServicerContext | None) -> str:
        """Extract client identifier from the gRPC context.

        Attempts to extract identity in this order:
        1. Authenticated user identity (from metadata)
        2. Peer address (IP address)
        3. Fallback to 'unknown'

        Args:
            context: The gRPC servicer context

        Returns:
            Client identifier string
        """
        if context is None:
            return 'unknown'

        # Try to get authenticated user from metadata
        try:
            invocation_metadata = context.invocation_metadata()
            metadata = dict(invocation_metadata) if invocation_metadata else {}  # type: ignore[arg-type]
            # Check common authentication headers
            for key in ['x-user-id', 'x-client-id', 'authorization']:
                if key in metadata:
                    return f'user:{metadata[key][:64]}'  # Truncate to prevent abuse
        except Exception:
            pass

        # Fall back to peer address
        try:
            peer = context.peer()
            if peer:
                # peer format is typically "ipv4:127.0.0.1:12345" or "ipv6:[::1]:12345"
                # Extract the IP address portion
                if peer.startswith('ipv4:'):
                    # Format: ipv4:IP:PORT
                    parts = peer[5:].rsplit(':', 1)
                    return f'ip:{parts[0]}'
                elif peer.startswith('ipv6:'):
                    # Format: ipv6:[IP]:PORT
                    if ']:' in peer:
                        ip = peer[6:].rsplit(']:', 1)[0]
                        return f'ip:{ip}'
                return f'peer:{peer}'
        except Exception:
            pass

        return 'unknown'

    def _should_skip_method(self, method: str) -> bool:
        """Check if a method should skip rate limiting.

        Args:
            method: The gRPC method path

        Returns:
            True if the method should skip rate limiting
        """
        return method in self._config.skip_methods

    def _is_read_operation(self, method: str) -> bool:
        """Determine if a method is a read operation.

        Args:
            method: The gRPC method path (e.g., '/graphiti.v1.RetrieveService/Search')

        Returns:
            True if this is a read operation
        """
        # Extract method name from path
        if '/' in method:
            method_name = method.rsplit('/', 1)[-1]
        else:
            method_name = method

        return method_name in self.READ_METHODS

    async def intercept_service(
        self,
        continuation: Callable[[grpc.HandlerCallDetails], Any],
        handler_call_details: grpc.HandlerCallDetails,
    ) -> Any:
        """Intercept and rate limit service calls."""
        method = handler_call_details.method

        # Skip rate limiting for exempted methods
        if self._should_skip_method(method):
            return await continuation(handler_call_details)

        # Skip if rate limiting is disabled
        if not self._config.enabled:
            return await continuation(handler_call_details)

        # Get the handler first
        handler = await continuation(handler_call_details)

        if handler is None:
            return handler

        # Determine if this is a read operation
        is_read = self._is_read_operation(method)

        # Wrap handlers to apply rate limiting
        if handler.unary_unary:
            return self._wrap_unary_unary(handler, method, is_read)
        elif handler.unary_stream:
            return self._wrap_unary_stream(handler, method, is_read)
        elif handler.stream_unary:
            return self._wrap_stream_unary(handler, method, is_read)
        elif handler.stream_stream:
            return self._wrap_stream_stream(handler, method, is_read)
        else:
            return handler

    async def _check_rate_limit(
        self, context: grpc.aio.ServicerContext, method: str, is_read: bool
    ) -> bool:
        """Check rate limit and abort if exceeded.

        Args:
            context: The gRPC servicer context
            method: The method being called
            is_read: Whether this is a read operation

        Returns:
            True if the request is allowed, False if it was rate limited
        """
        client_id = self._extract_client_id(context)

        if not await self._rate_limiter.is_allowed(client_id, is_read):
            current, max_req = self._rate_limiter.get_client_usage(client_id)
            logger.warning(
                f'Rate limit exceeded for client {client_id} on method {method} '
                f'({current}/{max_req} requests in {self._config.window_seconds}s window)'
            )

            # Set trailing metadata with rate limit info
            await context.abort(
                grpc.StatusCode.RESOURCE_EXHAUSTED,
                f'Rate limit exceeded. Maximum {max_req} requests per '
                f'{self._config.window_seconds} seconds. Please retry later.',
            )
            return False

        return True

    def _wrap_unary_unary(self, handler, method: str, is_read: bool):
        """Wrap a unary-unary handler with rate limiting."""
        original_handler = handler.unary_unary

        async def wrapped_handler(request, context):
            if not await self._check_rate_limit(context, method, is_read):
                return None  # Request was aborted
            return await original_handler(request, context)

        return grpc.unary_unary_rpc_method_handler(
            wrapped_handler,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )

    def _wrap_unary_stream(self, handler, method: str, is_read: bool):
        """Wrap a unary-stream handler with rate limiting."""
        original_handler = handler.unary_stream

        async def wrapped_handler(request, context):
            if not await self._check_rate_limit(context, method, is_read):
                return
            async for response in original_handler(request, context):
                yield response

        return grpc.unary_stream_rpc_method_handler(
            wrapped_handler,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )

    def _wrap_stream_unary(self, handler, method: str, is_read: bool):
        """Wrap a stream-unary handler with rate limiting."""
        original_handler = handler.stream_unary

        async def wrapped_handler(request_iterator, context):
            if not await self._check_rate_limit(context, method, is_read):
                return None  # Request was aborted
            return await original_handler(request_iterator, context)

        return grpc.stream_unary_rpc_method_handler(
            wrapped_handler,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )

    def _wrap_stream_stream(self, handler, method: str, is_read: bool):
        """Wrap a stream-stream handler with rate limiting."""
        original_handler = handler.stream_stream

        async def wrapped_handler(request_iterator, context):
            if not await self._check_rate_limit(context, method, is_read):
                return
            async for response in original_handler(request_iterator, context):
                yield response

        return grpc.stream_stream_rpc_method_handler(
            wrapped_handler,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )
