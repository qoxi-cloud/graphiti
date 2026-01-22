"""Tests for LoggingInterceptor."""

import logging
from unittest.mock import AsyncMock, MagicMock

import pytest


class TestLoggingInterceptor:
    """Tests for LoggingInterceptor core functionality."""

    @pytest.mark.asyncio
    async def test_intercept_service_logs_request(self, caplog):
        """Test that interceptor logs request start."""
        from src.interceptors.logging_interceptor import LoggingInterceptor

        interceptor = LoggingInterceptor()

        mock_handler = MagicMock()
        mock_handler.unary_unary = AsyncMock(return_value='response')
        mock_handler.unary_stream = None
        mock_handler.stream_unary = None
        mock_handler.stream_stream = None
        mock_handler.request_deserializer = None
        mock_handler.response_serializer = None

        async def continuation(handler_call_details):
            return mock_handler

        handler_call_details = MagicMock()
        handler_call_details.method = '/test.Service/TestMethod'

        with caplog.at_level(logging.INFO):
            await interceptor.intercept_service(continuation, handler_call_details)

        assert 'gRPC request started: /test.Service/TestMethod' in caplog.text

    @pytest.mark.asyncio
    async def test_intercept_service_returns_none_handler(self):
        """Test interceptor handles None handler gracefully."""
        from src.interceptors.logging_interceptor import LoggingInterceptor

        interceptor = LoggingInterceptor()

        async def continuation(handler_call_details):
            return None

        handler_call_details = MagicMock()
        handler_call_details.method = '/test.Service/TestMethod'

        result = await interceptor.intercept_service(continuation, handler_call_details)
        assert result is None

    @pytest.mark.asyncio
    async def test_intercept_service_wraps_unary_stream(self, create_mock_handler):
        """Test intercept_service wraps unary-stream handlers."""
        from src.interceptors.logging_interceptor import LoggingInterceptor

        interceptor = LoggingInterceptor()
        mock_handler = create_mock_handler('unary_stream')

        async def continuation(handler_call_details):
            return mock_handler

        handler_call_details = MagicMock()
        handler_call_details.method = '/test.Service/StreamMethod'

        wrapped = await interceptor.intercept_service(continuation, handler_call_details)
        assert wrapped is not None

    @pytest.mark.asyncio
    async def test_intercept_service_wraps_stream_unary(self, create_mock_handler):
        """Test intercept_service wraps stream-unary handlers."""
        from src.interceptors.logging_interceptor import LoggingInterceptor

        interceptor = LoggingInterceptor()
        mock_handler = create_mock_handler('stream_unary')

        async def continuation(handler_call_details):
            return mock_handler

        handler_call_details = MagicMock()
        handler_call_details.method = '/test.Service/StreamUnaryMethod'

        wrapped = await interceptor.intercept_service(continuation, handler_call_details)
        assert wrapped is not None

    @pytest.mark.asyncio
    async def test_intercept_service_wraps_stream_stream(self, create_mock_handler):
        """Test intercept_service wraps stream-stream handlers."""
        from src.interceptors.logging_interceptor import LoggingInterceptor

        interceptor = LoggingInterceptor()
        mock_handler = create_mock_handler('stream_stream')

        async def continuation(handler_call_details):
            return mock_handler

        handler_call_details = MagicMock()
        handler_call_details.method = '/test.Service/BiDiMethod'

        wrapped = await interceptor.intercept_service(continuation, handler_call_details)
        assert wrapped is not None

    @pytest.mark.asyncio
    async def test_intercept_service_unknown_handler_type(self):
        """Test intercept_service with unknown handler type passes through."""
        from src.interceptors.logging_interceptor import LoggingInterceptor

        interceptor = LoggingInterceptor()

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

    @pytest.mark.asyncio
    async def test_intercept_service_continuation_error(self, caplog):
        """Test intercept_service logs and re-raises continuation errors."""
        from src.interceptors.logging_interceptor import LoggingInterceptor

        interceptor = LoggingInterceptor()

        async def continuation(handler_call_details):
            raise RuntimeError('continuation error')

        handler_call_details = MagicMock()
        handler_call_details.method = '/test.Service/TestMethod'

        with caplog.at_level(logging.ERROR):
            with pytest.raises(RuntimeError, match='continuation error'):
                await interceptor.intercept_service(continuation, handler_call_details)

        assert 'gRPC request failed' in caplog.text


