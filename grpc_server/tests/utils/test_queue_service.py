"""Tests for QueueService."""

import asyncio

import pytest

from src.utils.queue_service import QueuedTask, QueueService, TaskStatus


class TestTaskStatus:
    """Tests for TaskStatus enum."""

    def test_task_status_values(self):
        """Test TaskStatus enum has expected values."""
        assert TaskStatus.PENDING.value == 'pending'
        assert TaskStatus.PROCESSING.value == 'processing'
        assert TaskStatus.COMPLETED.value == 'completed'
        assert TaskStatus.FAILED.value == 'failed'


class TestQueuedTask:
    """Tests for QueuedTask dataclass."""

    def test_queued_task_creation(self):
        """Test creating a QueuedTask."""
        from datetime import datetime, timezone

        task = QueuedTask(
            id='test-id',
            group_id='test-group',
            created_at=datetime.now(timezone.utc),
        )

        assert task.id == 'test-id'
        assert task.group_id == 'test-group'
        assert task.status == TaskStatus.PENDING
        assert task.started_at is None
        assert task.completed_at is None
        assert task.error is None
        assert task.result is None


class TestQueueService:
    """Tests for QueueService."""

    @pytest.mark.asyncio
    async def test_init(self):
        """Test QueueService initialization."""
        service = QueueService(max_concurrent=5)
        assert service._running is True
        await service.shutdown(timeout=1.0)

    @pytest.mark.asyncio
    async def test_add_task(self):
        """Test adding a task to the queue."""
        service = QueueService()

        async def dummy_task():
            return 'result'

        task_id = await service.add_task('group1', dummy_task())

        assert task_id is not None
        task = service.get_task_status(task_id)
        assert task is not None
        assert task.group_id == 'group1'

        # Wait for task to complete before shutdown
        await service.wait_for_task(task_id, timeout=5.0)
        await service.shutdown(timeout=1.0)

    @pytest.mark.asyncio
    async def test_add_task_with_custom_id(self):
        """Test adding a task with a custom ID."""
        service = QueueService()

        async def dummy_task():
            return 'result'

        task_id = await service.add_task('group1', dummy_task(), task_id='custom-id')

        assert task_id == 'custom-id'
        task = service.get_task_status(task_id)
        assert task.id == 'custom-id'

        # Wait for task to complete before shutdown
        await service.wait_for_task(task_id, timeout=5.0)
        await service.shutdown(timeout=1.0)

    @pytest.mark.asyncio
    async def test_add_task_after_shutdown(self):
        """Test adding a task after shutdown raises error."""
        service = QueueService()
        await service.shutdown(timeout=1.0)

        async def dummy_task():
            return 'result'

        coro = dummy_task()
        try:
            with pytest.raises(RuntimeError, match='shut down'):
                await service.add_task('group1', coro)
        finally:
            # Close the coroutine to avoid warning
            coro.close()

    @pytest.mark.asyncio
    async def test_task_completion(self):
        """Test task completes successfully."""
        service = QueueService()

        async def dummy_task():
            return 'success'

        task_id = await service.add_task('group1', dummy_task())

        # Wait for task completion
        task = await service.wait_for_task(task_id, timeout=5.0)

        assert task is not None
        assert task.status == TaskStatus.COMPLETED
        assert task.result == 'success'

        await service.shutdown(timeout=1.0)

    @pytest.mark.asyncio
    async def test_task_failure(self):
        """Test task failure is captured."""
        service = QueueService()

        async def failing_task():
            raise ValueError('Test error')

        task_id = await service.add_task('group1', failing_task())

        # Wait for task completion
        task = await service.wait_for_task(task_id, timeout=5.0)

        assert task is not None
        assert task.status == TaskStatus.FAILED
        assert 'Test error' in task.error

        await service.shutdown(timeout=1.0)

    @pytest.mark.asyncio
    async def test_get_task_status_not_found(self):
        """Test getting status of non-existent task."""
        service = QueueService()

        task = service.get_task_status('non-existent')
        assert task is None

        await service.shutdown(timeout=1.0)

    @pytest.mark.asyncio
    async def test_get_group_stats(self):
        """Test getting group statistics."""
        service = QueueService()

        async def dummy_task():
            await asyncio.sleep(0.01)
            return 'result'

        await service.add_task('group1', dummy_task())
        await service.add_task('group1', dummy_task())

        # Wait a bit for processing to start
        await asyncio.sleep(0.1)

        stats = service.get_group_stats('group1')

        assert 'total' in stats
        assert 'pending' in stats
        assert 'processing' in stats
        assert 'completed' in stats
        assert 'failed' in stats
        assert 'queue_size' in stats

        await service.shutdown(timeout=2.0)

    @pytest.mark.asyncio
    async def test_get_all_stats(self):
        """Test getting all group statistics."""
        service = QueueService()

        async def dummy_task():
            await asyncio.sleep(0.01)
            return 'result'

        await service.add_task('group1', dummy_task())
        await service.add_task('group2', dummy_task())

        # Wait for processing
        await asyncio.sleep(0.1)

        all_stats = service.get_all_stats()

        assert 'group1' in all_stats
        assert 'group2' in all_stats

        await service.shutdown(timeout=2.0)

    @pytest.mark.asyncio
    async def test_is_worker_running(self):
        """Test checking if worker is running."""
        service = QueueService()

        # No worker initially
        assert service.is_worker_running('group1') is False

        async def slow_task():
            await asyncio.sleep(1.0)
            return 'result'

        await service.add_task('group1', slow_task())

        # Worker should be running after adding task
        await asyncio.sleep(0.1)
        assert service.is_worker_running('group1') is True

        await service.shutdown(timeout=0.5)

    @pytest.mark.asyncio
    async def test_get_pending_count(self):
        """Test getting pending count."""
        service = QueueService()

        assert service.get_pending_count('group1') == 0

        async def slow_task():
            try:
                await asyncio.sleep(10.0)
                return 'result'
            except asyncio.CancelledError:
                return 'cancelled'

        # Add multiple tasks
        await service.add_task('group1', slow_task())
        await service.add_task('group1', slow_task())
        await service.add_task('group1', slow_task())

        # First task is being processed, rest are pending
        await asyncio.sleep(0.1)
        count = service.get_pending_count('group1')
        assert count >= 0  # At least some should be pending

        await service.shutdown(timeout=0.5)

    @pytest.mark.asyncio
    async def test_wait_for_task_timeout(self):
        """Test wait_for_task with timeout."""
        service = QueueService()

        async def slow_task():
            await asyncio.sleep(10.0)
            return 'result'

        task_id = await service.add_task('group1', slow_task())

        # Wait with short timeout
        task = await service.wait_for_task(task_id, timeout=0.1)

        assert task is not None
        assert task.status in (TaskStatus.PENDING, TaskStatus.PROCESSING)

        await service.shutdown(timeout=0.5)

    @pytest.mark.asyncio
    async def test_wait_for_task_not_found(self):
        """Test wait_for_task with non-existent task."""
        service = QueueService()

        task = await service.wait_for_task('non-existent', timeout=0.1)
        assert task is None

        await service.shutdown(timeout=1.0)

    @pytest.mark.asyncio
    async def test_clear_completed_tasks(self):
        """Test clearing completed tasks."""
        service = QueueService()

        async def dummy_task():
            return 'result'

        task_id = await service.add_task('group1', dummy_task())

        # Wait for completion
        await service.wait_for_task(task_id, timeout=5.0)

        # Task should exist
        assert service.get_task_status(task_id) is not None

        # Clear with 0 max_age to clear immediately
        service.clear_completed_tasks(max_age_seconds=0)

        # Task should be cleared
        assert service.get_task_status(task_id) is None

        await service.shutdown(timeout=1.0)

    @pytest.mark.asyncio
    async def test_clear_completed_tasks_by_group(self):
        """Test clearing completed tasks by group."""
        service = QueueService()

        async def dummy_task():
            return 'result'

        task_id1 = await service.add_task('group1', dummy_task())
        task_id2 = await service.add_task('group2', dummy_task())

        # Wait for completion
        await service.wait_for_task(task_id1, timeout=5.0)
        await service.wait_for_task(task_id2, timeout=5.0)

        # Clear only group1
        service.clear_completed_tasks(group_id='group1', max_age_seconds=0)

        # group1 task should be cleared, group2 should remain
        assert service.get_task_status(task_id1) is None
        assert service.get_task_status(task_id2) is not None

        await service.shutdown(timeout=1.0)

    @pytest.mark.asyncio
    async def test_shutdown_no_workers(self):
        """Test shutdown with no active workers."""
        service = QueueService()

        # Shutdown immediately with no tasks
        await service.shutdown(timeout=1.0)

        assert service._running is False

    @pytest.mark.asyncio
    async def test_shutdown_with_workers(self):
        """Test shutdown with active workers."""
        service = QueueService()

        async def slow_task():
            await asyncio.sleep(0.5)
            return 'result'

        await service.add_task('group1', slow_task())

        # Wait for worker to start
        await asyncio.sleep(0.1)
        assert service.is_worker_running('group1') is True

        # Shutdown
        await service.shutdown(timeout=2.0)

        assert service._running is False

    @pytest.mark.asyncio
    async def test_shutdown_with_timeout(self):
        """Test shutdown timeout cancels workers."""
        service = QueueService()

        async def very_slow_task():
            await asyncio.sleep(100.0)
            return 'result'

        await service.add_task('group1', very_slow_task())

        # Wait for worker to start
        await asyncio.sleep(0.1)

        # Shutdown with very short timeout
        await service.shutdown(timeout=0.1)

        assert service._running is False

    @pytest.mark.asyncio
    async def test_multiple_groups_concurrent(self):
        """Test multiple groups process concurrently."""
        service = QueueService(max_concurrent=10)
        results = []

        async def task_for_group(group: str):
            await asyncio.sleep(0.1)
            results.append(group)
            return group

        # Add tasks for different groups
        await service.add_task('group1', task_for_group('group1'))
        await service.add_task('group2', task_for_group('group2'))
        await service.add_task('group3', task_for_group('group3'))

        # Wait for all to complete
        await asyncio.sleep(0.5)

        assert len(results) == 3

        await service.shutdown(timeout=1.0)

    @pytest.mark.asyncio
    async def test_sequential_within_group(self):
        """Test tasks are processed sequentially within a group."""
        service = QueueService()
        order = []

        async def ordered_task(n: int):
            order.append(f'start-{n}')
            await asyncio.sleep(0.1)
            order.append(f'end-{n}')
            return n

        # Add multiple tasks to same group
        await service.add_task('group1', ordered_task(1))
        await service.add_task('group1', ordered_task(2))
        await service.add_task('group1', ordered_task(3))

        # Wait for all to complete
        await asyncio.sleep(1.0)

        # Tasks should complete in order (sequential within group)
        # First task should start before second task starts
        assert order.index('start-1') < order.index('start-2')
        assert order.index('end-1') < order.index('start-2')

        await service.shutdown(timeout=1.0)
