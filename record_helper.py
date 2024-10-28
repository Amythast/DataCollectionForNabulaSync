import datetime
import os
import random
import re
import subprocess
import sys
import threading
import time
from typing import Dict, Any
import urllib.request

from network.config_helper import ConfigManager
from danmu_fetcher.danmu_fetcher_helper import DanmuFetcherHelper
from utils.logger import logger
from utils import (delete_line, transform_int_to_time)
from deep_translator import GoogleTranslator
from translate import Translator
from network.spider import (
    get_douyin_stream_url,
    get_douyin_stream_data,
    get_douyin_app_stream_data,
    get_tiktok_stream_url,
    get_tiktok_stream_data,
    get_kuaishou_stream_url,
    get_kuaishou_stream_data,
    get_huya_stream_url,
    get_huya_stream_data,
    get_douyu_stream_url,
    get_douyu_info_data,
    get_yy_stream_url,
    get_yy_stream_data,
    get_bilibili_stream_url,
    get_bilibili_stream_data,
    get_xhs_stream_url,
    get_bigo_stream_url,
    get_blued_stream_url,
    get_afreecatv_stream_data,
    get_netease_stream_data,
    get_qiandurebo_stream_data,
    get_pandatv_stream_data,
    get_maoerfm_stream_url,
    get_winktv_stream_data,
    get_flextv_stream_data,
    get_looklive_stream_url,
    get_popkontv_stream_url,
    get_twitcasting_stream_url,
    get_baidu_stream_data,
    get_weibo_stream_data,
    get_kugou_stream_url,
    get_twitchtv_stream_data,
    get_liveme_stream_url,
    get_huajiao_stream_url,
    get_liuxing_stream_url,
    get_showroom_stream_data,
    get_acfun_stream_data,
    get_huya_app_stream_url,
    get_shiguang_stream_url,
    get_yingke_stream_url,
    get_netease_stream_url,
    get_stream_url
)

translator_vpn = GoogleTranslator(source='auto', target='en')
translator = Translator(to_lang="en", from_lang="zh")


class UrllibExecutor:
    def __init__(self, port_info):
        self.real_url = port_info.get("record_url")
        self.flv_url = port_info.get("flv_url")

    def execute(self, save_file_path):
        if self.flv_url:
            _filepath, _ = urllib.request.urlretrieve(self.real_url, save_file_path)
        else:
            raise Exception('该直播无flv直播流，请切换视频保存类型')


