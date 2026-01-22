"""Tests for AdminService."""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from graphiti_core.errors import EdgeNotFoundError, GroupsEdgesNotFoundError, NodeNotFoundError


class TestHealthCheck:
    """Tests for HealthCheck RPC."""

    @pytest.mark.asyncio
    async def test_health_check(self, mock_graphiti, mock_config):
        """Test HealthCheck RPC."""
        from src.generated.graphiti.v1 import admin_service_pb2
        from src.services.admin_service import AdminServiceServicer

        start_time = time.time()
        servicer = AdminServiceServicer(mock_graphiti, mock_config, start_time)

        request = admin_service_pb2.HealthCheckRequest()
        context = MagicMock()

        response = await servicer.HealthCheck(request, context)

        assert response.status == admin_service_pb2.HealthCheckResponse.SERVING_STATUS_SERVING
        assert response.message == 'Healthy'

    @pytest.mark.asyncio
    async def test_health_check_database_error(self, mock_graphiti, mock_config):
        """Test HealthCheck RPC when database is unavailable."""
        from src.generated.graphiti.v1 import admin_service_pb2
        from src.services.admin_service import AdminServiceServicer

        mock_graphiti.driver.execute_query = AsyncMock(side_effect=Exception('Connection failed'))

        start_time = time.time()
        servicer = AdminServiceServicer(mock_graphiti, mock_config, start_time)

        request = admin_service_pb2.HealthCheckRequest()
        context = MagicMock()

        response = await servicer.HealthCheck(request, context)

        assert response.status == admin_service_pb2.HealthCheckResponse.SERVING_STATUS_NOT_SERVING
        assert 'Connection failed' in response.message


class TestGetStatus:
    """Tests for GetStatus RPC."""

    @pytest.mark.asyncio
    async def test_get_status(self, mock_graphiti, mock_config):
        """Test GetStatus RPC."""
        from src.generated.graphiti.v1 import admin_service_pb2
        from src.services.admin_service import AdminServiceServicer

        start_time = time.time()
        servicer = AdminServiceServicer(mock_graphiti, mock_config, start_time)

        request = admin_service_pb2.GetStatusRequest()
        context = MagicMock()

        response = await servicer.GetStatus(request, context)

        assert response.version == '0.1.0'
        assert response.database_provider == 'falkordb'
        assert response.llm_provider == 'openai'
        assert response.database_connected is True

    @pytest.mark.asyncio
    async def test_get_status_database_disconnected(self, mock_graphiti, mock_config):
        """Test GetStatus RPC when database is disconnected."""
        from src.generated.graphiti.v1 import admin_service_pb2
        from src.services.admin_service import AdminServiceServicer

        mock_graphiti.driver.execute_query = AsyncMock(side_effect=Exception('Connection lost'))

        start_time = time.time()
        servicer = AdminServiceServicer(mock_graphiti, mock_config, start_time)

        request = admin_service_pb2.GetStatusRequest()
        context = MagicMock()

        response = await servicer.GetStatus(request, context)

        assert response.database_connected is False

    @pytest.mark.asyncio
    async def test_get_status_general_error(self, mock_graphiti, mock_config):
        """Test GetStatus RPC with general error."""
        from src.generated.graphiti.v1 import admin_service_pb2
        from src.services.admin_service import AdminServiceServicer

        start_time = time.time()
        servicer = AdminServiceServicer(mock_graphiti, mock_config, start_time)

        # Make the entire function raise an exception
        servicer._config = None  # This will cause an AttributeError

        request = admin_service_pb2.GetStatusRequest()
        context = MagicMock()
        context.abort = AsyncMock()

        await servicer.GetStatus(request, context)

        context.abort.assert_called_once()


