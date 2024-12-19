import subprocess
import urllib.request
from abc import abstractmethod, ABC
from datetime import datetime
from typing import Dict, List

from live_platform.base.base_var import recoding_var
from live_platform.base.live.base_model import BaseLivePortInfo, BaseLiveInfo
from common.logger import logger


class AbstractLiveClient(ABC):
    def __init__(
            self,
            port_info_fetcher: 'AbstractLivePortInfoFetcher',
            stream_fetcher: 'AbstractLiveStreamFetcher',
            danmu_fetcher: 'AbstractLiveDanmuFetcher'
    ):
        self.port_info_fetcher = port_info_fetcher
        self.stream_fetcher = stream_fetcher
        self.danmu_fetcher = danmu_fetcher
        self.recording = recoding_var.get()

    async def get_live_info(self) -> List[BaseLiveInfo]:
        """
        parse url data
        """
        pass

    async def start_record(self, live_infos: List[BaseLiveInfo]):
        """
        start record live stream and danmu stream
        """
        for live_info in live_infos:
            anchor_name = live_info.anchor_name

            if anchor_name in self.recording:
                logger.info(f"Live: {anchor_name} is already being recorded.")
                continue

            if not live_info.need_record:
                logger.info(f"Live: {anchor_name} is marked as does not need to be recorded.")
                continue

            try:
                live_info = await self.port_info_fetcher.get_port_info(live_info)
                port_info = self.port_info_fetcher.process_port_info(live_info)
            except Exception as e:
                logger.error(f"Failed to fetch or process port info for {anchor_name}: {e}")
                continue

            port_info.live_date = datetime.today().strftime("%Y-%m-%d")
            port_info.display_info()

            if not port_info.is_live:
                logger.info(f"Live: {anchor_name} is not live.")
                continue
            if not port_info.anchor_name:
                logger.error(f"[{port_info.live_url}] Failed to retrieve content. Retrying...")
                continue

            self.recording.add(anchor_name)
            try:
                self.stream_fetcher.start_fetch(port_info, task_name=f"fetch {anchor_name} live")
                self.danmu_fetcher.start_fetch(port_info, task_name=f"fetch {anchor_name} danmu")
            except Exception as e:
                logger.error(f"Recording failed for {anchor_name}: {e}")
                self.recording.remove(anchor_name)


class AbstractLivePortInfoFetcher(ABC):

    @abstractmethod
    async def get_port_info(self, live_info: BaseLiveInfo) -> BaseLiveInfo:
        """
        get live stream and danmu port info by live id
        """
        pass

    @abstractmethod
    def process_port_info(self, port_info: BaseLiveInfo) -> BaseLivePortInfo:
        """
        transform different platform params into uniform style;
        add additional info
        """
        pass


class AbstractLiveStreamFetcher(ABC):

    @abstractmethod
    def start_fetch(self, port_info: BaseLivePortInfo, task_name: str = None):
        """
        start record
        """
        pass


class FLVRecoder:
    def __init__(self, port_info: BaseLivePortInfo):
        self.record_url = port_info.record_url
        self.flv_url = port_info.flv_url

    def execute(self, save_file_path):
        if self.flv_url:
            _filepath, _ = urllib.request.urlretrieve(self.record_url, save_file_path)
        else:
            raise Exception('该直播无flv直播流，请切换视频保存类型')


