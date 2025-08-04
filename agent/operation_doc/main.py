# operation_doc_generator.py

import os, glob, time, base64, requests, json, configparser
from PIL import Image, ImageDraw, ImageFont
from prompts import SYSTEM_PROMPT  # 从 prompts.py 导入

# ------------------ 配置区域（集中管理） ------------------
CONFIG_FILE = '../../config.ini'            # 配置文件路径
CONFIG_SECTION = 'step_api_prod'            # config.ini 中使用的节(section)
USER_PROMPT = "帮我生成操作指引？"  # 用户提示内容
COMPLETION_MODEL = "step-1o-vision-32k"                 # 调用的模型名称 可以选择推理模型step-3
REASONING_FORMAT = "general"         # 推理格式，可选 "general" 或 "deepseek-style"

INPUT_PATH = "../../img/generateDoc"       # 输入：单张图片或图片目录
OUTPUT_DIR = "./img_processed"              # 处理后图片保存目录

BORDER_HEIGHT = 50                          # 图片上方黑边高度（像素）
FONT_SIZE = 48                              # 边框文字大小
# 支持中文的字体文件路径（macOS 示例），可改为你本地可用的 ttf/ttc
FONT_PATH = "/System/Library/Fonts/STHeiti Medium.ttc"
# ---------------------------------------------------------

def read_config():
    """
    从 config.ini 中读取 API KEY 和 Base URL
    """
    cfg = configparser.ConfigParser()
    cfg.read(CONFIG_FILE)
    key = cfg.get(CONFIG_SECTION, 'key')
    url = cfg.get(CONFIG_SECTION, 'url')
    return key, url

def image_to_base64(path):
    """
    将本地图片读为 base64 编码字符串
    """
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

def collect_images(path):
    """
    收集输入路径下的所有图片文件。支持单文件或目录扫描。
    返回排序后的图片路径列表。
    """
    if os.path.isfile(path):
        return [path]
    if os.path.isdir(path):
        exts = ('*.jpg','*.jpeg','*.png','*.bmp','*.gif')
        imgs = []
        for e in exts:
            imgs += glob.glob(os.path.join(path, e))
        return sorted(imgs)
    raise FileNotFoundError(f"找不到路径：{path}")

def annotate_image(src, dst, label, border_h, font):
    """
    在原图上方添加黑色边框，并在边框中央写入 label。
    src: 源图片路径
    dst: 目标图片路径
    label: 要写入的文字 (如 "第 1 张图")
    border_h: 边框高度 (像素)
    font: PIL ImageFont 对象
    """
    img = Image.open(src)
    w, h = img.size
    new_h = h + border_h
    new_img = Image.new("RGB", (w, new_h), (0, 0, 0))
    new_img.paste(img, (0, border_h))
    draw = ImageDraw.Draw(new_img)
    bbox = draw.textbbox((0, 0), label, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (w - tw) // 2
    y = (border_h - th) // 2
    draw.text((x, y), label, fill=(255, 255, 255), font=font)
    new_img.save(dst)

def main():
    # 1. 读取 API 配置
    STEP_API_KEY, BASE_URL = read_config()

    # 2. 收集图片
    imgs = collect_images(INPUT_PATH)
    if not imgs:
        print("未找到任何图片，退出。")
        return

    # 3. 准备输出目录
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 4. 加载字体，优先使用指定中文字体
    if FONT_PATH and os.path.isfile(FONT_PATH):
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    else:
        font = ImageFont.load_default()

    # 5. 处理图片：添加黑边并标注序号 → 转 base64
    b64_list = []
    for idx, path in enumerate(imgs, 1):
        name = os.path.basename(path)
        dst = os.path.join(OUTPUT_DIR, f"proc_{idx:03d}_{name}")
        label = f"第 {idx} 张图"
        annotate_image(path, dst, label, BORDER_HEIGHT, font)
        b64_list.append(image_to_base64(dst))
        print(f"已处理并保存：{dst}")

    # 6. 构造消息
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": [
            *[
                {"type": "image_url", "image_url": {
                    "url": f"data:image/jpeg;base64,{b}",
                    "detail": "high"
                }}
                for b in b64_list
            ],
            {"type": "text", "text": USER_PROMPT}
        ]}
    ]

    # 7. 调用 API
    headers = {
        "Authorization": f"Bearer {STEP_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {
        "model": COMPLETION_MODEL,
        "messages": messages,
        "stream": True,
        "reasoning_format": REASONING_FORMAT
    }
    try:
        resp = requests.post(f"{BASE_URL}/chat/completions",
                             headers=headers,
                             json=payload,
                             stream=True,
                             timeout=60)
        resp.raise_for_status()
    except Exception as e:
        print("请求失败：", e)
        return

    # 打印 Trace ID 便于问题定位
    traceid = resp.headers.get("X-Trace-ID")
    print(f"Trace ID: {traceid}")

    # 8. 流式打印响应
    buf = ""
    header_printed = False
    for chunk in resp.iter_lines():
        if not chunk:
            continue
        txt = chunk.decode('utf-8')
        if txt == "data: [DONE]":
            break
        if txt.startswith("data: "):
            data = json.loads(txt[6:])
            delta = data['choices'][0]['delta']
            # 输出思考过程
            rch = delta.get("reasoning_content" if REASONING_FORMAT == "deepseek-style" else "reasoning", "")
            if rch:
                if not header_printed:
                    print("\n[思考过程]:")
                    header_printed = True
                buf += rch
                if "\n" in buf:
                    for line in buf.split("\n")[:-1]:
                        print(line)
                    buf = buf.split("\n")[-1]
            # 输出模型回答
            cont = delta.get("content", "")
            if cont:
                print(cont, end="", flush=True)

    print("\n\n-- 完成 --")

if __name__ == "__main__":
    main()