"""Authentication interceptor for gRPC requests.

Supports API key and Bearer token authentication with configurable security options.
"""

import logging
import secrets
from typing import Any, Callable

import grpc

logger = logging.getLogger(__name__)


class AuthConfig:
    """Configuration for authentication interceptor."""

    def __init__(
        self,
        enabled: bool = True,
        api_keys: set[str] | None = None,
        jwt_secret: str | None = None,
        jwt_algorithm: str = 'HS256',
        skip_health_check: bool = True,
    ):
        """Initialize authentication configuration.

        Args:
            enabled: Whether authentication is enabled
            api_keys: Set of valid API keys (hashed with constant-time comparison)
            jwt_secret: Secret key for JWT verification
            jwt_algorithm: Algorithm for JWT verification (default: HS256)
            skip_health_check: Whether to skip auth for health check endpoints
        """
        self.enabled = enabled
        self.api_keys = api_keys or set()
        self.jwt_secret = jwt_secret
        self.jwt_algorithm = jwt_algorithm
        self.skip_health_check = skip_health_check

        # Validate configuration
        if self.enabled and not self.api_keys and not self.jwt_secret:
            logger.warning(
                'Authentication enabled but no API keys or JWT secret configured. '
                'All requests will be rejected.'
            )


class AuthInterceptor(grpc.aio.ServerInterceptor):
    """Interceptor that validates authentication credentials.

    Supports two authentication methods:
    1. API Key authentication via 'x-api-key' metadata header
    2. Bearer token (JWT) authentication via 'authorization' metadata header

    Health check endpoints can be optionally excluded from authentication.
    """

    # Health check method patterns
    HEALTH_CHECK_METHODS = {
        '/grpc.health.v1.Health/Check',
        '/grpc.health.v1.Health/Watch',
    }

    def __init__(self, config: AuthConfig):
        """Initialize the authentication interceptor.

        Args:
            config: Authentication configuration
        """
        self.config = config

    async def intercept_service(
        self,
        continuation: Callable[[grpc.HandlerCallDetails], Any],
        handler_call_details: grpc.HandlerCallDetails,
    ) -> Any:
        """Intercept and authenticate service calls.

        Args:
            continuation: Function to invoke the next interceptor or handler
            handler_call_details: Details about the RPC being handled

        Returns:
            Handler for the RPC call or None if authentication fails
        """
        method = handler_call_details.method

        # Skip authentication if disabled
        if not self.config.enabled:
            return await continuation(handler_call_details)

        # Skip authentication for health checks if configured
        if self.config.skip_health_check and method in self.HEALTH_CHECK_METHODS:
            return await continuation(handler_call_details)

        # Extract authentication metadata
        metadata = dict(handler_call_details.invocation_metadata)

        # Try API key authentication first
        api_key = metadata.get('x-api-key')
        if api_key:
            # Convert bytes to string if needed
            api_key_str = api_key.decode('utf-8') if isinstance(api_key, bytes) else api_key
            if self._validate_api_key(api_key_str):
                logger.debug(f'API key authentication successful for {method}')
                return await continuation(handler_call_details)
            else:
                logger.warning(f'Invalid API key for {method}')
                return self._create_unauthenticated_handler('Invalid API key')

        # Try Bearer token authentication
        auth_header = metadata.get('authorization')
        if auth_header:
            # Convert bytes to string if needed
            auth_header_str = (
                auth_header.decode('utf-8') if isinstance(auth_header, bytes) else auth_header
            )
            if auth_header_str.startswith('Bearer ') or auth_header_str.startswith('bearer '):
                token = auth_header_str[7:]  # Remove 'Bearer ' prefix
                if self._validate_jwt(token):
                    logger.debug(f'JWT authentication successful for {method}')
                    return await continuation(handler_call_details)
                else:
                    logger.warning(f'Invalid JWT token for {method}')
                    return self._create_unauthenticated_handler('Invalid token')
            else:
                logger.warning(f'Invalid authorization header format for {method}')
                return self._create_unauthenticated_handler('Invalid authorization header format')

        # No valid credentials provided
        logger.warning(f'No authentication credentials provided for {method}')
        return self._create_unauthenticated_handler('Authentication required')

    def _validate_api_key(self, api_key: str) -> bool:
        """Validate an API key using constant-time comparison.

        Args:
            api_key: The API key to validate

        Returns:
            True if the API key is valid, False otherwise
        """
        if not self.config.api_keys:
            return False

        # Input validation: reject empty or excessively long keys
        if not api_key or len(api_key) > 512:
            return False

        # Use constant-time comparison to prevent timing attacks
        # Compare against each configured API key
        for valid_key in self.config.api_keys:
            if secrets.compare_digest(api_key, valid_key):
                return True

        return False

    def _validate_jwt(self, token: str) -> bool:
        """Validate a JWT token.

        Args:
            token: The JWT token to validate

        Returns:
            True if the token is valid, False otherwise
        """
        if not self.config.jwt_secret:
            return False

        # Input validation: reject empty or excessively long tokens
        if not token or len(token) > 8192:
            return False

        try:
            # Import jwt only if needed to avoid unnecessary dependency
            import jwt

            # Decode and verify the JWT
            jwt.decode(
                token,
                self.config.jwt_secret,
                algorithms=[self.config.jwt_algorithm],
                options={
                    'verify_signature': True,
                    'verify_exp': True,
                    'verify_iat': True,
                    'require': ['exp', 'iat'],
                },
            )
            return True

        except ImportError:
            logger.error('PyJWT library not installed. JWT authentication disabled.')
            return False
        except jwt.ExpiredSignatureError:
            logger.warning('JWT token has expired')
            return False
        except jwt.InvalidTokenError as e:
            logger.warning(f'Invalid JWT token: {e}')
            return False
        except Exception as e:
            # Catch-all for unexpected errors during JWT validation
            logger.error(f'Unexpected error during JWT validation: {e}')
            return False

    def _create_unauthenticated_handler(self, message: str):
        """Create a handler that returns UNAUTHENTICATED status.

        Args:
            message: Error message to include in the response

        Returns:
            A handler that aborts with UNAUTHENTICATED status
        """

        async def abort_unauthenticated(request_or_iterator, context):
            """Abort the RPC with UNAUTHENTICATED status."""
            await context.abort(
                grpc.StatusCode.UNAUTHENTICATED,
                message,
            )

        # Return a generic handler that works for all RPC types
        # The handler will be called and will immediately abort
        return grpc.unary_unary_rpc_method_handler(
            abort_unauthenticated,
            request_deserializer=None,
            response_serializer=None,
        )
