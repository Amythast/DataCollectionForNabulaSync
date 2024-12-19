import gzip
import os
import time
import urllib.parse
import hashlib
import codecs
from datetime import datetime
from functools import partial

from dao.model import LiveRecord
from dao.repository import save_live_file
from live_platform.base.base_var import config_manager_var, group_id_gen_var, task_manager_var
from live_platform.douyin.live.danmu.ptotobuf.douyin_message import PushFrame, Response, ChatMessage, ControlMessage
from common.logger import logger
import websocket
from fake_useragent import UserAgent
from py_mini_racer import MiniRacer

from live_platform.base.live.base_crawler import AbstractLiveDanmuFetcher
from live_platform.douyin.live.douyin_model import DouyinLivePortInfo


def generate_signature(wss, script_file='./sign.js'):
    """
    出现gbk编码问题则修改 python模块subprocess.py的源码中Popen类的__init__函数参数encoding值为 "utf-8"
    """
    params = ("live_id,aid,version_code,webcast_sdk_version,"
              "room_id,sub_room_id,sub_channel_id,did_rule,"
              "user_unique_id,device_platform,device_type,ac,"
              "identity").split(',')
    wss_params = urllib.parse.urlparse(wss).query.split('&')
    wss_maps = {i.split('=')[0]: i.split("=")[-1] for i in wss_params}
    tpl_params = [f"{i}={wss_maps.get(i, '')}" for i in params]
    param = ','.join(tpl_params)
    md5 = hashlib.md5()
    md5.update(param.encode())
    md5_param = md5.hexdigest()

    with codecs.open(script_file, 'r', encoding='utf8') as f:
        script = f.read()

    ctx = MiniRacer()
    ctx.eval(script)
    try:
        signature = ctx.call("get_sign", md5_param)
        return signature
    except Exception as e:
        print(e)


