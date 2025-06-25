import configparser
import requests
from pydub import AudioSegment

def read_config():
    config = configparser.ConfigParser()
    config.read('../config.ini')
    api_key = config.get('step_api_prod', 'key')
    api_url = config.get('step_api_prod', 'url')
    return api_key, api_url

def transcribe_audio(api_url, api_key, audio_bytes, MODEL="step-asr", RESPONSE_FORMAT="text"):
    """
    调用转写接口（非流式），返回纯文本或 JSON 中的 text 字段。
    """
    files = {
        "file": ("slice.mp3", audio_bytes, "audio/mpeg"),
    }
    data = {
        "model": MODEL,
        "response_format": RESPONSE_FORMAT,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
    }

    url = f"{api_url}/audio/transcriptions"
    resp = requests.post(url, headers=headers, files=files, data=data)
    try:
        resp.raise_for_status()
    except requests.exceptions.HTTPError:
        print(f"[ERROR] HTTP {resp.status_code}: {resp.text}")
        raise

    content_type = resp.headers.get("Content-Type", "")
    if "application/json" in content_type:
        return resp.json().get("text", "")
    else:
        return resp.text

def slice_and_transcribe(
    api_url,
    api_key,
    AUDIO_FILE_PATH,
    MODEL="step-asr",
    RESPONSE_FORMAT="text",
    slice_duration_ms: int = 60_000,
    overlap_ms: int = 5_000
):
    audio = AudioSegment.from_file(AUDIO_FILE_PATH)
    total_ms = len(audio)
    slice_index = 1

    step = slice_duration_ms - overlap_ms
    start_ms = 0

    while start_ms < total_ms:
        end_ms = min(start_ms + slice_duration_ms, total_ms)
        segment = audio[start_ms:end_ms]
        buf = segment.export(format="mp3")

        text = transcribe_audio(
            api_url, api_key, buf,
            MODEL=MODEL,
            RESPONSE_FORMAT=RESPONSE_FORMAT
        )

        print(f"\n[Slice {slice_index}] {start_ms}–{end_ms} ms 转写结果：")
        print(text, flush=True)

        slice_index += 1

        # 如果已经处理到音频末尾，退出循环
        if end_ms >= total_ms:
            break

        # 否则按窗口长度前进
        start_ms += step

    print("\n所有切片均已转写完毕。")

if __name__ == "__main__":
    STEP_API_KEY, BASE_URL = read_config()
    AUDIO_FILE_PATH = "./output/11.MP3"
    slice_and_transcribe(
        BASE_URL,
        STEP_API_KEY,
        AUDIO_FILE_PATH,
        MODEL="step-asr",
        RESPONSE_FORMAT="text",
        slice_duration_ms=60_000,  # 切片长度：60 秒
        overlap_ms=500           # 重叠长度：5 秒
    )