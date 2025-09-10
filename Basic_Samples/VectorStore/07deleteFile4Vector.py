import requests
import os

# 从环境变量获取API密钥和基础URL
STEP_API_KEY = os.environ["STEPFUN_API_KEY"]
BASE_URL = os.environ['STEPFUN_ENDPOINT']

# 配置参数 - 请根据实际情况修改
vector_store_id = "274822495852478464"  # 知识库唯一ID
file_id = "file-KInq6Kuefo"  # 要删除的文件ID

# 构建删除请求的URL
url = f"{BASE_URL}/vector_stores/{vector_store_id}/files/{file_id}"

# 设置请求头（包含认证信息）
headers = {
    "Authorization": f"Bearer {STEP_API_KEY}"
}

try:
    # 发送DELETE请求
    response = requests.delete(url, headers=headers)
    response.raise_for_status()  # 检查HTTP错误状态码

    # 解析并打印成功响应
    result = response.json()
    if result.get("deleted"):
        print(f"文件 {file_id} 已成功从知识库 {vector_store_id} 中删除")
        print("响应详情:", result)
    else:
        print("删除操作未成功完成", result)

except requests.exceptions.HTTPError as e:
    print(f"HTTP错误: {e}")
    print("错误响应内容:", response.text)
except Exception as e:
    print(f"请求发生错误: {e}")