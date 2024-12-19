import functools
import hashlib
import os
import re
import subprocess
import sys
import threading
import traceback
from logger import logger
import urllib.request
from urllib.error import URLError, HTTPError


def proxy_test():
    try:
        print('系统代理检测中，请耐心等待...')
        response_g = urllib.request.urlopen("https://www.google.com/", timeout=15)
        print('\r全局/规则网络代理已开启√')
        return True
    except HTTPError as err:
        print(f"HTTP error occurred: {err.code} - {err.reason}")
        return False
    except URLError as err:
        print("URLError:", err.reason)
        print('INFO：未检测到全局/规则网络代理，请检查代理配置（若无需录制海外直播请忽略此条提示）')
        return False
    except Exception as err:
        print("An unexpected error occurred:", err)
        return False


def check_ffmpeg_existence(ffmpeg_path):
    dev_null = open(os.devnull, 'wb')
    try:
        subprocess.run(['ffmpeg', '--help'], stdout=dev_null, stderr=dev_null, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(e)
        sys.exit(1)
    except FileNotFoundError:
        ffmpeg_file_check = subprocess.getoutput(ffmpeg_path)
        if ffmpeg_file_check.find("run") > -1 and os.path.isfile(ffmpeg_path):
            os.environ['PATH'] += os.pathsep + os.path.dirname(os.path.abspath(ffmpeg_path))
            # print(f"已将ffmpeg路径添加到环境变量：{ffmpeg_path}")
            return
        else:
            logger.error("检测到ffmpeg不存在,请将ffmpeg.exe放到同目录,或者设置为环境变量,没有ffmpeg将无法录制")
            sys.exit(0)
    finally:
        dev_null.close()


def trace_error_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_line = traceback.extract_tb(e.__traceback__)[-1].lineno
            error_info = f"错误信息: type: {type(e).__name__}, {str(e)} in function {func.__name__} at line: {error_line}"
            logger.error(error_info)
            return []

    return wrapper


def check_md5(file_path):
    """
    计算文件的md5值
    """
    with open(file_path, 'rb') as fp:
        file_md5 = hashlib.md5(fp.read()).hexdigest()
    return file_md5


def dict_to_cookie_str(cookies_dict):
    cookie_str = '; '.join([f"{key}={value}" for key, value in cookies_dict.items()])
    return cookie_str


def load_collect_file(file_path):
    # 读取文档
    contents = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            if line.strip():
                timestamp, content = parse_content_line(line)
                if timestamp:
                    contents.append((timestamp, content))
                else:
                    if contents:
                        last_timestamp = contents[-1][0]
                        contents.append((last_timestamp, content))
                    else:
                        # 如果是文件开头部分没有时间戳的内容
                        contents.append((None, content))
    return contents


def parse_content_line(line):
    # 提取时间戳和内容
    match = re.match(r"\[(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})\] (.*)", line)
    if match:
        timestamp = match.group(1)
        content = match.group(2)
        return timestamp, content
    return None, None


def transform_int_to_time(seconds: int) -> str:
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}"


def contains_url(string: str) -> bool:
    pattern = (r"(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)?[a-zA-Z0-9][a-zA-Z0-9\-]+(\.["
               r"a-zA-Z0-9\-]+)*\.[a-zA-Z]{2,10}(:[0-9]{1,5})?(\/.*)?$")
    return re.search(pattern, string) is not None


file_update_lock = threading.Lock()


def update_file(file_path: str, old_str: str, new_str: str, start_str: str = None):
    # 如果待更新的new_str 和 已有的 old_str 没区别，并且 不需要使用注释(start_str)，则直接返回
    if old_str == new_str and start_str is None:
        return
    with file_update_lock:
        file_data = ""
        with open(file_path, "r", encoding="utf-8-sig") as f:
            for text_line in f:
                if old_str in text_line:
                    text_line = text_line.replace(old_str, new_str)
                    if start_str:
                        text_line = f'{start_str}{text_line}'
                file_data += text_line
        with open(file_path, "w", encoding="utf-8-sig") as f:
            f.write(file_data)


def delete_line(file_path: str, del_line: str):
    with file_update_lock:
        with open(file_path, 'r+', encoding='utf-8') as f:
            lines = f.readlines()
            f.seek(0)
            f.truncate()
            for txt_line in lines:
                if del_line not in txt_line:
                    f.write(txt_line)
