"""Tests for edge converter functions."""

from datetime import datetime, timezone


class TestEntityEdgeConverters:
    """Tests for EntityEdge conversion functions."""

    def test_entity_edge_to_proto(self, sample_entity_edge):
        """Test EntityEdge to proto conversion."""
        from src.converters.edge_converters import entity_edge_to_proto

        proto = entity_edge_to_proto(sample_entity_edge)

        assert proto.uuid == sample_entity_edge.uuid
        assert proto.group_id == sample_entity_edge.group_id
        assert proto.name == sample_entity_edge.name
        assert proto.fact == sample_entity_edge.fact
        assert proto.source_node_uuid == sample_entity_edge.source_node_uuid
        assert proto.target_node_uuid == sample_entity_edge.target_node_uuid

    def test_entity_edge_from_proto(self, sample_entity_edge):
        """Test proto to EntityEdge conversion (roundtrip)."""
        from src.converters.edge_converters import entity_edge_from_proto, entity_edge_to_proto

        proto = entity_edge_to_proto(sample_entity_edge)
        edge = entity_edge_from_proto(proto)

        assert edge.uuid == sample_entity_edge.uuid
        assert edge.name == sample_entity_edge.name
        assert edge.fact == sample_entity_edge.fact

    def test_entity_edge_to_proto_with_expired_at(self):
        """Test EntityEdge to proto conversion with expired_at set."""
        from graphiti_core.edges import EntityEdge

        from src.converters.edge_converters import entity_edge_to_proto

        now = datetime.now(timezone.utc)
        edge = EntityEdge(
            uuid='test-edge-uuid',
            group_id='test-group',
            source_node_uuid='source-uuid',
            target_node_uuid='target-uuid',
            created_at=now,
            name='RELATES_TO',
            fact='Test fact',
            episodes=['episode-1'],
            valid_at=now,
            expired_at=now,
        )

        proto = entity_edge_to_proto(edge)

        assert proto.uuid == edge.uuid
        assert proto.HasField('expired_at')
        assert proto.expired_at.seconds > 0

    def test_entity_edge_to_proto_with_invalid_at(self):
        """Test EntityEdge to proto conversion with invalid_at set."""
        from graphiti_core.edges import EntityEdge

        from src.converters.edge_converters import entity_edge_to_proto

        now = datetime.now(timezone.utc)
        edge = EntityEdge(
            uuid='test-edge-uuid',
            group_id='test-group',
            source_node_uuid='source-uuid',
            target_node_uuid='target-uuid',
            created_at=now,
            name='RELATES_TO',
            fact='Test fact',
            episodes=['episode-1'],
            valid_at=now,
            invalid_at=now,
        )

        proto = entity_edge_to_proto(edge)

        assert proto.uuid == edge.uuid
        assert proto.HasField('invalid_at')
        assert proto.invalid_at.seconds > 0

    def test_entity_edge_to_proto_with_attributes(self):
        """Test EntityEdge to proto conversion with attributes dict."""
        from graphiti_core.edges import EntityEdge

        from src.converters.edge_converters import entity_edge_to_proto

        now = datetime.now(timezone.utc)
        test_attributes = {'key1': 'value1', 'key2': 42, 'key3': True}
        edge = EntityEdge(
            uuid='test-edge-uuid',
            group_id='test-group',
            source_node_uuid='source-uuid',
            target_node_uuid='target-uuid',
            created_at=now,
            name='RELATES_TO',
            fact='Test fact',
            episodes=['episode-1'],
            valid_at=now,
            attributes=test_attributes,
        )

        proto = entity_edge_to_proto(edge)

        assert proto.uuid == edge.uuid
        assert proto.HasField('attributes')
        assert proto.attributes.fields['key1'].string_value == 'value1'
        assert proto.attributes.fields['key2'].number_value == 42
        assert proto.attributes.fields['key3'].bool_value is True

    def test_entity_edge_to_proto_with_all_optional_fields(self):
        """Test EntityEdge to proto conversion with all optional fields set."""
        from graphiti_core.edges import EntityEdge

        from src.converters.edge_converters import entity_edge_to_proto

        now = datetime.now(timezone.utc)
        test_attributes = {'status': 'active', 'priority': 1}
        edge = EntityEdge(
            uuid='test-edge-uuid',
            group_id='test-group',
            source_node_uuid='source-uuid',
            target_node_uuid='target-uuid',
            created_at=now,
            name='RELATES_TO',
            fact='Test fact with all fields',
            episodes=['episode-1', 'episode-2'],
            valid_at=now,
            invalid_at=now,
            expired_at=now,
            attributes=test_attributes,
        )

        proto = entity_edge_to_proto(edge)

        assert proto.uuid == edge.uuid
        assert proto.group_id == edge.group_id
        assert proto.name == edge.name
        assert proto.fact == edge.fact
        assert len(proto.episodes) == 2
        assert proto.HasField('created_at')
        assert proto.HasField('valid_at')
        assert proto.HasField('invalid_at')
        assert proto.HasField('expired_at')
        assert proto.HasField('attributes')
        assert proto.attributes.fields['status'].string_value == 'active'
        assert proto.attributes.fields['priority'].number_value == 1


