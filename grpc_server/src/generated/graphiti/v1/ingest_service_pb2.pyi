import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from graphiti.v1 import common_pb2 as _common_pb2
from graphiti.v1 import nodes_pb2 as _nodes_pb2
from graphiti.v1 import edges_pb2 as _edges_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class AddEpisodeRequest(_message.Message):
    __slots__ = ("uuid", "group_id", "name", "episode_body", "reference_time", "source", "source_description", "saga", "entity_types", "update_communities", "saga_previous_episode_uuid", "previous_episode_uuids", "custom_extraction_instructions")
    UUID_FIELD_NUMBER: _ClassVar[int]
    GROUP_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    EPISODE_BODY_FIELD_NUMBER: _ClassVar[int]
    REFERENCE_TIME_FIELD_NUMBER: _ClassVar[int]
    SOURCE_FIELD_NUMBER: _ClassVar[int]
    SOURCE_DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    SAGA_FIELD_NUMBER: _ClassVar[int]
    ENTITY_TYPES_FIELD_NUMBER: _ClassVar[int]
    UPDATE_COMMUNITIES_FIELD_NUMBER: _ClassVar[int]
    SAGA_PREVIOUS_EPISODE_UUID_FIELD_NUMBER: _ClassVar[int]
    PREVIOUS_EPISODE_UUIDS_FIELD_NUMBER: _ClassVar[int]
    CUSTOM_EXTRACTION_INSTRUCTIONS_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    group_id: str
    name: str
    episode_body: str
    reference_time: _timestamp_pb2.Timestamp
    source: _common_pb2.EpisodeType
    source_description: str
    saga: str
    entity_types: _struct_pb2.Struct
    update_communities: bool
    saga_previous_episode_uuid: str
    previous_episode_uuids: _containers.RepeatedScalarFieldContainer[str]
    custom_extraction_instructions: str
    def __init__(self, uuid: _Optional[str] = ..., group_id: _Optional[str] = ..., name: _Optional[str] = ..., episode_body: _Optional[str] = ..., reference_time: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., source: _Optional[_Union[_common_pb2.EpisodeType, str]] = ..., source_description: _Optional[str] = ..., saga: _Optional[str] = ..., entity_types: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., update_communities: bool = ..., saga_previous_episode_uuid: _Optional[str] = ..., previous_episode_uuids: _Optional[_Iterable[str]] = ..., custom_extraction_instructions: _Optional[str] = ...) -> None: ...

class AddEpisodeResponse(_message.Message):
    __slots__ = ("episode", "nodes", "edges")
    EPISODE_FIELD_NUMBER: _ClassVar[int]
    NODES_FIELD_NUMBER: _ClassVar[int]
    EDGES_FIELD_NUMBER: _ClassVar[int]
    episode: _nodes_pb2.EpisodicNode
    nodes: _containers.RepeatedCompositeFieldContainer[_nodes_pb2.EntityNode]
    edges: _containers.RepeatedCompositeFieldContainer[_edges_pb2.EntityEdge]
    def __init__(self, episode: _Optional[_Union[_nodes_pb2.EpisodicNode, _Mapping]] = ..., nodes: _Optional[_Iterable[_Union[_nodes_pb2.EntityNode, _Mapping]]] = ..., edges: _Optional[_Iterable[_Union[_edges_pb2.EntityEdge, _Mapping]]] = ...) -> None: ...

class AddEpisodeBulkRequest(_message.Message):
    __slots__ = ("episodes",)
    EPISODES_FIELD_NUMBER: _ClassVar[int]
    episodes: _containers.RepeatedCompositeFieldContainer[AddEpisodeRequest]
    def __init__(self, episodes: _Optional[_Iterable[_Union[AddEpisodeRequest, _Mapping]]] = ...) -> None: ...

class AddEpisodeBulkProgress(_message.Message):
    __slots__ = ("total", "completed", "failed", "current_uuid", "error_message", "is_complete", "results")
    TOTAL_FIELD_NUMBER: _ClassVar[int]
    COMPLETED_FIELD_NUMBER: _ClassVar[int]
    FAILED_FIELD_NUMBER: _ClassVar[int]
    CURRENT_UUID_FIELD_NUMBER: _ClassVar[int]
    ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    IS_COMPLETE_FIELD_NUMBER: _ClassVar[int]
    RESULTS_FIELD_NUMBER: _ClassVar[int]
    total: int
    completed: int
    failed: int
    current_uuid: str
    error_message: str
    is_complete: bool
    results: _containers.RepeatedCompositeFieldContainer[AddEpisodeResponse]
    def __init__(self, total: _Optional[int] = ..., completed: _Optional[int] = ..., failed: _Optional[int] = ..., current_uuid: _Optional[str] = ..., error_message: _Optional[str] = ..., is_complete: bool = ..., results: _Optional[_Iterable[_Union[AddEpisodeResponse, _Mapping]]] = ...) -> None: ...

class AddMessagesRequest(_message.Message):
    __slots__ = ("group_id", "messages")
    GROUP_ID_FIELD_NUMBER: _ClassVar[int]
    MESSAGES_FIELD_NUMBER: _ClassVar[int]
    group_id: str
    messages: _containers.RepeatedCompositeFieldContainer[_common_pb2.Message]
    def __init__(self, group_id: _Optional[str] = ..., messages: _Optional[_Iterable[_Union[_common_pb2.Message, _Mapping]]] = ...) -> None: ...

class AddMessagesResponse(_message.Message):
    __slots__ = ("result", "queued_count")
    RESULT_FIELD_NUMBER: _ClassVar[int]
    QUEUED_COUNT_FIELD_NUMBER: _ClassVar[int]
    result: _common_pb2.OperationResult
    queued_count: int
    def __init__(self, result: _Optional[_Union[_common_pb2.OperationResult, _Mapping]] = ..., queued_count: _Optional[int] = ...) -> None: ...

class AddEntityNodeRequest(_message.Message):
    __slots__ = ("uuid", "group_id", "name", "summary", "labels", "attributes")
    UUID_FIELD_NUMBER: _ClassVar[int]
    GROUP_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    SUMMARY_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    group_id: str
    name: str
    summary: str
    labels: _containers.RepeatedScalarFieldContainer[str]
    attributes: _struct_pb2.Struct
    def __init__(self, uuid: _Optional[str] = ..., group_id: _Optional[str] = ..., name: _Optional[str] = ..., summary: _Optional[str] = ..., labels: _Optional[_Iterable[str]] = ..., attributes: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class AddTripletRequest(_message.Message):
    __slots__ = ("group_id", "subject_name", "predicate", "object_name", "subject_uuid", "object_uuid", "valid_at", "invalid_at")
    GROUP_ID_FIELD_NUMBER: _ClassVar[int]
    SUBJECT_NAME_FIELD_NUMBER: _ClassVar[int]
    PREDICATE_FIELD_NUMBER: _ClassVar[int]
    OBJECT_NAME_FIELD_NUMBER: _ClassVar[int]
    SUBJECT_UUID_FIELD_NUMBER: _ClassVar[int]
    OBJECT_UUID_FIELD_NUMBER: _ClassVar[int]
    VALID_AT_FIELD_NUMBER: _ClassVar[int]
    INVALID_AT_FIELD_NUMBER: _ClassVar[int]
    group_id: str
    subject_name: str
    predicate: str
    object_name: str
    subject_uuid: str
    object_uuid: str
    valid_at: _timestamp_pb2.Timestamp
    invalid_at: _timestamp_pb2.Timestamp
    def __init__(self, group_id: _Optional[str] = ..., subject_name: _Optional[str] = ..., predicate: _Optional[str] = ..., object_name: _Optional[str] = ..., subject_uuid: _Optional[str] = ..., object_uuid: _Optional[str] = ..., valid_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., invalid_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class AddTripletResponse(_message.Message):
    __slots__ = ("subject_node", "object_node", "edge")
    SUBJECT_NODE_FIELD_NUMBER: _ClassVar[int]
    OBJECT_NODE_FIELD_NUMBER: _ClassVar[int]
    EDGE_FIELD_NUMBER: _ClassVar[int]
    subject_node: _nodes_pb2.EntityNode
    object_node: _nodes_pb2.EntityNode
    edge: _edges_pb2.EntityEdge
    def __init__(self, subject_node: _Optional[_Union[_nodes_pb2.EntityNode, _Mapping]] = ..., object_node: _Optional[_Union[_nodes_pb2.EntityNode, _Mapping]] = ..., edge: _Optional[_Union[_edges_pb2.EntityEdge, _Mapping]] = ...) -> None: ...

class StreamEpisodeRequest(_message.Message):
    __slots__ = ("episode", "correlation_id")
    EPISODE_FIELD_NUMBER: _ClassVar[int]
    CORRELATION_ID_FIELD_NUMBER: _ClassVar[int]
    episode: AddEpisodeRequest
    correlation_id: str
    def __init__(self, episode: _Optional[_Union[AddEpisodeRequest, _Mapping]] = ..., correlation_id: _Optional[str] = ...) -> None: ...

class StreamEpisodeResponse(_message.Message):
    __slots__ = ("correlation_id", "success", "error")
    CORRELATION_ID_FIELD_NUMBER: _ClassVar[int]
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    correlation_id: str
    success: AddEpisodeResponse
    error: str
    def __init__(self, correlation_id: _Optional[str] = ..., success: _Optional[_Union[AddEpisodeResponse, _Mapping]] = ..., error: _Optional[str] = ...) -> None: ...
