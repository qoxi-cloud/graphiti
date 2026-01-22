import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from graphiti.v1 import common_pb2 as _common_pb2
from graphiti.v1 import nodes_pb2 as _nodes_pb2
from graphiti.v1 import edges_pb2 as _edges_pb2
from graphiti.v1 import search_pb2 as _search_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class SearchRequest(_message.Message):
    __slots__ = ("group_ids", "query", "max_facts")
    GROUP_IDS_FIELD_NUMBER: _ClassVar[int]
    QUERY_FIELD_NUMBER: _ClassVar[int]
    MAX_FACTS_FIELD_NUMBER: _ClassVar[int]
    group_ids: _containers.RepeatedScalarFieldContainer[str]
    query: str
    max_facts: int
    def __init__(self, group_ids: _Optional[_Iterable[str]] = ..., query: _Optional[str] = ..., max_facts: _Optional[int] = ...) -> None: ...

class SearchResponse(_message.Message):
    __slots__ = ("facts",)
    FACTS_FIELD_NUMBER: _ClassVar[int]
    facts: _containers.RepeatedCompositeFieldContainer[_edges_pb2.FactResult]
    def __init__(self, facts: _Optional[_Iterable[_Union[_edges_pb2.FactResult, _Mapping]]] = ...) -> None: ...

class AdvancedSearchRequest(_message.Message):
    __slots__ = ("group_ids", "query", "config", "filters", "center_node_uuids")
    GROUP_IDS_FIELD_NUMBER: _ClassVar[int]
    QUERY_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    FILTERS_FIELD_NUMBER: _ClassVar[int]
    CENTER_NODE_UUIDS_FIELD_NUMBER: _ClassVar[int]
    group_ids: _containers.RepeatedScalarFieldContainer[str]
    query: str
    config: _search_pb2.SearchConfig
    filters: _search_pb2.SearchFilters
    center_node_uuids: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, group_ids: _Optional[_Iterable[str]] = ..., query: _Optional[str] = ..., config: _Optional[_Union[_search_pb2.SearchConfig, _Mapping]] = ..., filters: _Optional[_Union[_search_pb2.SearchFilters, _Mapping]] = ..., center_node_uuids: _Optional[_Iterable[str]] = ...) -> None: ...

class SearchResultChunk(_message.Message):
    __slots__ = ("edge", "node", "episode", "community", "fact", "score", "is_last")
    EDGE_FIELD_NUMBER: _ClassVar[int]
    NODE_FIELD_NUMBER: _ClassVar[int]
    EPISODE_FIELD_NUMBER: _ClassVar[int]
    COMMUNITY_FIELD_NUMBER: _ClassVar[int]
    FACT_FIELD_NUMBER: _ClassVar[int]
    SCORE_FIELD_NUMBER: _ClassVar[int]
    IS_LAST_FIELD_NUMBER: _ClassVar[int]
    edge: _edges_pb2.EntityEdge
    node: _nodes_pb2.EntityNode
    episode: _nodes_pb2.EpisodicNode
    community: _nodes_pb2.CommunityNode
    fact: _edges_pb2.FactResult
    score: float
    is_last: bool
    def __init__(self, edge: _Optional[_Union[_edges_pb2.EntityEdge, _Mapping]] = ..., node: _Optional[_Union[_nodes_pb2.EntityNode, _Mapping]] = ..., episode: _Optional[_Union[_nodes_pb2.EpisodicNode, _Mapping]] = ..., community: _Optional[_Union[_nodes_pb2.CommunityNode, _Mapping]] = ..., fact: _Optional[_Union[_edges_pb2.FactResult, _Mapping]] = ..., score: _Optional[float] = ..., is_last: bool = ...) -> None: ...

class GetEntityEdgeRequest(_message.Message):
    __slots__ = ("uuid",)
    UUID_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    def __init__(self, uuid: _Optional[str] = ...) -> None: ...

class GetEntityEdgesRequest(_message.Message):
    __slots__ = ("uuids",)
    UUIDS_FIELD_NUMBER: _ClassVar[int]
    uuids: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, uuids: _Optional[_Iterable[str]] = ...) -> None: ...

class GetEntityEdgesResponse(_message.Message):
    __slots__ = ("edges",)
    EDGES_FIELD_NUMBER: _ClassVar[int]
    edges: _containers.RepeatedCompositeFieldContainer[_edges_pb2.EntityEdge]
    def __init__(self, edges: _Optional[_Iterable[_Union[_edges_pb2.EntityEdge, _Mapping]]] = ...) -> None: ...