class TestEpisodicEdgeConverters:
    """Tests for EpisodicEdge conversion functions."""

    def test_episodic_edge_to_proto(self, sample_episodic_edge):
        """Test EpisodicEdge to proto conversion."""
        from src.converters.edge_converters import episodic_edge_to_proto

        proto = episodic_edge_to_proto(sample_episodic_edge)

        assert proto.uuid == sample_episodic_edge.uuid
        assert proto.group_id == sample_episodic_edge.group_id
        assert proto.source_node_uuid == sample_episodic_edge.source_node_uuid
        assert proto.target_node_uuid == sample_episodic_edge.target_node_uuid


class TestCommunityEdgeConverters:
    """Tests for CommunityEdge conversion functions."""

    def test_community_edge_to_proto(self, sample_community_edge):
        """Test CommunityEdge to proto conversion."""
        from src.converters.edge_converters import community_edge_to_proto

        proto = community_edge_to_proto(sample_community_edge)

        assert proto.uuid == sample_community_edge.uuid
        assert proto.group_id == sample_community_edge.group_id


class TestSpecialEdgeConverters:
    """Tests for special edge type conversions."""

    def test_has_episode_edge_to_proto(self):
        """Test HasEpisodeEdge to proto conversion."""
        from graphiti_core.edges import HasEpisodeEdge

        from src.converters.edge_converters import has_episode_edge_to_proto

        edge = HasEpisodeEdge(
            uuid='has-ep-uuid',
            group_id='test-group',
            source_node_uuid='source-uuid',
            target_node_uuid='target-uuid',
            created_at=datetime.now(timezone.utc),
        )

        proto = has_episode_edge_to_proto(edge)

        assert proto.uuid == edge.uuid
        assert proto.group_id == edge.group_id

    def test_next_episode_edge_to_proto(self):
        """Test NextEpisodeEdge to proto conversion."""
        from graphiti_core.edges import NextEpisodeEdge

        from src.converters.edge_converters import next_episode_edge_to_proto

        edge = NextEpisodeEdge(
            uuid='next-ep-uuid',
            group_id='test-group',
            source_node_uuid='source-uuid',
            target_node_uuid='target-uuid',
            created_at=datetime.now(timezone.utc),
        )

        proto = next_episode_edge_to_proto(edge)

        assert proto.uuid == edge.uuid
        assert proto.group_id == edge.group_id


