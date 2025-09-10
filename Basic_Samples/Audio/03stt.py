import requests
import os


STEP_API_KEY = os.environ["STEPFUN_API_KEY"]
BASE_URL= os.environ['STEPFUN_ENDPOINT']


def transcribe_audio(api_url,api_key, AUDIO_FILE_PATH, MODEL, RESPONSE_FORMAT,STREAM):
    # 打开音频文件
    with open(AUDIO_FILE_PATH, "rb") as audio_file:
        files = {
            "file": (AUDIO_FILE_PATH, audio_file, "audio/mpeg"),
        }
        data = {
            "model": MODEL,
            "stream": STREAM,
            "response_format": RESPONSE_FORMAT,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
        }

        try:
            # 发送 POST 请求
            url = api_url+"/audio/transcriptions"
            response = requests.post(url, headers=headers, files=files, data=data)
            response.raise_for_status()
            # 打印 Trace ID（如果响应头中返回）
            traceid = response.headers.get('X-Trace-ID')
            print(f"Trace ID: {traceid}")

            # 打印响应内容
            print("响应内容:")
            print(response.text)

        except requests.exceptions.RequestException as e:
            print(f"请求失败: {e}")
            print(response)


if __name__ == "__main__":
    # 从环境变量获取API密钥
    AUDIO_FILE_PATH = "./output/测试音频.mp3"  # 替换为您的音频文件路径
    MODEL = "step-asr"
    RESPONSE_FORMAT = "json"
    STREAM = True
    # 调整参数顺序
    transcribe_audio(BASE_URL, STEP_API_KEY, AUDIO_FILE_PATH, MODEL, RESPONSE_FORMAT,STREAM)