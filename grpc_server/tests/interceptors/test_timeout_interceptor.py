"""Tests for TimeoutInterceptor."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import grpc
import pytest

from src.config.schema import ServiceTimeoutConfig, TimeoutConfig
from src.interceptors.timeout_interceptor import TimeoutInterceptor


class TestTimeoutConfig:
    """Tests for TimeoutConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = TimeoutConfig()

        assert config.enabled is True
        assert config.default == 30.0
        assert config.services == {}

    def test_get_timeout_global_default(self):
        """Test get_timeout returns global default for unknown service."""
        config = TimeoutConfig(default=45.0)

        timeout = config.get_timeout('UnknownService', 'SomeMethod')
        assert timeout == 45.0

    def test_get_timeout_service_default(self):
        """Test get_timeout returns service default when configured."""
        config = TimeoutConfig(
            default=30.0,
            services={
                'IngestService': ServiceTimeoutConfig(default=120.0),
            },
        )

        timeout = config.get_timeout('IngestService', 'UnknownMethod')
        assert timeout == 120.0

    def test_get_timeout_method_override(self):
        """Test get_timeout returns method-specific timeout when configured."""
        config = TimeoutConfig(
            default=30.0,
            services={
                'IngestService': ServiceTimeoutConfig(
                    default=120.0,
                    methods={'AddEpisodeBulk': 600.0},
                ),
            },
        )

        timeout = config.get_timeout('IngestService', 'AddEpisodeBulk')
        assert timeout == 600.0

    def test_get_timeout_zero_means_no_timeout(self):
        """Test that timeout=0 means no timeout."""
        config = TimeoutConfig(
            default=30.0,
            services={
                'IngestService': ServiceTimeoutConfig(
                    default=120.0,
                    methods={'StreamEpisodes': 0},
                ),
            },
        )

        timeout = config.get_timeout('IngestService', 'StreamEpisodes')
        assert timeout == 0


class TestTimeoutInterceptorParsing:
    """Tests for method path parsing."""

    def test_parse_method_path_standard(self):
        """Test parsing standard gRPC method path."""
        interceptor = TimeoutInterceptor()

        service, method = interceptor._parse_method_path('/graphiti.v1.IngestService/AddEpisode')

        assert service == 'IngestService'
        assert method == 'AddEpisode'

    def test_parse_method_path_health(self):
        """Test parsing health check method path."""
        interceptor = TimeoutInterceptor()

        service, method = interceptor._parse_method_path('/grpc.health.v1.Health/Check')

        assert service == 'Health'
        assert method == 'Check'

    def test_parse_method_path_no_package(self):
        """Test parsing method path without package prefix."""
        interceptor = TimeoutInterceptor()

        service, method = interceptor._parse_method_path('/ServiceName/MethodName')

        assert service == 'ServiceName'
        assert method == 'MethodName'


class TestTimeoutInterceptorConfiguration:
    """Tests for interceptor configuration."""

    def test_default_interceptor(self):
        """Test interceptor with default configuration."""
        interceptor = TimeoutInterceptor()

        assert interceptor.config.enabled is True
        assert interceptor.config.default == 30.0

    def test_interceptor_with_custom_config(self):
        """Test interceptor with custom configuration."""
        config = TimeoutConfig(
            enabled=True,
            default=60.0,
            services={
                'IngestService': ServiceTimeoutConfig(default=120.0),
            },
        )
        interceptor = TimeoutInterceptor(config)

        assert interceptor.config.default == 60.0
        assert 'IngestService' in interceptor.config.services

    def test_get_timeout_for_method(self):
        """Test getting timeout for specific method."""
        config = TimeoutConfig(
            default=30.0,
            services={
                'IngestService': ServiceTimeoutConfig(
                    default=120.0,
                    methods={'AddEpisodeBulk': 600.0},
                ),
            },
        )
        interceptor = TimeoutInterceptor(config)

        # Service default
        timeout = interceptor._get_timeout('/graphiti.v1.IngestService/AddEpisode')
        assert timeout == 120.0

        # Method override
        timeout = interceptor._get_timeout('/graphiti.v1.IngestService/AddEpisodeBulk')
        assert timeout == 600.0

        # Global default for unknown service
        timeout = interceptor._get_timeout('/graphiti.v1.RetrieveService/Search')
        assert timeout == 30.0


