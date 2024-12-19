from dataclasses import dataclass
from typing import Dict, List

from live_platform.base.live.base_model import BaseLiveInfo, BaseLivePortInfo
from common.logger import logger


@dataclass
class DouyinSubscribe:
    is_member: bool
    level: int
    identify_type: int
    buy_type: int
    open: int


@dataclass
class DouyinOwner:
    id_str: str
    sec_uid: str
    avatar_thumb: List[str]
    follow_info: int
    suscribe: DouyinSubscribe
    open_id_str: str


@dataclass
class DouyinLiveStats:
    total_user_desp: str
    like_count: int
    total_user_str: str
    user_count_str: int


@dataclass
class DouyinLivePortInfo(BaseLivePortInfo):
    cookie: Dict

    def display_info(self):
        super().display_info()


class DouyinLiveInfo(BaseLiveInfo):
    # live room info
    id_str: str  # room id
    status: int
    title: str
    user_count_str: str
    cookie: Dict
    cover: List[str]
    stream_url: Dict[str, Dict]
    owner: DouyinOwner
    room_auth: Dict
    live_room_mode: int
    stats: DouyinLiveStats

    def display_info(self):
        logger.info(f"Platform: {self.platform}, Anchor name: {self.anchor_name} Live Id: {self.live_id}, "
                    f"Live URL: {self.live_url}, Record Quality: {self.record_quality}, Need Record: {self.need_record}"
                    f"Title: {self.title}, Status: {self.status}, User Count: {self.user_count_str}")

