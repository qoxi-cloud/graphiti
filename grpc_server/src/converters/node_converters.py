"""Converters for node types between Graphiti core and gRPC messages."""

from datetime import datetime, timezone
from typing import Any

from google.protobuf.struct_pb2 import Struct
from google.protobuf.timestamp_pb2 import Timestamp
from graphiti_core.nodes import (
    CommunityNode,
    EntityNode,
    EpisodeType,
    EpisodicNode,
    SagaNode,
)

from src.generated.graphiti.v1 import common_pb2, nodes_pb2


def datetime_to_timestamp(dt: datetime | None) -> Timestamp | None:
    """Convert Python datetime to protobuf Timestamp."""
    if dt is None:
        return None
    ts = Timestamp()
    ts.FromDatetime(dt)
    return ts


def timestamp_to_datetime(ts: Timestamp | None) -> datetime | None:
    """Convert protobuf Timestamp to Python datetime."""
    if ts is None or (ts.seconds == 0 and ts.nanos == 0):
        return None
    return ts.ToDatetime(tzinfo=timezone.utc)


def episode_type_to_proto(et: EpisodeType) -> common_pb2.EpisodeType:
    """Convert Graphiti EpisodeType to proto enum."""
    mapping = {
        EpisodeType.message: common_pb2.EPISODE_TYPE_MESSAGE,
        EpisodeType.json: common_pb2.EPISODE_TYPE_JSON,
        EpisodeType.text: common_pb2.EPISODE_TYPE_TEXT,
    }
    return mapping.get(et, common_pb2.EPISODE_TYPE_UNSPECIFIED)


def episode_type_from_proto(et: common_pb2.EpisodeType) -> EpisodeType:
    """Convert proto enum to Graphiti EpisodeType."""
    mapping = {
        common_pb2.EPISODE_TYPE_MESSAGE: EpisodeType.message,
        common_pb2.EPISODE_TYPE_JSON: EpisodeType.json,
        common_pb2.EPISODE_TYPE_TEXT: EpisodeType.text,
    }
    return mapping.get(et, EpisodeType.text)


def dict_to_struct(d: dict[str, Any] | None) -> Struct:
    """Convert Python dict to protobuf Struct."""
    s = Struct()
    if d:
        s.update(d)
    return s


def struct_to_dict(s: Struct | None) -> dict[str, Any]:
    """Convert protobuf Struct to Python dict."""
    if s is None:
        return {}
    from google.protobuf.json_format import MessageToDict

    return MessageToDict(s)


def entity_node_to_proto(node: EntityNode) -> nodes_pb2.EntityNode:
    """Convert Graphiti EntityNode to proto message."""
    proto_node = nodes_pb2.EntityNode(
        uuid=node.uuid,
        name=node.name,
        group_id=node.group_id,
        labels=node.labels,
        summary=node.summary,
    )

    created_at = datetime_to_timestamp(node.created_at)
    if created_at:
        proto_node.created_at.CopyFrom(created_at)

    if node.attributes:
        proto_node.attributes.CopyFrom(dict_to_struct(node.attributes))

    return proto_node


def entity_node_from_proto(proto_node: nodes_pb2.EntityNode) -> EntityNode:
    """Convert proto message to Graphiti EntityNode."""
    created_at = timestamp_to_datetime(proto_node.created_at)

    return EntityNode(
        uuid=proto_node.uuid,
        name=proto_node.name,
        group_id=proto_node.group_id,
        labels=list(proto_node.labels),
        created_at=created_at or datetime.now(timezone.utc),
        summary=proto_node.summary,
        attributes=struct_to_dict(proto_node.attributes)
        if proto_node.HasField('attributes')
        else {},
    )


def episodic_node_to_proto(node: EpisodicNode) -> nodes_pb2.EpisodicNode:
    """Convert Graphiti EpisodicNode to proto message."""
    proto_node = nodes_pb2.EpisodicNode(
        uuid=node.uuid,
        name=node.name,
        group_id=node.group_id,
        labels=node.labels,
        source=episode_type_to_proto(node.source),
        source_description=node.source_description,
        content=node.content,
        entity_edges=node.entity_edges,
    )

    created_at = datetime_to_timestamp(node.created_at)
    if created_at:
        proto_node.created_at.CopyFrom(created_at)

    valid_at = datetime_to_timestamp(node.valid_at)
    if valid_at:
        proto_node.valid_at.CopyFrom(valid_at)

    return proto_node


def episodic_node_from_proto(proto_node: nodes_pb2.EpisodicNode) -> EpisodicNode:
    """Convert proto message to Graphiti EpisodicNode."""
    created_at = timestamp_to_datetime(proto_node.created_at)
    valid_at = timestamp_to_datetime(proto_node.valid_at)

    return EpisodicNode(
        uuid=proto_node.uuid,
        name=proto_node.name,
        group_id=proto_node.group_id,
        labels=list(proto_node.labels),
        created_at=created_at or datetime.now(timezone.utc),
        source=episode_type_from_proto(proto_node.source),
        source_description=proto_node.source_description,
        content=proto_node.content,
        valid_at=valid_at or datetime.now(timezone.utc),
        entity_edges=list(proto_node.entity_edges),
    )


def community_node_to_proto(node: CommunityNode) -> nodes_pb2.CommunityNode:
    """Convert Graphiti CommunityNode to proto message."""
    proto_node = nodes_pb2.CommunityNode(
        uuid=node.uuid,
        name=node.name,
        group_id=node.group_id,
        labels=node.labels,
        summary=node.summary,
    )

    created_at = datetime_to_timestamp(node.created_at)
    if created_at:
        proto_node.created_at.CopyFrom(created_at)

    return proto_node


def saga_node_to_proto(node: SagaNode) -> nodes_pb2.SagaNode:
    """Convert Graphiti SagaNode to proto message."""
    proto_node = nodes_pb2.SagaNode(
        uuid=node.uuid,
        name=node.name,
        group_id=node.group_id,
        labels=node.labels,
    )

    created_at = datetime_to_timestamp(node.created_at)
    if created_at:
        proto_node.created_at.CopyFrom(created_at)

    return proto_node