class TestTimeoutInterceptorSkipLogic:
    """Tests for skip timeout logic."""

    def test_should_skip_when_disabled(self):
        """Test timeout is skipped when disabled in config."""
        config = TimeoutConfig(enabled=False)
        interceptor = TimeoutInterceptor(config)

        assert interceptor._should_skip_timeout('/any/Method', 30.0) is True

    def test_should_skip_when_timeout_zero(self):
        """Test timeout is skipped when timeout is 0."""
        interceptor = TimeoutInterceptor()

        assert interceptor._should_skip_timeout('/any/Method', 0) is True

    def test_should_skip_default_methods(self):
        """Test timeout is skipped for default skip methods."""
        interceptor = TimeoutInterceptor()

        assert interceptor._should_skip_timeout('/grpc.health.v1.Health/Watch', 30.0) is True
        assert (
            interceptor._should_skip_timeout(
                '/grpc.reflection.v1alpha.ServerReflection/ServerReflectionInfo', 30.0
            )
            is True
        )

    def test_should_not_skip_normal_methods(self):
        """Test timeout is not skipped for normal methods."""
        interceptor = TimeoutInterceptor()

        assert interceptor._should_skip_timeout('/graphiti.v1.IngestService/AddEpisode', 30.0) is False


class TestTimeoutInterceptorIntercept:
    """Tests for intercept_service method."""

    @pytest.mark.asyncio
    async def test_intercept_skips_when_disabled(self, create_mock_handler):
        """Test interceptor passes through when disabled."""
        config = TimeoutConfig(enabled=False)
        interceptor = TimeoutInterceptor(config)

        mock_handler = create_mock_handler('unary_unary')

        async def continuation(handler_call_details):
            return mock_handler

        handler_call_details = MagicMock()
        handler_call_details.method = '/graphiti.v1.IngestService/AddEpisode'

        result = await interceptor.intercept_service(continuation, handler_call_details)

        # Should return original handler unchanged
        assert result is mock_handler

    @pytest.mark.asyncio
    async def test_intercept_skips_zero_timeout(self, create_mock_handler):
        """Test interceptor passes through for zero timeout methods."""
        config = TimeoutConfig(
            default=30.0,
            services={
                'IngestService': ServiceTimeoutConfig(
                    default=120.0,
                    methods={'StreamEpisodes': 0},
                ),
            },
        )
        interceptor = TimeoutInterceptor(config)

        mock_handler = create_mock_handler('unary_stream')

        async def continuation(handler_call_details):
            return mock_handler

        handler_call_details = MagicMock()
        handler_call_details.method = '/graphiti.v1.IngestService/StreamEpisodes'

        result = await interceptor.intercept_service(continuation, handler_call_details)

        # Should return original handler unchanged
        assert result is mock_handler

    @pytest.mark.asyncio
    async def test_intercept_returns_none_handler(self):
        """Test interceptor handles None handler gracefully."""
        interceptor = TimeoutInterceptor()

        async def continuation(handler_call_details):
            return None

        handler_call_details = MagicMock()
        handler_call_details.method = '/graphiti.v1.IngestService/AddEpisode'

        result = await interceptor.intercept_service(continuation, handler_call_details)
        assert result is None