class TestDeleteEntityEdge:
    """Tests for DeleteEntityEdge RPC."""

    @pytest.mark.asyncio
    async def test_delete_entity_edge(self, mock_graphiti, mock_config):
        """Test DeleteEntityEdge RPC."""
        from src.generated.graphiti.v1 import admin_service_pb2
        from src.services.admin_service import AdminServiceServicer

        start_time = time.time()
        servicer = AdminServiceServicer(mock_graphiti, mock_config, start_time)

        request = admin_service_pb2.DeleteEntityEdgeRequest(uuid='test-uuid')
        context = MagicMock()

        mock_edge = MagicMock()
        mock_edge.delete = AsyncMock()

        with patch(
            'graphiti_core.edges.EntityEdge.get_by_uuid', new=AsyncMock(return_value=mock_edge)
        ):
            response = await servicer.DeleteEntityEdge(request, context)

        mock_edge.delete.assert_called_once_with(mock_graphiti.driver)
        assert response.success is True

    @pytest.mark.asyncio
    async def test_delete_entity_edge_not_found(self, mock_graphiti, mock_config):
        """Test DeleteEntityEdge RPC when edge not found."""
        from src.generated.graphiti.v1 import admin_service_pb2
        from src.services.admin_service import AdminServiceServicer

        start_time = time.time()
        servicer = AdminServiceServicer(mock_graphiti, mock_config, start_time)

        request = admin_service_pb2.DeleteEntityEdgeRequest(uuid='test-uuid')
        context = MagicMock()

        with patch(
            'graphiti_core.edges.EntityEdge.get_by_uuid',
            new=AsyncMock(side_effect=EdgeNotFoundError('test-uuid')),
        ):
            response = await servicer.DeleteEntityEdge(request, context)

        assert response.success is False
        assert response.error_code == 'NOT_FOUND'

    @pytest.mark.asyncio
    async def test_delete_entity_edge_general_error(self, mock_graphiti, mock_config):
        """Test DeleteEntityEdge RPC with general error."""
        from src.generated.graphiti.v1 import admin_service_pb2
        from src.services.admin_service import AdminServiceServicer

        start_time = time.time()
        servicer = AdminServiceServicer(mock_graphiti, mock_config, start_time)

        request = admin_service_pb2.DeleteEntityEdgeRequest(uuid='test-uuid')
        context = MagicMock()

        with patch(
            'graphiti_core.edges.EntityEdge.get_by_uuid',
            new=AsyncMock(side_effect=RuntimeError('Database error')),
        ):
            response = await servicer.DeleteEntityEdge(request, context)

        assert response.success is False
        assert response.error_code == 'DELETE_FAILED'


class TestDeleteEntityEdges:
    """Tests for DeleteEntityEdges RPC."""

    @pytest.mark.asyncio
    async def test_delete_entity_edges(self, mock_graphiti, mock_config):
        """Test DeleteEntityEdges RPC."""
        from src.generated.graphiti.v1 import admin_service_pb2
        from src.services.admin_service import AdminServiceServicer

        start_time = time.time()
        servicer = AdminServiceServicer(mock_graphiti, mock_config, start_time)

        request = admin_service_pb2.DeleteEntityEdgesRequest(uuids=['uuid1', 'uuid2'])
        context = MagicMock()

        with patch(
            'graphiti_core.edges.EntityEdge.delete_by_uuids',
            new=AsyncMock(),
        ):
            response = await servicer.DeleteEntityEdges(request, context)

        assert response.success is True

    @pytest.mark.asyncio
    async def test_delete_entity_edges_error(self, mock_graphiti, mock_config):
        """Test DeleteEntityEdges RPC with error."""
        from src.generated.graphiti.v1 import admin_service_pb2
        from src.services.admin_service import AdminServiceServicer

        start_time = time.time()
        servicer = AdminServiceServicer(mock_graphiti, mock_config, start_time)

        request = admin_service_pb2.DeleteEntityEdgesRequest(uuids=['uuid1', 'uuid2'])
        context = MagicMock()

        with patch(
            'src.services.admin_service.EntityEdge.delete_by_uuids',
            new=AsyncMock(side_effect=RuntimeError('Bulk delete failed')),
        ):
            response = await servicer.DeleteEntityEdges(request, context)

        assert response.success is False
        assert response.error_code == 'DELETE_FAILED'