class TestLoggingInterceptorWrappers:
    """Tests for LoggingInterceptor wrapper methods."""

    @pytest.mark.asyncio
    async def test_wrap_unary_unary_logs_completion(self, caplog):
        """Test that unary-unary wrapper logs completion."""
        from src.interceptors.logging_interceptor import LoggingInterceptor

        interceptor = LoggingInterceptor()

        mock_handler = MagicMock()
        mock_handler.unary_unary = AsyncMock(return_value='response')
        mock_handler.request_deserializer = None
        mock_handler.response_serializer = None

        with caplog.at_level(logging.INFO):
            wrapped = interceptor._wrap_unary_unary(mock_handler, '/test.Method', 0.0)
            await wrapped.unary_unary(MagicMock(), MagicMock())

        assert 'gRPC request completed: /test.Method' in caplog.text

    @pytest.mark.asyncio
    async def test_wrap_unary_stream(self, caplog, create_mock_handler):
        """Test unary-stream wrapper logs completion."""
        from src.interceptors.logging_interceptor import LoggingInterceptor

        interceptor = LoggingInterceptor()
        mock_handler = create_mock_handler('unary_stream')

        with caplog.at_level(logging.INFO):
            wrapped = interceptor._wrap_unary_stream(mock_handler, '/test.Method', 0.0)
            results = []
            async for item in wrapped.unary_stream(MagicMock(), MagicMock()):
                results.append(item)

        assert 'gRPC streaming completed' in caplog.text
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_wrap_unary_stream_error(self, caplog, create_mock_handler):
        """Test unary-stream wrapper logs errors."""
        from src.interceptors.logging_interceptor import LoggingInterceptor

        interceptor = LoggingInterceptor()

        mock_handler = MagicMock()
        mock_handler.request_deserializer = None
        mock_handler.response_serializer = None

        async def error_stream(*args, **kwargs):
            yield 'response1'
            raise ValueError('stream error')

        mock_handler.unary_stream = error_stream

        with caplog.at_level(logging.ERROR):
            wrapped = interceptor._wrap_unary_stream(mock_handler, '/test.Method', 0.0)

            responses = []
            with pytest.raises(ValueError, match='stream error'):
                async for item in wrapped.unary_stream(MagicMock(), MagicMock()):
                    responses.append(item)

        assert 'gRPC streaming failed' in caplog.text
        assert responses == ['response1']

    @pytest.mark.asyncio
    async def test_wrap_stream_unary(self, caplog, create_mock_handler):
        """Test stream-unary wrapper logs completion."""
        from src.interceptors.logging_interceptor import LoggingInterceptor

        interceptor = LoggingInterceptor()
        mock_handler = create_mock_handler('stream_unary')

        with caplog.at_level(logging.INFO):
            wrapped = interceptor._wrap_stream_unary(mock_handler, '/test.Method', 0.0)

            async def request_iterator():
                yield 'request1'

            await wrapped.stream_unary(request_iterator(), MagicMock())

        assert 'gRPC request completed' in caplog.text

    @pytest.mark.asyncio
    async def test_wrap_stream_unary_error(self, caplog, create_mock_handler):
        """Test stream-unary wrapper logs errors."""
        from src.interceptors.logging_interceptor import LoggingInterceptor

        interceptor = LoggingInterceptor()
        mock_handler = create_mock_handler('stream_unary')
        mock_handler.stream_unary = AsyncMock(side_effect=ValueError('stream unary error'))

        with caplog.at_level(logging.ERROR):
            wrapped = interceptor._wrap_stream_unary(mock_handler, '/test.Method', 0.0)

            async def request_iterator():
                yield 'request1'

            with pytest.raises(ValueError, match='stream unary error'):
                await wrapped.stream_unary(request_iterator(), MagicMock())

        assert 'gRPC request failed' in caplog.text

    @pytest.mark.asyncio
    async def test_wrap_stream_stream(self, caplog, create_mock_handler):
        """Test stream-stream wrapper logs completion."""
        from src.interceptors.logging_interceptor import LoggingInterceptor

        interceptor = LoggingInterceptor()
        mock_handler = create_mock_handler('stream_stream')

        with caplog.at_level(logging.INFO):
            wrapped = interceptor._wrap_stream_stream(mock_handler, '/test.Method', 0.0)

            async def request_iterator():
                yield 'request1'

            results = []
            async for item in wrapped.stream_stream(request_iterator(), MagicMock()):
                results.append(item)

        assert 'gRPC bidirectional streaming completed' in caplog.text
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_wrap_stream_stream_error(self, caplog):
        """Test stream-stream wrapper logs errors."""
        from src.interceptors.logging_interceptor import LoggingInterceptor

        interceptor = LoggingInterceptor()

        mock_handler = MagicMock()
        mock_handler.request_deserializer = None
        mock_handler.response_serializer = None

        async def error_bidir_stream(*args, **kwargs):
            yield 'response1'
            raise ValueError('bidir stream error')

        mock_handler.stream_stream = error_bidir_stream

        with caplog.at_level(logging.ERROR):
            wrapped = interceptor._wrap_stream_stream(mock_handler, '/test.Method', 0.0)

            async def request_iterator():
                yield 'request1'

            responses = []
            with pytest.raises(ValueError, match='bidir stream error'):
                async for item in wrapped.stream_stream(request_iterator(), MagicMock()):
                    responses.append(item)

        assert 'gRPC bidirectional streaming failed' in caplog.text
        assert responses == ['response1']

    @pytest.mark.asyncio
    async def test_wrap_unary_unary_error(self, caplog):
        """Test unary-unary wrapper logs errors."""
        from src.interceptors.logging_interceptor import LoggingInterceptor

        interceptor = LoggingInterceptor()

        mock_handler = MagicMock()
        mock_handler.unary_unary = AsyncMock(side_effect=ValueError('Test error'))
        mock_handler.request_deserializer = None
        mock_handler.response_serializer = None

        with caplog.at_level(logging.ERROR):
            wrapped = interceptor._wrap_unary_unary(mock_handler, '/test.Method', 0.0)

            with pytest.raises(ValueError):
                await wrapped.unary_unary(MagicMock(), MagicMock())

        assert 'gRPC request failed' in caplog.text
