"""Converters for edge types between Graphiti core and gRPC messages."""

from datetime import datetime, timezone

from graphiti_core.edges import (
    CommunityEdge,
    EntityEdge,
    EpisodicEdge,
    HasEpisodeEdge,
    NextEpisodeEdge,
)

from src.converters.node_converters import (
    datetime_to_timestamp,
    dict_to_struct,
    struct_to_dict,
    timestamp_to_datetime,
)
from src.generated.graphiti.v1 import edges_pb2


def entity_edge_to_proto(edge: EntityEdge) -> edges_pb2.EntityEdge:
    """Convert Graphiti EntityEdge to proto message."""
    proto_edge = edges_pb2.EntityEdge(
        uuid=edge.uuid,
        group_id=edge.group_id,
        source_node_uuid=edge.source_node_uuid,
        target_node_uuid=edge.target_node_uuid,
        name=edge.name,
        fact=edge.fact,
        episodes=edge.episodes,
    )

    created_at = datetime_to_timestamp(edge.created_at)
    if created_at:
        proto_edge.created_at.CopyFrom(created_at)

    expired_at = datetime_to_timestamp(edge.expired_at)
    if expired_at:
        proto_edge.expired_at.CopyFrom(expired_at)

    valid_at = datetime_to_timestamp(edge.valid_at)
    if valid_at:
        proto_edge.valid_at.CopyFrom(valid_at)

    invalid_at = datetime_to_timestamp(edge.invalid_at)
    if invalid_at:
        proto_edge.invalid_at.CopyFrom(invalid_at)

    if edge.attributes:
        proto_edge.attributes.CopyFrom(dict_to_struct(edge.attributes))

    return proto_edge


def entity_edge_from_proto(proto_edge: edges_pb2.EntityEdge) -> EntityEdge:
    """Convert proto message to Graphiti EntityEdge."""
    created_at = timestamp_to_datetime(proto_edge.created_at)
    expired_at = (
        timestamp_to_datetime(proto_edge.expired_at) if proto_edge.HasField('expired_at') else None
    )
    valid_at = (
        timestamp_to_datetime(proto_edge.valid_at) if proto_edge.HasField('valid_at') else None
    )
    invalid_at = (
        timestamp_to_datetime(proto_edge.invalid_at) if proto_edge.HasField('invalid_at') else None
    )

    return EntityEdge(
        uuid=proto_edge.uuid,
        group_id=proto_edge.group_id,
        source_node_uuid=proto_edge.source_node_uuid,
        target_node_uuid=proto_edge.target_node_uuid,
        created_at=created_at or datetime.now(timezone.utc),
        name=proto_edge.name,
        fact=proto_edge.fact,
        episodes=list(proto_edge.episodes),
        expired_at=expired_at,
        valid_at=valid_at,
        invalid_at=invalid_at,
        attributes=struct_to_dict(proto_edge.attributes)
        if proto_edge.HasField('attributes')
        else {},
    )


def episodic_edge_to_proto(edge: EpisodicEdge) -> edges_pb2.EpisodicEdge:
    """Convert Graphiti EpisodicEdge to proto message."""
    proto_edge = edges_pb2.EpisodicEdge(
        uuid=edge.uuid,
        group_id=edge.group_id,
        source_node_uuid=edge.source_node_uuid,
        target_node_uuid=edge.target_node_uuid,
    )

    created_at = datetime_to_timestamp(edge.created_at)
    if created_at:
        proto_edge.created_at.CopyFrom(created_at)

    return proto_edge


def community_edge_to_proto(edge: CommunityEdge) -> edges_pb2.CommunityEdge:
    """Convert Graphiti CommunityEdge to proto message."""
    proto_edge = edges_pb2.CommunityEdge(
        uuid=edge.uuid,
        group_id=edge.group_id,
        source_node_uuid=edge.source_node_uuid,
        target_node_uuid=edge.target_node_uuid,
    )

    created_at = datetime_to_timestamp(edge.created_at)
    if created_at:
        proto_edge.created_at.CopyFrom(created_at)

    return proto_edge


def has_episode_edge_to_proto(edge: HasEpisodeEdge) -> edges_pb2.HasEpisodeEdge:
    """Convert Graphiti HasEpisodeEdge to proto message."""
    proto_edge = edges_pb2.HasEpisodeEdge(
        uuid=edge.uuid,
        group_id=edge.group_id,
        source_node_uuid=edge.source_node_uuid,
        target_node_uuid=edge.target_node_uuid,
    )

    created_at = datetime_to_timestamp(edge.created_at)
    if created_at:
        proto_edge.created_at.CopyFrom(created_at)

    return proto_edge


def next_episode_edge_to_proto(edge: NextEpisodeEdge) -> edges_pb2.NextEpisodeEdge:
    """Convert Graphiti NextEpisodeEdge to proto message."""
    proto_edge = edges_pb2.NextEpisodeEdge(
        uuid=edge.uuid,
        group_id=edge.group_id,
        source_node_uuid=edge.source_node_uuid,
        target_node_uuid=edge.target_node_uuid,
    )

    created_at = datetime_to_timestamp(edge.created_at)
    if created_at:
        proto_edge.created_at.CopyFrom(created_at)

    return proto_edge


def fact_result_from_edge(edge: EntityEdge) -> edges_pb2.FactResult:
    """Convert Graphiti EntityEdge to FactResult proto message."""
    proto_fact = edges_pb2.FactResult(
        uuid=edge.uuid,
        name=edge.name,
        fact=edge.fact,
    )

    created_at = datetime_to_timestamp(edge.created_at)
    if created_at:
        proto_fact.created_at.CopyFrom(created_at)

    valid_at = datetime_to_timestamp(edge.valid_at)
    if valid_at:
        proto_fact.valid_at.CopyFrom(valid_at)

    invalid_at = datetime_to_timestamp(edge.invalid_at)
    if invalid_at:
        proto_fact.invalid_at.CopyFrom(invalid_at)

    expired_at = datetime_to_timestamp(edge.expired_at)
    if expired_at:
        proto_fact.expired_at.CopyFrom(expired_at)

    return proto_fact


def fact_result_to_proto(
    uuid: str,
    name: str,
    fact: str,
    created_at: datetime,
    valid_at: datetime | None = None,
    invalid_at: datetime | None = None,
    expired_at: datetime | None = None,
) -> edges_pb2.FactResult:
    """Create a FactResult proto message from individual fields."""
    proto_fact = edges_pb2.FactResult(
        uuid=uuid,
        name=name,
        fact=fact,
    )

    ts = datetime_to_timestamp(created_at)
    if ts:
        proto_fact.created_at.CopyFrom(ts)

    if valid_at:
        ts = datetime_to_timestamp(valid_at)
        if ts:
            proto_fact.valid_at.CopyFrom(ts)

    if invalid_at:
        ts = datetime_to_timestamp(invalid_at)
        if ts:
            proto_fact.invalid_at.CopyFrom(ts)

    if expired_at:
        ts = datetime_to_timestamp(expired_at)
        if ts:
            proto_fact.expired_at.CopyFrom(ts)

    return proto_fact
