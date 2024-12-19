from contextvars import ContextVar
from config_manager import ConfigManager
from live_platform.base.base_task_pool import BaseTaskPool
from common.task_manager import TaskManager, SafeGroupIDGenerator

# task_pool_var: ContextVar[BaseTaskPool] = ContextVar("task_pool")
config_manager_var: ContextVar[ConfigManager] = ContextVar("config_manager")
recoding_var: ContextVar[set] = ContextVar("recording")
task_manager_var: ContextVar[TaskManager] = ContextVar("task_manager")
group_id_gen_var: ContextVar[SafeGroupIDGenerator] = ContextVar("group_id_gen")
