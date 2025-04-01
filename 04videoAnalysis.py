import logging
from openai import OpenAI
import configparser
import time
import base64
import requests

# 配置日志输出格式和级别
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 读取配置文件
def read_config():
    logging.info("Reading configuration from config.ini")
    config = configparser.ConfigParser()
    config.read('config.ini')
    # 读取API配置，测试环境将step_api_prod换成step_api_test即可
    api_key = config.get('step_api_prod', 'key')
    api_url = config.get('step_api_prod', 'url')
    logging.info("Configuration loaded: API URL is %s", api_url)
    return api_key, api_url

STEP_API_KEY, BASE_URL = read_config()

# 初始化客户端
client = OpenAI(api_key=STEP_API_KEY, base_url=BASE_URL)
logging.info("Initialized OpenAI client")

# 选择模型（这里选择的是 step-1.5v-mini，可根据需要更换）
COMPLETION_MODEL = "step-1.5v-mini"
logging.info("Using model: %s", COMPLETION_MODEL)

# 系统提示，描述视频分析的角色
sys_prompt = """你是由阶跃星辰提供的AI视频分析师，善于视频分析，可以分析视频中的文字，地址，建筑，人物，动物，食物，植物等结构清晰的物品。"""

# 用户提示（可以根据需求修改）
user_prompt = "请解析视频中的信息，包括文字、场景、人物等。"
logging.info("User prompt set")

# 读取本地视频文件，并转换为 base64 编码
def video_to_base64(video_path):
    logging.info("Converting video at path '%s' to base64", video_path)
    with open(video_path, "rb") as video_file:
        encoded_string = base64.b64encode(video_file.read())
    logging.info("Video conversion completed, base64 string length: %d", len(encoded_string))
    return encoded_string.decode('utf-8')

# 注意：请将 video_path1 修改为你本地视频的正确路径，文件格式建议为 mp4
# video_path1 = "video/video.mp4"
video_path1 = "video/飞书20250319-194119.mp4"
bstring1 = video_to_base64(video_path1)

# 构造消息列表，此处将上传的视频使用 video_url，并指定对应的 MIME 类型
messages = [
    {"role": "system", "content": sys_prompt},
    {"role": "user", "content": [
        {"type": "video_url", "video_url": {"url": "data:video/mp4;base64,%s" % (bstring1)}},
        {"type": "text", "text": user_prompt}
    ]}
]
logging.info("Constructed messages for API request")

time_start = time.time()
logging.info("Sending request to API")
response = client.chat.completions.create(
    messages=messages,
    model=COMPLETION_MODEL,
    stream=True
)

# 输出返回的 header 信息
if hasattr(response, "headers"):
    headers = response.headers
    print("Response Headers:", headers)
    logging.info("Response Headers: %s", headers)
else:
    print("No header information available.")
    logging.info("No header information available.")

i = 0
for chunk in response:
    i += 1
    output = chunk.choices[0].delta.content
    print(output, end='')
    if i == 1:
        time_firstWord = time.time()
        elapsed_time = time_firstWord - time_start
        logging.info("First word generated after %.2f seconds", elapsed_time)
        print(f"\n首字生成时间: {elapsed_time:.2f} 秒")
logging.info("Response streaming complete")
time_end = time.time()
elapsed_time = time_end - time_start
logging.info("Total generation time: %.2f seconds", elapsed_time)
print("\n当前模型为", COMPLETION_MODEL)
print(f"总生成时间: {elapsed_time:.2f} 秒")