"""Tests for server_common.config module."""

from pathlib import Path

import pytest

from server_common.config import (
    AnthropicProviderConfig,
    AzureOpenAIProviderConfig,
    DatabaseConfig,
    DatabaseProvidersConfig,
    EmbedderConfig,
    EmbedderProvidersConfig,
    EntityTypeConfig,
    FalkorDBProviderConfig,
    GeminiProviderConfig,
    GraphitiAppConfig,
    GroqProviderConfig,
    LLMConfig,
    LLMProvidersConfig,
    Neo4jProviderConfig,
    OpenAIProviderConfig,
    VoyageProviderConfig,
    YamlSettingsSource,
)


class TestYamlSettingsSource:
    """Tests for YamlSettingsSource."""

    def test_init_default_path(self):
        """Test initialization with default path."""
        from pydantic_settings import BaseSettings

        source = YamlSettingsSource(BaseSettings)
        assert source.config_path == Path('config.yaml')

    def test_init_custom_path(self):
        """Test initialization with custom path."""
        from pydantic_settings import BaseSettings

        custom_path = Path('/custom/path/config.yaml')
        source = YamlSettingsSource(BaseSettings, config_path=custom_path)
        assert source.config_path == custom_path

    def test_load_nonexistent_file(self):
        """Test loading from nonexistent file returns empty dict."""
        from pydantic_settings import BaseSettings

        source = YamlSettingsSource(BaseSettings, config_path=Path('/nonexistent/config.yaml'))
        result = source()
        assert result == {}

    def test_load_valid_yaml(self, temp_yaml_file):
        """Test loading valid YAML file."""
        from pydantic_settings import BaseSettings

        yaml_content = """
llm:
  provider: openai
  model: gpt-4
database:
  provider: neo4j
"""
        config_path = temp_yaml_file(yaml_content)
        source = YamlSettingsSource(BaseSettings, config_path=config_path)
        result = source()

        assert result['llm']['provider'] == 'openai'
        assert result['llm']['model'] == 'gpt-4'
        assert result['database']['provider'] == 'neo4j'

    def test_expand_env_var_simple(self, temp_yaml_file, mock_env):
        """Test simple environment variable expansion."""
        from pydantic_settings import BaseSettings

        mock_env(TEST_API_KEY='my-secret-key')

        yaml_content = """
llm:
  api_key: ${TEST_API_KEY}
"""
        config_path = temp_yaml_file(yaml_content)
        source = YamlSettingsSource(BaseSettings, config_path=config_path)
        result = source()

        assert result['llm']['api_key'] == 'my-secret-key'

    def test_expand_env_var_with_default(self, temp_yaml_file, mock_env):
        """Test environment variable expansion with default value."""
        from pydantic_settings import BaseSettings

        yaml_content = """
llm:
  model: ${NONEXISTENT_VAR:gpt-4-default}
"""
        config_path = temp_yaml_file(yaml_content)
        source = YamlSettingsSource(BaseSettings, config_path=config_path)
        result = source()

        assert result['llm']['model'] == 'gpt-4-default'

    def test_expand_env_var_empty_default(self, temp_yaml_file, mock_env):
        """Test environment variable expansion with empty default."""
        from pydantic_settings import BaseSettings

        yaml_content = """
llm:
  api_key: ${NONEXISTENT_VAR:}
"""
        config_path = temp_yaml_file(yaml_content)
        source = YamlSettingsSource(BaseSettings, config_path=config_path)
        result = source()

        assert result['llm']['api_key'] is None

    def test_expand_env_var_boolean_true(self, temp_yaml_file, mock_env):
        """Test environment variable expansion converts to boolean True."""
        from pydantic_settings import BaseSettings

        mock_env(ENABLE_TLS='true')

        yaml_content = """
grpc:
  enable_tls: ${ENABLE_TLS}
"""
        config_path = temp_yaml_file(yaml_content)
        source = YamlSettingsSource(BaseSettings, config_path=config_path)
        result = source()

        assert result['grpc']['enable_tls'] is True

    def test_expand_env_var_boolean_false(self, temp_yaml_file, mock_env):
        """Test environment variable expansion converts to boolean False."""
        from pydantic_settings import BaseSettings

        mock_env(ENABLE_TLS='false')

        yaml_content = """
grpc:
  enable_tls: ${ENABLE_TLS}
"""
        config_path = temp_yaml_file(yaml_content)
        source = YamlSettingsSource(BaseSettings, config_path=config_path)
        result = source()

        assert result['grpc']['enable_tls'] is False

    def test_expand_env_var_boolean_yes(self, temp_yaml_file, mock_env):
        """Test 'yes' is converted to True."""
        from pydantic_settings import BaseSettings

        mock_env(FLAG='yes')

        yaml_content = """
flag: ${FLAG}
"""
        config_path = temp_yaml_file(yaml_content)
        source = YamlSettingsSource(BaseSettings, config_path=config_path)
        result = source()

        assert result['flag'] is True

    def test_expand_env_var_boolean_no(self, temp_yaml_file, mock_env):
        """Test 'no' is converted to False."""
        from pydantic_settings import BaseSettings

        mock_env(FLAG='no')

        yaml_content = """
flag: ${FLAG}
"""
        config_path = temp_yaml_file(yaml_content)
        source = YamlSettingsSource(BaseSettings, config_path=config_path)
        result = source()

        assert result['flag'] is False

    def test_expand_env_var_in_list(self, temp_yaml_file, mock_env):
        """Test environment variable expansion in list items."""
        from pydantic_settings import BaseSettings

        mock_env(KEY1='value1', KEY2='value2')

        yaml_content = """
keys:
  - ${KEY1}
  - ${KEY2}
  - static
"""
        config_path = temp_yaml_file(yaml_content)
        source = YamlSettingsSource(BaseSettings, config_path=config_path)
        result = source()

        assert result['keys'] == ['value1', 'value2', 'static']

    def test_expand_env_var_nested(self, temp_yaml_file, mock_env):
        """Test environment variable expansion in nested structures."""
        from pydantic_settings import BaseSettings

        mock_env(OPENAI_KEY='openai-key', ANTHROPIC_KEY='anthropic-key')

        yaml_content = """
llm:
  providers:
    openai:
      api_key: ${OPENAI_KEY}
    anthropic:
      api_key: ${ANTHROPIC_KEY}
"""
        config_path = temp_yaml_file(yaml_content)
        source = YamlSettingsSource(BaseSettings, config_path=config_path)
        result = source()

        assert result['llm']['providers']['openai']['api_key'] == 'openai-key'
        assert result['llm']['providers']['anthropic']['api_key'] == 'anthropic-key'

    def test_expand_env_var_partial_string(self, temp_yaml_file, mock_env):
        """Test environment variable expansion in partial string."""
        from pydantic_settings import BaseSettings

        mock_env(HOST='localhost', PORT='5432')

        yaml_content = """
database:
  uri: postgresql://${HOST}:${PORT}/mydb
"""
        config_path = temp_yaml_file(yaml_content)
        source = YamlSettingsSource(BaseSettings, config_path=config_path)
        result = source()

        assert result['database']['uri'] == 'postgresql://localhost:5432/mydb'

    def test_get_field_value_returns_none(self):
        """Test get_field_value always returns None."""
        from pydantic_settings import BaseSettings

        source = YamlSettingsSource(BaseSettings)
        assert source.get_field_value('any_field', None) is None


