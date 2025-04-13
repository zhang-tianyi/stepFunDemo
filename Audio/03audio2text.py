import requests
import configparser

def read_config():
    config = configparser.ConfigParser()
    config.read('../config.ini')
    # 读取API配置/测试环境将step_api_prod换成step_api_test即可
    api_key = config.get('step_api_test', 'key')
    api_url = config.get('step_api_test', 'url')
    return api_key,api_url


def transcribe_audio(api_url,api_key, AUDIO_FILE_PATH, MODEL, RESPONSE_FORMAT):
    # 打开音频文件
    with open(AUDIO_FILE_PATH, "rb") as audio_file:
        files = {
            "file": (AUDIO_FILE_PATH, audio_file, "audio/mpeg"),
        }
        data = {
            "model": MODEL,
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
            print(response.json())

        except requests.exceptions.RequestException as e:
            print(f"请求失败: {e}")

if __name__ == "__main__":
    # 从环境变量获取API密钥
    STEP_API_KEY, BASE_URL = read_config()
    AUDIO_FILE_PATH = "./output/测试音频.mp3"  # 替换为您的音频文件路径
    MODEL = "step-asr"
    RESPONSE_FORMAT = "json"
    # 调整参数顺序
    transcribe_audio(BASE_URL, STEP_API_KEY, AUDIO_FILE_PATH, MODEL, RESPONSE_FORMAT)