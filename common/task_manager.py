import threading
import time
import uuid
from abc import ABC, abstractmethod
from concurrent.futures import Future
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from typing import Callable, Any, List, Optional
from common.logger import logger


class OnCompleteCallback(ABC):
    @abstractmethod
    def on_complete(self, task_name: str, task_result: Any, task_error: Optional[Exception]):
        """任务完成后的回调方法"""
        pass


class SafeGroupIDGenerator:
    def __init__(self):
        self._lock = threading.Lock()  # 用于保护生成器的锁
        self._counter = 0
        self._current_group_id = None

    def get_group_id(self) -> str:
        """
        返回一个线程安全的 group_id，每两次调用生成同一个 group_id。
        """
        with self._lock:  # 确保线程安全
            if self._counter % 2 == 0:  # 每两次更换一个新的 group_id
                self._current_group_id = str(uuid.uuid4())
            self._counter += 1
            return self._current_group_id


class TaskWrapper:
    """封装任务，使其能在完成时通知 TaskManager"""
    def __init__(self, task_group_id: str, task_name: str,  func: Callable[..., Any], callback: Optional[OnCompleteCallback] = None, immediate: bool = False, *args, **kwargs):
        self.task_group_id = task_group_id
        self.task_name = task_name
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.immediate = immediate
        self.callback = callback  # 任务完成后的回调
        self.future: Optional[Future] = None

    def run(self, executor: ThreadPoolExecutor):
        """启动任务并注册完成回调"""
        self.future = executor.submit(self.func, *self.args, **self.kwargs)
        self.future.add_done_callback(self._on_done)

    def _on_done(self, future: Future):
        """任务完成时的回调，通知 TaskManager"""
        task_result = None
        task_error = None
        try:
            task_result = future.result()
            logger.info(f"Task {self.task_name} completed successfully.")
        except Exception as e:
            task_error = e
            logger.error(f"Task {self.task_name} failed with error: {e}")
        finally:
            # 通知任务管理器任务已完成
            self.callback.on_complete(self.task_name, task_result, task_error)


class TaskManager:
    def __init__(self, max_workers: int):
        self.max_workers = max_workers
        self.task_queue = Queue()
        self.results = []
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self.interval = 180  # 任务执行间隔,单位秒
        self.timer = None
        self._running = False
        self.task_groups = {}  # 存储task_queue中的任务，key为task_group_id
        self.default_callback = type(
            "DefaultOnComplete",
            (OnCompleteCallback,),
            {
                "on_complete": lambda self, task_name, result, error: (
                    logger.error(f"Task {task_name} failed with error: {error}")
                    if error
                    else logger.info(f"Task {task_name} completed with result: {result}")
                )
            }
        )()

    def create_task(self, task_name: str, func: Callable[..., Any], *args, on_complete: Optional[OnCompleteCallback] = None, immediate: bool = False, task_group_id: Optional[str] = None, **kwargs) -> None:
        """
        创建任务
        :param task_name: 任务名
        :param on_complete: 任务完成时的回调
        :param immediate: 如果为 True，则任务立即执行，忽略间隔时间
        :param task_group_id: 任务组 ID，相同组 ID 的任务将一起执行
        :param func: 任务函数
        :param args: 任务参数
        """
        if task_group_id is None:
            task_group_id = str(uuid.uuid4())
        if not on_complete:
            on_complete = self.default_callback
        task_wrapper = TaskWrapper(task_group_id, task_name, func, on_complete, *args, **kwargs)

        if immediate:
            self._submit_tasks([task_wrapper])
            logger.info(f"Task {task_name} submitted.")
        else:
            # 检查 group_id 以存储到 task_groups
            if task_group_id not in self.task_groups:
                self.task_groups[task_group_id] = [task_wrapper]
                self.task_queue.put(task_group_id)
            else:
                self.task_groups[task_group_id].append(task_wrapper)
            logger.info(f"Task {task_name} added in queue.")

    def _submit_tasks(self, tasks: List[TaskWrapper]) -> None:
        """将任务列表提交到线程池"""
        for task in tasks:
            task.run(self.executor)

    def _pop_and_execute_tasks(self):
        """定时检查并执行任务队列中的任务"""
        while not self.task_queue.empty():
            task_group_id = self.task_queue.get()

            # 检查该任务组是否存在，不存在则跳过
            tasks_to_execute = self.task_groups.pop(task_group_id, [])
            task_names = [task.task_name for task in tasks_to_execute]
            logger.info(f"Executing tasks in group {task_names}")
            if tasks_to_execute:
                self._submit_tasks(tasks_to_execute)

            # 控制执行间隔
            time.sleep(self.interval)

    def start(self):
        """启动任务管理器"""
        self._running = True
        self.timer = threading.Timer(self.interval, self._pop_and_execute_tasks)
        self.timer.start()

    def stop(self):
        """停止任务管理器并关闭线程池"""
        self._running = False
        if self.timer:
            self.timer.cancel()
        self.executor.shutdown(wait=True)

    def shutdown(self) -> None:
        """关闭线程池，释放资源"""
        self.executor.shutdown(wait=True)


# 示例任务函数
def sample_task(duration: int, name: str):
    time.sleep(duration)
    print(f"Task {name} completed in {duration} seconds")
    test = 1
    return name, test


class TestCallback(OnCompleteCallback):
    def on_complete(self, task_name: str, task_result: Any, task_error: Optional[Exception]):
        if task_error:
            print(f"Callback: Task '{task_name}' failed with error: {task_error}.")
        else:
            print(f"Callback: Task '{task_name}' completed successfully with result: {task_result[0]},{task_result[1]}.")


# 使用 TaskManager
if __name__ == "__main__":
    manager = TaskManager(max_workers=3)
    callback = TestCallback()

    # 创建任务
    group_id = str(uuid.uuid4())
    # manager.create_task("Task A", sample_task, duration=2, name="A", task_group_id=group_id)
    # manager.create_task("Task B", sample_task, duration=1, name="B", task_group_id=group_id)
    # manager.create_task("Task C", sample_task, duration=3, name="C", immediate=True)
    # manager.create_task("Task D", sample_task, duration=1, name="D")
    # manager.create_task("Task E", sample_task, duration=2, name="E")
    manager.create_task("Task F", sample_task, duration=1, name="F", on_complete=callback)

    # 启动任务管理器
    manager.start()
    time.sleep(1000)  # 运行一段时间

    # 停止任务管理器并打印结果
    manager.stop()
