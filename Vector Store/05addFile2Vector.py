import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
import configparser

#读取配置文件
def read_config():
    config = configparser.ConfigParser()
    config.read('../config.ini')
    # 读取API配置/测试环境将step_api_prod换成step_api_test即可
    api_key = config.get('step_api_prod', 'key')
    api_url = config.get('step_api_prod', 'url')
    return api_key,api_url
STEP_API_KEY,BASE_URL = read_config()

vector_store_id = "201278974746398720"
url = BASE_URL+"/vector_stores/"+vector_store_id+"/files"

headers = {
    "Authorization": f"Bearer {STEP_API_KEY}"  # 确保 STEP_API_KEY 是定义好的变量
}

# 准备 multipart 数据
multipart_data = MultipartEncoder(
    fields={
        "file_ids": "file-ErrCJi45k8"
    }
)
# 添加 multipart content-type 到头部
headers["Content-Type"] = multipart_data.content_type

response = requests.post(url, headers=headers, data=multipart_data)

if response.status_code == 200:
    print("Success:", response.json())
else:
    print("Error:", response.status_code, response.text)