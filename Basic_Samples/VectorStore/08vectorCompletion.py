from openai import OpenAI
import os

STEP_API_KEY = os.environ["STEPFUN_API_KEY"]
BASE_URL= os.environ['STEPFUN_ENDPOINT']

# 初始化
client = OpenAI(api_key=STEP_API_KEY, base_url=BASE_URL)
# 选择模型
COMPLETION_MODEL = "step-1-32k"

sys_prompt = """
你是一名食物营养成分专家。
你的任务是识别文本中的每一份食物，并根据以下分类规则预估它们的重量和热量、营养成本（碳水化合物、蛋白质、脂肪），并按「输出格式」进行最后结果的输出。
## 理解食物
1.我会给你一段文字，请识别文字中的食物
2.根据食物的名称，去检索食物的营养成分
4.如果检索后，上下文没有对应食物的营养成分，则直接在食物名称后加上「营养成分未知」，然后输出结果
## 输出格式（请仅输出以下内容，不要说任何多余的话）
1.如果检索出了食物的营养成分，则直接输出以下内容
食物名称：预计每100g的热量（大卡）,碳水化合物（g）,蛋白质（g）,脂肪（g）
2.如果没有检索出了食物的营养成分，则直接输出以下内容
食物名称：营养成分未知
"""
user_prompt = "西红柿鸡蛋面,巧克力泡芙"

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
            "description": "这个web_search用来搜索互联网的信息"
        }
    },
    {
        "type": "retrieval",
        "function": {
            "name": "food_nutrition",
            "description": "本文档存储了食物的营养成分，包含：食物名称,预估重量（g）,热量（大卡）,碳水化合物（g）,蛋白质（g）,脂肪（g）等信息",  # 知识库的描述
            "options": {
                "vector_store_id": "274822495852478464",  # 知识库 ID
                "prompt_template": "从文档 {{knowledge}} 中找到问题 {{query}} 的答案。根据文档内容中的语句找到答案，如果文档中没用答案则告诉用户找不到相关信息；"
            }
        }
    }

]
response = client.chat.completions.create(
    messages=messages,
    model=COMPLETION_MODEL,
    tool_choice="auto",
    tools=tools,
    # stream=True,
)
# print(response)

for chunk in response:
    print(chunk)
