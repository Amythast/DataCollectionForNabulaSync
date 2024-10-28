from abc import abstractmethod, ABC
from typing import Dict


class AbstractStreamCrawler(ABC):

    @abstractmethod
    async def get_live_port_info(self):
        """
        get live info
        """
        pass

    @abstractmethod
    async def start_record(self):
        """
        start record
        """
        pass


class AbstractDanmuFetcher(ABC):

    @abstractmethod
    async def get_danmu_port_info(self):
        """
        get danmu info
        """
        pass

    @abstractmethod
    async def start_fetch(self):
        """
        start fetch
        """
        pass


class AbstractLogin(ABC):
    @abstractmethod
    async def begin(self):
        pass

    @abstractmethod
    async def login_by_cookies(self):
        pass


class AbstractStore(ABC):
    @abstractmethod
    async def store_stream(self, stream_item: Dict):
        pass

    @abstractmethod
    async def store_danmu(self, danmu_item: Dict):
        pass