class FFmpegExecutor:
    def __init__(self, config_manager, record_url, real_url, proxy_address):
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
            if pt_host in record_url:
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
            "-i", real_url,
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

    def get_ts_video_split_command(self, segment_format, save_path_name):
        return [
            "-c:v", "copy",
            "-c:a", 'copy',
            "-map", "0",
            "-f", "segment",
            "-segment_time", self.config_manager.split_time,
            "-segment_format", segment_format,
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


class RecordManager:
    def __init__(self, config_manager: ConfigManager):
        self.rstr = r"[\/\\\:\*\?\"\<\>\|&.。,， ]"
        self.monitoring = 0
        self.start_display_time = datetime.datetime.now()
        self.max_request = config_manager.max_request
        self.config_manager = config_manager
        self.warning_count = 0
        self.recording = set()
        self.recording_time_list = {}
        self.running_list = []
        self.first_start = True
        self.record_threads_pool = locals()
        self.semaphore = threading.Semaphore(self.max_request)
        self.retry = 0  # only used for red book live
        self.danmu_fetcher = DanmuFetcherHelper(self.config_manager)

    def display_info(self):
        time.sleep(5)
        while True:
            try:
                time.sleep(60)
                if os.name == 'nt':
                    os.system("cls")
                elif os.name == 'posix':
                    os.system("clear")
                logger.info("-" * 60)
                format_now_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                logger.info(f"当前时间: {format_now_time}")
                logger.info(f"\r共监测{self.monitoring}个直播中")
                logger.info(f"同一时间访问网络的线程数: {self.max_request}")
                if len(self.config_manager.video_save_path) > 0:
                    if not os.path.exists(self.config_manager.video_save_path):
                        logger.info("配置文件里,直播保存路径并不存在,请重新输入一个正确的路径.或留空表示当前目录,按回车退出")
                        logger.info("程序结束")
                        sys.exit(0)

                logger.info(f"是否开启代理录制: {'是' if self.config_manager.use_proxy else '否'}")
                if self.config_manager.split_video_by_time:
                    logger.info(f"录制分段开启: {self.config_manager.split_time}秒")
                logger.info(f"是否生成时间文件: {'是' if self.config_manager.create_time_file else '否'}")
                logger.info(f"录制视频质量为: {self.config_manager.video_record_quality}")
                logger.info(f"录制视频格式为: {self.config_manager.video_save_type}")
                logger.info(f"目前瞬时错误数为: {self.warning_count}")

                if len(self.recording) == 0:
                    time.sleep(5)
                    logger.info(f"\r没有正在录制的直播 {format_now_time[-8:]}")
                    continue
                else:
                    now_time = datetime.datetime.now()
                    if len(self.recording) > 0:
                        logger.info(">" * 60)
                        no_repeat_recording = list(set(self.recording))
                        logger.info(f"正在录制{len(no_repeat_recording)}个直播: ")
                        for recording_live in no_repeat_recording:
                            rt, qa = self.recording_time_list[recording_live]
                            have_record_time = now_time - rt
                            logger.info(f"{recording_live}[{qa}] 正在录制中 " + str(have_record_time).split('.')[0])
                        logger.info(">" * 60)
                    else:
                        self.start_display_time = now_time
                    logger.info("-" * 60)
            except Exception as e:
                logger.error(f"错误信息: {e} 发生错误的行数: {e.__traceback__.tb_lineno}")

    def change_max_connect(self):
        preset = self.max_request
        start_time = time.time()

        while True:
            time.sleep(5)
            if 10 <= self.warning_count <= 20:
                if preset > 5:
                    self.max_request = 5
                else:
                    self.max_request //= 2
                    if self.max_request > 0:
                        self.max_request = preset
                    else:
                        preset = 1

                logger.info("同一时间访问网络的线程数动态改为", self.max_request)
                self.warning_count = 0
                time.sleep(5)

            elif 20 < self.warning_count:
                self.max_request = 1
                logger.info("同一时间访问网络的线程数动态改为", self.max_request)
                self.warning_count = 0
                time.sleep(10)

            elif self.warning_count < 10 and time.time() - start_time > 60:
                self.max_request = preset
                self.warning_count = 0
                start_time = time.time()
                logger.info("同一时间访问网络的线程数动态改为", self.max_request)
            self.semaphore = threading.Semaphore(self.max_request)

    def create_ass_file(self, anchor_name, filename_short):
        ass_filename = filename_short
        index_time = -1
        finish = 0
        today = datetime.datetime.now()
        re_datatime = today.strftime('%Y-%m-%d %H:%M:%S')

        while True:
            index_time += 1
            txt = str(index_time) + "\n" + transform_int_to_time(index_time) + ',000 --> ' + transform_int_to_time(
                index_time + 1) + ',000' + "\n" + str(re_datatime) + "\n"

            with open(ass_filename + ".ass", 'a', encoding='utf8') as f:
                f.write(txt)

            if anchor_name not in self.recording:
                finish += 1
                offset = datetime.timedelta(seconds=1)
                re_datatime = (today + offset).strftime('%Y-%m-%d %H:%M:%S')
                today = today + offset
            else:
                time.sleep(1)
                today = datetime.datetime.now()
                re_datatime = today.strftime('%Y-%m-%d %H:%M:%S')

            if finish > 15:
                break

    def start_record_threads(self):
        if len(self.config_manager.url_tuples_list) > 0:
            for url_tuple in self.config_manager.url_tuples_list:
                self.monitoring = len(self.running_list)
                if url_tuple[1] in self.config_manager.not_record_list:
                    continue

                if url_tuple[1] not in self.running_list:
                    if not self.first_start:
                        logger.info(f"\r新增链接: {url_tuple[1]}")
                    self.monitoring += 1
                    self.record_threads_pool['thread-' + str(self.monitoring)] = threading.Thread(
                        target=self._start_record,
                        args=[url_tuple, self.monitoring]
                    )
                    self.record_threads_pool['thread-' + str(self.monitoring)].daemon = True
                    self.record_threads_pool['thread-' + str(self.monitoring)].start()
                    self.running_list.append(url_tuple[1])
                    time.sleep(self.config_manager.local_delay_default)
        self.config_manager.url_tuples_list.clear()
        self.first_start = False

    def _start_record(self, url_data: tuple, count_variable: int = -1):
        # msg_push_helper = MsgPushHelper()
        thread_name = threading.current_thread().name
        while True:
            try:
                record_finished = False
                count_time = time.time()
                self.retry = 0  # only used for red book live
                record_quality, record_url, anchor_name = url_data
                proxy_address = self.config_manager.get_proxy_address(record_url)

                if proxy_address:
                    logger.info(f'\r[{thread_name}]代理地址:{proxy_address}')
                logger.info(f"\r[{thread_name}]运行新线程,传入地址 {record_url}")

                while True:
                    try:
                        port_info = self._handle_platform(record_url, proxy_address, record_quality)
                        if not port_info:
                            return

                        anchor_name = port_info.get("anchor_name", '')

                        if not anchor_name:
                            logger.error(f'[{thread_name}] 网址内容获取失败,进行重试中...获取失败的地址是:{url_data}')
                            self.warning_count += 1
                        else:
                            anchor_name = re.sub(self.rstr, "_", anchor_name)  # 过滤不能作为文件名的字符，替换为下划线
                            threading.current_thread().name = f'{thread_name}-{anchor_name}'
                            logger.info(f"\r线程名更新: {thread_name} -> {threading.current_thread().name}")
                            thread_name = threading.current_thread().name
                            record_name = thread_name

                            if anchor_name in self.recording:
                                logger.info(f"[{thread_name}]新增的地址: {anchor_name} 已经存在,本条线程将会退出")
                                return

                            # msg_push_helper.push_live_msg(self.config_manager, port_info, record_name)

                            if port_info['is_live'] is False:
                                # 未开播
                                continue
                            else:
                                # 开播
                                if self.config_manager.disable_record:  # 只发消息不录制
                                    time.sleep(self.config_manager.push_check_seconds)
                                    continue

                                record_finished = self._start_record_inner(
                                    record_quality,
                                    record_url,
                                    port_info,
                                    anchor_name,
                                    proxy_address,
                                    record_name
                                )
                                count_time = time.time()

                    except Exception as e:
                        logger.error(f"[{thread_name}]错误信息: {e} 发生错误的行数: {e.__traceback__.tb_lineno}")
                        self.warning_count += 1

                    # 生成-5到5的随机数，加上delay_default，确保不小于0
                    num = max(0, random.randint(-5, 5) + self.config_manager.delay_default)

                    # 如果出错太多,延迟加60秒
                    if self.warning_count > 20:
                        num += 60
                        logger.info(f"[{thread_name}]瞬时错误太多,延迟加60秒")

                    # 检查录制是否结束，调整等待时间
                    x = 30 if record_finished and (time.time() - count_time) < 60 else num
                    record_finished = False

                    # 等待中
                    while x > 0:
                        if self.config_manager.loop_time:
                            logger.info(f'\r[{thread_name}]{anchor_name}循环等待{x}秒 ', end="")
                        time.sleep(1)
                        x -= 1

                    if self.config_manager.loop_time:
                        logger.info(f'\r[{thread_name}]检测直播间中...', end="")

            except Exception as e:
                logger.error(f"[{thread_name}]错误信息: {e} 发生错误的行数: {e.__traceback__.tb_lineno}")
                self.warning_count += 1
                time.sleep(2)

    def _handle_platform(self, record_url, proxy_address, record_quality) -> Dict[str, Any]:
        platform_functions = {
            'douyin.com/': ('DouyinLive', self._get_douyin_live_info),
            'tiktok.com/': ('TikTokLive', self._get_tiktok_live_info),
            'live.kuaishou.com/': ('KuaishouLive', self._get_kuai_live_info),
            'huya.com/': ('HuyaLive', self._get_huya_live_info),
            'douyu.com/': ('DouyuLive', self._get_douyu_live_info),
            'yy.com/': ('YYLive', self._get_yy_live_info),
            'live.bilibili.com/': ('BilibiliLive', self._get_bilibili_live_info),
            'redelight.cn/': ('RedbookLive', self._get_redbook_live_info),
            'xiaohongshu.com/': ('RedbookLive', self._get_redbook_live_info),
            'xhslink.com/': ('RedbookLive', self._get_redbook_live_info),
            'bigo.tv/': ('BigoLive', self._get_bigo_live_info),
            'blued.cn/': ('BluedLive', self._get_blued_live_info),
            'afreecatv.com/': ('AfreecaTV', self._start_record_afreecatv),
            'cc.163.com/': ('WangyiCCLive', self._get_wangyi_live_info),
            'qiandurebo.com/': ('QianduLive', self._get_qiandu_live_info),
            'pandalive.co.kr/': ('PandaTV', self._get_panda_live_info),
            'fm.missevan.com/': ('MaoerFMLive', self._get_maoerfm_live_info),
            'winktv.co.kr/': ('WinkTV', self._get_winktv_live_info),
            'flextv.co.kr/': ('FlexTV', self._get_flextv_live_info),
            'look.163.com/': ('LookLive', self._get_look_live_info),
            'popkontv.com/': ('PopkonTV', self._get_popkon_live_info),
            'twitcasting.tv/': ('TwitCasting', self._get_twitcasting_live_info),
            'live.baidu.com/': ('BaiduLive', self._get_baidu_live_info),
            'weibo.com/': ('WeiboLive', self._get_weibo_live_info),
            'kugou.com/': ('KugouLive', self._get_kugou_live_info),
            'twitch.tv/': ('TwitchTV', self._get_twitch_live_info),
            'liveme.com/': ('LiveMe', self._get_liveme_live_info),
            'huajiao.com/': ('HuajiaoLive', self._get_huajiao_live_info),
            '7u66.com/': ('LiuxingLive', self._get_liuxing_live_info),
            'showroom-live.com/': ('ShowRoom', self._get_showroom_live_info),
            'acfun.cn/': ('Acfun', self._get_acfun_live_info),
            'rengzu.com/': ('ShiguangLive', self._get_shiguang_live_info),
            'inke.cn/': ('YingkeLive', self._get_inke_live_info),
        }

        for key, (platform, func) in platform_functions.items():
            if key in record_url:
                port_info = func(record_url, proxy_address, record_quality)
                port_info['platform'] = platform
                return port_info

        logger.error(f'{record_url} 未知直播地址')
        return {}

    def _get_douyin_live_info(self, record_url: str, proxy_address: str, record_quality: str) -> Dict[str, Any]:
        with self.semaphore:
            if 'live.douyin.com' in record_url:
                json_data = get_douyin_stream_data(
                    url=record_url,
                    proxy_addr=proxy_address,
                    cookies=self.config_manager.dy_cookie)
            else:
                json_data = get_douyin_app_stream_data(
                    url=record_url,
                    proxy_addr=proxy_address,
                    cookies=self.config_manager.dy_cookie)
            port_info = get_douyin_stream_url(json_data, record_quality)
            port_info['rid'] = record_url.split('/')[-1]
            return port_info

    def _get_tiktok_live_info(self, record_url: str, proxy_address: str, record_quality: str) -> Dict[str, Any]:
        with self.semaphore:
            if self.config_manager.global_proxy or proxy_address:
                json_data = get_tiktok_stream_data(
                    url=record_url,
                    proxy_addr=proxy_address,
                    cookies=self.config_manager.tiktok_cookie)
                return get_tiktok_stream_url(json_data, record_quality)
            else:
                logger.error(f"错误信息: 网络异常，请检查网络是否能正常访问TikTok平台")
                return {}

    def _get_kuai_live_info(self, record_url: str, proxy_address: str, record_quality: str) -> Dict[str, Any]:
        with self.semaphore:
            json_data = get_kuaishou_stream_data(
                url=record_url,
                proxy_addr=proxy_address,
                cookies=self.config_manager.ks_cookie)
            port_info = get_kuaishou_stream_url(json_data, record_quality)
            port_info['rid'] = record_url.split('/')[-1]
            return port_info

    def _get_huya_live_info(self, record_url: str, proxy_address: str, record_quality: str) -> Dict[str, Any]:
        with self.semaphore:
            if record_quality not in ['原画', '蓝光', '超清']:
                json_data = get_huya_stream_data(
                    url=record_url,
                    proxy_addr=proxy_address,
                    cookies=self.config_manager.hy_cookie)
                return get_huya_stream_url(json_data, record_quality)
            else:
                return get_huya_app_stream_url(
                    url=record_url,
                    proxy_addr=proxy_address,
                    cookies=self.config_manager.hy_cookie
                )

    def _get_douyu_live_info(self, record_url: str, proxy_address: str, record_quality: str) -> Dict[str, Any]:
        with self.semaphore:
            json_data = get_douyu_info_data(
                url=record_url,
                proxy_addr=proxy_address,
                cookies=self.config_manager.douyu_cookie
            )
            return get_douyu_stream_url(
                json_data,
                proxy_address=proxy_address,
                cookies=self.config_manager.douyu_cookie,
                video_quality=record_quality
            )

    def _get_yy_live_info(self, record_url: str, proxy_address: str, record_quality: str) -> Dict[str, Any]:
        with self.semaphore:
            json_data = get_yy_stream_data(
                url=record_url,
                proxy_addr=proxy_address,
                cookies=self.config_manager.yy_cookie
            )
            return get_yy_stream_url(json_data)

    def _get_bilibili_live_info(self, record_url: str, proxy_address: str, record_quality: str) -> Dict[str, Any]:
        with self.semaphore:
            json_data = get_bilibili_stream_data(
                url=record_url,
                proxy_addr=proxy_address,
                cookies=self.config_manager.bili_cookie
            )
            return get_bilibili_stream_url(json_data, record_quality)

    def _get_redbook_live_info(self, record_url: str, proxy_address: str, record_quality: str) -> Dict[str, Any]:
        if self.retry > 0:
            delete_line(self.config_manager.url_config_file, record_url)
            if record_url in self.running_list:
                self.running_list.remove(record_url)
                self.config_manager.not_record_list.append(record_url)
                logger.info(f'{record_url} 小红书直播已结束，停止录制')
                return {}
        with self.semaphore:
            self.retry += 1
            return get_xhs_stream_url(
                url=record_url,
                proxy_addr=proxy_address,
                cookies=self.config_manager.xhs_cookie
            )

    def _get_bigo_live_info(self, record_url: str, proxy_address: str, record_quality: str) -> Dict[str, Any]:
        with self.semaphore:
            return get_bigo_stream_url(
                record_url,
                proxy_addr=proxy_address,
                cookies=self.config_manager.bigo_cookie
            )

    def _get_blued_live_info(self, record_url: str, proxy_address: str, record_quality: str) -> Dict[str, Any]:
        with self.semaphore:
            return get_blued_stream_url(
                record_url,
                proxy_addr=proxy_address,
                cookies=self.config_manager.blued_cookie
            )

    def _start_record_afreecatv(self, record_url: str, proxy_address: str, record_quality: str) -> Dict[str, Any]:
        with self.semaphore:
            if self.config_manager.global_proxy or proxy_address:
                json_data = get_afreecatv_stream_data(
                    url=record_url, proxy_addr=proxy_address,
                    cookies=self.config_manager.afreecatv_cookie,
                    username=self.config_manager.afreecatv_username,
                    password=self.config_manager.afreecatv_password
                )
                return get_stream_url(json_data, record_quality, spec=True)
            else:
                logger.error(f"错误信息: 网络异常，请检查本网络是否能正常访问AfreecaTV平台")
                return {}

    def _get_wangyi_live_info(self, record_url: str, proxy_address: str, record_quality: str) -> Dict[str, Any]:
        with self.semaphore:
            json_data = get_netease_stream_data(
                url=record_url,
                cookies=self.config_manager.netease_cookie
            )
            return get_netease_stream_url(json_data, record_quality)

    def _get_qiandu_live_info(self, record_url: str, proxy_address: str, record_quality: str) -> Dict[str, Any]:
        with self.semaphore:
            return get_qiandurebo_stream_data(
                url=record_url,
                proxy_addr=proxy_address,
                cookies=self.config_manager.qiandurebo_cookie
            )

    def _get_panda_live_info(self, record_url: str, proxy_address: str, record_quality: str) -> Dict[str, Any]:
        with self.semaphore:
            if self.config_manager.global_proxy or proxy_address:
                json_data = get_pandatv_stream_data(
                    url=record_url,
                    proxy_addr=proxy_address,
                    cookies=self.config_manager.pandatv_cookie
                )
                return get_stream_url(json_data, record_quality, spec=True)
            else:
                logger.error(f"错误信息: 网络异常，请检查本网络是否能正常访问PandaTV直播平台")
                return {}

    def _get_maoerfm_live_info(self, record_url: str, proxy_address: str, record_quality: str) -> Dict[str, Any]:
        with self.semaphore:
            return get_maoerfm_stream_url(
                url=record_url,
                proxy_addr=proxy_address,
                cookies=self.config_manager.maoerfm_cookie
            )

    def _get_winktv_live_info(self, record_url: str, proxy_address: str, record_quality: str) -> Dict[str, Any]:
        with self.semaphore:
            if self.config_manager.global_proxy or proxy_address:
                json_data = get_winktv_stream_data(
                    url=record_url,
                    proxy_addr=proxy_address,
                    cookies=self.config_manager.winktv_cookie)
                return get_stream_url(json_data, record_quality, spec=True)
            else:
                logger.error(f"错误信息: 网络异常，请检查本网络是否能正常访问WinkTV直播平台")
                return {}

    def _get_flextv_live_info(self, record_url: str, proxy_address: str, record_quality: str) -> Dict[str, Any]:
        with self.semaphore:
            if self.config_manager.global_proxy or proxy_address:
                json_data = get_flextv_stream_data(
                    url=record_url,
                    proxy_addr=proxy_address,
                    cookies=self.config_manager.flextv_cookie,
                    username=self.config_manager.flextv_username,
                    password=self.config_manager.flextv_password
                )
                return get_stream_url(json_data, record_quality, spec=True)
            else:
                logger.error(f"错误信息: 网络异常，请检查本网络是否能正常访问FlexTV直播平台")
                return {}

    def _get_look_live_info(self, record_url: str, proxy_address: str, record_quality: str) -> Dict[str, Any]:
        with self.semaphore:
            return get_looklive_stream_url(
                url=record_url,
                proxy_addr=proxy_address,
                cookies=self.config_manager.look_cookie
            )

    def _get_popkon_live_info(self, record_url: str, proxy_address: str, record_quality: str) -> Dict[str, Any]:
        with self.semaphore:
            if self.config_manager.global_proxy or proxy_address:
                return get_popkontv_stream_url(
                    url=record_url,
                    proxy_addr=proxy_address,
                    access_token=self.config_manager.popkontv_access_token,
                    username=self.config_manager.popkontv_username,
                    password=self.config_manager.popkontv_password,
                    partner_code=self.config_manager.popkontv_partner_code
                )
            else:
                logger.error(f"错误信息: 网络异常，请检查本网络是否能正常访问PopkonTV直播平台")
                return {}

    def _get_twitcasting_live_info(self, record_url: str, proxy_address: str, record_quality: str) -> Dict[str, Any]:
        with self.semaphore:
            return get_twitcasting_stream_url(
                url=record_url,
                proxy_addr=proxy_address,
                cookies=self.config_manager.twitcasting_cookie,
                account_type=self.config_manager.twitcasting_account_type,
                username=self.config_manager.twitcasting_username,
                password=self.config_manager.twitcasting_password
            )

    def _get_baidu_live_info(self, record_url: str, proxy_address: str, record_quality: str) -> Dict[str, Any]:
        with self.semaphore:
            json_data = get_baidu_stream_data(
                url=record_url,
                proxy_addr=proxy_address,
                cookies=self.config_manager.baidu_cookie)
            return get_stream_url(json_data, record_quality)

    def _get_weibo_live_info(self, record_url: str, proxy_address: str, record_quality: str) -> Dict[str, Any]:
        with self.semaphore:
            json_data = get_weibo_stream_data(
                url=record_url,
                proxy_addr=proxy_address,
                cookies=self.config_manager.weibo_cookie
            )
            return get_stream_url(json_data, record_quality, extra_key='m3u8_url')

    def _get_kugou_live_info(self, record_url: str, proxy_address: str, record_quality: str) -> Dict[str, Any]:
        with self.semaphore:
            return get_kugou_stream_url(
                url=record_url,
                proxy_addr=proxy_address,
                cookies=self.config_manager.kugou_cookie
            )

    def _get_twitch_live_info(self, record_url: str, proxy_address: str, record_quality: str) -> Dict[str, Any]:
        with self.semaphore:
            if self.config_manager.global_proxy or proxy_address:
                json_data = get_twitchtv_stream_data(
                    url=record_url,
                    proxy_addr=proxy_address,
                    cookies=self.config_manager.twitch_cookie
                )
                return get_stream_url(json_data, record_quality, spec=True)
            else:
                logger.error(f"错误信息: 网络异常，请检查本网络是否能正常访问TwitchTV直播平台")
                return {}

    def _get_liveme_live_info(self, record_url: str, proxy_address: str, record_quality: str) -> Dict[str, Any]:
        with self.semaphore:
            return get_liveme_stream_url(
                url=record_url,
                proxy_addr=proxy_address,
                cookies=self.config_manager.liveme_cookie
            )

    def _get_huajiao_live_info(self, record_url: str, proxy_address: str, record_quality: str) -> Dict[str, Any]:
        with self.semaphore:
            return get_huajiao_stream_url(
                url=record_url,
                proxy_addr=proxy_address,
                cookies=self.config_manager.huajiao_cookie
            )

    def _get_liuxing_live_info(self, record_url: str, proxy_address: str, record_quality: str) -> Dict[str, Any]:
        with self.semaphore:
            return get_liuxing_stream_url(
                url=record_url,
                proxy_addr=proxy_address,
                cookies=self.config_manager.liuxing_cookie
            )

    def _get_showroom_live_info(self, record_url: str, proxy_address: str, record_quality: str) -> Dict[str, Any]:
        with self.semaphore:
            json_data = get_showroom_stream_data(
                url=record_url, proxy_addr=proxy_address, cookies=self.config_manager.showroom_cookie
            )
            return get_stream_url(json_data, record_quality, spec=True)

    def _get_acfun_live_info(self, record_url: str, proxy_address: str, record_quality: str) -> Dict[str, Any]:
        with self.semaphore:
            json_data = get_acfun_stream_data(
                url=record_url, proxy_addr=proxy_address, cookies=self.config_manager.acfun_cookie
            )
            return get_stream_url(json_data, record_quality, url_type='flv', extra_key='url')

    def _get_shiguang_live_info(self, record_url: str, proxy_address: str, record_quality: str) -> Dict[str, Any]:
        with self.semaphore:
            return get_shiguang_stream_url(
                url=record_url,
                proxy_addr=proxy_address,
                cookies=self.config_manager.shiguang_cookie
            )

    def _get_inke_live_info(self, record_url: str, proxy_address: str, record_quality: str) -> Dict[str, Any]:
        with self.semaphore:
            return get_yingke_stream_url(
                url=record_url,
                proxy_addr=proxy_address,
                cookies=self.config_manager.yingke_cookie
            )

    def _start_record_inner(self, record_quality, record_url, port_info, anchor_name, proxy_address, record_name):
        real_url = port_info['record_url']
        platform = port_info['platform']
        thread_name = threading.current_thread().name
        translated_platform = (translator_vpn if self.config_manager.use_vpn else translator).translate(platform)
        translated_platform = translated_platform.replace(" ", "")

        # anchor_name = (translator_vpn if self.config_manager.use_vpn else translator).translate(anchor_name)
        # anchor_name = anchor_name.replace(" ", "")

        video_save_path = self.config_manager.video_save_path.rstrip("/\\")  # 去除末尾的分隔符
        base_path = video_save_path if video_save_path else self.config_manager.default_path
        full_path = f'{base_path}/{translated_platform}'.replace("\\", "/")

        if len(real_url) > 0:
            now = datetime.datetime.today().strftime("%Y-%m-%d_%H-%M-%S")
            today = datetime.datetime.today().strftime("%Y-%m-%d")

            try:
                if self.config_manager.folder_by_author:
                    full_path = f'{full_path}/{anchor_name}/{today}'
                if not os.path.exists(full_path):
                    os.makedirs(full_path)
            except Exception as e:
                logger.error(f"[{thread_name}]错误信息: {e} 发生错误的行数: {e.__traceback__.tb_lineno}")

            if not os.path.exists(full_path):
                logger.error(f"[{thread_name}]错误信息: 保存路径不存在,不能生成录制.请避免把本程序放在c盘,桌面,下载文件夹,qq默认传输目录.请重新检查设置")

            ffmpeg_executor = FFmpegExecutor(self.config_manager, record_url, real_url, proxy_address)
            urllib_executor = UrllibExecutor(port_info)

            self.recording.add(record_name)
            start_record_time = datetime.datetime.now()
            self.recording_time_list[record_name] = [start_record_time, record_quality]
            if self.config_manager.show_url:
                re_plat = ['WinkTV', 'PandaTV', 'ShowRoom']
                if platform in re_plat:
                    logger.info(f"[{thread_name}]{platform} | {anchor_name} | 直播源地址: {port_info['m3u8_url']}")
                else:
                    logger.info(f"[{thread_name}]{platform} | {anchor_name} | 直播源地址: {port_info['record_url']}")

            video_save_type_functions = {
                'FLV': self._save_flv_video_file,
                'MKV': self._save_mkv_video_file,
                'MKV音频': self._save_mkv_audio_file,
                'MP4': self._save_mp4_video_file,
                'TS': self._save_ts_video_file,
                'TS音频': self._save_ts_audio_file,
            }

            save_danmu_path_name = f"{full_path}/{anchor_name}_{now}_danmu.txt"
            room_id = port_info.get('rid', None)
            threading.Thread(
                target=self.danmu_fetcher.fetch_danmu,
                args=(platform, room_id, save_danmu_path_name),
                daemon=True,
                name=f"{thread_name}-danmu-fetcher"
            ).start()

            record_result = video_save_type_functions.get(self.config_manager.video_save_type)(
                anchor_name, now, full_path, urllib_executor, ffmpeg_executor
            )

            if record_name in self.recording:
                self.recording.remove(record_name)

            if record_result:
                logger.info(f"\n[{thread_name}]{anchor_name} {time.strftime('%Y-%m-%d %H:%M:%S')} 直播录制完成\n")
            else:
                logger.info(f"\n[{thread_name}]{anchor_name} {time.strftime('%Y-%m-%d %H:%M:%S')} 直播录制出错,请检查网络\n")
            return record_result

    def _create_time_file(self, anchor_name, filename_short):
        if self.config_manager.create_time_file:
            self.record_threads_pool[str(filename_short)] = threading.Thread(
                target=self.create_ass_file,
                args=(anchor_name, filename_short)
            )
            self.record_threads_pool[str(filename_short)].daemon = True
            self.record_threads_pool[str(filename_short)].start()

    def _save_flv_video_file(self, anchor_name, now, full_path, urllib_executor: UrllibExecutor, ffmpeg_executor: FFmpegExecutor):
        filename = anchor_name + '_' + now + '.flv'
        rec_info = f"\r{anchor_name} 录制视频中: {full_path}"
        thread_name = threading.current_thread().name
        logger.info(f'[{thread_name}]{rec_info}/{filename}')

        filename_short = full_path + '/' + anchor_name + '_' + now
        self._create_time_file(anchor_name, filename_short)

        try:
            urllib_executor.execute(full_path + '/' + filename)
            return True
        except Exception as e:
            logger.error(f"[{thread_name}]错误信息: {e} 发生错误的行数: {e.__traceback__.tb_lineno}")
            self.warning_count += 1
            return False

    def _save_mkv_video_file(self, anchor_name, now, full_path, urllib_executor: UrllibExecutor, ffmpeg_executor: FFmpegExecutor):
        filename = anchor_name + '_' + now + ".mkv"
        rec_info = f"\r{anchor_name} 录制视频中: {full_path}"
        thread_name = threading.current_thread().name
        logger.info(f'[{thread_name}]{rec_info}/{filename}')

        save_file_path = full_path + '/' + filename
        filename_short = full_path + '/' + anchor_name + '_' + now

        try:
            if self.config_manager.split_video_by_time:
                now = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
                save_file_path = f"{full_path}/{anchor_name}_{now}_%03d.mkv"
                command = ffmpeg_executor.get_mkv_split_video_command(save_file_path)
            else:
                self._create_time_file(anchor_name, filename_short)
                command = ffmpeg_executor.get_mkv_video_command(save_file_path)
            ffmpeg_executor.execute(command)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"[{thread_name}]错误信息: {e} 发生错误的行数: {e.__traceback__.tb_lineno}")
            self.warning_count += 1
            return False

    def _save_mp4_video_file(self, anchor_name, now, full_path, urllib_executor: UrllibExecutor, ffmpeg_executor: FFmpegExecutor):
        filename = anchor_name + '_' + now + ".mp4"
        rec_info = f"\r{anchor_name} 录制视频中: {full_path}"
        thread_name = threading.current_thread().name
        logger.info(f'[{thread_name}]{rec_info}/{filename}')

        save_file_path = full_path + '/' + filename
        filename_short = full_path + '/' + anchor_name + '_' + now

        try:
            if self.config_manager.split_video_by_time:
                now = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
                save_file_path = f"{full_path}/{anchor_name}_{now}_%03d.mp4"
                command = ffmpeg_executor.get_mp4_split_video_command(save_file_path)
            else:
                self._create_time_file(anchor_name, filename_short)
                command = ffmpeg_executor.get_mp4_video_command(save_file_path)
            ffmpeg_executor.execute(command)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"[{thread_name}]错误信息: {e} 发生错误的行数: {e.__traceback__.tb_lineno}")
            self.warning_count += 1
            return False

    def _save_mkv_audio_file(self, anchor_name, now, full_path, urllib_executor: UrllibExecutor, ffmpeg_executor: FFmpegExecutor):
        thread_name = threading.current_thread().name
        try:
            if self.config_manager.split_video_by_time:
                now = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
                filename = anchor_name + '_' + now + ".mkv"
                rec_info = f"\r{anchor_name} 录制视频中: {full_path}"
                logger.info(f'[{thread_name}]{rec_info}/{filename}')

                if self.config_manager.ts_to_mp3:
                    save_path_name = f"{full_path}/{anchor_name}_{now}_%03d.mp3"
                else:
                    save_path_name = f"{full_path}/{anchor_name}_{now}_%03d.mkv"

                command = ffmpeg_executor.get_mkv_split_audio_command(save_path_name)
                ffmpeg_executor.execute(command)
                record_finished = True
            else:
                filename = anchor_name + '_' + now + ".mkv"
                rec_info = f"\r{anchor_name} 录制视频中: {full_path}"
                logger.info(f'[{thread_name}]{rec_info}/{filename}')

                save_file_path = full_path + '/' + filename

                command = ffmpeg_executor.get_mkv_audio_command(save_file_path)
                ffmpeg_executor.execute(command)
                record_finished = True

                if self.config_manager.ts_to_m4a:
                    threading.Thread(target=self.converts_m4a, args=(save_file_path,)).start()
            return record_finished
        except subprocess.CalledProcessError as e:
            logger.error(f"[{thread_name}]错误信息: {e} 发生错误的行数: {e.__traceback__.tb_lineno}")
            self.warning_count += 1
            return False

    def _save_ts_audio_file(self, anchor_name, now, full_path, urllib_executor: UrllibExecutor, ffmpeg_executor: FFmpegExecutor):
        thread_name = threading.current_thread().name
        try:
            if self.config_manager.split_video_by_time:
                now = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
                filename = anchor_name + '_' + now + ".ts"
                rec_info = f"\r{anchor_name} 录制视频中: {full_path}"
                logger.info(f'[{thread_name}]{rec_info}/{filename}')

                if self.config_manager.ts_to_mp3:
                    save_path_name = f"{full_path}/{anchor_name}_{now}_%03d.mp3"
                else:
                    save_path_name = f"{full_path}/{anchor_name}_{now}_%03d.ts"

                command = ffmpeg_executor.get_ts_audio_split_command(save_path_name)

                ffmpeg_executor.execute(command)
                record_finished = True
            else:
                filename = anchor_name + '_' + now + ".ts"
                rec_info = f"\r{anchor_name} 录制视频中: {full_path}"
                logger.info(f'[{thread_name}]{rec_info}/{filename}')
                save_file_path = full_path + '/' + filename

                command = ffmpeg_executor.get_ts_audio_command(save_file_path)
                ffmpeg_executor.execute(command)
                record_finished = True

                if self.config_manager.ts_to_m4a:
                    threading.Thread(target=self.converts_m4a, args=(save_file_path,)).start()
            return record_finished
        except subprocess.CalledProcessError as e:
            logger.error(f"[{thread_name}]错误信息: {e} 发生错误的行数: {e.__traceback__.tb_lineno}")
            self.warning_count += 1
            return False

    def _save_ts_video_file(self, anchor_name, now, full_path, urllib_executor: UrllibExecutor, ffmpeg_executor: FFmpegExecutor):
        thread_name = threading.current_thread().name
        if self.config_manager.split_video_by_time:
            now = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
            filename = anchor_name + '_' + now + ".ts"
            rec_info = f"\r{anchor_name} 录制视频中: {full_path}"
            logger.info(f'[{thread_name}]{rec_info}/{filename}')

            try:
                if self.config_manager.ts_to_mp4:
                    save_path_name = f"{full_path}/{anchor_name}_{now}_%03d.mp4"
                    segment_format = 'mp4'
                else:
                    save_path_name = f"{full_path}/{anchor_name}_{now}_%03d.ts"
                    segment_format = 'mpegts'

                command = ffmpeg_executor.get_ts_video_split_command(segment_format, save_path_name)
                ffmpeg_executor.execute(command)
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"[{thread_name}]错误信息: {e} 发生错误的行数: {e.__traceback__.tb_lineno}")
                self.warning_count += 1
                return False

        else:
            filename = anchor_name + '_' + now + ".ts"
            rec_info = f"\r{anchor_name} 录制视频中: {full_path}"
            logger.info(f'[{thread_name}]{rec_info}/{filename}')
            save_file_path = full_path + '/' + filename
            filename_short = full_path + '/' + anchor_name + '_' + now

            self._create_time_file(anchor_name, filename_short)

            try:
                command = ffmpeg_executor.get_ts_video_command(save_file_path)
                ffmpeg_executor.execute(command)

                if self.config_manager.ts_to_mp4:
                    threading.Thread(target=self.converts_mp4, args=(save_file_path,)).start()
                if self.config_manager.ts_to_m4a:
                    threading.Thread(target=self.converts_m4a, args=(save_file_path,)).start()
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"[{thread_name}]错误信息: {e} 发生错误的行数: {e.__traceback__.tb_lineno}")
                self.warning_count += 1
                return False

    def converts_mp4(self, address: str):
        if self.config_manager.ts_to_mp4:
            _output = subprocess.check_output([
                "ffmpeg", "-i", address,
                "-c:v", "copy",
                "-c:a", "copy",
                "-f", "mp4", address.split('.')[0] + ".mp4",
            ], stderr=subprocess.STDOUT)
            if self.config_manager.delete_origin_file:
                time.sleep(1)
                if os.path.exists(address):
                    os.remove(address)

    def converts_m4a(self, address: str):
        if self.config_manager.ts_to_m4a:
            _output = subprocess.check_output([
                "ffmpeg", "-i", address,
                "-n", "-vn",
                "-c:a", "aac", "-bsf:a", "aac_adtstoasc", "-ab", "320k",
                address.split('.')[0] + ".m4a",
            ], stderr=subprocess.STDOUT)
            if self.config_manager.delete_origin_file:
                time.sleep(1)
                if os.path.exists(address):
                    os.remove(address)

