import requests
import os

#读取配置文件
STEP_API_KEY = os.environ["STEPFUN_API_KEY"]
BASE_URL= os.environ['STEPFUN_ENDPOINT']
url = BASE_URL+"/vector_stores"

params = {
    "limit": 20,
    "order": "desc",
    # "before": "137723691273302016"
}
headers = {
    "Authorization": f"Bearer {STEP_API_KEY}"  # 确保 STEP_API_KEY 是定义好的变量
}

response = requests.get(url, headers=headers, params=params)

if response.status_code == 200:
    print("Success:", response.json())
else:
    print("Error:", response.status_code, response.text)