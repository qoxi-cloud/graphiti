"""Configuration schemas for gRPC server.

Imports shared configuration from server_common and adds gRPC-specific config.
"""

import os
from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

# Import shared configs from server_common
from server_common.config import (
    DatabaseConfig,
    DatabaseProvidersConfig,
    EmbedderConfig,
    EmbedderProvidersConfig,
    EntityTypeConfig,
    FalkorDBProviderConfig,
    GraphitiAppConfig,
    LLMConfig,
    LLMProvidersConfig,
    Neo4jProviderConfig,
    OpenAIProviderConfig,
    YamlSettingsSource,
)

# Re-export for backwards compatibility
__all__ = [
    'AuthConfig',
    'CompressionConfig',
    'RateLimitConfig',
    'ServiceTimeoutConfig',
    'TimeoutConfig',
    'GRPCServerConfig',
    'GraphitiGRPCConfig',
    # Re-exported from server_common
    'LLMConfig',
    'LLMProvidersConfig',
    'EmbedderConfig',
    'EmbedderProvidersConfig',
    'DatabaseConfig',
    'DatabaseProvidersConfig',
    'EntityTypeConfig',
    'GraphitiAppConfig',
    'Neo4jProviderConfig',
    'FalkorDBProviderConfig',
    'OpenAIProviderConfig',
    'YamlSettingsSource',
]


class CompressionConfig(BaseModel):
    """Compression configuration for gRPC server."""

    enabled: bool = Field(default=True, description='Enable compression')
    algorithm: str = Field(
        default='gzip',
        description='Compression algorithm (gzip, deflate, or none)',
    )
    level: int = Field(
        default=2,
        ge=0,
        le=9,
        description='Compression level (0-9, where 0 is no compression and 9 is maximum)',
    )


class AuthConfig(BaseModel):
    """Authentication configuration."""

    enabled: bool = Field(default=False, description='Enable authentication')
    api_keys: list[str] = Field(default_factory=list, description='List of valid API keys')
    jwt_secret: str | None = Field(default=None, description='JWT secret key for token validation')
    jwt_algorithm: str = Field(default='HS256', description='JWT algorithm')
    skip_health_check: bool = Field(
        default=True, description='Skip authentication for health check endpoints'
    )


class RateLimitConfig(BaseModel):
    """Rate limiting configuration."""

    enabled: bool = Field(default=False, description='Enable rate limiting')
    window_seconds: float = Field(default=60.0, description='Time window in seconds')
    max_requests: int = Field(default=100, description='Maximum requests per window')
    read_max_requests: int | None = Field(
        default=None, description='Max requests for read operations (if different)'
    )
    write_max_requests: int | None = Field(
        default=None, description='Max requests for write operations (if different)'
    )
    skip_methods: list[str] = Field(
        default_factory=list, description='Additional methods to skip rate limiting'
    )


class ServiceTimeoutConfig(BaseModel):
    """Per-service timeout configuration with optional per-method overrides.

    Example YAML:
        default: 120
        methods:
          AddEpisodeBulk: 600
          StreamEpisodes: 0  # 0 means no timeout (for streaming)
    """

    default: float = Field(
        default=30.0,
        ge=0,
        description='Default timeout in seconds for this service (0 = no timeout)',
    )
    methods: dict[str, float] = Field(
        default_factory=dict,
        description='Per-method timeout overrides in seconds (0 = no timeout)',
    )

    def get_timeout(self, method_name: str) -> float:
        """Get the timeout for a specific method.

        Args:
            method_name: The method name (not the full path)

        Returns:
            Timeout in seconds, or 0 for no timeout
        """
        return self.methods.get(method_name, self.default)