class GetEpisodesRequest(_message.Message):
    __slots__ = ("group_id", "last_n", "reference_time", "pagination")
    GROUP_ID_FIELD_NUMBER: _ClassVar[int]
    LAST_N_FIELD_NUMBER: _ClassVar[int]
    REFERENCE_TIME_FIELD_NUMBER: _ClassVar[int]
    PAGINATION_FIELD_NUMBER: _ClassVar[int]
    group_id: str
    last_n: int
    reference_time: _timestamp_pb2.Timestamp
    pagination: _common_pb2.PaginationCursor
    def __init__(self, group_id: _Optional[str] = ..., last_n: _Optional[int] = ..., reference_time: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., pagination: _Optional[_Union[_common_pb2.PaginationCursor, _Mapping]] = ...) -> None: ...

class GetEpisodesResponse(_message.Message):
    __slots__ = ("episodes", "next_cursor")
    EPISODES_FIELD_NUMBER: _ClassVar[int]
    NEXT_CURSOR_FIELD_NUMBER: _ClassVar[int]
    episodes: _containers.RepeatedCompositeFieldContainer[_nodes_pb2.EpisodicNode]
    next_cursor: str
    def __init__(self, episodes: _Optional[_Iterable[_Union[_nodes_pb2.EpisodicNode, _Mapping]]] = ..., next_cursor: _Optional[str] = ...) -> None: ...

class GetMemoryRequest(_message.Message):
    __slots__ = ("group_id", "max_facts", "center_node_uuid", "messages")
    GROUP_ID_FIELD_NUMBER: _ClassVar[int]
    MAX_FACTS_FIELD_NUMBER: _ClassVar[int]
    CENTER_NODE_UUID_FIELD_NUMBER: _ClassVar[int]
    MESSAGES_FIELD_NUMBER: _ClassVar[int]
    group_id: str
    max_facts: int
    center_node_uuid: str
    messages: _containers.RepeatedCompositeFieldContainer[_common_pb2.Message]
    def __init__(self, group_id: _Optional[str] = ..., max_facts: _Optional[int] = ..., center_node_uuid: _Optional[str] = ..., messages: _Optional[_Iterable[_Union[_common_pb2.Message, _Mapping]]] = ...) -> None: ...

class GetMemoryResponse(_message.Message):
    __slots__ = ("facts",)
    FACTS_FIELD_NUMBER: _ClassVar[int]
    facts: _containers.RepeatedCompositeFieldContainer[_edges_pb2.FactResult]
    def __init__(self, facts: _Optional[_Iterable[_Union[_edges_pb2.FactResult, _Mapping]]] = ...) -> None: ...

class GetEntityNodeRequest(_message.Message):
    __slots__ = ("uuid",)
    UUID_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    def __init__(self, uuid: _Optional[str] = ...) -> None: ...

class GetEntityNodesRequest(_message.Message):
    __slots__ = ("group_ids", "pagination")
    GROUP_IDS_FIELD_NUMBER: _ClassVar[int]
    PAGINATION_FIELD_NUMBER: _ClassVar[int]
    group_ids: _containers.RepeatedScalarFieldContainer[str]
    pagination: _common_pb2.PaginationCursor
    def __init__(self, group_ids: _Optional[_Iterable[str]] = ..., pagination: _Optional[_Union[_common_pb2.PaginationCursor, _Mapping]] = ...) -> None: ...

class GetEntityNodesResponse(_message.Message):
    __slots__ = ("nodes", "next_cursor")
    NODES_FIELD_NUMBER: _ClassVar[int]
    NEXT_CURSOR_FIELD_NUMBER: _ClassVar[int]
    nodes: _containers.RepeatedCompositeFieldContainer[_nodes_pb2.EntityNode]
    next_cursor: str
    def __init__(self, nodes: _Optional[_Iterable[_Union[_nodes_pb2.EntityNode, _Mapping]]] = ..., next_cursor: _Optional[str] = ...) -> None: ...

class GetCommunitiesRequest(_message.Message):
    __slots__ = ("group_ids", "pagination")
    GROUP_IDS_FIELD_NUMBER: _ClassVar[int]
    PAGINATION_FIELD_NUMBER: _ClassVar[int]
    group_ids: _containers.RepeatedScalarFieldContainer[str]
    pagination: _common_pb2.PaginationCursor
    def __init__(self, group_ids: _Optional[_Iterable[str]] = ..., pagination: _Optional[_Union[_common_pb2.PaginationCursor, _Mapping]] = ...) -> None: ...

