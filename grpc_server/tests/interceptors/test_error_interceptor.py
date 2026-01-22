"""Tests for ErrorInterceptor."""

from unittest.mock import AsyncMock, MagicMock

import grpc
import pytest


class TestErrorTranslation:
    """Tests for error translation."""

    @pytest.mark.asyncio
    async def test_translate_exception_node_not_found(self):
        """Test NodeNotFoundError translation."""
        from graphiti_core.errors import NodeNotFoundError

        from src.interceptors.error_interceptor import ErrorInterceptor

        interceptor = ErrorInterceptor()
        error = NodeNotFoundError('test-uuid')

        status_code, message = interceptor._translate_exception(error)

        assert status_code == grpc.StatusCode.NOT_FOUND
        assert 'Node not found' in message

    @pytest.mark.asyncio
    async def test_translate_exception_edge_not_found(self):
        """Test EdgeNotFoundError translation."""
        from graphiti_core.errors import EdgeNotFoundError

        from src.interceptors.error_interceptor import ErrorInterceptor

        interceptor = ErrorInterceptor()
        error = EdgeNotFoundError('test-uuid')

        status_code, message = interceptor._translate_exception(error)

        assert status_code == grpc.StatusCode.NOT_FOUND
        assert 'Edge not found' in message

    @pytest.mark.asyncio
    async def test_translate_exception_value_error(self):
        """Test ValueError translation."""
        from src.interceptors.error_interceptor import ErrorInterceptor

        interceptor = ErrorInterceptor()
        error = ValueError('Invalid argument')

        status_code, message = interceptor._translate_exception(error)

        assert status_code == grpc.StatusCode.INVALID_ARGUMENT
        assert 'Invalid argument' in message

    @pytest.mark.asyncio
    async def test_translate_exception_permission_error(self):
        """Test PermissionError translation."""
        from src.interceptors.error_interceptor import ErrorInterceptor

        interceptor = ErrorInterceptor()
        error = PermissionError('Access denied')

        status_code, message = interceptor._translate_exception(error)

        assert status_code == grpc.StatusCode.PERMISSION_DENIED

    @pytest.mark.asyncio
    async def test_translate_exception_not_implemented(self):
        """Test NotImplementedError translation."""
        from src.interceptors.error_interceptor import ErrorInterceptor

        interceptor = ErrorInterceptor()
        error = NotImplementedError('Not implemented')

        status_code, message = interceptor._translate_exception(error)

        assert status_code == grpc.StatusCode.UNIMPLEMENTED

    @pytest.mark.asyncio
    async def test_translate_exception_timeout(self):
        """Test TimeoutError translation."""
        from src.interceptors.error_interceptor import ErrorInterceptor

        interceptor = ErrorInterceptor()
        error = TimeoutError('Deadline exceeded')

        status_code, message = interceptor._translate_exception(error)

        assert status_code == grpc.StatusCode.DEADLINE_EXCEEDED

    @pytest.mark.asyncio
    async def test_translate_exception_generic(self):
        """Test generic exception translation."""
        from src.interceptors.error_interceptor import ErrorInterceptor

        interceptor = ErrorInterceptor()
        error = RuntimeError('Unknown error')

        status_code, message = interceptor._translate_exception(error)

        assert status_code == grpc.StatusCode.INTERNAL
        assert 'Internal error' in message


class TestErrorInterceptor:
    """Tests for ErrorInterceptor core functionality."""

    @pytest.mark.asyncio
    async def test_intercept_service_returns_none_handler(self):
        """Test interceptor handles None handler gracefully."""
        from src.interceptors.error_interceptor import ErrorInterceptor

        interceptor = ErrorInterceptor()

        async def continuation(handler_call_details):
            return None

        handler_call_details = MagicMock()

        result = await interceptor.intercept_service(continuation, handler_call_details)
        assert result is None


