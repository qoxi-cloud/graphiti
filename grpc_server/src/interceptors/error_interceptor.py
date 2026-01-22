"""Error handling interceptor for gRPC requests."""

import logging
from typing import Any, Callable

import grpc
from graphiti_core.errors import EdgeNotFoundError, NodeNotFoundError

logger = logging.getLogger(__name__)


class ErrorInterceptor(grpc.aio.ServerInterceptor):
    """Interceptor that handles and translates exceptions to gRPC status codes."""

    async def intercept_service(
        self,
        continuation: Callable[[grpc.HandlerCallDetails], Any],
        handler_call_details: grpc.HandlerCallDetails,
    ) -> Any:
        """Intercept and handle errors in service calls."""
        handler = await continuation(handler_call_details)

        if handler is None:
            return handler

        # Wrap handlers to catch and translate exceptions
        if handler.unary_unary:
            return self._wrap_unary_unary(handler)
        elif handler.unary_stream:
            return self._wrap_unary_stream(handler)
        elif handler.stream_unary:
            return self._wrap_stream_unary(handler)
        elif handler.stream_stream:
            return self._wrap_stream_stream(handler)
        else:
            return handler

    def _translate_exception(self, e: Exception) -> tuple[grpc.StatusCode, str]:
        """Translate a Python exception to a gRPC status code and message."""
        if isinstance(e, NodeNotFoundError):
            return grpc.StatusCode.NOT_FOUND, f'Node not found: {e}'
        elif isinstance(e, EdgeNotFoundError):
            return grpc.StatusCode.NOT_FOUND, f'Edge not found: {e}'
        elif isinstance(e, ValueError):
            return grpc.StatusCode.INVALID_ARGUMENT, str(e)
        elif isinstance(e, PermissionError):
            return grpc.StatusCode.PERMISSION_DENIED, str(e)
        elif isinstance(e, NotImplementedError):
            return grpc.StatusCode.UNIMPLEMENTED, str(e)
        elif isinstance(e, TimeoutError):
            return grpc.StatusCode.DEADLINE_EXCEEDED, str(e)
        else:
            return grpc.StatusCode.INTERNAL, f'Internal error: {e}'

    def _wrap_unary_unary(self, handler):
        """Wrap a unary-unary handler with error handling."""
        original_handler = handler.unary_unary

        async def wrapped_handler(request, context):
            try:
                return await original_handler(request, context)
            except grpc.RpcError:
                # Re-raise gRPC errors as-is
                raise
            except Exception as e:
                logger.exception('Unhandled exception in gRPC handler')
                status_code, message = self._translate_exception(e)
                await context.abort(status_code, message)

        return grpc.unary_unary_rpc_method_handler(
            wrapped_handler,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )

    def _wrap_unary_stream(self, handler):
        """Wrap a unary-stream handler with error handling."""
        original_handler = handler.unary_stream

        async def wrapped_handler(request, context):
            try:
                async for response in original_handler(request, context):
                    yield response
            except grpc.RpcError:
                raise
            except Exception as e:
                logger.exception('Unhandled exception in gRPC streaming handler')
                status_code, message = self._translate_exception(e)
                await context.abort(status_code, message)

        return grpc.unary_stream_rpc_method_handler(
            wrapped_handler,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )

    def _wrap_stream_unary(self, handler):
        """Wrap a stream-unary handler with error handling."""
        original_handler = handler.stream_unary

        async def wrapped_handler(request_iterator, context):
            try:
                return await original_handler(request_iterator, context)
            except grpc.RpcError:
                raise
            except Exception as e:
                logger.exception('Unhandled exception in gRPC handler')
                status_code, message = self._translate_exception(e)
                await context.abort(status_code, message)

        return grpc.stream_unary_rpc_method_handler(
            wrapped_handler,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )

    def _wrap_stream_stream(self, handler):
        """Wrap a stream-stream handler with error handling."""
        original_handler = handler.stream_stream

        async def wrapped_handler(request_iterator, context):
            try:
                async for response in original_handler(request_iterator, context):
                    yield response
            except grpc.RpcError:
                raise
            except Exception as e:
                logger.exception('Unhandled exception in gRPC bidirectional streaming handler')
                status_code, message = self._translate_exception(e)
                await context.abort(status_code, message)

        return grpc.stream_stream_rpc_method_handler(
            wrapped_handler,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )
