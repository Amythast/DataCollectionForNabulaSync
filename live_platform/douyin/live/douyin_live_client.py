from typing import Dict, List

from dao.repository import query_target_live_by_platform
from live_platform.base.base_var import task_manager_var
from live_platform.base.live.base_crawler import AbstractLiveClient
from live_platform.douyin.live.danmu.douyin_live_danmu_fetcher import DouyinLiveDanmuFetcher
from live_platform.douyin.live.douyin_live_port_info_fetcher import DouyinLiveLivePortInfoFetcher
from live_platform.douyin.live.douyin_model import DouyinLiveInfo
from live_platform.douyin.live.stream.douyin_live_stream_fetcher import DouyinLiveLiveStreamFetcher


class DouyinLiveClient(AbstractLiveClient):
    def __init__(self):
        super().__init__(
            port_info_fetcher=DouyinLiveLivePortInfoFetcher(),
            stream_fetcher=DouyinLiveLiveStreamFetcher(),
            danmu_fetcher=DouyinLiveDanmuFetcher()
        )
        self.platform = "douyin"

    async def get_live_info(self) -> List[DouyinLiveInfo]:
        records = await query_target_live_by_platform(self.platform)
        return [DouyinLiveInfo.from_dict(record) for record in records]

    async def start_record(self, live_infos: List[DouyinLiveInfo]):
        super(live_infos)