class TestDeleteGroup:
    """Tests for DeleteGroup RPC."""

    @pytest.mark.asyncio
    async def test_delete_group(self, mock_graphiti, mock_config):
        """Test DeleteGroup RPC."""
        from src.generated.graphiti.v1 import admin_service_pb2
        from src.services.admin_service import AdminServiceServicer

        start_time = time.time()
        servicer = AdminServiceServicer(mock_graphiti, mock_config, start_time)

        request = admin_service_pb2.DeleteGroupRequest(group_id='test-group')
        context = MagicMock()

        mock_edge = MagicMock()
        mock_edge.delete = AsyncMock()

        mock_node = MagicMock()
        mock_node.delete = AsyncMock()

        mock_episode = MagicMock()
        mock_episode.delete = AsyncMock()

        with (
            patch(
                'graphiti_core.edges.EntityEdge.get_by_group_ids',
                new=AsyncMock(return_value=[mock_edge]),
            ),
            patch(
                'graphiti_core.nodes.EntityNode.get_by_group_ids',
                new=AsyncMock(return_value=[mock_node]),
            ),
            patch(
                'graphiti_core.nodes.EpisodicNode.get_by_group_ids',
                new=AsyncMock(return_value=[mock_episode]),
            ),
        ):
            response = await servicer.DeleteGroup(request, context)

        mock_edge.delete.assert_called_once_with(mock_graphiti.driver)
        mock_node.delete.assert_called_once_with(mock_graphiti.driver)
        mock_episode.delete.assert_called_once_with(mock_graphiti.driver)
        assert response.success is True

    @pytest.mark.asyncio
    async def test_delete_group_no_edges(self, mock_graphiti, mock_config):
        """Test DeleteGroup RPC when group has no edges."""
        from src.generated.graphiti.v1 import admin_service_pb2
        from src.services.admin_service import AdminServiceServicer

        start_time = time.time()
        servicer = AdminServiceServicer(mock_graphiti, mock_config, start_time)

        request = admin_service_pb2.DeleteGroupRequest(group_id='test-group')
        context = MagicMock()

        mock_node = MagicMock()
        mock_node.delete = AsyncMock()

        mock_episode = MagicMock()
        mock_episode.delete = AsyncMock()

        with (
            patch(
                'graphiti_core.edges.EntityEdge.get_by_group_ids',
                new=AsyncMock(side_effect=GroupsEdgesNotFoundError(['test-group'])),
            ),
            patch(
                'graphiti_core.nodes.EntityNode.get_by_group_ids',
                new=AsyncMock(return_value=[mock_node]),
            ),
            patch(
                'graphiti_core.nodes.EpisodicNode.get_by_group_ids',
                new=AsyncMock(return_value=[mock_episode]),
            ),
        ):
            response = await servicer.DeleteGroup(request, context)

        assert response.success is True

    @pytest.mark.asyncio
    async def test_delete_group_error(self, mock_graphiti, mock_config):
        """Test DeleteGroup RPC with error."""
        from src.generated.graphiti.v1 import admin_service_pb2
        from src.services.admin_service import AdminServiceServicer

        start_time = time.time()
        servicer = AdminServiceServicer(mock_graphiti, mock_config, start_time)

        request = admin_service_pb2.DeleteGroupRequest(group_id='test-group')
        context = MagicMock()

        with patch(
            'graphiti_core.edges.EntityEdge.get_by_group_ids',
            new=AsyncMock(side_effect=RuntimeError('Database error')),
        ):
            response = await servicer.DeleteGroup(request, context)

        assert response.success is False
        assert response.error_code == 'DELETE_FAILED'


