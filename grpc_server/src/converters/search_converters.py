"""Converters for search types between Graphiti core and gRPC messages."""

from graphiti_core.search.search_config import (
    CommunityReranker,
    CommunitySearchConfig,
    CommunitySearchMethod,
    EdgeReranker,
    EdgeSearchConfig,
    EdgeSearchMethod,
    EpisodeReranker,
    EpisodeSearchConfig,
    EpisodeSearchMethod,
    NodeReranker,
    NodeSearchConfig,
    NodeSearchMethod,
    SearchConfig,
    SearchResults,
)
from graphiti_core.search.search_filters import (
    ComparisonOperator,
    DateFilter,
    PropertyFilter,
    SearchFilters,
)

from src.converters.edge_converters import entity_edge_to_proto
from src.converters.node_converters import (
    community_node_to_proto,
    entity_node_to_proto,
    episodic_node_to_proto,
    timestamp_to_datetime,
)
from src.generated.graphiti.v1 import common_pb2, search_pb2

# Edge search method mappings
EDGE_SEARCH_METHOD_TO_PROTO = {
    EdgeSearchMethod.cosine_similarity: search_pb2.EDGE_SEARCH_METHOD_COSINE_SIMILARITY,
    EdgeSearchMethod.bm25: search_pb2.EDGE_SEARCH_METHOD_BM25,
    EdgeSearchMethod.bfs: search_pb2.EDGE_SEARCH_METHOD_BFS,
}

EDGE_SEARCH_METHOD_FROM_PROTO = {v: k for k, v in EDGE_SEARCH_METHOD_TO_PROTO.items()}

# Edge reranker mappings
EDGE_RERANKER_TO_PROTO = {
    EdgeReranker.rrf: search_pb2.EDGE_RERANKER_RRF,
    EdgeReranker.node_distance: search_pb2.EDGE_RERANKER_NODE_DISTANCE,
    EdgeReranker.episode_mentions: search_pb2.EDGE_RERANKER_EPISODE_MENTIONS,
    EdgeReranker.mmr: search_pb2.EDGE_RERANKER_MMR,
    EdgeReranker.cross_encoder: search_pb2.EDGE_RERANKER_CROSS_ENCODER,
}

EDGE_RERANKER_FROM_PROTO = {v: k for k, v in EDGE_RERANKER_TO_PROTO.items()}

# Node search method mappings
NODE_SEARCH_METHOD_TO_PROTO = {
    NodeSearchMethod.cosine_similarity: search_pb2.NODE_SEARCH_METHOD_COSINE_SIMILARITY,
    NodeSearchMethod.bm25: search_pb2.NODE_SEARCH_METHOD_BM25,
    NodeSearchMethod.bfs: search_pb2.NODE_SEARCH_METHOD_BFS,
}

NODE_SEARCH_METHOD_FROM_PROTO = {v: k for k, v in NODE_SEARCH_METHOD_TO_PROTO.items()}

# Node reranker mappings
NODE_RERANKER_TO_PROTO = {
    NodeReranker.rrf: search_pb2.NODE_RERANKER_RRF,
    NodeReranker.node_distance: search_pb2.NODE_RERANKER_NODE_DISTANCE,
    NodeReranker.episode_mentions: search_pb2.NODE_RERANKER_EPISODE_MENTIONS,
    NodeReranker.mmr: search_pb2.NODE_RERANKER_MMR,
    NodeReranker.cross_encoder: search_pb2.NODE_RERANKER_CROSS_ENCODER,
}

NODE_RERANKER_FROM_PROTO = {v: k for k, v in NODE_RERANKER_TO_PROTO.items()}

# Episode search method mappings
EPISODE_SEARCH_METHOD_TO_PROTO = {
    EpisodeSearchMethod.bm25: search_pb2.EPISODE_SEARCH_METHOD_BM25,
}

EPISODE_SEARCH_METHOD_FROM_PROTO = {v: k for k, v in EPISODE_SEARCH_METHOD_TO_PROTO.items()}

# Episode reranker mappings
EPISODE_RERANKER_TO_PROTO = {
    EpisodeReranker.rrf: search_pb2.EPISODE_RERANKER_RRF,
    EpisodeReranker.cross_encoder: search_pb2.EPISODE_RERANKER_CROSS_ENCODER,
}

EPISODE_RERANKER_FROM_PROTO = {v: k for k, v in EPISODE_RERANKER_TO_PROTO.items()}

# Community search method mappings
COMMUNITY_SEARCH_METHOD_TO_PROTO = {
    CommunitySearchMethod.cosine_similarity: search_pb2.COMMUNITY_SEARCH_METHOD_COSINE_SIMILARITY,
    CommunitySearchMethod.bm25: search_pb2.COMMUNITY_SEARCH_METHOD_BM25,
}

COMMUNITY_SEARCH_METHOD_FROM_PROTO = {v: k for k, v in COMMUNITY_SEARCH_METHOD_TO_PROTO.items()}

