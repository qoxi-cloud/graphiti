"""Tests for RetrieveService."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from graphiti_core.errors import EdgeNotFoundError, NodeNotFoundError
from graphiti_core.search.search_config import SearchResults


class TestSearch:
    """Tests for Search RPC."""

    @pytest.mark.asyncio
    async def test_search(self, mock_graphiti, sample_entity_edge):
        """Test Search RPC."""
        from src.generated.graphiti.v1 import retrieve_service_pb2
        from src.services.retrieve_service import RetrieveServiceServicer

        mock_graphiti.search.return_value = [sample_entity_edge]

        servicer = RetrieveServiceServicer(mock_graphiti)

        request = retrieve_service_pb2.SearchRequest(
            group_ids=['test-group'],
            query='test query',
            max_facts=10,
        )

        context = MagicMock()
        response = await servicer.Search(request, context)

        mock_graphiti.search.assert_called_once()
        assert len(response.facts) == 1
        assert response.facts[0].fact == sample_entity_edge.fact

    @pytest.mark.asyncio
    async def test_search_error(self, mock_graphiti, sample_entity_edge):
        """Test Search RPC error handling."""
        from src.generated.graphiti.v1 import retrieve_service_pb2
        from src.services.retrieve_service import RetrieveServiceServicer

        mock_graphiti.search = AsyncMock(side_effect=ValueError('Test error'))

        servicer = RetrieveServiceServicer(mock_graphiti)

        request = retrieve_service_pb2.SearchRequest(
            group_ids=['test-group'],
            query='test query',
            max_facts=10,
        )

        context = MagicMock()
        context.abort = AsyncMock()

        await servicer.Search(request, context)

        context.abort.assert_called_once()


class TestAdvancedSearch:
    """Tests for AdvancedSearch RPC."""

    @pytest.mark.asyncio
    async def test_advanced_search(self, mock_graphiti):
        """Test AdvancedSearch RPC."""
        from src.generated.graphiti.v1 import retrieve_service_pb2
        from src.services.retrieve_service import RetrieveServiceServicer

        mock_results = SearchResults(
            edges=[],
            edge_reranker_scores=[],
            nodes=[],
            node_reranker_scores=[],
            episodes=[],
            episode_reranker_scores=[],
            communities=[],
            community_reranker_scores=[],
        )
        mock_graphiti.search_.return_value = mock_results

        servicer = RetrieveServiceServicer(mock_graphiti)

        request = retrieve_service_pb2.AdvancedSearchRequest(
            group_ids=['test-group'],
            query='test query',
        )

        context = MagicMock()
        response = await servicer.AdvancedSearch(request, context)

        mock_graphiti.search_.assert_called_once()
        assert len(response.edges) == 0

    @pytest.mark.asyncio
    async def test_advanced_search_error(self, mock_graphiti):
        """Test AdvancedSearch RPC error handling."""
        from src.generated.graphiti.v1 import retrieve_service_pb2
        from src.services.retrieve_service import RetrieveServiceServicer

        mock_graphiti.search_ = AsyncMock(side_effect=RuntimeError('Search failed'))

        servicer = RetrieveServiceServicer(mock_graphiti)

        request = retrieve_service_pb2.AdvancedSearchRequest(
            group_ids=['test-group'],
            query='test query',
        )

        context = MagicMock()
        context.abort = AsyncMock()

        await servicer.AdvancedSearch(request, context)

        context.abort.assert_called_once()


class TestStreamSearch:
    """Tests for StreamSearch RPC."""

    @pytest.mark.asyncio
    async def test_stream_search(self, mock_graphiti, sample_entity_edge):
        """Test StreamSearch RPC."""
        from src.generated.graphiti.v1 import retrieve_service_pb2
        from src.services.retrieve_service import RetrieveServiceServicer

        mock_graphiti.search.return_value = [sample_entity_edge]

        servicer = RetrieveServiceServicer(mock_graphiti)

        request = retrieve_service_pb2.SearchRequest(
            group_ids=['test-group'],
            query='test query',
            max_facts=10,
        )

        context = MagicMock()

        chunks = []
        async for chunk in servicer.StreamSearch(request, context):
            chunks.append(chunk)

        assert len(chunks) == 1
        assert chunks[0].is_last is True

    @pytest.mark.asyncio
    async def test_stream_search_error(self, mock_graphiti, sample_entity_edge):
        """Test StreamSearch RPC error handling."""
        from src.generated.graphiti.v1 import retrieve_service_pb2
        from src.services.retrieve_service import RetrieveServiceServicer

        mock_graphiti.search = AsyncMock(side_effect=RuntimeError('Stream search failed'))

        servicer = RetrieveServiceServicer(mock_graphiti)

        request = retrieve_service_pb2.SearchRequest(
            group_ids=['test-group'],
            query='test query',
            max_facts=10,
        )

        context = MagicMock()
        context.abort = AsyncMock()

        chunks = []
        async for chunk in servicer.StreamSearch(request, context):
            chunks.append(chunk)

        context.abort.assert_called_once()


class TestGetEntityEdge:
    """Tests for GetEntityEdge RPC."""

    @pytest.mark.asyncio
    async def test_get_entity_edge(self, mock_graphiti, sample_entity_edge):
        """Test GetEntityEdge RPC."""
        from src.generated.graphiti.v1 import retrieve_service_pb2
        from src.services.retrieve_service import RetrieveServiceServicer

        servicer = RetrieveServiceServicer(mock_graphiti)

        request = retrieve_service_pb2.GetEntityEdgeRequest(uuid='test-uuid')
        context = MagicMock()

        with patch(
            'graphiti_core.edges.EntityEdge.get_by_uuid',
            new=AsyncMock(return_value=sample_entity_edge),
        ):
            response = await servicer.GetEntityEdge(request, context)

        assert response.uuid == sample_entity_edge.uuid

    @pytest.mark.asyncio
    async def test_get_entity_edge_not_found(self, mock_graphiti, sample_entity_edge):
        """Test GetEntityEdge RPC when edge not found."""
        from src.generated.graphiti.v1 import retrieve_service_pb2
        from src.services.retrieve_service import RetrieveServiceServicer

        mock_graphiti.get_entity_edge = AsyncMock(side_effect=EdgeNotFoundError('test-uuid'))

        servicer = RetrieveServiceServicer(mock_graphiti)

        request = retrieve_service_pb2.GetEntityEdgeRequest(uuid='test-uuid')
        context = MagicMock()
        context.abort = AsyncMock()

        await servicer.GetEntityEdge(request, context)

        context.abort.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_entity_edge_general_error(self, mock_graphiti):
        """Test GetEntityEdge RPC with general error."""
        from src.generated.graphiti.v1 import retrieve_service_pb2
        from src.services.retrieve_service import RetrieveServiceServicer

        servicer = RetrieveServiceServicer(mock_graphiti)

        request = retrieve_service_pb2.GetEntityEdgeRequest(uuid='test-uuid')
        context = MagicMock()
        context.abort = AsyncMock()

        with patch(
            'graphiti_core.edges.EntityEdge.get_by_uuid',
            new=AsyncMock(side_effect=RuntimeError('Database error')),
        ):
            await servicer.GetEntityEdge(request, context)

        context.abort.assert_called_once()


class TestGetEntityEdges:
    """Tests for GetEntityEdges RPC."""

    @pytest.mark.asyncio
    async def test_get_entity_edges(self, mock_graphiti, sample_entity_edge):
        """Test GetEntityEdges RPC."""
        from src.generated.graphiti.v1 import retrieve_service_pb2
        from src.services.retrieve_service import RetrieveServiceServicer

        servicer = RetrieveServiceServicer(mock_graphiti)

        request = retrieve_service_pb2.GetEntityEdgesRequest(uuids=['uuid1', 'uuid2'])
        context = MagicMock()

        with patch(
            'graphiti_core.edges.EntityEdge.get_by_uuids',
            new=AsyncMock(return_value=[sample_entity_edge, sample_entity_edge]),
        ):
            response = await servicer.GetEntityEdges(request, context)

        assert len(response.edges) == 2

    @pytest.mark.asyncio
    async def test_get_entity_edges_error(self, mock_graphiti):
        """Test GetEntityEdges RPC with error."""
        from src.generated.graphiti.v1 import retrieve_service_pb2
        from src.services.retrieve_service import RetrieveServiceServicer

        servicer = RetrieveServiceServicer(mock_graphiti)

        request = retrieve_service_pb2.GetEntityEdgesRequest(uuids=['uuid1', 'uuid2'])
        context = MagicMock()
        context.abort = AsyncMock()

        with patch(
            'graphiti_core.edges.EntityEdge.get_by_uuids',
            new=AsyncMock(side_effect=RuntimeError('Batch get failed')),
        ):
            await servicer.GetEntityEdges(request, context)

        context.abort.assert_called_once()


class TestGetEpisodes:
    """Tests for GetEpisodes RPC."""

    @pytest.mark.asyncio
    async def test_get_episodes(self, mock_graphiti, sample_episodic_node):
        """Test GetEpisodes RPC."""
        from src.generated.graphiti.v1 import retrieve_service_pb2
        from src.services.retrieve_service import RetrieveServiceServicer

        mock_graphiti.retrieve_episodes.return_value = [sample_episodic_node]

        servicer = RetrieveServiceServicer(mock_graphiti)

        request = retrieve_service_pb2.GetEpisodesRequest(
            group_id='test-group',
            last_n=10,
        )

        context = MagicMock()
        response = await servicer.GetEpisodes(request, context)

        mock_graphiti.retrieve_episodes.assert_called_once()
        assert len(response.episodes) == 1

    @pytest.mark.asyncio
    async def test_get_episodes_error(self, mock_graphiti):
        """Test GetEpisodes RPC with error."""
        from src.generated.graphiti.v1 import retrieve_service_pb2
        from src.services.retrieve_service import RetrieveServiceServicer

        mock_graphiti.retrieve_episodes = AsyncMock(
            side_effect=RuntimeError('Retrieve episodes failed')
        )

        servicer = RetrieveServiceServicer(mock_graphiti)

        request = retrieve_service_pb2.GetEpisodesRequest(
            group_id='test-group',
            last_n=10,
        )

        context = MagicMock()
        context.abort = AsyncMock()

        await servicer.GetEpisodes(request, context)

        context.abort.assert_called_once()


class TestGetMemory:
    """Tests for GetMemory RPC."""

    @pytest.mark.asyncio
    async def test_get_memory(self, mock_graphiti, sample_entity_edge):
        """Test GetMemory RPC."""
        from src.generated.graphiti.v1 import common_pb2, retrieve_service_pb2
        from src.services.retrieve_service import RetrieveServiceServicer

        mock_graphiti.search.return_value = [sample_entity_edge]

        servicer = RetrieveServiceServicer(mock_graphiti)

        message = common_pb2.Message(
            name='User',
            role='user',
            role_type='user',
            content='What do you know about X?',
        )

        request = retrieve_service_pb2.GetMemoryRequest(
            group_id='test-group',
            max_facts=10,
            messages=[message],
        )

        context = MagicMock()
        response = await servicer.GetMemory(request, context)

        mock_graphiti.search.assert_called_once()
        assert len(response.facts) == 1

    @pytest.mark.asyncio
    async def test_get_memory_error(self, mock_graphiti):
        """Test GetMemory RPC with error."""
        from src.generated.graphiti.v1 import common_pb2, retrieve_service_pb2
        from src.services.retrieve_service import RetrieveServiceServicer

        mock_graphiti.search = AsyncMock(side_effect=RuntimeError('Memory retrieval failed'))

        servicer = RetrieveServiceServicer(mock_graphiti)

        message = common_pb2.Message(
            name='User',
            role='user',
            role_type='user',
            content='What do you know about X?',
        )

        request = retrieve_service_pb2.GetMemoryRequest(
            group_id='test-group',
            max_facts=10,
            messages=[message],
        )

        context = MagicMock()
        context.abort = AsyncMock()

        await servicer.GetMemory(request, context)

        context.abort.assert_called_once()


class TestGetEntityNode:
    """Tests for GetEntityNode RPC."""

    @pytest.mark.asyncio
    async def test_get_entity_node(self, mock_graphiti, sample_entity_node):
        """Test GetEntityNode RPC."""
        from src.generated.graphiti.v1 import retrieve_service_pb2
        from src.services.retrieve_service import RetrieveServiceServicer

        servicer = RetrieveServiceServicer(mock_graphiti)

        request = retrieve_service_pb2.GetEntityNodeRequest(uuid='test-uuid')
        context = MagicMock()

        with patch(
            'graphiti_core.nodes.EntityNode.get_by_uuid',
            new=AsyncMock(return_value=sample_entity_node),
        ):
            response = await servicer.GetEntityNode(request, context)

        assert response.uuid == sample_entity_node.uuid

    @pytest.mark.asyncio
    async def test_get_entity_node_error(self, mock_graphiti):
        """Test GetEntityNode RPC with error."""
        from src.generated.graphiti.v1 import retrieve_service_pb2
        from src.services.retrieve_service import RetrieveServiceServicer

        servicer = RetrieveServiceServicer(mock_graphiti)

        request = retrieve_service_pb2.GetEntityNodeRequest(uuid='test-uuid')
        context = MagicMock()
        context.abort = AsyncMock()

        with patch(
            'graphiti_core.nodes.EntityNode.get_by_uuid',
            new=AsyncMock(side_effect=NodeNotFoundError('test-uuid')),
        ):
            await servicer.GetEntityNode(request, context)

        context.abort.assert_called_once()


class TestGetEntityNodes:
    """Tests for GetEntityNodes RPC."""

    @pytest.mark.asyncio
    async def test_get_entity_nodes(self, mock_graphiti, sample_entity_node):
        """Test GetEntityNodes RPC."""
        from src.generated.graphiti.v1 import retrieve_service_pb2
        from src.services.retrieve_service import RetrieveServiceServicer

        servicer = RetrieveServiceServicer(mock_graphiti)

        request = retrieve_service_pb2.GetEntityNodesRequest(group_ids=['test-group'])
        context = MagicMock()

        with patch(
            'graphiti_core.nodes.EntityNode.get_by_group_ids',
            new=AsyncMock(return_value=[sample_entity_node]),
        ):
            response = await servicer.GetEntityNodes(request, context)

        assert len(response.nodes) == 1

    @pytest.mark.asyncio
    async def test_get_entity_nodes_error(self, mock_graphiti):
        """Test GetEntityNodes RPC with error."""
        from src.generated.graphiti.v1 import retrieve_service_pb2
        from src.services.retrieve_service import RetrieveServiceServicer

        servicer = RetrieveServiceServicer(mock_graphiti)

        request = retrieve_service_pb2.GetEntityNodesRequest(group_ids=['test-group'])
        context = MagicMock()
        context.abort = AsyncMock()

        with patch(
            'graphiti_core.nodes.EntityNode.get_by_group_ids',
            new=AsyncMock(side_effect=RuntimeError('Batch get nodes failed')),
        ):
            await servicer.GetEntityNodes(request, context)

        context.abort.assert_called_once()


class TestGetCommunities:
    """Tests for GetCommunities RPC."""

    @pytest.mark.asyncio
    async def test_get_communities(self, mock_graphiti, sample_community_node):
        """Test GetCommunities RPC."""
        from src.generated.graphiti.v1 import retrieve_service_pb2
        from src.services.retrieve_service import RetrieveServiceServicer

        servicer = RetrieveServiceServicer(mock_graphiti)

        request = retrieve_service_pb2.GetCommunitiesRequest(group_ids=['test-group'])
        context = MagicMock()

        with patch(
            'graphiti_core.nodes.CommunityNode.get_by_group_ids',
            new=AsyncMock(return_value=[sample_community_node]),
        ):
            response = await servicer.GetCommunities(request, context)

        assert len(response.communities) == 1

    @pytest.mark.asyncio
    async def test_get_communities_error(self, mock_graphiti):
        """Test GetCommunities RPC with error."""
        from src.generated.graphiti.v1 import retrieve_service_pb2
        from src.services.retrieve_service import RetrieveServiceServicer

        servicer = RetrieveServiceServicer(mock_graphiti)

        request = retrieve_service_pb2.GetCommunitiesRequest(group_ids=['test-group'])
        context = MagicMock()
        context.abort = AsyncMock()

        with patch(
            'graphiti_core.nodes.CommunityNode.get_by_group_ids',
            new=AsyncMock(side_effect=RuntimeError('Get communities failed')),
        ):
            await servicer.GetCommunities(request, context)

        context.abort.assert_called_once()


class TestRetrieveEpisodes:
    """Tests for RetrieveEpisodes RPC (streaming)."""

    @pytest.mark.asyncio
    async def test_retrieve_episodes(self, mock_graphiti, sample_episodic_node):
        """Test RetrieveEpisodes streaming RPC."""
        from src.generated.graphiti.v1 import retrieve_service_pb2
        from src.services.retrieve_service import RetrieveServiceServicer

        mock_graphiti.retrieve_episodes.return_value = [sample_episodic_node]

        servicer = RetrieveServiceServicer(mock_graphiti)

        request = retrieve_service_pb2.RetrieveEpisodesRequest(
            group_ids=['test-group'],
            last_n=10,
        )

        context = MagicMock()

        episodes = []
        async for episode in servicer.RetrieveEpisodes(request, context):
            episodes.append(episode)

        mock_graphiti.retrieve_episodes.assert_called_once()
        assert len(episodes) == 1
        assert episodes[0].uuid == sample_episodic_node.uuid

    @pytest.mark.asyncio
    async def test_retrieve_episodes_error(self, mock_graphiti):
        """Test RetrieveEpisodes RPC with error."""
        from src.generated.graphiti.v1 import retrieve_service_pb2
        from src.services.retrieve_service import RetrieveServiceServicer

        mock_graphiti.retrieve_episodes = AsyncMock(
            side_effect=RuntimeError('Retrieve episodes failed')
        )

        servicer = RetrieveServiceServicer(mock_graphiti)

        request = retrieve_service_pb2.RetrieveEpisodesRequest(
            group_ids=['test-group'],
            last_n=10,
        )

        context = MagicMock()
        context.abort = AsyncMock()

        episodes = []
        async for episode in servicer.RetrieveEpisodes(request, context):
            episodes.append(episode)

        context.abort.assert_called_once()


class TestGetNodesByEpisodes:
    """Tests for GetNodesByEpisodes RPC."""

    @pytest.mark.asyncio
    async def test_get_nodes_by_episodes(self, mock_graphiti, sample_entity_node, sample_entity_edge):
        """Test GetNodesByEpisodes RPC."""
        from graphiti_core.edges import EpisodicEdge

        from src.generated.graphiti.v1 import retrieve_service_pb2
        from src.services.retrieve_service import RetrieveServiceServicer

        mock_episodic_edge = MagicMock(spec=EpisodicEdge)
        mock_episodic_edge.target_node_uuid = sample_entity_node.uuid

        servicer = RetrieveServiceServicer(mock_graphiti)

        request = retrieve_service_pb2.GetNodesByEpisodesRequest(
            episode_uuids=['episode-uuid-1']
        )
        context = MagicMock()

        with patch(
            'graphiti_core.edges.EpisodicEdge.get_by_uuids',
            new=AsyncMock(return_value=[mock_episodic_edge]),
        ), patch(
            'graphiti_core.nodes.EntityNode.get_by_uuid',
            new=AsyncMock(return_value=sample_entity_node),
        ), patch(
            'graphiti_core.edges.EntityEdge.get_by_node_uuid',
            new=AsyncMock(return_value=[sample_entity_edge]),
        ):
            response = await servicer.GetNodesByEpisodes(request, context)

        assert len(response.nodes) == 1
        assert len(response.edges) == 1

    @pytest.mark.asyncio
    async def test_get_nodes_by_episodes_error(self, mock_graphiti):
        """Test GetNodesByEpisodes RPC with error."""
        from src.generated.graphiti.v1 import retrieve_service_pb2
        from src.services.retrieve_service import RetrieveServiceServicer

        servicer = RetrieveServiceServicer(mock_graphiti)

        request = retrieve_service_pb2.GetNodesByEpisodesRequest(
            episode_uuids=['episode-uuid-1']
        )
        context = MagicMock()
        context.abort = AsyncMock()

        with patch(
            'graphiti_core.edges.EpisodicEdge.get_by_uuids',
            new=AsyncMock(side_effect=RuntimeError('Get episodic edges failed')),
        ):
            await servicer.GetNodesByEpisodes(request, context)

        context.abort.assert_called_once()


class TestSearchNodes:
    """Tests for SearchNodes RPC."""

    @pytest.mark.asyncio
    async def test_search_nodes(self, mock_graphiti, sample_entity_node):
        """Test SearchNodes RPC."""
        from graphiti_core.search.search_config import SearchResults

        from src.generated.graphiti.v1 import retrieve_service_pb2
        from src.services.retrieve_service import RetrieveServiceServicer

        mock_results = SearchResults(
            edges=[],
            edge_reranker_scores=[],
            nodes=[sample_entity_node],
            node_reranker_scores=[0.9],
            episodes=[],
            episode_reranker_scores=[],
            communities=[],
            community_reranker_scores=[],
        )
        mock_graphiti.search_.return_value = mock_results

        servicer = RetrieveServiceServicer(mock_graphiti)

        request = retrieve_service_pb2.SearchNodesRequest(
            query='test query',
            group_ids=['test-group'],
            max_nodes=10,
            entity_types=['Person'],
        )

        context = MagicMock()
        response = await servicer.SearchNodes(request, context)

        mock_graphiti.search_.assert_called_once()
        assert len(response.nodes) == 1
        assert 'Found 1 nodes' in response.message

    @pytest.mark.asyncio
    async def test_search_nodes_error(self, mock_graphiti):
        """Test SearchNodes RPC with error."""
        from src.generated.graphiti.v1 import retrieve_service_pb2
        from src.services.retrieve_service import RetrieveServiceServicer

        mock_graphiti.search_ = AsyncMock(side_effect=RuntimeError('Search nodes failed'))

        servicer = RetrieveServiceServicer(mock_graphiti)

        request = retrieve_service_pb2.SearchNodesRequest(
            query='test query',
            group_ids=['test-group'],
        )

        context = MagicMock()
        context.abort = AsyncMock()

        await servicer.SearchNodes(request, context)

        context.abort.assert_called_once()


class TestSearchFacts:
    """Tests for SearchFacts RPC."""

    @pytest.mark.asyncio
    async def test_search_facts(self, mock_graphiti, sample_entity_edge):
        """Test SearchFacts RPC."""
        from src.generated.graphiti.v1 import retrieve_service_pb2
        from src.services.retrieve_service import RetrieveServiceServicer

        mock_graphiti.search.return_value = [sample_entity_edge]

        servicer = RetrieveServiceServicer(mock_graphiti)

        request = retrieve_service_pb2.SearchFactsRequest(
            query='test query',
            group_ids=['test-group'],
            max_facts=10,
        )

        context = MagicMock()
        response = await servicer.SearchFacts(request, context)

        mock_graphiti.search.assert_called_once()
        assert len(response.facts) == 1
        assert 'Found 1 facts' in response.message

    @pytest.mark.asyncio
    async def test_search_facts_with_center_node(self, mock_graphiti, sample_entity_edge):
        """Test SearchFacts RPC with center node."""
        from src.generated.graphiti.v1 import retrieve_service_pb2
        from src.services.retrieve_service import RetrieveServiceServicer

        mock_graphiti.search.return_value = [sample_entity_edge]

        servicer = RetrieveServiceServicer(mock_graphiti)

        request = retrieve_service_pb2.SearchFactsRequest(
            query='test query',
            group_ids=['test-group'],
            max_facts=10,
            center_node_uuid='center-uuid',
        )

        context = MagicMock()
        await servicer.SearchFacts(request, context)

        mock_graphiti.search.assert_called_once()
        call_kwargs = mock_graphiti.search.call_args[1]
        assert call_kwargs['center_node_uuid'] == 'center-uuid'

    @pytest.mark.asyncio
    async def test_search_facts_error(self, mock_graphiti):
        """Test SearchFacts RPC with error."""
        from src.generated.graphiti.v1 import retrieve_service_pb2
        from src.services.retrieve_service import RetrieveServiceServicer

        mock_graphiti.search = AsyncMock(side_effect=RuntimeError('Search facts failed'))

        servicer = RetrieveServiceServicer(mock_graphiti)

        request = retrieve_service_pb2.SearchFactsRequest(
            query='test query',
            group_ids=['test-group'],
        )

        context = MagicMock()
        context.abort = AsyncMock()

        await servicer.SearchFacts(request, context)

        context.abort.assert_called_once()