class TestDeleteEpisode:
    """Tests for DeleteEpisode RPC."""

    @pytest.mark.asyncio
    async def test_delete_episode(self, mock_graphiti, mock_config):
        """Test DeleteEpisode RPC."""
        from src.generated.graphiti.v1 import admin_service_pb2
        from src.services.admin_service import AdminServiceServicer

        start_time = time.time()
        servicer = AdminServiceServicer(mock_graphiti, mock_config, start_time)

        request = admin_service_pb2.DeleteEpisodeRequest(uuid='test-uuid')
        context = MagicMock()

        mock_episode = MagicMock()
        mock_episode.delete = AsyncMock()

        with patch(
            'graphiti_core.nodes.EpisodicNode.get_by_uuid',
            new=AsyncMock(return_value=mock_episode),
        ):
            response = await servicer.DeleteEpisode(request, context)

        mock_episode.delete.assert_called_once()
        assert response.success is True

    @pytest.mark.asyncio
    async def test_delete_episode_not_found(self, mock_graphiti, mock_config):
        """Test DeleteEpisode RPC when episode not found."""
        from src.generated.graphiti.v1 import admin_service_pb2
        from src.services.admin_service import AdminServiceServicer

        start_time = time.time()
        servicer = AdminServiceServicer(mock_graphiti, mock_config, start_time)

        request = admin_service_pb2.DeleteEpisodeRequest(uuid='test-uuid')
        context = MagicMock()

        with patch(
            'graphiti_core.nodes.EpisodicNode.get_by_uuid',
            new=AsyncMock(side_effect=NodeNotFoundError('test-uuid')),
        ):
            response = await servicer.DeleteEpisode(request, context)

        assert response.success is False
        assert response.error_code == 'NOT_FOUND'

    @pytest.mark.asyncio
    async def test_delete_episode_general_error(self, mock_graphiti, mock_config):
        """Test DeleteEpisode RPC with general error."""
        from src.generated.graphiti.v1 import admin_service_pb2
        from src.services.admin_service import AdminServiceServicer

        start_time = time.time()
        servicer = AdminServiceServicer(mock_graphiti, mock_config, start_time)

        request = admin_service_pb2.DeleteEpisodeRequest(uuid='test-uuid')
        context = MagicMock()

        with patch(
            'graphiti_core.nodes.EpisodicNode.get_by_uuid',
            new=AsyncMock(side_effect=RuntimeError('Database error')),
        ):
            response = await servicer.DeleteEpisode(request, context)

        assert response.success is False
        assert response.error_code == 'DELETE_FAILED'


class TestDeleteEpisodes:
    """Tests for DeleteEpisodes RPC."""

    @pytest.mark.asyncio
    async def test_delete_episodes(self, mock_graphiti, mock_config):
        """Test DeleteEpisodes RPC."""
        from src.generated.graphiti.v1 import admin_service_pb2
        from src.services.admin_service import AdminServiceServicer

        start_time = time.time()
        servicer = AdminServiceServicer(mock_graphiti, mock_config, start_time)

        request = admin_service_pb2.DeleteEpisodesRequest(uuids=['uuid1', 'uuid2'])
        context = MagicMock()

        with patch(
            'graphiti_core.nodes.EpisodicNode.delete_by_uuids',
            new=AsyncMock(),
        ):
            response = await servicer.DeleteEpisodes(request, context)

        assert response.success is True
        assert '2' in response.message

    @pytest.mark.asyncio
    async def test_delete_episodes_error(self, mock_graphiti, mock_config):
        """Test DeleteEpisodes RPC with error."""
        from src.generated.graphiti.v1 import admin_service_pb2
        from src.services.admin_service import AdminServiceServicer

        start_time = time.time()
        servicer = AdminServiceServicer(mock_graphiti, mock_config, start_time)

        request = admin_service_pb2.DeleteEpisodesRequest(uuids=['uuid1', 'uuid2'])
        context = MagicMock()

        with patch(
            'graphiti_core.nodes.EpisodicNode.delete_by_uuids',
            new=AsyncMock(side_effect=RuntimeError('Delete failed')),
        ):
            response = await servicer.DeleteEpisodes(request, context)

        assert response.success is False
        assert response.error_code == 'DELETE_FAILED'


