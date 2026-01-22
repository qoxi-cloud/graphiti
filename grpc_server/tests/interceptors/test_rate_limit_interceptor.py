"""Tests for rate limit interceptor."""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock

import grpc
import pytest

from src.interceptors.rate_limit_interceptor import (
    ClientWindow,
    RateLimitConfig,
    RateLimitInterceptor,
    SlidingWindowRateLimiter,
)


class TestRateLimitConfig:
    """Tests for RateLimitConfig class."""

    def test_config_defaults(self):
        """Test RateLimitConfig with default values."""
        config = RateLimitConfig()

        assert config.enabled is True
        assert config.window_seconds == 60.0
        assert config.max_requests == 100
        assert config.read_max_requests is None
        assert config.write_max_requests is None
        assert config.skip_methods == [
            '/grpc.health.v1.Health/Check',
            '/grpc.health.v1.Health/Watch',
            '/grpc.reflection.v1alpha.ServerReflection/ServerReflectionInfo',
        ]

    def test_config_custom_values(self):
        """Test RateLimitConfig with custom values."""
        config = RateLimitConfig(
            enabled=False,
            window_seconds=30.0,
            max_requests=50,
            read_max_requests=100,
            write_max_requests=25,
            skip_methods=['/custom.Service/Method'],
        )

        assert config.enabled is False
        assert config.window_seconds == 30.0
        assert config.max_requests == 50
        assert config.read_max_requests == 100
        assert config.write_max_requests == 25
        assert config.skip_methods == ['/custom.Service/Method']

    def test_config_empty_skip_methods_initializes_defaults(self):
        """Test that empty skip_methods list gets populated with defaults."""
        config = RateLimitConfig(skip_methods=[])

        # Post-init should populate defaults
        assert '/grpc.health.v1.Health/Check' in config.skip_methods
        assert '/grpc.health.v1.Health/Watch' in config.skip_methods

    def test_config_with_only_read_limit(self):
        """Test RateLimitConfig with only read limit set."""
        config = RateLimitConfig(max_requests=50, read_max_requests=200)

        assert config.max_requests == 50
        assert config.read_max_requests == 200
        assert config.write_max_requests is None


class TestClientWindow:
    """Tests for ClientWindow class."""

    def test_client_window_default_values(self):
        """Test ClientWindow initializes with empty timestamps."""
        window = ClientWindow()

        assert window.timestamps == []
        assert isinstance(window.lock, asyncio.Lock)

    @pytest.mark.asyncio
    async def test_client_window_lock_works(self):
        """Test that ClientWindow lock can be acquired."""
        window = ClientWindow()

        async with window.lock:
            window.timestamps.append(time.monotonic())

        assert len(window.timestamps) == 1