class TimeoutConfig(BaseModel):
    """Timeout configuration for gRPC server with per-service and per-method support.

    Example YAML configuration:
        grpc:
          timeouts:
            enabled: true
            default: 30
            services:
              IngestService:
                default: 120
                methods:
                  AddEpisodeBulk: 600
                  StreamEpisodes: 0
              RetrieveService:
                default: 30
              AdminService:
                default: 60
                methods:
                  BuildCommunities: 300
                  ClearData: 120
    """

    enabled: bool = Field(default=True, description='Enable timeout enforcement')
    default: float = Field(
        default=30.0,
        ge=0,
        description='Global default timeout in seconds (0 = no timeout)',
    )
    services: dict[str, ServiceTimeoutConfig] = Field(
        default_factory=dict,
        description='Per-service timeout configuration',
    )

    def get_timeout(self, service_name: str, method_name: str) -> float:
        """Get the timeout for a specific service and method.

        Resolution order:
        1. Per-method timeout if configured
        2. Per-service default timeout if configured
        3. Global default timeout

        Args:
            service_name: The service name (e.g., 'IngestService')
            method_name: The method name (e.g., 'AddEpisode')

        Returns:
            Timeout in seconds, or 0 for no timeout
        """
        if service_name in self.services:
            return self.services[service_name].get_timeout(method_name)
        return self.default


class GRPCServerConfig(BaseModel):
    """gRPC server configuration."""

    host: str = Field(default='0.0.0.0', description='Server host')
    port: int = Field(default=50051, description='Server port')
    max_workers: int = Field(default=10, description='Maximum number of worker threads')
    enable_tls: bool = Field(default=False, description='Enable TLS')
    cert_path: str | None = Field(default=None, description='Path to TLS certificate')
    key_path: str | None = Field(default=None, description='Path to TLS private key')
    enable_reflection: bool = Field(default=True, description='Enable gRPC reflection')
    compression: CompressionConfig = Field(
        default_factory=CompressionConfig, description='Compression configuration'
    )
    auth: AuthConfig = Field(default_factory=AuthConfig, description='Authentication configuration')
    rate_limit: RateLimitConfig = Field(
        default_factory=RateLimitConfig, description='Rate limiting configuration'
    )
    timeouts: TimeoutConfig = Field(
        default_factory=TimeoutConfig, description='Timeout configuration'
    )


class GraphitiGRPCConfig(BaseSettings):
    """Graphiti gRPC configuration with YAML and environment support."""

    grpc: GRPCServerConfig = Field(default_factory=GRPCServerConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    embedder: EmbedderConfig = Field(default_factory=EmbedderConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    graphiti: GraphitiAppConfig = Field(default_factory=GraphitiAppConfig)

    # Additional server options
    destroy_graph: bool = Field(default=False, description='Clear graph on startup')

    model_config = SettingsConfigDict(
        env_prefix='',
        env_nested_delimiter='__',
        case_sensitive=False,
        extra='ignore',
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Customize settings sources to include YAML."""
        config_path = Path(os.environ.get('CONFIG_PATH', 'config/config.yaml'))
        yaml_settings = YamlSettingsSource(settings_cls, config_path)
        return (init_settings, env_settings, yaml_settings, dotenv_settings)

    def apply_cli_overrides(self, args) -> None:
        """Apply CLI argument overrides to configuration."""
        # Override gRPC settings
        if hasattr(args, 'host') and args.host:
            self.grpc.host = args.host
        if hasattr(args, 'port') and args.port:
            self.grpc.port = args.port
        if hasattr(args, 'max_workers') and args.max_workers:
            self.grpc.max_workers = args.max_workers

        # Override LLM settings
        if hasattr(args, 'llm_provider') and args.llm_provider:
            self.llm.provider = args.llm_provider
        if hasattr(args, 'model') and args.model:
            self.llm.model = args.model
        if hasattr(args, 'temperature') and args.temperature is not None:
            self.llm.temperature = args.temperature

        # Override embedder settings
        if hasattr(args, 'embedder_provider') and args.embedder_provider:
            self.embedder.provider = args.embedder_provider
        if hasattr(args, 'embedder_model') and args.embedder_model:
            self.embedder.model = args.embedder_model

        # Override database settings
        if hasattr(args, 'database_provider') and args.database_provider:
            self.database.provider = args.database_provider

        # Override Graphiti settings
        if hasattr(args, 'group_id') and args.group_id:
            self.graphiti.group_id = args.group_id
        if hasattr(args, 'user_id') and args.user_id:
            self.graphiti.user_id = args.user_id
