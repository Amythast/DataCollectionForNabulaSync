
from danmu_fetcher import DouyinDanmuFetcher


class DanmuFetcherHelper:
    def __init__(self, config_manager):
        self.config_manager = config_manager

    def fetch_danmu(self, platform: str, room_id: str, save_danmu_file_path: str):
        if platform == 'DouyinLive':
            DouyinDanmuFetcher(room_id, save_danmu_file_path, self.config_manager.split_time).start()
