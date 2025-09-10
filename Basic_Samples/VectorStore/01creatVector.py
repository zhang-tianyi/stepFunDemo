import requests
import os

STEP_API_KEY = os.environ["STEPFUN_API_KEY"]
BASE_URL= os.environ['STEPFUN_ENDPOINT']

url = BASE_URL+"/vector_stores"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {STEP_API_KEY}"  # 确保 STEP_API_KEY 是定义好的变量
}
data = {
    "name": "vector_iamge",
    "type": "image"
    # 支持 text (文本类型知识库）和 image (图片知识库）
}

response = requests.post(url, headers=headers, json=data)

if response.status_code == 200:
    print("Success:", response.json())
else:
    print("Error:", response.status_code, response.text)