class TestSlidingWindowRateLimiter:
    """Tests for SlidingWindowRateLimiter class."""

    def test_limiter_initialization(self):
        """Test SlidingWindowRateLimiter initializes correctly."""
        config = RateLimitConfig(window_seconds=30.0, max_requests=50)
        limiter = SlidingWindowRateLimiter(config)

        assert limiter.config == config
        assert len(limiter._windows) == 0
        assert limiter._cleanup_interval == 300.0

    @pytest.mark.asyncio
    async def test_is_allowed_when_disabled(self):
        """Test that is_allowed returns True when rate limiting is disabled."""
        config = RateLimitConfig(enabled=False, max_requests=0)
        limiter = SlidingWindowRateLimiter(config)

        result = await limiter.is_allowed('client1', is_read_operation=True)

        assert result is True

    @pytest.mark.asyncio
    async def test_is_allowed_first_request(self):
        """Test that first request is always allowed."""
        config = RateLimitConfig(enabled=True, max_requests=10)
        limiter = SlidingWindowRateLimiter(config)

        result = await limiter.is_allowed('client1', is_read_operation=True)

        assert result is True
        assert 'client1' in limiter._windows
        assert len(limiter._windows['client1'].timestamps) == 1

    @pytest.mark.asyncio
    async def test_is_allowed_within_limit(self):
        """Test that requests within limit are allowed."""
        config = RateLimitConfig(enabled=True, max_requests=5)
        limiter = SlidingWindowRateLimiter(config)

        # Make 5 requests
        for _ in range(5):
            result = await limiter.is_allowed('client1', is_read_operation=True)
            assert result is True

        assert len(limiter._windows['client1'].timestamps) == 5

    @pytest.mark.asyncio
    async def test_is_allowed_exceeds_limit(self):
        """Test that requests exceeding limit are rejected."""
        config = RateLimitConfig(enabled=True, max_requests=3)
        limiter = SlidingWindowRateLimiter(config)

        # Make 3 requests (should succeed)
        for _ in range(3):
            result = await limiter.is_allowed('client1', is_read_operation=True)
            assert result is True

        # 4th request should fail
        result = await limiter.is_allowed('client1', is_read_operation=True)
        assert result is False

        # Timestamps should still be 3 (rejected request not added)
        assert len(limiter._windows['client1'].timestamps) == 3

    @pytest.mark.asyncio
    async def test_is_allowed_window_expiry(self):
        """Test that old timestamps outside window are removed."""
        config = RateLimitConfig(enabled=True, window_seconds=0.1, max_requests=2)
        limiter = SlidingWindowRateLimiter(config)

        # Make 2 requests (fill the limit)
        for _ in range(2):
            result = await limiter.is_allowed('client1', is_read_operation=True)
            assert result is True

        # 3rd request should fail
        result = await limiter.is_allowed('client1', is_read_operation=True)
        assert result is False

        # Wait for window to expire
        await asyncio.sleep(0.15)

        # Should be allowed again after window expires
        result = await limiter.is_allowed('client1', is_read_operation=True)
        assert result is True

    @pytest.mark.asyncio
    async def test_is_allowed_read_operation_limit(self):
        """Test that read operations use read_max_requests when set."""
        config = RateLimitConfig(
            enabled=True, max_requests=2, read_max_requests=5, write_max_requests=1
        )
        limiter = SlidingWindowRateLimiter(config)

        # Read operations should allow up to 5 requests
        for _ in range(5):
            result = await limiter.is_allowed('client1', is_read_operation=True)
            assert result is True

        # 6th read request should fail
        result = await limiter.is_allowed('client1', is_read_operation=True)
        assert result is False

    @pytest.mark.asyncio
    async def test_is_allowed_write_operation_limit(self):
        """Test that write operations use write_max_requests when set."""
        config = RateLimitConfig(
            enabled=True, max_requests=10, read_max_requests=20, write_max_requests=2
        )
        limiter = SlidingWindowRateLimiter(config)

        # Write operations should allow up to 2 requests
        for _ in range(2):
            result = await limiter.is_allowed('client2', is_read_operation=False)
            assert result is True

        # 3rd write request should fail
        result = await limiter.is_allowed('client2', is_read_operation=False)
        assert result is False

    @pytest.mark.asyncio
    async def test_is_allowed_falls_back_to_max_requests(self):
        """Test that is_allowed falls back to max_requests when specific limit not set."""
        config = RateLimitConfig(enabled=True, max_requests=3)
        limiter = SlidingWindowRateLimiter(config)

        # Both read and write should use max_requests (3)
        for _ in range(3):
            result = await limiter.is_allowed('client1', is_read_operation=True)
            assert result is True

        result = await limiter.is_allowed('client1', is_read_operation=True)
        assert result is False

    @pytest.mark.asyncio
    async def test_is_allowed_different_clients_independent(self):
        """Test that different clients have independent rate limits."""
        config = RateLimitConfig(enabled=True, max_requests=2)
        limiter = SlidingWindowRateLimiter(config)

        # Client 1 makes 2 requests
        for _ in range(2):
            result = await limiter.is_allowed('client1', is_read_operation=True)
            assert result is True

        # Client 1's 3rd request should fail
        result = await limiter.is_allowed('client1', is_read_operation=True)
        assert result is False

        # Client 2 should still be able to make requests
        result = await limiter.is_allowed('client2', is_read_operation=True)
        assert result is True

    @pytest.mark.asyncio
    async def test_maybe_cleanup_not_triggered_before_interval(self):
        """Test that cleanup doesn't run before cleanup interval."""
        config = RateLimitConfig(enabled=True, window_seconds=60.0)
        limiter = SlidingWindowRateLimiter(config)

        # Make a request to create a window
        await limiter.is_allowed('client1', is_read_operation=True)

        # Set last cleanup to recent time
        limiter._last_cleanup = time.monotonic()

        # Call cleanup (should not actually clean up)
        await limiter._maybe_cleanup()

        # Window should still exist
        assert 'client1' in limiter._windows

    @pytest.mark.asyncio
    async def test_maybe_cleanup_removes_stale_windows(self):
        """Test that cleanup removes stale client windows."""
        config = RateLimitConfig(enabled=True, window_seconds=0.1)
        limiter = SlidingWindowRateLimiter(config)

        # Make requests for multiple clients
        await limiter.is_allowed('client1', is_read_operation=True)
        await limiter.is_allowed('client2', is_read_operation=True)
        await limiter.is_allowed('client3', is_read_operation=True)

        assert len(limiter._windows) == 3

        # Wait for windows to become stale
        await asyncio.sleep(0.15)

        # Force cleanup by setting last_cleanup to past
        limiter._last_cleanup = time.monotonic() - 400

        # Trigger cleanup
        await limiter._maybe_cleanup()

        # Stale windows should be removed
        assert len(limiter._windows) == 0

    @pytest.mark.asyncio
    async def test_maybe_cleanup_double_check_locking(self):
        """Test that cleanup uses double-check locking pattern."""
        config = RateLimitConfig(enabled=True, window_seconds=60.0)
        limiter = SlidingWindowRateLimiter(config)

        # Set last cleanup to trigger cleanup
        limiter._last_cleanup = time.monotonic() - 400

        # Simulate concurrent cleanup attempts
        tasks = [limiter._maybe_cleanup() for _ in range(5)]
        await asyncio.gather(*tasks)

        # Cleanup should have run once (last_cleanup updated)
        assert time.monotonic() - limiter._last_cleanup < 1.0

    def test_get_client_usage_nonexistent_client(self):
        """Test get_client_usage for client with no window."""
        config = RateLimitConfig(enabled=True, max_requests=50)
        limiter = SlidingWindowRateLimiter(config)

        current, max_req = limiter.get_client_usage('nonexistent')

        assert current == 0
        assert max_req == 50

    @pytest.mark.asyncio
    async def test_get_client_usage_with_requests(self):
        """Test get_client_usage returns correct counts."""
        config = RateLimitConfig(enabled=True, max_requests=10)
        limiter = SlidingWindowRateLimiter(config)

        # Make 3 requests
        for _ in range(3):
            await limiter.is_allowed('client1', is_read_operation=True)

        current, max_req = limiter.get_client_usage('client1')

        assert current == 3
        assert max_req == 10

    @pytest.mark.asyncio
    async def test_get_client_usage_filters_expired_timestamps(self):
        """Test that get_client_usage only counts timestamps in current window."""
        config = RateLimitConfig(enabled=True, window_seconds=0.1, max_requests=10)
        limiter = SlidingWindowRateLimiter(config)

        # Make 3 requests
        for _ in range(3):
            await limiter.is_allowed('client1', is_read_operation=True)

        # Wait for some timestamps to expire
        await asyncio.sleep(0.15)

        # Make 2 more requests
        for _ in range(2):
            await limiter.is_allowed('client1', is_read_operation=True)

        current, max_req = limiter.get_client_usage('client1')

        # Should only count the 2 recent requests
        assert current == 2
        assert max_req == 10


