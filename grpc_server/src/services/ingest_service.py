"""IngestService implementation for handling data ingestion."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import AsyncIterator
from uuid import uuid4

import grpc
from graphiti_core.nodes import EntityNode, EpisodeType

from src.converters.edge_converters import entity_edge_to_proto
from src.converters.node_converters import (
    entity_node_to_proto,
    episode_type_from_proto,
    episodic_node_to_proto,
    timestamp_to_datetime,
)
from src.generated.graphiti.v1 import (
    common_pb2,
    ingest_service_pb2,
    ingest_service_pb2_grpc,
    nodes_pb2,
)
from src.services.base import BaseServicer

logger = logging.getLogger(__name__)


class IngestServiceServicer(BaseServicer, ingest_service_pb2_grpc.IngestServiceServicer):
    """gRPC service implementation for data ingestion."""

    async def AddEpisode(
        self,
        request: ingest_service_pb2.AddEpisodeRequest,
        context: grpc.aio.ServicerContext,
    ) -> ingest_service_pb2.AddEpisodeResponse:
        """Add a single episode to the graph."""
        try:
            # Parse request
            uuid = request.uuid if request.uuid else str(uuid4())
            reference_time = timestamp_to_datetime(request.reference_time)
            if reference_time is None:
                reference_time = datetime.now(timezone.utc)

            source = episode_type_from_proto(request.source)
            saga = request.saga if request.saga else None

            # New fields from updated proto
            update_communities = request.update_communities
            saga_previous_episode_uuid = (
                request.saga_previous_episode_uuid if request.saga_previous_episode_uuid else None
            )
            previous_episode_uuids = (
                list(request.previous_episode_uuids) if request.previous_episode_uuids else None
            )
            custom_extraction_instructions = (
                request.custom_extraction_instructions
                if request.custom_extraction_instructions
                else None
            )

            # Add episode with all parameters
            result = await self.graphiti.add_episode(
                uuid=uuid,
                group_id=request.group_id,
                name=request.name,
                episode_body=request.episode_body,
                reference_time=reference_time,
                source=source,
                source_description=request.source_description,
                saga=saga,
                update_communities=update_communities,
                saga_previous_episode_uuid=saga_previous_episode_uuid,
                previous_episode_uuids=previous_episode_uuids,
                custom_extraction_instructions=custom_extraction_instructions,
            )

            # Build response
            response = ingest_service_pb2.AddEpisodeResponse()

            if result.episode:
                response.episode.CopyFrom(episodic_node_to_proto(result.episode))

            for node in result.nodes:
                response.nodes.append(entity_node_to_proto(node))

            for edge in result.edges:
                response.edges.append(entity_edge_to_proto(edge))

            return response

        except Exception as e:
            logger.exception('Error adding episode')
            await context.abort(grpc.StatusCode.INTERNAL, str(e))

    async def AddEpisodeBulk(
        self,
        request: ingest_service_pb2.AddEpisodeBulkRequest,
        context: grpc.aio.ServicerContext,
    ) -> AsyncIterator[ingest_service_pb2.AddEpisodeBulkProgress]:
        """Add multiple episodes in bulk with progress streaming."""
        total = len(request.episodes)
        completed = 0
        failed = 0
        results = []

        for episode_request in request.episodes:
            try:
                # Progress update
                yield ingest_service_pb2.AddEpisodeBulkProgress(
                    total=total,
                    completed=completed,
                    failed=failed,
                    current_uuid=episode_request.uuid or 'generating...',
                    is_complete=False,
                )

                # Add episode
                uuid = episode_request.uuid if episode_request.uuid else str(uuid4())
                reference_time = timestamp_to_datetime(episode_request.reference_time)
                if reference_time is None:
                    reference_time = datetime.now(timezone.utc)

                source = episode_type_from_proto(episode_request.source)
                saga = episode_request.saga if episode_request.saga else None

                # New fields from updated proto
                update_communities = episode_request.update_communities
                saga_previous_episode_uuid = (
                    episode_request.saga_previous_episode_uuid
                    if episode_request.saga_previous_episode_uuid
                    else None
                )
                previous_episode_uuids = (
                    list(episode_request.previous_episode_uuids)
                    if episode_request.previous_episode_uuids
                    else None
                )
                custom_extraction_instructions = (
                    episode_request.custom_extraction_instructions
                    if episode_request.custom_extraction_instructions
                    else None
                )

                result = await self.graphiti.add_episode(
                    uuid=uuid,
                    group_id=episode_request.group_id,
                    name=episode_request.name,
                    episode_body=episode_request.episode_body,
                    reference_time=reference_time,
                    source=source,
                    source_description=episode_request.source_description,
                    saga=saga,
                    update_communities=update_communities,
                    saga_previous_episode_uuid=saga_previous_episode_uuid,
                    previous_episode_uuids=previous_episode_uuids,
                    custom_extraction_instructions=custom_extraction_instructions,
                )

                # Build result
                response = ingest_service_pb2.AddEpisodeResponse()
                if result.episode:
                    response.episode.CopyFrom(episodic_node_to_proto(result.episode))
                for node in result.nodes:
                    response.nodes.append(entity_node_to_proto(node))
                for edge in result.edges:
                    response.edges.append(entity_edge_to_proto(edge))

                results.append(response)
                completed += 1

            except Exception as e:
                logger.exception(f'Error adding episode {episode_request.uuid}')
                failed += 1
                yield ingest_service_pb2.AddEpisodeBulkProgress(
                    total=total,
                    completed=completed,
                    failed=failed,
                    current_uuid=episode_request.uuid,
                    error_message=str(e),
                    is_complete=False,
                )

        # Final progress with all results
        yield ingest_service_pb2.AddEpisodeBulkProgress(
            total=total,
            completed=completed,
            failed=failed,
            is_complete=True,
            results=results,
        )

    async def AddMessages(
        self,
        request: ingest_service_pb2.AddMessagesRequest,
        context: grpc.aio.ServicerContext,
    ) -> ingest_service_pb2.AddMessagesResponse:
        """Add messages (chat/conversation format)."""
        try:
            queued_count = 0

            for message in request.messages:
                uuid = message.uuid if message.uuid else str(uuid4())
                timestamp = timestamp_to_datetime(message.timestamp)
                if timestamp is None:
                    timestamp = datetime.now(timezone.utc)

                # Format episode body in message format
                episode_body = f'{message.role or ""}({message.role_type}): {message.content}'

                # Add episode asynchronously (fire and forget pattern)
                asyncio.create_task(
                    self.graphiti.add_episode(
                        uuid=uuid,
                        group_id=request.group_id,
                        name=message.name,
                        episode_body=episode_body,
                        reference_time=timestamp,
                        source=EpisodeType.message,
                        source_description=message.source_description,
                    )
                )
                queued_count += 1

            return ingest_service_pb2.AddMessagesResponse(
                result=common_pb2.OperationResult(
                    success=True,
                    message='Messages added to processing queue',
                ),
                queued_count=queued_count,
            )

        except Exception as e:
            logger.exception('Error adding messages')
            await context.abort(grpc.StatusCode.INTERNAL, str(e))

    async def AddEntityNode(
        self,
        request: ingest_service_pb2.AddEntityNodeRequest,
        context: grpc.aio.ServicerContext,
    ) -> nodes_pb2.EntityNode:
        """Add an entity node directly."""
        try:
            uuid = request.uuid if request.uuid else str(uuid4())
            summary = request.summary if request.summary else ''

            # Create the entity node
            node = EntityNode(
                name=request.name,
                uuid=uuid,
                group_id=request.group_id,
                summary=summary,
            )

            # Generate embedding and save to graph
            await node.generate_name_embedding(self.graphiti.embedder)
            await node.save(self.graphiti.driver)

            return entity_node_to_proto(node)

        except Exception as e:
            logger.exception('Error adding entity node')
            await context.abort(grpc.StatusCode.INTERNAL, str(e))

    async def AddTriplet(
        self,
        request: ingest_service_pb2.AddTripletRequest,
        context: grpc.aio.ServicerContext,
    ) -> ingest_service_pb2.AddTripletResponse:
        """Add a triplet (subject-predicate-object) directly."""
        try:
            from graphiti_core.edges import EntityEdge

            subject_uuid = request.subject_uuid if request.subject_uuid else str(uuid4())
            object_uuid = request.object_uuid if request.object_uuid else str(uuid4())
            edge_uuid = str(uuid4())
            now = datetime.now(timezone.utc)

            valid_at = (
                timestamp_to_datetime(request.valid_at) if request.HasField('valid_at') else now
            )
            invalid_at = (
                timestamp_to_datetime(request.invalid_at)
                if request.HasField('invalid_at')
                else None
            )

            # Create source node
            source_node = EntityNode(
                uuid=subject_uuid,
                name=request.subject_name,
                group_id=request.group_id,
                summary='',
            )

            # Create target node
            target_node = EntityNode(
                uuid=object_uuid,
                name=request.object_name,
                group_id=request.group_id,
                summary='',
            )

            # Create edge
            edge = EntityEdge(
                uuid=edge_uuid,
                source_node_uuid=subject_uuid,
                target_node_uuid=object_uuid,
                group_id=request.group_id,
                name=request.predicate,
                fact=f'{request.subject_name} {request.predicate} {request.object_name}',
                created_at=now,
                valid_at=valid_at,
                invalid_at=invalid_at,
            )

            result = await self.graphiti.add_triplet(
                source_node=source_node,
                edge=edge,
                target_node=target_node,
            )

            # AddTripletResults has nodes and edges lists
            subject_node_result = result.nodes[0] if result.nodes else source_node
            object_node_result = result.nodes[1] if len(result.nodes) > 1 else target_node
            edge_result = result.edges[0] if result.edges else edge

            return ingest_service_pb2.AddTripletResponse(
                subject_node=entity_node_to_proto(subject_node_result),
                object_node=entity_node_to_proto(object_node_result),
                edge=entity_edge_to_proto(edge_result),
            )

        except Exception as e:
            logger.exception('Error adding triplet')
            await context.abort(grpc.StatusCode.INTERNAL, str(e))

    async def StreamEpisodes(
        self,
        request_iterator: AsyncIterator[ingest_service_pb2.StreamEpisodeRequest],
        context: grpc.aio.ServicerContext,
    ) -> AsyncIterator[ingest_service_pb2.StreamEpisodeResponse]:
        """Bidirectional streaming for continuous episode ingestion."""
        async for request in request_iterator:
            correlation_id = request.correlation_id if request.correlation_id else None
            episode_request = request.episode

            try:
                uuid = episode_request.uuid if episode_request.uuid else str(uuid4())
                reference_time = timestamp_to_datetime(episode_request.reference_time)
                if reference_time is None:
                    reference_time = datetime.now(timezone.utc)

                source = episode_type_from_proto(episode_request.source)
                saga = episode_request.saga if episode_request.saga else None

                # New fields from updated proto
                update_communities = episode_request.update_communities
                saga_previous_episode_uuid = (
                    episode_request.saga_previous_episode_uuid
                    if episode_request.saga_previous_episode_uuid
                    else None
                )
                previous_episode_uuids = (
                    list(episode_request.previous_episode_uuids)
                    if episode_request.previous_episode_uuids
                    else None
                )
                custom_extraction_instructions = (
                    episode_request.custom_extraction_instructions
                    if episode_request.custom_extraction_instructions
                    else None
                )

                result = await self.graphiti.add_episode(
                    uuid=uuid,
                    group_id=episode_request.group_id,
                    name=episode_request.name,
                    episode_body=episode_request.episode_body,
                    reference_time=reference_time,
                    source=source,
                    source_description=episode_request.source_description,
                    saga=saga,
                    update_communities=update_communities,
                    saga_previous_episode_uuid=saga_previous_episode_uuid,
                    previous_episode_uuids=previous_episode_uuids,
                    custom_extraction_instructions=custom_extraction_instructions,
                )

                # Build success response
                response = ingest_service_pb2.AddEpisodeResponse()
                if result.episode:
                    response.episode.CopyFrom(episodic_node_to_proto(result.episode))
                for node in result.nodes:
                    response.nodes.append(entity_node_to_proto(node))
                for edge in result.edges:
                    response.edges.append(entity_edge_to_proto(edge))

                yield ingest_service_pb2.StreamEpisodeResponse(
                    correlation_id=correlation_id,
                    success=response,
                )

            except Exception as e:
                logger.exception('Error processing streamed episode')
                yield ingest_service_pb2.StreamEpisodeResponse(
                    correlation_id=correlation_id,
                    error=str(e),
                )
