import configparser
import datetime
import os
import shutil
import sys
import time
import re
from typing import Any, Union
from common.logger import logger
from common.utils import (proxy_test, check_md5, contains_url, update_file)


def read_specific_config_value(file_path, section, key):
    """
    从配置文件中读取指定键的值。

    参数:
    - file_path: 配置文件的路径。
    - section: 部分名称。
    - key: 键名称。

    返回:
    - 键的值，如果部分或键不存在则返回None。
    """
    config = configparser.ConfigParser()

    try:
        config.read(file_path, encoding='utf-8-sig')
    except Exception as e:
        print(f"读取配置文件时出错: {e}")
        return None

    if section in config:
        if key in config[section]:
            return config[section][key]
        else:
            print(f"键[{key}]不存在于部分[{section}]中。")
    else:
        print(f"部分[{section}]不存在于文件中。")

    return None


def update_config(file_path, section, key, new_value):
    """
    更新配置文件中的键值。

    参数:
    - file_path: 配置文件的路径。
    - section: 要更新的部分名称。
    - key: 要更新的键名称。
    - new_value: 新的键值。
    """
    config = configparser.ConfigParser()

    try:
        config.read(file_path, encoding='utf-8-sig')
    except Exception as e:
        print(f"读取配置文件时出错: {e}")
        return

    if section not in config:
        print(f"部分[{section}]不存在于文件中。")
        return

    # 转义%字符
    escaped_value = new_value.replace('%', '%%')
    config[section][key] = escaped_value

    try:
        with open(file_path, 'w', encoding='utf-8-sig') as configfile:
            config.write(configfile)
        print(f"配置文件中[{section}]下的{key}的值已更新")
    except Exception as e:
        print(f"写入配置文件时出错: {e}")


