import functools
import signal
import threading

import schedule

from config_manager import *
from common.utils import check_ffmpeg_existence
from file_processor.schedule_process_files import process_live_record_folders
from live_platform.base.base_var import *
from dao import repository
from live_platform.douyin.live.douyin_live_client import DouyinLiveClient


def signal_handler(_signal, _frame):
    sys.exit(0)


text_no_repeat_url = []
first_run = True
start_display_time = datetime.datetime.now()
global_proxy = False
script_path = os.path.split(os.path.realpath(sys.argv[0]))[0]
config_file = f'{script_path}/config/config.ini'
url_config_file = f'{script_path}/config/URL_config.ini'
backup_dir = f'{script_path}/backup_config'
ffmpeg_path = f"{script_path}/ffmpeg.exe"
default_path = f'{script_path}/downloads'

os.makedirs(default_path, exist_ok=True)

config_manager = ConfigManager()
config_manager_var.set(config_manager)
signal.signal(signal.SIGTERM, signal_handler)

# --------------------------检测是否存在ffmpeg-------------------------------------
check_ffmpeg_existence(ffmpeg_path)

# --------------------------初始化程序-------------------------------------
print("-----------------------------------------------------")
print("|           DataCollectionForNebulaSync             |")
print("-----------------------------------------------------")

os.makedirs(os.path.dirname(config_file), exist_ok=True)

# 备份配置
backup_thread = threading.Thread(target=config_manager.backup_config_start, args=(), daemon=True)
backup_thread.start()

config_manager.load_config()
task_manager = TaskManager(max_workers=config_manager.max_request)
task_manager_var.set(task_manager)
group_id_gen_var.set(SafeGroupIDGenerator())
recoding_var.set(set())

live_clients = [DouyinLiveClient()]
schedule.every(2).hours.do(functools.partial(process_live_record_folders, config_manager.video_save_path))

while True:
    for client in live_clients:
        target_lives = await client.get_live_info()
        client.start_record(target_lives)

    time.sleep(30)
    config_manager.load_config()  # 重新加载配置, 处理配置文件修改
    schedule.run_pending()
