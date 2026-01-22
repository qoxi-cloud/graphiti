import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from graphiti.v1 import common_pb2 as _common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class EpisodicNode(_message.Message):
    __slots__ = ("uuid", "name", "group_id", "labels", "created_at", "source", "source_description", "content", "valid_at", "entity_edges")
    UUID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    GROUP_ID_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    SOURCE_FIELD_NUMBER: _ClassVar[int]
    SOURCE_DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    VALID_AT_FIELD_NUMBER: _ClassVar[int]
    ENTITY_EDGES_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    name: str
    group_id: str
    labels: _containers.RepeatedScalarFieldContainer[str]
    created_at: _timestamp_pb2.Timestamp
    source: _common_pb2.EpisodeType
    source_description: str
    content: str
    valid_at: _timestamp_pb2.Timestamp
    entity_edges: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, uuid: _Optional[str] = ..., name: _Optional[str] = ..., group_id: _Optional[str] = ..., labels: _Optional[_Iterable[str]] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., source: _Optional[_Union[_common_pb2.EpisodeType, str]] = ..., source_description: _Optional[str] = ..., content: _Optional[str] = ..., valid_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., entity_edges: _Optional[_Iterable[str]] = ...) -> None: ...

class EntityNode(_message.Message):
    __slots__ = ("uuid", "name", "group_id", "labels", "created_at", "summary", "attributes")
    UUID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    GROUP_ID_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    SUMMARY_FIELD_NUMBER: _ClassVar[int]
    ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    name: str
    group_id: str
    labels: _containers.RepeatedScalarFieldContainer[str]
    created_at: _timestamp_pb2.Timestamp
    summary: str
    attributes: _struct_pb2.Struct
    def __init__(self, uuid: _Optional[str] = ..., name: _Optional[str] = ..., group_id: _Optional[str] = ..., labels: _Optional[_Iterable[str]] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., summary: _Optional[str] = ..., attributes: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class CommunityNode(_message.Message):
    __slots__ = ("uuid", "name", "group_id", "labels", "created_at", "summary")
    UUID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    GROUP_ID_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    SUMMARY_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    name: str
    group_id: str
    labels: _containers.RepeatedScalarFieldContainer[str]
    created_at: _timestamp_pb2.Timestamp
    summary: str
    def __init__(self, uuid: _Optional[str] = ..., name: _Optional[str] = ..., group_id: _Optional[str] = ..., labels: _Optional[_Iterable[str]] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., summary: _Optional[str] = ...) -> None: ...

class SagaNode(_message.Message):
    __slots__ = ("uuid", "name", "group_id", "labels", "created_at")
    UUID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    GROUP_ID_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    name: str
    group_id: str
    labels: _containers.RepeatedScalarFieldContainer[str]
    created_at: _timestamp_pb2.Timestamp
    def __init__(self, uuid: _Optional[str] = ..., name: _Optional[str] = ..., group_id: _Optional[str] = ..., labels: _Optional[_Iterable[str]] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...