class TestErrorInterceptorWrappers:
    """Tests for ErrorInterceptor wrapper methods."""

    @pytest.mark.asyncio
    async def test_wrap_unary_unary_success(self, create_mock_handler):
        """Test unary-unary wrapper passes through on success."""
        from src.interceptors.error_interceptor import ErrorInterceptor

        interceptor = ErrorInterceptor()
        mock_handler = create_mock_handler('unary_unary')

        wrapped = interceptor._wrap_unary_unary(mock_handler)
        result = await wrapped.unary_unary(MagicMock(), MagicMock())

        assert result == 'response'

    @pytest.mark.asyncio
    async def test_wrap_unary_unary_grpc_error(self):
        """Test unary-unary wrapper re-raises gRPC errors."""
        from src.interceptors.error_interceptor import ErrorInterceptor

        interceptor = ErrorInterceptor()

        mock_handler = MagicMock()
        mock_handler.unary_unary = AsyncMock(side_effect=grpc.RpcError())
        mock_handler.request_deserializer = None
        mock_handler.response_serializer = None

        wrapped = interceptor._wrap_unary_unary(mock_handler)

        with pytest.raises(grpc.RpcError):
            await wrapped.unary_unary(MagicMock(), MagicMock())

    @pytest.mark.asyncio
    async def test_wrap_unary_unary_translates_error(self):
        """Test unary-unary wrapper translates errors."""
        from src.interceptors.error_interceptor import ErrorInterceptor

        interceptor = ErrorInterceptor()

        mock_handler = MagicMock()
        mock_handler.unary_unary = AsyncMock(side_effect=ValueError('Test error'))
        mock_handler.request_deserializer = None
        mock_handler.response_serializer = None

        mock_context = MagicMock()
        mock_context.abort = AsyncMock()

        wrapped = interceptor._wrap_unary_unary(mock_handler)
        await wrapped.unary_unary(MagicMock(), mock_context)

        mock_context.abort.assert_called_once()
        call_args = mock_context.abort.call_args
        assert call_args[0][0] == grpc.StatusCode.INVALID_ARGUMENT

    @pytest.mark.asyncio
    async def test_wrap_unary_stream_error(self):
        """Test unary-stream wrapper handles errors."""
        from src.interceptors.error_interceptor import ErrorInterceptor

        interceptor = ErrorInterceptor()

        mock_handler = MagicMock()

        async def failing_stream(*args, **kwargs):
            yield 'first'
            raise ValueError('Stream error')

        mock_handler.unary_stream = failing_stream
        mock_handler.request_deserializer = None
        mock_handler.response_serializer = None

        mock_context = MagicMock()
        mock_context.abort = AsyncMock()

        wrapped = interceptor._wrap_unary_stream(mock_handler)

        results = []
        async for item in wrapped.unary_stream(MagicMock(), mock_context):
            results.append(item)

        assert len(results) == 1
        mock_context.abort.assert_called_once()

    @pytest.mark.asyncio
    async def test_wrap_stream_unary_error(self):
        """Test stream-unary wrapper handles errors."""
        from src.interceptors.error_interceptor import ErrorInterceptor

        interceptor = ErrorInterceptor()

        mock_handler = MagicMock()
        mock_handler.stream_unary = AsyncMock(side_effect=ValueError('Test error'))
        mock_handler.request_deserializer = None
        mock_handler.response_serializer = None

        mock_context = MagicMock()
        mock_context.abort = AsyncMock()

        wrapped = interceptor._wrap_stream_unary(mock_handler)

        async def request_iterator():
            yield 'request1'

        await wrapped.stream_unary(request_iterator(), mock_context)

        mock_context.abort.assert_called_once()

    @pytest.mark.asyncio
    async def test_wrap_stream_stream_error(self):
        """Test stream-stream wrapper handles errors."""
        from src.interceptors.error_interceptor import ErrorInterceptor

        interceptor = ErrorInterceptor()

        mock_handler = MagicMock()

        async def failing_bidir(*args, **kwargs):
            yield 'first'
            raise ValueError('Bidir error')

        mock_handler.stream_stream = failing_bidir
        mock_handler.request_deserializer = None
        mock_handler.response_serializer = None

        mock_context = MagicMock()
        mock_context.abort = AsyncMock()

        wrapped = interceptor._wrap_stream_stream(mock_handler)

        async def request_iterator():
            yield 'request1'

        results = []
        async for item in wrapped.stream_stream(request_iterator(), mock_context):
            results.append(item)

        mock_context.abort.assert_called_once()


