"""Tests for IngestService."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest


class TestAddEpisode:
    """Tests for AddEpisode RPC."""

    @pytest.mark.asyncio
    async def test_add_episode(
        self, mock_graphiti, sample_episodic_node, sample_entity_node, sample_entity_edge
    ):
        """Test AddEpisode RPC."""
        from google.protobuf.timestamp_pb2 import Timestamp

        from src.generated.graphiti.v1 import common_pb2, ingest_service_pb2
        from src.services.ingest_service import IngestServiceServicer

        class MockResult:
            episode = sample_episodic_node
            nodes = [sample_entity_node]
            edges = [sample_entity_edge]

        mock_graphiti.add_episode.return_value = MockResult()

        servicer = IngestServiceServicer(mock_graphiti)

        ts = Timestamp()
        ts.FromDatetime(datetime.now(timezone.utc))

        request = ingest_service_pb2.AddEpisodeRequest(
            group_id='test-group',
            name='Test Episode',
            episode_body='Test content',
            source=common_pb2.EPISODE_TYPE_MESSAGE,
            source_description='Test source',
        )
        request.reference_time.CopyFrom(ts)

        context = MagicMock()
        response = await servicer.AddEpisode(request, context)

        mock_graphiti.add_episode.assert_called_once()
        assert response.episode.uuid == sample_episodic_node.uuid
        assert len(response.nodes) == 1
        assert len(response.edges) == 1

    @pytest.mark.asyncio
    async def test_add_episode_with_auto_generated_uuid(
        self, mock_graphiti, sample_episodic_node, sample_entity_node, sample_entity_edge
    ):
        """Test AddEpisode RPC with auto-generated UUID."""
        from google.protobuf.timestamp_pb2 import Timestamp

        from src.generated.graphiti.v1 import common_pb2, ingest_service_pb2
        from src.services.ingest_service import IngestServiceServicer

        class MockResult:
            episode = sample_episodic_node
            nodes = [sample_entity_node]
            edges = [sample_entity_edge]

        mock_graphiti.add_episode.return_value = MockResult()

        servicer = IngestServiceServicer(mock_graphiti)

        ts = Timestamp()
        ts.FromDatetime(datetime.now(timezone.utc))

        request = ingest_service_pb2.AddEpisodeRequest(
            group_id='test-group',
            name='Test Episode',
            episode_body='Test content',
            source=common_pb2.EPISODE_TYPE_MESSAGE,
            source_description='Test source',
            # No uuid - should auto-generate
        )
        request.reference_time.CopyFrom(ts)

        context = MagicMock()
        await servicer.AddEpisode(request, context)

        mock_graphiti.add_episode.assert_called_once()
        call_args = mock_graphiti.add_episode.call_args
        assert call_args.kwargs['uuid'] is not None

    @pytest.mark.asyncio
    async def test_add_episode_with_no_reference_time(
        self, mock_graphiti, sample_episodic_node, sample_entity_node, sample_entity_edge
    ):
        """Test AddEpisode RPC without reference_time uses current time."""
        from src.generated.graphiti.v1 import common_pb2, ingest_service_pb2
        from src.services.ingest_service import IngestServiceServicer

        class MockResult:
            episode = sample_episodic_node
            nodes = [sample_entity_node]
            edges = [sample_entity_edge]

        mock_graphiti.add_episode.return_value = MockResult()

        servicer = IngestServiceServicer(mock_graphiti)

        request = ingest_service_pb2.AddEpisodeRequest(
            group_id='test-group',
            name='Test Episode',
            episode_body='Test content',
            source=common_pb2.EPISODE_TYPE_MESSAGE,
            source_description='Test source',
            # No reference_time - should use current time
        )

        context = MagicMock()
        await servicer.AddEpisode(request, context)

        mock_graphiti.add_episode.assert_called_once()
        call_args = mock_graphiti.add_episode.call_args
        assert call_args.kwargs['reference_time'] is not None

    @pytest.mark.asyncio
    async def test_add_episode_with_saga_and_options(
        self, mock_graphiti, sample_episodic_node, sample_entity_node, sample_entity_edge
    ):
        """Test AddEpisode RPC with saga and additional options."""
        from google.protobuf.timestamp_pb2 import Timestamp

        from src.generated.graphiti.v1 import common_pb2, ingest_service_pb2
        from src.services.ingest_service import IngestServiceServicer

        class MockResult:
            episode = sample_episodic_node
            nodes = [sample_entity_node]
            edges = [sample_entity_edge]

        mock_graphiti.add_episode.return_value = MockResult()

        servicer = IngestServiceServicer(mock_graphiti)

        ts = Timestamp()
        ts.FromDatetime(datetime.now(timezone.utc))

        request = ingest_service_pb2.AddEpisodeRequest(
            group_id='test-group',
            name='Test Episode',
            episode_body='Test content',
            source=common_pb2.EPISODE_TYPE_MESSAGE,
            source_description='Test source',
            saga='test-saga',
            update_communities=True,
            saga_previous_episode_uuid='prev-uuid',
            previous_episode_uuids=['prev-1', 'prev-2'],
            custom_extraction_instructions='Extract entities carefully',
        )
        request.reference_time.CopyFrom(ts)

        context = MagicMock()
        await servicer.AddEpisode(request, context)

        mock_graphiti.add_episode.assert_called_once()
        call_args = mock_graphiti.add_episode.call_args
        assert call_args.kwargs['saga'] == 'test-saga'
        assert call_args.kwargs['update_communities'] is True
        assert call_args.kwargs['saga_previous_episode_uuid'] == 'prev-uuid'
        assert call_args.kwargs['previous_episode_uuids'] == ['prev-1', 'prev-2']
        assert call_args.kwargs['custom_extraction_instructions'] == 'Extract entities carefully'

    @pytest.mark.asyncio
    async def test_add_episode_error(
        self, mock_graphiti, sample_episodic_node, sample_entity_node, sample_entity_edge
    ):
        """Test AddEpisode RPC error handling."""
        from google.protobuf.timestamp_pb2 import Timestamp

        from src.generated.graphiti.v1 import common_pb2, ingest_service_pb2
        from src.services.ingest_service import IngestServiceServicer

        mock_graphiti.add_episode = AsyncMock(side_effect=ValueError('Test error'))

        servicer = IngestServiceServicer(mock_graphiti)

        ts = Timestamp()
        ts.FromDatetime(datetime.now(timezone.utc))

        request = ingest_service_pb2.AddEpisodeRequest(
            group_id='test-group',
            name='Test Episode',
            episode_body='Test content',
            source=common_pb2.EPISODE_TYPE_MESSAGE,
            source_description='Test source',
        )
        request.reference_time.CopyFrom(ts)

        context = MagicMock()
        context.abort = AsyncMock()

        await servicer.AddEpisode(request, context)

        context.abort.assert_called_once()


class TestAddEpisodeBulk:
    """Tests for AddEpisodeBulk RPC."""

    @pytest.mark.asyncio
    async def test_add_episode_bulk(
        self, mock_graphiti, sample_episodic_node, sample_entity_node, sample_entity_edge
    ):
        """Test AddEpisodeBulk RPC streaming."""
        from google.protobuf.timestamp_pb2 import Timestamp

        from src.generated.graphiti.v1 import common_pb2, ingest_service_pb2
        from src.services.ingest_service import IngestServiceServicer

        class MockResult:
            episode = sample_episodic_node
            nodes = [sample_entity_node]
            edges = [sample_entity_edge]

        mock_graphiti.add_episode.return_value = MockResult()

        servicer = IngestServiceServicer(mock_graphiti)

        ts = Timestamp()
        ts.FromDatetime(datetime.now(timezone.utc))

        episode1 = ingest_service_pb2.AddEpisodeRequest(
            group_id='test-group',
            name='Episode 1',
            episode_body='Content 1',
            source=common_pb2.EPISODE_TYPE_MESSAGE,
            source_description='Test',
        )
        episode1.reference_time.CopyFrom(ts)

        episode2 = ingest_service_pb2.AddEpisodeRequest(
            group_id='test-group',
            name='Episode 2',
            episode_body='Content 2',
            source=common_pb2.EPISODE_TYPE_MESSAGE,
            source_description='Test',
        )
        episode2.reference_time.CopyFrom(ts)

        request = ingest_service_pb2.AddEpisodeBulkRequest(episodes=[episode1, episode2])

        context = MagicMock()

        responses = []
        async for response in servicer.AddEpisodeBulk(request, context):
            responses.append(response)

        assert len(responses) >= 1
        assert responses[-1].is_complete is True
        assert responses[-1].completed == 2

    @pytest.mark.asyncio
    async def test_add_episode_bulk_with_error(
        self, mock_graphiti, sample_episodic_node, sample_entity_node, sample_entity_edge
    ):
        """Test AddEpisodeBulk RPC with one episode failing."""
        from google.protobuf.timestamp_pb2 import Timestamp

        from src.generated.graphiti.v1 import common_pb2, ingest_service_pb2
        from src.services.ingest_service import IngestServiceServicer

        class MockResult:
            episode = sample_episodic_node
            nodes = [sample_entity_node]
            edges = [sample_entity_edge]

        # First call succeeds, second fails
        mock_graphiti.add_episode = AsyncMock(
            side_effect=[MockResult(), ValueError('Episode 2 failed')]
        )

        servicer = IngestServiceServicer(mock_graphiti)

        ts = Timestamp()
        ts.FromDatetime(datetime.now(timezone.utc))

        episode1 = ingest_service_pb2.AddEpisodeRequest(
            group_id='test-group',
            name='Episode 1',
            episode_body='Content 1',
            source=common_pb2.EPISODE_TYPE_MESSAGE,
            source_description='Test',
        )
        episode1.reference_time.CopyFrom(ts)

        episode2 = ingest_service_pb2.AddEpisodeRequest(
            group_id='test-group',
            name='Episode 2',
            episode_body='Content 2',
            source=common_pb2.EPISODE_TYPE_MESSAGE,
            source_description='Test',
        )
        episode2.reference_time.CopyFrom(ts)

        request = ingest_service_pb2.AddEpisodeBulkRequest(episodes=[episode1, episode2])

        context = MagicMock()

        responses = []
        async for response in servicer.AddEpisodeBulk(request, context):
            responses.append(response)

        # Should have progress updates and a final complete
        assert responses[-1].is_complete is True
        assert responses[-1].failed == 1
        assert responses[-1].completed == 1


class TestAddMessages:
    """Tests for AddMessages RPC."""

    @pytest.mark.asyncio
    async def test_add_messages(self, mock_graphiti):
        """Test AddMessages RPC."""
        from google.protobuf.timestamp_pb2 import Timestamp

        from src.generated.graphiti.v1 import common_pb2, ingest_service_pb2
        from src.services.ingest_service import IngestServiceServicer

        servicer = IngestServiceServicer(mock_graphiti)

        ts = Timestamp()
        ts.FromDatetime(datetime.now(timezone.utc))

        message = common_pb2.Message(
            uuid='msg-uuid',
            name='User',
            role='user',
            role_type='user',
            content='Hello world',
            source_description='Test',
        )
        message.timestamp.CopyFrom(ts)

        request = ingest_service_pb2.AddMessagesRequest(
            group_id='test-group',
            messages=[message],
        )

        context = MagicMock()
        response = await servicer.AddMessages(request, context)

        assert response.result.success is True
        assert response.queued_count == 1

    @pytest.mark.asyncio
    async def test_add_messages_without_timestamp(self, mock_graphiti):
        """Test AddMessages RPC without timestamp uses current time."""
        from src.generated.graphiti.v1 import common_pb2, ingest_service_pb2
        from src.services.ingest_service import IngestServiceServicer

        servicer = IngestServiceServicer(mock_graphiti)

        message = common_pb2.Message(
            name='User',
            role='user',
            role_type='user',
            content='Hello world',
            source_description='Test',
            # No timestamp
        )

        request = ingest_service_pb2.AddMessagesRequest(
            group_id='test-group',
            messages=[message],
        )

        context = MagicMock()
        response = await servicer.AddMessages(request, context)

        assert response.result.success is True
        assert response.queued_count == 1

    @pytest.mark.asyncio
    async def test_add_messages_error(self, mock_graphiti):
        """Test AddMessages RPC error handling."""
        from src.generated.graphiti.v1 import common_pb2, ingest_service_pb2
        from src.services.ingest_service import IngestServiceServicer

        # Make add_episode raise an error
        mock_graphiti.add_episode = AsyncMock(side_effect=RuntimeError('Processing failed'))

        servicer = IngestServiceServicer(mock_graphiti)

        ts_proto = MagicMock()
        ts_proto.ToDatetime.return_value = None

        # Create request with messages that will be processed
        message = common_pb2.Message(
            uuid='msg-uuid',
            name='User',
            role='user',
            role_type='user',
            content='Hello world',
            source_description='Test',
        )

        request = ingest_service_pb2.AddMessagesRequest(
            group_id='test-group',
            messages=[message],
        )

        context = MagicMock()
        context.abort = AsyncMock()

        # This will queue the message (fire-and-forget) successfully
        response = await servicer.AddMessages(request, context)

        # The queueing should succeed even if the background task fails
        assert response.queued_count == 1


class TestAddEntityNode:
    """Tests for AddEntityNode RPC."""

    @pytest.mark.asyncio
    async def test_add_entity_node(self, mock_graphiti, sample_entity_node):
        """Test AddEntityNode RPC."""
        from src.generated.graphiti.v1 import ingest_service_pb2
        from src.services.ingest_service import IngestServiceServicer

        mock_graphiti.embedder.create = AsyncMock(return_value=[[0.1, 0.2, 0.3]])
        mock_graphiti.driver.graph_operations_interface = MagicMock()
        mock_graphiti.driver.graph_operations_interface.node_save = AsyncMock()

        servicer = IngestServiceServicer(mock_graphiti)

        request = ingest_service_pb2.AddEntityNodeRequest(
            group_id='test-group',
            name='Test Entity',
            summary='Test summary',
        )

        context = MagicMock()
        response = await servicer.AddEntityNode(request, context)

        mock_graphiti.embedder.create.assert_called_once()
        mock_graphiti.driver.graph_operations_interface.node_save.assert_called_once()
        assert response.name == 'Test Entity'
        assert response.group_id == 'test-group'
        assert response.summary == 'Test summary'

    @pytest.mark.asyncio
    async def test_add_entity_node_error(self, mock_graphiti, sample_entity_node):
        """Test AddEntityNode RPC error handling."""
        from src.generated.graphiti.v1 import ingest_service_pb2
        from src.services.ingest_service import IngestServiceServicer

        mock_graphiti.embedder.create = AsyncMock(side_effect=RuntimeError('Embedding failed'))

        servicer = IngestServiceServicer(mock_graphiti)

        request = ingest_service_pb2.AddEntityNodeRequest(
            group_id='test-group',
            name='Test Entity',
            summary='Test summary',
        )

        context = MagicMock()
        context.abort = AsyncMock()

        await servicer.AddEntityNode(request, context)

        context.abort.assert_called_once()


class TestAddTriplet:
    """Tests for AddTriplet RPC."""

    @pytest.mark.asyncio
    async def test_add_triplet(self, mock_graphiti, sample_entity_node, sample_entity_edge):
        """Test AddTriplet RPC."""
        from src.generated.graphiti.v1 import ingest_service_pb2
        from src.services.ingest_service import IngestServiceServicer

        class MockResult:
            nodes = [sample_entity_node, sample_entity_node]
            edges = [sample_entity_edge]

        mock_graphiti.add_triplet = AsyncMock(return_value=MockResult())

        servicer = IngestServiceServicer(mock_graphiti)

        request = ingest_service_pb2.AddTripletRequest(
            group_id='test-group',
            subject_name='Subject',
            predicate='RELATES_TO',
            object_name='Object',
        )

        context = MagicMock()
        response = await servicer.AddTriplet(request, context)

        mock_graphiti.add_triplet.assert_called_once()
        assert response.subject_node.name == sample_entity_node.name
        assert response.edge.uuid == sample_entity_edge.uuid

    @pytest.mark.asyncio
    async def test_add_triplet_with_valid_times(
        self, mock_graphiti, sample_entity_node, sample_entity_edge
    ):
        """Test AddTriplet RPC with valid_at and invalid_at."""
        from google.protobuf.timestamp_pb2 import Timestamp

        from src.generated.graphiti.v1 import ingest_service_pb2
        from src.services.ingest_service import IngestServiceServicer

        class MockResult:
            nodes = [sample_entity_node, sample_entity_node]
            edges = [sample_entity_edge]

        mock_graphiti.add_triplet = AsyncMock(return_value=MockResult())

        servicer = IngestServiceServicer(mock_graphiti)

        valid_at = Timestamp()
        valid_at.FromDatetime(datetime.now(timezone.utc))

        invalid_at = Timestamp()
        invalid_at.FromDatetime(datetime.now(timezone.utc))

        request = ingest_service_pb2.AddTripletRequest(
            group_id='test-group',
            subject_name='Subject',
            predicate='RELATES_TO',
            object_name='Object',
        )
        request.valid_at.CopyFrom(valid_at)
        request.invalid_at.CopyFrom(invalid_at)

        context = MagicMock()
        await servicer.AddTriplet(request, context)

        mock_graphiti.add_triplet.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_triplet_error(self, mock_graphiti, sample_entity_node, sample_entity_edge):
        """Test AddTriplet RPC error handling."""
        from src.generated.graphiti.v1 import ingest_service_pb2
        from src.services.ingest_service import IngestServiceServicer

        mock_graphiti.add_triplet = AsyncMock(side_effect=RuntimeError('Triplet failed'))

        servicer = IngestServiceServicer(mock_graphiti)

        request = ingest_service_pb2.AddTripletRequest(
            group_id='test-group',
            subject_name='Subject',
            predicate='RELATES_TO',
            object_name='Object',
        )

        context = MagicMock()
        context.abort = AsyncMock()

        await servicer.AddTriplet(request, context)

        context.abort.assert_called_once()


class TestStreamEpisodes:
    """Tests for StreamEpisodes RPC."""

    @pytest.mark.asyncio
    async def test_stream_episodes(
        self, mock_graphiti, sample_episodic_node, sample_entity_node, sample_entity_edge
    ):
        """Test StreamEpisodes bidirectional streaming."""
        from google.protobuf.timestamp_pb2 import Timestamp

        from src.generated.graphiti.v1 import common_pb2, ingest_service_pb2
        from src.services.ingest_service import IngestServiceServicer

        class MockResult:
            episode = sample_episodic_node
            nodes = [sample_entity_node]
            edges = [sample_entity_edge]

        mock_graphiti.add_episode.return_value = MockResult()

        servicer = IngestServiceServicer(mock_graphiti)

        ts = Timestamp()
        ts.FromDatetime(datetime.now(timezone.utc))

        episode1 = ingest_service_pb2.AddEpisodeRequest(
            group_id='test-group',
            name='Episode 1',
            episode_body='Content 1',
            source=common_pb2.EPISODE_TYPE_MESSAGE,
            source_description='Test',
        )
        episode1.reference_time.CopyFrom(ts)

        async def request_iterator():
            yield ingest_service_pb2.StreamEpisodeRequest(
                correlation_id='corr-1',
                episode=episode1,
            )
            yield ingest_service_pb2.StreamEpisodeRequest(
                correlation_id='corr-2',
                episode=episode1,
            )

        context = MagicMock()

        responses = []
        async for response in servicer.StreamEpisodes(request_iterator(), context):
            responses.append(response)

        assert len(responses) == 2
        assert responses[0].correlation_id == 'corr-1'
        assert responses[1].correlation_id == 'corr-2'

    @pytest.mark.asyncio
    async def test_stream_episodes_with_error(
        self, mock_graphiti, sample_episodic_node, sample_entity_node, sample_entity_edge
    ):
        """Test StreamEpisodes with error handling."""
        from google.protobuf.timestamp_pb2 import Timestamp

        from src.generated.graphiti.v1 import common_pb2, ingest_service_pb2
        from src.services.ingest_service import IngestServiceServicer

        class MockResult:
            episode = sample_episodic_node
            nodes = [sample_entity_node]
            edges = [sample_entity_edge]

        # First call succeeds, second fails
        mock_graphiti.add_episode = AsyncMock(
            side_effect=[MockResult(), RuntimeError('Stream error')]
        )

        servicer = IngestServiceServicer(mock_graphiti)

        ts = Timestamp()
        ts.FromDatetime(datetime.now(timezone.utc))

        episode1 = ingest_service_pb2.AddEpisodeRequest(
            group_id='test-group',
            name='Episode 1',
            episode_body='Content 1',
            source=common_pb2.EPISODE_TYPE_MESSAGE,
            source_description='Test',
        )
        episode1.reference_time.CopyFrom(ts)

        async def request_iterator():
            yield ingest_service_pb2.StreamEpisodeRequest(
                correlation_id='corr-1',
                episode=episode1,
            )
            yield ingest_service_pb2.StreamEpisodeRequest(
                correlation_id='corr-2',
                episode=episode1,
            )

        context = MagicMock()

        responses = []
        async for response in servicer.StreamEpisodes(request_iterator(), context):
            responses.append(response)

        assert len(responses) == 2
        # First should have success
        assert responses[0].HasField('success')
        # Second should have error
        assert responses[1].error == 'Stream error'

    @pytest.mark.asyncio
    async def test_stream_episodes_without_correlation_id(
        self, mock_graphiti, sample_episodic_node, sample_entity_node, sample_entity_edge
    ):
        """Test StreamEpisodes without correlation_id."""
        from google.protobuf.timestamp_pb2 import Timestamp

        from src.generated.graphiti.v1 import common_pb2, ingest_service_pb2
        from src.services.ingest_service import IngestServiceServicer

        class MockResult:
            episode = sample_episodic_node
            nodes = [sample_entity_node]
            edges = [sample_entity_edge]

        mock_graphiti.add_episode.return_value = MockResult()

        servicer = IngestServiceServicer(mock_graphiti)

        ts = Timestamp()
        ts.FromDatetime(datetime.now(timezone.utc))

        episode1 = ingest_service_pb2.AddEpisodeRequest(
            group_id='test-group',
            name='Episode 1',
            episode_body='Content 1',
            source=common_pb2.EPISODE_TYPE_MESSAGE,
            source_description='Test',
        )
        episode1.reference_time.CopyFrom(ts)

        async def request_iterator():
            yield ingest_service_pb2.StreamEpisodeRequest(
                # No correlation_id
                episode=episode1,
            )

        context = MagicMock()

        responses = []
        async for response in servicer.StreamEpisodes(request_iterator(), context):
            responses.append(response)

        assert len(responses) == 1
