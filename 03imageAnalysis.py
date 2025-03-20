from openai import OpenAI
import configparser
import time
import base64
import requests

#读取配置文件
def read_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    # 读取API配置/测试环境将step_api_prod换成step_api_test即可
    api_key = config.get('step_api_prod', 'key')
    api_url = config.get('step_api_prod', 'url')
    return api_key,api_url
STEP_API_KEY,BASE_URL = read_config()

# 初始化
client = OpenAI(api_key=STEP_API_KEY,base_url=BASE_URL)
# 选择模型
#COMPLETION_MODEL = "step-1-flash"
#COMPLETION_MODEL = "step-1-8k"
#COMPLETION_MODEL = "step-1-32k"
#COMPLETION_MODEL = "step-1-128k"
#COMPLETION_MODEL = "step-1-256k"
COMPLETION_MODEL = "step-1v-8k"
#COMPLETION_MODEL = "step-1v-32k"
#COMPLETION_MODEL = "step-2-16k-nightly"
#COMPLETION_MODEL = "step-1x-medium"

sys_prompt = """你是由阶跃星辰提供的AI图像分析师，善于图片分析，可以分析图片中的文字，地址，建筑，人物，动物，食物，植物等结构清晰的物品。
"""
user_prompt = """
请从下面pdf中提取用户的First Name和Last name, Filing Status, digital asset，
Income 1h, Income 1a, Income 1z, Income 8, Income 9, Income 10, Income 11, Income 12, Income 14, Refund 35a, Firms EIN, Preparer's name
"""

#user_prompt = "你好，请介绍一下阶跃星辰的人工智能！"

#######读取本地图片文件，并转换为base64编码########
def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    return encoded_string.decode('utf-8')
#
image_path1 = "img/图1.jpg"
image_path2 = "img/图2.jpg"
# image_path3 = "img/图3.png"
# image_path4 = "img/图4.jpg"
# image_path5 = "img/图表1.jpg"
# image_path6 = "img/病例.jpg"

bstring1 = image_to_base64(image_path1)
bstring2 = image_to_base64(image_path2)
# bstring3 = image_to_base64(image_path3)
# bstring4 = image_to_base64(image_path4)
# bstring5 = image_to_base64(image_path5)
# bstring6 = image_to_base64(image_path6)

messages = [
          # {"role": "system", "content": sys_prompt},
          {"role": "user", "content":
              [
                  {"type": "image_url", "image_url": {"url": "data:image/jpg;base64,%s" % (bstring1)}},
                  {"type": "image_url", "image_url": {"url": "data:image/jpg;base64,%s" % (bstring2)}},
                  # {"type": "image_url", "image_url": {"url": "data:image/png;base64,%s" % (bstring3)}},
                  # {"type": "image_url", "image_url": {"url": "data:image/jpg;base64,%s" % (bstring4)}},
                  # {"type": "image_url", "image_url": {"url": "data:image/jpg;base64,%s" % (bstring5),"detail": "high"}},
                  # {"type": "image_url", "image_url": {"url": "data:image/jpg;base64,%s" % (bstring6),"detail": "high"}},
                  # {"type": "text", "text": "请解析图片里包含的信息，包含文字和风格类型等。"}
                  {"type": "text", "text": user_prompt}
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
response = client.chat.completions.create(
    messages=messages,
    model=COMPLETION_MODEL,
    stream=True
)
#message = response.choices[0].message.content
# print(response)
i=0
for chunk in response:
    i += 1
    #print(chunk.choices[0])
    #print(chunk.choices[0].delta.dict())
    #print(chunk.choices[0].message.content)
    print(chunk.choices[0].delta.content,end='')
    if i == 1:
        time_firstWord = time.time()
        elapsed_time= time_firstWord-time_start
        print(f"首字生成时间: {elapsed_time:.2f} 秒")
time_end = time.time()
elapsed_time = time_end - time_start
print("\n当前模型为",COMPLETION_MODEL)
print(f"总生成时间: {elapsed_time:.2f} 秒")