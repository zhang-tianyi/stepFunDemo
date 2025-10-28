from openai import OpenAI
import os
import time
import base64
import requests
import json

STEP_API_KEY = os.environ["STEPFUN_API_KEY"]
BASE_URL= os.environ['STEPFUN_ENDPOINT']

# 初始化
client = OpenAI(api_key=STEP_API_KEY,base_url=BASE_URL)
# 选择模型
#COMPLETION_MODEL = "step-1-flash"
# COMPLETION_MODEL = "step-1v-8k"
#COMPLETION_MODEL = "step-1-32k"
#COMPLETION_MODEL = "step-1-128k"
#COMPLETION_MODEL = "step-1-256k"
COMPLETION_MODEL = "step-1o-vision-32k"
# COMPLETION_MODEL = "step-1o-turbo-vision"
# COMPLETION_MODEL = "step-3"
#COMPLETION_MODEL = "step-1v-32k"
#COMPLETION_MODEL = "step-1x-medium"

sys_prompt = """你是由阶跃星辰提供的AI图像分析师，善于图片分析，可以分析图片中的文字，地址，建筑，人物，动物，食物，植物等结构清晰的物品。
"""
# sys_prompt = """
#
# """

user_prompt = """
你看到看到了几张图，分别是什么内容
"""

#######读取本地图片文件，并转换为base64编码########
def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    return encoded_string.decode('utf-8')

# image_path1 = "../img/图1.jpg"
# image_path2 = "../img/图2.jpg"
# image_path3 = "../img/图3.png"
# image_path4 = "img/图4.jpg"
# image_path5 = "img/图表1.jpg"
image_path6 = "./病例.jpeg"

# bstring1 = image_to_base64(image_path1)
# bstring2 = image_to_base64(image_path2)
# bstring3 = image_to_base64(image_path3)
# bstring4 = image_to_base64(image_path4)
# bstring5 = image_to_base64(image_path5)
bstring6 = image_to_base64(image_path6)

messages = [
          # {"role": "system", "content": sys_prompt},
          {"role": "user", 
           "temprature": 0,
           "content":
              [
                #   {"type": "image_url", "image_url": {"url": "data:image/jpg;base64,%s" % (bstring1),"detail": "high"}},
                #   {"type": "image_url", "image_url": {"url": "data:image/jpg;base64,%s" % (bstring2)}},
                #   {"type": "image_url", "image_url": {"url": "data:image/png;base64,%s" % (bstring3)}},
                # {"type": "image_url", "image_url": {"url": "data:image/jpg;base64,%s" % (bstring4)}},
                # {"type": "image_url", "image_url": {"url": "data:image/jpg;base64,%s" % (bstring5),"detail": "high"}},
                # {"type": "image_url", "image_url": {"url": "data:image/jpg;base64,%s" % (bstring6),"detail": "high"}},
                {"type": "image_url", "image_url": {"url": "data:image/jpg;base64,%s" % (bstring6),"detail": "low"}},
                {"type": "text", "text": "图片分析"}
                # {"type": "text", "text": "请解析图片里包含的信息，包含文字和风格类型等。"}
                #   {"type": "text", "text": user_prompt}
              ]
           }
]

####################读取在线图片并解析###########################
# messages = [
#         # {"role": "system", "content": sys_prompt},
#         {"role": "user", "content":[
#             # {"type": "image_url", "image_url": {"url": "https://www3.autoimg.cn/cardfs/product/g32/M0A/1D/67/1488x0_1_autohomecar__ChxkPWaOQlyAWXj9ADlcMrFdh1s800.jpg"}},
#             # {"type": "image_url", "image_url": {"url": "https://pics0.baidu.com/feed/810a19d8bc3eb135550e9a94456ee5ddfc1f4456.jpeg@f_auto?token=259ca4ea4c4790d1af236aa47d32637d"}},
#             # {"type": "image_url", "image_url": {"url": "https://storage.wanyol.com/text2img/llm_chat_pic/20240820/1275411797365510144.jpg?AWSAccessKeyId=zWzbylLJz1hliqj6Xcvh9XqAWiHqxc5JJ_PgCLiw&Expires=1724728268&Signature=fm5EYvqE30yDt41Qb7Qzd3oOy98%3"}},
#             {"type": "image_url", "image_url": {"url": "https://upload.dify.ai/files/bca64c95-633e-40c6-89b9-58c5e12a4ab1/image-preview?timestamp=1724229032&nonce=f9e7e20da1e8b62c3e12427b76072050&sign=xlXObXQgnjaQwHwGvx9yEMwm9IAsGpgo7h4BtukOMB0="}},
#             {"type": "text", "text": user_prompt}]
#          }
#     ]
time_start = time.time()

# 使用requests直接发送请求
url = f"{BASE_URL}/chat/completions"
headers = {
    "Authorization": f"Bearer {STEP_API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

payload = {
    "model": COMPLETION_MODEL,
    "messages": messages,
    # "response_format": {"type": "json_object"},
    "stream": True
}

time_start = time.time()
response = requests.post(url, headers=headers, json=payload, stream=True)

# 打印TraceID（注意实际header key可能需要调整）
traceid = response.headers.get('Trace-ID') or response.headers.get('X-Trace-ID')
print(f"Trace ID: {traceid}")
print(response)
# 流式处理
time_first_word = None
content_buffer = ""
i = 0

for chunk in response.iter_lines():
    # 过滤心跳包
    if chunk:
        decoded = chunk.decode('utf-8')

        # 处理结束标记
        if decoded == "data: [DONE]":
            break

        # 处理有效数据块
        if decoded.startswith("data: "):
            json_str = decoded[6:].strip()

            try:
                data = json.loads(json_str)
                if data.get("object") == "chat.completion.chunk":
                    # 提取内容
                    content = data['choices'][0]['delta'].get('content', '')

                    # 首字时间记录
                    if content and time_first_word is None:
                        time_first_word = time.time()
                        print(f"\n首字生成时间: {time_first_word - time_start:.2f}秒")

                    # 累积输出内容
                    if content:
                        content_buffer += content
                        i += 1
                        print(content, end='', flush=True)

            except json.JSONDecodeError as e:
                print(f"\nJSON解析错误: {e}")
            except KeyError as e:
                print(f"\n键值缺失: {e}")

# 最终计时
time_end = time.time()
print(f"\n\n总生成时间: {time_end - time_start:.2f}秒")
print(f"当前模型: {COMPLETION_MODEL}")
print(f"总生成字数: {i}字")