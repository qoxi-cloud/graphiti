"""Tests for configuration schema."""

import os


class TestGRPCServerConfig:
    """Tests for GRPCServerConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        from src.config.schema import GRPCServerConfig

        config = GRPCServerConfig()

        assert config.host == '0.0.0.0'
        assert config.port == 50051
        assert config.max_workers == 10
        assert config.enable_tls is False
        assert config.enable_reflection is True

    def test_custom_values(self):
        """Test custom configuration values."""
        from src.config.schema import GRPCServerConfig

        config = GRPCServerConfig(
            host='127.0.0.1',
            port=9000,
            max_workers=20,
            enable_tls=True,
            cert_path='/path/to/cert',
            key_path='/path/to/key',
        )

        assert config.host == '127.0.0.1'
        assert config.port == 9000
        assert config.max_workers == 20
        assert config.enable_tls is True
        assert config.cert_path == '/path/to/cert'


class TestGraphitiGRPCConfig:
    """Tests for GraphitiGRPCConfig."""

    def test_default_config(self):
        """Test default full configuration."""
        from src.config.schema import GraphitiGRPCConfig

        config = GraphitiGRPCConfig()

        assert config.grpc.port == 50051
        assert config.llm.provider == 'openai'
        assert config.database.provider == 'falkordb'

    def test_yaml_settings_source_expand_env_vars(self):
        """Test environment variable expansion in YAML config."""
        from pydantic_settings import BaseSettings

        from src.config.schema import YamlSettingsSource

        class MockSettings(BaseSettings):
            pass

        source = YamlSettingsSource(MockSettings)

        # Test simple expansion
        os.environ['TEST_VAR'] = 'test_value'
        result = source._expand_env_vars('${TEST_VAR}')
        assert result == 'test_value'

        # Test with default
        result = source._expand_env_vars('${NONEXISTENT_VAR:default}')
        assert result == 'default'

        # Test boolean conversion
        os.environ['TEST_BOOL'] = 'true'
        result = source._expand_env_vars('${TEST_BOOL}')
        assert result is True

        # Test nested dict
        os.environ['NESTED_VAR'] = 'nested_value'
        result = source._expand_env_vars({'key': '${NESTED_VAR}'})
        assert result == {'key': 'nested_value'}

        # Clean up
        del os.environ['TEST_VAR']
        del os.environ['TEST_BOOL']
        del os.environ['NESTED_VAR']


class TestLLMConfig:
    """Tests for LLMConfig."""

    def test_default_values(self):
        """Test default LLM configuration."""
        from src.config.schema import LLMConfig

        config = LLMConfig()

        assert config.provider == 'openai'
        assert config.model == 'gpt-4o-mini'
        assert config.temperature is None
        assert config.max_tokens == 4096

    def test_custom_values(self):
        """Test custom LLM configuration."""
        from src.config.schema import LLMConfig

        config = LLMConfig(
            provider='anthropic',
            model='claude-3-sonnet',
            temperature=0.7,
            max_tokens=8192,
        )

        assert config.provider == 'anthropic'
        assert config.model == 'claude-3-sonnet'
        assert config.temperature == 0.7
        assert config.max_tokens == 8192


class TestEmbedderConfig:
    """Tests for EmbedderConfig."""

    def test_default_values(self):
        """Test default embedder configuration."""
        from src.config.schema import EmbedderConfig

        config = EmbedderConfig()

        assert config.provider == 'openai'
        assert config.model == 'text-embedding-3-small'
        assert config.dimensions == 1536


class TestDatabaseConfig:
    """Tests for DatabaseConfig."""

    def test_default_values(self):
        """Test default database configuration."""
        from src.config.schema import DatabaseConfig

        config = DatabaseConfig()

        assert config.provider == 'falkordb'

    def test_neo4j_provider_config(self):
        """Test Neo4j provider configuration."""
        from src.config.schema import Neo4jProviderConfig

        config = Neo4jProviderConfig(
            uri='bolt://localhost:7687',
            username='neo4j',
            password='password',
            database='testdb',
        )

        assert config.uri == 'bolt://localhost:7687'
        assert config.username == 'neo4j'
        assert config.password == 'password'
        assert config.database == 'testdb'

    def test_falkordb_provider_config(self):
        """Test FalkorDB provider configuration."""
        from src.config.schema import FalkorDBProviderConfig

        config = FalkorDBProviderConfig(
            uri='redis://localhost:6379',
            password='password',
            database='testdb',
        )

        assert config.uri == 'redis://localhost:6379'
        assert config.password == 'password'
        assert config.database == 'testdb'


class TestGraphitiAppConfig:
    """Tests for GraphitiAppConfig."""

    def test_default_values(self):
        """Test default Graphiti app configuration."""
        from src.config.schema import GraphitiAppConfig

        config = GraphitiAppConfig()

        assert config.group_id == 'main'
        assert config.episode_id_prefix == ''
        assert config.user_id == 'user'
        assert config.entity_types == []

    def test_episode_id_prefix_none_handling(self):
        """Test that None episode_id_prefix is converted to empty string."""
        from src.config.schema import GraphitiAppConfig

        config = GraphitiAppConfig(episode_id_prefix=None)

        assert config.episode_id_prefix == ''