# Community reranker mappings
COMMUNITY_RERANKER_TO_PROTO = {
    CommunityReranker.rrf: search_pb2.COMMUNITY_RERANKER_RRF,
    CommunityReranker.mmr: search_pb2.COMMUNITY_RERANKER_MMR,
    CommunityReranker.cross_encoder: search_pb2.COMMUNITY_RERANKER_CROSS_ENCODER,
}

COMMUNITY_RERANKER_FROM_PROTO = {v: k for k, v in COMMUNITY_RERANKER_TO_PROTO.items()}

# Comparison operator mappings
COMPARISON_OPERATOR_TO_PROTO = {
    ComparisonOperator.equals: common_pb2.COMPARISON_OPERATOR_EQUALS,
    ComparisonOperator.not_equals: common_pb2.COMPARISON_OPERATOR_NOT_EQUALS,
    ComparisonOperator.greater_than: common_pb2.COMPARISON_OPERATOR_GREATER_THAN,
    ComparisonOperator.less_than: common_pb2.COMPARISON_OPERATOR_LESS_THAN,
    ComparisonOperator.greater_than_equal: common_pb2.COMPARISON_OPERATOR_GREATER_THAN_EQUAL,
    ComparisonOperator.less_than_equal: common_pb2.COMPARISON_OPERATOR_LESS_THAN_EQUAL,
    ComparisonOperator.is_null: common_pb2.COMPARISON_OPERATOR_IS_NULL,
    ComparisonOperator.is_not_null: common_pb2.COMPARISON_OPERATOR_IS_NOT_NULL,
}

COMPARISON_OPERATOR_FROM_PROTO = {v: k for k, v in COMPARISON_OPERATOR_TO_PROTO.items()}


def edge_search_config_from_proto(
    proto_config: search_pb2.EdgeSearchConfig | None,
) -> EdgeSearchConfig | None:
    """Convert proto EdgeSearchConfig to Graphiti EdgeSearchConfig."""
    if proto_config is None:
        return None

    search_methods = [
        EDGE_SEARCH_METHOD_FROM_PROTO.get(m, EdgeSearchMethod.cosine_similarity)
        for m in proto_config.search_methods
    ]

    return EdgeSearchConfig(
        search_methods=search_methods,
        reranker=EDGE_RERANKER_FROM_PROTO.get(proto_config.reranker, EdgeReranker.rrf),
        sim_min_score=proto_config.sim_min_score if proto_config.HasField('sim_min_score') else 0.0,
        mmr_lambda=proto_config.mmr_lambda if proto_config.HasField('mmr_lambda') else 0.5,
        bfs_max_depth=proto_config.bfs_max_depth if proto_config.HasField('bfs_max_depth') else 3,
    )


def node_search_config_from_proto(
    proto_config: search_pb2.NodeSearchConfig | None,
) -> NodeSearchConfig | None:
    """Convert proto NodeSearchConfig to Graphiti NodeSearchConfig."""
    if proto_config is None:
        return None

    search_methods = [
        NODE_SEARCH_METHOD_FROM_PROTO.get(m, NodeSearchMethod.cosine_similarity)
        for m in proto_config.search_methods
    ]

    return NodeSearchConfig(
        search_methods=search_methods,
        reranker=NODE_RERANKER_FROM_PROTO.get(proto_config.reranker, NodeReranker.rrf),
        sim_min_score=proto_config.sim_min_score if proto_config.HasField('sim_min_score') else 0.0,
        mmr_lambda=proto_config.mmr_lambda if proto_config.HasField('mmr_lambda') else 0.5,
        bfs_max_depth=proto_config.bfs_max_depth if proto_config.HasField('bfs_max_depth') else 3,
    )


def episode_search_config_from_proto(
    proto_config: search_pb2.EpisodeSearchConfig | None,
) -> EpisodeSearchConfig | None:
    """Convert proto EpisodeSearchConfig to Graphiti EpisodeSearchConfig."""
    if proto_config is None:
        return None

    search_methods = [
        EPISODE_SEARCH_METHOD_FROM_PROTO.get(m, EpisodeSearchMethod.bm25)
        for m in proto_config.search_methods
    ]

    return EpisodeSearchConfig(
        search_methods=search_methods,
        reranker=EPISODE_RERANKER_FROM_PROTO.get(proto_config.reranker, EpisodeReranker.rrf),
        sim_min_score=proto_config.sim_min_score if proto_config.HasField('sim_min_score') else 0.0,
        mmr_lambda=proto_config.mmr_lambda if proto_config.HasField('mmr_lambda') else 0.5,
        bfs_max_depth=proto_config.bfs_max_depth if proto_config.HasField('bfs_max_depth') else 3,
    )


