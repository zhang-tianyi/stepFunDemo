import requests
import os

STEP_API_KEY = os.environ["STEPFUN_API_KEY"]
BASE_URL= os.environ['STEPFUN_ENDPOINT']

file_id = "file-KIcn9wB3ZI"
URL = BASE_URL+"/files/"+file_id

headers = {
    "Authorization": f"Bearer {STEP_API_KEY}"
}

response = requests.delete(URL, headers=headers)
responseJson = response.json()
print(responseJson)