class TestDeleteEntityNode:
    """Tests for DeleteEntityNode RPC."""

    @pytest.mark.asyncio
    async def test_delete_entity_node(self, mock_graphiti, mock_config):
        """Test DeleteEntityNode RPC."""
        from src.generated.graphiti.v1 import admin_service_pb2
        from src.services.admin_service import AdminServiceServicer

        start_time = time.time()
        servicer = AdminServiceServicer(mock_graphiti, mock_config, start_time)

        request = admin_service_pb2.DeleteEntityNodeRequest(uuid='test-uuid')
        context = MagicMock()

        mock_node = MagicMock()
        mock_node.delete = AsyncMock()

        with patch(
            'graphiti_core.nodes.EntityNode.get_by_uuid',
            new=AsyncMock(return_value=mock_node),
        ):
            response = await servicer.DeleteEntityNode(request, context)

        mock_node.delete.assert_called_once()
        assert response.success is True

    @pytest.mark.asyncio
    async def test_delete_entity_node_error(self, mock_graphiti, mock_config):
        """Test DeleteEntityNode RPC with error."""
        from src.generated.graphiti.v1 import admin_service_pb2
        from src.services.admin_service import AdminServiceServicer

        start_time = time.time()
        servicer = AdminServiceServicer(mock_graphiti, mock_config, start_time)

        request = admin_service_pb2.DeleteEntityNodeRequest(uuid='test-uuid')
        context = MagicMock()

        with patch(
            'src.services.admin_service.EntityNode.get_by_uuid',
            new=AsyncMock(side_effect=RuntimeError('Node not found')),
        ):
            response = await servicer.DeleteEntityNode(request, context)

        assert response.success is False
        assert response.error_code == 'DELETE_FAILED'


class TestClearData:
    """Tests for ClearData RPC."""

    @pytest.mark.asyncio
    async def test_clear_data_requires_confirmation(self, mock_graphiti, mock_config):
        """Test ClearData RPC requires confirmation."""
        from src.generated.graphiti.v1 import admin_service_pb2
        from src.services.admin_service import AdminServiceServicer

        start_time = time.time()
        servicer = AdminServiceServicer(mock_graphiti, mock_config, start_time)

        request = admin_service_pb2.ClearDataRequest(confirm=False)
        context = MagicMock()

        response = await servicer.ClearData(request, context)

        assert response.success is False
        assert 'Confirmation required' in response.message

    @pytest.mark.asyncio
    async def test_clear_data_with_confirmation(self, mock_graphiti, mock_config):
        """Test ClearData RPC with confirmation."""
        from src.generated.graphiti.v1 import admin_service_pb2
        from src.services.admin_service import AdminServiceServicer

        start_time = time.time()
        servicer = AdminServiceServicer(mock_graphiti, mock_config, start_time)

        request = admin_service_pb2.ClearDataRequest(confirm=True)
        context = MagicMock()

        with patch('src.services.admin_service.clear_data', new=AsyncMock()):
            response = await servicer.ClearData(request, context)

        assert response.success is True

    @pytest.mark.asyncio
    async def test_clear_data_error(self, mock_graphiti, mock_config):
        """Test ClearData RPC with error."""
        from src.generated.graphiti.v1 import admin_service_pb2
        from src.services.admin_service import AdminServiceServicer

        start_time = time.time()
        servicer = AdminServiceServicer(mock_graphiti, mock_config, start_time)

        request = admin_service_pb2.ClearDataRequest(confirm=True)
        context = MagicMock()

        with patch(
            'src.services.admin_service.clear_data',
            new=AsyncMock(side_effect=RuntimeError('Clear failed')),
        ):
            response = await servicer.ClearData(request, context)

        assert response.success is False
        assert response.error_code == 'CLEAR_FAILED'


