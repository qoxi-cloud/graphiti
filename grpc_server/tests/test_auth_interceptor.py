"""Tests for authentication interceptor."""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.interceptors.auth_interceptor import AuthConfig, AuthInterceptor


class TestAuthConfig:
    """Tests for AuthConfig class."""

    def test_auth_config_defaults(self):
        """Test AuthConfig with default values."""
        config = AuthConfig()

        assert config.enabled is True
        assert config.api_keys == set()
        assert config.jwt_secret is None
        assert config.jwt_algorithm == 'HS256'
        assert config.skip_health_check is True

    def test_auth_config_with_api_keys(self):
        """Test AuthConfig with API keys."""
        api_keys = {'key1', 'key2', 'key3'}
        config = AuthConfig(api_keys=api_keys)

        assert config.enabled is True
        assert config.api_keys == api_keys

    def test_auth_config_with_jwt_secret(self):
        """Test AuthConfig with JWT secret."""
        config = AuthConfig(jwt_secret='my-secret-key')

        assert config.enabled is True
        assert config.jwt_secret == 'my-secret-key'
        assert config.jwt_algorithm == 'HS256'

    def test_auth_config_disabled(self):
        """Test AuthConfig with auth disabled."""
        config = AuthConfig(enabled=False)

        assert config.enabled is False

    def test_auth_config_custom_jwt_algorithm(self):
        """Test AuthConfig with custom JWT algorithm."""
        config = AuthConfig(jwt_secret='secret', jwt_algorithm='RS256')

        assert config.jwt_algorithm == 'RS256'

    def test_auth_config_warning_no_credentials(self, caplog):
        """Test AuthConfig logs warning when enabled but no credentials configured."""
        AuthConfig(enabled=True, api_keys=set(), jwt_secret=None)

        assert 'Authentication enabled but no API keys or JWT secret configured' in caplog.text