class TestOpenAIProviderConfig:
    """Tests for OpenAIProviderConfig."""

    def test_defaults(self):
        """Test default values."""
        config = OpenAIProviderConfig()
        assert config.api_key is None
        assert config.api_url == 'https://api.openai.com/v1'
        assert config.organization_id is None

    def test_custom_values(self):
        """Test custom values."""
        config = OpenAIProviderConfig(
            api_key='sk-test',
            api_url='https://custom.api.com/v1',
            organization_id='org-123',
        )
        assert config.api_key == 'sk-test'
        assert config.api_url == 'https://custom.api.com/v1'
        assert config.organization_id == 'org-123'


class TestAzureOpenAIProviderConfig:
    """Tests for AzureOpenAIProviderConfig."""

    def test_defaults(self):
        """Test default values."""
        config = AzureOpenAIProviderConfig()
        assert config.api_key is None
        assert config.api_url is None
        assert config.api_version == '2024-10-21'
        assert config.deployment_name is None
        assert config.use_azure_ad is False

    def test_custom_values(self):
        """Test custom values."""
        config = AzureOpenAIProviderConfig(
            api_key='azure-key',
            api_url='https://my-resource.openai.azure.com',
            api_version='2024-01-01',
            deployment_name='gpt-4-deployment',
            use_azure_ad=True,
        )
        assert config.api_key == 'azure-key'
        assert config.api_url == 'https://my-resource.openai.azure.com'
        assert config.api_version == '2024-01-01'
        assert config.deployment_name == 'gpt-4-deployment'
        assert config.use_azure_ad is True


