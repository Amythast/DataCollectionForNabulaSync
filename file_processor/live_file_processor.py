import json
import os
import re
from datetime import datetime, timedelta
import whisper
from sentence_transformers import SentenceTransformer, util
from opencc import OpenCC

import utils

audio_text_prefix = '[audio_text]'
audio_text_combined_prefix = '[audio_combined]'
danmu_text_prefix = '[danmu_text]'
merge_for_azure_prefix = '[azure_finetune]'
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
# 繁体转简体
cc = OpenCC('t2s')


def transcribe_audio_to_text(ts_file_path):
    whisper_model = whisper.load_model("small")
    dir_path, filename = os.path.split(ts_file_path)
    azure_folder = os.path.join(dir_path, 'azure')
    if not os.path.exists(azure_folder):
        os.makedirs(azure_folder)

    name, ext = os.path.splitext(filename)
    result = whisper_model.transcribe(ts_file_path, append_punctuations=True)
    new_filename = audio_text_prefix + name + '.txt'
    processed_file_path = os.path.join(azure_folder, new_filename)
    for segment in result['segments']:
        content = format_output_with_timestamp(
            extract_timestamp_from_filename(filename),
            segment['start'],
            segment['text']
        ).strip()
        write_content_to_file(processed_file_path, content)
    return processed_file_path


def write_content_to_file(file_path, msg):
    try:
        with open(file_path, 'a') as file:
            file.write(f'{msg} \n')
    except Exception as e:
        print(f"写入文件时发生错误: {e}")


def format_timestamp(seconds):
    # 使用1970-01-01作为起始日期
    base_date = datetime(1970, 1, 1)
    td = timedelta(seconds=seconds)
    # 计算时间戳对应的日期时间
    timestamp = base_date + td
    # 格式化为"%Y-%m-%d_%H-%M-%S"
    return timestamp.strftime("%Y-%m-%d_%H-%M-%S")


def extract_timestamp_from_filename(filename):
    # 假设文件名格式为 "test_2024-07-28_15-40-13_000.ts"
    base_name = filename.split('.')[0]
    timestamp_str = base_name.split('_')[-3] + '_' + base_name.split('_')[-2]
    # 将字符串转换为datetime对象
    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d_%H-%M-%S")
    return timestamp


def format_output_with_timestamp(base_timestamp, offset_seconds, content):
    # 计算每句话的实际时间
    actual_timestamp = base_timestamp + timedelta(seconds=offset_seconds)
    formatted_timestamp = actual_timestamp.strftime("%Y-%m-%d_%H-%M-%S")
    simplified_text = cc.convert(content)

    return f"[{formatted_timestamp}] {simplified_text}"


def extract_timestamp_and_content(line):
    if not line:
        return None
    # 使用正则表达式提取时间戳和最后的内容部分
    timestamp_match = re.match(r"\[(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})\]", line)
    if not timestamp_match:
        return None
    timestamp = timestamp_match.group(1)

    content = line.split(']:')[-1].strip()

    if not content or len(content) == 0:
        return None
    return timestamp, content


# extract timestamp and content from danmu file, deduplicate and write to a new file
def process_danmu_file(input_file):
    dir_path, filename = os.path.split(input_file)
    azure_folder = os.path.join(dir_path, 'azure')
    if not os.path.exists(azure_folder):
        os.makedirs(azure_folder)

    name, ext = os.path.splitext(filename)
    output_file = os.path.join(azure_folder, danmu_text_prefix + name + '.txt')
    seen_content = set()  # 用于存储已经见过的内容
    with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
        for line in infile:
            timestamp, content = extract_timestamp_and_content(line)
            if timestamp and content and len(content) != 0 and content not in seen_content:
                outfile.write(f'[{timestamp}] {content}' + '\n')
                seen_content.add(content)
    return output_file


def sample():
    model = whisper.load_model("base")

    # load audio and pad/trim it to fit 30 seconds
    audio = whisper.load_audio("../downloads/output_test.wav")
    audio = whisper.pad_or_trim(audio)

    # make log-Mel spectrogram and move to the same device as the model
    mel = whisper.log_mel_spectrogram(audio).to(model.device)

    # detect the spoken language
    _, probs = model.detect_language(mel)
    print(f"Detected language: {max(probs, key=probs.get)}")

    # decode the audio
    options = whisper.DecodingOptions()
    result = whisper.decode(model, mel, options)

    # print the recognized text
    print(result.text)