class DouyinLiveDanmuFetcher(AbstractLiveDanmuFetcher):

    def __init__(self):
        self.task_name = None
        self.task_manager = task_manager_var.get()
        self.message_handlers = {
            'WebcastChatMessage': self._parse_chat_msg,  # 聊天消息
            'WebcastControlMessage': self._parse_control_msg,  # 直播间状态消息
        }
        self.config_manager = config_manager_var.get()
        self.group_id_gen = group_id_gen_var.get()
        self.split_time = int(self.config_manager.split_time)

    def start_fetch(self, port_info: DouyinLivePortInfo, task_name: str = None):
        self._connect_websocket(port_info, datetime.now())
        self.task_name = task_name

    def stop(self):
        self.ws.close()

    def _connect_websocket(self, port_info: DouyinLivePortInfo, start_time):
        """
        连接抖音直播间websocket服务器，请求直播间数据
        """
        room_id = port_info.live_id
        wss = ("wss://webcast5-ws-web-hl.douyin.com/webcast/im/push/v2/?app_name=douyin_web"
               "&version_code=180800&webcast_sdk_version=1.0.14-beta.0"
               "&update_version_code=1.0.14-beta.0&compress=gzip&device_platform=web&cookie_enabled=true"
               "&screen_width=1536&screen_height=864&browser_language=zh-CN&browser_platform=Win32"
               "&browser_name=Mozilla"
               "&browser_version=5.0%20(Windows%20NT%2010.0;%20Win64;%20x64)%20AppleWebKit/537.36%20(KHTML,"
               "%20like%20Gecko)%20Chrome/126.0.0.0%20Safari/537.36"
               "&browser_online=true&tz_name=Asia/Shanghai"
               "&cursor=d-1_u-1_fh-7392091211001140287_t-1721106114633_r-1"
               f"&internal_ext=internal_src:dim|wss_push_room_id:{room_id}|wss_push_did:7319483754668557238"
               f"|first_req_ms:1721106114541|fetch_time:1721106114633|seq:1|wss_info:0-1721106114633-0-0|"
               f"wrds_v:7392094459690748497"
               f"&host=https://live.douyin.com&aid=6383&live_id=1&did_rule=3&endpoint=live_pc&support_wrds=1"
               f"&user_unique_id=7319483754668557238&im_path=/webcast/im/fetch/&identity=audience"
               f"&need_persist_msg_count=15&insert_task_id=&live_reason=&room_id={room_id}&heartbeatDuration=0")

        signature = generate_signature(wss)
        wss += f"&signature={signature}"

        headers = {
            "cookie": port_info.cookie,
            'user-agent': UserAgent().chrome,
        }

        on_open = partial(self._on_ws_open, port_info)
        on_message = partial(self._on_ws_message, port_info, start_time)
        on_error = partial(self._on_ws_error, port_info)
        on_close = partial(self._on_ws_close, port_info)

        self.ws = websocket.WebSocketApp(
            wss,
            header=headers,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        try:
            self.task_manager.create_task(
                task_name=self.task_name,
                func=self.ws.run_forever,
                task_group_id=self.group_id_gen.get_group_id()
            )
        except Exception:
            self.stop()
            raise

    def _on_ws_open(self, port_info, ws):
        """
        连接建立成功
        """
        logger.info(f"[{self.task_name}] WebSocket connected for room {port_info.anchor_name}.")

    def _on_ws_message(self, port_info, start_time, ws, message):
        """
        接收到数据
        :param ws: websocket实例
        :param message: 数据
        """

        # 根据proto结构体解析对象
        package = PushFrame().parse(message)
        response = Response().parse(gzip.decompress(package.payload))

        # 返回直播间服务器链接存活确认消息，便于持续获取数据
        if response.need_ack:
            ack = PushFrame(
                log_id=package.log_id,
                payload_type='ack',
                payload=response.internal_ext.encode('utf-8')
            ).SerializeToString()
            ws.send(ack, websocket.ABNF.OPCODE_BINARY)

        # 根据消息类别解析消息体
        for msg in response.messages_list:
            method = msg.method
            handler = self.message_handlers.get(method)

            if handler:
                try:
                    handler(msg.payload, port_info, start_time)
                except Exception as e:
                    # 记录详细错误日志
                    logger.error(f"[{self.task_name}][解析消息失败] 方法: {method}, 错误: {e}", exc_info=True)
            else:
                # 当消息类型没有处理器时
                logger.warning(f"[{self.task_name}]未知/不处理的消息类型: {method}")

    def _on_ws_error(self, port_info, ws, error):
        logger.error(f"[{self.task_name}] WebSocket error for room {port_info.anchor_name}: {error}")

    def _on_ws_close(self, port_info, ws, *args):
        logger.info(f"[{self.task_name}] WebSocket connection closed for room {port_info.anchor_name}.")
        self._save_record_to_db(port_info)

    def _parse_chat_msg(self, payload, port_info, start_time):
        """聊天消息"""
        message = ChatMessage().parse(payload)
        user_name = message.user.nick_name
        user_gender = message.user.gender
        user_age = message.user.age_range
        user_id = message.user.id
        content = message.content
        logger.info(f"[{self.task_name}][聊天msg][{user_id}]{user_name}: {content}")
        save_msg = f"[user_name: {user_name}][gender: {user_gender}][age: {user_age}] {content}"
        self.write_msg_to_file(save_msg, port_info, start_time)

    def _parse_control_msg(self, payload, port_info, start_time):
        """直播间状态消息"""
        message = ControlMessage().parse(payload)

        if message.status == 3:
            logger.info(f"[{self.task_name}]直播间{port_info.anchor_name}已结束")
            self.stop()

    def write_msg_to_file(self, msg, port_info, start_time):
        try:
            temp_file_path = self._get_file_path(port_info, start_time)
            with open(temp_file_path, 'a') as file:
                now = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
                file.write(f'[{now}] {msg} \n')
        except Exception as e:
            logger.error(f"[{self.task_name}]写入文件时发生错误: {e}")

    def _get_file_folder(self, port_info):
        path = self.config_manager.video_save_path
        folder_path = f"{path}/live/{port_info.platform}/danmu/{port_info.anchor_name}"

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        return folder_path

    def _get_file_path(self, port_info, start_time):
        file_index = int((datetime.now() - start_time).total_seconds() / self.split_time)
        return f"{self._get_file_folder(port_info)}/{port_info.live_date}_{file_index:03d}.txt"

    def _save_record_to_db(self, port_info: DouyinLivePortInfo):
        try:
            file_folder = self._get_file_folder(port_info)
            for root, dirs, files in os.walk(file_folder):
                for file_name in files:
                    file_path = os.path.join(root, file_name)

                    await save_live_file(
                        LiveRecord(
                            anchor_name=port_info.anchor_name,
                            platform=port_info.platform,
                            category=port_info.category,
                            live_date=port_info.live_date,
                            live_url=port_info.live_url,
                            live_slice=os.path.splitext(file_name)[0],
                            live_danmu_file=file_path
                        )
                    )
                    logger.info(f"文件 {file_path} 已存入数据库。")
        except Exception as e:
            logger.error(f"[{self.task_name}]写入数据库时发生错误: {e}")


if __name__ == "__main__":
    pass