class GetCommunitiesResponse(_message.Message):
    __slots__ = ("communities", "next_cursor")
    COMMUNITIES_FIELD_NUMBER: _ClassVar[int]
    NEXT_CURSOR_FIELD_NUMBER: _ClassVar[int]
    communities: _containers.RepeatedCompositeFieldContainer[_nodes_pb2.CommunityNode]
    next_cursor: str
    def __init__(self, communities: _Optional[_Iterable[_Union[_nodes_pb2.CommunityNode, _Mapping]]] = ..., next_cursor: _Optional[str] = ...) -> None: ...

class RetrieveEpisodesRequest(_message.Message):
    __slots__ = ("group_ids", "reference_time", "last_n", "source", "saga")
    GROUP_IDS_FIELD_NUMBER: _ClassVar[int]
    REFERENCE_TIME_FIELD_NUMBER: _ClassVar[int]
    LAST_N_FIELD_NUMBER: _ClassVar[int]
    SOURCE_FIELD_NUMBER: _ClassVar[int]
    SAGA_FIELD_NUMBER: _ClassVar[int]
    group_ids: _containers.RepeatedScalarFieldContainer[str]
    reference_time: _timestamp_pb2.Timestamp
    last_n: int
    source: _common_pb2.EpisodeType
    saga: str
    def __init__(self, group_ids: _Optional[_Iterable[str]] = ..., reference_time: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., last_n: _Optional[int] = ..., source: _Optional[_Union[_common_pb2.EpisodeType, str]] = ..., saga: _Optional[str] = ...) -> None: ...

class GetNodesByEpisodesRequest(_message.Message):
    __slots__ = ("episode_uuids",)
    EPISODE_UUIDS_FIELD_NUMBER: _ClassVar[int]
    episode_uuids: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, episode_uuids: _Optional[_Iterable[str]] = ...) -> None: ...

class GetNodesByEpisodesResponse(_message.Message):
    __slots__ = ("nodes", "edges")
    NODES_FIELD_NUMBER: _ClassVar[int]
    EDGES_FIELD_NUMBER: _ClassVar[int]
    nodes: _containers.RepeatedCompositeFieldContainer[_nodes_pb2.EntityNode]
    edges: _containers.RepeatedCompositeFieldContainer[_edges_pb2.EntityEdge]
    def __init__(self, nodes: _Optional[_Iterable[_Union[_nodes_pb2.EntityNode, _Mapping]]] = ..., edges: _Optional[_Iterable[_Union[_edges_pb2.EntityEdge, _Mapping]]] = ...) -> None: ...

class SearchNodesRequest(_message.Message):
    __slots__ = ("query", "group_ids", "max_nodes", "entity_types")
    QUERY_FIELD_NUMBER: _ClassVar[int]
    GROUP_IDS_FIELD_NUMBER: _ClassVar[int]
    MAX_NODES_FIELD_NUMBER: _ClassVar[int]
    ENTITY_TYPES_FIELD_NUMBER: _ClassVar[int]
    query: str
    group_ids: _containers.RepeatedScalarFieldContainer[str]
    max_nodes: int
    entity_types: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, query: _Optional[str] = ..., group_ids: _Optional[_Iterable[str]] = ..., max_nodes: _Optional[int] = ..., entity_types: _Optional[_Iterable[str]] = ...) -> None: ...

class SearchNodesResponse(_message.Message):
    __slots__ = ("nodes", "message")
    NODES_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    nodes: _containers.RepeatedCompositeFieldContainer[_nodes_pb2.EntityNode]
    message: str
    def __init__(self, nodes: _Optional[_Iterable[_Union[_nodes_pb2.EntityNode, _Mapping]]] = ..., message: _Optional[str] = ...) -> None: ...

class SearchFactsRequest(_message.Message):
    __slots__ = ("query", "group_ids", "max_facts", "center_node_uuid")
    QUERY_FIELD_NUMBER: _ClassVar[int]
    GROUP_IDS_FIELD_NUMBER: _ClassVar[int]
    MAX_FACTS_FIELD_NUMBER: _ClassVar[int]
    CENTER_NODE_UUID_FIELD_NUMBER: _ClassVar[int]
    query: str
    group_ids: _containers.RepeatedScalarFieldContainer[str]
    max_facts: int
    center_node_uuid: str
    def __init__(self, query: _Optional[str] = ..., group_ids: _Optional[_Iterable[str]] = ..., max_facts: _Optional[int] = ..., center_node_uuid: _Optional[str] = ...) -> None: ...

class SearchFactsResponse(_message.Message):
    __slots__ = ("facts", "message")
    FACTS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    facts: _containers.RepeatedCompositeFieldContainer[_edges_pb2.FactResult]
    message: str
    def __init__(self, facts: _Optional[_Iterable[_Union[_edges_pb2.FactResult, _Mapping]]] = ..., message: _Optional[str] = ...) -> None: ...
