import requests
import configparser
import json

def read_config():
    config = configparser.ConfigParser()
    config.read('../config.ini')
    # 读取 API 配置，测试环境将 step_api_prod 换成 step_api_test 即可
    api_key = config.get('step_api_prod', 'key')
    api_url = config.get('step_api_prod', 'url')
    return api_key, api_url

def transcribe_audio(api_url, api_key, audio_path, model, response_format, stream):
    url = f"{api_url}/audio/transcriptions"
    headers = {"Authorization": f"Bearer {api_key}"}
    files = {"file": (audio_path, open(audio_path, "rb"), "audio/mpeg")}
    data = {
        "model": model,
        "response_format": response_format,
        "stream": stream,
    }

    try:
        if stream:
            # 流式模式：边收边打印 delta
            resp = requests.post(url, headers=headers, files=files, data=data, stream=True)
            resp.raise_for_status()
            print("Trace ID:", resp.headers.get('X-Trace-ID'))
            print("开始流式输出：")
            for line in resp.iter_lines(decode_unicode=True):
                if not line:
                    continue
                # 形如 "data: {...}" 或 "data: [DONE]"
                prefix, payload = line.split(":", 1)
                payload = payload.strip()
                if payload == "[DONE]":
                    break
                try:
                    chunk = json.loads(payload)
                    # 增量文本在 delta 字段
                    print(chunk.get("delta", ""), end="", flush=True)
                except json.JSONDecodeError:
                    print(payload)
            print("\n—— 流式结束 ——")
        else:
            # 非流式模式：一次性拿完整 JSON
            resp = requests.post(url, headers=headers, files=files, data=data)
            resp.raise_for_status()
            print("Trace ID:", resp.headers.get('X-Trace-ID'))
            result = resp.json()
            # 完整文本
            text = result.get("text") or "（无 text 字段）"
            print("完整转写文本：\n", text)
            # 如果有 segments，也可以输出
            segments = result.get("segments")
            if segments:
                print("\n分段信息：")
                for seg in segments:
                    print(f" - [{seg.get('type')}] {seg.get('text')}")
    except requests.exceptions.RequestException as e:
        print("请求失败：", e)
    finally:
        files["file"][1].close()

if __name__ == "__main__":

    STEP_API_KEY, BASE_URL = read_config()
    AUDIO_FILE_PATH = "./response.mpga"
    MODEL = "step-asr-mini"
    RESPONSE_FORMAT = "json"
    STREAM = True

    transcribe_audio(
        api_url=BASE_URL,
        api_key=STEP_API_KEY,
        audio_path=AUDIO_FILE_PATH,
        model=MODEL,
        response_format=RESPONSE_FORMAT,
        stream=STREAM
    )