class TestFactResultConverters:
    """Tests for FactResult conversion functions."""

    def test_fact_result_from_edge(self, sample_entity_edge):
        """Test FactResult creation from EntityEdge."""
        from src.converters.edge_converters import fact_result_from_edge

        proto = fact_result_from_edge(sample_entity_edge)

        assert proto.uuid == sample_entity_edge.uuid
        assert proto.name == sample_entity_edge.name
        assert proto.fact == sample_entity_edge.fact

    def test_fact_result_to_proto(self):
        """Test FactResult creation from fields."""
        from src.converters.edge_converters import fact_result_to_proto

        now = datetime.now(timezone.utc)

        proto = fact_result_to_proto(
            uuid='test-uuid',
            name='RELATES_TO',
            fact='A relates to B',
            created_at=now,
            valid_at=now,
        )

        assert proto.uuid == 'test-uuid'
        assert proto.name == 'RELATES_TO'
        assert proto.fact == 'A relates to B'

    def test_fact_result_from_edge_with_invalid_at(self):
        """Test FactResult from EntityEdge with invalid_at set."""
        from graphiti_core.edges import EntityEdge

        from src.converters.edge_converters import fact_result_from_edge

        now = datetime.now(timezone.utc)
        edge = EntityEdge(
            uuid='test-edge-uuid',
            group_id='test-group',
            source_node_uuid='source-uuid',
            target_node_uuid='target-uuid',
            created_at=now,
            name='RELATES_TO',
            fact='Test fact',
            episodes=['episode-1'],
            valid_at=now,
            invalid_at=now,
        )

        proto = fact_result_from_edge(edge)

        assert proto.uuid == edge.uuid
        assert proto.name == edge.name
        assert proto.fact == edge.fact
        assert proto.HasField('invalid_at')
        assert proto.invalid_at.seconds > 0

    def test_fact_result_from_edge_with_expired_at(self):
        """Test FactResult from EntityEdge with expired_at set."""
        from graphiti_core.edges import EntityEdge

        from src.converters.edge_converters import fact_result_from_edge

        now = datetime.now(timezone.utc)
        edge = EntityEdge(
            uuid='test-edge-uuid',
            group_id='test-group',
            source_node_uuid='source-uuid',
            target_node_uuid='target-uuid',
            created_at=now,
            name='RELATES_TO',
            fact='Test fact',
            episodes=['episode-1'],
            valid_at=now,
            expired_at=now,
        )

        proto = fact_result_from_edge(edge)

        assert proto.uuid == edge.uuid
        assert proto.name == edge.name
        assert proto.fact == edge.fact
        assert proto.HasField('expired_at')
        assert proto.expired_at.seconds > 0

    def test_fact_result_to_proto_with_invalid_at(self):
        """Test FactResult creation with invalid_at field."""
        from src.converters.edge_converters import fact_result_to_proto

        now = datetime.now(timezone.utc)

        proto = fact_result_to_proto(
            uuid='test-uuid',
            name='RELATES_TO',
            fact='A relates to B',
            created_at=now,
            valid_at=now,
            invalid_at=now,
        )

        assert proto.uuid == 'test-uuid'
        assert proto.name == 'RELATES_TO'
        assert proto.fact == 'A relates to B'
        assert proto.HasField('invalid_at')
        assert proto.invalid_at.seconds > 0

    def test_fact_result_to_proto_with_expired_at(self):
        """Test FactResult creation with expired_at field."""
        from src.converters.edge_converters import fact_result_to_proto

        now = datetime.now(timezone.utc)

        proto = fact_result_to_proto(
            uuid='test-uuid',
            name='RELATES_TO',
            fact='A relates to B',
            created_at=now,
            valid_at=now,
            expired_at=now,
        )

        assert proto.uuid == 'test-uuid'
        assert proto.name == 'RELATES_TO'
        assert proto.fact == 'A relates to B'
        assert proto.HasField('expired_at')
        assert proto.expired_at.seconds > 0

    def test_fact_result_to_proto_with_all_date_fields(self):
        """Test FactResult creation with all optional date fields."""
        from src.converters.edge_converters import fact_result_to_proto

        now = datetime.now(timezone.utc)

        proto = fact_result_to_proto(
            uuid='test-uuid',
            name='RELATES_TO',
            fact='A relates to B',
            created_at=now,
            valid_at=now,
            invalid_at=now,
            expired_at=now,
        )

        assert proto.uuid == 'test-uuid'
        assert proto.name == 'RELATES_TO'
        assert proto.fact == 'A relates to B'
        assert proto.HasField('created_at')
        assert proto.HasField('valid_at')
        assert proto.HasField('invalid_at')
        assert proto.HasField('expired_at')
