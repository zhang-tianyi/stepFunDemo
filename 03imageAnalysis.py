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
# COMPLETION_MODEL = "step-1o-vision-32k"
COMPLETION_MODEL = "step-1o-turbo-vision"
#COMPLETION_MODEL = "step-1v-32k"
#COMPLETION_MODEL = "step-2-16k-nightly"
#COMPLETION_MODEL = "step-1x-medium"

# sys_prompt = """你是由阶跃星辰提供的AI图像分析师，善于图片分析，可以分析图片中的文字，地址，建筑，人物，动物，食物，植物等结构清晰的物品。
# """
sys_prompt = """此问题都是基于店铺巡查监测，需要你分析图片，并给出详细数据；
请将所有结果都以 js 数组格式输出；
如果结果不合格，请给出 不超过50字的点评，并给出理由；
具体输出格式 的 typescript interface 是：
interface Data {
  "name": string; // "检测名-1",
  "success": boolean;
  "message": string;
}
注意直接给出数组，不要其他额外数据结构"""
user_prompt = """
检测名-18：员工玩手机检测
检测内容：你是一个智能店铺巡检系统，分析监控摄像头的图像画面，理解画面中的场景，判断画面中是否有员工存在以及每位员工是否存在违规使用手机的现象：
人物区分：注意区分画面的人物身份（员工、外卖员（多为黄色或蓝色工装）、顾客）。
当判断员工存在时，执行以下操作：
1. 手持设备检测：识别员工手部区域是否持有智能手机（需排除对讲机、扫码枪等工作设备），观察设备屏幕是否处于亮屏状态；
2. 视觉注意力分析：检测员工是否低头注视手部区域；
3. 动作模式识别：判断是否存在单手/双手握持姿势，以及手指滑动、点击等典型触屏操作特征；
使用场景验证：排除合理使用场景（如扫描商品条码、接听工作电话、查看订单信息等），重点监测社交/娱乐行为（视频播放、游戏界面等）；
4. 干扰项排除：区分类似动作（手持笔记录、操作收银键盘、整理票据等），通过设备边缘反光特征、握持角度进行二次校验；
Take a deep breath and work on this problem step-by-step
检测标准：输出二分类结论（合规/不合规）及违规类型； 若检测到员工玩手机则判定为“不合规”；若检测到员工未在场则判定为“合规”，并输出结果为“未有效检测”
"""

#user_prompt = "你好，请介绍一下阶跃星辰的人工智能！"

#######读取本地图片文件，并转换为base64编码########
def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    return encoded_string.decode('utf-8')
#
image_path1 = "img/10-3.jpg"
# image_path2 = "img/图2.jpg"
# image_path3 = "img/图3.png"
# image_path4 = "img/图4.jpg"
# image_path5 = "img/图表1.jpg"
# image_path6 = "img/病例.jpg"

bstring1 = image_to_base64(image_path1)
# bstring2 = image_to_base64(image_path2)
# bstring3 = image_to_base64(image_path3)
# bstring4 = image_to_base64(image_path4)
# bstring5 = image_to_base64(image_path5)
# bstring6 = image_to_base64(image_path6)

messages = [
          {"role": "system", "content": sys_prompt},
          {"role": "user", "content":
              [
                  {"type": "image_url", "image_url": {"url": "data:image/jpg;base64,%s" % (bstring1),"detail": "high"}},
                  # {"type": "image_url", "image_url": {"url": "data:image/jpg;base64,%s" % (bstring2)}},
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