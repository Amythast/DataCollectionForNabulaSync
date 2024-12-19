import asyncio
import random
from abc import ABC, abstractmethod
from common.logger import logger


class BaseTask(ABC):
    @abstractmethod
    async def execute(self) -> None:
        """
        Task execution logic.
        """
        pass


class BaseTaskPool:
    def __init__(self, max_workers: int = 10):
        self.queue = asyncio.Queue()
        self.max_workers = max_workers

        # Start worker tasks
        for _ in range(max_workers):
            asyncio.create_task(self._worker())

    async def join(self):
        """
        Wait until all tasks are completed.
        """
        await self.queue.join()
        logger.info("All tasks are completed.")

    async def _worker(self):
        """
        Worker to process tasks from the queue at a fixed interval.

        Args:
        - queue (asyncio.Queue): Queue containing tasks.
        - interval (float): Time in seconds between task executions.
        """
        while True:
            # Wait for a task to be available in the queue
            task = await self.queue.get()

            try:
                # Execute the task
                await task
            except Exception as e:
                logger.error(f"Task failed with error: {e}")
            finally:
                # Notify the queue that the task is done
                self.queue.task_done()

            # Wait for the specified interval before processing the next task
            interval = random.uniform(60 * 4, 60 * 6)  # 4-6 minutes
            await asyncio.sleep(interval)

    async def add_task(self, task: BaseTask):
        """
        Add a task to the queue.

        Args:
        - queue (asyncio.Queue): Queue to add the task to.
        - task (Coroutine): The task (coroutine) to add.
        """
        await self.queue.put(task)

