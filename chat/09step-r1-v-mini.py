import configparser
import time
import base64
import requests
import json


# 辅助函数：尝试在 buffer 前 width 个字符内找到合适的断行位置
def flush_reasoning_line(buffer, width=40, threshold=5):
    """
    参数:
      buffer: 待处理的字符串
      width: 指定每行最大字符数
      threshold: 至少保留多少个字符之后再允许断行
    返回:
      一个 tuple(line, remaining)，line 为本次分割出的行，remaining 为剩余字符串
    """
    if len(buffer) < width:
        return None, buffer

    punctuation = "，。；、！？“”‘’"  # 可扩展其它中文标点
    candidate_idx = -1
    for i in range(width - 1, threshold - 1, -1):
        if buffer[i] in punctuation:
            candidate_idx = i
            break
    if candidate_idx != -1:
        line = buffer[:candidate_idx + 1]
        remaining = buffer[candidate_idx + 1:]
    else:
        line = buffer[:width]
        remaining = buffer[width:]
    return line, remaining


# 读取配置文件
def read_config():
    config = configparser.ConfigParser()
    config.read('../config.ini')
    # 读取 API 配置；测试环境将 step_api_prod 换成 step_api_test 即可
    api_key = config.get('step_api_prod', 'key')
    api_url = config.get('step_api_prod', 'url')
    return api_key, api_url


STEP_API_KEY, BASE_URL = read_config()

# 选择模型
COMPLETION_MODEL = "step-r1-v-mini"

# 用户问题提示
user_prompt = "帮我看看这是哪里？"


# 将本地图片转换为 base64 字符串
def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    return encoded_string.decode('utf-8')


image_path1 = "../img/图1.jpg"
bstring1 = image_to_base64(image_path1)

# 构造消息，依靠模型自主深度思考
messages = [
    {"role": "user", "content": [
        {"type": "image_url", "image_url": {"url": "data:image/jpg;base64,%s" % bstring1, "detail": "high"}},
        {"type": "text", "text": user_prompt}
    ]}
]

time_start = time.time()

# 使用 requests 调用 API，设置请求参数
url = f"{BASE_URL}/chat/completions"
headers = {
    "Authorization": f"Bearer {STEP_API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}
payload = {
    "model": COMPLETION_MODEL,
    "messages": messages,
    "stream": True
}

try:
    response = requests.post(url, headers=headers, json=payload, stream=True, timeout=60)
    # 检查 HTTP 状态码
    if response.status_code != 200:
        print(f"请求失败，状态码：{response.status_code}")
        # 如果服务器返回了错误详情，尝试解析并打印
        try:
            error_info = response.json()
            print("错误详情:", json.dumps(error_info, ensure_ascii=False, indent=2))
        except Exception as e:
            print("解析错误详情失败:", e)
        exit(1)
except requests.RequestException as e:
    print(f"请求 API 时发生异常：{e}")
    exit(1)

# 打印 Trace ID（如果响应头中返回）
traceid = response.headers.get('X-Trace-ID')
print(f"Trace ID: {traceid}")

reasoning_header_printed = False  # 标记是否已打印 [思考过程] 标签
reasoning_buffer = ""  # 累积 reasoning 字符串
word_count = 0

# 流式处理响应数据
try:
    for chunk in response.iter_lines():
        if chunk:
            decoded = chunk.decode('utf-8')
            if decoded == "data: [DONE]":
                break
            if decoded.startswith("data: "):
                json_str = decoded[6:].strip()
                try:
                    data = json.loads(json_str)
                    if data.get("object") == "chat.completion.chunk":
                        delta = data['choices'][0]['delta']

                        # 处理 reasoning 信息，流式输出时尝试按每行40个字符分割
                        if "reasoning" in delta:
                            reasoning_chunk = delta.get("reasoning", "")
                            if reasoning_chunk:
                                if not reasoning_header_printed:
                                    print("\n\n[思考过程]:")
                                    reasoning_header_printed = True
                                reasoning_buffer += reasoning_chunk  # 累加，不插入额外空格
                                while len(reasoning_buffer) >= 40:
                                    line, reasoning_buffer = flush_reasoning_line(reasoning_buffer, width=40)
                                    if line:
                                        print(line)

                        # 获取实际输出的 content 内容并实时打印
                        content = delta.get("content", "")
                        if content:
                            print(content, end='', flush=True)
                            word_count += len(content)
                except json.JSONDecodeError as e:
                    print(f"\nJSON解析错误: {e}")
                except KeyError as e:
                    print(f"\n键值缺失: {e}")
except Exception as e:
    print(f"\n处理响应流时发生异常: {e}")

# 如果 reasoning_buffer 中还有未满40个字符的剩余内容，也输出
if reasoning_buffer:
    print(reasoning_buffer)

time_end = time.time()
print(f"\n\n总生成时间: {time_end - time_start:.2f}秒")
print(f"当前模型: {COMPLETION_MODEL}")
print(f"总生成字数: {word_count}")