class TestAnthropicProviderConfig:
    """Tests for AnthropicProviderConfig."""

    def test_defaults(self):
        """Test default values."""
        config = AnthropicProviderConfig()
        assert config.api_key is None
        assert config.api_url == 'https://api.anthropic.com'
        assert config.max_retries == 3

    def test_custom_values(self):
        """Test custom values."""
        config = AnthropicProviderConfig(
            api_key='anthropic-key',
            api_url='https://custom.anthropic.com',
            max_retries=5,
        )
        assert config.api_key == 'anthropic-key'
        assert config.api_url == 'https://custom.anthropic.com'
        assert config.max_retries == 5


class TestGeminiProviderConfig:
    """Tests for GeminiProviderConfig."""

    def test_defaults(self):
        """Test default values."""
        config = GeminiProviderConfig()
        assert config.api_key is None
        assert config.project_id is None
        assert config.location == 'us-central1'

    def test_custom_values(self):
        """Test custom values."""
        config = GeminiProviderConfig(
            api_key='gemini-key',
            project_id='my-project',
            location='europe-west1',
        )
        assert config.api_key == 'gemini-key'
        assert config.project_id == 'my-project'
        assert config.location == 'europe-west1'


class TestGroqProviderConfig:
    """Tests for GroqProviderConfig."""

    def test_defaults(self):
        """Test default values."""
        config = GroqProviderConfig()
        assert config.api_key is None
        assert config.api_url == 'https://api.groq.com/openai/v1'

    def test_custom_values(self):
        """Test custom values."""
        config = GroqProviderConfig(
            api_key='groq-key',
            api_url='https://custom.groq.com/v1',
        )
        assert config.api_key == 'groq-key'
        assert config.api_url == 'https://custom.groq.com/v1'


class TestVoyageProviderConfig:
    """Tests for VoyageProviderConfig."""

    def test_defaults(self):
        """Test default values."""
        config = VoyageProviderConfig()
        assert config.api_key is None
        assert config.api_url == 'https://api.voyageai.com/v1'
        assert config.model == 'voyage-3'

    def test_custom_values(self):
        """Test custom values."""
        config = VoyageProviderConfig(
            api_key='voyage-key',
            api_url='https://custom.voyage.com/v1',
            model='voyage-2',
        )
        assert config.api_key == 'voyage-key'
        assert config.api_url == 'https://custom.voyage.com/v1'
        assert config.model == 'voyage-2'


class TestLLMProvidersConfig:
    """Tests for LLMProvidersConfig."""

    def test_defaults(self):
        """Test default values."""
        config = LLMProvidersConfig()
        assert config.openai is None
        assert config.azure_openai is None
        assert config.anthropic is None
        assert config.gemini is None
        assert config.groq is None

    def test_with_providers(self):
        """Test with provider configurations."""
        config = LLMProvidersConfig(
            openai=OpenAIProviderConfig(api_key='openai-key'),
            anthropic=AnthropicProviderConfig(api_key='anthropic-key'),
        )
        assert config.openai.api_key == 'openai-key'
        assert config.anthropic.api_key == 'anthropic-key'
        assert config.gemini is None


class TestLLMConfig:
    """Tests for LLMConfig."""

    def test_defaults(self):
        """Test default values."""
        config = LLMConfig()
        assert config.provider == 'openai'
        assert config.model == 'gpt-4o-mini'
        assert config.temperature is None
        assert config.max_tokens == 4096
        assert config.providers is not None

    def test_custom_values(self):
        """Test custom values."""
        config = LLMConfig(
            provider='anthropic',
            model='claude-3-opus',
            temperature=0.7,
            max_tokens=8192,
        )
        assert config.provider == 'anthropic'
        assert config.model == 'claude-3-opus'
        assert config.temperature == 0.7
        assert config.max_tokens == 8192


class TestEmbedderProvidersConfig:
    """Tests for EmbedderProvidersConfig."""

    def test_defaults(self):
        """Test default values."""
        config = EmbedderProvidersConfig()
        assert config.openai is None
        assert config.azure_openai is None
        assert config.gemini is None
        assert config.voyage is None

    def test_with_providers(self):
        """Test with provider configurations."""
        config = EmbedderProvidersConfig(
            openai=OpenAIProviderConfig(api_key='openai-key'),
            voyage=VoyageProviderConfig(api_key='voyage-key'),
        )
        assert config.openai.api_key == 'openai-key'
        assert config.voyage.api_key == 'voyage-key'


