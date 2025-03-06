import requests
import time
from openai import OpenAI
import configparser

def read_config():
    config = configparser.ConfigParser()
    config.read('../config.ini')
    # 读取API配置/测试环境将step_api_prod换成step_api_test即可
    api_key = config.get('step_api_prod', 'key')
    api_url = config.get('step_api_prod', 'url')
    return api_key,api_url
STEP_API_KEY,BASE_URL = read_config()
def upload_file(filename, filepath, base_url, step_api_key):
    headers = {
        "Authorization": f"Bearer {step_api_key}"
    }
    with open(filepath, "rb") as file:
        files = {
            "file": (filename, file),
        }
        data = {
            "purpose": "file-extract"
        }
        # Make the API request
        response = requests.post(f"{base_url}/files", headers=headers, files=files, data=data)
        # Parse the JSON response
        response_json = response.json()
        # Return the file ID
        return response_json.get("id")
def get_file_status(fileid, base_url, step_api_key):
    headers = {
        "Authorization": f"Bearer {step_api_key}"
    }
    url = f"{base_url}/files/{fileid}"
    response = requests.get(url, headers=headers)
    response_json = response.json()
    return response_json.get('status', 'unknown')

def get_file_content(fileid, base_url, step_api_key):
    headers = {
        "Authorization": f"Bearer {step_api_key}"
    }
    url = f"{base_url}/files/{fileid}/content"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        return f"Error: {response.status_code} - {response.text}"


# 上传文件获取文件ID
file_id = upload_file(
    filename="经济责任审计制度.doc",
    filepath="./file/《经济责任审计制度》.doc",
    base_url=BASE_URL,
    step_api_key=STEP_API_KEY,
)

# 等待文件解析完成
while True:
    status = get_file_status(file_id, BASE_URL, STEP_API_KEY)
    if status == 'success':
        break
    time.sleep(1)  # 避免频繁请求

# 获取文件内容
file_content = get_file_content(file_id, BASE_URL, STEP_API_KEY)
print(file_content)

# 生成对话
messages = [
    {
        "role": "system",
        "content": "你是阶跃星辰助手，会读取用户发送给你的文件的内容，并结合文件内容回答问题",
    },
    {
        "role": "user",
        "content": file_content,
    },
    {"role": "user", "content": "请简单介绍文档的具体内容"},
]
time_start = time.time()
# 初始化
client = OpenAI(api_key=STEP_API_KEY,base_url=BASE_URL)
# 针对文件大小，可以使用 step-1-128k 或者 step-1-256k 等超长上下文大模型
# 实现文本补全
response = client.chat.completions.create(
    messages=messages,
    model="step-1-128k",
    stream=True,
)
i=0
for chunk in response:
    i += 1
    print(chunk.choices[0].delta.content.strip(),end="")
    if i == 1:
        time_firstWord = time.time()
        elapsed_time= time_firstWord-time_start
        print(f"首字生成时间: {elapsed_time:.2f} 秒")
time_end = time.time()
elapsed_time = time_end - time_start
print(f"总生成时间: {elapsed_time:.2f} 秒")