class TestAuthInterceptor:
    """Tests for AuthInterceptor class."""

    @pytest.fixture
    def mock_continuation(self):
        """Create a mock continuation function."""
        mock = AsyncMock()
        mock_handler = MagicMock()
        mock_handler.unary_unary = AsyncMock()
        mock.return_value = mock_handler
        return mock

    @pytest.fixture
    def mock_handler_details(self):
        """Create mock handler call details."""
        details = MagicMock()
        details.method = '/graphiti.v1.IngestService/AddEpisode'
        details.invocation_metadata = []
        return details

    @pytest.mark.asyncio
    async def test_auth_disabled(self, mock_continuation, mock_handler_details):
        """Test that authentication is bypassed when disabled."""
        config = AuthConfig(enabled=False)
        interceptor = AuthInterceptor(config)

        result = await interceptor.intercept_service(mock_continuation, mock_handler_details)

        mock_continuation.assert_called_once_with(mock_handler_details)
        assert result is not None

    @pytest.mark.asyncio
    async def test_health_check_skip_auth(self, mock_continuation, mock_handler_details):
        """Test that health check endpoints skip authentication."""
        config = AuthConfig(enabled=True, skip_health_check=True, api_keys={'test-key'})
        interceptor = AuthInterceptor(config)

        mock_handler_details.method = '/grpc.health.v1.Health/Check'

        result = await interceptor.intercept_service(mock_continuation, mock_handler_details)

        mock_continuation.assert_called_once_with(mock_handler_details)
        assert result is not None

    @pytest.mark.asyncio
    async def test_health_check_watch_skip_auth(self, mock_continuation, mock_handler_details):
        """Test that health check watch endpoint skips authentication."""
        config = AuthConfig(enabled=True, skip_health_check=True, api_keys={'test-key'})
        interceptor = AuthInterceptor(config)

        mock_handler_details.method = '/grpc.health.v1.Health/Watch'

        result = await interceptor.intercept_service(mock_continuation, mock_handler_details)

        mock_continuation.assert_called_once_with(mock_handler_details)
        assert result is not None

    @pytest.mark.asyncio
    async def test_valid_api_key(self, mock_continuation, mock_handler_details):
        """Test successful authentication with valid API key."""
        api_key = 'valid-api-key-123'
        config = AuthConfig(enabled=True, api_keys={api_key})
        interceptor = AuthInterceptor(config)

        mock_handler_details.invocation_metadata = [('x-api-key', api_key)]

        result = await interceptor.intercept_service(mock_continuation, mock_handler_details)

        mock_continuation.assert_called_once_with(mock_handler_details)
        assert result is not None

    @pytest.mark.asyncio
    async def test_invalid_api_key(self, mock_continuation, mock_handler_details):
        """Test authentication failure with invalid API key."""
        config = AuthConfig(enabled=True, api_keys={'valid-key'})
        interceptor = AuthInterceptor(config)

        mock_handler_details.invocation_metadata = [('x-api-key', 'invalid-key')]

        result = await interceptor.intercept_service(mock_continuation, mock_handler_details)

        # Should not call continuation with invalid key
        mock_continuation.assert_not_called()
        assert result is not None

    @pytest.mark.asyncio
    async def test_empty_api_key(self, mock_continuation, mock_handler_details):
        """Test authentication failure with empty API key."""
        config = AuthConfig(enabled=True, api_keys={'valid-key'})
        interceptor = AuthInterceptor(config)

        mock_handler_details.invocation_metadata = [('x-api-key', '')]

        result = await interceptor.intercept_service(mock_continuation, mock_handler_details)

        mock_continuation.assert_not_called()
        assert result is not None

    @pytest.mark.asyncio
    async def test_excessively_long_api_key(self, mock_continuation, mock_handler_details):
        """Test authentication failure with excessively long API key (DoS prevention)."""
        config = AuthConfig(enabled=True, api_keys={'valid-key'})
        interceptor = AuthInterceptor(config)

        long_key = 'x' * 1000  # 1000 characters
        mock_handler_details.invocation_metadata = [('x-api-key', long_key)]

        result = await interceptor.intercept_service(mock_continuation, mock_handler_details)

        mock_continuation.assert_not_called()
        assert result is not None

    @pytest.mark.asyncio
    async def test_valid_jwt_token(self, mock_continuation, mock_handler_details):
        """Test successful authentication with valid JWT token."""
        import jwt

        secret = 'my-jwt-secret'
        config = AuthConfig(enabled=True, jwt_secret=secret)
        interceptor = AuthInterceptor(config)

        # Create a valid JWT token
        payload = {'user_id': '123', 'exp': time.time() + 3600, 'iat': time.time()}
        token = jwt.encode(payload, secret, algorithm='HS256')

        mock_handler_details.invocation_metadata = [('authorization', f'Bearer {token}')]

        result = await interceptor.intercept_service(mock_continuation, mock_handler_details)

        mock_continuation.assert_called_once_with(mock_handler_details)
        assert result is not None

    @pytest.mark.asyncio
    async def test_expired_jwt_token(self, mock_continuation, mock_handler_details):
        """Test authentication failure with expired JWT token."""
        import jwt

        secret = 'my-jwt-secret'
        config = AuthConfig(enabled=True, jwt_secret=secret)
        interceptor = AuthInterceptor(config)

        # Create an expired JWT token
        payload = {'user_id': '123', 'exp': time.time() - 3600, 'iat': time.time() - 7200}
        token = jwt.encode(payload, secret, algorithm='HS256')

        mock_handler_details.invocation_metadata = [('authorization', f'Bearer {token}')]

        result = await interceptor.intercept_service(mock_continuation, mock_handler_details)

        mock_continuation.assert_not_called()
        assert result is not None

    @pytest.mark.asyncio
    async def test_invalid_jwt_token(self, mock_continuation, mock_handler_details):
        """Test authentication failure with invalid JWT token."""
        config = AuthConfig(enabled=True, jwt_secret='my-jwt-secret')
        interceptor = AuthInterceptor(config)

        mock_handler_details.invocation_metadata = [('authorization', 'Bearer invalid-token')]

        result = await interceptor.intercept_service(mock_continuation, mock_handler_details)

        mock_continuation.assert_not_called()
        assert result is not None

    @pytest.mark.asyncio
    async def test_jwt_wrong_secret(self, mock_continuation, mock_handler_details):
        """Test authentication failure with JWT signed with wrong secret."""
        import jwt

        config = AuthConfig(enabled=True, jwt_secret='correct-secret')
        interceptor = AuthInterceptor(config)

        # Create token with wrong secret
        payload = {'user_id': '123', 'exp': time.time() + 3600, 'iat': time.time()}
        token = jwt.encode(payload, 'wrong-secret', algorithm='HS256')

        mock_handler_details.invocation_metadata = [('authorization', f'Bearer {token}')]

        result = await interceptor.intercept_service(mock_continuation, mock_handler_details)

        mock_continuation.assert_not_called()
        assert result is not None

    @pytest.mark.asyncio
    async def test_jwt_missing_required_claims(self, mock_continuation, mock_handler_details):
        """Test authentication failure with JWT missing required claims."""
        import jwt

        secret = 'my-jwt-secret'
        config = AuthConfig(enabled=True, jwt_secret=secret)
        interceptor = AuthInterceptor(config)

        # Create token without exp and iat claims
        payload = {'user_id': '123'}
        token = jwt.encode(payload, secret, algorithm='HS256')

        mock_handler_details.invocation_metadata = [('authorization', f'Bearer {token}')]

        result = await interceptor.intercept_service(mock_continuation, mock_handler_details)

        mock_continuation.assert_not_called()
        assert result is not None

    @pytest.mark.asyncio
    async def test_bearer_token_case_insensitive(self, mock_continuation, mock_handler_details):
        """Test that Bearer prefix is case-insensitive."""
        import jwt

        secret = 'my-jwt-secret'
        config = AuthConfig(enabled=True, jwt_secret=secret)
        interceptor = AuthInterceptor(config)

        payload = {'user_id': '123', 'exp': time.time() + 3600, 'iat': time.time()}
        token = jwt.encode(payload, secret, algorithm='HS256')

        # Use lowercase 'bearer'
        mock_handler_details.invocation_metadata = [('authorization', f'bearer {token}')]

        result = await interceptor.intercept_service(mock_continuation, mock_handler_details)

        mock_continuation.assert_called_once_with(mock_handler_details)
        assert result is not None

    @pytest.mark.asyncio
    async def test_invalid_authorization_header_format(
        self, mock_continuation, mock_handler_details
    ):
        """Test authentication failure with invalid authorization header format."""
        config = AuthConfig(enabled=True, jwt_secret='secret')
        interceptor = AuthInterceptor(config)

        # No 'Bearer ' prefix
        mock_handler_details.invocation_metadata = [('authorization', 'InvalidFormat token123')]

        result = await interceptor.intercept_service(mock_continuation, mock_handler_details)

        mock_continuation.assert_not_called()
        assert result is not None

    @pytest.mark.asyncio
    async def test_no_credentials_provided(self, mock_continuation, mock_handler_details):
        """Test authentication failure when no credentials provided."""
        config = AuthConfig(enabled=True, api_keys={'valid-key'})
        interceptor = AuthInterceptor(config)

        # No authentication metadata
        mock_handler_details.invocation_metadata = []

        result = await interceptor.intercept_service(mock_continuation, mock_handler_details)

        mock_continuation.assert_not_called()
        assert result is not None

    @pytest.mark.asyncio
    async def test_api_key_takes_precedence_over_jwt(self, mock_continuation, mock_handler_details):
        """Test that API key authentication is tried before JWT."""
        api_key = 'valid-api-key'
        config = AuthConfig(enabled=True, api_keys={api_key}, jwt_secret='jwt-secret')
        interceptor = AuthInterceptor(config)

        # Provide both API key and JWT token
        mock_handler_details.invocation_metadata = [
            ('x-api-key', api_key),
            ('authorization', 'Bearer invalid-token'),
        ]

        result = await interceptor.intercept_service(mock_continuation, mock_handler_details)

        # Should succeed with API key, JWT not even validated
        mock_continuation.assert_called_once_with(mock_handler_details)
        assert result is not None

    @pytest.mark.asyncio
    async def test_constant_time_api_key_comparison(self, mock_continuation, mock_handler_details):
        """Test that API key comparison uses constant-time comparison (timing attack prevention)."""
        config = AuthConfig(enabled=True, api_keys={'valid-key-123'})
        interceptor = AuthInterceptor(config)

        # Test with similar keys
        mock_handler_details.invocation_metadata = [('x-api-key', 'valid-key-456')]

        with patch('secrets.compare_digest') as mock_compare:
            mock_compare.return_value = False
            await interceptor.intercept_service(mock_continuation, mock_handler_details)

            # Verify constant-time comparison was used
            mock_compare.assert_called()

    @pytest.mark.asyncio
    async def test_jwt_without_pyjwt_library(self, mock_continuation, mock_handler_details):
        """Test JWT authentication when PyJWT library is not installed."""
        config = AuthConfig(enabled=True, jwt_secret='secret')
        interceptor = AuthInterceptor(config)

        mock_handler_details.invocation_metadata = [('authorization', 'Bearer some-token')]

        # Mock ImportError when trying to import jwt
        with patch.dict('sys.modules', {'jwt': None}):
            result = await interceptor.intercept_service(mock_continuation, mock_handler_details)

            mock_continuation.assert_not_called()
            assert result is not None

    @pytest.mark.asyncio
    async def test_excessively_long_jwt_token(self, mock_continuation, mock_handler_details):
        """Test authentication failure with excessively long JWT token (DoS prevention)."""
        config = AuthConfig(enabled=True, jwt_secret='secret')
        interceptor = AuthInterceptor(config)

        long_token = 'x' * 10000  # 10,000 characters
        mock_handler_details.invocation_metadata = [('authorization', f'Bearer {long_token}')]

        result = await interceptor.intercept_service(mock_continuation, mock_handler_details)

        mock_continuation.assert_not_called()
        assert result is not None

    @pytest.mark.asyncio
    async def test_multiple_api_keys(self, mock_continuation, mock_handler_details):
        """Test authentication with multiple valid API keys."""
        config = AuthConfig(enabled=True, api_keys={'key1', 'key2', 'key3'})
        interceptor = AuthInterceptor(config)

        # Test with each key
        for key in ['key1', 'key2', 'key3']:
            mock_handler_details.invocation_metadata = [('x-api-key', key)]
            result = await interceptor.intercept_service(mock_continuation, mock_handler_details)
            assert result is not None

        # Reset mock
        mock_continuation.reset_mock()

        # Test with invalid key
        mock_handler_details.invocation_metadata = [('x-api-key', 'invalid')]
        result = await interceptor.intercept_service(mock_continuation, mock_handler_details)
        mock_continuation.assert_not_called()

    @pytest.mark.asyncio
    async def test_custom_jwt_algorithm(self, mock_continuation, mock_handler_details):
        """Test JWT authentication with custom algorithm."""
        import jwt

        secret = 'my-secret'
        config = AuthConfig(enabled=True, jwt_secret=secret, jwt_algorithm='HS512')
        interceptor = AuthInterceptor(config)

        # Create token with HS512
        payload = {'user_id': '123', 'exp': time.time() + 3600, 'iat': time.time()}
        token = jwt.encode(payload, secret, algorithm='HS512')

        mock_handler_details.invocation_metadata = [('authorization', f'Bearer {token}')]

        result = await interceptor.intercept_service(mock_continuation, mock_handler_details)

        mock_continuation.assert_called_once_with(mock_handler_details)
        assert result is not None

    def test_create_unauthenticated_handler(self):
        """Test that unauthenticated handler is created correctly."""
        config = AuthConfig(enabled=True, api_keys={'test'})
        interceptor = AuthInterceptor(config)

        handler = interceptor._create_unauthenticated_handler('Test message')

        assert handler is not None
        assert handler.unary_unary is not None
