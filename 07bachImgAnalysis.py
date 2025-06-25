import os
import configparser
import time
import base64
from openai import OpenAI

SUPPORTED_IMAGE_TYPES = {
    '.jpg': 'jpeg',
    '.jpeg': 'jpeg',
    '.png': 'png',
    '.gif': 'gif',
    '.webp': 'webp',
}

def read_config(config_file='config.ini'):
    print(f"[1] 开始读取配置文件：{config_file}")
    config = configparser.ConfigParser()
    config.read(config_file)
    api_key = config.get('step_api_prod', 'key')
    api_url = config.get('step_api_prod', 'url')
    print(f"[2] 读取到 API_KEY 长度 {len(api_key)}，API_URL：{api_url}")
    return api_key, api_url

def get_image_paths(input_path, max_images=50):
    print(f"[3] 开始扫描路径：{input_path}（最多 {max_images} 张）")
    if os.path.isdir(input_path):
        files = sorted(os.listdir(input_path))
        images = []
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in SUPPORTED_IMAGE_TYPES:
                path = os.path.join(input_path, f)
                images.append(path)
                print(f"    扫描到第 {len(images)} 张图片：{path}")
                if len(images) >= max_images:
                    break
        print(f"[4] 共找到 {len(images)} 张图片")
        return images
    elif os.path.isfile(input_path):
        ext = os.path.splitext(input_path)[1].lower()
        if ext not in SUPPORTED_IMAGE_TYPES:
            raise ValueError(f"不支持的图片格式: {ext}")
        print(f"[4] 输入为单文件：{input_path}")
        return [input_path]
    else:
        raise ValueError(f"路径无效: {input_path}")

def image_to_data_url(image_path):
    print(f"[5] 编码图片为 data URL：{image_path}")
    ext = os.path.splitext(image_path)[1].lower()
    mime_subtype = SUPPORTED_IMAGE_TYPES.get(ext)
    if not mime_subtype:
        raise ValueError(f"不支持的图片格式: {ext}")
    with open(image_path, 'rb') as f:
        data = base64.b64encode(f.read()).decode('utf-8')
    return f"data:image/{mime_subtype};base64,{data}"

if __name__ == '__main__':
    start_time = time.time()
    STEP_API_KEY, BASE_URL = read_config()
    client = OpenAI(api_key=STEP_API_KEY, base_url=BASE_URL)
    MODEL = 'step-1o-turbo-vision'

    sys_prompt = """
你是一个电商商品信息提取专家。请阅读用户提供的商品促销图片，提取并整理出规范化的商品信息。

请按以下分组提取内容，并用标准JSON格式输出。各字段说明如下：
	•	基础属性：提取商品的名称、型号、基本参数、尺寸、重量、颜色、包装清单、制造商、生产日期等与商品物理属性直接相关的信息。
	•	使用说明：提取适用人群、适用场景、安装方式、使用或操作指南等内容。
	•	功能卖点：提取专利技术、核心性能参数、智能功能、连接方式、实际使用场景优势等描述。
	•	品牌信息：提取品牌名称、认证标识、获奖记录等品牌相关信息。
	•	安全信息：提取质检标准、使用注意事项等安全相关信息。
	•	售后服务：提取保修政策、退换货政策、客服联系方式等售后服务信息。
	•	客户评价：提取用户评论摘要、平均评分等客户反馈信息。
	•	价格信息：提取市场价、优惠价、促销活动等价格相关信息。

要求：
	•	只提取图片中明确出现的信息，不要根据常识推测或自行补充内容。
	•	如果某部分图片中没有对应信息，输出字段值为空字符串""。
	•	保持语言简洁准确，尽量保留图片上的原始描述。
	•	输出只包含标准JSON，不附加其他解释或回答。

【开始提取】
    """
    user_prompt = "请根据要求分析图片并输出产品信息给我"

    input_path = 'img/food'
    image_paths = get_image_paths(input_path, max_images=50)
    if not image_paths:
        raise RuntimeError(f"在路径 {input_path} 下未找到任何支持的图片格式。")

    print("[6] 构造消息内容列表中")
    content_items = [{'type': 'text', 'text': user_prompt}]
    for idx, img in enumerate(image_paths, 1):
        data_url = image_to_data_url(img)
        content_items.append({
            'type': 'image_url',
            'image_url': {'url': data_url, 'detail': 'high'}
        })
        print(f"    已加入第 {idx} 张图片")
    print(f"[7] 消息列表构建完成，共 {len(content_items)} 项")

    messages = [
        {'role': 'system', 'content': sys_prompt},
        {'role': 'user', 'content': content_items}
    ]

    print("[8] 开始发送请求到模型", MODEL)
    start_request = time.time()
    response = client.chat.completions.create(
        messages=messages,
        model=MODEL,
        stream=True
    )

    print("[9] 请求已发送，开始接收流式响应")
    first_token = True
    first_chunk = True
    for chunk in response:
        if first_chunk:
            print(f"响应 ID: {chunk.id}")
            first_chunk = False
        delta = chunk.choices[0].delta.content or ''
        print(delta, end='', flush=True)
        if first_token and delta.strip():
            elapsed = time.time() - start_request
            print(f"\n首字生成时间: {elapsed:.2f} 秒")
            first_token = False

    total_request = time.time() - start_request
    total = time.time() - start_time
    print(f"\n模型 {MODEL} 响应接收完毕，用时 {total_request:.2f} 秒")
    print(f"脚本总耗时: {total:.2f} 秒")