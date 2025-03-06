import base64
import configparser
import json
import time
import os
import re
import glob
import argparse

from PIL import Image, ImageDraw, ImageFont
from openai import OpenAI  # 确保使用正确的 OpenAI 库

"""
文件名: 099bachImgAnnoPig.py
功能: 批量或单独标注图像中的猪，生成标注图像。

使用方法:
1. 基本运行:
   使用 Python 解释器运行脚本，并通过命令行参数指定需要处理的图像文件或文件夹。

2. 参数说明:
   - `-f` 或 `--file`:
     指定一个图像文件路径进行单独处理。
     示例: python 099bachImgAnnoPig.py --file /path/to/image.jpg

   - `-d` 或 `--dir`:
     指定一个文件夹路径以批量处理文件夹内的所有图像。
     示例: python 099bachImgAnnoPig.py --dir /path/to/images

   - `-m` 或 `--model`:
     指定使用的模型名称（默认为 'step-1v-8k'）。
     示例: python 099bachImgAnnoPig.py --file /path/to/image.jpg --model step-1v-16k

   - `-c` 或 `--config`:
     指定配置文件路径（默认为 'config.ini'），配置文件中存储 API 的 URL 和密钥。
     示例: python 099bachImgAnnoPig.py --file /path/to/image.jpg --config custom_config.ini

   - `--delay`:
     设置每张图片处理之间的延迟时间（以秒为单位，默认为 1.0）。
     示例: python 099bachImgAnnoPig.py --dir /path/to/images --delay 2.0

3. 示例:
   - 单张图像处理:
     python 099bachImgAnnoPig.py --file /path/to/image.jpg
   - 批量处理文件夹内所有图像:
     python 099bachImgAnnoPig.py --dir /path/to/images
   - 使用自定义模型和配置文件:
     python 099bachImgAnnoPig.py --file /path/to/image.jpg --model step-1v-16k --config custom_config.ini

注意:
1. 该脚本会自动创建输出目录，并将标注后的图像保存至 `output` 子文件夹中。
2. 支持的图像格式包括: `.jpg`, `.jpeg`, `.png`, `.bmp`, `.gif`。
3. 配置文件中需包含 `step_api_prod` 部分，格式如下:
"""

# 读取配置文件
def read_config(config_path='config.ini'):
    config = configparser.ConfigParser()
    config.read(config_path)
    # 读取API配置
    api_key = config.get('step_api_prod', 'key')
    api_url = config.get('step_api_prod', 'url')
    return api_key, api_url


STEP_API_KEY,BASE_URL = read_config()


# 初始化OpenAI客户端
client = OpenAI(api_key=STEP_API_KEY, base_url=BASE_URL)


def remove_leading_zeros(json_str):
    # 正则表达式匹配数组中的数字，去除前导零
    pattern = r'(?<=[\[, ])0+(\d+)'
    corrected_json_str = re.sub(pattern, r'\1', json_str)
    return corrected_json_str


def get_image_size(image_path):
    try:
        with Image.open(image_path) as img:
            return img.size  # 返回 (宽度, 高度)
    except FileNotFoundError:
        print(f"图像文件未找到: {image_path}")
        return None
    except Exception as e:
        print(f"获取图像大小时发生错误: {e}")
        return None


def image_to_base64(image_path):
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        return encoded_string
    except FileNotFoundError:
        print(f"图像文件未找到: {image_path}")
        return None
    except Exception as e:
        print(f"将图像转换为Base64时发生错误: {e}")
        return None


