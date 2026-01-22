"""Tests for search converter functions."""

from datetime import datetime, timezone


class TestSearchConfigConverters:
    """Tests for SearchConfig conversion functions."""

    def test_search_config_from_proto_none(self):
        """Test search config from proto with None."""
        from src.converters.search_converters import search_config_from_proto

        config = search_config_from_proto(None)

        assert config is not None
        assert config.limit == 10

    def test_search_config_from_proto_full(self):
        """Test full SearchConfig from proto conversion."""
        from src.converters.search_converters import search_config_from_proto
        from src.generated.graphiti.v1 import search_pb2

        edge_config = search_pb2.EdgeSearchConfig(
            search_methods=[search_pb2.EDGE_SEARCH_METHOD_COSINE_SIMILARITY],
        )
        node_config = search_pb2.NodeSearchConfig(
            search_methods=[search_pb2.NODE_SEARCH_METHOD_BM25],
        )

        proto_config = search_pb2.SearchConfig(
            edge_config=edge_config,
            node_config=node_config,
            limit=20,
            reranker_min_score=0.3,
        )

        config = search_config_from_proto(proto_config)

        assert config is not None
        assert config.limit == 20
        assert config.reranker_min_score == 0.3
        assert config.edge_config is not None
        assert config.node_config is not None


class TestEntitySearchConfigConverters:
    """Tests for entity-specific search config conversions."""

    def test_edge_search_config_from_proto(self):
        """Test EdgeSearchConfig from proto conversion."""
        from src.converters.search_converters import edge_search_config_from_proto
        from src.generated.graphiti.v1 import search_pb2

        proto_config = search_pb2.EdgeSearchConfig(
            search_methods=[search_pb2.EDGE_SEARCH_METHOD_COSINE_SIMILARITY],
            reranker=search_pb2.EDGE_RERANKER_RRF,
            sim_min_score=0.5,
            mmr_lambda=0.7,
            bfs_max_depth=4,
        )

        config = edge_search_config_from_proto(proto_config)

        assert config is not None
        assert len(config.search_methods) == 1
        assert config.sim_min_score == 0.5
        assert config.mmr_lambda == 0.7
        assert config.bfs_max_depth == 4

    def test_node_search_config_from_proto(self):
        """Test NodeSearchConfig from proto conversion."""
        from src.converters.search_converters import node_search_config_from_proto
        from src.generated.graphiti.v1 import search_pb2

        proto_config = search_pb2.NodeSearchConfig(
            search_methods=[search_pb2.NODE_SEARCH_METHOD_BM25],
            reranker=search_pb2.NODE_RERANKER_CROSS_ENCODER,
        )

        config = node_search_config_from_proto(proto_config)

        assert config is not None
        assert len(config.search_methods) == 1

    def test_episode_search_config_from_proto(self):
        """Test EpisodeSearchConfig from proto conversion."""
        from src.converters.search_converters import episode_search_config_from_proto
        from src.generated.graphiti.v1 import search_pb2

        proto_config = search_pb2.EpisodeSearchConfig(
            search_methods=[search_pb2.EPISODE_SEARCH_METHOD_BM25],
            reranker=search_pb2.EPISODE_RERANKER_RRF,
        )

        config = episode_search_config_from_proto(proto_config)

        assert config is not None
        assert len(config.search_methods) == 1

    def test_community_search_config_from_proto(self):
        """Test CommunitySearchConfig from proto conversion."""
        from src.converters.search_converters import community_search_config_from_proto
        from src.generated.graphiti.v1 import search_pb2

        proto_config = search_pb2.CommunitySearchConfig(
            search_methods=[search_pb2.COMMUNITY_SEARCH_METHOD_COSINE_SIMILARITY],
            reranker=search_pb2.COMMUNITY_RERANKER_MMR,
        )

        config = community_search_config_from_proto(proto_config)

        assert config is not None
        assert len(config.search_methods) == 1


