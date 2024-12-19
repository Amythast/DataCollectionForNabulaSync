from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict

from common.logger import logger


@dataclass
class BaseLivePortInfo(ABC):
    live_date: str  # %Y-%m-%d
    live_url: int
    live_id: str  # room id
    platform: str
    category: str
    anchor_name: str
    is_live: bool
    title: str
    flv_url: str
    m3u8_url: str
    record_url: str  # 录制使用的url

    @abstractmethod
    def display_info(self):
        """
        Display the information of the data class.
        """
        logger.info(f"Platform: {self.platform}, Anchor Name: {self.anchor_name}, Live URL: {self.live_url}, "
                    f"roomId:{self.live_id}, is_live:{self.is_live}, title:{self.title}")


@dataclass
class BaseLiveInfo(ABC):
    # db data
    live_id: str
    live_url: str
    platform: str
    anchor_name: str
    category: str
    record_quality: str
    need_record: bool

    @classmethod
    def from_dict(cls, data: Dict) -> 'BaseLiveInfo':
        """
        从字典数据创建 BaseLiveInfo 实例。
        """
        return cls(
            live_id=data.get("live_id", ""),
            live_url=data.get("live_url", ""),
            platform=data.get("live_platform", ""),
            anchor_name=data.get("anchor_name", ""),
            category=data.get("category", ""),
            record_quality=data.get("record_quality", ""),
            need_record=bool(data.get("need_record", False))
        )

    def display_info(self):
        """
        Display the information of the data class.
        """
        logger.info(f"Platform: {self.platform}, Anchor name: {self.anchor_name} Live Id: {self.live_id}, "
                    f"Live URL: {self.live_url}, Record Quality: {self.record_quality}, Need Record: {self.need_record}")

