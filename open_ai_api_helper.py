from openai import AzureOpenAI

import utils

client = AzureOpenAI(
    api_key="956f32dfe9ad42848d18acd29e7da5e9",
    api_version="2023-03-15-preview",
    azure_endpoint="https://ffxgpt4.openai.azure.com"
)

deployment_name = 'gpt4'

# Send a completion call to generate an answer
print('Sending a test completion job')
start_phrase = 'Write a tagline for an ice cream shop. '
contents = utils.load_collect_file("downloads/XiaomiOfficialFlagshipStore/[audio_text]XiaomiOfficialFlagshipStore_2024-07-28_15-40-13_000.txt")
content = ""
for c in contents:
    content += c[0] + " " + c[1] + "\n"
response = client.chat.completions.create(
    model=deployment_name,
    messages=[
        {"role": "system", "content": "You are a text proofreader who converts audio to text."},
        {"role": "user", "content": f"```\n{content}```\nThe above text is a transcription of live streaming voice, there are some inaccuracies, please correct them; Some sentences are divided into several lines and merged together, using the timestamp of the first line when merging. Directly revise the original text and output it in the original text format, only need to output the file"},
    ]
)
print(response.choices[0].message.content)