class TestRateLimitInterceptor:
    """Tests for RateLimitInterceptor class."""

    @pytest.fixture
    def mock_continuation(self, create_mock_handler):
        """Create a mock continuation function."""

        async def continuation(handler_call_details):
            return create_mock_handler('unary_unary')

        return continuation

    @pytest.fixture
    def mock_handler_details(self):
        """Create mock handler call details."""
        details = MagicMock()
        details.method = '/graphiti.v1.IngestService/AddEpisode'
        return details

    @pytest.fixture
    def mock_context(self):
        """Create mock gRPC context."""
        context = MagicMock(spec=grpc.aio.ServicerContext)
        context.peer.return_value = 'ipv4:127.0.0.1:12345'
        context.invocation_metadata.return_value = []
        context.abort = AsyncMock()
        return context

    def test_interceptor_initialization_with_config(self):
        """Test interceptor initialization with RateLimitConfig."""
        config = RateLimitConfig(enabled=False, max_requests=50)
        interceptor = RateLimitInterceptor(config=config)

        assert interceptor.config.enabled is False
        assert interceptor.config.max_requests == 50

    def test_interceptor_initialization_with_parameters(self):
        """Test interceptor initialization with individual parameters."""
        interceptor = RateLimitInterceptor(
            enabled=False,
            window_seconds=30.0,
            max_requests=75,
            read_max_requests=100,
            write_max_requests=50,
            skip_methods=['/custom.Method'],
        )

        assert interceptor.config.enabled is False
        assert interceptor.config.window_seconds == 30.0
        assert interceptor.config.max_requests == 75
        assert interceptor.config.read_max_requests == 100
        assert interceptor.config.write_max_requests == 50
        assert interceptor.config.skip_methods == ['/custom.Method']

    def test_interceptor_default_initialization(self):
        """Test interceptor with default values."""
        interceptor = RateLimitInterceptor()

        assert interceptor.config.enabled is True
        assert interceptor.config.window_seconds == 60.0
        assert interceptor.config.max_requests == 100

    @pytest.mark.asyncio
    async def test_rate_limiting_disabled(self, mock_continuation, mock_handler_details):
        """Test that rate limiting is bypassed when disabled."""
        interceptor = RateLimitInterceptor(enabled=False)

        result = await interceptor.intercept_service(mock_continuation, mock_handler_details)

        assert result is not None

    @pytest.mark.asyncio
    async def test_skip_health_check_method(self, mock_continuation, mock_handler_details):
        """Test that health check methods skip rate limiting."""
        interceptor = RateLimitInterceptor(max_requests=0)  # Set limit to 0 to test skip
        mock_handler_details.method = '/grpc.health.v1.Health/Check'

        result = await interceptor.intercept_service(mock_continuation, mock_handler_details)

        assert result is not None

    @pytest.mark.asyncio
    async def test_skip_health_watch_method(self, mock_continuation, mock_handler_details):
        """Test that health watch method skips rate limiting."""
        interceptor = RateLimitInterceptor(max_requests=0)
        mock_handler_details.method = '/grpc.health.v1.Health/Watch'

        result = await interceptor.intercept_service(mock_continuation, mock_handler_details)

        assert result is not None

    @pytest.mark.asyncio
    async def test_skip_reflection_method(self, mock_continuation, mock_handler_details):
        """Test that reflection methods skip rate limiting."""
        interceptor = RateLimitInterceptor(max_requests=0)
        mock_handler_details.method = (
            '/grpc.reflection.v1alpha.ServerReflection/ServerReflectionInfo'
        )

        result = await interceptor.intercept_service(mock_continuation, mock_handler_details)

        assert result is not None

    @pytest.mark.asyncio
    async def test_skip_custom_methods(self, mock_continuation, mock_handler_details):
        """Test that custom skip methods work."""
        interceptor = RateLimitInterceptor(
            max_requests=0, skip_methods=['/custom.Service/CustomMethod']
        )
        mock_handler_details.method = '/custom.Service/CustomMethod'

        result = await interceptor.intercept_service(mock_continuation, mock_handler_details)

        assert result is not None

    def test_is_read_operation_read_methods(self):
        """Test that read methods are correctly identified."""
        interceptor = RateLimitInterceptor()

        # Test various read methods
        assert interceptor._is_read_operation('/graphiti.v1.RetrieveService/Search') is True
        assert interceptor._is_read_operation('/graphiti.v1.RetrieveService/GetEntity') is True
        assert interceptor._is_read_operation('/graphiti.v1.RetrieveService/GetEntities') is True
        assert interceptor._is_read_operation('/graphiti.v1.AdminService/GetServerStatus') is True

    def test_is_read_operation_write_methods(self):
        """Test that write methods are correctly identified."""
        interceptor = RateLimitInterceptor()

        # Test various write methods
        assert interceptor._is_read_operation('/graphiti.v1.IngestService/AddEpisode') is False
        assert (
            interceptor._is_read_operation('/graphiti.v1.IngestService/UpdateEntity') is False
        )
        assert interceptor._is_read_operation('/graphiti.v1.IngestService/DeleteNode') is False

    def test_is_read_operation_method_name_without_path(self):
        """Test is_read_operation with method name without path."""
        interceptor = RateLimitInterceptor()

        assert interceptor._is_read_operation('Search') is True
        assert interceptor._is_read_operation('GetEntity') is True
        assert interceptor._is_read_operation('AddEpisode') is False

    def test_extract_client_id_from_metadata_user_id(self):
        """Test extracting client ID from x-user-id metadata."""
        interceptor = RateLimitInterceptor()

        context = MagicMock()
        context.invocation_metadata.return_value = [('x-user-id', 'user123')]
        context.peer.return_value = 'ipv4:127.0.0.1:12345'

        client_id = interceptor._extract_client_id(context)

        assert client_id == 'user:user123'

    def test_extract_client_id_from_metadata_client_id(self):
        """Test extracting client ID from x-client-id metadata."""
        interceptor = RateLimitInterceptor()

        context = MagicMock()
        context.invocation_metadata.return_value = [('x-client-id', 'client456')]
        context.peer.return_value = 'ipv4:127.0.0.1:12345'

        client_id = interceptor._extract_client_id(context)

        assert client_id == 'user:client456'

    def test_extract_client_id_from_metadata_authorization(self):
        """Test extracting client ID from authorization metadata."""
        interceptor = RateLimitInterceptor()

        context = MagicMock()
        context.invocation_metadata.return_value = [('authorization', 'Bearer token789')]
        context.peer.return_value = 'ipv4:127.0.0.1:12345'

        client_id = interceptor._extract_client_id(context)

        assert client_id == 'user:Bearer token789'

    def test_extract_client_id_truncates_long_values(self):
        """Test that client ID from metadata is truncated to prevent abuse."""
        interceptor = RateLimitInterceptor()

        long_value = 'x' * 100
        context = MagicMock()
        context.invocation_metadata.return_value = [('x-user-id', long_value)]
        context.peer.return_value = 'ipv4:127.0.0.1:12345'

        client_id = interceptor._extract_client_id(context)

        # Should be truncated to 64 characters
        assert client_id == f'user:{long_value[:64]}'
        assert len(client_id) == 69  # 'user:' + 64 chars

    def test_extract_client_id_from_ipv4_peer(self):
        """Test extracting client ID from IPv4 peer address."""
        interceptor = RateLimitInterceptor()

        context = MagicMock()
        context.invocation_metadata.return_value = []
        context.peer.return_value = 'ipv4:192.168.1.100:54321'

        client_id = interceptor._extract_client_id(context)

        assert client_id == 'ip:192.168.1.100'

    def test_extract_client_id_from_ipv6_peer(self):
        """Test extracting client ID from IPv6 peer address."""
        interceptor = RateLimitInterceptor()

        context = MagicMock()
        context.invocation_metadata.return_value = []
        context.peer.return_value = 'ipv6:[::1]:12345'

        client_id = interceptor._extract_client_id(context)

        # The brackets are removed during parsing: peer[6:] removes 'ipv6:[', then rsplit removes ']:PORT'
        assert client_id == 'ip:::1'

    def test_extract_client_id_from_ipv6_full_address(self):
        """Test extracting client ID from full IPv6 address."""
        interceptor = RateLimitInterceptor()

        context = MagicMock()
        context.invocation_metadata.return_value = []
        context.peer.return_value = 'ipv6:[2001:0db8:85a3::8a2e:0370:7334]:443'

        client_id = interceptor._extract_client_id(context)

        # The brackets are removed during parsing
        assert client_id == 'ip:2001:0db8:85a3::8a2e:0370:7334'

    def test_extract_client_id_from_unknown_peer_format(self):
        """Test extracting client ID from unknown peer format."""
        interceptor = RateLimitInterceptor()

        context = MagicMock()
        context.invocation_metadata.return_value = []
        context.peer.return_value = 'unix:/tmp/socket'

        client_id = interceptor._extract_client_id(context)

        assert client_id == 'peer:unix:/tmp/socket'

    def test_extract_client_id_none_context(self):
        """Test extracting client ID when context is None."""
        interceptor = RateLimitInterceptor()

        client_id = interceptor._extract_client_id(None)

        assert client_id == 'unknown'

    def test_extract_client_id_peer_exception(self):
        """Test extracting client ID when peer() raises exception."""
        interceptor = RateLimitInterceptor()

        context = MagicMock()
        context.invocation_metadata.return_value = []
        context.peer.side_effect = Exception('Peer error')

        client_id = interceptor._extract_client_id(context)

        assert client_id == 'unknown'

    def test_extract_client_id_metadata_exception(self):
        """Test extracting client ID when metadata access raises exception."""
        interceptor = RateLimitInterceptor()

        context = MagicMock()
        context.invocation_metadata.side_effect = Exception('Metadata error')
        context.peer.return_value = 'ipv4:127.0.0.1:12345'

        client_id = interceptor._extract_client_id(context)

        # Should fall back to peer address
        assert client_id == 'ip:127.0.0.1'

    @pytest.mark.asyncio
    async def test_check_rate_limit_allowed(self, mock_context):
        """Test _check_rate_limit allows request within limit."""
        interceptor = RateLimitInterceptor(max_requests=10)

        result = await interceptor._check_rate_limit(
            mock_context, '/test.Service/Method', is_read=True
        )

        assert result is True
        mock_context.abort.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_rate_limit_exceeded(self, mock_context):
        """Test _check_rate_limit aborts when limit exceeded."""
        interceptor = RateLimitInterceptor(max_requests=2)

        # Make requests up to limit
        for _ in range(2):
            await interceptor._check_rate_limit(mock_context, '/test.Service/Method', is_read=True)

        # Next request should be rate limited
        result = await interceptor._check_rate_limit(
            mock_context, '/test.Service/Method', is_read=True
        )

        assert result is False
        mock_context.abort.assert_called_once()

        # Check abort was called with correct status and message
        call_args = mock_context.abort.call_args
        assert call_args[0][0] == grpc.StatusCode.RESOURCE_EXHAUSTED
        assert 'Rate limit exceeded' in call_args[0][1]

    @pytest.mark.asyncio
    async def test_check_rate_limit_different_limits_for_read_write(self):
        """Test that read and write operations have different limits."""
        interceptor = RateLimitInterceptor(read_max_requests=5, write_max_requests=2)

        # Create separate contexts for write and read operations
        write_context = MagicMock(spec=grpc.aio.ServicerContext)
        write_context.peer.return_value = 'ipv4:192.168.1.1:12345'
        write_context.invocation_metadata.return_value = []
        write_context.abort = AsyncMock()

        read_context = MagicMock(spec=grpc.aio.ServicerContext)
        read_context.peer.return_value = 'ipv4:192.168.1.2:12345'
        read_context.invocation_metadata.return_value = []
        read_context.abort = AsyncMock()

        # Make 2 write requests (should fill write limit)
        for _ in range(2):
            result = await interceptor._check_rate_limit(
                write_context, '/test.Service/Write', is_read=False
            )
            assert result is True

        # 3rd write request should fail
        result = await interceptor._check_rate_limit(
            write_context, '/test.Service/Write', is_read=False
        )
        assert result is False

        # Read requests from different client should work (up to 5)
        for _ in range(5):
            result = await interceptor._check_rate_limit(
                read_context, '/test.Service/Read', is_read=True
            )
            assert result is True

        # 6th read request should fail
        result = await interceptor._check_rate_limit(
            read_context, '/test.Service/Read', is_read=True
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_intercept_service_none_handler(self, mock_handler_details):
        """Test intercept_service handles None handler gracefully."""
        interceptor = RateLimitInterceptor()

        async def continuation(handler_call_details):
            return None

        result = await interceptor.intercept_service(continuation, mock_handler_details)

        assert result is None

    @pytest.mark.asyncio
    async def test_intercept_service_wraps_unary_unary(
        self, create_mock_handler, mock_handler_details
    ):
        """Test intercept_service wraps unary-unary handlers."""
        interceptor = RateLimitInterceptor()

        async def continuation(handler_call_details):
            return create_mock_handler('unary_unary')

        wrapped = await interceptor.intercept_service(continuation, mock_handler_details)

        assert wrapped is not None
        assert wrapped.unary_unary is not None

    @pytest.mark.asyncio
    async def test_intercept_service_wraps_unary_stream(
        self, create_mock_handler, mock_handler_details
    ):
        """Test intercept_service wraps unary-stream handlers."""
        interceptor = RateLimitInterceptor()

        async def continuation(handler_call_details):
            return create_mock_handler('unary_stream')

        wrapped = await interceptor.intercept_service(continuation, mock_handler_details)

        assert wrapped is not None
        assert wrapped.unary_stream is not None

    @pytest.mark.asyncio
    async def test_intercept_service_wraps_stream_unary(
        self, create_mock_handler, mock_handler_details
    ):
        """Test intercept_service wraps stream-unary handlers."""
        interceptor = RateLimitInterceptor()

        async def continuation(handler_call_details):
            return create_mock_handler('stream_unary')

        wrapped = await interceptor.intercept_service(continuation, mock_handler_details)

        assert wrapped is not None
        assert wrapped.stream_unary is not None

    @pytest.mark.asyncio
    async def test_intercept_service_wraps_stream_stream(
        self, create_mock_handler, mock_handler_details
    ):
        """Test intercept_service wraps stream-stream handlers."""
        interceptor = RateLimitInterceptor()

        async def continuation(handler_call_details):
            return create_mock_handler('stream_stream')

        wrapped = await interceptor.intercept_service(continuation, mock_handler_details)

        assert wrapped is not None
        assert wrapped.stream_stream is not None

    @pytest.mark.asyncio
    async def test_intercept_service_unknown_handler_type(self, mock_handler_details):
        """Test intercept_service with unknown handler type passes through."""
        interceptor = RateLimitInterceptor()

        mock_handler = MagicMock()
        mock_handler.unary_unary = None
        mock_handler.unary_stream = None
        mock_handler.stream_unary = None
        mock_handler.stream_stream = None

        async def continuation(handler_call_details):
            return mock_handler

        wrapped = await interceptor.intercept_service(continuation, mock_handler_details)

        assert wrapped is mock_handler

    @pytest.mark.asyncio
    async def test_wrap_unary_unary_allows_request(
        self, create_mock_handler, mock_context, mock_handler_details
    ):
        """Test unary-unary wrapper allows request within limit."""
        interceptor = RateLimitInterceptor(max_requests=10)

        async def continuation(handler_call_details):
            return create_mock_handler('unary_unary')

        wrapped_handler = await interceptor.intercept_service(continuation, mock_handler_details)

        request = MagicMock()
        result = await wrapped_handler.unary_unary(request, mock_context)

        assert result == 'response'
        mock_context.abort.assert_not_called()

    @pytest.mark.asyncio
    async def test_wrap_unary_unary_rate_limited(
        self, create_mock_handler, mock_context, mock_handler_details
    ):
        """Test unary-unary wrapper aborts when rate limited."""
        interceptor = RateLimitInterceptor(max_requests=1)

        async def continuation(handler_call_details):
            return create_mock_handler('unary_unary')

        wrapped_handler = await interceptor.intercept_service(continuation, mock_handler_details)

        request = MagicMock()

        # First request should succeed
        result1 = await wrapped_handler.unary_unary(request, mock_context)
        assert result1 == 'response'

        # Second request should be rate limited
        result2 = await wrapped_handler.unary_unary(request, mock_context)
        assert result2 is None
        mock_context.abort.assert_called_once()

    @pytest.mark.asyncio
    async def test_wrap_unary_stream_allows_request(
        self, create_mock_handler, mock_context, mock_handler_details
    ):
        """Test unary-stream wrapper allows request within limit."""
        interceptor = RateLimitInterceptor(max_requests=10)

        async def continuation(handler_call_details):
            return create_mock_handler('unary_stream')

        wrapped_handler = await interceptor.intercept_service(continuation, mock_handler_details)

        request = MagicMock()
        results = []
        async for item in wrapped_handler.unary_stream(request, mock_context):
            results.append(item)

        assert results == ['response1', 'response2']
        mock_context.abort.assert_not_called()

    @pytest.mark.asyncio
    async def test_wrap_unary_stream_rate_limited(
        self, create_mock_handler, mock_context, mock_handler_details
    ):
        """Test unary-stream wrapper aborts when rate limited."""
        interceptor = RateLimitInterceptor(max_requests=1)

        async def continuation(handler_call_details):
            return create_mock_handler('unary_stream')

        wrapped_handler = await interceptor.intercept_service(continuation, mock_handler_details)

        request = MagicMock()

        # First request should succeed
        results1 = []
        async for item in wrapped_handler.unary_stream(request, mock_context):
            results1.append(item)
        assert len(results1) == 2

        # Second request should be rate limited (returns immediately)
        results2 = []
        async for item in wrapped_handler.unary_stream(request, mock_context):
            results2.append(item)

        assert len(results2) == 0
        mock_context.abort.assert_called_once()

    @pytest.mark.asyncio
    async def test_wrap_stream_unary_allows_request(
        self, create_mock_handler, mock_context, mock_handler_details
    ):
        """Test stream-unary wrapper allows request within limit."""
        interceptor = RateLimitInterceptor(max_requests=10)

        async def continuation(handler_call_details):
            return create_mock_handler('stream_unary')

        wrapped_handler = await interceptor.intercept_service(continuation, mock_handler_details)

        async def request_iterator():
            yield 'request1'

        result = await wrapped_handler.stream_unary(request_iterator(), mock_context)

        assert result == 'response'
        mock_context.abort.assert_not_called()

    @pytest.mark.asyncio
    async def test_wrap_stream_unary_rate_limited(
        self, create_mock_handler, mock_context, mock_handler_details
    ):
        """Test stream-unary wrapper aborts when rate limited."""
        interceptor = RateLimitInterceptor(max_requests=1)

        async def continuation(handler_call_details):
            return create_mock_handler('stream_unary')

        wrapped_handler = await interceptor.intercept_service(continuation, mock_handler_details)

        async def request_iterator():
            yield 'request1'

        # First request should succeed
        result1 = await wrapped_handler.stream_unary(request_iterator(), mock_context)
        assert result1 == 'response'

        # Second request should be rate limited
        result2 = await wrapped_handler.stream_unary(request_iterator(), mock_context)
        assert result2 is None
        mock_context.abort.assert_called_once()

    @pytest.mark.asyncio
    async def test_wrap_stream_stream_allows_request(
        self, create_mock_handler, mock_context, mock_handler_details
    ):
        """Test stream-stream wrapper allows request within limit."""
        interceptor = RateLimitInterceptor(max_requests=10)

        async def continuation(handler_call_details):
            return create_mock_handler('stream_stream')

        wrapped_handler = await interceptor.intercept_service(continuation, mock_handler_details)

        async def request_iterator():
            yield 'request1'

        results = []
        async for item in wrapped_handler.stream_stream(request_iterator(), mock_context):
            results.append(item)

        assert results == ['response1', 'response2']
        mock_context.abort.assert_not_called()

    @pytest.mark.asyncio
    async def test_wrap_stream_stream_rate_limited(
        self, create_mock_handler, mock_context, mock_handler_details
    ):
        """Test stream-stream wrapper aborts when rate limited."""
        interceptor = RateLimitInterceptor(max_requests=1)

        async def continuation(handler_call_details):
            return create_mock_handler('stream_stream')

        wrapped_handler = await interceptor.intercept_service(continuation, mock_handler_details)

        async def request_iterator():
            yield 'request1'

        # First request should succeed
        results1 = []
        async for item in wrapped_handler.stream_stream(request_iterator(), mock_context):
            results1.append(item)
        assert len(results1) == 2

        # Second request should be rate limited
        results2 = []
        async for item in wrapped_handler.stream_stream(request_iterator(), mock_context):
            results2.append(item)

        assert len(results2) == 0
        mock_context.abort.assert_called_once()

    @pytest.mark.asyncio
    async def test_concurrent_requests_different_clients(self, mock_context):
        """Test that concurrent requests from different clients are handled correctly."""
        interceptor = RateLimitInterceptor(max_requests=5)

        # Create multiple contexts with different IPs
        contexts = []
        for i in range(3):
            ctx = MagicMock(spec=grpc.aio.ServicerContext)
            ctx.peer.return_value = f'ipv4:192.168.1.{i}:12345'
            ctx.invocation_metadata.return_value = []
            ctx.abort = AsyncMock()
            contexts.append(ctx)

        # Make concurrent requests from different clients
        tasks = [
            interceptor._check_rate_limit(ctx, '/test.Service/Method', is_read=True)
            for ctx in contexts
        ]
        results = await asyncio.gather(*tasks)

        # All should be allowed
        assert all(results)
        for ctx in contexts:
            ctx.abort.assert_not_called()

    @pytest.mark.asyncio
    async def test_rate_limit_logging(self, mock_context, caplog):
        """Test that rate limit exceeded events are logged."""
        import logging

        interceptor = RateLimitInterceptor(max_requests=1)

        # Make requests up to limit
        await interceptor._check_rate_limit(mock_context, '/test.Service/Method', is_read=True)

        with caplog.at_level(logging.WARNING):
            # Next request should log warning
            await interceptor._check_rate_limit(mock_context, '/test.Service/Method', is_read=True)

        assert 'Rate limit exceeded' in caplog.text
        assert 'ip:127.0.0.1' in caplog.text
