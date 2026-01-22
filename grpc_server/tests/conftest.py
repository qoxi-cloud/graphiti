"""Pytest fixtures for gRPC server tests."""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from graphiti_core.edges import EntityEdge
from graphiti_core.nodes import EntityNode, EpisodeType, EpisodicNode


@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_graphiti():
    """Create a mock Graphiti client."""
    graphiti = MagicMock()
    graphiti.driver = MagicMock()
    graphiti.driver.execute_query = AsyncMock(return_value=([], None, None))

    # Mock add_episode
    graphiti.add_episode = AsyncMock()

    # Mock search
    graphiti.search = AsyncMock(return_value=[])
    graphiti.search_ = AsyncMock()

    # Mock other methods
    graphiti.save_entity_node = AsyncMock()
    graphiti.add_triplet = AsyncMock()
    graphiti.get_entity_edge = AsyncMock()
    graphiti.retrieve_episodes = AsyncMock(return_value=[])
    graphiti.delete_entity_edge = AsyncMock()
    graphiti.delete_group = AsyncMock()
    graphiti.delete_episodic_node = AsyncMock()
    graphiti.build_indices_and_constraints = AsyncMock()

    return graphiti


@pytest.fixture
def sample_entity_node():
    """Create a sample EntityNode."""
    return EntityNode(
        uuid='test-node-uuid',
        name='Test Entity',
        group_id='test-group',
        labels=['Entity', 'TestType'],
        created_at=datetime.now(timezone.utc),
        summary='A test entity',
        attributes={'key': 'value'},
    )


@pytest.fixture
def sample_episodic_node():
    """Create a sample EpisodicNode."""
    return EpisodicNode(
        uuid='test-episode-uuid',
        name='Test Episode',
        group_id='test-group',
        labels=['Episodic'],
        created_at=datetime.now(timezone.utc),
        source=EpisodeType.message,
        source_description='Test source',
        content='Test content',
        valid_at=datetime.now(timezone.utc),
        entity_edges=['edge-1', 'edge-2'],
    )


@pytest.fixture
def sample_entity_edge():
    """Create a sample EntityEdge."""
    return EntityEdge(
        uuid='test-edge-uuid',
        group_id='test-group',
        source_node_uuid='source-node-uuid',
        target_node_uuid='target-node-uuid',
        created_at=datetime.now(timezone.utc),
        name='RELATES_TO',
        fact='Test fact',
        episodes=['episode-1'],
        valid_at=datetime.now(timezone.utc),
        invalid_at=None,
        expired_at=None,
        attributes={},
    )


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    from src.config.schema import (
        DatabaseConfig,
        EmbedderConfig,
        GraphitiAppConfig,
        GraphitiGRPCConfig,
        GRPCServerConfig,
        LLMConfig,
    )

    return GraphitiGRPCConfig(
        grpc=GRPCServerConfig(
            host='0.0.0.0',
            port=50051,
            max_workers=10,
            enable_tls=False,
            enable_reflection=True,
        ),
        llm=LLMConfig(
            provider='openai',
            model='gpt-4o-mini',
        ),
        embedder=EmbedderConfig(
            provider='openai',
            model='text-embedding-3-small',
        ),
        database=DatabaseConfig(
            provider='falkordb',
        ),
        graphiti=GraphitiAppConfig(
            group_id='test',
            user_id='test-user',
        ),
    )


@pytest.fixture
def sample_community_node():
    """Create a sample CommunityNode."""
    from graphiti_core.nodes import CommunityNode

    return CommunityNode(
        uuid='test-community-uuid',
        name='Test Community',
        group_id='test-group',
        labels=['Community'],
        created_at=datetime.now(timezone.utc),
        summary='A test community',
    )


@pytest.fixture
def sample_episodic_edge():
    """Create a sample EpisodicEdge."""
    from graphiti_core.edges import EpisodicEdge

    return EpisodicEdge(
        uuid='test-episodic-edge-uuid',
        group_id='test-group',
        source_node_uuid='source-uuid',
        target_node_uuid='target-uuid',
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_community_edge():
    """Create a sample CommunityEdge."""
    from graphiti_core.edges import CommunityEdge

    return CommunityEdge(
        uuid='test-community-edge-uuid',
        group_id='test-group',
        source_node_uuid='source-uuid',
        target_node_uuid='target-uuid',
        created_at=datetime.now(timezone.utc),
    )
