import gzip
import json
import logging
import os
import random
import re
import string
import time
from datetime import datetime
from urllib.parse import urlparse

import websocket

from danmu_fetcher.kuaishou.kuaishou_message import SCWebFeedPush, CSWebEnterRoom, SocketMessage, PayloadType, \
    SocketMessageCompressionType, WebCommentFeed
from network.spider import get_req


class KuaishouDanmuFetcher:
    def __init__(self, live_id, base_file_path, split_time, cookie):
        self.__room_id = None
        self.cookie = cookie
        self.live_id = live_id
        self.start_time = datetime.now()
        self.base_file_path = base_file_path
        self.split_time = int(split_time)
        self.live_url = "https://live.kuaishou.com/u/"
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) " \
                          "Chrome/120.0.0.0 Safari/537.36"
        self.message_handlers = {
            'WebcastChatMessage': self._parse_chat_msg,  # 聊天消息
            'WebcastControlMessage': self._parse_control_msg,  # 直播间状态消息
        }

        logging.basicConfig(level=logging.ERROR)
        self.logger = logging.getLogger(__name__)

    def _get_current_file_path(self):
        file_index = int((datetime.now() - self.start_time).total_seconds() / self.split_time)
        base_name, ext = os.path.splitext(self.base_file_path)
        return f"{base_name}_{file_index:03d}.{ext}"

    def start(self):
        self._connect_websocket()

    def stop(self):
        self.ws.close()

    def get_websocket_info(self):
        url = self.live_url + self.live_id
        parsed_url = urlparse(url)
        host = parsed_url.hostname
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
            'Accept-Encoding': 'gzip, deflate, br',
            'Host': host,
            'Cookie': self.cookie
        }
        try:
            html_str = get_req(url=url, headers=headers)
        except Exception as e:
            print(f"Failed to fetch dao from {url}.{e}")
            return None

        try:
            pattern_live_stream_id = r'"liveStream":\{"id":"([\w\d\-]+)"'
            match = re.search(pattern_live_stream_id, html_str)

            if match:
                live_stream_id = match.group(1)
                if live_stream_id:
                    result = {"live_stream_id": live_stream_id}
                    websocket_info_url = f"https://live.kuaishou.com/live_api/liveroom/websocketinfo?liveStreamId={live_stream_id}"
                    headers1 = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Accept': '*/*',
                        'Host': host,
                        'Cookie': self.cookie,
                        'Referer': url,
                    }
                    response = get_req(url=websocket_info_url, headers=headers1)
                    websocket_info = json.loads(response)
                    if websocket_info.get('dao') and websocket_info['dao'].get('result') == 1 and websocket_info['dao'].get('token'):
                        token = websocket_info['dao']['token']
                        websocket_urls = websocket_info['dao']['websocketUrls']
                        result.update({"token": token, "websocket_urls": websocket_urls})
                        return result
                    else:
                        print(f"Failed to get websocket token from {websocket_info_url}, response: {websocket_info}")
                        return None
        except (AttributeError, IndexError, json.JSONDecodeError) as e:
            print(f"Failed to parse JSON dao from {url}. Error: {e}")
            return None

    def _connect_websocket(self):
        """
        连接抖音直播间websocket服务器，请求直播间数据
        """
        self.websocket_info = self.get_websocket_info()
        if not self.websocket_info:
            return

        wss = (self.websocket_info["websocket_urls"][0])

        self.ws = websocket.WebSocketApp(
            wss,
            on_open=self._on_ws_open,
            on_message=self._on_ws_message,
            on_error=self._on_ws_error,
            on_close=self._on_ws_close
        )
        try:
            self.ws.run_forever()
        except Exception:
            self.stop()
            raise

    def _on_ws_open(self, ws):
        def random_string(length):
            return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
        """
        连接建立成功
        """
        print(f"WebSocket connected. Prepared save path:{self._get_current_file_path()} ")
        # send_auth_request
        websocket_info = self.websocket_info
        enter_room_message = CSWebEnterRoom(
            token=websocket_info["token"],
            live_stream_id=websocket_info["live_stream_id"],
            reconnect_count=3,
            last_error_code=4,
            exp_tag="",
            attach="",
            page_id=random_string(16) + str(int(time.time()))
        )
        socket_message = SocketMessage(
            payload_type=PayloadType.CS_ENTER_ROOM,
            payload=enter_room_message.SerializeToString()
        )

        ws.send(socket_message.SerializeToString(), opcode=websocket.ABNF.OPCODE_BINARY)

    def _on_ws_message(self, ws, message):
        """
        接收到数据
        :param ws: websocket实例
        :param message: 数据
        """

        # 根据proto结构体解析对象
        socket_message = SocketMessage().parse(message)
        compression_type = socket_message.compression_type
        payload_byte_string = socket_message.payload

        if compression_type == SocketMessageCompressionType.GZIP:
            try:
                socket_message.payload = gzip.decompress(payload_byte_string)
            except Exception as e:
                self.logger.error(f"Error during GZIP decompression: {e}")
                return

        sc_web_feed_push = SCWebFeedPush().parse(socket_message.payload)

        # 返回直播间服务器链接存活确认消息，便于持续获取数据
        if len(sc_web_feed_push.comment_feeds) > 0:
            for feed in sc_web_feed_push.comment_feeds:
                self._parse_chat_msg(feed)
            # ack = PushFrame(
            #     log_id=package.log_id,
            #     payload_type='ack',
            #     payload=response.internal_ext.encode('utf-8')
            # ).SerializeToString()
            # ws.send(ack, websocket.ABNF.OPCODE_BINARY)

    def _on_ws_error(self, ws, error):
        self.logger.error("WebSocket error: ", error)

    def _on_ws_close(self, ws, *args):
        self.logger.info("WebSocket connection closed.")

    def _parse_chat_msg(self, msg: WebCommentFeed):
        """聊天消息"""
        user_name = msg.user.user_name
        content = msg.content
        self.logger.info(f"【聊天msg】{user_name}: {content}")
        save_msg = f"[user_name: {user_name}] {content}"
        self.write_msg_to_file(save_msg)

    def _parse_gift_msg(self, payload):
        """礼物消息"""
        self.logger.info(f"【礼物msg】todo")

    def _parse_like_msg(self, payload):
        """点赞消息"""
        self.logger.info(f"【点赞msg】todo")

    def _parseMemberMsg(self, payload):
        """进入直播间消息"""
        self.logger.info(f"【进场msg】todo")

    def _parse_social_msg(self, payload):
        """关注消息"""
        self.logger.info(f"【关注msg】todo")

    def _parse_room_user_seq_msg(self, payload):
        """直播间统计"""
        self.logger.info(f"【统计msg】todo")

    def _parse_fans_club_msg(self, payload):
        """粉丝团消息"""
        self.logger.info(f"【粉丝团msg】todo")

    def _parse_emoji_chat_msg(self, payload):
        """聊天表情包消息"""
        self.logger.info(f"【聊天表情包id】todo")

    def _parse_room_msg(self, payload):
        self.logger.info(f"【直播间msg】todo")

    def _parse_room_state_msg(self, payload):
        self.logger.info(f"【直播间统计msg】todo")

    def _parse_rank_msg(self, payload):
        self.logger.info(f"【直播间排行榜msg】todo")

    def _parse_control_msg(self, payload):
        """直播间状态消息"""
        self.logger.info("直播间已结束")
        self.stop()

    def write_msg_to_file(self, msg):
        try:
            save_danmu_file_path = self._get_current_file_path()
            with open(save_danmu_file_path, 'a') as file:
                now = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
                file.write(f'[{now}] {msg} \n')
        except Exception as e:
            self.logger.error(f"写入文件时发生错误: {e}")
