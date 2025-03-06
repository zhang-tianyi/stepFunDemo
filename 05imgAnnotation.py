import base64
import configparser
import json
import time

from PIL import Image, ImageDraw, ImageFont
from openai import OpenAI


# 读取配置文件
def read_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    # 读取API配置/测试环境将step_api_prod换成step_api_test即可
    api_key = config.get('step_api_prod', 'key')
    api_url = config.get('step_api_prod', 'url')
    return api_key, api_url

STEP_API_KEY,BASE_URL = read_config()

# 初始化OpenAI客户端
client = OpenAI(api_key=api_key, base_url=api_url)


def get_image_size(image_path):
    with Image.open(image_path) as img:
        return img.size  # 返回 (宽度, 高度)


def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return encoded_string


def analyze_image(image_path, image_size):
    # 将图像转换为Base64
    image_base64 = image_to_base64(image_path)

    width, height = image_size

    # 动态生成系统提示，包含实际图像大小
    sys_prompt = f"""
    你是一个图像分析助手。请分析我上传的图片。
    并以严格的JSON对象格式返回每道菜品的信息。JSON对象应包含一个键 "dishes"，其值为一个包含每道菜品信息的数组。
    - 名称（name）：菜品名称，字符串类型。
    - 重量预估（weight）：菜品重量，整数类型，单位为克（g）。
    - 位置（position）：菜品在图像中的位置，是一个包含四个整数的数组 [xmin, ymin, xmax, ymax]，表示菜品在图像中的左上角和右下角坐标。

    请确保所有坐标在图像范围内，并且输出结果仅包含JSON数据，不要包含任何额外的描述或解释。以下是一个示例输出：
    ```json
    {{
        "dishes":
        [
          {{
            "name": "salad",
            "weight": 400,
            "position": [100, 270, 758, 769]
          }},
          {{
            "name": "lemon slices",
            "weight": 50,
            "position": [136, 745, 258, 871]
          }}
        ]
    }}
    ```
    请按照上述示例格式返回结果。
    """
    print("系统提示内容:")
    print(sys_prompt)

    user_prompt = "请分析以下Base64编码的图像并返回菜品信息。"

    messages = [
        {
            "role": "system",
            "content": sys_prompt
        },
        {
            "role": "user",
            "content": [
                {"type": "image_url",
                 "image_url": {"url": "data:image/jpg;base64,%s" % image_base64, "detail": "high"}},
                {"type": "text", "text": user_prompt}
            ]
        }
    ]
    # # 打印发送的消息内容
    # import pprint
    # print("发送给 API 的消息内容:")
    # pprint.pprint(messages)

    # 发送请求到OpenAI API
    try:
        response = client.chat.completions.create(
            messages=messages,
            model="step-1v-8k",  # 替换为你实际使用的模型
            response_format={"type": "json_object"},
        )
    except Exception as e:
        print(f"API请求失败: {e}")
        return None

    # 假设API返回的内容在response['choices'][0]['message']['content']
    # response_content = response.choices[0].message.content
    print(response)
    response_content = response.choices[0].message.content.strip()
    print(response_content)
    try:
        # 尝试解析JSON
        analysis_result = json.loads(response_content)
        # 转换相对坐标为绝对坐标
        for dish in analysis_result.get("dishes", []):
            pos = dish.get("position", [])
            if len(pos) != 4:
                print(f"菜品 {dish.get('name', '未知')} 的位置格式不正确: {pos}")
                continue  # 跳过该菜品
            rel_xmin, rel_ymin, rel_xmax, rel_ymax = pos
            abs_xmin = int(rel_xmin / 1000 * width)
            abs_ymin = int(rel_ymin / 1000 * height)
            abs_xmax = int(rel_xmax / 1000 * width)
            abs_ymax = int(rel_ymax / 1000 * height)

            # 确保坐标在图像范围内
            abs_xmin = max(0, min(abs_xmin, width - 1))
            abs_ymin = max(0, min(abs_ymin, height - 1))
            abs_xmax = max(0, min(abs_xmax, width - 1))
            abs_ymax = max(0, min(abs_ymax, height - 1))

            # 更新位置
            dish["position"] = [abs_xmin, abs_ymin, abs_xmax, abs_ymax]
        return analysis_result
    except json.JSONDecodeError as e:
        print("解析JSON失败，请检查API返回内容。")
        print("返回内容:", response_content)
        return None


def validate_coordinates(dishes, image_size):
    width, height = image_size
    for dish in dishes:
        pos = dish.get('position', [])
        if len(pos) != 4:
            print(f"菜品 {dish.get('name', '未知')} 的位置格式不正确: {pos}")
            return False
        xmin, ymin, xmax, ymax = pos
        if not (0 <= xmin < xmax <= width and 0 <= ymin < ymax <= height):
            print(f"菜品 {dish.get('name', '未知')} 的坐标超出图像范围: {pos}")
            return False
    return True


def annotate_image(image_path, dishes, output_path):
    with Image.open(image_path) as img:
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", size=20)
        except IOError:
            font = ImageFont.load_default()

        for dish in dishes:
            name = dish.get('name', '未知')
            pos = dish.get('position', [0, 0, 0, 0])
            xmin, ymin, xmax, ymax = pos
            # 在菜品左上角标注名称
            draw.text((xmin, ymin - 20 if ymin - 20 > 0 else ymin), name, fill="red", font=font)
            # 可选：绘制边界框
            draw.rectangle(pos, outline="red", width=2)

        img.save(output_path)
        print(f"标注后的图像已保存至 {output_path}")


def main():
    input_image_path = "./img/food/菜肴06.jpeg"  # 替换为你的输入图像路径
    output_image_path = "./img/food/output/菜肴06_标注.jpg"  # 替换为你的输出图像路径
    max_retries = 5
    attempt = 0

    image_size = get_image_size(input_image_path)
    print(f"图像大小: {image_size}")

    while attempt < max_retries:
        try:
            analysis_result = analyze_image(input_image_path, image_size)
            if not analysis_result:
                print("未能获取有效的分析结果。")
                return

            # 假设API返回的数据格式如下：
            # {
            #     "dishes": [
            #         {"name": "宫保鸡丁", "weight": 200, "position": [100, 150, 200, 250]},
            #         {"name": "麻婆豆腐", "weight": 150, "position": [300, 400, 400, 500]},
            #         ...
            #     ]
            # }
            dishes = analysis_result.get("dishes", [])

            if not dishes:
                print("未识别到任何菜品，请检查图像或API响应。")
                return

            if validate_coordinates(dishes, image_size):
                annotate_image(input_image_path, dishes, output_image_path)
                break
            else:
                print("坐标超出图像范围，重新识别...")
                attempt += 1
                time.sleep(1)  # 等待一段时间再重试
        except Exception as e:
            print(f"发生错误: {e}")
            attempt += 1
            time.sleep(1)  # 等待一段时间再重试
    else:
        print("达到最大重试次数，操作失败。")


if __name__ == "__main__":
    main()
