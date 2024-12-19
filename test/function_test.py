import threading
import time
from concurrent.futures.thread import ThreadPoolExecutor

from common.logger import logger


def task(name):
    """线程执行的任务，记录日志带上线程名称"""
    logger.info(f"Starting task in thread: {name}")
    time.sleep(2)  # 模拟任务执行
    logger.info(f"Completed task in thread: {name}")


# 创建线程池
num_threads = 5  # 设置线程数量
with ThreadPoolExecutor(max_workers=num_threads) as executor:
    # 提交任务，设置线程名称
    for i in range(num_threads):
        executor.submit(task, f"Thread-{i + 1}")

# 等待所有线程完成
executor.shutdown(wait=True)


threading.Thread(target=task, args=(), daemon=True).start()
