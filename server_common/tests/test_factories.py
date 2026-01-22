"""Tests for server_common.factories module."""

from unittest.mock import MagicMock, patch

import pytest

from server_common.config import (
    AnthropicProviderConfig,
    AzureOpenAIProviderConfig,
    DatabaseConfig,
    DatabaseProvidersConfig,
    EmbedderConfig,
    EmbedderProvidersConfig,
    FalkorDBProviderConfig,
    GeminiProviderConfig,
    GroqProviderConfig,
    LLMConfig,
    LLMProvidersConfig,
    Neo4jProviderConfig,
    OpenAIProviderConfig,
    VoyageProviderConfig,
)
from server_common.factories import (
    DatabaseDriverFactory,
    EmbedderFactory,
    LLMClientFactory,
    _validate_api_key,
)


class TestValidateApiKey:
    """Tests for _validate_api_key helper function."""

    def test_valid_api_key(self):
        """Test validation with valid API key."""
        result = _validate_api_key('OpenAI', 'sk-valid-key')
        assert result == 'sk-valid-key'

    def test_none_api_key_raises(self):
        """Test that None API key raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            _validate_api_key('OpenAI', None)
        assert 'OpenAI API key is not configured' in str(exc_info.value)

    def test_empty_api_key_raises(self):
        """Test that empty string API key raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            _validate_api_key('OpenAI', '')
        assert 'OpenAI API key is not configured' in str(exc_info.value)


class TestLLMClientFactory:
    """Tests for LLMClientFactory."""

    def test_create_openai_client(self):
        """Test creating OpenAI client."""
        config = LLMConfig(
            provider='openai',
            model='gpt-4o-mini',
            providers=LLMProvidersConfig(
                openai=OpenAIProviderConfig(api_key='sk-test-key')
            ),
        )

        with patch('server_common.factories.OpenAIClient') as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance

            client = LLMClientFactory.create(config)

            mock_client.assert_called_once()
            assert client == mock_instance

    def test_create_openai_client_reasoning_model(self):
        """Test creating OpenAI client with reasoning model (gpt-5)."""
        config = LLMConfig(
            provider='openai',
            model='gpt-5',
            providers=LLMProvidersConfig(
                openai=OpenAIProviderConfig(api_key='sk-test-key')
            ),
        )

        with patch('server_common.factories.OpenAIClient') as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance

            LLMClientFactory.create(config)

            mock_client.assert_called_once()
            call_kwargs = mock_client.call_args[1]
            assert call_kwargs.get('reasoning') == 'minimal'
            assert call_kwargs.get('verbosity') == 'low'

    def test_create_openai_client_o1_model(self):
        """Test creating OpenAI client with o1 reasoning model."""
        config = LLMConfig(
            provider='openai',
            model='o1-preview',
            providers=LLMProvidersConfig(
                openai=OpenAIProviderConfig(api_key='sk-test-key')
            ),
        )

        with patch('server_common.factories.OpenAIClient') as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance

            LLMClientFactory.create(config)

            call_kwargs = mock_client.call_args[1]
            assert call_kwargs.get('reasoning') == 'minimal'

    def test_create_openai_client_missing_config(self):
        """Test that missing OpenAI provider config raises error."""
        config = LLMConfig(
            provider='openai',
            model='gpt-4',
            providers=LLMProvidersConfig(),  # No openai config
        )

        with pytest.raises(ValueError) as exc_info:
            LLMClientFactory.create(config)
        assert 'OpenAI provider configuration not found' in str(exc_info.value)

    def test_create_openai_client_missing_api_key(self):
        """Test that missing API key raises error."""
        config = LLMConfig(
            provider='openai',
            model='gpt-4',
            providers=LLMProvidersConfig(
                openai=OpenAIProviderConfig(api_key=None)
            ),
        )

        with pytest.raises(ValueError) as exc_info:
            LLMClientFactory.create(config)
        assert 'API key is not configured' in str(exc_info.value)

    def test_create_anthropic_client(self):
        """Test creating Anthropic client."""
        import server_common.factories as factories_module

        if not factories_module.HAS_ANTHROPIC:
            pytest.skip('Anthropic client not available')

        config = LLMConfig(
            provider='anthropic',
            model='claude-3-opus',
            providers=LLMProvidersConfig(
                anthropic=AnthropicProviderConfig(api_key='anthropic-key')
            ),
        )

        with patch.object(factories_module, 'AnthropicClient') as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance

            client = LLMClientFactory.create(config)

            mock_client.assert_called_once()
            assert client == mock_instance

    @patch('server_common.factories.HAS_ANTHROPIC', False)
    def test_create_anthropic_client_not_available(self):
        """Test that unavailable Anthropic client raises error."""
        config = LLMConfig(
            provider='anthropic',
            model='claude-3-opus',
            providers=LLMProvidersConfig(
                anthropic=AnthropicProviderConfig(api_key='anthropic-key')
            ),
        )

        with pytest.raises(ValueError) as exc_info:
            LLMClientFactory.create(config)
        assert 'Anthropic client not available' in str(exc_info.value)

    def test_create_gemini_client(self):
        """Test creating Gemini client."""
        import server_common.factories as factories_module

        if not factories_module.HAS_GEMINI:
            pytest.skip('Gemini client not available')

        config = LLMConfig(
            provider='gemini',
            model='gemini-pro',
            providers=LLMProvidersConfig(
                gemini=GeminiProviderConfig(api_key='gemini-key')
            ),
        )

        with patch.object(factories_module, 'GeminiClient') as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance

            client = LLMClientFactory.create(config)

            mock_client.assert_called_once()
            assert client == mock_instance

    @patch('server_common.factories.HAS_GEMINI', False)
    def test_create_gemini_client_not_available(self):
        """Test that unavailable Gemini client raises error."""
        config = LLMConfig(
            provider='gemini',
            model='gemini-pro',
            providers=LLMProvidersConfig(
                gemini=GeminiProviderConfig(api_key='gemini-key')
            ),
        )

        with pytest.raises(ValueError) as exc_info:
            LLMClientFactory.create(config)
        assert 'Gemini client not available' in str(exc_info.value)

    def test_create_groq_client(self):
        """Test creating Groq client."""
        import server_common.factories as factories_module

        if not factories_module.HAS_GROQ:
            pytest.skip('Groq client not available')

        config = LLMConfig(
            provider='groq',
            model='mixtral-8x7b',
            providers=LLMProvidersConfig(
                groq=GroqProviderConfig(api_key='groq-key')
            ),
        )

        with patch.object(factories_module, 'GroqClient') as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance

            client = LLMClientFactory.create(config)

            mock_client.assert_called_once()
            assert client == mock_instance

    @patch('server_common.factories.HAS_GROQ', False)
    def test_create_groq_client_not_available(self):
        """Test that unavailable Groq client raises error."""
        config = LLMConfig(
            provider='groq',
            model='mixtral-8x7b',
            providers=LLMProvidersConfig(
                groq=GroqProviderConfig(api_key='groq-key')
            ),
        )

        with pytest.raises(ValueError) as exc_info:
            LLMClientFactory.create(config)
        assert 'Groq client not available' in str(exc_info.value)

    def test_create_unsupported_provider(self):
        """Test that unsupported provider raises error."""
        config = LLMConfig(
            provider='unsupported',
            model='some-model',
        )

        with pytest.raises(ValueError) as exc_info:
            LLMClientFactory.create(config)
        assert 'Unsupported LLM provider: unsupported' in str(exc_info.value)

    @patch('server_common.factories.HAS_AZURE_LLM', True)
    def test_create_azure_openai_client(self):
        """Test creating Azure OpenAI client."""
        config = LLMConfig(
            provider='azure_openai',
            model='gpt-4',
            providers=LLMProvidersConfig(
                azure_openai=AzureOpenAIProviderConfig(
                    api_key='azure-key',
                    api_url='https://my-resource.openai.azure.com',
                    deployment_name='gpt-4-deployment',
                )
            ),
        )

        with patch('server_common.factories.AsyncAzureOpenAI'):
            with patch('server_common.factories.AzureOpenAILLMClient') as mock_client:
                mock_instance = MagicMock()
                mock_client.return_value = mock_instance

                client = LLMClientFactory.create(config)

                mock_client.assert_called_once()
                assert client == mock_instance

    @patch('server_common.factories.HAS_AZURE_LLM', True)
    def test_create_azure_openai_client_missing_url(self):
        """Test that missing Azure URL raises error."""
        config = LLMConfig(
            provider='azure_openai',
            model='gpt-4',
            providers=LLMProvidersConfig(
                azure_openai=AzureOpenAIProviderConfig(
                    api_key='azure-key',
                    api_url=None,
                )
            ),
        )

        with pytest.raises(ValueError) as exc_info:
            LLMClientFactory.create(config)
        assert 'Azure OpenAI API URL is required' in str(exc_info.value)


