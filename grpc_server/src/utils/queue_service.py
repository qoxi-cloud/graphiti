"""Async queue service for processing messages by group."""

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Coroutine
from uuid import uuid4

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Status of a queued task."""

    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'


@dataclass
class QueuedTask:
    """Represents a task in the queue."""

    id: str
    group_id: str
    created_at: datetime
    status: TaskStatus = TaskStatus.PENDING
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
    result: Any = None


class QueueService:
    """Service for managing async task queues per group.

    This service provides fire-and-forget task processing with tracking capabilities.
    Tasks are organized by group_id to allow for per-group queue management and
    sequential processing within each group.

    Features:
    - Per-group queue management
    - Concurrent processing with configurable semaphore limits
    - Task status tracking (pending, processing, completed, failed)
    - Graceful shutdown with worker cancellation
    - Automatic worker lifecycle management
    """

    def __init__(self, max_concurrent: int = 10):
        """Initialize the queue service.

        Args:
            max_concurrent: Maximum number of concurrent tasks across all groups.
                           Defaults to 10.
        """
        self._queues: dict[str, asyncio.Queue[tuple[str, Coroutine[Any, Any, Any]]]] = defaultdict(
            asyncio.Queue
        )
        self._tasks: dict[str, QueuedTask] = {}
        self._workers: dict[str, asyncio.Task[None]] = {}
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._running = True
        self._lock = asyncio.Lock()

    async def add_task(
        self,
        group_id: str,
        coro: Coroutine[Any, Any, Any],
        task_id: str | None = None,
    ) -> str:
        """Add a task to the group's queue.

        Args:
            group_id: The group identifier for queue partitioning.
            coro: The coroutine to execute.
            task_id: Optional custom task ID. If not provided, a UUID will be generated.

        Returns:
            The task ID for status tracking.

        Raises:
            RuntimeError: If the queue service has been shut down.
        """
        if not self._running:
            raise RuntimeError('Queue service has been shut down')

        if task_id is None:
            task_id = str(uuid4())

        task = QueuedTask(
            id=task_id,
            group_id=group_id,
            created_at=datetime.now(timezone.utc),
        )
        self._tasks[task_id] = task

        await self._queues[group_id].put((task_id, coro))

        logger.debug(f'Task {task_id} queued for group {group_id}')

        # Start worker for this group if not running
        async with self._lock:
            if group_id not in self._workers or self._workers[group_id].done():
                self._workers[group_id] = asyncio.create_task(
                    self._process_queue(group_id),
                    name=f'queue-worker-{group_id}',
                )
                logger.info(f'Started queue worker for group {group_id}')

        return task_id

    async def _process_queue(self, group_id: str) -> None:
        """Process tasks from a group's queue.

        This worker processes tasks sequentially within a group while respecting
        the global concurrency limit via semaphore.

        Args:
            group_id: The group identifier for the queue to process.
        """
        queue = self._queues[group_id]

        while self._running:
            try:
                task_id, coro = await asyncio.wait_for(queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                if queue.empty():
                    logger.debug(f'Queue empty for group {group_id}, worker exiting')
                    break
                continue
            except asyncio.CancelledError:
                logger.info(f'Worker for group {group_id} was cancelled')
                raise

            task = self._tasks.get(task_id)
            if not task:
                logger.warning(f'Task {task_id} not found in task registry')
                continue

            async with self._semaphore:
                task.status = TaskStatus.PROCESSING
                task.started_at = datetime.now(timezone.utc)
                logger.debug(f'Processing task {task_id} for group {group_id}')

                try:
                    result = await coro
                    task.status = TaskStatus.COMPLETED
                    task.completed_at = datetime.now(timezone.utc)
                    task.result = result
                    logger.debug(f'Task {task_id} completed for group {group_id}')
                except asyncio.CancelledError:
                    task.status = TaskStatus.FAILED
                    task.completed_at = datetime.now(timezone.utc)
                    task.error = 'Task was cancelled'
                    logger.warning(f'Task {task_id} was cancelled')
                    raise
                except Exception as e:
                    task.status = TaskStatus.FAILED
                    task.completed_at = datetime.now(timezone.utc)
                    task.error = str(e)
                    logger.error(f'Task {task_id} failed: {e}', exc_info=True)

    def get_task_status(self, task_id: str) -> QueuedTask | None:
        """Get the status of a task.

        Args:
            task_id: The task identifier.

        Returns:
            The QueuedTask object if found, None otherwise.
        """
        return self._tasks.get(task_id)

    def get_group_stats(self, group_id: str) -> dict[str, int]:
        """Get statistics for a group's queue.

        Args:
            group_id: The group identifier.

        Returns:
            Dictionary containing task counts by status.
        """
        group_tasks = [t for t in self._tasks.values() if t.group_id == group_id]
        return {
            'total': len(group_tasks),
            'pending': sum(1 for t in group_tasks if t.status == TaskStatus.PENDING),
            'processing': sum(1 for t in group_tasks if t.status == TaskStatus.PROCESSING),
            'completed': sum(1 for t in group_tasks if t.status == TaskStatus.COMPLETED),
            'failed': sum(1 for t in group_tasks if t.status == TaskStatus.FAILED),
            'queue_size': self._queues[group_id].qsize() if group_id in self._queues else 0,
        }

    def get_all_stats(self) -> dict[str, dict[str, int]]:
        """Get statistics for all groups.

        Returns:
            Dictionary mapping group_id to their statistics.
        """
        groups = set(t.group_id for t in self._tasks.values())
        return {group_id: self.get_group_stats(group_id) for group_id in groups}

    def is_worker_running(self, group_id: str) -> bool:
        """Check if a worker is running for a group.

        Args:
            group_id: The group identifier.

        Returns:
            True if a worker is active for the group, False otherwise.
        """
        return group_id in self._workers and not self._workers[group_id].done()

    def get_pending_count(self, group_id: str) -> int:
        """Get the number of pending tasks for a group.

        Args:
            group_id: The group identifier.

        Returns:
            Number of tasks waiting in the queue.
        """
        if group_id not in self._queues:
            return 0
        return self._queues[group_id].qsize()

    async def wait_for_task(self, task_id: str, timeout: float | None = None) -> QueuedTask | None:
        """Wait for a task to complete.

        Args:
            task_id: The task identifier.
            timeout: Maximum time to wait in seconds. None for no timeout.

        Returns:
            The completed QueuedTask, or None if task not found or timeout.
        """
        task = self._tasks.get(task_id)
        if not task:
            return None

        start_time = asyncio.get_event_loop().time()

        while task.status in (TaskStatus.PENDING, TaskStatus.PROCESSING):
            if timeout is not None:
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed >= timeout:
                    return task
            await asyncio.sleep(0.1)

        return task

    def clear_completed_tasks(self, group_id: str | None = None, max_age_seconds: float = 3600):
        """Clear completed and failed tasks from memory.

        Args:
            group_id: Optional group to clear. If None, clears all groups.
            max_age_seconds: Only clear tasks older than this many seconds.
        """
        now = datetime.now(timezone.utc)
        tasks_to_remove = []

        for task_id, task in self._tasks.items():
            if group_id is not None and task.group_id != group_id:
                continue

            if task.status not in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                continue

            if task.completed_at is not None:
                age = (now - task.completed_at).total_seconds()
                if age >= max_age_seconds:
                    tasks_to_remove.append(task_id)

        for task_id in tasks_to_remove:
            del self._tasks[task_id]

        if tasks_to_remove:
            logger.info(f'Cleared {len(tasks_to_remove)} completed tasks')

    async def shutdown(self, timeout: float = 30.0):
        """Gracefully shutdown the queue service.

        Stops accepting new tasks and waits for current tasks to complete
        or cancels them after the timeout.

        Args:
            timeout: Maximum time to wait for tasks to complete before cancelling.
        """
        logger.info('Shutting down queue service...')
        self._running = False

        # Collect all active workers
        active_workers = [worker for worker in self._workers.values() if not worker.done()]

        if not active_workers:
            logger.info('No active workers to shut down')
            return

        # Wait for workers to finish with timeout
        try:
            await asyncio.wait_for(
                asyncio.gather(*active_workers, return_exceptions=True),
                timeout=timeout,
            )
            logger.info('All workers completed gracefully')
        except asyncio.TimeoutError:
            logger.warning(f'Timeout waiting for workers, cancelling {len(active_workers)} workers')
            for worker in active_workers:
                if not worker.done():
                    worker.cancel()

            # Wait for cancellation to complete
            await asyncio.gather(*active_workers, return_exceptions=True)
            logger.info('All workers cancelled')

        logger.info('Queue service shutdown complete')