class TestTimeoutInterceptorUnaryUnary:
    """Tests for unary-unary timeout wrapper."""

    @pytest.mark.asyncio
    async def test_wrap_unary_unary_success(self, create_mock_handler):
        """Test unary-unary wrapper passes through on success."""
        config = TimeoutConfig(default=5.0)
        interceptor = TimeoutInterceptor(config)
        mock_handler = create_mock_handler('unary_unary')

        mock_context = MagicMock()
        mock_context.time_remaining = MagicMock(return_value=None)

        wrapped = interceptor._wrap_unary_unary(mock_handler, '/test/Method', 5.0)
        result = await wrapped.unary_unary(MagicMock(), mock_context)

        assert result == 'response'

    @pytest.mark.asyncio
    async def test_wrap_unary_unary_timeout(self):
        """Test unary-unary wrapper handles timeout."""
        config = TimeoutConfig(default=0.1)
        interceptor = TimeoutInterceptor(config)

        async def slow_handler(request, context):
            await asyncio.sleep(1.0)
            return 'response'

        mock_handler = MagicMock()
        mock_handler.unary_unary = slow_handler
        mock_handler.request_deserializer = None
        mock_handler.response_serializer = None

        mock_context = MagicMock()
        mock_context.abort = AsyncMock()
        mock_context.time_remaining = MagicMock(return_value=None)

        wrapped = interceptor._wrap_unary_unary(mock_handler, '/test/Method', 0.1)
        await wrapped.unary_unary(MagicMock(), mock_context)

        mock_context.abort.assert_called_once()
        call_args = mock_context.abort.call_args
        assert call_args[0][0] == grpc.StatusCode.DEADLINE_EXCEEDED

    @pytest.mark.asyncio
    async def test_wrap_unary_unary_no_timeout_when_zero(self, create_mock_handler):
        """Test unary-unary wrapper skips timeout when timeout is 0."""
        interceptor = TimeoutInterceptor()
        mock_handler = create_mock_handler('unary_unary')

        mock_context = MagicMock()
        mock_context.time_remaining = MagicMock(return_value=None)

        wrapped = interceptor._wrap_unary_unary(mock_handler, '/test/Method', 0)
        result = await wrapped.unary_unary(MagicMock(), mock_context)

        assert result == 'response'


class TestTimeoutInterceptorUnaryStream:
    """Tests for unary-stream timeout wrapper."""

    @pytest.mark.asyncio
    async def test_wrap_unary_stream_success(self, create_mock_handler):
        """Test unary-stream wrapper passes through on success."""
        config = TimeoutConfig(default=5.0)
        interceptor = TimeoutInterceptor(config)
        mock_handler = create_mock_handler('unary_stream')

        mock_context = MagicMock()
        mock_context.time_remaining = MagicMock(return_value=None)

        wrapped = interceptor._wrap_unary_stream(mock_handler, '/test/Method', 5.0)

        results = []
        async for item in wrapped.unary_stream(MagicMock(), mock_context):
            results.append(item)

        assert results == ['response1', 'response2']

    @pytest.mark.asyncio
    async def test_wrap_unary_stream_no_timeout_when_zero(self, create_mock_handler):
        """Test unary-stream wrapper skips timeout when timeout is 0."""
        interceptor = TimeoutInterceptor()
        mock_handler = create_mock_handler('unary_stream')

        mock_context = MagicMock()
        mock_context.time_remaining = MagicMock(return_value=None)

        wrapped = interceptor._wrap_unary_stream(mock_handler, '/test/Method', 0)

        results = []
        async for item in wrapped.unary_stream(MagicMock(), mock_context):
            results.append(item)

        assert results == ['response1', 'response2']


