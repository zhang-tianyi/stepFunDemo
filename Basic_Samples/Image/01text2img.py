import requests
import base64
import os

STEP_API_KEY = os.environ["STEPFUN_API_KEY"]
BASE_URL= os.environ['STEPFUN_ENDPOINT']

def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    return encoded_string.decode('utf-8')

COMPLETION_MODEL = "step-1x-medium"


image_path1 = "lihua.jpg"

bstring1 = image_to_base64(image_path1)
base64_image = f"data:image/jpeg;base64,{bstring1}"

url = f'{BASE_URL}/images/generations'
params = {
        "model":"step-2x-large",
        "prompt":"帮我基于图像生成一个白色的猫",
        "style_reference": {
             "source_url": base64_image,
             "weight":2
        }
}



headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {STEP_API_KEY}"
}

res = requests.post(url,json=params,headers=headers)
print(res.text)