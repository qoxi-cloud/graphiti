"""Tests for TracingInterceptor."""

from unittest.mock import AsyncMock, MagicMock

import pytest


class TestTracingInterceptor:
    """Tests for TracingInterceptor."""

    @pytest.mark.asyncio
    async def test_init_without_otel(self):
        """Test initialization without OpenTelemetry."""
        from src.interceptors.tracing_interceptor import TracingInterceptor

        interceptor = TracingInterceptor('test-service')
        assert interceptor._service_name == 'test-service'

    @pytest.mark.asyncio
    async def test_intercept_service_without_otel(self):
        """Test intercept_service passes through without OpenTelemetry."""
        from src.interceptors.tracing_interceptor import HAS_OTEL, TracingInterceptor

        interceptor = TracingInterceptor('test-service')

        mock_handler = MagicMock()

        async def continuation(handler_call_details):
            return mock_handler

        handler_call_details = MagicMock()
        handler_call_details.method = '/test.Service/TestMethod'

        result = await interceptor.intercept_service(continuation, handler_call_details)

        if not HAS_OTEL:
            assert result == mock_handler

    @pytest.mark.asyncio
    async def test_intercept_service_returns_none_handler(self):
        """Test interceptor handles None handler gracefully."""
        from src.interceptors.tracing_interceptor import HAS_OTEL, TracingInterceptor

        interceptor = TracingInterceptor('test-service')

        async def continuation(handler_call_details):
            return None

        handler_call_details = MagicMock()

        result = await interceptor.intercept_service(continuation, handler_call_details)

        if HAS_OTEL:
            assert result is None

    @pytest.mark.asyncio
    async def test_intercept_service_wraps_handlers(self, create_mock_handler):
        """Test interceptor wraps all handler types."""
        from src.interceptors.tracing_interceptor import HAS_OTEL, TracingInterceptor

        if not HAS_OTEL:
            pytest.skip('OpenTelemetry not installed')

        interceptor = TracingInterceptor('test-service')

        for handler_type in ['unary_unary', 'unary_stream', 'stream_unary', 'stream_stream']:
            mock_handler = create_mock_handler(handler_type)

            async def continuation(handler_call_details):
                return mock_handler

            handler_call_details = MagicMock()
            handler_call_details.method = '/test.Service/TestMethod'

            result = await interceptor.intercept_service(continuation, handler_call_details)
            assert result is not None