class TestSearchFiltersConverters:
    """Tests for SearchFilters conversion functions."""

    def test_search_filters_from_proto_none(self):
        """Test search filters from proto with None."""
        from src.converters.search_converters import search_filters_from_proto

        filters = search_filters_from_proto(None)

        assert filters is not None
        assert filters.node_labels is None
        assert filters.edge_types is None

    def test_search_filters_from_proto_with_labels_and_types(self):
        """Test search filters from proto with labels and types."""
        from src.converters.search_converters import search_filters_from_proto
        from src.generated.graphiti.v1 import search_pb2

        proto_filters = search_pb2.SearchFilters(
            node_labels=['Person', 'Organization'],
            edge_types=['KNOWS', 'WORKS_AT'],
        )

        filters = search_filters_from_proto(proto_filters)

        assert filters is not None
        assert filters.node_labels == ['Person', 'Organization']
        assert filters.edge_types == ['KNOWS', 'WORKS_AT']

    def test_search_filters_with_property_filters(self):
        """Test search filters from proto with property filters."""
        from src.converters.search_converters import search_filters_from_proto
        from src.generated.graphiti.v1 import common_pb2, search_pb2

        property_filter = common_pb2.PropertyFilter(
            property_name='status',
            string_value='active',
            comparison_operator=common_pb2.COMPARISON_OPERATOR_EQUALS,
        )

        proto_filters = search_pb2.SearchFilters(
            property_filters=[property_filter],
        )

        filters = search_filters_from_proto(proto_filters)

        assert filters is not None
        assert len(filters.property_filters) == 1
        assert filters.property_filters[0].property_name == 'status'


class TestFilterConverters:
    """Tests for filter conversion functions."""

    def test_date_filter_from_proto(self):
        """Test DateFilter from proto conversion."""
        from google.protobuf.timestamp_pb2 import Timestamp

        from src.converters.search_converters import date_filter_from_proto
        from src.generated.graphiti.v1 import common_pb2

        ts = Timestamp()
        ts.FromDatetime(datetime(2024, 1, 15, tzinfo=timezone.utc))

        proto_filter = common_pb2.DateFilter(
            date=ts,
            comparison_operator=common_pb2.COMPARISON_OPERATOR_GREATER_THAN,
        )

        filter = date_filter_from_proto(proto_filter)

        assert filter is not None
        assert filter.date.year == 2024

    def test_property_filter_from_proto_string(self):
        """Test PropertyFilter from proto with string value."""
        from src.converters.search_converters import property_filter_from_proto
        from src.generated.graphiti.v1 import common_pb2

        proto_filter = common_pb2.PropertyFilter(
            property_name='status',
            string_value='active',
            comparison_operator=common_pb2.COMPARISON_OPERATOR_EQUALS,
        )

        filter = property_filter_from_proto(proto_filter)

        assert filter is not None
        assert filter.property_name == 'status'
        assert filter.property_value == 'active'

    def test_property_filter_from_proto_int(self):
        """Test PropertyFilter from proto with int value."""
        from src.converters.search_converters import property_filter_from_proto
        from src.generated.graphiti.v1 import common_pb2

        proto_filter = common_pb2.PropertyFilter(
            property_name='count',
            int_value=42,
            comparison_operator=common_pb2.COMPARISON_OPERATOR_GREATER_THAN,
        )

        filter = property_filter_from_proto(proto_filter)

        assert filter is not None
        assert filter.property_value == 42

    def test_property_filter_from_proto_float(self):
        """Test PropertyFilter from proto with float value."""
        from src.converters.search_converters import property_filter_from_proto
        from src.generated.graphiti.v1 import common_pb2

        proto_filter = common_pb2.PropertyFilter(
            property_name='score',
            float_value=0.85,
            comparison_operator=common_pb2.COMPARISON_OPERATOR_LESS_THAN,
        )

        filter = property_filter_from_proto(proto_filter)

        assert filter is not None
        assert filter.property_value == 0.85


class TestSearchResultsConverters:
    """Tests for SearchResults conversion functions."""

    def test_search_results_to_proto(
        self, sample_entity_edge, sample_entity_node, sample_episodic_node, sample_community_node
    ):
        """Test SearchResults to proto conversion."""
        from graphiti_core.search.search_config import SearchResults

        from src.converters.search_converters import search_results_to_proto

        results = SearchResults(
            edges=[sample_entity_edge],
            edge_reranker_scores=[0.9],
            nodes=[sample_entity_node],
            node_reranker_scores=[0.8],
            episodes=[sample_episodic_node],
            episode_reranker_scores=[0.7],
            communities=[sample_community_node],
            community_reranker_scores=[0.6],
        )

        proto = search_results_to_proto(results)

        assert len(proto.edges) == 1
        assert len(proto.nodes) == 1
        assert len(proto.episodes) == 1
        assert len(proto.communities) == 1
        assert proto.edge_reranker_scores[0] == 0.9