class ConfigManager:
    def __init__(self):
        script_path = os.path.split(os.path.realpath(sys.argv[0]))[0]
        self.config_file = f'{script_path}/config/config.ini'
        self.url_config_file = f'{script_path}/config/URL_config.ini'
        self.backup_dir = f'{script_path}/backup_config'
        self.default_path = f'{script_path}/downloads'
        self.encoding = 'utf-8-sig'
        self.config_parser = configparser.RawConfigParser()
        self.need_update_line_list = []
        self.text_no_repeat_url = []
        self.not_record_list = []
        self.url_tuples_list = []
        self.platform_host = [
            'live.douyin.com',
            'v.douyin.com',
            'live.kuaishou.com',
            'www.huya.com',
            'www.douyu.com',
            'www.yy.com',
            'live.bilibili.com',
            'www.redelight.cn',
            'www.xiaohongshu.com',
            'xhslink.com',
            'www.bigo.tv',
            'slink.bigovideo.tv',
            'app.blued.cn',
            'cc.163.com',
            'qiandurebo.com',
            'fm.missevan.com',
            'look.163.com',
            'twitcasting.tv',
            'live.baidu.com',
            'weibo.com',
            'fanxing.kugou.com',
            'fanxing2.kugou.com',
            'mfanxing.kugou.com',
            'www.liveme.com',
            'www.huajiao.com',
            'www.7u66.com',
            'wap.7u66.com',
            'live.acfun.cn',
            'm.acfun.cn',
            'www.rengzu.com',
            'wap.rengzu.com',
            'www.inke.cn'
        ]
        self.overseas_platform_host = [
            'www.tiktok.com',
            'play.afreecatv.com',
            'm.afreecatv.com',
            'www.pandalive.co.kr',
            'www.winktv.co.kr',
            'www.flextv.co.kr',
            'www.popkontv.com',
            'www.twitch.tv',
            'www.showroom-live.com'
        ]
        self.platform_host.extend(self.overseas_platform_host)

    def load_config(self):
        self._read_config_file()
        self._initialize_configs()
        self._read_url_config_file()

    def _read_config_file(self):
        options = {"是": True, "否": False}

        try:
            if not os.path.isfile(self.config_file):
                with open(self.config_file, 'w', encoding=self.encoding) as file:
                    pass
        except OSError as err:
            logger.error(f"发生 I/O 错误: {err}")

        self.global_proxy = options.get(self._read_config_value('录制设置', '是否跳过代理检测（是/否）', "否"), False) or proxy_test()
        self.video_save_path = self._read_config_value('录制设置', '直播保存路径（不填则默认）', "")
        self.folder_by_author = options.get(self._read_config_value('录制设置', '保存文件夹是否以作者区分', "是"), False)
        self.video_save_type = self._read_config_value('录制设置', '视频保存格式ts|mkv|flv|mp4|ts音频|mkv音频', "ts")
        self.video_record_quality = self._read_config_value('录制设置', '原画|超清|高清|标清|流畅', "原画")
        self.use_proxy = options.get(self._read_config_value('录制设置', '是否使用代理ip（是/否）', "是"), False)
        self.use_vpn = options.get(self._read_config_value('录制设置', '是否使用VPN', "否"), False)
        self.proxy_addr_bak = self._read_config_value('录制设置', '代理地址', "")
        self.max_request = int(self._read_config_value('录制设置', '同一时间访问网络的线程数', 3))
        self.delay_default = int(self._read_config_value('录制设置', '循环时间(秒)', 120))
        self.local_delay_default = int(self._read_config_value('录制设置', '排队读取网址时间(秒)', 0))
        self.loop_time = options.get(self._read_config_value('录制设置', '是否显示循环秒数', "否"), False)
        self.show_url = options.get(self._read_config_value('录制设置', '是否显示直播源地址', "否"), False)
        self.split_video_by_time = options.get(self._read_config_value('录制设置', '分段录制是否开启', "否"), False)
        self.split_time = str(self._read_config_value('录制设置', '视频分段时间(秒)', 1800))
        self.ts_to_mp4 = options.get(self._read_config_value('录制设置', 'ts录制完成后自动转为mp4格式', "否"), False)
        self.ts_to_m4a = options.get(self._read_config_value('录制设置', 'ts录制完成后自动增加生成m4a格式', "否"), False)
        self.ts_to_mp3 = options.get(self._read_config_value('录制设置', '音频录制完成后自动转为mp3格式', "否"), False)
        self.delete_origin_file = options.get(self._read_config_value('录制设置', '追加格式后删除原文件', "否"), False)
        self.create_time_file = options.get(self._read_config_value('录制设置', '生成时间文件', "否"), False)
        self.enable_proxy_platform = self._read_config_value(
            '录制设置',
            '使用代理录制的平台（逗号分隔）',
            'tiktok, afreecatv, pandalive, winktv, flextv, popkontv, twitch, showroom'
        )
        self.extra_enable_proxy = self._read_config_value('录制设置', '额外使用代理录制的平台（逗号分隔）', '')
        self.live_status_push = self._read_config_value('推送配置', '直播状态通知(可选微信|钉钉|tg或者都填)', "")
        self.dingtalk_api_url = self._read_config_value('推送配置', '钉钉推送接口链接', "")
        self.xizhi_api_url = self._read_config_value('推送配置', '微信推送接口链接', "")
        self.dingtalk_phone_num = self._read_config_value('推送配置', '钉钉通知@对象(填手机号)', "")
        self.tg_token = self._read_config_value('推送配置', 'tgapi令牌', "")
        self.tg_chat_id = self._read_config_value('推送配置', 'tg聊天id(个人或者群组id)', "")
        self.begin_push_message_text = self._read_config_value('推送配置', '自定义开播推送内容', "")
        self.over_push_message_text = self._read_config_value('推送配置', '自定义关播推送内容', "")
        self.disable_record = options.get(self._read_config_value('推送配置', '只推送通知不录制（是/否）', "否"), False)
        self.push_check_seconds = int(self._read_config_value('推送配置', '直播推送检测频率（秒）', 1800))
        self.begin_show_push = options.get(self._read_config_value('推送配置', '开播推送开启（是/否）', "是"), True)
        self.over_show_push = options.get(self._read_config_value('推送配置', '关播推送开启（是/否）', "否"), False)
        self.afreecatv_username = self._read_config_value('账号密码', 'afreecatv账号', '')
        self.afreecatv_password = self._read_config_value('账号密码', 'afreecatv密码', '')
        self.flextv_username = self._read_config_value('账号密码', 'flextv账号', '')
        self.flextv_password = self._read_config_value('账号密码', 'flextv密码', '')
        self.popkontv_username = self._read_config_value('账号密码', 'popkontv账号', '')
        self.popkontv_partner_code = self._read_config_value('账号密码', 'partner_code', 'P-00001')
        self.popkontv_password = self._read_config_value('账号密码', 'popkontv密码', '')
        self.twitcasting_account_type = self._read_config_value('账号密码', 'twitcasting账号类型', 'normal')
        self.twitcasting_username = self._read_config_value('账号密码', 'twitcasting账号', '')
        self.twitcasting_password = self._read_config_value('账号密码', 'twitcasting密码', '')
        self.popkontv_access_token = self._read_config_value('Authorization', 'popkontv_token', '')
        self.dy_cookie = self._read_config_value('Cookie', '抖音cookie(录制抖音必须要有)', '')
        self.ks_cookie = self._read_config_value('Cookie', '快手cookie', '')
        self.tiktok_cookie = self._read_config_value('Cookie', 'tiktok_cookie', '')
        self.hy_cookie = self._read_config_value('Cookie', '虎牙cookie', '')
        self.douyu_cookie = self._read_config_value('Cookie', '斗鱼cookie', '')
        self.yy_cookie = self._read_config_value('Cookie', 'yy_cookie', '')
        self.bili_cookie = self._read_config_value('Cookie', 'B站cookie', '')
        self.xhs_cookie = self._read_config_value('Cookie', '小红书cookie', '')
        self.bigo_cookie = self._read_config_value('Cookie', 'bigo_cookie', '')
        self.blued_cookie = self._read_config_value('Cookie', 'blued_cookie', '')
        self.afreecatv_cookie = self._read_config_value('Cookie', 'afreecatv_cookie', '')
        self.netease_cookie = self._read_config_value('Cookie', 'netease_cookie', '')
        self.qiandurebo_cookie = self._read_config_value('Cookie', '千度热播_cookie', '')
        self.pandatv_cookie = self._read_config_value('Cookie', 'pandatv_cookie', '')
        self.maoerfm_cookie = self._read_config_value('Cookie', '猫耳fm_cookie', '')
        self.winktv_cookie = self._read_config_value('Cookie', 'winktv_cookie', '')
        self.flextv_cookie = self._read_config_value('Cookie', 'flextv_cookie', '')
        self.look_cookie = self._read_config_value('Cookie', 'look_cookie', '')
        self.twitcasting_cookie = self._read_config_value('Cookie', 'twitcasting_cookie', '')
        self.baidu_cookie = self._read_config_value('Cookie', 'baidu_cookie', '')
        self.weibo_cookie = self._read_config_value('Cookie', 'weibo_cookie', '')
        self.kugou_cookie = self._read_config_value('Cookie', 'kugou_cookie', '')
        self.twitch_cookie = self._read_config_value('Cookie', 'twitch_cookie', '')
        self.liveme_cookie = self._read_config_value('Cookie', 'liveme_cookie', '')
        self.huajiao_cookie = self._read_config_value('Cookie', 'huajiao_cookie', '')
        self.liuxing_cookie = self._read_config_value('Cookie', 'liuxing_cookie', '')
        self.showroom_cookie = self._read_config_value('Cookie', 'showroom_cookie', '')
        self.acfun_cookie = self._read_config_value('Cookie', 'acfun_cookie', '')
        self.shiguang_cookie = self._read_config_value('Cookie', 'shiguang_cookie', '')
        self.yingke_cookie = self._read_config_value('Cookie', 'yingke_cookie', '')

    def _initialize_configs(self):
        self.proxy_addr = None if not self.use_proxy else self.proxy_addr_bak
        self.enable_proxy_platform_list = self.enable_proxy_platform \
            .replace('，', ',') \
            .split(',') if self.enable_proxy_platform else None

        self.extra_enable_proxy_platform_list = self.extra_enable_proxy \
            .replace('，', ',') \
            .split(',') if self.extra_enable_proxy else None

        if len(self.video_save_type) > 0:
            if self.video_save_type.upper().lower() == "FLV".lower():
                self.video_save_type = "FLV"
            elif self.video_save_type.upper().lower() == "MKV".lower():
                self.video_save_type = "MKV"
            elif self.video_save_type.upper().lower() == "TS".lower():
                self.video_save_type = "TS"
            elif self.video_save_type.upper().lower() == "MP4".lower():
                self.video_save_type = "MP4"
            elif self.video_save_type.upper().lower() == "TS音频".lower():
                self.video_save_type = "TS音频"
            elif self.video_save_type.upper().lower() == "MKV音频".lower():
                self.video_save_type = "MKV音频"
            else:
                self.video_save_type = "TS"
                logger.info("直播视频保存格式设置有问题,这次录制重置为默认的TS格式")
        else:
            self.video_save_type = "TS"
            logger.info("直播视频保存为TS格式")

    def _read_url_config_file(self):
        try:
            ini_URL_content = ''
            if os.path.isfile(self.url_config_file):
                with open(self.url_config_file, 'r', encoding=self.encoding) as file:
                    ini_URL_content = file.read().strip()

            if not ini_URL_content.strip():
                input_url = input('请输入要录制的主播直播间网址（尽量使用PC网页端的直播间地址）:\n')
                with open(self.url_config_file, 'w', encoding=self.encoding) as file:
                    file.write(input_url)

            with open(self.url_config_file, "r", encoding=self.encoding, errors='ignore') as file:
                for line in file:
                    line = line.strip()
                    if line.startswith("#") or len(line) < 20:
                        continue

                    if re.search('[,，]', line):
                        split_line = re.split('[,，]', line)
                    else:
                        split_line = [line, '']

                    if len(split_line) == 1:
                        url = split_line[0]
                        quality, name = [self.video_record_quality, '']
                    elif len(split_line) == 2:
                        if contains_url(split_line[0]):
                            quality = self.video_record_quality
                            url, name = split_line
                        else:
                            quality, url = split_line
                            name = ''
                    else:
                        quality, url, name = split_line

                    if quality not in ["原画", "蓝光", "超清", "高清", "标清", "流畅"]:
                        quality = '原画'

                    if ('http://' not in url) and ('https://' not in url):
                        url = 'https://' + url

                    url_host = url.split('/')[2]

                    if url_host in self.platform_host:
                        if url_host in ['live.douyin.com', 'live.bilibili.com', 'www.huajiao.com']:
                            update_file(self.url_config_file, url, url.split('?')[0])
                            url = url.split('?')[0]
                        if url_host in ['www.xiaohongshu.com', 'www.redelight.cn']:
                            if 'share_source' in url:
                                xhs_url_h, xhs_url_t, = url.split('?')
                                new_xhs_url = xhs_url_h + '?appuid=' + xhs_url_t.split('&appuid=')[1].split('&')[0]
                                update_file(self.url_config_file, url, new_xhs_url)
                                url = new_xhs_url

                        new_line = (quality, url, name)
                        self.url_tuples_list.append(new_line)
                    else:
                        logger.info(f"\r{url} 未知链接.此条跳过")
                        update_file(self.url_config_file, url, url, start_str='#')

            while len(self.need_update_line_list):
                a = self.need_update_line_list.pop()
                replace_words = a.split('|')
                if replace_words[0] != replace_words[1]:
                    if replace_words[1].startswith("#"):
                        start_with = '#'
                        new_word = replace_words[1][1:]
                    else:
                        start_with = None
                        new_word = replace_words[1]
                    update_file(self.url_config_file, replace_words[0], new_word, start_str=start_with)

            # 去重
            if len(self.url_tuples_list) > 0:
                self.url_tuples_list = list(set(self.url_tuples_list))

        except Exception as err:
            logger.error(f"错误信息: {err} 发生错误的行数: {err.__traceback__.tb_lineno}")

    def get_proxy_address(self, url):
        proxy = self.proxy_addr
        if self.proxy_addr:
            proxy = None
            for platform in self.enable_proxy_platform_list:
                if platform and platform.strip() in url:
                    proxy = self.proxy_addr
                    break

        if not proxy:
            if self.extra_enable_proxy_platform_list:
                for pt in self.extra_enable_proxy_platform_list:
                    if pt and pt.strip() in url:
                        proxy = self.proxy_addr_bak if self.proxy_addr_bak else None
        return proxy

    def _read_config_value(
            self,
            section: str,
            option: str,
            default_value: Any
    ) -> Union[str, int, bool]:
        try:
            self.config_parser.read(self.config_file, encoding=self.encoding)
            if '录制设置' not in self.config_parser.sections():
                self.config_parser.add_section('录制设置')
            if '推送配置' not in self.config_parser.sections():
                self.config_parser.add_section('推送配置')
            if 'Cookie' not in self.config_parser.sections():
                self.config_parser.add_section('Cookie')
            if 'Authorization' not in self.config_parser.sections():
                self.config_parser.add_section('Authorization')
            if '账号密码' not in self.config_parser.sections():
                self.config_parser.add_section('账号密码')
            return self.config_parser.get(section, option)
        except (configparser.NoSectionError, configparser.NoOptionError):
            self.config_parser.set(section, option, str(default_value))
            with open(self.config_file, 'w', encoding=self.encoding) as f:
                self.config_parser.write(f)
            return default_value

    def backup_config_start(self):
        config_md5 = ''
        url_config_md5 = ''
        while True:
            try:
                if os.path.exists(self.config_file):
                    new_config_md5 = check_md5(self.config_file)
                    if new_config_md5 != config_md5:
                        self._backup_file(self.config_file, self.backup_dir)
                        config_md5 = new_config_md5

                if os.path.exists(self.url_config_file):
                    new_url_config_md5 = check_md5(self.url_config_file)
                    if new_url_config_md5 != url_config_md5:
                        self._backup_file(self.url_config_file, self.backup_dir)
                        url_config_md5 = new_url_config_md5
                time.sleep(600)  # 每10分钟检测一次文件是否有修改
            except Exception as e:
                logger.info(f'执行脚本异常：{str(e)}')

    def _backup_file(self, file_path: str, backup_dir_path: str):
        try:
            if not os.path.exists(backup_dir_path):
                os.makedirs(backup_dir_path)

            timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            backup_file_name = os.path.basename(file_path) + '_' + timestamp

            backup_file_path = os.path.join(backup_dir_path, backup_file_name).replace("\\", "/")
            shutil.copy2(file_path, backup_file_path)
            # print(f'\r已备份配置文件 {file_path} 到 {backup_file_path}')

            files = os.listdir(backup_dir_path)
            url_files = [f for f in files if f.startswith(os.path.basename(self.url_config_file))]
            config_files = [f for f in files if f.startswith(os.path.basename(self.config_file))]

            url_files.sort(key=lambda x: os.path.getmtime(os.path.join(backup_dir_path, x)))
            config_files.sort(key=lambda x: os.path.getmtime(os.path.join(backup_dir_path, x)))

            while len(url_files) > 6:
                oldest_file = url_files[0]
                os.remove(os.path.join(backup_dir_path, oldest_file))
                url_files = url_files[1:]

            while len(config_files) > 6:
                oldest_file = config_files[0]
                os.remove(os.path.join(backup_dir_path, oldest_file))
                config_files = config_files[1:]

        except Exception as e:
            logger.error(f'\r备份配置文件 {file_path} 失败：{str(e)}')

        