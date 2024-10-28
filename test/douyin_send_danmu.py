import random
import threading
from datetime import datetime

from selenium.webdriver import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.support.wait import WebDriverWait


def read_file_to_list(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    return [line.strip() for line in lines]


def send_danmaku():
    while True:
        try:
            message = random.choice(danmaku_list)

            danmaku_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="chat-textarea"]'))
            )
            danmaku_input.click()
            danmaku_input.clear()  # 清除任何可能存在的默认文本
            danmaku_input.send_keys(message)

            # 等待发送按钮元素加载
            send_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.webcast-chatroom___send-btn.btn-icon'))  # 根据实际的类名修改
            )

            send_button.click()
            time.sleep(random.uniform(min_delay, max_delay))
        except Exception as e:
            print("发弹幕出错:", e)


# 模拟点赞的操作
def like_live():
    while True:
        try:
            # 找到点赞按钮并点击
            video_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="island_d3bbb"]/div[1]'))  # 根据实际的类名修改
            )
            video_element.click()

            # 使用 ActionChains 模拟按下快捷键 'z'
            actions = ActionChains(driver)
            actions.send_keys('z').perform()
            time.sleep(random.uniform(min_delay1, max_delay1))
        except Exception as e:
            print("点赞出错:", e)


def adjust_delay():
    global min_delay, max_delay, min_delay1, max_delay1
    while True:
        try:
            new_min_delay = float(input("请输入弹幕新的最小延迟（秒）："))
            new_max_delay = float(input("请输入弹幕新的最大延迟（秒）："))
            new_min_delay1 = float(input("请输入点赞新的最小延迟（秒）："))
            new_max_delay1 = float(input("请输入点赞新的最大延迟（秒）："))
            if 0 <= new_min_delay < new_max_delay and 0 <= new_min_delay1 < new_max_delay1:
                min_delay, max_delay = new_min_delay, new_max_delay
                min_delay1, max_delay1 = new_min_delay1, new_max_delay1
                print(f"弹幕延迟已更新为：{min_delay} - {max_delay} 秒")
                print(f"点赞延迟已更新为：{min_delay1} - {max_delay1} 秒")
            else:
                print("请输入有效的延迟时间范围。")
        except ValueError:
            print("请输入有效的数字。")
        time.sleep(30)


