import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
import os

STEP_API_KEY = os.environ["STEPFUN_API_KEY"]
BASE_URL= os.environ['STEPFUN_ENDPOINT']

vector_store_id = "274822495852478464"
url = BASE_URL+"/vector_stores/"+vector_store_id+"/files"

headers = {
    "Authorization": f"Bearer {STEP_API_KEY}"  # 确保 STEP_API_KEY 是定义好的变量
}

# 准备 multipart 数据 
# 文件需要是retrieval-image或retrieval-text类型
multipart_data = MultipartEncoder(
    fields={
        "file_ids": "file-KInq6Kuefo"
    }
)
# 添加 multipart content-type 到头部
headers["Content-Type"] = multipart_data.content_type

response = requests.post(url, headers=headers, data=multipart_data)

if response.status_code == 200:
    print("Success:", response.json())
else:
    print("Error:", response.status_code, response.text)