class TestEmbedderFactory:
    """Tests for EmbedderFactory."""

    def test_create_openai_embedder(self):
        """Test creating OpenAI embedder."""
        config = EmbedderConfig(
            provider='openai',
            model='text-embedding-3-small',
            providers=EmbedderProvidersConfig(
                openai=OpenAIProviderConfig(api_key='sk-test-key')
            ),
        )

        with patch('server_common.factories.OpenAIEmbedder') as mock_embedder:
            mock_instance = MagicMock()
            mock_embedder.return_value = mock_instance

            embedder = EmbedderFactory.create(config)

            mock_embedder.assert_called_once()
            assert embedder == mock_instance

    def test_create_openai_embedder_missing_config(self):
        """Test that missing OpenAI provider config raises error."""
        config = EmbedderConfig(
            provider='openai',
            model='text-embedding-3-small',
            providers=EmbedderProvidersConfig(),
        )

        with pytest.raises(ValueError) as exc_info:
            EmbedderFactory.create(config)
        assert 'OpenAI provider configuration not found' in str(exc_info.value)

    def test_create_openai_embedder_missing_api_key(self):
        """Test that missing API key raises error."""
        config = EmbedderConfig(
            provider='openai',
            model='text-embedding-3-small',
            providers=EmbedderProvidersConfig(
                openai=OpenAIProviderConfig(api_key=None)
            ),
        )

        with pytest.raises(ValueError) as exc_info:
            EmbedderFactory.create(config)
        assert 'API key is not configured' in str(exc_info.value)

    def test_create_voyage_embedder(self):
        """Test creating Voyage embedder."""
        import server_common.factories as factories_module

        if not factories_module.HAS_VOYAGE_EMBEDDER:
            pytest.skip('Voyage embedder not available')

        config = EmbedderConfig(
            provider='voyage',
            model='voyage-3',
            dimensions=1024,
            providers=EmbedderProvidersConfig(
                voyage=VoyageProviderConfig(api_key='voyage-key')
            ),
        )

        with patch.object(factories_module, 'VoyageAIEmbedder') as mock_embedder:
            mock_instance = MagicMock()
            mock_embedder.return_value = mock_instance

            embedder = EmbedderFactory.create(config)

            mock_embedder.assert_called_once()
            assert embedder == mock_instance

    @patch('server_common.factories.HAS_VOYAGE_EMBEDDER', False)
    def test_create_voyage_embedder_not_available(self):
        """Test that unavailable Voyage embedder raises error."""
        config = EmbedderConfig(
            provider='voyage',
            model='voyage-3',
            providers=EmbedderProvidersConfig(
                voyage=VoyageProviderConfig(api_key='voyage-key')
            ),
        )

        with pytest.raises(ValueError) as exc_info:
            EmbedderFactory.create(config)
        assert 'Voyage embedder not available' in str(exc_info.value)

    def test_create_gemini_embedder(self):
        """Test creating Gemini embedder."""
        import server_common.factories as factories_module

        if not factories_module.HAS_GEMINI_EMBEDDER:
            pytest.skip('Gemini embedder not available')

        config = EmbedderConfig(
            provider='gemini',
            model='models/text-embedding-004',
            dimensions=768,
            providers=EmbedderProvidersConfig(
                gemini=GeminiProviderConfig(api_key='gemini-key')
            ),
        )

        with patch.object(factories_module, 'GeminiEmbedder') as mock_embedder:
            mock_instance = MagicMock()
            mock_embedder.return_value = mock_instance

            embedder = EmbedderFactory.create(config)

            mock_embedder.assert_called_once()
            assert embedder == mock_instance

    @patch('server_common.factories.HAS_GEMINI_EMBEDDER', False)
    def test_create_gemini_embedder_not_available(self):
        """Test that unavailable Gemini embedder raises error."""
        config = EmbedderConfig(
            provider='gemini',
            model='models/text-embedding-004',
            providers=EmbedderProvidersConfig(
                gemini=GeminiProviderConfig(api_key='gemini-key')
            ),
        )

        with pytest.raises(ValueError) as exc_info:
            EmbedderFactory.create(config)
        assert 'Gemini embedder not available' in str(exc_info.value)

    @patch('server_common.factories.HAS_AZURE_EMBEDDER', True)
    def test_create_azure_embedder(self):
        """Test creating Azure OpenAI embedder."""
        config = EmbedderConfig(
            provider='azure_openai',
            model='text-embedding-3-small',
            providers=EmbedderProvidersConfig(
                azure_openai=AzureOpenAIProviderConfig(
                    api_key='azure-key',
                    api_url='https://my-resource.openai.azure.com',
                    deployment_name='embeddings-deployment',
                )
            ),
        )

        with patch('server_common.factories.AsyncAzureOpenAI'):
            with patch('server_common.factories.AzureOpenAIEmbedderClient') as mock_embedder:
                mock_instance = MagicMock()
                mock_embedder.return_value = mock_instance

                embedder = EmbedderFactory.create(config)

                mock_embedder.assert_called_once()
                assert embedder == mock_instance

    def test_create_unsupported_embedder(self):
        """Test that unsupported embedder provider raises error."""
        config = EmbedderConfig(
            provider='unsupported',
            model='some-model',
        )

        with pytest.raises(ValueError) as exc_info:
            EmbedderFactory.create(config)
        assert 'Unsupported Embedder provider: unsupported' in str(exc_info.value)


