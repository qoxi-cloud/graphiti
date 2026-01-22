import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class EpisodicEdge(_message.Message):
    __slots__ = ("uuid", "group_id", "source_node_uuid", "target_node_uuid", "created_at")
    UUID_FIELD_NUMBER: _ClassVar[int]
    GROUP_ID_FIELD_NUMBER: _ClassVar[int]
    SOURCE_NODE_UUID_FIELD_NUMBER: _ClassVar[int]
    TARGET_NODE_UUID_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    group_id: str
    source_node_uuid: str
    target_node_uuid: str
    created_at: _timestamp_pb2.Timestamp
    def __init__(self, uuid: _Optional[str] = ..., group_id: _Optional[str] = ..., source_node_uuid: _Optional[str] = ..., target_node_uuid: _Optional[str] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class EntityEdge(_message.Message):
    __slots__ = ("uuid", "group_id", "source_node_uuid", "target_node_uuid", "created_at", "name", "fact", "episodes", "expired_at", "valid_at", "invalid_at", "attributes")
    UUID_FIELD_NUMBER: _ClassVar[int]
    GROUP_ID_FIELD_NUMBER: _ClassVar[int]
    SOURCE_NODE_UUID_FIELD_NUMBER: _ClassVar[int]
    TARGET_NODE_UUID_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    FACT_FIELD_NUMBER: _ClassVar[int]
    EPISODES_FIELD_NUMBER: _ClassVar[int]
    EXPIRED_AT_FIELD_NUMBER: _ClassVar[int]
    VALID_AT_FIELD_NUMBER: _ClassVar[int]
    INVALID_AT_FIELD_NUMBER: _ClassVar[int]
    ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    group_id: str
    source_node_uuid: str
    target_node_uuid: str
    created_at: _timestamp_pb2.Timestamp
    name: str
    fact: str
    episodes: _containers.RepeatedScalarFieldContainer[str]
    expired_at: _timestamp_pb2.Timestamp
    valid_at: _timestamp_pb2.Timestamp
    invalid_at: _timestamp_pb2.Timestamp
    attributes: _struct_pb2.Struct
    def __init__(self, uuid: _Optional[str] = ..., group_id: _Optional[str] = ..., source_node_uuid: _Optional[str] = ..., target_node_uuid: _Optional[str] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., name: _Optional[str] = ..., fact: _Optional[str] = ..., episodes: _Optional[_Iterable[str]] = ..., expired_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., valid_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., invalid_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., attributes: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class CommunityEdge(_message.Message):
    __slots__ = ("uuid", "group_id", "source_node_uuid", "target_node_uuid", "created_at")
    UUID_FIELD_NUMBER: _ClassVar[int]
    GROUP_ID_FIELD_NUMBER: _ClassVar[int]
    SOURCE_NODE_UUID_FIELD_NUMBER: _ClassVar[int]
    TARGET_NODE_UUID_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    group_id: str
    source_node_uuid: str
    target_node_uuid: str
    created_at: _timestamp_pb2.Timestamp
    def __init__(self, uuid: _Optional[str] = ..., group_id: _Optional[str] = ..., source_node_uuid: _Optional[str] = ..., target_node_uuid: _Optional[str] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class HasEpisodeEdge(_message.Message):
    __slots__ = ("uuid", "group_id", "source_node_uuid", "target_node_uuid", "created_at")
    UUID_FIELD_NUMBER: _ClassVar[int]
    GROUP_ID_FIELD_NUMBER: _ClassVar[int]
    SOURCE_NODE_UUID_FIELD_NUMBER: _ClassVar[int]
    TARGET_NODE_UUID_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    group_id: str
    source_node_uuid: str
    target_node_uuid: str
    created_at: _timestamp_pb2.Timestamp
    def __init__(self, uuid: _Optional[str] = ..., group_id: _Optional[str] = ..., source_node_uuid: _Optional[str] = ..., target_node_uuid: _Optional[str] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class NextEpisodeEdge(_message.Message):
    __slots__ = ("uuid", "group_id", "source_node_uuid", "target_node_uuid", "created_at")
    UUID_FIELD_NUMBER: _ClassVar[int]
    GROUP_ID_FIELD_NUMBER: _ClassVar[int]
    SOURCE_NODE_UUID_FIELD_NUMBER: _ClassVar[int]
    TARGET_NODE_UUID_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    group_id: str
    source_node_uuid: str
    target_node_uuid: str
    created_at: _timestamp_pb2.Timestamp
    def __init__(self, uuid: _Optional[str] = ..., group_id: _Optional[str] = ..., source_node_uuid: _Optional[str] = ..., target_node_uuid: _Optional[str] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class FactResult(_message.Message):
    __slots__ = ("uuid", "name", "fact", "valid_at", "invalid_at", "created_at", "expired_at")
    UUID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    FACT_FIELD_NUMBER: _ClassVar[int]
    VALID_AT_FIELD_NUMBER: _ClassVar[int]
    INVALID_AT_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    EXPIRED_AT_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    name: str
    fact: str
    valid_at: _timestamp_pb2.Timestamp
    invalid_at: _timestamp_pb2.Timestamp
    created_at: _timestamp_pb2.Timestamp
    expired_at: _timestamp_pb2.Timestamp
    def __init__(self, uuid: _Optional[str] = ..., name: _Optional[str] = ..., fact: _Optional[str] = ..., valid_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., invalid_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., expired_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...
