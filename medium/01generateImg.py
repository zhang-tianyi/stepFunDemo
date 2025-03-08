import requests
import base64
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

def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    return encoded_string.decode('utf-8')

COMPLETION_MODEL = "step-1x-medium"


image_path1 = "../img/qyl.png"

bstring1 = image_to_base64(image_path1)
base64_image = f"data:image/jpeg;base64,{bstring1}"

url = f'{BASE_URL}/images/generations'
params = {
        "model":"step-1x-medium",
        "prompt":"帮我基于图像生成一个卡通可爱版，预祝妇女节快乐的图像",
        "style_reference": {
             "source_url": base64_image,
             "weight":2
        }
}

headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {STEP_API_KEY}"
}

res = requests.post(url,json=params,headers=headers)
print(res.text)