import os
import subprocess
import time
from typing import Any, Optional

from dao.model import LiveRecord
from dao.repository import save_live_file

from common.task_manager import OnCompleteCallback
from live_platform.base.base_var import task_manager_var, config_manager_var, group_id_gen_var, recoding_var
from live_platform.base.live.base_crawler import AbstractLiveStreamFetcher, FFmpegExecutor, FLVRecoder
from live_platform.douyin.live.douyin_model import DouyinLivePortInfo
from common.logger import logger


class OnLiveStreamRecordFinished(OnCompleteCallback):
    def on_complete(self, task_name: str, task_result: Any, task_error: Optional[Exception]):
        record_result = task_result[0]
        port_info = task_result[1]
        file_name = task_result[2]
        recoding_var.get().remove(port_info.anchor_name)
        save_live_file(
            LiveRecord(
                anchor_name=port_info.anchor_name,
                platform=port_info.platform,
                category=port_info.category,
                live_date=port_info.live_date,
                live_url=port_info.live_url,
                live_slice=os.path.splitext(file_name)[0],
                live_danmu_file=file_name
            )
        )
        if record_result:
            logger.info(f"\n{port_info.anchor_name} {time.strftime('%Y-%m-%d %H:%M:%S')} 直播录制完成\n")
        else:
            logger.info(f"\n{port_info.anchor_name} {time.strftime('%Y-%m-%d %H:%M:%S')} 直播录制出错,请检查网络\n")


