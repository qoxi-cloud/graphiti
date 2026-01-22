"""Shared fixtures for interceptor tests."""

from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def create_mock_handler():
    """Factory fixture to create mock handlers for testing."""

    def _create_mock_handler(handler_type='unary_unary'):
        mock_handler = MagicMock()
        mock_handler.unary_unary = None
        mock_handler.unary_stream = None
        mock_handler.stream_unary = None
        mock_handler.stream_stream = None
        mock_handler.request_deserializer = None
        mock_handler.response_serializer = None

        if handler_type == 'unary_unary':
            mock_handler.unary_unary = AsyncMock(return_value='response')
        elif handler_type == 'unary_stream':

            async def stream_gen(*args, **kwargs):
                yield 'response1'
                yield 'response2'

            mock_handler.unary_stream = stream_gen
        elif handler_type == 'stream_unary':
            mock_handler.stream_unary = AsyncMock(return_value='response')
        elif handler_type == 'stream_stream':

            async def bidir_gen(*args, **kwargs):
                yield 'response1'
                yield 'response2'

            mock_handler.stream_stream = bidir_gen

        return mock_handler

    return _create_mock_handler