class TestTimeoutInterceptorStreamUnary:
    """Tests for stream-unary timeout wrapper."""

    @pytest.mark.asyncio
    async def test_wrap_stream_unary_success(self, create_mock_handler):
        """Test stream-unary wrapper passes through on success."""
        config = TimeoutConfig(default=5.0)
        interceptor = TimeoutInterceptor(config)
        mock_handler = create_mock_handler('stream_unary')

        mock_context = MagicMock()
        mock_context.time_remaining = MagicMock(return_value=None)

        async def request_iterator():
            yield 'request1'
            yield 'request2'

        wrapped = interceptor._wrap_stream_unary(mock_handler, '/test/Method', 5.0)
        result = await wrapped.stream_unary(request_iterator(), mock_context)

        assert result == 'response'

    @pytest.mark.asyncio
    async def test_wrap_stream_unary_timeout(self):
        """Test stream-unary wrapper handles timeout."""
        config = TimeoutConfig(default=0.1)
        interceptor = TimeoutInterceptor(config)

        async def slow_handler(request_iterator, context):
            await asyncio.sleep(1.0)
            return 'response'

        mock_handler = MagicMock()
        mock_handler.stream_unary = slow_handler
        mock_handler.request_deserializer = None
        mock_handler.response_serializer = None

        mock_context = MagicMock()
        mock_context.abort = AsyncMock()
        mock_context.time_remaining = MagicMock(return_value=None)

        async def request_iterator():
            yield 'request1'

        wrapped = interceptor._wrap_stream_unary(mock_handler, '/test/Method', 0.1)
        await wrapped.stream_unary(request_iterator(), mock_context)

        mock_context.abort.assert_called_once()
        call_args = mock_context.abort.call_args
        assert call_args[0][0] == grpc.StatusCode.DEADLINE_EXCEEDED

    @pytest.mark.asyncio
    async def test_wrap_stream_unary_no_timeout_when_zero(self, create_mock_handler):
        """Test stream-unary wrapper skips timeout when timeout is 0."""
        interceptor = TimeoutInterceptor()
        mock_handler = create_mock_handler('stream_unary')

        mock_context = MagicMock()
        mock_context.time_remaining = MagicMock(return_value=None)

        async def request_iterator():
            yield 'request1'
            yield 'request2'

        wrapped = interceptor._wrap_stream_unary(mock_handler, '/test/Method', 0)
        result = await wrapped.stream_unary(request_iterator(), mock_context)

        assert result == 'response'


class TestTimeoutInterceptorStreamStream:
    """Tests for stream-stream timeout wrapper."""

    @pytest.mark.asyncio
    async def test_wrap_stream_stream_success(self, create_mock_handler):
        """Test stream-stream wrapper passes through on success."""
        config = TimeoutConfig(default=5.0)
        interceptor = TimeoutInterceptor(config)
        mock_handler = create_mock_handler('stream_stream')

        mock_context = MagicMock()
        mock_context.time_remaining = MagicMock(return_value=None)

        async def request_iterator():
            yield 'request1'

        wrapped = interceptor._wrap_stream_stream(mock_handler, '/test/Method', 5.0)

        results = []
        async for item in wrapped.stream_stream(request_iterator(), mock_context):
            results.append(item)

        assert results == ['response1', 'response2']

    @pytest.mark.asyncio
    async def test_wrap_stream_stream_no_timeout_when_zero(self, create_mock_handler):
        """Test stream-stream wrapper skips timeout when timeout is 0."""
        interceptor = TimeoutInterceptor()
        mock_handler = create_mock_handler('stream_stream')

        mock_context = MagicMock()
        mock_context.time_remaining = MagicMock(return_value=None)

        async def request_iterator():
            yield 'request1'

        wrapped = interceptor._wrap_stream_stream(mock_handler, '/test/Method', 0)

        results = []
        async for item in wrapped.stream_stream(request_iterator(), mock_context):
            results.append(item)

        assert results == ['response1', 'response2']


