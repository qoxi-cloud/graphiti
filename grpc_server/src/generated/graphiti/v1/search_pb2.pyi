from graphiti.v1 import common_pb2 as _common_pb2
from graphiti.v1 import nodes_pb2 as _nodes_pb2
from graphiti.v1 import edges_pb2 as _edges_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class EdgeSearchMethod(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    EDGE_SEARCH_METHOD_UNSPECIFIED: _ClassVar[EdgeSearchMethod]
    EDGE_SEARCH_METHOD_COSINE_SIMILARITY: _ClassVar[EdgeSearchMethod]
    EDGE_SEARCH_METHOD_BM25: _ClassVar[EdgeSearchMethod]
    EDGE_SEARCH_METHOD_BFS: _ClassVar[EdgeSearchMethod]

class NodeSearchMethod(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    NODE_SEARCH_METHOD_UNSPECIFIED: _ClassVar[NodeSearchMethod]
    NODE_SEARCH_METHOD_COSINE_SIMILARITY: _ClassVar[NodeSearchMethod]
    NODE_SEARCH_METHOD_BM25: _ClassVar[NodeSearchMethod]
    NODE_SEARCH_METHOD_BFS: _ClassVar[NodeSearchMethod]

class EpisodeSearchMethod(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    EPISODE_SEARCH_METHOD_UNSPECIFIED: _ClassVar[EpisodeSearchMethod]
    EPISODE_SEARCH_METHOD_BM25: _ClassVar[EpisodeSearchMethod]

class CommunitySearchMethod(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    COMMUNITY_SEARCH_METHOD_UNSPECIFIED: _ClassVar[CommunitySearchMethod]
    COMMUNITY_SEARCH_METHOD_COSINE_SIMILARITY: _ClassVar[CommunitySearchMethod]
    COMMUNITY_SEARCH_METHOD_BM25: _ClassVar[CommunitySearchMethod]

class EdgeReranker(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    EDGE_RERANKER_UNSPECIFIED: _ClassVar[EdgeReranker]
    EDGE_RERANKER_RRF: _ClassVar[EdgeReranker]
    EDGE_RERANKER_NODE_DISTANCE: _ClassVar[EdgeReranker]
    EDGE_RERANKER_EPISODE_MENTIONS: _ClassVar[EdgeReranker]
    EDGE_RERANKER_MMR: _ClassVar[EdgeReranker]
    EDGE_RERANKER_CROSS_ENCODER: _ClassVar[EdgeReranker]

class NodeReranker(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    NODE_RERANKER_UNSPECIFIED: _ClassVar[NodeReranker]
    NODE_RERANKER_RRF: _ClassVar[NodeReranker]
    NODE_RERANKER_NODE_DISTANCE: _ClassVar[NodeReranker]
    NODE_RERANKER_EPISODE_MENTIONS: _ClassVar[NodeReranker]
    NODE_RERANKER_MMR: _ClassVar[NodeReranker]
    NODE_RERANKER_CROSS_ENCODER: _ClassVar[NodeReranker]

class EpisodeReranker(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    EPISODE_RERANKER_UNSPECIFIED: _ClassVar[EpisodeReranker]
    EPISODE_RERANKER_RRF: _ClassVar[EpisodeReranker]
    EPISODE_RERANKER_CROSS_ENCODER: _ClassVar[EpisodeReranker]

class CommunityReranker(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    COMMUNITY_RERANKER_UNSPECIFIED: _ClassVar[CommunityReranker]
    COMMUNITY_RERANKER_RRF: _ClassVar[CommunityReranker]
    COMMUNITY_RERANKER_MMR: _ClassVar[CommunityReranker]
    COMMUNITY_RERANKER_CROSS_ENCODER: _ClassVar[CommunityReranker]
EDGE_SEARCH_METHOD_UNSPECIFIED: EdgeSearchMethod
EDGE_SEARCH_METHOD_COSINE_SIMILARITY: EdgeSearchMethod
EDGE_SEARCH_METHOD_BM25: EdgeSearchMethod
EDGE_SEARCH_METHOD_BFS: EdgeSearchMethod
NODE_SEARCH_METHOD_UNSPECIFIED: NodeSearchMethod
NODE_SEARCH_METHOD_COSINE_SIMILARITY: NodeSearchMethod
NODE_SEARCH_METHOD_BM25: NodeSearchMethod
NODE_SEARCH_METHOD_BFS: NodeSearchMethod
EPISODE_SEARCH_METHOD_UNSPECIFIED: EpisodeSearchMethod
EPISODE_SEARCH_METHOD_BM25: EpisodeSearchMethod
COMMUNITY_SEARCH_METHOD_UNSPECIFIED: CommunitySearchMethod
COMMUNITY_SEARCH_METHOD_COSINE_SIMILARITY: CommunitySearchMethod
COMMUNITY_SEARCH_METHOD_BM25: CommunitySearchMethod
EDGE_RERANKER_UNSPECIFIED: EdgeReranker
EDGE_RERANKER_RRF: EdgeReranker
EDGE_RERANKER_NODE_DISTANCE: EdgeReranker
EDGE_RERANKER_EPISODE_MENTIONS: EdgeReranker
EDGE_RERANKER_MMR: EdgeReranker
EDGE_RERANKER_CROSS_ENCODER: EdgeReranker
NODE_RERANKER_UNSPECIFIED: NodeReranker
NODE_RERANKER_RRF: NodeReranker
NODE_RERANKER_NODE_DISTANCE: NodeReranker
NODE_RERANKER_EPISODE_MENTIONS: NodeReranker
NODE_RERANKER_MMR: NodeReranker
NODE_RERANKER_CROSS_ENCODER: NodeReranker
EPISODE_RERANKER_UNSPECIFIED: EpisodeReranker
EPISODE_RERANKER_RRF: EpisodeReranker
EPISODE_RERANKER_CROSS_ENCODER: EpisodeReranker
COMMUNITY_RERANKER_UNSPECIFIED: CommunityReranker
COMMUNITY_RERANKER_RRF: CommunityReranker
COMMUNITY_RERANKER_MMR: CommunityReranker
COMMUNITY_RERANKER_CROSS_ENCODER: CommunityReranker

class EdgeSearchConfig(_message.Message):
    __slots__ = ("search_methods", "reranker", "sim_min_score", "mmr_lambda", "bfs_max_depth")
    SEARCH_METHODS_FIELD_NUMBER: _ClassVar[int]
    RERANKER_FIELD_NUMBER: _ClassVar[int]
    SIM_MIN_SCORE_FIELD_NUMBER: _ClassVar[int]
    MMR_LAMBDA_FIELD_NUMBER: _ClassVar[int]
    BFS_MAX_DEPTH_FIELD_NUMBER: _ClassVar[int]
    search_methods: _containers.RepeatedScalarFieldContainer[EdgeSearchMethod]
    reranker: EdgeReranker
    sim_min_score: float
    mmr_lambda: float
    bfs_max_depth: int
    def __init__(self, search_methods: _Optional[_Iterable[_Union[EdgeSearchMethod, str]]] = ..., reranker: _Optional[_Union[EdgeReranker, str]] = ..., sim_min_score: _Optional[float] = ..., mmr_lambda: _Optional[float] = ..., bfs_max_depth: _Optional[int] = ...) -> None: ...

class NodeSearchConfig(_message.Message):
    __slots__ = ("search_methods", "reranker", "sim_min_score", "mmr_lambda", "bfs_max_depth")
    SEARCH_METHODS_FIELD_NUMBER: _ClassVar[int]
    RERANKER_FIELD_NUMBER: _ClassVar[int]
    SIM_MIN_SCORE_FIELD_NUMBER: _ClassVar[int]
    MMR_LAMBDA_FIELD_NUMBER: _ClassVar[int]
    BFS_MAX_DEPTH_FIELD_NUMBER: _ClassVar[int]
    search_methods: _containers.RepeatedScalarFieldContainer[NodeSearchMethod]
    reranker: NodeReranker
    sim_min_score: float
    mmr_lambda: float
    bfs_max_depth: int
    def __init__(self, search_methods: _Optional[_Iterable[_Union[NodeSearchMethod, str]]] = ..., reranker: _Optional[_Union[NodeReranker, str]] = ..., sim_min_score: _Optional[float] = ..., mmr_lambda: _Optional[float] = ..., bfs_max_depth: _Optional[int] = ...) -> None: ...

class EpisodeSearchConfig(_message.Message):
    __slots__ = ("search_methods", "reranker", "sim_min_score", "mmr_lambda", "bfs_max_depth")
    SEARCH_METHODS_FIELD_NUMBER: _ClassVar[int]
    RERANKER_FIELD_NUMBER: _ClassVar[int]
    SIM_MIN_SCORE_FIELD_NUMBER: _ClassVar[int]
    MMR_LAMBDA_FIELD_NUMBER: _ClassVar[int]
    BFS_MAX_DEPTH_FIELD_NUMBER: _ClassVar[int]
    search_methods: _containers.RepeatedScalarFieldContainer[EpisodeSearchMethod]
    reranker: EpisodeReranker
    sim_min_score: float
    mmr_lambda: float
    bfs_max_depth: int
    def __init__(self, search_methods: _Optional[_Iterable[_Union[EpisodeSearchMethod, str]]] = ..., reranker: _Optional[_Union[EpisodeReranker, str]] = ..., sim_min_score: _Optional[float] = ..., mmr_lambda: _Optional[float] = ..., bfs_max_depth: _Optional[int] = ...) -> None: ...

class CommunitySearchConfig(_message.Message):
    __slots__ = ("search_methods", "reranker", "sim_min_score", "mmr_lambda", "bfs_max_depth")
    SEARCH_METHODS_FIELD_NUMBER: _ClassVar[int]
    RERANKER_FIELD_NUMBER: _ClassVar[int]
    SIM_MIN_SCORE_FIELD_NUMBER: _ClassVar[int]
    MMR_LAMBDA_FIELD_NUMBER: _ClassVar[int]
    BFS_MAX_DEPTH_FIELD_NUMBER: _ClassVar[int]
    search_methods: _containers.RepeatedScalarFieldContainer[CommunitySearchMethod]
    reranker: CommunityReranker
    sim_min_score: float
    mmr_lambda: float
    bfs_max_depth: int
    def __init__(self, search_methods: _Optional[_Iterable[_Union[CommunitySearchMethod, str]]] = ..., reranker: _Optional[_Union[CommunityReranker, str]] = ..., sim_min_score: _Optional[float] = ..., mmr_lambda: _Optional[float] = ..., bfs_max_depth: _Optional[int] = ...) -> None: ...

class SearchConfig(_message.Message):
    __slots__ = ("edge_config", "node_config", "episode_config", "community_config", "limit", "reranker_min_score")
    EDGE_CONFIG_FIELD_NUMBER: _ClassVar[int]
    NODE_CONFIG_FIELD_NUMBER: _ClassVar[int]
    EPISODE_CONFIG_FIELD_NUMBER: _ClassVar[int]
    COMMUNITY_CONFIG_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    RERANKER_MIN_SCORE_FIELD_NUMBER: _ClassVar[int]
    edge_config: EdgeSearchConfig
    node_config: NodeSearchConfig
    episode_config: EpisodeSearchConfig
    community_config: CommunitySearchConfig
    limit: int
    reranker_min_score: float
    def __init__(self, edge_config: _Optional[_Union[EdgeSearchConfig, _Mapping]] = ..., node_config: _Optional[_Union[NodeSearchConfig, _Mapping]] = ..., episode_config: _Optional[_Union[EpisodeSearchConfig, _Mapping]] = ..., community_config: _Optional[_Union[CommunitySearchConfig, _Mapping]] = ..., limit: _Optional[int] = ..., reranker_min_score: _Optional[float] = ...) -> None: ...

class SearchFilters(_message.Message):
    __slots__ = ("node_labels", "edge_types", "valid_at", "invalid_at", "created_at", "expired_at", "edge_uuids", "property_filters")
    NODE_LABELS_FIELD_NUMBER: _ClassVar[int]
    EDGE_TYPES_FIELD_NUMBER: _ClassVar[int]
    VALID_AT_FIELD_NUMBER: _ClassVar[int]
    INVALID_AT_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    EXPIRED_AT_FIELD_NUMBER: _ClassVar[int]
    EDGE_UUIDS_FIELD_NUMBER: _ClassVar[int]
    PROPERTY_FILTERS_FIELD_NUMBER: _ClassVar[int]
    node_labels: _containers.RepeatedScalarFieldContainer[str]
    edge_types: _containers.RepeatedScalarFieldContainer[str]
    valid_at: _containers.RepeatedCompositeFieldContainer[DateFilterGroup]
    invalid_at: _containers.RepeatedCompositeFieldContainer[DateFilterGroup]
    created_at: _containers.RepeatedCompositeFieldContainer[DateFilterGroup]
    expired_at: _containers.RepeatedCompositeFieldContainer[DateFilterGroup]
    edge_uuids: _containers.RepeatedScalarFieldContainer[str]
    property_filters: _containers.RepeatedCompositeFieldContainer[_common_pb2.PropertyFilter]
    def __init__(self, node_labels: _Optional[_Iterable[str]] = ..., edge_types: _Optional[_Iterable[str]] = ..., valid_at: _Optional[_Iterable[_Union[DateFilterGroup, _Mapping]]] = ..., invalid_at: _Optional[_Iterable[_Union[DateFilterGroup, _Mapping]]] = ..., created_at: _Optional[_Iterable[_Union[DateFilterGroup, _Mapping]]] = ..., expired_at: _Optional[_Iterable[_Union[DateFilterGroup, _Mapping]]] = ..., edge_uuids: _Optional[_Iterable[str]] = ..., property_filters: _Optional[_Iterable[_Union[_common_pb2.PropertyFilter, _Mapping]]] = ...) -> None: ...

class DateFilterGroup(_message.Message):
    __slots__ = ("filters",)
    FILTERS_FIELD_NUMBER: _ClassVar[int]
    filters: _containers.RepeatedCompositeFieldContainer[_common_pb2.DateFilter]
    def __init__(self, filters: _Optional[_Iterable[_Union[_common_pb2.DateFilter, _Mapping]]] = ...) -> None: ...

class SearchResults(_message.Message):
    __slots__ = ("edges", "edge_reranker_scores", "nodes", "node_reranker_scores", "episodes", "episode_reranker_scores", "communities", "community_reranker_scores")
    EDGES_FIELD_NUMBER: _ClassVar[int]
    EDGE_RERANKER_SCORES_FIELD_NUMBER: _ClassVar[int]
    NODES_FIELD_NUMBER: _ClassVar[int]
    NODE_RERANKER_SCORES_FIELD_NUMBER: _ClassVar[int]
    EPISODES_FIELD_NUMBER: _ClassVar[int]
    EPISODE_RERANKER_SCORES_FIELD_NUMBER: _ClassVar[int]
    COMMUNITIES_FIELD_NUMBER: _ClassVar[int]
    COMMUNITY_RERANKER_SCORES_FIELD_NUMBER: _ClassVar[int]
    edges: _containers.RepeatedCompositeFieldContainer[_edges_pb2.EntityEdge]
    edge_reranker_scores: _containers.RepeatedScalarFieldContainer[float]
    nodes: _containers.RepeatedCompositeFieldContainer[_nodes_pb2.EntityNode]
    node_reranker_scores: _containers.RepeatedScalarFieldContainer[float]
    episodes: _containers.RepeatedCompositeFieldContainer[_nodes_pb2.EpisodicNode]
    episode_reranker_scores: _containers.RepeatedScalarFieldContainer[float]
    communities: _containers.RepeatedCompositeFieldContainer[_nodes_pb2.CommunityNode]
    community_reranker_scores: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, edges: _Optional[_Iterable[_Union[_edges_pb2.EntityEdge, _Mapping]]] = ..., edge_reranker_scores: _Optional[_Iterable[float]] = ..., nodes: _Optional[_Iterable[_Union[_nodes_pb2.EntityNode, _Mapping]]] = ..., node_reranker_scores: _Optional[_Iterable[float]] = ..., episodes: _Optional[_Iterable[_Union[_nodes_pb2.EpisodicNode, _Mapping]]] = ..., episode_reranker_scores: _Optional[_Iterable[float]] = ..., communities: _Optional[_Iterable[_Union[_nodes_pb2.CommunityNode, _Mapping]]] = ..., community_reranker_scores: _Optional[_Iterable[float]] = ...) -> None: ...
