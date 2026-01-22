"""Tests for main module."""

import argparse
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestParseArgs:
    """Tests for parse_args function."""

    def test_parse_args_defaults(self):
        """Test parsing with no arguments."""
        from src.main import parse_args

        with patch('sys.argv', ['main.py']):
            args = parse_args()

        assert args.host is None
        assert args.port is None
        assert args.max_workers is None

    def test_parse_args_server_options(self):
        """Test parsing server options."""
        from src.main import parse_args

        with patch(
            'sys.argv', ['main.py', '--host', '0.0.0.0', '--port', '50051', '--max-workers', '10']
        ):
            args = parse_args()

        assert args.host == '0.0.0.0'
        assert args.port == 50051
        assert args.max_workers == 10

    def test_parse_args_llm_options(self):
        """Test parsing LLM options."""
        from src.main import parse_args

        with patch(
            'sys.argv',
            ['main.py', '--llm-provider', 'openai', '--model', 'gpt-4', '--temperature', '0.7'],
        ):
            args = parse_args()

        assert args.llm_provider == 'openai'
        assert args.model == 'gpt-4'
        assert args.temperature == 0.7

    def test_parse_args_embedder_options(self):
        """Test parsing embedder options."""
        from src.main import parse_args

        with patch(
            'sys.argv',
            [
                'main.py',
                '--embedder-provider',
                'openai',
                '--embedder-model',
                'text-embedding-3-small',
            ],
        ):
            args = parse_args()

        assert args.embedder_provider == 'openai'
        assert args.embedder_model == 'text-embedding-3-small'

    def test_parse_args_database_options(self):
        """Test parsing database options."""
        from src.main import parse_args

        with patch('sys.argv', ['main.py', '--database-provider', 'neo4j']):
            args = parse_args()

        assert args.database_provider == 'neo4j'

    def test_parse_args_graphiti_options(self):
        """Test parsing graphiti options."""
        from src.main import parse_args

        with patch('sys.argv', ['main.py', '--group-id', 'my-group', '--user-id', 'my-user']):
            args = parse_args()

        assert args.group_id == 'my-group'
        assert args.user_id == 'my-user'


class TestCreateGraphitiClient:
    """Tests for create_graphiti_client function."""

    @pytest.mark.asyncio
    async def test_create_graphiti_client_neo4j(self, mock_config):
        """Test creating Graphiti client with Neo4j."""
        from src.main import create_graphiti_client

        mock_config.database.provider = 'neo4j'

        mock_llm = MagicMock()
        mock_embedder = MagicMock()
        mock_graphiti = MagicMock()
        mock_graphiti.build_indices_and_constraints = AsyncMock()

        with (
            patch('src.main.LLMClientFactory.create', return_value=mock_llm),
            patch('src.main.EmbedderFactory.create', return_value=mock_embedder),
            patch(
                'src.main.DatabaseDriverFactory.create_config',
                return_value={
                    'uri': 'bolt://localhost:7687',
                    'user': 'neo4j',
                    'password': 'password',
                },
            ),
            patch('src.main.Graphiti', return_value=mock_graphiti) as mock_graphiti_class,
        ):
            client = await create_graphiti_client(mock_config)

            mock_graphiti_class.assert_called_once()
            mock_graphiti.build_indices_and_constraints.assert_called_once()
            assert client == mock_graphiti

    @pytest.mark.asyncio
    async def test_create_graphiti_client_falkordb(self, mock_config):
        """Test creating Graphiti client with FalkorDB."""
        from src.main import create_graphiti_client

        mock_config.database.provider = 'falkordb'

        mock_llm = MagicMock()
        mock_embedder = MagicMock()
        mock_driver = MagicMock()
        mock_graphiti = MagicMock()
        mock_graphiti.build_indices_and_constraints = AsyncMock()

        # Patch at the import location within src.main
        with (
            patch('src.main.LLMClientFactory.create', return_value=mock_llm),
            patch('src.main.EmbedderFactory.create', return_value=mock_embedder),
            patch(
                'src.main.DatabaseDriverFactory.create_config',
                return_value={
                    'driver': 'falkordb',
                    'host': 'localhost',
                    'port': 6379,
                    'password': None,
                    'database': 'default_db',
                },
            ),
            patch.dict(
                'sys.modules',
                {
                    'graphiti_core.driver.falkordb_driver': MagicMock(
                        FalkorDriver=MagicMock(return_value=mock_driver)
                    )
                },
            ),
            patch('src.main.Graphiti', return_value=mock_graphiti) as mock_graphiti_class,
        ):
            client = await create_graphiti_client(mock_config)

            mock_graphiti_class.assert_called_once()
            mock_graphiti.build_indices_and_constraints.assert_called_once()
            assert client == mock_graphiti

    @pytest.mark.asyncio
    async def test_create_graphiti_client_unsupported_provider(self, mock_config):
        """Test creating Graphiti client with unsupported provider."""
        from src.main import create_graphiti_client

        mock_config.database.provider = 'unknown'

        mock_llm = MagicMock()
        mock_embedder = MagicMock()

        with (
            patch('src.main.LLMClientFactory.create', return_value=mock_llm),
            patch('src.main.EmbedderFactory.create', return_value=mock_embedder),
            patch('src.main.DatabaseDriverFactory.create_config', return_value={}),
            pytest.raises(ValueError, match='Unsupported database provider'),
        ):
            await create_graphiti_client(mock_config)


