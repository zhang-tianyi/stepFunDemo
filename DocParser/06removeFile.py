import requests
import configparser

def read_config():
    config = configparser.ConfigParser()
    config.read('../config.ini')
    # 读取API配置/测试环境将step_api_prod换成step_api_test即可
    api_key = config.get('step_api_prod', 'key')
    api_url = config.get('step_api_prod', 'url')
    return api_key,api_url
STEP_API_KEY,BASE_URL = read_config()

file_id = "file-C0OGG69uvw"
URL = BASE_URL+"/files/"+file_id

headers = {
    "Authorization": f"Bearer {STEP_API_KEY}"
}

response = requests.delete(URL, headers=headers)
responseJson = response.json()
print(responseJson)