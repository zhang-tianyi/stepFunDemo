import base64
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

vector_store_id = "167830095522738176"
url = BASE_URL+"/vector_stores/"+vector_store_id+"/search"

def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    return encoded_string.decode('utf-8')
#
image_path1 = "../img/xicha/喜茶01.png"
image_path2 = "../img/xicha/喜茶02.JPEG"
image_path3 = "../img/xicha/喜茶03.png"
image_path4 = "../img/pigs/猪1.jpeg"

bstring1 = image_to_base64(image_path1)
bstring2 = image_to_base64(image_path2)
bstring3 = image_to_base64(image_path3)
bstring4 = image_to_base64(image_path4)

# print(bstring1)
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {STEP_API_KEY}"  # 确保 STEP_API_KEY 是定义好的变量
}
data = {
    # "image": f"data:image/webp;base64,{bstring1}",
    "term": "西红柿鸡炒番茄"
    # "count":5

}

response = requests.post(url, headers=headers, json=data)

if response.status_code == 200:
    print("Success:", response.json())
else:
    print("Error:", response.status_code, response.text)