import json
import re
from typing import Dict

from network.network_utils import get_request
from live_platform.base.base_var import config_manager_var
from live_platform.base.live.base_crawler import AbstractLivePortInfoFetcher
from live_platform.douyin.live.douyin_model import DouyinLivePortInfo, DouyinLiveInfo, DouyinOwner, DouyinSubscribe, \
    DouyinLiveStats
from common.logger import logger


class DouyinLiveLivePortInfoFetcher(AbstractLivePortInfoFetcher):
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'Referer': 'https://live.douyin.com/',
            'Cookie': 'ttwid=1%7CB1qls3GdnZhUov9o2NxOMxxYS2ff6OSvEWbv0ytbES4%7C1680522049%7C280d802d6d478e3e78d0c807f7c487e7ffec0ae4e5fdd6a0fe74c3c6af149511; my_rd=1; passport_csrf_token=3ab34460fa656183fccfb904b16ff742; passport_csrf_token_default=3ab34460fa656183fccfb904b16ff742; d_ticket=9f562383ac0547d0b561904513229d76c9c21; n_mh=hvnJEQ4Q5eiH74-84kTFUyv4VK8xtSrpRZG1AhCeFNI; store-region=cn-fj; store-region-src=uid; LOGIN_STATUS=1; __security_server_data_status=1; FORCE_LOGIN=%7B%22videoConsumedRemainSeconds%22%3A180%7D; pwa2=%223%7C0%7C3%7C0%22; download_guide=%223%2F20230729%2F0%22; volume_info=%7B%22isUserMute%22%3Afalse%2C%22isMute%22%3Afalse%2C%22volume%22%3A0.6%7D; strategyABtestKey=%221690824679.923%22; stream_recommend_feed_params=%22%7B%5C%22cookie_enabled%5C%22%3Atrue%2C%5C%22screen_width%5C%22%3A1536%2C%5C%22screen_height%5C%22%3A864%2C%5C%22browser_online%5C%22%3Atrue%2C%5C%22cpu_core_num%5C%22%3A8%2C%5C%22device_memory%5C%22%3A8%2C%5C%22downlink%5C%22%3A10%2C%5C%22effective_type%5C%22%3A%5C%224g%5C%22%2C%5C%22round_trip_time%5C%22%3A150%7D%22; VIDEO_FILTER_MEMO_SELECT=%7B%22expireTime%22%3A1691443863751%2C%22type%22%3Anull%7D; home_can_add_dy_2_desktop=%221%22; __live_version__=%221.1.1.2169%22; device_web_cpu_core=8; device_web_memory_size=8; xgplayer_user_id=346045893336; csrf_session_id=2e00356b5cd8544d17a0e66484946f28; odin_tt=724eb4dd23bc6ffaed9a1571ac4c757ef597768a70c75fef695b95845b7ffcd8b1524278c2ac31c2587996d058e03414595f0a4e856c53bd0d5e5f56dc6d82e24004dc77773e6b83ced6f80f1bb70627; __ac_nonce=064caded4009deafd8b89; __ac_signature=_02B4Z6wo00f01HLUuwwAAIDBh6tRkVLvBQBy9L-AAHiHf7; ttcid=2e9619ebbb8449eaa3d5a42d8ce88ec835; webcast_leading_last_show_time=1691016922379; webcast_leading_total_show_times=1; webcast_local_quality=sd; live_can_add_dy_2_desktop=%221%22; msToken=1JDHnVPw_9yTvzIrwb7cQj8dCMNOoesXbA_IooV8cezcOdpe4pzusZE7NB7tZn9TBXPr0ylxmv-KMs5rqbNUBHP4P7VBFUu0ZAht_BEylqrLpzgt3y5ne_38hXDOX8o=; msToken=jV_yeN1IQKUd9PlNtpL7k5vthGKcHo0dEh_QPUQhr8G3cuYv-Jbb4NnIxGDmhVOkZOCSihNpA2kvYtHiTW25XNNX_yrsv5FN8O6zm3qmCIXcEe0LywLn7oBO2gITEeg=; tt_scid=mYfqpfbDjqXrIGJuQ7q-DlQJfUSG51qG.KUdzztuGP83OjuVLXnQHjsz-BRHRJu4e986'
        }
        self.config_manager = config_manager_var.get()
        self.cookies = self.config_manager.dy_cookie
        if self.cookies:
            self.headers['Cookie'] = self.cookies

    async def get_port_info(self, live_info: DouyinLiveInfo) -> DouyinLiveInfo:
        try:
            origin_url_list = None
            response: Dict = get_request(
                url=live_info.live_url,
                proxy_addr=self.config_manager.proxy_addr,
                headers=self.headers
            )
            html_str = response['response']
            live_info.cookie = {**self.cookies, **response['cookies']}
            match_json_str = re.search(r'(\{\\"state\\":.*?)]\\n"]\)', html_str)
            if not match_json_str:
                match_json_str = re.search(r'(\{\\"common\\":.*?)]\\n"]\)</script><div hidden', html_str)
            json_str = match_json_str.group(1)
            cleaned_string = json_str.replace('\\', '').replace(r'u0026', r'&')
            room_store = re.search('"roomStore":(.*?),"linkmicStore"', cleaned_string, re.S).group(1)
            anchor_name = re.search('"nickname":"(.*?)","avatar_thumb', room_store, re.S).group(1)
            anchor_name = self._replace_illegal_char(anchor_name)
            room_store = room_store.split(',"has_commerce_goods"')[0] + '}}}'
            room_data = json.loads(room_store)['roomInfo']['room']

            live_info.anchor_name = anchor_name
            live_info.id_str = room_data['id_str']
            live_info.title = room_data['title']
            live_info.status = room_data['status']
            live_info.user_count_str = str(room_data['user_count_str'])

            if live_info.status and live_info.status == 4:
                return live_info

            match_json_str2 = re.search(r'"(\{\\"common\\":.*?)"]\)</script><script nonce=', html_str)
            if match_json_str2:
                json_str = match_json_str2.group(1).replace('\\', '').replace('"{', '{').replace('}"', '}').replace(
                    'u0026', '&')
                json_data2 = json.loads(json_str)
                if 'origin' in json_data2['dao']:
                    origin_url_list = json_data2['dao']['origin']['main']

            else:
                match_json_str3 = re.search('"origin":\{"main":(.*?),"dash"',
                                            html_str.replace('\\', '').replace('u0026', '&'), re.S)
                if match_json_str3:
                    origin_url_list = json.loads(match_json_str3.group(1) + '}')

            if origin_url_list:
                origin_m3u8 = {'ORIGIN': origin_url_list["hls"]}
                origin_flv = {'ORIGIN': origin_url_list["flv"]}
                hls_pull_url_map = room_data['stream_url']['hls_pull_url_map']
                flv_pull_url = room_data['stream_url']['flv_pull_url']
                room_data['stream_url']['hls_pull_url_map'] = {**origin_m3u8, **hls_pull_url_map}
                room_data['stream_url']['flv_pull_url'] = {**origin_flv, **flv_pull_url}

                live_info.stream_url = room_data['stream_url']
                live_info.cover = room_data['cover']

                live_info.owner = DouyinOwner(
                    id_str=room_data['owner']['id_str'],
                    sec_uid=room_data['owner']['sec_uid'],
                    avatar_thumb=room_data['owner']['avatar_thumb'],
                    follow_info=room_data['owner']['follow_info']['follow_status'],
                    suscribe=DouyinSubscribe(
                        is_member=room_data['owner']['subscribe']['is_member'],
                        level=room_data['owner']['subscribe']['level'],
                        identify_type=room_data['owner']['subscribe']['identify_type'],
                        buy_type=room_data['owner']['subscribe']['buy_type'],
                        open=room_data['owner']['subscribe']['open']
                    ),
                    open_id_str=room_data['owner']['open_id_str'],
                )
                live_info.room_auth = room_data['room_auth'],
                live_info.live_room_mode = room_data['live_room_mode']
                live_info.stats = DouyinLiveStats(
                    total_user_desp=room_data['stats']['total_user_desp'],
                    like_count=room_data['stats']['like_count'],
                    total_user_str=room_data['stats']['total_user_str'],
                    user_count_str=room_data['stats']['user_count_str']
                )
            return live_info

        except Exception as e:
            logger.error(f'第一次获取数据失败：{live_info.live_url} 尝试切换解析方法{e}')
            raise e

    def _replace_illegal_char(self, string: str) -> str:
        rstr = r"[\/\\\:\*\?\"\<\>\|&.。,， ]"
        return re.sub(rstr, "_", string)

    def process_port_info(self, live_info: DouyinLiveInfo) -> DouyinLivePortInfo:
        video_qualities = {"原画": 0, "蓝光": 0, "超清": 1, "高清": 2, "标清": 3, "流畅": 4}

        port_info = DouyinLivePortInfo(
            live_url=live_info.live_url,
            platform=live_info.platform,
            category=live_info.category,
            live_id=live_info.id_str,
            anchor_name=live_info.anchor_name,
            title=live_info.title,
            is_live=live_info.status != 4  # 判断是否直播中
        )

        if not port_info.is_live:
            return port_info

        quality_index = video_qualities.get(live_info.record_quality, 0)

        flv_url_dict = live_info.stream_url.get('flv_pull_url', {})
        m3u8_url_dict = live_info.stream_url.get('hls_pull_url_map', {})
        flv_url_list = list(flv_url_dict.values())
        m3u8_url_list = list(m3u8_url_dict.values())

        port_info.m3u8_url = m3u8_url_list[quality_index] if quality_index < len(m3u8_url_list) else None
        port_info.flv_url = flv_url_list[quality_index] if quality_index < len(flv_url_list) else None
        port_info.record_url = port_info.m3u8_url

        return port_info