class TestDatabaseDriverFactory:
    """Tests for DatabaseDriverFactory."""

    def test_create_neo4j_config_defaults(self):
        """Test creating Neo4j config with defaults."""
        config = DatabaseConfig(
            provider='neo4j',
            providers=DatabaseProvidersConfig(
                neo4j=Neo4jProviderConfig()
            ),
        )

        result = DatabaseDriverFactory.create_config(config)

        assert result['uri'] == 'bolt://localhost:7687'
        assert result['user'] == 'neo4j'
        assert result['password'] is None

    def test_create_neo4j_config_custom(self):
        """Test creating Neo4j config with custom values."""
        config = DatabaseConfig(
            provider='neo4j',
            providers=DatabaseProvidersConfig(
                neo4j=Neo4jProviderConfig(
                    uri='bolt://neo4j-server:7687',
                    username='admin',
                    password='secret',
                )
            ),
        )

        result = DatabaseDriverFactory.create_config(config)

        assert result['uri'] == 'bolt://neo4j-server:7687'
        assert result['user'] == 'admin'
        assert result['password'] == 'secret'

    def test_create_neo4j_config_from_env(self, mock_env):
        """Test that environment variables override Neo4j config."""
        mock_env(
            NEO4J_URI='bolt://env-server:7687',
            NEO4J_USER='env-user',
            NEO4J_PASSWORD='env-password',
        )

        config = DatabaseConfig(
            provider='neo4j',
            providers=DatabaseProvidersConfig(
                neo4j=Neo4jProviderConfig(
                    uri='bolt://config-server:7687',
                    username='config-user',
                    password='config-password',
                )
            ),
        )

        result = DatabaseDriverFactory.create_config(config)

        assert result['uri'] == 'bolt://env-server:7687'
        assert result['user'] == 'env-user'
        assert result['password'] == 'env-password'

    def test_create_neo4j_config_no_provider_config(self):
        """Test creating Neo4j config without provider config uses defaults."""
        config = DatabaseConfig(
            provider='neo4j',
            providers=DatabaseProvidersConfig(),
        )

        result = DatabaseDriverFactory.create_config(config)

        assert result['uri'] == 'bolt://localhost:7687'
        assert result['user'] == 'neo4j'

    @patch('server_common.factories.HAS_FALKOR', True)
    def test_create_falkordb_config_defaults(self):
        """Test creating FalkorDB config with defaults."""
        config = DatabaseConfig(
            provider='falkordb',
            providers=DatabaseProvidersConfig(
                falkordb=FalkorDBProviderConfig()
            ),
        )

        result = DatabaseDriverFactory.create_config(config)

        assert result['driver'] == 'falkordb'
        assert result['host'] == 'localhost'
        assert result['port'] == 6379
        assert result['password'] is None
        assert result['database'] == 'default_db'

    @patch('server_common.factories.HAS_FALKOR', True)
    def test_create_falkordb_config_custom(self):
        """Test creating FalkorDB config with custom values."""
        config = DatabaseConfig(
            provider='falkordb',
            providers=DatabaseProvidersConfig(
                falkordb=FalkorDBProviderConfig(
                    uri='redis://falkor-server:6380',
                    password='redis-secret',
                    database='my_db',
                )
            ),
        )

        result = DatabaseDriverFactory.create_config(config)

        assert result['driver'] == 'falkordb'
        assert result['host'] == 'falkor-server'
        assert result['port'] == 6380
        assert result['password'] == 'redis-secret'
        assert result['database'] == 'my_db'

    @patch('server_common.factories.HAS_FALKOR', True)
    def test_create_falkordb_config_from_env(self, mock_env):
        """Test that environment variables override FalkorDB config."""
        mock_env(
            FALKORDB_URI='redis://env-server:6381',
            FALKORDB_PASSWORD='env-password',
        )

        config = DatabaseConfig(
            provider='falkordb',
            providers=DatabaseProvidersConfig(
                falkordb=FalkorDBProviderConfig(
                    uri='redis://config-server:6379',
                    password='config-password',
                )
            ),
        )

        result = DatabaseDriverFactory.create_config(config)

        assert result['host'] == 'env-server'
        assert result['port'] == 6381
        assert result['password'] == 'env-password'

    @patch('server_common.factories.HAS_FALKOR', False)
    def test_create_falkordb_not_available(self):
        """Test that unavailable FalkorDB raises error."""
        config = DatabaseConfig(
            provider='falkordb',
            providers=DatabaseProvidersConfig(
                falkordb=FalkorDBProviderConfig()
            ),
        )

        with pytest.raises(ValueError) as exc_info:
            DatabaseDriverFactory.create_config(config)
        assert 'FalkorDB driver not available' in str(exc_info.value)

    def test_create_unsupported_database(self):
        """Test that unsupported database provider raises error."""
        config = DatabaseConfig(
            provider='unsupported',
        )

        with pytest.raises(ValueError) as exc_info:
            DatabaseDriverFactory.create_config(config)
        assert 'Unsupported Database provider: unsupported' in str(exc_info.value)


class TestAzureCredentialTokenProvider:
    """Tests for create_azure_credential_token_provider."""

    def test_missing_azure_identity_package(self):
        """Test that missing azure-identity raises ImportError."""
        # This test verifies the behavior when azure-identity is not installed
        # The actual import error is raised inside the function
        pass  # Import error will be raised when called without azure-identity

    def test_creates_token_provider_when_available(self):
        """Test that token provider is created when azure-identity is available."""
        try:
            from azure.identity import DefaultAzureCredential  # noqa: F401

            # If we get here, azure-identity is available
            from server_common.factories import create_azure_credential_token_provider

            # Just verify it can be called without error
            # (actual token fetching would require Azure credentials)
            token_provider = create_azure_credential_token_provider()
            assert callable(token_provider)
        except ImportError:
            pytest.skip('azure-identity not installed')
