from openai import OpenAI
import configparser
import time

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
COMPLETION_MODEL = "step-1-8k"
#COMPLETION_MODEL = "step-1-32k"
#COMPLETION_MODEL = "step-1-128k"
#COMPLETION_MODEL = "step-1-256k"
#COMPLETION_MODEL = "step-1v-8k"
#COMPLETION_MODEL = "step-1v-32k"
#COMPLETION_MODEL = "step-2-16k-nightly"
#COMPLETION_MODEL = "step-1x-medium"

sys_prompt = """每个提问先通过web_search，然后通过web_search的结果，回答用户问题。
"""
user_prompt = "上海最高的楼上海什么楼？请只回答楼的名称，不要包含其他内容。例如：上海金茂大厦。"

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
tools = [
    {
        "type": "web_search",
        "function": {
            "description": "这个web_search函数用来搜索互联网的内容"
        }
    }
]
time_start = time.time()
response = client.chat.completions.create(
    messages=messages,
    model=COMPLETION_MODEL,
    tool_choice="auto",
    tools=tools,
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