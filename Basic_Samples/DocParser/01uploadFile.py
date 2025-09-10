import requests
import os

STEP_API_KEY = os.environ["STEPFUN_API_KEY"]
BASE_URL= os.environ['STEPFUN_ENDPOINT']

headers = {
    "Authorization": f"Bearer {STEP_API_KEY}"
}
files = {
    "file": ("lihua.jpg", open("../Image/lihua.jpg", "rb")),
    #"file": ("测试音频.mp3", open("../audio/output/测试音频.mp3", "rb")),
    # "url": (None, "https://arxiv.org/pdf/2402.01684"),
}
data = {
    # "purpose": "storage"
    # "purpose": "file-extract"
    "purpose": "retrieval-image"
}

response = requests.post(BASE_URL+"/files", headers=headers, files=files, data=data)

print(response.json())
