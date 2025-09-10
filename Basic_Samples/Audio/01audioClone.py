import requests
import os

STEP_API_KEY = os.environ["STEPFUN_API_KEY"]
BASE_URL= os.environ['STEPFUN_ENDPOINT']

url = BASE_URL+"/audio/voices"

headers = {
    "Authorization": f"Bearer {STEP_API_KEY}",
    "Content-Type":"application/json"
}

data = {
    "file_id": "file-K2CCHn6HjM",
    "model": "step-tts-vivid",
    "text": "众鸟高飞尽，孤云独去闲。相看两不厌，只有敬亭山。",
    "sample_text": "床前明月光，疑似地上霜。"
}

response = requests.post(BASE_URL+"/audio/voices", headers=headers, json=data)
print(response.status_code)
print(response.json())