# combine similar contents
def combine_audio_contents(audio_text_file, similarity_threshold=0.8):
    contents = utils.load_collect_file(audio_text_file)
    flat_contents = [content[1] for content in contents]

    # 计算每行的嵌入
    embeddings = model.encode(flat_contents, convert_to_tensor=True)

    # 聚合相似的内容
    combined_answers = []
    i = 0

    while i < len(contents):
        current_content = [contents[i]]
        current_embedding = embeddings[i]
        j = i + 1

        while j < len(contents):
            similarity = util.pytorch_cos_sim(current_embedding, embeddings[j])[0][0].item()
            if similarity >= similarity_threshold:
                current_content.append(contents[j])
                combined_text = ' '.join([content[1] for content in current_content])
                current_embedding = model.encode(combined_text, convert_to_tensor=True)
                j += 1
            else:
                break

        first_timestamp = current_content[0][0]
        combined_content = ' '.join([content[1] for content in current_content])
        combined_answers.append(f"[{first_timestamp}] {combined_content}")

        i = j

    dir_path, filename = os.path.split(audio_text_file)
    name, ext = os.path.splitext(filename)
    output_file = os.path.join(dir_path, audio_text_combined_prefix + name + ext)
    with open(output_file, 'w', encoding='utf-8') as file:
        for answer in combined_answers:
            file.write(answer + '\n')
    return output_file


def combine_audio_and_danmu(
        audio_text_file,
        danmu_file,
        go_through_audio_line=10,
        max_time_difference=4,
        similarity_threshold=0.6
):
    audio_contents = utils.load_collect_file(audio_text_file)
    danmu_contents = utils.load_collect_file(danmu_file)
    audio_segments = []
    for i in range(len(audio_contents) - go_through_audio_line):
        combined_text = ' '.join([audio_contents[j][1] + "." for j in range(i, i + go_through_audio_line)])
        audio_segments.append((audio_contents[i][0], combined_text))

    audio_text_contents = [content[1] for content in audio_segments]
    danmu_text_contents = [content[1] for content in danmu_contents]

    audio_embeddings = model.encode(audio_text_contents, convert_to_tensor=True)
    danmu_embeddings = model.encode(danmu_text_contents, convert_to_tensor=True)

    results = [{"role": "assistant", "content": a_content} for (a_timestamp, a_content) in audio_contents]
    origin_indexes = [i for i in range(len(audio_contents))]
    for i, (d_timestamp, d_content) in enumerate(danmu_contents):
        d_time = datetime.strptime(d_timestamp, "%Y-%m-%d_%H-%M-%S")
        best_similarity = -1
        best_position = -1
        # 查找与弹幕内容匹配的音频内容
        for j in range(len(audio_segments)):
            a_timestamp, a_content = audio_segments[j]
            a_time = datetime.strptime(a_timestamp, "%Y-%m-%d_%H-%M-%S")
            time_diff = a_time - d_time

            if time_diff.total_seconds() > 0 and time_diff <= timedelta(minutes=max_time_difference):
                similarity = util.pytorch_cos_sim(danmu_embeddings[i], audio_embeddings[j])[0][0].item()
                if similarity > best_similarity:
                    # 更新最匹配的位置
                    best_similarity = similarity
                    best_position = j
            elif time_diff.total_seconds() > timedelta(minutes=max_time_difference).total_seconds():
                # 超过时间范围，停止查找
                break

        if best_similarity >= similarity_threshold and best_position != -1:
            contexts = audio_segments[best_position][1].split('.')
            contexts_embeddings = model.encode(contexts, convert_to_tensor=True)
            most_similarity = -1
            most_index = -1
            for e in range(len(contexts_embeddings)):
                similarity = util.pytorch_cos_sim(contexts_embeddings[e], danmu_embeddings[i])[0][0].item()
                if similarity >= most_similarity:
                    most_similarity = similarity
                    most_index = e

            insert_position = origin_indexes[best_position + most_index]
            results.insert(
                insert_position,
                {"role": "user", "content": d_content}
            )
            for k in range(insert_position, len(audio_contents)):
                origin_indexes[k] += 1

    output_filename = audio_text_file.replace(f"{audio_text_combined_prefix}{audio_text_prefix}", f"{merge_for_azure_prefix}")
    output_filename = output_filename.replace(".txt", ".json")

    with open(output_filename, 'w', encoding='utf-8') as file:
        json.dump(results, file, ensure_ascii=False, indent=4)
    return results


# transcribe_audio_to_text("downloads/XiaomiOfficialFlagshipStore/XiaomiOfficialFlagshipStore_2024-07-28_15-40-13_000.ts")
# process_danmu_file("downloads/XiaomiOfficialFlagshipStore/XiaomiOfficialFlagshipStore_2024-07-28_15-40-13.txt")
# combine_audio_contents("downloads/XiaomiOfficialFlagshipStore/[audio_text]XiaomiOfficialFlagshipStore_2024-07-28_15-40-13_000.txt")
# combine_audio_and_danmu(
#     "downloads/XiaomiOfficialFlagshipStore/[audio_combined][audio_text]XiaomiOfficialFlagshipStore_2024-07-28_15-40-13_000.txt",
#     "downloads/XiaomiOfficialFlagshipStore/[danmu_text]XiaomiOfficialFlagshipStore_2024-07-28_15-40-13.txt")
