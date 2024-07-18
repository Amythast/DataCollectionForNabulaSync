import whisper

model = whisper.load_model("base")
result = model.transcribe("downloads/抖音直播/天元邓刚/天元邓刚_2024-07-18_23-02-34_000.ts")
print(result["text"])