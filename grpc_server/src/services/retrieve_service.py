"""RetrieveService implementation for data retrieval operations."""

import logging
from datetime import datetime, timezone
from typing import AsyncIterator

import grpc

from src.converters.edge_converters import entity_edge_to_proto, fact_result_from_edge
from src.converters.node_converters import (
    community_node_to_proto,
    entity_node_to_proto,
    episode_type_from_proto,
    episodic_node_to_proto,
    timestamp_to_datetime,
)
from src.converters.search_converters import (
    search_config_from_proto,
    search_filters_from_proto,
    search_results_to_proto,
)
from src.generated.graphiti.v1 import (
    edges_pb2,
    nodes_pb2,
    retrieve_service_pb2,
    retrieve_service_pb2_grpc,
    search_pb2,
)
from src.services.base import BaseServicer

logger = logging.getLogger(__name__)


class RetrieveServiceServicer(BaseServicer, retrieve_service_pb2_grpc.RetrieveServiceServicer):
    """gRPC service implementation for data retrieval."""

    async def Search(
        self,
        request: retrieve_service_pb2.SearchRequest,
        context: grpc.aio.ServicerContext,
    ) -> retrieve_service_pb2.SearchResponse:
        """Simple search returning facts."""
        try:
            group_ids = list(request.group_ids) if request.group_ids else None
            max_facts = request.max_facts if request.HasField('max_facts') else 10

            edges = await self.graphiti.search(
                group_ids=group_ids,
                query=request.query,
                num_results=max_facts,
            )

            facts = [fact_result_from_edge(edge) for edge in edges]

            return retrieve_service_pb2.SearchResponse(facts=facts)

        except Exception as e:
            logger.exception('Error during search')
            await context.abort(grpc.StatusCode.INTERNAL, str(e))

    async def AdvancedSearch(
        self,
        request: retrieve_service_pb2.AdvancedSearchRequest,
        context: grpc.aio.ServicerContext,
    ) -> search_pb2.SearchResults:
        """Advanced search with full configuration."""
        try:
            group_ids = list(request.group_ids) if request.group_ids else None
            config = search_config_from_proto(
                request.config if request.HasField('config') else None
            )
            filters = search_filters_from_proto(
                request.filters if request.HasField('filters') else None
            )
            center_node_uuids = list(request.center_node_uuids) if request.center_node_uuids else []
            # search_ takes center_node_uuid (singular) and bfs_origin_node_uuids
            center_node_uuid = center_node_uuids[0] if center_node_uuids else None
            bfs_origin_node_uuids = center_node_uuids[1:] if len(center_node_uuids) > 1 else None

            results = await self.graphiti.search_(
                group_ids=group_ids,
                query=request.query,
                config=config,
                search_filter=filters,
                center_node_uuid=center_node_uuid,
                bfs_origin_node_uuids=bfs_origin_node_uuids,
            )

            return search_results_to_proto(results)

        except Exception as e:
            logger.exception('Error during advanced search')
            await context.abort(grpc.StatusCode.INTERNAL, str(e))

    async def StreamSearch(
        self,
        request: retrieve_service_pb2.SearchRequest,
        context: grpc.aio.ServicerContext,
    ) -> AsyncIterator[retrieve_service_pb2.SearchResultChunk]:
        """Streaming search for large result sets."""
        try:
            group_ids = list(request.group_ids) if request.group_ids else None
            max_facts = request.max_facts if request.HasField('max_facts') else 10

            edges = await self.graphiti.search(
                group_ids=group_ids,
                query=request.query,
                num_results=max_facts,
            )

            # Stream each result
            for i, edge in enumerate(edges):
                is_last = i == len(edges) - 1
                chunk = retrieve_service_pb2.SearchResultChunk(
                    fact=fact_result_from_edge(edge),
                    is_last=is_last,
                )
                yield chunk

            # If no results, yield an empty final chunk
            if not edges:
                yield retrieve_service_pb2.SearchResultChunk(is_last=True)

        except Exception as e:
            logger.exception('Error during streaming search')
            await context.abort(grpc.StatusCode.INTERNAL, str(e))

    async def GetEntityEdge(
        self,
        request: retrieve_service_pb2.GetEntityEdgeRequest,
        context: grpc.aio.ServicerContext,
    ) -> edges_pb2.EntityEdge:
        """Get a specific entity edge by UUID."""
        try:
            from graphiti_core.edges import EntityEdge

            edge = await EntityEdge.get_by_uuid(self.graphiti.driver, request.uuid)
            return entity_edge_to_proto(edge)

        except Exception as e:
            logger.exception(f'Error getting entity edge {request.uuid}')
            await context.abort(grpc.StatusCode.NOT_FOUND, str(e))

    async def GetEntityEdges(
        self,
        request: retrieve_service_pb2.GetEntityEdgesRequest,
        context: grpc.aio.ServicerContext,
    ) -> retrieve_service_pb2.GetEntityEdgesResponse:
        """Get entity edges by multiple UUIDs."""
        try:
            from graphiti_core.edges import EntityEdge

            edges = await EntityEdge.get_by_uuids(self.graphiti.driver, list(request.uuids))

            return retrieve_service_pb2.GetEntityEdgesResponse(
                edges=[entity_edge_to_proto(edge) for edge in edges]
            )

        except Exception as e:
            logger.exception('Error getting entity edges')
            await context.abort(grpc.StatusCode.INTERNAL, str(e))

    async def GetEpisodes(
        self,
        request: retrieve_service_pb2.GetEpisodesRequest,
        context: grpc.aio.ServicerContext,
    ) -> retrieve_service_pb2.GetEpisodesResponse:
        """Get episodes for a group."""
        try:
            last_n = request.last_n if request.HasField('last_n') else 10
            reference_time = datetime.now(timezone.utc)
            if request.HasField('reference_time'):
                parsed_time = timestamp_to_datetime(request.reference_time)
                if parsed_time is not None:
                    reference_time = parsed_time

            episodes = await self.graphiti.retrieve_episodes(
                group_ids=[request.group_id],
                last_n=last_n,
                reference_time=reference_time,
            )

            return retrieve_service_pb2.GetEpisodesResponse(
                episodes=[episodic_node_to_proto(ep) for ep in episodes]
            )

        except Exception as e:
            logger.exception('Error getting episodes')
            await context.abort(grpc.StatusCode.INTERNAL, str(e))

    async def GetMemory(
        self,
        request: retrieve_service_pb2.GetMemoryRequest,
        context: grpc.aio.ServicerContext,
    ) -> retrieve_service_pb2.GetMemoryResponse:
        """Get memory (contextual retrieval based on messages)."""
        try:
            max_facts = request.max_facts if request.HasField('max_facts') else 10

            # Compose query from messages
            combined_query = ''
            for message in request.messages:
                combined_query += (
                    f'{message.role_type or ""}({message.role or ""}): {message.content}\n'
                )

            edges = await self.graphiti.search(
                group_ids=[request.group_id],
                query=combined_query,
                num_results=max_facts,
            )

            facts = [fact_result_from_edge(edge) for edge in edges]

            return retrieve_service_pb2.GetMemoryResponse(facts=facts)

        except Exception as e:
            logger.exception('Error getting memory')
            await context.abort(grpc.StatusCode.INTERNAL, str(e))

    async def GetEntityNode(
        self,
        request: retrieve_service_pb2.GetEntityNodeRequest,
        context: grpc.aio.ServicerContext,
    ) -> nodes_pb2.EntityNode:
        """Get entity node by UUID."""
        try:
            from graphiti_core.nodes import EntityNode

            node = await EntityNode.get_by_uuid(self.graphiti.driver, request.uuid)
            return entity_node_to_proto(node)

        except Exception as e:
            logger.exception(f'Error getting entity node {request.uuid}')
            await context.abort(grpc.StatusCode.NOT_FOUND, str(e))

    async def GetEntityNodes(
        self,
        request: retrieve_service_pb2.GetEntityNodesRequest,
        context: grpc.aio.ServicerContext,
    ) -> retrieve_service_pb2.GetEntityNodesResponse:
        """Get entity nodes by group."""
        try:
            from graphiti_core.nodes import EntityNode

            group_ids = list(request.group_ids) if request.group_ids else []
            limit = None
            uuid_cursor = None

            if request.HasField('pagination'):
                limit = request.pagination.limit if request.pagination.HasField('limit') else None
                uuid_cursor = (
                    request.pagination.uuid_cursor
                    if request.pagination.HasField('uuid_cursor')
                    else None
                )

            nodes = await EntityNode.get_by_group_ids(
                self.graphiti.driver,
                group_ids=group_ids,
                limit=limit,
                uuid_cursor=uuid_cursor,
            )

            next_cursor = nodes[-1].uuid if nodes else None

            return retrieve_service_pb2.GetEntityNodesResponse(
                nodes=[entity_node_to_proto(node) for node in nodes],
                next_cursor=next_cursor,
            )

        except Exception as e:
            logger.exception('Error getting entity nodes')
            await context.abort(grpc.StatusCode.INTERNAL, str(e))

    async def GetCommunities(
        self,
        request: retrieve_service_pb2.GetCommunitiesRequest,
        context: grpc.aio.ServicerContext,
    ) -> retrieve_service_pb2.GetCommunitiesResponse:
        """Get communities by group."""
        try:
            from graphiti_core.nodes import CommunityNode

            group_ids = list(request.group_ids) if request.group_ids else []
            limit = None
            uuid_cursor = None

            if request.HasField('pagination'):
                limit = request.pagination.limit if request.pagination.HasField('limit') else None
                uuid_cursor = (
                    request.pagination.uuid_cursor
                    if request.pagination.HasField('uuid_cursor')
                    else None
                )

            communities = await CommunityNode.get_by_group_ids(
                self.graphiti.driver,
                group_ids=group_ids,
                limit=limit,
                uuid_cursor=uuid_cursor,
            )

            next_cursor = communities[-1].uuid if communities else None

            return retrieve_service_pb2.GetCommunitiesResponse(
                communities=[community_node_to_proto(c) for c in communities],
                next_cursor=next_cursor,
            )

        except Exception as e:
            logger.exception('Error getting communities')
            await context.abort(grpc.StatusCode.INTERNAL, str(e))

    async def RetrieveEpisodes(
        self,
        request: retrieve_service_pb2.RetrieveEpisodesRequest,
        context: grpc.aio.ServicerContext,
    ) -> AsyncIterator[nodes_pb2.EpisodicNode]:
        """Retrieve episodes with filters (streaming)."""
        try:
            group_ids = list(request.group_ids) if request.group_ids else None
            last_n = request.last_n if request.last_n > 0 else 10
            reference_time = timestamp_to_datetime(request.reference_time)
            if reference_time is None:
                reference_time = datetime.now(timezone.utc)

            # Parse optional filters
            source_type = None
            if request.HasField('source'):
                source_type = episode_type_from_proto(request.source)

            saga = request.saga if request.HasField('saga') else None

            episodes = await self.graphiti.retrieve_episodes(
                group_ids=group_ids,
                last_n=last_n,
                reference_time=reference_time,
                source=source_type,
                saga=saga,
            )

            # Stream episodes one by one
            for episode in episodes:
                yield episodic_node_to_proto(episode)

        except Exception as e:
            logger.exception('Error retrieving episodes')
            await context.abort(grpc.StatusCode.INTERNAL, str(e))

    async def GetNodesByEpisodes(
        self,
        request: retrieve_service_pb2.GetNodesByEpisodesRequest,
        context: grpc.aio.ServicerContext,
    ) -> retrieve_service_pb2.GetNodesByEpisodesResponse:
        """Get nodes and edges by episode UUIDs."""
        try:
            from graphiti_core.edges import EntityEdge, EpisodicEdge
            from graphiti_core.nodes import EntityNode

            episode_uuids = list(request.episode_uuids)

            # Get episodic edges for the given episodes
            episodic_edges = await EpisodicEdge.get_by_uuids(
                self.graphiti.driver, episode_uuids
            )

            # Collect unique entity node UUIDs from episodic edges
            entity_uuids = set()
            for edge in episodic_edges:
                entity_uuids.add(edge.target_node_uuid)

            # Get entity nodes
            nodes = []
            if entity_uuids:
                for uuid in entity_uuids:
                    try:
                        node = await EntityNode.get_by_uuid(self.graphiti.driver, uuid)
                        nodes.append(node)
                    except Exception:
                        pass  # Skip nodes that don't exist

            # Get entity edges connected to these nodes
            edges = []
            seen_edge_uuids = set()
            if entity_uuids:
                for node_uuid in entity_uuids:
                    try:
                        node_edges = await EntityEdge.get_by_node_uuid(
                            self.graphiti.driver, node_uuid
                        )
                        for edge in node_edges:
                            if edge.uuid not in seen_edge_uuids:
                                edges.append(edge)
                                seen_edge_uuids.add(edge.uuid)
                    except Exception:
                        pass  # Skip if no edges found

            return retrieve_service_pb2.GetNodesByEpisodesResponse(
                nodes=[entity_node_to_proto(n) for n in nodes],
                edges=[entity_edge_to_proto(e) for e in edges],
            )

        except Exception as e:
            logger.exception('Error getting nodes by episodes')
            await context.abort(grpc.StatusCode.INTERNAL, str(e))

    async def SearchNodes(
        self,
        request: retrieve_service_pb2.SearchNodesRequest,
        context: grpc.aio.ServicerContext,
    ) -> retrieve_service_pb2.SearchNodesResponse:
        """Search nodes by query and entity types."""
        try:
            from graphiti_core.search.search_config import (
                NodeReranker,
                NodeSearchConfig,
                NodeSearchMethod,
                SearchConfig,
            )
            from graphiti_core.search.search_filters import SearchFilters

            group_ids = list(request.group_ids) if request.group_ids else None
            max_nodes = request.max_nodes if request.HasField('max_nodes') else 10
            entity_types = list(request.entity_types) if request.entity_types else None

            # Configure search for nodes only
            config = SearchConfig(
                node_config=NodeSearchConfig(
                    search_methods=[NodeSearchMethod.cosine_similarity, NodeSearchMethod.bm25],
                    reranker=NodeReranker.rrf,
                ),
                limit=max_nodes,
            )

            # Build filters for entity types
            filters = SearchFilters(node_labels=entity_types) if entity_types else SearchFilters()

            results = await self.graphiti.search_(
                group_ids=group_ids,
                query=request.query,
                config=config,
                search_filter=filters,
            )

            return retrieve_service_pb2.SearchNodesResponse(
                nodes=[entity_node_to_proto(n) for n in results.nodes],
                message=f'Found {len(results.nodes)} nodes',
            )

        except Exception as e:
            logger.exception('Error searching nodes')
            await context.abort(grpc.StatusCode.INTERNAL, str(e))

    async def SearchFacts(
        self,
        request: retrieve_service_pb2.SearchFactsRequest,
        context: grpc.aio.ServicerContext,
    ) -> retrieve_service_pb2.SearchFactsResponse:
        """Search facts with optional center node."""
        try:
            group_ids = list(request.group_ids) if request.group_ids else None
            max_facts = request.max_facts if request.HasField('max_facts') else 10
            center_node_uuid = (
                request.center_node_uuid if request.HasField('center_node_uuid') else None
            )

            edges = await self.graphiti.search(
                group_ids=group_ids,
                query=request.query,
                num_results=max_facts,
                center_node_uuid=center_node_uuid,
            )

            facts = [fact_result_from_edge(edge) for edge in edges]

            return retrieve_service_pb2.SearchFactsResponse(
                facts=facts,
                message=f'Found {len(facts)} facts',
            )

        except Exception as e:
            logger.exception('Error searching facts')
            await context.abort(grpc.StatusCode.INTERNAL, str(e))