class TestEffectiveTimeout:
    """Tests for effective timeout calculation."""

    def test_effective_timeout_uses_server_timeout(self):
        """Test effective timeout uses server timeout when no client deadline."""
        interceptor = TimeoutInterceptor()

        mock_context = MagicMock()
        mock_context.time_remaining = MagicMock(return_value=None)

        effective = interceptor._get_effective_timeout(mock_context, 30.0)
        assert effective == 30.0

    def test_effective_timeout_uses_client_deadline_when_shorter(self):
        """Test effective timeout uses client deadline when shorter."""
        interceptor = TimeoutInterceptor()

        mock_context = MagicMock()
        mock_context.time_remaining = MagicMock(return_value=10.0)

        effective = interceptor._get_effective_timeout(mock_context, 30.0)
        assert effective == 10.0

    def test_effective_timeout_uses_server_when_shorter(self):
        """Test effective timeout uses server timeout when shorter than client."""
        interceptor = TimeoutInterceptor()

        mock_context = MagicMock()
        mock_context.time_remaining = MagicMock(return_value=60.0)

        effective = interceptor._get_effective_timeout(mock_context, 30.0)
        assert effective == 30.0

    def test_effective_timeout_zero_returns_zero(self):
        """Test effective timeout returns 0 when server timeout is 0."""
        interceptor = TimeoutInterceptor()

        mock_context = MagicMock()
        mock_context.time_remaining = MagicMock(return_value=30.0)

        effective = interceptor._get_effective_timeout(mock_context, 0)
        assert effective == 0

    def test_effective_timeout_handles_exception(self):
        """Test effective timeout handles exception from time_remaining."""
        interceptor = TimeoutInterceptor()

        mock_context = MagicMock()
        mock_context.time_remaining = MagicMock(side_effect=Exception('Not available'))

        effective = interceptor._get_effective_timeout(mock_context, 30.0)
        assert effective == 30.0


class TestStreamTimeoutEdgeCases:
    """Tests for streaming timeout edge cases."""

    @pytest.mark.asyncio
    async def test_wrap_unary_stream_timeout(self):
        """Test unary-stream wrapper handles timeout during streaming."""
        config = TimeoutConfig(default=0.1)
        interceptor = TimeoutInterceptor(config)

        async def slow_stream_handler(request, context):
            yield 'response1'
            await asyncio.sleep(1.0)  # Exceed timeout
            yield 'response2'

        mock_handler = MagicMock()
        mock_handler.unary_stream = slow_stream_handler
        mock_handler.request_deserializer = None
        mock_handler.response_serializer = None

        mock_context = MagicMock()
        mock_context.abort = AsyncMock()
        mock_context.time_remaining = MagicMock(return_value=None)

        wrapped = interceptor._wrap_unary_stream(mock_handler, '/test/Method', 0.1)

        results = []
        try:
            async for item in wrapped.unary_stream(MagicMock(), mock_context):
                results.append(item)
        except Exception:
            pass  # Expected to abort

        # Should have received at least the first item before timeout
        assert len(results) >= 1
        mock_context.abort.assert_called_once()
        call_args = mock_context.abort.call_args
        assert call_args[0][0] == grpc.StatusCode.DEADLINE_EXCEEDED

    @pytest.mark.asyncio
    async def test_wrap_stream_stream_timeout(self):
        """Test stream-stream wrapper handles timeout during streaming."""
        config = TimeoutConfig(default=0.1)
        interceptor = TimeoutInterceptor(config)

        async def slow_bidir_handler(request_iterator, context):
            async for request in request_iterator:
                yield f'response_to_{request}'
                await asyncio.sleep(1.0)  # Exceed timeout
                yield 'response2'

        mock_handler = MagicMock()
        mock_handler.stream_stream = slow_bidir_handler
        mock_handler.request_deserializer = None
        mock_handler.response_serializer = None

        mock_context = MagicMock()
        mock_context.abort = AsyncMock()
        mock_context.time_remaining = MagicMock(return_value=None)

        async def request_iterator():
            yield 'request1'

        wrapped = interceptor._wrap_stream_stream(mock_handler, '/test/Method', 0.1)

        results = []
        try:
            async for item in wrapped.stream_stream(request_iterator(), mock_context):
                results.append(item)
        except Exception:
            pass  # Expected to abort

        # Should have received at least the first item before timeout
        assert len(results) >= 1
        mock_context.abort.assert_called_once()
        call_args = mock_context.abort.call_args
        assert call_args[0][0] == grpc.StatusCode.DEADLINE_EXCEEDED


