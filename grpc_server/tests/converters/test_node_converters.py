"""Tests for node converter functions."""

from datetime import datetime, timezone

from graphiti_core.nodes import EpisodeType


class TestDateTimeConversions:
    """Tests for datetime conversion functions."""

    def test_datetime_to_timestamp(self):
        """Test datetime to timestamp conversion."""
        from src.converters.node_converters import datetime_to_timestamp

        dt = datetime(2024, 1, 15, 12, 30, 0, tzinfo=timezone.utc)
        ts = datetime_to_timestamp(dt)

        assert ts is not None
        assert ts.ToDatetime(tzinfo=timezone.utc) == dt

    def test_datetime_to_timestamp_none(self):
        """Test datetime to timestamp with None."""
        from src.converters.node_converters import datetime_to_timestamp

        ts = datetime_to_timestamp(None)
        assert ts is None

    def test_timestamp_to_datetime(self):
        """Test timestamp to datetime conversion."""
        from google.protobuf.timestamp_pb2 import Timestamp

        from src.converters.node_converters import timestamp_to_datetime

        ts = Timestamp()
        ts.FromDatetime(datetime(2024, 1, 15, 12, 30, 0, tzinfo=timezone.utc))

        dt = timestamp_to_datetime(ts)
        assert dt is not None
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 15

    def test_timestamp_to_datetime_empty(self):
        """Test timestamp to datetime with empty timestamp."""
        from google.protobuf.timestamp_pb2 import Timestamp

        from src.converters.node_converters import timestamp_to_datetime

        ts = Timestamp()  # Empty timestamp (seconds=0, nanos=0)
        dt = timestamp_to_datetime(ts)

        assert dt is None


class TestEpisodeTypeConversions:
    """Tests for EpisodeType conversion functions."""

    def test_episode_type_to_proto(self):
        """Test EpisodeType to proto enum conversion."""
        from src.converters.node_converters import episode_type_to_proto
        from src.generated.graphiti.v1 import common_pb2

        assert episode_type_to_proto(EpisodeType.message) == common_pb2.EPISODE_TYPE_MESSAGE
        assert episode_type_to_proto(EpisodeType.json) == common_pb2.EPISODE_TYPE_JSON
        assert episode_type_to_proto(EpisodeType.text) == common_pb2.EPISODE_TYPE_TEXT

    def test_episode_type_from_proto(self):
        """Test proto enum to EpisodeType conversion."""
        from src.converters.node_converters import episode_type_from_proto
        from src.generated.graphiti.v1 import common_pb2

        assert episode_type_from_proto(common_pb2.EPISODE_TYPE_MESSAGE) == EpisodeType.message
        assert episode_type_from_proto(common_pb2.EPISODE_TYPE_JSON) == EpisodeType.json
        assert episode_type_from_proto(common_pb2.EPISODE_TYPE_TEXT) == EpisodeType.text


class TestEntityNodeConverters:
    """Tests for EntityNode conversion functions."""

    def test_entity_node_to_proto(self, sample_entity_node):
        """Test EntityNode to proto conversion."""
        from src.converters.node_converters import entity_node_to_proto

        proto = entity_node_to_proto(sample_entity_node)

        assert proto.uuid == sample_entity_node.uuid
        assert proto.name == sample_entity_node.name
        assert proto.group_id == sample_entity_node.group_id
        assert proto.summary == sample_entity_node.summary
        assert list(proto.labels) == sample_entity_node.labels

    def test_entity_node_from_proto(self, sample_entity_node):
        """Test proto to EntityNode conversion (roundtrip)."""
        from src.converters.node_converters import entity_node_from_proto, entity_node_to_proto

        proto = entity_node_to_proto(sample_entity_node)
        node = entity_node_from_proto(proto)

        assert node.uuid == sample_entity_node.uuid
        assert node.name == sample_entity_node.name
        assert node.group_id == sample_entity_node.group_id
        assert node.summary == sample_entity_node.summary


class TestEpisodicNodeConverters:
    """Tests for EpisodicNode conversion functions."""

    def test_episodic_node_to_proto(self, sample_episodic_node):
        """Test EpisodicNode to proto conversion."""
        from src.converters.node_converters import episodic_node_to_proto

        proto = episodic_node_to_proto(sample_episodic_node)

        assert proto.uuid == sample_episodic_node.uuid
        assert proto.name == sample_episodic_node.name
        assert proto.content == sample_episodic_node.content
        assert proto.source_description == sample_episodic_node.source_description


class TestCommunityNodeConverters:
    """Tests for CommunityNode conversion functions."""

    def test_community_node_to_proto(self, sample_community_node):
        """Test CommunityNode to proto conversion."""
        from src.converters.node_converters import community_node_to_proto

        proto = community_node_to_proto(sample_community_node)

        assert proto.uuid == sample_community_node.uuid
        assert proto.name == sample_community_node.name
        assert proto.summary == sample_community_node.summary


class TestSagaNodeConverters:
    """Tests for SagaNode conversion functions."""

    def test_saga_node_to_proto(self):
        """Test SagaNode to proto conversion."""
        from graphiti_core.nodes import SagaNode

        from src.converters.node_converters import saga_node_to_proto

        saga_node = SagaNode(
            uuid='saga-uuid',
            name='Test Saga',
            group_id='test-group',
            labels=['Saga'],
            created_at=datetime.now(timezone.utc),
        )

        proto = saga_node_to_proto(saga_node)

        assert proto.uuid == saga_node.uuid
        assert proto.name == saga_node.name


class TestStructConversions:
    """Tests for dict/Struct conversion functions."""

    def test_dict_to_struct(self):
        """Test dict to protobuf Struct conversion."""
        from src.converters.node_converters import dict_to_struct

        d = {'key1': 'value1', 'key2': 123, 'key3': True}
        struct = dict_to_struct(d)

        assert struct.fields['key1'].string_value == 'value1'
        assert struct.fields['key2'].number_value == 123
        assert struct.fields['key3'].bool_value is True

    def test_dict_to_struct_none(self):
        """Test dict to struct with None."""
        from src.converters.node_converters import dict_to_struct

        struct = dict_to_struct(None)
        assert len(struct.fields) == 0

    def test_struct_to_dict(self):
        """Test protobuf Struct to dict conversion."""
        from src.converters.node_converters import dict_to_struct, struct_to_dict

        original = {'key1': 'value1', 'key2': 123.0}
        struct = dict_to_struct(original)
        result = struct_to_dict(struct)

        assert result['key1'] == 'value1'
        assert result['key2'] == 123.0