class TestBuildIndices:
    """Tests for BuildIndices RPC."""

    @pytest.mark.asyncio
    async def test_build_indices(self, mock_graphiti, mock_config):
        """Test BuildIndices RPC."""
        from src.generated.graphiti.v1 import admin_service_pb2
        from src.services.admin_service import AdminServiceServicer

        start_time = time.time()
        servicer = AdminServiceServicer(mock_graphiti, mock_config, start_time)

        request = admin_service_pb2.BuildIndicesRequest()
        context = MagicMock()

        response = await servicer.BuildIndices(request, context)

        mock_graphiti.build_indices_and_constraints.assert_called_once()
        assert response.success is True

    @pytest.mark.asyncio
    async def test_build_indices_error(self, mock_graphiti, mock_config):
        """Test BuildIndices RPC with error."""
        from src.generated.graphiti.v1 import admin_service_pb2
        from src.services.admin_service import AdminServiceServicer

        mock_graphiti.build_indices_and_constraints = AsyncMock(
            side_effect=RuntimeError('Build failed')
        )

        start_time = time.time()
        servicer = AdminServiceServicer(mock_graphiti, mock_config, start_time)

        request = admin_service_pb2.BuildIndicesRequest()
        context = MagicMock()

        response = await servicer.BuildIndices(request, context)

        assert response.success is False
        assert response.error_code == 'BUILD_FAILED'


class TestRemoveEpisode:
    """Tests for RemoveEpisode RPC."""

    @pytest.mark.asyncio
    async def test_remove_episode(self, mock_graphiti, mock_config):
        """Test RemoveEpisode RPC."""
        from src.generated.graphiti.v1 import admin_service_pb2
        from src.services.admin_service import AdminServiceServicer

        start_time = time.time()
        servicer = AdminServiceServicer(mock_graphiti, mock_config, start_time)

        mock_graphiti.remove_episode = AsyncMock(
            return_value={'nodes_removed': 2, 'edges_removed': 3}
        )

        request = admin_service_pb2.RemoveEpisodeRequest(uuid='test-uuid')
        context = MagicMock()

        response = await servicer.RemoveEpisode(request, context)

        mock_graphiti.remove_episode.assert_called_once_with('test-uuid')
        assert response.result.success is True
        assert response.orphaned_nodes_removed == 2
        assert response.orphaned_edges_removed == 3

    @pytest.mark.asyncio
    async def test_remove_episode_non_dict_result(self, mock_graphiti, mock_config):
        """Test RemoveEpisode RPC with non-dict result."""
        from src.generated.graphiti.v1 import admin_service_pb2
        from src.services.admin_service import AdminServiceServicer

        start_time = time.time()
        servicer = AdminServiceServicer(mock_graphiti, mock_config, start_time)

        mock_graphiti.remove_episode = AsyncMock(return_value=None)

        request = admin_service_pb2.RemoveEpisodeRequest(uuid='test-uuid')
        context = MagicMock()

        response = await servicer.RemoveEpisode(request, context)

        assert response.result.success is True
        assert response.orphaned_nodes_removed == 0
        assert response.orphaned_edges_removed == 0

    @pytest.mark.asyncio
    async def test_remove_episode_not_found(self, mock_graphiti, mock_config):
        """Test RemoveEpisode RPC when episode not found."""
        from src.generated.graphiti.v1 import admin_service_pb2
        from src.services.admin_service import AdminServiceServicer

        start_time = time.time()
        servicer = AdminServiceServicer(mock_graphiti, mock_config, start_time)

        mock_graphiti.remove_episode = AsyncMock(side_effect=NodeNotFoundError('test-uuid'))

        request = admin_service_pb2.RemoveEpisodeRequest(uuid='test-uuid')
        context = MagicMock()

        response = await servicer.RemoveEpisode(request, context)

        assert response.result.success is False
        assert response.result.error_code == 'NOT_FOUND'

    @pytest.mark.asyncio
    async def test_remove_episode_general_error(self, mock_graphiti, mock_config):
        """Test RemoveEpisode RPC with general error."""
        from src.generated.graphiti.v1 import admin_service_pb2
        from src.services.admin_service import AdminServiceServicer

        start_time = time.time()
        servicer = AdminServiceServicer(mock_graphiti, mock_config, start_time)

        mock_graphiti.remove_episode = AsyncMock(side_effect=RuntimeError('Database error'))

        request = admin_service_pb2.RemoveEpisodeRequest(uuid='test-uuid')
        context = MagicMock()

        response = await servicer.RemoveEpisode(request, context)

        assert response.result.success is False
        assert response.result.error_code == 'REMOVE_FAILED'