class TestMappings:
    """Tests for enum/method mappings."""

    def test_comparison_operator_mappings(self):
        """Test comparison operator mappings."""
        from graphiti_core.search.search_filters import ComparisonOperator

        from src.converters.search_converters import COMPARISON_OPERATOR_FROM_PROTO
        from src.generated.graphiti.v1 import common_pb2

        assert (
            COMPARISON_OPERATOR_FROM_PROTO[common_pb2.COMPARISON_OPERATOR_EQUALS]
            == ComparisonOperator.equals
        )
        assert (
            COMPARISON_OPERATOR_FROM_PROTO[common_pb2.COMPARISON_OPERATOR_NOT_EQUALS]
            == ComparisonOperator.not_equals
        )
        assert (
            COMPARISON_OPERATOR_FROM_PROTO[common_pb2.COMPARISON_OPERATOR_GREATER_THAN]
            == ComparisonOperator.greater_than
        )
        assert (
            COMPARISON_OPERATOR_FROM_PROTO[common_pb2.COMPARISON_OPERATOR_LESS_THAN]
            == ComparisonOperator.less_than
        )

    def test_edge_search_method_mappings(self):
        """Test edge search method mappings."""
        from graphiti_core.search.search_config import EdgeSearchMethod

        from src.converters.search_converters import EDGE_SEARCH_METHOD_FROM_PROTO
        from src.generated.graphiti.v1 import search_pb2

        assert (
            EDGE_SEARCH_METHOD_FROM_PROTO[search_pb2.EDGE_SEARCH_METHOD_COSINE_SIMILARITY]
            == EdgeSearchMethod.cosine_similarity
        )
        assert (
            EDGE_SEARCH_METHOD_FROM_PROTO[search_pb2.EDGE_SEARCH_METHOD_BM25]
            == EdgeSearchMethod.bm25
        )

    def test_node_search_method_mappings(self):
        """Test node search method mappings."""
        from graphiti_core.search.search_config import NodeSearchMethod

        from src.converters.search_converters import NODE_SEARCH_METHOD_FROM_PROTO
        from src.generated.graphiti.v1 import search_pb2

        assert (
            NODE_SEARCH_METHOD_FROM_PROTO[search_pb2.NODE_SEARCH_METHOD_COSINE_SIMILARITY]
            == NodeSearchMethod.cosine_similarity
        )
        assert (
            NODE_SEARCH_METHOD_FROM_PROTO[search_pb2.NODE_SEARCH_METHOD_BM25]
            == NodeSearchMethod.bm25
        )

    def test_episode_search_method_mappings(self):
        """Test episode search method mappings."""
        from graphiti_core.search.search_config import EpisodeSearchMethod

        from src.converters.search_converters import EPISODE_SEARCH_METHOD_FROM_PROTO
        from src.generated.graphiti.v1 import search_pb2

        assert (
            EPISODE_SEARCH_METHOD_FROM_PROTO[search_pb2.EPISODE_SEARCH_METHOD_BM25]
            == EpisodeSearchMethod.bm25
        )

    def test_community_search_method_mappings(self):
        """Test community search method mappings."""
        from graphiti_core.search.search_config import CommunitySearchMethod

        from src.converters.search_converters import COMMUNITY_SEARCH_METHOD_FROM_PROTO
        from src.generated.graphiti.v1 import search_pb2

        assert (
            COMMUNITY_SEARCH_METHOD_FROM_PROTO[search_pb2.COMMUNITY_SEARCH_METHOD_COSINE_SIMILARITY]
            == CommunitySearchMethod.cosine_similarity
        )
        assert (
            COMMUNITY_SEARCH_METHOD_FROM_PROTO[search_pb2.COMMUNITY_SEARCH_METHOD_BM25]
            == CommunitySearchMethod.bm25
        )