class DouyinLiveLiveStreamFetcher(AbstractLiveStreamFetcher):
    def __init__(self):
        self.task_manager = task_manager_var.get()
        self.config_manager = config_manager_var.get()
        self.group_id_gen = group_id_gen_var.get()

    async def start_fetch(self, port_info: DouyinLivePortInfo, task_name: str = None):
        """
        start record
        """
        ffmpeg_executor = FFmpegExecutor(
            self.config_manager,
            port_info.live_url,
            port_info.record_url,
            self.config_manager.get_proxy_address(port_info.record_url)
        )
        flv_recoder = FLVRecoder(port_info)
        on_record_finished = OnLiveStreamRecordFinished()
        match self.config_manager.video_save_type:
            case 'FLV':
                self.task_manager.create_task(
                    task_name=task_name,
                    func=self._save_flv_video_file,
                    port_info=port_info,
                    flv_recoder=flv_recoder,
                    on_complete=on_record_finished,
                    task_group_id=self.group_id_gen.get_group_id()
                )
            case 'MKV':
                self.task_manager.create_task(
                    task_name=task_name,
                    func=self._save_mkv_video_file,
                    port_info=port_info,
                    ffmpeg_executor=ffmpeg_executor,
                    on_complete=on_record_finished,
                    task_group_id=self.group_id_gen.get_group_id()
                )
            case 'MKV音频':
                self.task_manager.create_task(
                    task_name=task_name,
                    func=self._save_mkv_audio_file,
                    port_info=port_info,
                    ffmpeg_executor=ffmpeg_executor,
                    on_complete=on_record_finished,
                    task_group_id=self.group_id_gen.get_group_id()
                )
            case 'MP4':
                self.task_manager.create_task(
                    task_name=task_name,
                    func=self._save_mp4_video_file,
                    port_info=port_info,
                    ffmpeg_executor=ffmpeg_executor,
                    on_complete=on_record_finished,
                    task_group_id=self.group_id_gen.get_group_id()
                )
            case 'TS':
                self.task_manager.create_task(
                    task_name=task_name,
                    func=self._save_ts_video_file,
                    port_info=port_info,
                    ffmpeg_executor=ffmpeg_executor,
                    on_complete=on_record_finished,
                    task_group_id=self.group_id_gen.get_group_id()
                )
            case 'TS音频':
                self.task_manager.create_task(
                    task_name=task_name,
                    func=self._save_ts_audio_file,
                    port_info=port_info,
                    ffmpeg_executor=ffmpeg_executor,
                    on_complete=on_record_finished,
                    task_group_id=self.group_id_gen.get_group_id()
                )

    def _save_flv_video_file(self, port_info, flv_recoder: FLVRecoder):
        anchor_name = port_info.anchor_name
        logger.info(f"\r{anchor_name} 录制flv视频中")
        filename = self._get_file_path(port_info, "flv")
        try:
            flv_recoder.execute(filename)
            return True, port_info, filename
        except Exception as e:
            logger.error(f"错误信息: {e} 发生错误的行数: {e.__traceback__.tb_lineno}")
            return False, port_info, filename

    def _save_mkv_video_file(self, port_info, ffmpeg_executor: FFmpegExecutor):
        anchor_name = port_info.anchor_name
        logger.info(f"\r{anchor_name} 录制mkv视频中")
        filename = self._get_file_path(port_info, "mkv")

        try:
            command = ffmpeg_executor.get_mkv_split_video_command(filename)
            ffmpeg_executor.execute(command)
            return True, port_info, filename
        except subprocess.CalledProcessError as e:
            logger.error(f"错误信息: {e} 发生错误的行数: {e.__traceback__.tb_lineno}")
            return False, port_info, filename

    def _save_mkv_audio_file(self, port_info, ffmpeg_executor: FFmpegExecutor):
        anchor_name = port_info.anchor_name
        logger.info(f"\r{anchor_name} 录制mkv音频中")
        filename = self._get_file_path(port_info, "mkv")

        try:
            command = ffmpeg_executor.get_mkv_split_audio_command(filename)
            ffmpeg_executor.execute(command)
            return True, port_info, filename
        except subprocess.CalledProcessError as e:
            logger.error(f"错误信息: {e} 发生错误的行数: {e.__traceback__.tb_lineno}")
            return False, port_info, filename

    def _save_mp4_video_file(self, port_info, ffmpeg_executor: FFmpegExecutor):
        anchor_name = port_info.anchor_name
        logger.info(f"\r{anchor_name} 录制mp4视频中")
        filename = self._get_file_path(port_info, "mp4")

        try:
            command = ffmpeg_executor.get_mp4_split_video_command(filename)
            ffmpeg_executor.execute(command)
            return True, port_info, filename
        except subprocess.CalledProcessError as e:
            logger.error(f"错误信息: {e} 发生错误的行数: {e.__traceback__.tb_lineno}")
            return False, port_info, filename

    def _save_ts_audio_file(self, port_info, ffmpeg_executor: FFmpegExecutor):
        anchor_name = port_info.anchor_name
        logger.info(f"\r{anchor_name} 录制ts音频中")
        filename = self._get_file_path(port_info, "ts")
        try:
            command = ffmpeg_executor.get_ts_audio_split_command(filename)
            ffmpeg_executor.execute(command)
            return True, port_info, filename
        except subprocess.CalledProcessError as e:
            logger.error(f"错误信息: {e} 发生错误的行数: {e.__traceback__.tb_lineno}")
            return False, port_info, filename

    def _save_ts_video_file(self, port_info, ffmpeg_executor: FFmpegExecutor):
        anchor_name = port_info.anchor_name
        logger.info(f"\r{anchor_name} 录制ts音频中")
        filename = self._get_file_path(port_info, "ts")

        try:
            command = ffmpeg_executor.get_ts_video_split_command(filename)
            ffmpeg_executor.execute(command)
            return True, port_info, filename
        except subprocess.CalledProcessError as e:
            logger.error(f"错误信息: {e} 发生错误的行数: {e.__traceback__.tb_lineno}")
            return False, port_info, filename

    def _get_file_folder(self, platform, anchor_name):
        path = self.config_manager.video_save_path
        folder_path = f"{path}/live/{platform}/stream/{anchor_name}"

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        return folder_path

    def _get_file_path(self, port_info, file_type):
        return f"{self._get_file_folder(port_info.platform, port_info.anchor_name)}/{port_info.live_date}_%03d.{file_type}"