class TestErrorInterceptorEdgeCases:
    """Tests for ErrorInterceptor edge cases and full coverage."""

    @pytest.mark.asyncio
    async def test_intercept_service_unknown_handler_type(self, create_mock_handler):
        """Test interceptor returns handler as-is when no handler type is recognized."""
        from src.interceptors.error_interceptor import ErrorInterceptor

        interceptor = ErrorInterceptor()

        # Create a handler with all handler types set to None/False
        mock_handler = MagicMock()
        mock_handler.unary_unary = None
        mock_handler.unary_stream = None
        mock_handler.stream_unary = None
        mock_handler.stream_stream = None

        async def continuation(handler_call_details):
            return mock_handler

        handler_call_details = MagicMock()

        result = await interceptor.intercept_service(continuation, handler_call_details)

        # Should return the handler as-is without wrapping
        assert result == mock_handler

    @pytest.mark.asyncio
    async def test_intercept_service_wraps_unary_unary_handler(self, create_mock_handler):
        """Test interceptor wraps unary_unary handler type."""
        from src.interceptors.error_interceptor import ErrorInterceptor

        interceptor = ErrorInterceptor()
        mock_handler = create_mock_handler('unary_unary')

        async def continuation(handler_call_details):
            return mock_handler

        handler_call_details = MagicMock()

        result = await interceptor.intercept_service(continuation, handler_call_details)

        # Should return a wrapped handler with unary_unary method
        assert result is not None
        assert hasattr(result, 'unary_unary')
        assert result != mock_handler

    @pytest.mark.asyncio
    async def test_intercept_service_wraps_unary_stream_handler(self, create_mock_handler):
        """Test interceptor wraps unary_stream handler type."""
        from src.interceptors.error_interceptor import ErrorInterceptor

        interceptor = ErrorInterceptor()
        mock_handler = create_mock_handler('unary_stream')

        async def continuation(handler_call_details):
            return mock_handler

        handler_call_details = MagicMock()

        result = await interceptor.intercept_service(continuation, handler_call_details)

        # Should return a wrapped handler with unary_stream method
        assert result is not None
        assert hasattr(result, 'unary_stream')
        assert result != mock_handler

    @pytest.mark.asyncio
    async def test_intercept_service_wraps_stream_unary_handler(self, create_mock_handler):
        """Test interceptor wraps stream_unary handler type."""
        from src.interceptors.error_interceptor import ErrorInterceptor

        interceptor = ErrorInterceptor()
        mock_handler = create_mock_handler('stream_unary')

        async def continuation(handler_call_details):
            return mock_handler

        handler_call_details = MagicMock()

        result = await interceptor.intercept_service(continuation, handler_call_details)

        # Should return a wrapped handler with stream_unary method
        assert result is not None
        assert hasattr(result, 'stream_unary')
        assert result != mock_handler

    @pytest.mark.asyncio
    async def test_intercept_service_wraps_stream_stream_handler(self, create_mock_handler):
        """Test interceptor wraps stream_stream handler type."""
        from src.interceptors.error_interceptor import ErrorInterceptor

        interceptor = ErrorInterceptor()
        mock_handler = create_mock_handler('stream_stream')

        async def continuation(handler_call_details):
            return mock_handler

        handler_call_details = MagicMock()

        result = await interceptor.intercept_service(continuation, handler_call_details)

        # Should return a wrapped handler with stream_stream method
        assert result is not None
        assert hasattr(result, 'stream_stream')
        assert result != mock_handler

    @pytest.mark.asyncio
    async def test_wrap_unary_stream_grpc_error(self):
        """Test unary-stream wrapper re-raises gRPC errors."""
        from src.interceptors.error_interceptor import ErrorInterceptor

        interceptor = ErrorInterceptor()

        mock_handler = MagicMock()

        async def failing_grpc_stream(*args, **kwargs):
            yield 'first'
            raise grpc.RpcError()

        mock_handler.unary_stream = failing_grpc_stream
        mock_handler.request_deserializer = None
        mock_handler.response_serializer = None

        mock_context = MagicMock()
        mock_context.abort = AsyncMock()

        wrapped = interceptor._wrap_unary_stream(mock_handler)

        results = []
        with pytest.raises(grpc.RpcError):
            async for item in wrapped.unary_stream(MagicMock(), mock_context):
                results.append(item)

        # abort should not be called for grpc.RpcError
        mock_context.abort.assert_not_called()

    @pytest.mark.asyncio
    async def test_wrap_stream_unary_grpc_error(self):
        """Test stream-unary wrapper re-raises gRPC errors."""
        from src.interceptors.error_interceptor import ErrorInterceptor

        interceptor = ErrorInterceptor()

        mock_handler = MagicMock()
        mock_handler.stream_unary = AsyncMock(side_effect=grpc.RpcError())
        mock_handler.request_deserializer = None
        mock_handler.response_serializer = None

        mock_context = MagicMock()
        mock_context.abort = AsyncMock()

        wrapped = interceptor._wrap_stream_unary(mock_handler)

        async def request_iterator():
            yield 'request1'

        with pytest.raises(grpc.RpcError):
            await wrapped.stream_unary(request_iterator(), mock_context)

        # abort should not be called for grpc.RpcError
        mock_context.abort.assert_not_called()

    @pytest.mark.asyncio
    async def test_wrap_stream_stream_grpc_error(self):
        """Test stream-stream wrapper re-raises gRPC errors."""
        from src.interceptors.error_interceptor import ErrorInterceptor

        interceptor = ErrorInterceptor()

        mock_handler = MagicMock()

        async def failing_grpc_bidir(*args, **kwargs):
            yield 'first'
            raise grpc.RpcError()

        mock_handler.stream_stream = failing_grpc_bidir
        mock_handler.request_deserializer = None
        mock_handler.response_serializer = None

        mock_context = MagicMock()
        mock_context.abort = AsyncMock()

        wrapped = interceptor._wrap_stream_stream(mock_handler)

        async def request_iterator():
            yield 'request1'

        results = []
        with pytest.raises(grpc.RpcError):
            async for item in wrapped.stream_stream(request_iterator(), mock_context):
                results.append(item)

        # abort should not be called for grpc.RpcError
        mock_context.abort.assert_not_called()

    @pytest.mark.asyncio
    async def test_wrap_unary_stream_success(self, create_mock_handler):
        """Test unary-stream wrapper passes through on success."""
        from src.interceptors.error_interceptor import ErrorInterceptor

        interceptor = ErrorInterceptor()
        mock_handler = create_mock_handler('unary_stream')

        wrapped = interceptor._wrap_unary_stream(mock_handler)

        results = []
        async for item in wrapped.unary_stream(MagicMock(), MagicMock()):
            results.append(item)

        assert len(results) == 2
        assert results == ['response1', 'response2']

    @pytest.mark.asyncio
    async def test_wrap_stream_unary_success(self, create_mock_handler):
        """Test stream-unary wrapper passes through on success."""
        from src.interceptors.error_interceptor import ErrorInterceptor

        interceptor = ErrorInterceptor()
        mock_handler = create_mock_handler('stream_unary')

        wrapped = interceptor._wrap_stream_unary(mock_handler)

        async def request_iterator():
            yield 'request1'

        result = await wrapped.stream_unary(request_iterator(), MagicMock())

        assert result == 'response'

    @pytest.mark.asyncio
    async def test_wrap_stream_stream_success(self, create_mock_handler):
        """Test stream-stream wrapper passes through on success."""
        from src.interceptors.error_interceptor import ErrorInterceptor

        interceptor = ErrorInterceptor()
        mock_handler = create_mock_handler('stream_stream')

        wrapped = interceptor._wrap_stream_stream(mock_handler)

        async def request_iterator():
            yield 'request1'

        results = []
        async for item in wrapped.stream_stream(request_iterator(), MagicMock()):
            results.append(item)

        assert len(results) == 2
        assert results == ['response1', 'response2']

    @pytest.mark.asyncio
    async def test_wrap_unary_stream_all_error_types(self):
        """Test unary-stream wrapper translates various error types correctly."""
        from graphiti_core.errors import NodeNotFoundError

        from src.interceptors.error_interceptor import ErrorInterceptor

        interceptor = ErrorInterceptor()

        # Test with NodeNotFoundError
        mock_handler = MagicMock()

        async def failing_stream(*args, **kwargs):
            yield 'first'
            raise NodeNotFoundError('test-uuid')

        mock_handler.unary_stream = failing_stream
        mock_handler.request_deserializer = None
        mock_handler.response_serializer = None

        mock_context = MagicMock()
        mock_context.abort = AsyncMock()

        wrapped = interceptor._wrap_unary_stream(mock_handler)

        results = []
        async for item in wrapped.unary_stream(MagicMock(), mock_context):
            results.append(item)

        assert len(results) == 1
        mock_context.abort.assert_called_once()
        call_args = mock_context.abort.call_args
        assert call_args[0][0] == grpc.StatusCode.NOT_FOUND

    @pytest.mark.asyncio
    async def test_wrap_stream_unary_all_error_types(self):
        """Test stream-unary wrapper translates various error types correctly."""
        from src.interceptors.error_interceptor import ErrorInterceptor

        interceptor = ErrorInterceptor()

        # Test with NotImplementedError
        mock_handler = MagicMock()
        mock_handler.stream_unary = AsyncMock(side_effect=NotImplementedError('Not supported'))
        mock_handler.request_deserializer = None
        mock_handler.response_serializer = None

        mock_context = MagicMock()
        mock_context.abort = AsyncMock()

        wrapped = interceptor._wrap_stream_unary(mock_handler)

        async def request_iterator():
            yield 'request1'

        await wrapped.stream_unary(request_iterator(), mock_context)

        mock_context.abort.assert_called_once()
        call_args = mock_context.abort.call_args
        assert call_args[0][0] == grpc.StatusCode.UNIMPLEMENTED

    @pytest.mark.asyncio
    async def test_wrap_stream_stream_all_error_types(self):
        """Test stream-stream wrapper translates various error types correctly."""
        from src.interceptors.error_interceptor import ErrorInterceptor

        interceptor = ErrorInterceptor()

        # Test with TimeoutError
        mock_handler = MagicMock()

        async def failing_bidir(*args, **kwargs):
            yield 'first'
            raise TimeoutError('Request timeout')

        mock_handler.stream_stream = failing_bidir
        mock_handler.request_deserializer = None
        mock_handler.response_serializer = None

        mock_context = MagicMock()
        mock_context.abort = AsyncMock()

        wrapped = interceptor._wrap_stream_stream(mock_handler)

        async def request_iterator():
            yield 'request1'

        results = []
        async for item in wrapped.stream_stream(request_iterator(), mock_context):
            results.append(item)

        assert len(results) == 1
        mock_context.abort.assert_called_once()
        call_args = mock_context.abort.call_args
        assert call_args[0][0] == grpc.StatusCode.DEADLINE_EXCEEDED