class TestBuildCommunities:
    """Tests for BuildCommunities RPC."""

    @pytest.mark.asyncio
    async def test_build_communities(self, mock_graphiti, mock_config, sample_community_node):
        """Test BuildCommunities RPC."""
        from src.generated.graphiti.v1 import admin_service_pb2
        from src.services.admin_service import AdminServiceServicer

        start_time = time.time()
        servicer = AdminServiceServicer(mock_graphiti, mock_config, start_time)

        mock_graphiti.build_communities = AsyncMock(return_value=([sample_community_node], []))

        request = admin_service_pb2.BuildCommunitiesRequest(group_ids=['test-group'])
        context = MagicMock()

        response = await servicer.BuildCommunities(request, context)

        mock_graphiti.build_communities.assert_called_once()
        assert response.total_created == 1

    @pytest.mark.asyncio
    async def test_build_communities_no_group_ids(self, mock_graphiti, mock_config):
        """Test BuildCommunities RPC with no group_ids."""
        from src.generated.graphiti.v1 import admin_service_pb2
        from src.services.admin_service import AdminServiceServicer

        start_time = time.time()
        servicer = AdminServiceServicer(mock_graphiti, mock_config, start_time)

        mock_graphiti.build_communities = AsyncMock(return_value=([], []))

        request = admin_service_pb2.BuildCommunitiesRequest()
        context = MagicMock()

        response = await servicer.BuildCommunities(request, context)

        mock_graphiti.build_communities.assert_called_once_with(group_ids=None)
        assert response.total_created == 0

    @pytest.mark.asyncio
    async def test_build_communities_empty_result(self, mock_graphiti, mock_config):
        """Test BuildCommunities RPC with empty result."""
        from src.generated.graphiti.v1 import admin_service_pb2
        from src.services.admin_service import AdminServiceServicer

        start_time = time.time()
        servicer = AdminServiceServicer(mock_graphiti, mock_config, start_time)

        mock_graphiti.build_communities = AsyncMock(return_value=None)

        request = admin_service_pb2.BuildCommunitiesRequest(group_ids=['test-group'])
        context = MagicMock()

        response = await servicer.BuildCommunities(request, context)

        assert response.total_created == 0

    @pytest.mark.asyncio
    async def test_build_communities_error(self, mock_graphiti, mock_config):
        """Test BuildCommunities RPC with error."""
        from src.generated.graphiti.v1 import admin_service_pb2
        from src.services.admin_service import AdminServiceServicer

        start_time = time.time()
        servicer = AdminServiceServicer(mock_graphiti, mock_config, start_time)

        mock_graphiti.build_communities = AsyncMock(side_effect=RuntimeError('Build failed'))

        request = admin_service_pb2.BuildCommunitiesRequest(group_ids=['test-group'])
        context = MagicMock()
        context.abort = AsyncMock()

        await servicer.BuildCommunities(request, context)

        context.abort.assert_called_once()
