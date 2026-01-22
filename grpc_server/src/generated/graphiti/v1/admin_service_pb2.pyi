from graphiti.v1 import common_pb2 as _common_pb2
from graphiti.v1 import nodes_pb2 as _nodes_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class HealthCheckRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class HealthCheckResponse(_message.Message):
    __slots__ = ("status", "message")
    class ServingStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        SERVING_STATUS_UNSPECIFIED: _ClassVar[HealthCheckResponse.ServingStatus]
        SERVING_STATUS_SERVING: _ClassVar[HealthCheckResponse.ServingStatus]
        SERVING_STATUS_NOT_SERVING: _ClassVar[HealthCheckResponse.ServingStatus]
    SERVING_STATUS_UNSPECIFIED: HealthCheckResponse.ServingStatus
    SERVING_STATUS_SERVING: HealthCheckResponse.ServingStatus
    SERVING_STATUS_NOT_SERVING: HealthCheckResponse.ServingStatus
    STATUS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    status: HealthCheckResponse.ServingStatus
    message: str
    def __init__(self, status: _Optional[_Union[HealthCheckResponse.ServingStatus, str]] = ..., message: _Optional[str] = ...) -> None: ...

class GetStatusRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetStatusResponse(_message.Message):
    __slots__ = ("version", "database_provider", "llm_provider", "embedder_provider", "database_connected", "uptime_seconds")
    VERSION_FIELD_NUMBER: _ClassVar[int]
    DATABASE_PROVIDER_FIELD_NUMBER: _ClassVar[int]
    LLM_PROVIDER_FIELD_NUMBER: _ClassVar[int]
    EMBEDDER_PROVIDER_FIELD_NUMBER: _ClassVar[int]
    DATABASE_CONNECTED_FIELD_NUMBER: _ClassVar[int]
    UPTIME_SECONDS_FIELD_NUMBER: _ClassVar[int]
    version: str
    database_provider: str
    llm_provider: str
    embedder_provider: str
    database_connected: bool
    uptime_seconds: int
    def __init__(self, version: _Optional[str] = ..., database_provider: _Optional[str] = ..., llm_provider: _Optional[str] = ..., embedder_provider: _Optional[str] = ..., database_connected: bool = ..., uptime_seconds: _Optional[int] = ...) -> None: ...

class DeleteEntityEdgeRequest(_message.Message):
    __slots__ = ("uuid",)
    UUID_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    def __init__(self, uuid: _Optional[str] = ...) -> None: ...

class DeleteEntityEdgesRequest(_message.Message):
    __slots__ = ("uuids",)
    UUIDS_FIELD_NUMBER: _ClassVar[int]
    uuids: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, uuids: _Optional[_Iterable[str]] = ...) -> None: ...

class DeleteGroupRequest(_message.Message):
    __slots__ = ("group_id",)
    GROUP_ID_FIELD_NUMBER: _ClassVar[int]
    group_id: str
    def __init__(self, group_id: _Optional[str] = ...) -> None: ...

class DeleteEpisodeRequest(_message.Message):
    __slots__ = ("uuid",)
    UUID_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    def __init__(self, uuid: _Optional[str] = ...) -> None: ...

class DeleteEpisodesRequest(_message.Message):
    __slots__ = ("uuids",)
    UUIDS_FIELD_NUMBER: _ClassVar[int]
    uuids: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, uuids: _Optional[_Iterable[str]] = ...) -> None: ...

class DeleteEntityNodeRequest(_message.Message):
    __slots__ = ("uuid",)
    UUID_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    def __init__(self, uuid: _Optional[str] = ...) -> None: ...

class ClearDataRequest(_message.Message):
    __slots__ = ("confirm",)
    CONFIRM_FIELD_NUMBER: _ClassVar[int]
    confirm: bool
    def __init__(self, confirm: bool = ...) -> None: ...

class BuildIndicesRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RemoveEpisodeRequest(_message.Message):
    __slots__ = ("uuid",)
    UUID_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    def __init__(self, uuid: _Optional[str] = ...) -> None: ...

class RemoveEpisodeResponse(_message.Message):
    __slots__ = ("result", "orphaned_nodes_removed", "orphaned_edges_removed")
    RESULT_FIELD_NUMBER: _ClassVar[int]
    ORPHANED_NODES_REMOVED_FIELD_NUMBER: _ClassVar[int]
    ORPHANED_EDGES_REMOVED_FIELD_NUMBER: _ClassVar[int]
    result: _common_pb2.OperationResult
    orphaned_nodes_removed: int
    orphaned_edges_removed: int
    def __init__(self, result: _Optional[_Union[_common_pb2.OperationResult, _Mapping]] = ..., orphaned_nodes_removed: _Optional[int] = ..., orphaned_edges_removed: _Optional[int] = ...) -> None: ...

class BuildCommunitiesRequest(_message.Message):
    __slots__ = ("group_ids",)
    GROUP_IDS_FIELD_NUMBER: _ClassVar[int]
    group_ids: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, group_ids: _Optional[_Iterable[str]] = ...) -> None: ...

class BuildCommunitiesResponse(_message.Message):
    __slots__ = ("communities", "total_created")
    COMMUNITIES_FIELD_NUMBER: _ClassVar[int]
    TOTAL_CREATED_FIELD_NUMBER: _ClassVar[int]
    communities: _containers.RepeatedCompositeFieldContainer[_nodes_pb2.CommunityNode]
    total_created: int
    def __init__(self, communities: _Optional[_Iterable[_Union[_nodes_pb2.CommunityNode, _Mapping]]] = ..., total_created: _Optional[int] = ...) -> None: ...
