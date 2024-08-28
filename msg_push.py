# -*- coding: utf-8 -*-

"""
Author: Hmily
GitHub: https://github.com/ihmily
Date: 2023-09-03 19:18:36
Update: 2024-07-01 22:16:36
Copyright (c) 2023 by Hmily, All Rights Reserved.
"""
import datetime
from typing import Dict, Any, Optional, Union
import json
import urllib.request
from utils import trace_error_decorator

no_proxy_handler = urllib.request.ProxyHandler({})
opener = urllib.request.build_opener(no_proxy_handler)
headers: Dict[str, str] = {'Content-Type': 'application/json'}


@trace_error_decorator
def dingtalk(url: str, content: str, phone_number: Optional[str] = '') -> Dict[str, Any]:
    json_data = {
        'msgtype': 'text',
        'text': {
            'content': content,
        },
        "at": {
            "atMobiles": [
                phone_number  # 添加这个手机号，可以被@通知（必须要在群里）
            ],
        },
    }
    data = json.dumps(json_data).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers)
    response = opener.open(req, timeout=10)
    json_str = response.read().decode('utf-8')
    json_data = json.loads(json_str)
    return json_data


@trace_error_decorator
def xizhi(url: str, content: str) -> Dict[str, Any]:
    json_data = {
        'title': '直播间状态更新',
        'content': content
    }
    data = json.dumps(json_data).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers)
    response = opener.open(req, timeout=10)
    json_str = response.read().decode('utf-8')
    json_data = json.loads(json_str)
    return json_data


@trace_error_decorator
def tg_bot(chat_id: int, token: str, content: str) -> Dict[str, Any]:
    json_data = {
        "chat_id": chat_id,
        'text': content
    }
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    data = json.dumps(json_data).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers)
    response = urllib.request.urlopen(req, timeout=15)
    json_str = response.read().decode('utf-8')
    json_data = json.loads(json_str)
    return json_data


def _push_message(config_manager, content: str) -> Union[str, list]:
    push_pts = []
    if '微信' in config_manager.live_status_push:
        push_pts.append('微信')
        xizhi(config_manager.xizhi_api_url, content)
    if '钉钉' in config_manager.live_status_push:
        push_pts.append('钉钉')
        dingtalk(config_manager.dingtalk_api_url, content, config_manager.dingtalk_phone_num)
    if 'TG' in config_manager.live_status_push or 'tg' in config_manager.live_status_push:
        push_pts.append('TG')
        tg_bot(config_manager.tg_chat_id, config_manager.tg_token, content)
    push_pts = '、'.join(push_pts) if len(push_pts) > 0 else []
    return push_pts


class MsgPushHelper:
    def __init__(self):
        self.live_start_pushed = False
        pass

    def push_live_msg(self, config_manager, port_info, record_name):
        push_at = datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        if port_info['is_live'] is False:
            print(f"\r{record_name} 等待直播... ")

            if self.live_start_pushed:
                if config_manager.over_show_push:
                    push_content = f"直播间状态更新：[直播间名称] 直播已结束！时间：[时间]"
                    if config_manager.over_push_message_text:
                        push_content = config_manager.over_push_message_text

                    push_content = push_content.replace('[直播间名称]', record_name).replace('[时间]', push_at)
                    push_pts = _push_message(push_content.replace(r'\n', '\n'))
                    if push_pts:
                        print(f'提示信息：已经将[{record_name}]直播状态消息推送至你的{push_pts}')
                self.live_start_pushed = False
        else:
            print(f"\r{record_name} 正在直播中...")

            if config_manager.live_status_push and not self.live_start_pushed:
                if config_manager.begin_show_push:
                    push_content = f"直播间状态更新：[直播间名称] 正在直播中，时间：[时间]"
                    if config_manager.begin_push_message_text:
                        push_content = config_manager.begin_push_message_text

                    push_content = push_content.replace('[直播间名称]', record_name).replace('[时间]', push_at)
                    push_pts = _push_message(config_manager, push_content.replace(r'\n', '\n'))
                    if push_pts:
                        print(f'提示信息：已经将[{record_name}]直播状态消息推送至你的{push_pts}')
                self.live_start_pushed = True


if __name__ == '__main__':
    content = '张三 开播了！'  # 推送内容

    # 钉钉推送通知
    webhook_api = ''  # 替换成自己Webhook链接,参考文档：https://open.dingtalk.com/document/robots/custom-robot-access
    phone_number = ''  # 被@用户的手机号码
    # dingtalk(webhook_api, content, phone_number)

    # 微信推送通知
    # 替换成自己的单点推送接口,获取地址：https://xz.qqoq.net/#/admin/one
    # 当然也可以使用其他平台API 如server酱 使用方法一样
    xizhi_api = 'https://xizhi.qqoq.net/XZa5a4a224987c88ab828acbcc0aa4c853.send'
    # xizhi(xizhi_api, content)

    # telegram推送通知
    token = ''  # tg搜索"BotFather"获取的token值
    chat_id = 000000  # tg搜索"userinfobot"获取的chat_id值，即可发送推送消息给你自己，如果下面的是群组id则发送到群
    # tg_bot(chat_id, token, content)