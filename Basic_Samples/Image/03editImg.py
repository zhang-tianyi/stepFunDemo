import base64
from openai import OpenAI
import os

STEP_API_KEY = os.environ["STEPFUN_API_KEY"]
BASE_URL= os.environ['STEPFUN_ENDPOINT']

client = OpenAI(api_key=STEP_API_KEY, base_url=BASE_URL)
 
prompt = """
变成一只白猫
"""
 
result = client.images.edit(
  model="step-1x-edit",
  image=open("lihua.jpg", "rb"),
  prompt=prompt,
  response_format="b64_json",
  extra_body={"cfg_scale": 10.0, "steps": 20, "seed": 1},
)
 
print(result)
image_base64 = result.data[0].b64_json
image_bytes = base64.b64decode(image_base64)
 
# Save the image to a file
with open("white-cat.png", "wb") as f:
  f.write(image_bytes)
 