def analyze_image(image_path, model_name, image_size):
    image_base64 = image_to_base64(image_path)
    print("Base64编码的图像:")
    if not image_base64:
        return None

    width, height = image_size

    # 动态生成系统提示，包含实际图像大小
    sys_prompt = f"""
    你是一个图像分析助手。请分析我上传的猪圈图片。
    并以严格的JSON对象格式返回每头猪的信息。JSON对象应包含一个键 "pigs"，其值为一个包含每头猪信息的数组。
    - 编号（id）：猪的编号，字符串类型，例如 "pig1"。
    - 位置（position）：猪在图像中的位置，是一个包含四个不带前导零的整数的数组 [xmin, ymin, xmax, ymax]，表示猪在图像中的左上角和右下角坐标。
    请确保所有坐标在图像范围内，且不带前导零。输出结果仅包含JSON数据，不要包含任何额外的描述或解释。以下是一个示例输出：
    ```json
    {{
        "pigs":
        [
          {{
            "id": "pig1",
            "position": [100, 270, 200, 370]
          }},
          {{
            "id": "pig2",
            "position": [300, 400, 400, 500]
          }}
        ]
    }}
    ```
    请按照上述示例格式返回结果。
    """
    print("系统提示内容:")
    print(sys_prompt)
    user_prompt = "请分析以下Base64编码的图像并返回猪的数量及其位置。"
    messages = [
        {
            "role": "system",
            "content": sys_prompt
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpg;base64,{image_base64}",
                        "detail": "high"
                    }
                },
                {
                    "type": "text",
                    "text": user_prompt
                }
            ]
        }
    ]

    # 发送请求到OpenAI API
    try:
        response = client.chat.completions.create(
            messages=messages,
            model=model_name,  # 使用定义的模型名称
            response_format={"type": "json_object"},
        )
    except Exception as e:
        print(f"API请求失败: {e}")
        return None

    # 确认响应类型
    print(f"响应类型: {type(response)}")
    print(response)

    # 获取API返回内容
    response_content = response.choices[0].message.content.strip().replace('\n', '')

    print("API返回内容:")
    print(response_content)
    try:
        # 解析JSON
        corrected_content = remove_leading_zeros(response_content)
        analysis_result = json.loads(corrected_content)
        # 转换相对坐标为绝对坐标
        for pig in analysis_result.get("pigs", []):
            pos = pig.get("position", [])
            if len(pos) != 4:
                print(f"猪 {pig.get('id', '未知')} 的位置格式不正确: {pos}")
                continue  # 跳过该猪
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
            pig["position"] = [abs_xmin, abs_ymin, abs_xmax, abs_ymax]
        return analysis_result
    except json.JSONDecodeError as e:
        print("解析JSON失败，请检查API返回内容。")
        print("返回内容:", response_content)
        return None


def validate_coordinates(pigs, image_size):
    width, height = image_size
    for pig in pigs:
        pos = pig.get('position', [])
        if len(pos) != 4:
            print(f"{pig.get('id', '未知')} 的位置格式不正确: {pos}")
            return False
        xmin, ymin, xmax, ymax = pos
        if not (0 <= xmin < xmax <= width and 0 <= ymin < ymax <= height):
            print(f"{pig.get('id', '未知')} 的坐标超出图像范围: {pos}")
            return False
    return True


def annotate_image(image_path, pigs, output_path):
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    try:
        with Image.open(image_path) as img:
            draw = ImageDraw.Draw(img)
            try:
                # 提供更通用的字体路径，适用于不同操作系统
                font = ImageFont.truetype("arial.ttf", size=20)
            except IOError:
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size=20)
                except IOError:
                    font = ImageFont.load_default()

            for pig in pigs:
                pig_id = pig.get('id', '未知')
                pos = pig.get('position', [0, 0, 0, 0])
                xmin, ymin, xmax, ymax = pos
                # 计算中间点
                center_x = (xmin + xmax) // 2
                center_y = (ymin + ymax) // 2

                # 绘制10像素直径的绿色圆点
                radius = 5  # 半径为5像素
                left_up_point = (center_x - radius, center_y - radius)
                right_down_point = (center_x + radius, center_y + radius)
                draw.ellipse([left_up_point, right_down_point], fill="green", outline=None)

                # 在圆点右侧显示猪的ID，偏移5像素
                text_position = (center_x + radius + 5, center_y - radius)
                draw.text(text_position, pig_id, fill="blue", font=font)

            img.save(output_path)
            print(f"标注后的图像已保存至 {output_path}")
    except FileNotFoundError:
        print(f"图像文件未找到: {image_path}")
    except Exception as e:
        print(f"标注图像时发生错误: {e}")


