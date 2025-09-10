import requests
import os

STEP_API_KEY = os.environ["STEPFUN_API_KEY"]
BASE_URL= os.environ['STEPFUN_ENDPOINT']
#filePurpose根据需要填写file-extract或retrieval
filePurpose="file-extract"
URL = BASE_URL+"/files?purpose="+filePurpose

headers = {
    "Authorization": f"Bearer {STEP_API_KEY}"
}

response = requests.get(URL, headers=headers)
responseJson = response.json()
print(responseJson)