class TestClientDeadlineEdgeCases:
    """Tests for client deadline interaction edge cases."""

    def test_effective_timeout_client_deadline_zero(self):
        """Test effective timeout when client deadline is 0 or negative."""
        interceptor = TimeoutInterceptor()

        mock_context = MagicMock()
        mock_context.time_remaining = MagicMock(return_value=0)

        # When client deadline is 0 or negative, should use server timeout
        effective = interceptor._get_effective_timeout(mock_context, 30.0)
        assert effective == 30.0

    def test_effective_timeout_client_deadline_negative(self):
        """Test effective timeout when client deadline is negative (expired)."""
        interceptor = TimeoutInterceptor()

        mock_context = MagicMock()
        mock_context.time_remaining = MagicMock(return_value=-5.0)

        # When client deadline is negative, should use server timeout
        effective = interceptor._get_effective_timeout(mock_context, 30.0)
        assert effective == 30.0

    @pytest.mark.asyncio
    async def test_wrap_unary_unary_with_client_deadline(self, create_mock_handler):
        """Test unary-unary wrapper respects client deadline when shorter."""
        config = TimeoutConfig(default=30.0)
        interceptor = TimeoutInterceptor(config)
        mock_handler = create_mock_handler('unary_unary')

        mock_context = MagicMock()
        # Client has a shorter deadline (5 seconds)
        mock_context.time_remaining = MagicMock(return_value=5.0)

        wrapped = interceptor._wrap_unary_unary(mock_handler, '/test/Method', 30.0)
        result = await wrapped.unary_unary(MagicMock(), mock_context)

        # Should succeed with the shorter client deadline
        assert result == 'response'

    @pytest.mark.asyncio
    async def test_wrap_stream_unary_with_client_deadline(self, create_mock_handler):
        """Test stream-unary wrapper respects client deadline when shorter."""
        config = TimeoutConfig(default=30.0)
        interceptor = TimeoutInterceptor(config)
        mock_handler = create_mock_handler('stream_unary')

        mock_context = MagicMock()
        # Client has a shorter deadline (5 seconds)
        mock_context.time_remaining = MagicMock(return_value=5.0)

        async def request_iterator():
            yield 'request1'
            yield 'request2'

        wrapped = interceptor._wrap_stream_unary(mock_handler, '/test/Method', 30.0)
        result = await wrapped.stream_unary(request_iterator(), mock_context)

        # Should succeed with the shorter client deadline
        assert result == 'response'


class TestMethodPathParsingEdgeCases:
    """Tests for edge cases in method path parsing."""

    def test_parse_method_path_malformed_single_part(self):
        """Test parsing malformed method path with single part."""
        interceptor = TimeoutInterceptor()

        service, method = interceptor._parse_method_path('/SinglePart')

        # Should return empty service and the original method
        assert service == ''
        assert method == '/SinglePart'

    def test_parse_method_path_empty(self):
        """Test parsing empty method path."""
        interceptor = TimeoutInterceptor()

        service, method = interceptor._parse_method_path('')

        # Should return empty strings
        assert service == ''
        assert method == ''