class FFmpegExecutor:
    def __init__(self, config_manager, live_url, record_url, proxy_address):
        self.config_manager = config_manager
        user_agent = (
            "Mozilla/5.0 (Linux; Android 11; SAMSUNG SM-G973U) AppleWebKit/537.36 ("
            "KHTML, like Gecko) SamsungBrowser/14.2 Chrome/87.0.4280.141 Mobile "
            "Safari/537.36"
        )
        analyzeduration = "20000000"
        probesize = "10000000"
        bufsize = "8000k"
        max_muxing_queue_size = "1024"
        for pt_host in self.config_manager.overseas_platform_host:
            if pt_host in live_url:
                analyzeduration = "40000000"
                probesize = "20000000"
                bufsize = "15000k"
                max_muxing_queue_size = "2048"
                break
        self.ffmpeg_command = [
            'ffmpeg', "-y",
            "-v", "verbose",
            "-rw_timeout", "30000000",
            "-loglevel", "error",
            "-hide_banner",
            "-user_agent", user_agent,
            "-protocol_whitelist", "rtmp,crypto,file,http,https,tcp,tls,udp,rtp",
            "-thread_queue_size", "1024",
            "-analyzeduration", analyzeduration,
            "-probesize", probesize,
            "-fflags", "+discardcorrupt",
            "-i", record_url,
            "-bufsize", bufsize,
            "-sn", "-dn",
            "-reconnect_delay_max", "60",
            "-reconnect_streamed", "-reconnect_at_eof",
            "-max_muxing_queue_size", max_muxing_queue_size,
            "-correct_ts_overflow", "1",
        ]

        # 添加代理参数
        if proxy_address:
            self.ffmpeg_command.insert(1, "-http_proxy")
            self.ffmpeg_command.insert(2, proxy_address)

    def execute(self, command):
        base_command = self.ffmpeg_command.copy()
        base_command.extend(command)
        _output = subprocess.check_output(base_command, stderr=subprocess.STDOUT)

    def get_mkv_split_video_command(self, save_file_path):
        return [
            "-flags", "global_header",
            "-c:v", "copy",
            "-c:a", "aac",
            "-map", "0",
            "-f", "segment",
            "-segment_time", self.config_manager.split_time,
            "-segment_format", "matroska",
            "-reset_timestamps", "1",
            save_file_path,
        ]

    def get_mkv_video_command(self, save_file_path):
        return [
            "-flags", "global_header",
            "-map", "0",
            "-c:v", "copy",
            "-c:a", "copy",
            "-f", "matroska",
            "{path}".format(path=save_file_path),
        ]

    def get_mp4_split_video_command(self, save_file_path):
         return [
            "-c:v", "copy",
            "-c:a", "aac",
            "-map", "0",
            "-f", "segment",
            "-segment_time", self.config_manager.split_time,
            "-segment_format", "mp4",
            "-reset_timestamps", "1",
            save_file_path,
        ]

    def get_mp4_video_command(self, save_file_path):
        return [
            "-map", "0",
            "-c:v", "copy",
            "-c:a", "copy",
            "-f", "mp4",
            "{path}".format(path=save_file_path),
        ]

    def get_mkv_split_audio_command(self, save_file_path):
        return [
            "-map", "0:a",
            "-c:a", 'copy',
            "-f", "segment",
            "-segment_time", self.config_manager.split_time,
            "-segment_format", 'mpegts',
            "-reset_timestamps", "1",
            save_file_path,
        ]

    def get_mkv_audio_command(self, save_file_path):
        return [
            "-map", "0:a",
            "-c:a", "copy",
            "-f", "segment",
            "-segment_time", self.config_manager.split_time,
            "-segment_format", "matroska",
            "-reset_timestamps", "1",
            save_file_path,
        ]

    def get_ts_audio_split_command(self, save_path_name):
        return [
            "-map", "0:a",
            "-c:a", 'copy',
            "-f", "segment",
            "-segment_time", self.config_manager.split_time,
            "-segment_format", 'mpegts',
            "-reset_timestamps", "1",
            save_path_name,
        ]

    def get_ts_audio_command(self, save_path_name):
        return [
            "-map", "0:a",
            "-c:a", "copy",
            "-f", "mpegts",
            "{path}".format(path=save_path_name),
        ]

    def get_ts_video_split_command(self, save_path_name):
        return [
            "-c:v", "copy",
            "-c:a", 'copy',
            "-map", "0",
            "-f", "segment",
            "-segment_time", self.config_manager.split_time,
            "-segment_format", "mpegts",
            "-reset_timestamps", "1",
            save_path_name,
        ]

    def get_ts_video_command(self, save_path_name):
        return [
            "-c:v", "copy",
            "-c:a", "copy",
            "-map", "0",
            "-f", "mpegts",
            "{path}".format(path=save_path_name),
        ]


class AbstractLiveDanmuFetcher(ABC):

    @abstractmethod
    def start_fetch(self, port_info: BaseLivePortInfo, task_name: str = None):
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
