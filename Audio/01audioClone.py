import requests
import configparser

#读取配置文件
def read_config():
    config = configparser.ConfigParser()
    config.read('../config.ini')
    # 读取API配置/测试环境将step_api_prod换成step_api_test即可
    api_key = config.get('step_api_prod', 'key')
    api_url = config.get('step_api_prod', 'url')
    return api_key,api_url
STEP_API_KEY,BASE_URL = read_config()

url = BASE_URL+"/audio/voices"

headers = {
    "Authorization": f"Bearer {STEP_API_KEY}"
}

data = {
    "file_id": "file-DnGR6zVayG",
    "model": "step-tts-mini",
    "text": "一二三四一二三四。",
    "sample_text": "床前明月光疑似地上霜，举头望明月，低头思故乡。"
}

# response = requests.post(BASE_URL+"/audio/voices", headers=headers, data=data)
try:
    # 发送POST请求
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()  # 如果响应状态码不是200，将抛出HTTPError异常

    # 解析并打印响应的JSON数据
    response_data = response.json()
    print(response_data)

except requests.exceptions.HTTPError as http_err:
    print(f'HTTP错误: {http_err}')
except Exception as err:
    print(f'其他错误: {err}')