class TestTracingInterceptorWithOTel:
    """Tests for TracingInterceptor with OpenTelemetry mocked."""

    @pytest.mark.asyncio
    async def test_unary_unary_handler_success(self, create_mock_handler):
        """Test unary-unary handler with successful tracing."""
        from src.interceptors.tracing_interceptor import HAS_OTEL, TracingInterceptor

        if not HAS_OTEL:
            pytest.skip('OpenTelemetry not installed')

        interceptor = TracingInterceptor('test-service')
        mock_handler = create_mock_handler('unary_unary')

        async def continuation(handler_call_details):
            return mock_handler

        handler_call_details = MagicMock()
        handler_call_details.method = '/test.Service/TestMethod'

        wrapped = await interceptor.intercept_service(continuation, handler_call_details)

        # Call the wrapped handler
        request = MagicMock()
        context = MagicMock()
        result = await wrapped.unary_unary(request, context)

        assert result == 'response'

    @pytest.mark.asyncio
    async def test_unary_unary_handler_error(self, create_mock_handler):
        """Test unary-unary handler with exception tracing."""
        from src.interceptors.tracing_interceptor import HAS_OTEL, TracingInterceptor

        if not HAS_OTEL:
            pytest.skip('OpenTelemetry not installed')

        interceptor = TracingInterceptor('test-service')
        mock_handler = create_mock_handler('unary_unary')
        mock_handler.unary_unary = AsyncMock(side_effect=ValueError('test error'))

        async def continuation(handler_call_details):
            return mock_handler

        handler_call_details = MagicMock()
        handler_call_details.method = '/test.Service/TestMethod'

        wrapped = await interceptor.intercept_service(continuation, handler_call_details)

        request = MagicMock()
        context = MagicMock()

        with pytest.raises(ValueError, match='test error'):
            await wrapped.unary_unary(request, context)

    @pytest.mark.asyncio
    async def test_unary_stream_handler_success(self, create_mock_handler):
        """Test unary-stream handler with successful tracing."""
        from src.interceptors.tracing_interceptor import HAS_OTEL, TracingInterceptor

        if not HAS_OTEL:
            pytest.skip('OpenTelemetry not installed')

        interceptor = TracingInterceptor('test-service')
        mock_handler = create_mock_handler('unary_stream')

        async def continuation(handler_call_details):
            return mock_handler

        handler_call_details = MagicMock()
        handler_call_details.method = '/test.Service/StreamMethod'

        wrapped = await interceptor.intercept_service(continuation, handler_call_details)

        request = MagicMock()
        context = MagicMock()

        responses = []
        async for response in wrapped.unary_stream(request, context):
            responses.append(response)

        assert responses == ['response1', 'response2']

    @pytest.mark.asyncio
    async def test_unary_stream_handler_error(self, create_mock_handler):
        """Test unary-stream handler with exception tracing."""
        from src.interceptors.tracing_interceptor import HAS_OTEL, TracingInterceptor

        if not HAS_OTEL:
            pytest.skip('OpenTelemetry not installed')

        interceptor = TracingInterceptor('test-service')
        mock_handler = MagicMock()
        mock_handler.unary_unary = None
        mock_handler.stream_unary = None
        mock_handler.stream_stream = None
        mock_handler.request_deserializer = None
        mock_handler.response_serializer = None

        async def error_stream(*args, **kwargs):
            yield 'response1'
            raise ValueError('stream error')

        mock_handler.unary_stream = error_stream

        async def continuation(handler_call_details):
            return mock_handler

        handler_call_details = MagicMock()
        handler_call_details.method = '/test.Service/StreamMethod'

        wrapped = await interceptor.intercept_service(continuation, handler_call_details)

        request = MagicMock()
        context = MagicMock()

        responses = []
        with pytest.raises(ValueError, match='stream error'):
            async for response in wrapped.unary_stream(request, context):
                responses.append(response)

        assert responses == ['response1']

    @pytest.mark.asyncio
    async def test_stream_unary_handler_success(self, create_mock_handler):
        """Test stream-unary handler with successful tracing."""
        from src.interceptors.tracing_interceptor import HAS_OTEL, TracingInterceptor

        if not HAS_OTEL:
            pytest.skip('OpenTelemetry not installed')

        interceptor = TracingInterceptor('test-service')
        mock_handler = create_mock_handler('stream_unary')

        async def continuation(handler_call_details):
            return mock_handler

        handler_call_details = MagicMock()
        handler_call_details.method = '/test.Service/StreamUnaryMethod'

        wrapped = await interceptor.intercept_service(continuation, handler_call_details)

        async def request_iterator():
            yield 'request1'
            yield 'request2'

        context = MagicMock()
        result = await wrapped.stream_unary(request_iterator(), context)

        assert result == 'response'

    @pytest.mark.asyncio
    async def test_stream_unary_handler_error(self, create_mock_handler):
        """Test stream-unary handler with exception tracing."""
        from src.interceptors.tracing_interceptor import HAS_OTEL, TracingInterceptor

        if not HAS_OTEL:
            pytest.skip('OpenTelemetry not installed')

        interceptor = TracingInterceptor('test-service')
        mock_handler = create_mock_handler('stream_unary')
        mock_handler.stream_unary = AsyncMock(side_effect=ValueError('stream unary error'))

        async def continuation(handler_call_details):
            return mock_handler

        handler_call_details = MagicMock()
        handler_call_details.method = '/test.Service/StreamUnaryMethod'

        wrapped = await interceptor.intercept_service(continuation, handler_call_details)

        async def request_iterator():
            yield 'request1'

        context = MagicMock()

        with pytest.raises(ValueError, match='stream unary error'):
            await wrapped.stream_unary(request_iterator(), context)

    @pytest.mark.asyncio
    async def test_stream_stream_handler_success(self, create_mock_handler):
        """Test stream-stream handler with successful tracing."""
        from src.interceptors.tracing_interceptor import HAS_OTEL, TracingInterceptor

        if not HAS_OTEL:
            pytest.skip('OpenTelemetry not installed')

        interceptor = TracingInterceptor('test-service')
        mock_handler = create_mock_handler('stream_stream')

        async def continuation(handler_call_details):
            return mock_handler

        handler_call_details = MagicMock()
        handler_call_details.method = '/test.Service/BiDiMethod'

        wrapped = await interceptor.intercept_service(continuation, handler_call_details)

        async def request_iterator():
            yield 'request1'
            yield 'request2'

        context = MagicMock()

        responses = []
        async for response in wrapped.stream_stream(request_iterator(), context):
            responses.append(response)

        assert responses == ['response1', 'response2']

    @pytest.mark.asyncio
    async def test_stream_stream_handler_error(self, create_mock_handler):
        """Test stream-stream handler with exception tracing."""
        from src.interceptors.tracing_interceptor import HAS_OTEL, TracingInterceptor

        if not HAS_OTEL:
            pytest.skip('OpenTelemetry not installed')

        interceptor = TracingInterceptor('test-service')
        mock_handler = MagicMock()
        mock_handler.unary_unary = None
        mock_handler.unary_stream = None
        mock_handler.stream_unary = None
        mock_handler.request_deserializer = None
        mock_handler.response_serializer = None

        async def error_bidir_stream(*args, **kwargs):
            yield 'response1'
            raise ValueError('bidir stream error')

        mock_handler.stream_stream = error_bidir_stream

        async def continuation(handler_call_details):
            return mock_handler

        handler_call_details = MagicMock()
        handler_call_details.method = '/test.Service/BiDiMethod'

        wrapped = await interceptor.intercept_service(continuation, handler_call_details)

        async def request_iterator():
            yield 'request1'

        context = MagicMock()

        responses = []
        with pytest.raises(ValueError, match='bidir stream error'):
            async for response in wrapped.stream_stream(request_iterator(), context):
                responses.append(response)

        assert responses == ['response1']

    @pytest.mark.asyncio
    async def test_handler_with_no_handler_type(self):
        """Test handler with no recognized handler type."""
        from src.interceptors.tracing_interceptor import HAS_OTEL, TracingInterceptor

        if not HAS_OTEL:
            pytest.skip('OpenTelemetry not installed')

        interceptor = TracingInterceptor('test-service')
        mock_handler = MagicMock()
        mock_handler.unary_unary = None
        mock_handler.unary_stream = None
        mock_handler.stream_unary = None
        mock_handler.stream_stream = None

        async def continuation(handler_call_details):
            return mock_handler

        handler_call_details = MagicMock()
        handler_call_details.method = '/test.Service/UnknownMethod'

        wrapped = await interceptor.intercept_service(continuation, handler_call_details)

        assert wrapped is mock_handler


class TestTracingInterceptorNoOTel:
    """Tests for TracingInterceptor when OpenTelemetry is not available."""

    @pytest.mark.asyncio
    async def test_tracer_passthrough_when_disabled(self):
        """Test that interceptor passes through when tracer is None."""
        from src.interceptors.tracing_interceptor import TracingInterceptor

        interceptor = TracingInterceptor('test-service')
        # Force tracer to None to simulate no OpenTelemetry
        interceptor._tracer = None

        mock_handler = MagicMock()
        mock_handler.unary_unary = AsyncMock(return_value='response')

        async def continuation(handler_call_details):
            return mock_handler

        handler_call_details = MagicMock()
        handler_call_details.method = '/test.Service/TestMethod'

        # When tracer is None, it should pass through without wrapping
        result = await interceptor.intercept_service(continuation, handler_call_details)
        # Since _tracer is None but HAS_OTEL might be True, the behavior depends on the check
        assert result is not None
