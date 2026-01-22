"""OpenTelemetry tracing interceptor for gRPC requests."""

import logging
from typing import TYPE_CHECKING, Any, Callable

import grpc

logger = logging.getLogger(__name__)

# Try to import OpenTelemetry
try:
    from opentelemetry import trace
    from opentelemetry.trace import SpanKind, Status, StatusCode, Tracer

    HAS_OTEL = True
except ImportError:
    HAS_OTEL = False
    logger.info('OpenTelemetry not available, tracing disabled')

    if TYPE_CHECKING:
        from opentelemetry.trace import SpanKind, Status, StatusCode, Tracer


class TracingInterceptor(grpc.aio.ServerInterceptor):
    """Interceptor that adds OpenTelemetry tracing to gRPC requests."""

    _tracer: 'Tracer | None'

    def __init__(self, service_name: str = 'graphiti-grpc-server'):
        """Initialize the tracing interceptor.

        Args:
            service_name: The name of the service for tracing.
        """
        self._service_name = service_name
        if HAS_OTEL:
            self._tracer = trace.get_tracer(service_name)
        else:
            self._tracer = None

    async def intercept_service(
        self,
        continuation: Callable[[grpc.HandlerCallDetails], Any],
        handler_call_details: grpc.HandlerCallDetails,
    ) -> Any:
        """Intercept and trace service calls."""
        if not HAS_OTEL or self._tracer is None:
            return await continuation(handler_call_details)

        handler = await continuation(handler_call_details)

        if handler is None:
            return handler

        method = handler_call_details.method

        # Wrap handlers with tracing
        if handler.unary_unary:
            return self._wrap_unary_unary(handler, method)
        elif handler.unary_stream:
            return self._wrap_unary_stream(handler, method)
        elif handler.stream_unary:
            return self._wrap_stream_unary(handler, method)
        elif handler.stream_stream:
            return self._wrap_stream_stream(handler, method)
        else:
            return handler

    def _wrap_unary_unary(self, handler, method: str):
        """Wrap a unary-unary handler with tracing."""
        assert self._tracer is not None  # Checked in intercept_service
        tracer = self._tracer
        original_handler = handler.unary_unary

        async def wrapped_handler(request, context):
            with tracer.start_as_current_span(
                method,
                kind=SpanKind.SERVER,
            ) as span:
                span.set_attribute('rpc.system', 'grpc')
                span.set_attribute('rpc.method', method)
                span.set_attribute('rpc.service', self._service_name)

                try:
                    response = await original_handler(request, context)
                    span.set_status(Status(StatusCode.OK))
                    return response
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        return grpc.unary_unary_rpc_method_handler(
            wrapped_handler,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )

    def _wrap_unary_stream(self, handler, method: str):
        """Wrap a unary-stream handler with tracing."""
        assert self._tracer is not None  # Checked in intercept_service
        tracer = self._tracer
        original_handler = handler.unary_stream

        async def wrapped_handler(request, context):
            with tracer.start_as_current_span(
                method,
                kind=SpanKind.SERVER,
            ) as span:
                span.set_attribute('rpc.system', 'grpc')
                span.set_attribute('rpc.method', method)
                span.set_attribute('rpc.service', self._service_name)

                try:
                    async for response in original_handler(request, context):
                        yield response
                    span.set_status(Status(StatusCode.OK))
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        return grpc.unary_stream_rpc_method_handler(
            wrapped_handler,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )

    def _wrap_stream_unary(self, handler, method: str):
        """Wrap a stream-unary handler with tracing."""
        assert self._tracer is not None  # Checked in intercept_service
        tracer = self._tracer
        original_handler = handler.stream_unary

        async def wrapped_handler(request_iterator, context):
            with tracer.start_as_current_span(
                method,
                kind=SpanKind.SERVER,
            ) as span:
                span.set_attribute('rpc.system', 'grpc')
                span.set_attribute('rpc.method', method)
                span.set_attribute('rpc.service', self._service_name)

                try:
                    response = await original_handler(request_iterator, context)
                    span.set_status(Status(StatusCode.OK))
                    return response
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        return grpc.stream_unary_rpc_method_handler(
            wrapped_handler,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )

    def _wrap_stream_stream(self, handler, method: str):
        """Wrap a stream-stream handler with tracing."""
        assert self._tracer is not None  # Checked in intercept_service
        tracer = self._tracer
        original_handler = handler.stream_stream

        async def wrapped_handler(request_iterator, context):
            with tracer.start_as_current_span(
                method,
                kind=SpanKind.SERVER,
            ) as span:
                span.set_attribute('rpc.system', 'grpc')
                span.set_attribute('rpc.method', method)
                span.set_attribute('rpc.service', self._service_name)

                try:
                    async for response in original_handler(request_iterator, context):
                        yield response
                    span.set_status(Status(StatusCode.OK))
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        return grpc.stream_stream_rpc_method_handler(
            wrapped_handler,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )
