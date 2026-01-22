"""Configuration schemas for MCP server.

Imports shared configuration from server_common and adds MCP-specific config.
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
    EmbedderConfig,
    EntityTypeConfig,
    GraphitiAppConfig,
    LLMConfig,
    YamlSettingsSource,
)

# Re-export for backwards compatibility
__all__ = [
    'ServerConfig',
    'GraphitiConfig',
    'LLMConfig',
    'EmbedderConfig',
    'DatabaseConfig',
    'EntityTypeConfig',
    'GraphitiAppConfig',
]


class ServerConfig(BaseModel):
    """MCP Server configuration."""

    transport: str = Field(
        default='http',
        description='Transport type: http (default, recommended), stdio, or sse (deprecated)',
    )
    host: str = Field(default='0.0.0.0', description='Server host')
    port: int = Field(default=8000, description='Server port')


class GraphitiConfig(BaseSettings):
    """Graphiti MCP configuration with YAML and environment support."""

    server: ServerConfig = Field(default_factory=ServerConfig)
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
        # Override server settings
        if hasattr(args, 'transport') and args.transport:
            self.server.transport = args.transport

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