if __name__ == '__main__':
    # 初始化WebDriver
    options = webdriver.ChromeOptions()
    # 如果不需要浏览器窗口显示，可以使用headless模式
    # options.add_argument("--headless")
    usr_data_dir = '/Users/feifeixia/Library/Application Support/Google/Chrome/Profile 1'
    options.add_argument(f"user-data-dir={usr_data_dir}")
    service = Service('/Users/feifeixia/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=options)
    cookies = [
        {'name': 'live_use_vvc', 'value': '%22false%22'},
        {'name': 'csrf_session_id', 'value': 'a79289f2967334618b97fd81adc70c51'},
        {'name': 'xgplayer_user_id', 'value': '478865389283'},
        {'name': 'my_rd', 'value': '2'},
        {'name': 'bd_ticket_guard_client_web_domain', 'value': '2'},
        {'name': 'passport_assist_user',
         'value': 'Cj3G7yR0gF2yXyCd28eRxBvaY9pXUFyfBZpiSgKIDg09Si-8I1MD7al_WNslPgQMOyLwcHa_hgN83OmiB_gXGkoKPDLd7j9ST6Xtfw76zNZOvvRX2TmYVcDCTg_VD2Tfi11lvGA9Ggx2N6EjSDmEU_qs5vMEYWsXbElFfnbFTBCyz8wNGImv1lQgASIBA2QbGdE%3D'},
        {'name': 'LOGIN_STATUS', 'value': '1'},
        {'name': 'has_avx2', 'value': 'null'},
        {'name': 'device_web_cpu_core', 'value': '8'},
        {'name': 'device_web_memory_size', 'value': '8'},
        {'name': 'webcast_local_quality', 'value': 'origin'},
        {'name': 'SEARCH_RESULT_LIST_TYPE', 'value': '%22single%22'},
        {'name': 'UIFID_TEMP',
         'value': '7457f5ef2178e63069f24974fa04cbf9321b3fa7afdb44208071bc08e7f7084f3230f6376cb3e850f92a8246ef00aa12f75309333c468f5a1c80b7ba5367c169f9889447be76902b4bb1ed4fc14247c4'},
        {'name': 'x-web-secsdk-uid', 'value': '9e2a10ef-9aac-4cf9-bac7-a7aba1bfe482'},
        {'name': 'fpk1',
         'value': 'U2FsdGVkX1+w8r2cO0M/7Ch1rLyKGBI1tyiunzuuHORSrQlTZpsecnaimP1ojYyeO7rSWCxGLU4u+LaJpkCY7A=='},
        {'name': 'fpk2', 'value': '8381c048a9d70230af13a12a76663dc4'},
        {'name': 's_v_web_id', 'value': 'verify_lyolnwwl_RvxsZyYi_gYU1_4nYB_88Sb_oEDY5x2XFVgg'},
        {'name': 'UIFID',
         'value': '7457f5ef2178e63069f24974fa04cbf9321b3fa7afdb44208071bc08e7f7084f3230f6376cb3e850f92a8246ef00aa12c0fe10e79d655ab7658136935a2a0280885def09a9056e15335006f6e5a6b55d7b757d479a3f0b7251f0f75a3c98b0c7759872dd5d93dd05f482e2839cb355968459749a0ef83374e01f63ee9776703750996693508871ba7e5c53fd8b9844c4f6616c9abc764ca9b696ff761ff9b1178885a875925493ba09ad2d6c81ef9424'},
        {'name': 'passport_csrf_token', 'value': '38572f6ed24024b4e1074623a41195de'},
        {'name': 'passport_csrf_token_default', 'value': '38572f6ed24024b4e1074623a41195de'},
        {'name': 'hevc_supported', 'value': 'true'},
        {'name': 'SelfTabRedDotControl', 'value': '%5B%5D'},
        {'name': 'passport_fe_beating_status', 'value': 'true'},
        {'name': 'publish_badge_show_info', 'value': '%220%2C0%2C0%2C1725548890891%22'},
        {'name': 'h265ErrorNum', 'value': '-1'},
        {'name': 'pwa2', 'value': '%220%7C0%7C3%7C0%22'},
        {'name': 'download_guide', 'value': '%223%2F20240906%2F1%22'},
        {'name': 'WallpaperGuide',
         'value': '%7B%22showTime%22%3A1725553685912%2C%22closeTime%22%3A0%2C%22showCount%22%3A1%2C%22cursor1%22%3A21%2C%22cursor2%22%3A2%2C%22hoverTime%22%3A1725554001926%7D'},
        {'name': 'volume_info', 'value': '%7B%22isUserMute%22%3Atrue%2C%22isMute%22%3Atrue%2C%22volume%22%3A0.6%7D'},
        {'name': 'FOLLOW_LIVE_POINT_INFO',
         'value': '%22MS4wLjABAAAAGaN54bXxNxSIQHRO3vdTtTqT5sp4d3hGA9Erpsqfe_E%2F1725638400000%2F0%2F1725559189405%2F0%22'},
        {'name': 'stream_recommend_feed_params',
         'value': '%22%7B%5C%22cookie_enabled%5C%22%3Atrue%2C%5C%22screen_width%5C%22%3A1512%2C%5C%22screen_height%5C%22%3A982%2C%5C%22browser_online%5C%22%3Atrue%2C%5C%22cpu_core_num%5C%22%3A8%2C%5C%22device_memory%5C%22%3A8%2C%5C%22downlink%5C%22%3A10%2C%5C%22effective_type%5C%22%3A%5C%224g%5C%22%2C%5C%22round_trip_time%5C%22%3A200%7D%22'},
        {'name': 'strategyABtestKey', 'value': '%221725699565.681%22'},
        {'name': 'biz_trace_id', 'value': '6f14a9df'},
        {'name': 'FOLLOW_NUMBER_YELLOW_POINT_INFO',
         'value': '%22MS4wLjABAAAAGaN54bXxNxSIQHRO3vdTtTqT5sp4d3hGA9Erpsqfe_E%2F1725724800000%2F0%2F1725699565982%2F0%22'},
        {'name': 'home_can_add_dy_2_desktop', 'value': '%221%22'},
        {'name': '__live_version__', 'value': '%221.1.2.3340%22'},
        {'name': '__ac_nonce', 'value': '066dc15f40099cf076b24'},
        {'name': '__ac_signature',
         'value': '_02B4Z6wo00f01RLzpxwAAIDCQAyHBgg9XnkS06OAACJjYKcLvdpiTBTcXEe04A-f3A0n1vyuv4adEYldemy7xO23SJes.DQxjz23DUOiPBCGMMT4EIYVnaCjKfm2C31TyP19WlzYl5E43SYz4a'},
        {'name': 'webcast_leading_last_show_time', 'value': '1725699574371'},
        {'name': 'webcast_leading_total_show_times', 'value': '13'},
        {'name': 'xg_device_score', 'value': '7.467505202438508'},
        {'name': 'bd_ticket_guard_client_data',
         'value': 'eyJiZC10aWNrZXQtZ3VhcmQtdmVyc2lvbiI6MiwiYmQtdGlja2V0LWd1YXJkLWl0ZXJhdGlvbi12ZXJzaW9uIjoxLCJiZC10aWNrZXQtZ3VhcmQtcmVlLXB1YmxpYy1rZXkiOiJCQVNwR3dvRkpWVUZNb28vNEI2THBrcnArU2EvVCszRTg3cC9OcHFUSXg3a2U0amtXSzI5RWdZNjlrK3pQRDdwcUY0YWFxcFVzTk5RS1BlREFNb3JodUE9IiwiYmQtdGlja2V0LWd1YXJkLXdlYi12ZXJzaW9uIjoxfQ%3D%3D'},
        {'name': 'live_can_add_dy_2_desktop', 'value': '%221%22'},
        {'name': 'IsDouyinActive', 'value': 'true'}
    ]

    # 打开抖音直播页面
    driver.get("https://www.douyin.com")

    for cookie in cookies:
        driver.add_cookie(cookie)

    time.sleep(1)
    driver.get("https://live.douyin.com/233276192382")
    danmaku_list = read_file_to_list("/test/live_danmu.txt")

    # 假设已经登录了抖音账号
    # 手动登录或者使用Selenium进行扫码等操作（这里可以根据具体情况处理）
    min_delay = 30
    max_delay = 45
    min_delay1 = 1
    max_delay1 = 2
    threading.Thread(target=send_danmaku, daemon=True).start()
    threading.Thread(target=like_live, daemon=True).start()

    while True:
        print("直播中")
        time.sleep(random.uniform(min_delay, max_delay))
    # 关闭浏览器
    # driver.quit()