def process_image(image_path, model_name):
    print(f"正在处理图像: {image_path}")
    image_size = get_image_size(image_path)
    if not image_size:
        print("无法获取图像大小，跳过此图像。")
        return

    print(f"图像大小: {image_size}")
    max_retries = 5
    attempt = 0

    while attempt < max_retries:
        try:
            analysis_result = analyze_image(image_path, model_name, image_size)
            if not analysis_result:
                print("未能获取有效的分析结果，跳过此图像。")
                return

            pigs = analysis_result.get("pigs", [])

            if not pigs:
                print("未识别到任何猪，请检查图像或API响应，跳过此图像。")
                return

            if validate_coordinates(pigs, image_size):
                # 动态生成输出文件名
                original_name = os.path.splitext(os.path.basename(image_path))[0]
                pig_count = len(pigs)
                # Sanitize model_name to remove any characters that might not be suitable for filenames
                sanitized_model_name = re.sub(r'[\/\\:*?"<>|]', '_', model_name)
                output_filename = f"{original_name}_model-{sanitized_model_name}_pigs-{pig_count}_annotated.jpg"
                output_image_path = os.path.join(os.path.dirname(image_path), "output", output_filename)

                annotate_image(image_path, pigs, output_image_path)
                print(f"识别到 {pig_count} 头猪。")
                break
            else:
                print("坐标超出图像范围，重新识别...")
                attempt += 1
                time.sleep(1)  # 等待一段时间再重试
        except Exception as e:
            print("发生错误:", e)
            attempt += 1
            time.sleep(1)  # 等待一段时间再重试
    else:
        print("达到最大重试次数，操作失败.")


def main():
    parser = argparse.ArgumentParser(description="批量或单独标注猪的图像。")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-f', '--file', type=str, help="指定单个图像文件路径。")
    group.add_argument('-d', '--dir', type=str, help="指定图像文件夹路径。")
    parser.add_argument('-m', '--model', type=str, default="step-1v-8k",
                        help="指定使用的模型名称，默认为 'step-1v-8k'。")
    parser.add_argument('-c', '--config', type=str, default="config.ini",
                        help="指定配置文件路径，默认为 'config.ini'。")
    parser.add_argument('--delay', type=float, default=1.0,
                        help="指定每次处理之间的延时时间（秒），默认为 1.0 秒。")

    args = parser.parse_args()

    # 读取配置文件
    global api_key, api_url, client
    api_key, api_url = read_config(args.config)
    client = OpenAI(api_key=api_key, base_url=api_url)

    model_name = args.model

    if args.file:
        image_path = args.file
        if not os.path.isfile(image_path):
            print(f"指定的文件不存在: {image_path}")
            return
        process_image(image_path, model_name)
    elif args.dir:
        input_folder = args.dir
        if not os.path.isdir(input_folder):
            print(f"指定的文件夹不存在: {input_folder}")
            return

        # 支持的图像格式
        supported_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.gif']

        # 获取所有图像文件
        image_files = []
        for ext in supported_extensions:
            image_files.extend(glob.glob(os.path.join(input_folder, ext)))

        if not image_files:
            print(f"在文件夹 {input_folder} 中未找到任何图像文件。")
            return

        print(f"找到 {len(image_files)} 张图像，开始处理...")

        for image_path in image_files:
            process_image(image_path, model_name)
            # 可选：添加延时以避免过快发送请求
            time.sleep(args.delay)  # 根据需要调整延时时间


if __name__ == "__main__":
    main()