def community_search_config_from_proto(
    proto_config: search_pb2.CommunitySearchConfig | None,
) -> CommunitySearchConfig | None:
    """Convert proto CommunitySearchConfig to Graphiti CommunitySearchConfig."""
    if proto_config is None:
        return None

    search_methods = [
        COMMUNITY_SEARCH_METHOD_FROM_PROTO.get(m, CommunitySearchMethod.cosine_similarity)
        for m in proto_config.search_methods
    ]

    return CommunitySearchConfig(
        search_methods=search_methods,
        reranker=COMMUNITY_RERANKER_FROM_PROTO.get(proto_config.reranker, CommunityReranker.rrf),
        sim_min_score=proto_config.sim_min_score if proto_config.HasField('sim_min_score') else 0.0,
        mmr_lambda=proto_config.mmr_lambda if proto_config.HasField('mmr_lambda') else 0.5,
        bfs_max_depth=proto_config.bfs_max_depth if proto_config.HasField('bfs_max_depth') else 3,
    )


def search_config_from_proto(proto_config: search_pb2.SearchConfig | None) -> SearchConfig:
    """Convert proto SearchConfig to Graphiti SearchConfig."""
    if proto_config is None:
        return SearchConfig()

    return SearchConfig(
        edge_config=edge_search_config_from_proto(
            proto_config.edge_config if proto_config.HasField('edge_config') else None
        ),
        node_config=node_search_config_from_proto(
            proto_config.node_config if proto_config.HasField('node_config') else None
        ),
        episode_config=episode_search_config_from_proto(
            proto_config.episode_config if proto_config.HasField('episode_config') else None
        ),
        community_config=community_search_config_from_proto(
            proto_config.community_config if proto_config.HasField('community_config') else None
        ),
        limit=proto_config.limit if proto_config.HasField('limit') else 10,
        reranker_min_score=proto_config.reranker_min_score
        if proto_config.HasField('reranker_min_score')
        else 0.0,
    )


def date_filter_from_proto(proto_filter: common_pb2.DateFilter) -> DateFilter:
    """Convert proto DateFilter to Graphiti DateFilter."""
    date = timestamp_to_datetime(proto_filter.date) if proto_filter.HasField('date') else None
    op = COMPARISON_OPERATOR_FROM_PROTO.get(
        proto_filter.comparison_operator, ComparisonOperator.equals
    )

    return DateFilter(date=date, comparison_operator=op)


def property_filter_from_proto(proto_filter: common_pb2.PropertyFilter) -> PropertyFilter:
    """Convert proto PropertyFilter to Graphiti PropertyFilter."""
    value = None
    if proto_filter.HasField('string_value'):
        value = proto_filter.string_value
    elif proto_filter.HasField('int_value'):
        value = proto_filter.int_value
    elif proto_filter.HasField('float_value'):
        value = proto_filter.float_value

    op = COMPARISON_OPERATOR_FROM_PROTO.get(
        proto_filter.comparison_operator, ComparisonOperator.equals
    )

    return PropertyFilter(
        property_name=proto_filter.property_name,
        property_value=value,
        comparison_operator=op,
    )


def search_filters_from_proto(proto_filters: search_pb2.SearchFilters | None) -> SearchFilters:
    """Convert proto SearchFilters to Graphiti SearchFilters."""
    if proto_filters is None:
        return SearchFilters()

    # Convert date filter groups
    valid_at = None
    if proto_filters.valid_at:
        valid_at = [
            [date_filter_from_proto(df) for df in group.filters] for group in proto_filters.valid_at
        ]

    invalid_at = None
    if proto_filters.invalid_at:
        invalid_at = [
            [date_filter_from_proto(df) for df in group.filters]
            for group in proto_filters.invalid_at
        ]

    created_at = None
    if proto_filters.created_at:
        created_at = [
            [date_filter_from_proto(df) for df in group.filters]
            for group in proto_filters.created_at
        ]

    expired_at = None
    if proto_filters.expired_at:
        expired_at = [
            [date_filter_from_proto(df) for df in group.filters]
            for group in proto_filters.expired_at
        ]

    property_filters = None
    if proto_filters.property_filters:
        property_filters = [property_filter_from_proto(pf) for pf in proto_filters.property_filters]

    return SearchFilters(
        node_labels=list(proto_filters.node_labels) if proto_filters.node_labels else None,
        edge_types=list(proto_filters.edge_types) if proto_filters.edge_types else None,
        valid_at=valid_at,
        invalid_at=invalid_at,
        created_at=created_at,
        expired_at=expired_at,
        edge_uuids=list(proto_filters.edge_uuids) if proto_filters.edge_uuids else None,
        property_filters=property_filters,
    )


def search_results_to_proto(results: SearchResults) -> search_pb2.SearchResults:
    """Convert Graphiti SearchResults to proto message."""
    proto_results = search_pb2.SearchResults(
        edges=[entity_edge_to_proto(e) for e in results.edges],
        edge_reranker_scores=results.edge_reranker_scores,
        nodes=[entity_node_to_proto(n) for n in results.nodes],
        node_reranker_scores=results.node_reranker_scores,
        episodes=[episodic_node_to_proto(e) for e in results.episodes],
        episode_reranker_scores=results.episode_reranker_scores,
        communities=[community_node_to_proto(c) for c in results.communities],
        community_reranker_scores=results.community_reranker_scores,
    )

    return proto_results