class TestConfigOverrides:
    """Tests for CLI config overrides."""

    def test_apply_cli_overrides_host(self):
        """Test applying host override."""
        from src.config.schema import GraphitiGRPCConfig

        config = GraphitiGRPCConfig()
        args = argparse.Namespace(
            host='192.168.1.1',
            port=None,
            max_workers=None,
            llm_provider=None,
            model=None,
            temperature=None,
            embedder_provider=None,
            embedder_model=None,
            database_provider=None,
            group_id=None,
            user_id=None,
        )
        config.apply_cli_overrides(args)

        assert config.grpc.host == '192.168.1.1'

    def test_apply_cli_overrides_port(self):
        """Test applying port override."""
        from src.config.schema import GraphitiGRPCConfig

        config = GraphitiGRPCConfig()
        args = argparse.Namespace(
            host=None,
            port=8080,
            max_workers=None,
            llm_provider=None,
            model=None,
            temperature=None,
            embedder_provider=None,
            embedder_model=None,
            database_provider=None,
            group_id=None,
            user_id=None,
        )
        config.apply_cli_overrides(args)

        assert config.grpc.port == 8080

    def test_apply_cli_overrides_max_workers(self):
        """Test applying max_workers override."""
        from src.config.schema import GraphitiGRPCConfig

        config = GraphitiGRPCConfig()
        args = argparse.Namespace(
            host=None,
            port=None,
            max_workers=20,
            llm_provider=None,
            model=None,
            temperature=None,
            embedder_provider=None,
            embedder_model=None,
            database_provider=None,
            group_id=None,
            user_id=None,
        )
        config.apply_cli_overrides(args)

        assert config.grpc.max_workers == 20

    def test_apply_cli_overrides_llm(self):
        """Test applying LLM overrides."""
        from src.config.schema import GraphitiGRPCConfig

        config = GraphitiGRPCConfig()
        args = argparse.Namespace(
            host=None,
            port=None,
            max_workers=None,
            llm_provider='anthropic',
            model='claude-3',
            temperature=0.5,
            embedder_provider=None,
            embedder_model=None,
            database_provider=None,
            group_id=None,
            user_id=None,
        )
        config.apply_cli_overrides(args)

        assert config.llm.provider == 'anthropic'
        assert config.llm.model == 'claude-3'
        assert config.llm.temperature == 0.5

    def test_apply_cli_overrides_embedder(self):
        """Test applying embedder overrides."""
        from src.config.schema import GraphitiGRPCConfig

        config = GraphitiGRPCConfig()
        args = argparse.Namespace(
            host=None,
            port=None,
            max_workers=None,
            llm_provider=None,
            model=None,
            temperature=None,
            embedder_provider='voyage',
            embedder_model='voyage-3',
            database_provider=None,
            group_id=None,
            user_id=None,
        )
        config.apply_cli_overrides(args)

        assert config.embedder.provider == 'voyage'
        assert config.embedder.model == 'voyage-3'

    def test_apply_cli_overrides_database(self):
        """Test applying database overrides."""
        from src.config.schema import GraphitiGRPCConfig

        config = GraphitiGRPCConfig()
        args = argparse.Namespace(
            host=None,
            port=None,
            max_workers=None,
            llm_provider=None,
            model=None,
            temperature=None,
            embedder_provider=None,
            embedder_model=None,
            database_provider='neo4j',
            group_id=None,
            user_id=None,
        )
        config.apply_cli_overrides(args)

        assert config.database.provider == 'neo4j'

    def test_apply_cli_overrides_graphiti(self):
        """Test applying graphiti overrides."""
        from src.config.schema import GraphitiGRPCConfig

        config = GraphitiGRPCConfig()
        args = argparse.Namespace(
            host=None,
            port=None,
            max_workers=None,
            llm_provider=None,
            model=None,
            temperature=None,
            embedder_provider=None,
            embedder_model=None,
            database_provider=None,
            group_id='custom-group',
            user_id='custom-user',
        )
        config.apply_cli_overrides(args)

        assert config.graphiti.group_id == 'custom-group'
        assert config.graphiti.user_id == 'custom-user'


class TestMain:
    """Tests for main function."""

    def test_main_keyboard_interrupt(self):
        """Test main handles KeyboardInterrupt."""
        from src.main import main

        with (
            patch('sys.argv', ['main.py']),
            patch('src.main.GraphitiGRPCConfig'),
            patch('asyncio.run', side_effect=KeyboardInterrupt()),
            patch('sys.exit') as mock_exit,
        ):
            main()
            mock_exit.assert_called_once_with(0)

    def test_main_exception(self):
        """Test main handles exceptions."""
        from src.main import main

        with (
            patch('sys.argv', ['main.py']),
            patch('src.main.GraphitiGRPCConfig'),
            patch('asyncio.run', side_effect=Exception('Test error')),
            patch('sys.exit') as mock_exit,
        ):
            main()
            mock_exit.assert_called_once_with(1)
