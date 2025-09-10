from openai import OpenAI
import time
import base64
import os

# 推理模型最佳实践
# ref：https://platform.stepfun.com/docs/guide/reasoning#%E8%8E%B7%E5%8F%96-reasoning-%E5%86%85%E5%AE%B9

STEP_API_KEY = os.environ["STEPFUN_API_KEY"]
BASE_URL= os.environ['STEPFUN_ENDPOINT']

# 初始化
client = OpenAI(api_key=STEP_API_KEY,base_url=BASE_URL)
# 必填-选择模型
COMPLETION_MODEL = "step-3"
#COMPLETION_MODEL = "step-1-32k"
#COMPLETION_MODEL = "step-1-256k"
#COMPLETION_MODEL = "step-1v-mini"
#COMPLETION_MODEL = "step-2-16k"
#COMPLETION_MODEL = "step-2-mini"

# 将本地图片转换为 base64 字符串
def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    return encoded_string.decode('utf-8')
 
# 注意提供准确的图片路径
image_path1 = "./media/鱼香肉丝.jpg"
bstring1 = image_to_base64(image_path1)

# content为multipart消息列表 
sys_prompt = """你是由阶跃星辰提供的AI聊天助手，你擅长中文，英文，以及多种其他语言的对话。在保证用户数据安全的前提下，你能对用户的问题和请求，
作出快速和精准的回答。同时，你的回答和建议应该拒绝黄赌毒，暴力恐怖主义的内容。
"""
user_prompt = "帮我看看这是什么菜，如何制作？"
messages = [
    {"role": "user", "content": [
        {"type": "image_url", "image_url": {"url": f"data:image/jpg;base64,{bstring1}", "detail": "high"}},
        {"type": "text", "text": user_prompt}
    ]}
]

# content为普通文本消息
# messages = [{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_prompt}]

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
    # print(chunk)
    #print(chunk.choices[0])
    if hasattr(chunk.choices[0].delta, 'reasoning'):
        reasoning = chunk.choices[0].delta.reasoning
        print("模型思考过程:", reasoning)
    else:
        print(chunk.choices[0].delta.content.strip(),end="")
    if i == 1:
        time_firstWord = time.time()
        elapsed_time= time_firstWord-time_start
        print(f"首字生成时间: {elapsed_time:.2f} 秒")
time_end = time.time()
elapsed_time = time_end - time_start
print("\n当前模型为",COMPLETION_MODEL)
print(f"总生成时间: {elapsed_time:.2f} 秒")