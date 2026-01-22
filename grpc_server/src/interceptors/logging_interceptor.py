"""Logging interceptor for gRPC requests."""

import logging
import time
from typing import Any, Callable

import grpc

logger = logging.getLogger(__name__)


class LoggingInterceptor(grpc.aio.ServerInterceptor):
    """Interceptor that logs gRPC requests and responses."""

    async def intercept_service(
        self,
        continuation: Callable[[grpc.HandlerCallDetails], Any],
        handler_call_details: grpc.HandlerCallDetails,
    ) -> Any:
        """Intercept and log service calls."""
        method = handler_call_details.method
        start_time = time.time()

        # Log request start
        logger.info(f'gRPC request started: {method}')

        try:
            # Get the handler
            handler = await continuation(handler_call_details)

            if handler is None:
                logger.warning(f'No handler found for method: {method}')
                return handler

            # Wrap the handler to log response
            if handler.unary_unary:
                return self._wrap_unary_unary(handler, method, start_time)
            elif handler.unary_stream:
                return self._wrap_unary_stream(handler, method, start_time)
            elif handler.stream_unary:
                return self._wrap_stream_unary(handler, method, start_time)
            elif handler.stream_stream:
                return self._wrap_stream_stream(handler, method, start_time)
            else:
                return handler

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.error(f'gRPC request failed: {method} - {e} ({duration:.2f}ms)')
            raise

    def _wrap_unary_unary(self, handler, method: str, start_time: float):
        """Wrap a unary-unary handler."""
        original_handler = handler.unary_unary

        async def wrapped_handler(request, context):
            try:
                response = await original_handler(request, context)
                duration = (time.time() - start_time) * 1000
                logger.info(f'gRPC request completed: {method} ({duration:.2f}ms)')
                return response
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                logger.error(f'gRPC request failed: {method} - {e} ({duration:.2f}ms)')
                raise

        return grpc.unary_unary_rpc_method_handler(
            wrapped_handler,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )

    def _wrap_unary_stream(self, handler, method: str, start_time: float):
        """Wrap a unary-stream handler."""
        original_handler = handler.unary_stream

        async def wrapped_handler(request, context):
            try:
                async for response in original_handler(request, context):
                    yield response
                duration = (time.time() - start_time) * 1000
                logger.info(f'gRPC streaming completed: {method} ({duration:.2f}ms)')
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                logger.error(f'gRPC streaming failed: {method} - {e} ({duration:.2f}ms)')
                raise

        return grpc.unary_stream_rpc_method_handler(
            wrapped_handler,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )

    def _wrap_stream_unary(self, handler, method: str, start_time: float):
        """Wrap a stream-unary handler."""
        original_handler = handler.stream_unary

        async def wrapped_handler(request_iterator, context):
            try:
                response = await original_handler(request_iterator, context)
                duration = (time.time() - start_time) * 1000
                logger.info(f'gRPC request completed: {method} ({duration:.2f}ms)')
                return response
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                logger.error(f'gRPC request failed: {method} - {e} ({duration:.2f}ms)')
                raise

        return grpc.stream_unary_rpc_method_handler(
            wrapped_handler,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )

    def _wrap_stream_stream(self, handler, method: str, start_time: float):
        """Wrap a stream-stream handler."""
        original_handler = handler.stream_stream

        async def wrapped_handler(request_iterator, context):
            try:
                async for response in original_handler(request_iterator, context):
                    yield response
                duration = (time.time() - start_time) * 1000
                logger.info(f'gRPC bidirectional streaming completed: {method} ({duration:.2f}ms)')
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                logger.error(
                    f'gRPC bidirectional streaming failed: {method} - {e} ({duration:.2f}ms)'
                )
                raise

        return grpc.stream_stream_rpc_method_handler(
            wrapped_handler,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )
