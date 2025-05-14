from openai import OpenAI
import configparser
import time

#读取配置文件
def read_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    # 读取API配置/测试环境将step_api_prod换成step_api_test即可
    api_key = config.get('step_api_test', 'key')
    api_url = config.get('step_api_test', 'url')
    return api_key,api_url
STEP_API_KEY,BASE_URL = read_config()

# 初始化
client = OpenAI(api_key=STEP_API_KEY,base_url=BASE_URL)
# 必填-选择模型
#COMPLETION_MODEL = "step-1-flash"
COMPLETION_MODEL = "step-sys-1"
#COMPLETION_MODEL = "step-1-32k"
#COMPLETION_MODEL = "step-1-128k"
#COMPLETION_MODEL = "step-1-256k"
#COMPLETION_MODEL = "step-1v-8k"
#COMPLETION_MODEL = "step-1v-32k"
#COMPLETION_MODEL = "step-2-16k-nightly"
#COMPLETION_MODEL = "step-1x-medium"

sys_prompt = """你是由阶跃星辰提供的AI聊天助手，你擅长中文，英文，以及多种其他语言的对话。在保证用户数据安全的前提下，你能对用户的问题和请求，
作出快速和精准的回答。同时，你的回答和建议应该拒绝黄赌毒，暴力恐怖主义的内容。
"""
user_prompt = "你好，请介绍一下阶跃星辰的人工智能！"
#必填-信息
messages = [
    {
        "role": "system",
        "content": sys_prompt
    },
    {
        "role": "user",
        "content": user_prompt
    }
]
time_start = time.time()
# 实现文本补全
response = client.chat.completions.create(
    messages=messages,
    model=COMPLETION_MODEL,
    stream=True,
)
#message = response.choices[0].message.content
i=0
for chunk in response:
    i += 1
    #print(chunk.choices[0])
    #print(chunk.choices[0].delta.dict())
    #print(chunk.choices[0].message.content)
    print(chunk.choices[0].delta.content.strip(),end="")
    if i == 1:
        time_firstWord = time.time()
        elapsed_time= time_firstWord-time_start
        print(f"首字生成时间: {elapsed_time:.2f} 秒")
time_end = time.time()
elapsed_time = time_end - time_start
print("\n当前模型为",COMPLETION_MODEL)
print(f"总生成时间: {elapsed_time:.2f} 秒")