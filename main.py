import signal
import threading

from config_helper import *
from record_helper import RecordManager
from utils import (check_ffmpeg_existence)


def signal_handler(_signal, _frame):
    sys.exit(0)


version = "v3.0.7"
platforms = (
    "\n国内站点：抖音|快手|虎牙|斗鱼|YY|B站|小红书|bigo|blued|网易CC|千度热播|猫耳FM|Look|TwitCasting|百度|微博|"
    "酷狗|LiveMe|花椒|流星|Acfun|时光|映客"
    "\n海外站点：TikTok|AfreecaTV|PandaTV|WinkTV|FlexTV|PopkonTV|TwitchTV|ShowRoom"
)

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
signal.signal(signal.SIGTERM, signal_handler)

# --------------------------检测是否存在ffmpeg-------------------------------------
check_ffmpeg_existence(ffmpeg_path)

# --------------------------初始化程序-------------------------------------
print("-----------------------------------------------------")
print("|                DouyinLiveRecorder                 |")
print("-----------------------------------------------------")

print(f"版本号: {version}")
print(f"GitHub: https://github.com/ihmily/DouyinLiveRecorder")
print(f'支持平台: {platforms}')
print('.....................................................')

os.makedirs(os.path.dirname(config_file), exist_ok=True)

# 备份配置
backup_thread = threading.Thread(target=config_manager.backup_config_start, args=(), daemon=True)
backup_thread.start()

config_manager = ConfigManager()
config_manager.load_config()
record_manager = RecordManager(config_manager)  # 初始化录制管理器

while True:
    record_manager.start_record_threads()  # 启动录制线程

    if first_run:
        display_info_thread = threading.Thread(target=record_manager.display_info, args=(), daemon=True)
        display_info_thread.start()
        change_max_connect_thread = threading.Thread(target=record_manager.change_max_connect, args=(), daemon=True)
        change_max_connect_thread.start()

        first_run = False

    time.sleep(3)
    config_manager.load_config()  # 重新加载配置, 处理配置文件修改

