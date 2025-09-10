import requests
import os

STEP_API_KEY = os.environ["STEPFUN_API_KEY"]
BASE_URL= os.environ['STEPFUN_ENDPOINT']

file_id = "file-KIc1YSExFY"
URL = BASE_URL+"/files/"+file_id+"/content"

headers = {
    "Authorization": f"Bearer {STEP_API_KEY}"
}

response = requests.get(URL, headers=headers)

print(response.text)
print("返回码：", response.status_code)

