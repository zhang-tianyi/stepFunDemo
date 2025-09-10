import base64
import requests
import os

#这个代码跑不了
#Error: 400 {"error":{"message":"this knowledge base do not support 'term' search","type":"request_params_invalid"}}
STEP_API_KEY = os.environ["STEPFUN_API_KEY"]
BASE_URL = os.environ['STEPFUN_ENDPOINT']

# 配置参数 - 请根据实际情况修改
vector_store_id = "274822495852478464"
url = BASE_URL+"/vector_stores/"+vector_store_id+"/search"

def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    return encoded_string.decode('utf-8')
#
image_path1 = "./img/pigs/猪1.jpeg"
image_path2 = "./img/pigs/猪2.jpeg"
image_path3 = "./img/pigs/猪3.jpeg"
image_path4 = "./img/pigs/猪4.jpeg"

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