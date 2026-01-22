"""AdminService implementation for administrative operations."""

import logging
import time

import grpc
from graphiti_core.edges import EntityEdge
from graphiti_core.errors import EdgeNotFoundError, GroupsEdgesNotFoundError, NodeNotFoundError
from graphiti_core.nodes import EntityNode, EpisodicNode
from graphiti_core.utils.maintenance.graph_data_operations import clear_data

from src.generated.graphiti.v1 import admin_service_pb2, admin_service_pb2_grpc, common_pb2
from src.services.base import BaseServicer

logger = logging.getLogger(__name__)


class AdminServiceServicer(BaseServicer, admin_service_pb2_grpc.AdminServiceServicer):
    """gRPC service implementation for administrative operations."""

    def __init__(self, graphiti, config, start_time: float):
        """Initialize the admin servicer.

        Args:
            graphiti: The Graphiti client instance.
            config: The server configuration.
            start_time: The server start time for uptime calculation.
        """
        super().__init__(graphiti)
        self._config = config
        self._start_time = start_time

    async def HealthCheck(
        self,
        request: admin_service_pb2.HealthCheckRequest,
        context: grpc.aio.ServicerContext,
    ) -> admin_service_pb2.HealthCheckResponse:
        """Health check endpoint."""
        try:
            # Try to verify database connection
            # A simple query to check connectivity
            await self.graphiti.driver.execute_query(
                'RETURN 1 as health_check',
                routing_='r',
            )

            return admin_service_pb2.HealthCheckResponse(
                status=admin_service_pb2.HealthCheckResponse.SERVING_STATUS_SERVING,
                message='Healthy',
            )

        except Exception as e:
            logger.warning(f'Health check failed: {e}')
            return admin_service_pb2.HealthCheckResponse(
                status=admin_service_pb2.HealthCheckResponse.SERVING_STATUS_NOT_SERVING,
                message=str(e),
            )

    async def GetStatus(
        self,
        request: admin_service_pb2.GetStatusRequest,
        context: grpc.aio.ServicerContext,
    ) -> admin_service_pb2.GetStatusResponse:
        """Get server status."""
        try:
            # Check database connection
            db_connected = True
            try:
                await self.graphiti.driver.execute_query(
                    'RETURN 1 as health_check',
                    routing_='r',
                )
            except Exception:
                db_connected = False

            uptime_seconds = int(time.time() - self._start_time)

            return admin_service_pb2.GetStatusResponse(
                version='0.1.0',
                database_provider=self._config.database.provider,
                llm_provider=self._config.llm.provider,
                embedder_provider=self._config.embedder.provider,
                database_connected=db_connected,
                uptime_seconds=uptime_seconds,
            )

        except Exception as e:
            logger.exception('Error getting status')
            await context.abort(grpc.StatusCode.INTERNAL, str(e))

    async def DeleteEntityEdge(
        self,
        request: admin_service_pb2.DeleteEntityEdgeRequest,
        context: grpc.aio.ServicerContext,
    ) -> common_pb2.OperationResult:
        """Delete an entity edge."""
        try:
            edge = await EntityEdge.get_by_uuid(self.graphiti.driver, request.uuid)
            await edge.delete(self.graphiti.driver)

            return common_pb2.OperationResult(
                success=True,
                message='Entity edge deleted',
            )

        except EdgeNotFoundError as e:
            logger.warning(f'Entity edge not found: {request.uuid}')
            return common_pb2.OperationResult(
                success=False,
                message=e.message,
                error_code='NOT_FOUND',
            )

        except Exception as e:
            logger.exception(f'Error deleting entity edge {request.uuid}')
            return common_pb2.OperationResult(
                success=False,
                message=str(e),
                error_code='DELETE_FAILED',
            )

    async def DeleteEntityEdges(
        self,
        request: admin_service_pb2.DeleteEntityEdgesRequest,
        context: grpc.aio.ServicerContext,
    ) -> common_pb2.OperationResult:
        """Delete multiple entity edges."""
        try:
            from graphiti_core.edges import EntityEdge

            await EntityEdge.delete_by_uuids(self.graphiti.driver, list(request.uuids))

            return common_pb2.OperationResult(
                success=True,
                message=f'Deleted {len(request.uuids)} entity edges',
            )

        except Exception as e:
            logger.exception('Error deleting entity edges')
            return common_pb2.OperationResult(
                success=False,
                message=str(e),
                error_code='DELETE_FAILED',
            )

    async def DeleteGroup(
        self,
        request: admin_service_pb2.DeleteGroupRequest,
        context: grpc.aio.ServicerContext,
    ) -> common_pb2.OperationResult:
        """Delete a group and all its data."""
        try:
            # Get all edges for the group
            try:
                edges = await EntityEdge.get_by_group_ids(self.graphiti.driver, [request.group_id])
            except GroupsEdgesNotFoundError:
                logger.warning(f'No edges found for group {request.group_id}')
                edges = []

            # Get all nodes and episodes for the group
            nodes = await EntityNode.get_by_group_ids(self.graphiti.driver, [request.group_id])
            episodes = await EpisodicNode.get_by_group_ids(self.graphiti.driver, [request.group_id])

            # Delete all edges, nodes, and episodes
            for edge in edges:
                await edge.delete(self.graphiti.driver)
            for node in nodes:
                await node.delete(self.graphiti.driver)
            for episode in episodes:
                await episode.delete(self.graphiti.driver)

            return common_pb2.OperationResult(
                success=True,
                message='Group deleted',
            )

        except Exception as e:
            logger.exception(f'Error deleting group {request.group_id}')
            return common_pb2.OperationResult(
                success=False,
                message=str(e),
                error_code='DELETE_FAILED',
            )

    async def DeleteEpisode(
        self,
        request: admin_service_pb2.DeleteEpisodeRequest,
        context: grpc.aio.ServicerContext,
    ) -> common_pb2.OperationResult:
        """Delete an episode."""
        try:
            episode = await EpisodicNode.get_by_uuid(self.graphiti.driver, request.uuid)
            await episode.delete(self.graphiti.driver)

            return common_pb2.OperationResult(
                success=True,
                message='Episode deleted',
            )

        except NodeNotFoundError as e:
            logger.warning(f'Episode not found: {request.uuid}')
            return common_pb2.OperationResult(
                success=False,
                message=e.message,
                error_code='NOT_FOUND',
            )

        except Exception as e:
            logger.exception(f'Error deleting episode {request.uuid}')
            return common_pb2.OperationResult(
                success=False,
                message=str(e),
                error_code='DELETE_FAILED',
            )

    async def DeleteEpisodes(
        self,
        request: admin_service_pb2.DeleteEpisodesRequest,
        context: grpc.aio.ServicerContext,
    ) -> common_pb2.OperationResult:
        """Delete multiple episodes."""
        try:
            await EpisodicNode.delete_by_uuids(self.graphiti.driver, list(request.uuids))

            return common_pb2.OperationResult(
                success=True,
                message=f'Deleted {len(request.uuids)} episodes',
            )

        except Exception as e:
            logger.exception('Error deleting episodes')
            return common_pb2.OperationResult(
                success=False,
                message=str(e),
                error_code='DELETE_FAILED',
            )

    async def DeleteEntityNode(
        self,
        request: admin_service_pb2.DeleteEntityNodeRequest,
        context: grpc.aio.ServicerContext,
    ) -> common_pb2.OperationResult:
        """Delete an entity node."""
        try:
            from graphiti_core.nodes import EntityNode

            node = await EntityNode.get_by_uuid(self.graphiti.driver, request.uuid)
            await node.delete(self.graphiti.driver)

            return common_pb2.OperationResult(
                success=True,
                message='Entity node deleted',
            )

        except Exception as e:
            logger.exception(f'Error deleting entity node {request.uuid}')
            return common_pb2.OperationResult(
                success=False,
                message=str(e),
                error_code='DELETE_FAILED',
            )

    async def ClearData(
        self,
        request: admin_service_pb2.ClearDataRequest,
        context: grpc.aio.ServicerContext,
    ) -> common_pb2.OperationResult:
        """Clear all data in the graph."""
        try:
            if not request.confirm:
                return common_pb2.OperationResult(
                    success=False,
                    message='Confirmation required to clear data',
                    error_code='CONFIRMATION_REQUIRED',
                )

            await clear_data(self.graphiti.driver)
            await self.graphiti.build_indices_and_constraints()

            return common_pb2.OperationResult(
                success=True,
                message='Graph cleared',
            )

        except Exception as e:
            logger.exception('Error clearing data')
            return common_pb2.OperationResult(
                success=False,
                message=str(e),
                error_code='CLEAR_FAILED',
            )

    async def BuildIndices(
        self,
        request: admin_service_pb2.BuildIndicesRequest,
        context: grpc.aio.ServicerContext,
    ) -> common_pb2.OperationResult:
        """Build indices and constraints."""
        try:
            await self.graphiti.build_indices_and_constraints()

            return common_pb2.OperationResult(
                success=True,
                message='Indices and constraints built',
            )

        except Exception as e:
            logger.exception('Error building indices')
            return common_pb2.OperationResult(
                success=False,
                message=str(e),
                error_code='BUILD_FAILED',
            )

    async def RemoveEpisode(
        self,
        request: admin_service_pb2.RemoveEpisodeRequest,
        context: grpc.aio.ServicerContext,
    ) -> admin_service_pb2.RemoveEpisodeResponse:
        """Remove an episode and clean up orphaned nodes."""
        try:
            # Use graphiti's remove_episode method which handles orphan cleanup
            result = await self.graphiti.remove_episode(request.uuid)

            return admin_service_pb2.RemoveEpisodeResponse(
                result=common_pb2.OperationResult(
                    success=True,
                    message='Episode removed with orphan cleanup',
                ),
                orphaned_nodes_removed=result.get('nodes_removed', 0)
                if isinstance(result, dict)
                else 0,
                orphaned_edges_removed=result.get('edges_removed', 0)
                if isinstance(result, dict)
                else 0,
            )

        except NodeNotFoundError as e:
            logger.warning(f'Episode not found: {request.uuid}')
            return admin_service_pb2.RemoveEpisodeResponse(
                result=common_pb2.OperationResult(
                    success=False,
                    message=e.message,
                    error_code='NOT_FOUND',
                ),
            )

        except Exception as e:
            logger.exception(f'Error removing episode {request.uuid}')
            return admin_service_pb2.RemoveEpisodeResponse(
                result=common_pb2.OperationResult(
                    success=False,
                    message=str(e),
                    error_code='REMOVE_FAILED',
                ),
            )

    async def BuildCommunities(
        self,
        request: admin_service_pb2.BuildCommunitiesRequest,
        context: grpc.aio.ServicerContext,
    ) -> admin_service_pb2.BuildCommunitiesResponse:
        """Build communities for specified groups."""
        try:
            from src.converters.node_converters import community_node_to_proto

            group_ids = list(request.group_ids) if request.group_ids else None

            # Build communities using graphiti's method
            # Returns tuple[list[CommunityNode], list[CommunityEdge]]
            result = await self.graphiti.build_communities(group_ids=group_ids)

            # Convert communities to proto
            communities_proto = []
            if result:
                # Result is a tuple (community_nodes, community_edges)
                community_nodes, _ = result
                communities_proto = [community_node_to_proto(c) for c in community_nodes]

            return admin_service_pb2.BuildCommunitiesResponse(
                communities=communities_proto,
                total_created=len(communities_proto),
            )

        except Exception as e:
            logger.exception('Error building communities')
            await context.abort(grpc.StatusCode.INTERNAL, str(e))
