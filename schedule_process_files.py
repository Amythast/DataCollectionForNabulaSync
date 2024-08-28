import os
import shutil

import schedule
import time
from datetime import datetime, timedelta
import re
import live_file_processor

# sales_bot 目录的根路径
base_dir = "/Volumes/External/sales_bot"


# 检查是否是有效的日期文件夹
def is_date_folder(folder_name):
    # 匹配 YYYY-MM-DD 的日期格式
    return re.match(r'\d{4}-\d{2}-\d{2}', folder_name) is not None


def process_live_record_folders():
    # 遍历 sales_bot 目录下的平台文件夹
    for platform_folder in os.listdir(base_dir):
        if check_hide_folder_or_file(platform_folder):
            continue
        platform_path = os.path.join(base_dir, platform_folder)
        print(f"处理平台文件夹: {platform_path}")
        # 确认这是一个文件夹
        if os.path.isdir(platform_path):
            # 遍历每个平台文件夹下的主播文件夹
            for anchor_folder in os.listdir(platform_path):
                if check_hide_folder_or_file(anchor_folder):
                    continue
                anchor_path = os.path.join(platform_path, anchor_folder)
                print(f"处理主播文件夹: {anchor_path}")
                # 确认这是一个主播文件夹
                if os.path.isdir(anchor_path):
                    # 遍历主播文件夹下的日期文件夹
                    for date_folder in os.listdir(anchor_path):
                        if check_hide_folder_or_file(date_folder):
                            continue
                        date_path = os.path.join(anchor_path, date_folder)
                        print(f"处理日期文件夹: {date_path}")

                        # 检查子目录是否为有效的日期文件夹
                        if os.path.isdir(date_path) and is_date_folder(date_folder):
                            # 只处理前一天的日期文件夹
                            find_file_folder(anchor_folder, date_path)


def check_hide_folder_or_file(folder_or_file_name):
    if folder_or_file_name.startswith('.'):
        return True


def find_file_folder(anchor_folder, date_path):
    files = os.listdir(date_path)
    for file_name in files:
        audio_match = re.match(
            rf'({anchor_folder}_\d{{4}}-\d{{2}}-\d{{2}}_\d{{2}}-\d{{2}}-\d{{2}})_(\d{{3}})\.ts',
            file_name
        )
        if audio_match:
            print(f"找到音频文件: {file_name}")
            base_name = audio_match.group(1)
            index = audio_match.group(2)
            expected_danmu_file = f"{base_name}_danmu_{index}.txt"
            if expected_danmu_file in files:
                print(f"找到弹幕文件: {expected_danmu_file}")
                audio_file_path = os.path.join(date_path, file_name)
                danmu_file_path = os.path.join(date_path, expected_danmu_file)
                process_audio_and_danmu(audio_file_path, danmu_file_path)
            else:
                print(f"No matching danmu file for {file_name}")


def process_audio_and_danmu(audio_file, danmu_file):
    # 这里实现你想要的具体处理逻辑
    print(f"处理音频文件: {audio_file}")
    transcribe_audio = live_file_processor.transcribe_audio_to_text(audio_file)
    combined_audio = live_file_processor.combine_audio_contents(transcribe_audio)
    print(f"处理弹幕文件: {danmu_file}")
    processed_danmu = live_file_processor.process_danmu_file(danmu_file)
    print(f"合并音频和弹幕文件")
    live_file_processor.combine_audio_and_danmu(combined_audio, processed_danmu)
    print(f"合并完成")
    move_file_to_processed_folder(audio_file)
    move_file_to_processed_folder(danmu_file)


def move_file_to_processed_folder(file_path):
    file_directory = os.path.dirname(file_path)
    processed_folder = os.path.join(file_directory, 'processed')

    if not os.path.exists(processed_folder):
        os.makedirs(processed_folder)

    destination_path = os.path.join(processed_folder, os.path.basename(file_path))
    shutil.move(file_path, destination_path)
    print(f"Moved {file_path} to {destination_path}")


# 设置定时任务每2h执行一次
schedule.every(2).hours.do(process_live_record_folders)

if __name__ == "__main__":
    # 初次执行时运行一次任务
    process_live_record_folders()

    # 进入定时任务的循环
    while True:
        schedule.run_pending()
        time.sleep(60)  # 每分钟检查一次
