import requests
import configparser

def read_config():
    config = configparser.ConfigParser()
    config.read('../config.ini')
    # 读取API配置/测试环境将step_api_prod换成step_api_test即可
    api_key = config.get('step_api_prod', 'audio_key')
    api_url = config.get('step_api_prod', 'url')
    # api_key = config.get('step_api_test', 'audio_key')
    # api_url = config.get('step_api_test', 'url')
    return api_key,api_url
STEP_API_KEY,BASE_URL = read_config()

headers = {
    "Authorization": f"Bearer {STEP_API_KEY}"
}
files = {
    "file": ("猎聘男生片段.m4a", open("../file/猎聘男生片段.m4a", "rb")),
    # "file": ("11.pdf", open("file/2402.01684v1.pdf", "rb")),
    # "url": (None, "https://arxiv.org/pdf/2402.01684"),
}
data = {
    "purpose": "storage"
    # "purpose": "file-extract"
}

response = requests.post(BASE_URL+"/files", headers=headers, files=files, data=data)

print(response.json())