class TestEmbedderConfig:
    """Tests for EmbedderConfig."""

    def test_defaults(self):
        """Test default values."""
        config = EmbedderConfig()
        assert config.provider == 'openai'
        assert config.model == 'text-embedding-3-small'
        assert config.dimensions == 1536
        assert config.providers is not None

    def test_custom_values(self):
        """Test custom values."""
        config = EmbedderConfig(
            provider='voyage',
            model='voyage-3',
            dimensions=1024,
        )
        assert config.provider == 'voyage'
        assert config.model == 'voyage-3'
        assert config.dimensions == 1024


class TestNeo4jProviderConfig:
    """Tests for Neo4jProviderConfig."""

    def test_defaults(self):
        """Test default values."""
        config = Neo4jProviderConfig()
        assert config.uri == 'bolt://localhost:7687'
        assert config.username == 'neo4j'
        assert config.password is None
        assert config.database == 'neo4j'
        assert config.use_parallel_runtime is False

    def test_custom_values(self):
        """Test custom values."""
        config = Neo4jProviderConfig(
            uri='bolt://neo4j-server:7687',
            username='admin',
            password='secret',
            database='mydb',
            use_parallel_runtime=True,
        )
        assert config.uri == 'bolt://neo4j-server:7687'
        assert config.username == 'admin'
        assert config.password == 'secret'
        assert config.database == 'mydb'
        assert config.use_parallel_runtime is True


class TestFalkorDBProviderConfig:
    """Tests for FalkorDBProviderConfig."""

    def test_defaults(self):
        """Test default values."""
        config = FalkorDBProviderConfig()
        assert config.uri == 'redis://localhost:6379'
        assert config.password is None
        assert config.database == 'default_db'

    def test_custom_values(self):
        """Test custom values."""
        config = FalkorDBProviderConfig(
            uri='redis://falkordb-server:6380',
            password='redis-secret',
            database='my_graph_db',
        )
        assert config.uri == 'redis://falkordb-server:6380'
        assert config.password == 'redis-secret'
        assert config.database == 'my_graph_db'


class TestDatabaseProvidersConfig:
    """Tests for DatabaseProvidersConfig."""

    def test_defaults(self):
        """Test default values."""
        config = DatabaseProvidersConfig()
        assert config.neo4j is None
        assert config.falkordb is None

    def test_with_providers(self):
        """Test with provider configurations."""
        config = DatabaseProvidersConfig(
            neo4j=Neo4jProviderConfig(password='neo4j-pass'),
            falkordb=FalkorDBProviderConfig(password='falkor-pass'),
        )
        assert config.neo4j.password == 'neo4j-pass'
        assert config.falkordb.password == 'falkor-pass'


class TestDatabaseConfig:
    """Tests for DatabaseConfig."""

    def test_defaults(self):
        """Test default values."""
        config = DatabaseConfig()
        assert config.provider == 'falkordb'
        assert config.providers is not None

    def test_custom_values(self):
        """Test custom values."""
        config = DatabaseConfig(
            provider='neo4j',
            providers=DatabaseProvidersConfig(
                neo4j=Neo4jProviderConfig(uri='bolt://custom:7687')
            ),
        )
        assert config.provider == 'neo4j'
        assert config.providers.neo4j.uri == 'bolt://custom:7687'


class TestEntityTypeConfig:
    """Tests for EntityTypeConfig."""

    def test_creation(self):
        """Test entity type creation."""
        config = EntityTypeConfig(
            name='Person',
            description='A human being',
        )
        assert config.name == 'Person'
        assert config.description == 'A human being'

    def test_required_fields(self):
        """Test that name and description are required."""
        with pytest.raises(Exception):  # ValidationError
            EntityTypeConfig()


class TestGraphitiAppConfig:
    """Tests for GraphitiAppConfig."""

    def test_defaults(self):
        """Test default values."""
        config = GraphitiAppConfig()
        assert config.group_id == 'main'
        assert config.episode_id_prefix == ''
        assert config.user_id == 'user'
        assert config.entity_types == []

    def test_custom_values(self):
        """Test custom values."""
        config = GraphitiAppConfig(
            group_id='custom-group',
            episode_id_prefix='ep-',
            user_id='custom-user',
            entity_types=[
                EntityTypeConfig(name='Person', description='A person'),
                EntityTypeConfig(name='Organization', description='An organization'),
            ],
        )
        assert config.group_id == 'custom-group'
        assert config.episode_id_prefix == 'ep-'
        assert config.user_id == 'custom-user'
        assert len(config.entity_types) == 2
        assert config.entity_types[0].name == 'Person'

    def test_none_episode_id_prefix_converted_to_empty_string(self):
        """Test that None episode_id_prefix is converted to empty string."""
        config = GraphitiAppConfig(episode_id_prefix=None)
        assert config.episode_id_prefix == ''
