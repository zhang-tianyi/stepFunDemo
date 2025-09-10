import requests
import os

#读取配置文件
STEP_API_KEY = os.environ["STEPFUN_API_KEY"]
BASE_URL= os.environ['STEPFUN_ENDPOINT']

vector_store_id = "274822495852478464"
url = BASE_URL+"/vector_stores/"+vector_store_id

headers = {
    "Authorization": f"Bearer {STEP_API_KEY}"  # 确保 STEP_API_KEY 是定义好的变量
}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    print("Success:", response.json())
else:
    print("Error:", response.status_code, response.text)