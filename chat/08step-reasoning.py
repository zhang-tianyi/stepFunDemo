import configparser
import time
import base64
import requests
import json

def read_config():
    config = configparser.ConfigParser()
    config.read('../config.ini')
    # 读取 API 配置；测试环境将 step_api_prod 换成 step_api_test 即可
    api_key = config.get('step_api_test', 'key')
    api_url = config.get('step_api_test', 'url')
    return api_key, api_url

# 从配置文件读取
STEP_API_KEY, BASE_URL = read_config()

# 模型与推理格式设置
COMPLETION_MODEL = "step-3"
REASONING_FORMAT = "deepseek-style"  # 可选 "general" 或 "deepseek-style"
user_prompt = "帮我看看这是什么菜，如何制作？"

# 将本地图片转换为 base64 字符串
def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

image_path1 = "../img/宫保鸡丁.png"
bstring1 = image_to_base64(image_path1)

# 构造聊天消息
messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{bstring1}",
                    "detail": "high"
                }
            },
            {
                "type": "text",
                "text": user_prompt
            }
        ]
    }
]

# 开始计时
time_start = time.time()

# 构造请求
url = f"{BASE_URL}/chat/completions"
headers = {
    "Authorization": f"Bearer {STEP_API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}
payload = {
    "model": COMPLETION_MODEL,
    "messages": messages,
    "reasoning_format": REASONING_FORMAT,
    "stream": True
}

# 发送请求
try:
    resp = requests.post(url, headers=headers, json=payload, stream=True, timeout=60)
except requests.RequestException as e:
    print("请求 API 时发生异常:", e)
    exit(1)

# 检查状态码
if resp.status_code != 200:
    print(f"请求失败，状态码：{resp.status_code}")
    try:
        err = resp.json()
        print("错误详情：", json.dumps(err, ensure_ascii=False, indent=2))
    except Exception:
        print("无法解析错误响应。")
    exit(1)

# 强制使用 UTF-8 解码，避免中文乱码
resp.encoding = 'utf-8'

# 提取并打印 Trace ID
trace_id = resp.headers.get("X-Trace-ID")
if trace_id:
    print(f"Trace ID: {trace_id}")
else:
    print("未能提取到 Trace ID。")

print("---------- 开始输出流式结果 ----------")

# 流式打印每一行
try:
    for raw in resp.iter_lines(decode_unicode=False):
        if not raw:
            continue
        try:
            line = raw.decode('utf-8')
        except UnicodeDecodeError:
            # 出现意外编码时，用 replacement 方式避免异常
            line = raw.decode('utf-8', errors='replace')
        print(line)
except Exception as e:
    print("处理流式结果时发生错误:", e)

# 打印总耗时
time_end = time.time()
print(f"\n总生成时间: {time_end - time_start:.2f} 秒")