class TestInterceptUnknownHandlerType:
    """Tests for intercept_service with unknown handler types."""

    @pytest.mark.asyncio
    async def test_intercept_unknown_handler_type(self):
        """Test interceptor handles unknown handler type gracefully."""
        interceptor = TimeoutInterceptor()

        # Create a handler with no recognized handler type
        mock_handler = MagicMock()
        mock_handler.unary_unary = None
        mock_handler.unary_stream = None
        mock_handler.stream_unary = None
        mock_handler.stream_stream = None

        async def continuation(handler_call_details):
            return mock_handler

        handler_call_details = MagicMock()
        handler_call_details.method = '/graphiti.v1.IngestService/AddEpisode'

        result = await interceptor.intercept_service(continuation, handler_call_details)

        # Should return the handler unchanged
        assert result is mock_handler

    @pytest.mark.asyncio
    async def test_intercept_wraps_unary_stream(self, create_mock_handler):
        """Test interceptor wraps unary-stream handler."""
        interceptor = TimeoutInterceptor()
        mock_handler = create_mock_handler('unary_stream')

        async def continuation(handler_call_details):
            return mock_handler

        handler_call_details = MagicMock()
        handler_call_details.method = '/graphiti.v1.IngestService/StreamEpisodes'

        result = await interceptor.intercept_service(continuation, handler_call_details)

        # Should return a wrapped handler (not the same object)
        assert result is not mock_handler
        assert result.unary_stream is not None

    @pytest.mark.asyncio
    async def test_intercept_wraps_stream_unary(self, create_mock_handler):
        """Test interceptor wraps stream-unary handler."""
        interceptor = TimeoutInterceptor()
        mock_handler = create_mock_handler('stream_unary')

        async def continuation(handler_call_details):
            return mock_handler

        handler_call_details = MagicMock()
        handler_call_details.method = '/graphiti.v1.IngestService/AddEpisode'

        result = await interceptor.intercept_service(continuation, handler_call_details)

        # Should return a wrapped handler (not the same object)
        assert result is not mock_handler
        assert result.stream_unary is not None

    @pytest.mark.asyncio
    async def test_intercept_wraps_stream_stream(self, create_mock_handler):
        """Test interceptor wraps stream-stream handler."""
        interceptor = TimeoutInterceptor()
        mock_handler = create_mock_handler('stream_stream')

        async def continuation(handler_call_details):
            return mock_handler

        handler_call_details = MagicMock()
        handler_call_details.method = '/graphiti.v1.IngestService/StreamBidirectional'

        result = await interceptor.intercept_service(continuation, handler_call_details)

        # Should return a wrapped handler (not the same object)
        assert result is not mock_handler
        assert result.stream_stream is not None


class TestFullIntegration:
    """Integration tests for the full timeout interceptor flow."""

    @pytest.mark.asyncio
    async def test_full_flow_with_service_config(self, create_mock_handler):
        """Test full interceptor flow with service-specific configuration."""
        config = TimeoutConfig(
            enabled=True,
            default=30.0,
            services={
                'IngestService': ServiceTimeoutConfig(
                    default=120.0,
                    methods={
                        'AddEpisodeBulk': 600.0,
                        'StreamEpisodes': 0,
                    },
                ),
                'RetrieveService': ServiceTimeoutConfig(default=30.0),
                'AdminService': ServiceTimeoutConfig(
                    default=60.0,
                    methods={
                        'BuildCommunities': 300.0,
                        'ClearData': 120.0,
                    },
                ),
            },
        )
        interceptor = TimeoutInterceptor(config)

        # Test IngestService default
        timeout = interceptor._get_timeout('/graphiti.v1.IngestService/AddEpisode')
        assert timeout == 120.0

        # Test IngestService method override
        timeout = interceptor._get_timeout('/graphiti.v1.IngestService/AddEpisodeBulk')
        assert timeout == 600.0

        # Test IngestService streaming (no timeout)
        timeout = interceptor._get_timeout('/graphiti.v1.IngestService/StreamEpisodes')
        assert timeout == 0

        # Test RetrieveService default
        timeout = interceptor._get_timeout('/graphiti.v1.RetrieveService/Search')
        assert timeout == 30.0

        # Test AdminService method override
        timeout = interceptor._get_timeout('/graphiti.v1.AdminService/BuildCommunities')
        assert timeout == 300.0

        # Test unknown service uses global default
        timeout = interceptor._get_timeout('/graphiti.v1.UnknownService/SomeMethod')
        assert timeout == 30.0
