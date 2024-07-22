import datetime
import whisper


def simple_transcribe(ts_file_path):
    # model = whisper.load_model("medium")
    model = whisper.load_model("base")
    result = model.transcribe(ts_file_path, append_punctuations=True)
    for segment in result['segments']:
        start = format_timestamp(segment['start'])
        end = format_timestamp(segment['end'])
        text = segment['text'].strip()
        print(f"[{start} --> {end}] {text}")

    return result["text"]


def format_timestamp(seconds):
    td = datetime.timedelta(seconds=seconds)
    # 返回格式 [HH:MM:SS.sss]
    return str(td)[:-3].replace('.', ',')


def sample():
    model = whisper.load_model("base")

    # load audio and pad/trim it to fit 30 seconds
    audio = whisper.load_audio("downloads/output_test.wav")
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


simple_transcribe("downloads/test.ts")
# devide_sentences()
