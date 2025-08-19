# -*- coding: utf-8 -*-
"""
图像菜品标注（重构版）
- 变量集中在顶部
- 自动处理 RGBA -> JPEG 铺白
- 支持相对(0~1000)与绝对像素坐标
"""

import os
import base64
import configparser
import json
import time
from typing import List, Dict, Any, Tuple, Optional

from PIL import Image, ImageDraw, ImageFont
from openai import OpenAI

# =========================
# ======= 配置区域 ========
# =========================
# 读取的 config.ini 节点，可切换为 step_api_test
STEP_PROFILE = "step_api_prod"

# OpenAI / Step 模型配置
# MODEL_NAME = "step-1o-turbo-vision"
MODEL_NAME = "step-1o-vision-32k"
RESPONSE_FORMAT_JSON = {"type": "json_object"}

# 坐标模式：
# - "auto"：自动判定（若坐标最大值<=1000 且图像宽/高>1200 之一，则按相对0~1000处理；否则按绝对像素）
# - "relative_0_1000"：强制相对坐标（0~1000）
# - "absolute_px"：强制绝对像素
POSITION_MODE = "relative_0_1000"

# 文件路径
INPUT_IMAGE_PATH = "./img/food/food.png"
OUTPUT_IMAGE_PATH = "./img/food/output"   # 若为 .jpg/.jpeg 会自动铺白
FONT_PATHS = [
    # 优先使用常见字体，按平台尝试
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",  # macOS 常见全字库
    "/System/Library/Fonts/Helvetica.ttc",
    "arial.ttf",
]
FONT_SIZE = 20

# 重试
MAX_RETRIES = 5
RETRY_SLEEP_SECONDS = 1

# 调试输出
VERBOSE = True
# =========================
# ===== 配置区域结束 ======
# =========================


def read_config() -> Tuple[str, str]:
    """读取 STEP API_KEY 与 BASE_URL"""
    config = configparser.ConfigParser()
    config.read('config.ini')
    api_key = config.get(STEP_PROFILE, 'key')
    api_url = config.get(STEP_PROFILE, 'url')
    return api_key, api_url


STEP_API_KEY, BASE_URL = read_config()
client = OpenAI(api_key=STEP_API_KEY, base_url=BASE_URL)


def log(*args):
    if VERBOSE:
        print(*args)


def get_image_size(image_path: str) -> Tuple[int, int]:
    with Image.open(image_path) as img:
        return img.size  # (w, h)


def image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def build_system_prompt() -> str:
    return (
        "你是一个图像分析助手。请分析我上传的图片，并仅标注图中**不同食物**的区域，返回严格的 JSON 对象。\n"
        "【输出要求】\n"
        "1) 仅返回 JSON，不要包含任何额外描述或解释。\n"
        "2) JSON 必须包含键 \"dishes\"，其值为数组；数组中每个元素包含：\n"
        "   - 名称（name）：食物名称，**必须使用中文**（例如：\"沙拉\"、\"炸鸡\"、\"水果拼盘\"）。\n"
        "   - 热量（calories）：该食物在图片中**这一份**的大致卡路里，整数，单位为 kcal。\n"
        "   - 位置（position）：四个整数 [xmin, ymin, xmax, ymax]，表示左上角与右下角坐标。\n"
        "\n"
        "【边界规则】\n"
        "1) 坐标采用**相对坐标制**：范围为 0~1000 的整数（即 0 表示最左/最上，1000 表示最右/最下）。\n"
        "2) 所有坐标必须在图像范围内，且满足 xmin < xmax、ymin < ymax。\n"
        "3) **不同食物的框之间不得重叠**。如可能重叠：\n"
        "   - 优先保留面积更大的、与盘子/容器边界更贴合的框；\n"
        "   - 或者将可能重叠的多个框**合并为一个更大框**（以避免重叠）。\n"
        "\n"
        "【食物定义与去重】\n"
        "1) 若一个盘子/容器里包含多种食物（例如拼盘、便当），将该盘子/容器内的食物**视为一个整体食物**，只输出一个框，名称可概括为中文（如：\"水果拼盘\"、\"便当\"、\"海鲜拼盘\"）。\n"
        "2) 同类/同一盘的重复框只保留一个，避免重复标注。\n"
        "\n"
        "【示例输出】\n"
        "{\n"
        "  \"dishes\": [\n"
        "    {\"name\": \"沙拉\", \"calories\": 380, \"position\": [100, 270, 758, 769]},\n"
        "    {\"name\": \"水果拼盘\", \"calories\": 220, \"position\": [136, 745, 258, 871]}\n"
        "  ]\n"
        "}\n"
        "请严格按上述字段与格式返回结果。"
    )


def call_model(image_b64: str) -> Optional[Dict[str, Any]]:
    sys_prompt = build_system_prompt()
    log("系统提示内容:\n\n", sys_prompt)

    messages = [
        {"role": "system", "content": sys_prompt},
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpg;base64,{image_b64}",
                        "detail": "high",
                    },
                },
                {"type": "text", "text": "请分析以下Base64编码的图像并返回菜品信息。"},
            ],
        },
    ]

    try:
        response = client.chat.completions.create(
            messages=messages,
            model=MODEL_NAME,
            response_format=RESPONSE_FORMAT_JSON,
        )
    except Exception as e:
        log(f"API请求失败: {e}")
        return None

    # 打印完整响应（可按需注释）
    log(response)

    try:
        content = response.choices[0].message.content.strip()
        log(content)
        return json.loads(content)
    except Exception as e:
        log("解析JSON失败，请检查API返回内容。报错：", e)
        return None


def _clamp(v: int, low: int, high: int) -> int:
    return max(low, min(v, high))


def _to_int4(pos: List[Any]) -> Optional[List[int]]:
    if not isinstance(pos, (list, tuple)) or len(pos) != 4:
        return None
    try:
        # 支持 float/str，统一转 int
        iv = [int(round(float(x))) for x in pos]
        return iv
    except Exception:
        return None


def _auto_position_mode(dishes: List[Dict[str, Any]], width: int, height: int) -> str:
    """
    简单启发式：
    - 若所有坐标都在 0~1000 且图像一边>1200，则认为是相对(0~1000)
    - 否则认为是绝对像素
    """
    max_coord = 0
    for d in dishes:
        pos = d.get("position", [])
        iv = _to_int4(pos)
        if not iv:
            continue
        max_coord = max(max_coord, max(iv))
    if max_coord <= 1000 and (width > 1200 or height > 1200):
        return "relative_0_1000"
    return "absolute_px"


def normalize_positions(
    dishes: List[Dict[str, Any]],
    image_size: Tuple[int, int],
    mode: str,
) -> List[Dict[str, Any]]:
    w, h = image_size

    # 自动模式时，先粗判
    eff_mode = mode
    if mode == "auto":
        eff_mode = _auto_position_mode(dishes, w, h)
        log(f"[坐标模式自动判定] -> {eff_mode}")

    out = []
    for d in dishes:
        name = d.get("name", "未知")
        pos_raw = d.get("position", [])
        iv = _to_int4(pos_raw)
        if not iv:
            log(f"菜品 {name} 的位置格式不正确: {pos_raw}")
            continue

        xmin, ymin, xmax, ymax = iv

        if eff_mode == "relative_0_1000":
            # 0~1000 相对坐标换算到像素
            xmin = int(xmin / 1000.0 * w)
            ymin = int(ymin / 1000.0 * h)
            xmax = int(xmax / 1000.0 * w)
            ymax = int(ymax / 1000.0 * h)
        # else: absolute_px 直接使用像素

        # 夹取范围
        xmin = _clamp(xmin, 0, w - 1)
        ymin = _clamp(ymin, 0, h - 1)
        xmax = _clamp(xmax, 0, w - 1)
        ymax = _clamp(ymax, 0, h - 1)

        # 确保左上 < 右下
        if xmax <= xmin:
            xmax = _clamp(xmin + 1, 1, w - 1)
        if ymax <= ymin:
            ymax = _clamp(ymin + 1, 1, h - 1)

        nd = dict(d)
        nd["position"] = [xmin, ymin, xmax, ymax]
        out.append(nd)
    return out


def validate_coordinates(dishes: List[Dict[str, Any]], image_size: Tuple[int, int]) -> bool:
    w, h = image_size
    for dish in dishes:
        pos = dish.get('position', [])
        iv = _to_int4(pos)
        if not iv:
            log(f"菜品 {dish.get('name', '未知')} 的位置格式不正确: {pos}")
            return False
        xmin, ymin, xmax, ymax = iv
        if not (0 <= xmin < xmax <= w - 1 and 0 <= ymin < ymax <= h - 1):
            log(f"菜品 {dish.get('name', '未知')} 的坐标超出图像范围: {iv} (图像大小: {image_size})")
            return False
    return True


def _load_font(paths: List[str], size: int) -> ImageFont.FreeTypeFont:
    for p in paths:
        try:
            return ImageFont.truetype(p, size=size)
        except Exception:
            continue
    # 回退
    return ImageFont.load_default()


def annotate_image(image_path: str, dishes: List[Dict[str, Any]], output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with Image.open(image_path) as img:
        # 统一到 RGBA，绘制时更稳定
        if img.mode != "RGBA":
            img = img.convert("RGBA")

        draw = ImageDraw.Draw(img)
        font = _load_font(FONT_PATHS, FONT_SIZE)

        for dish in dishes:
            name = str(dish.get('name', '未知'))
            cal = dish.get('calories', None)
            label = f"{name} - {cal} kcal" if isinstance(cal, (int, float)) else name

            xmin, ymin, xmax, ymax = dish.get('position', [0, 0, 0, 0])
            # 边框
            draw.rectangle([xmin, ymin, xmax, ymax], outline=(255, 0, 0, 255), width=2)

            # 计算中心点
            cx = (xmin + xmax) // 2
            cy = (ymin + ymax) // 2

            # 计算文本尺寸
            # textbbox 返回 (l, t, r, b)
            l, t, r, b = draw.textbbox((0, 0), label, font=font)
            tw, th = r - l, b - t
            pad = 6

            # 以中心点为基准居中放置文字与底衬
            rect_left = cx - (tw // 2) - pad
            rect_top = cy - (th // 2) - pad
            rect_right = cx + (tw // 2) + pad
            rect_bottom = cy + (th // 2) + pad

            # 夹取，避免越界
            W, H = img.size
            dx, dy = 0, 0
            if rect_left < 0:
                dx = -rect_left
            if rect_right > W:
                dx = min(dx, W - rect_right)
            if rect_top < 0:
                dy = -rect_top
            if rect_bottom > H:
                dy = min(dy, H - rect_bottom)
            rect_left += dx
            rect_right += dx
            rect_top += dy
            rect_bottom += dy

            # 半透明底
            draw.rectangle([rect_left, rect_top, rect_right, rect_bottom], fill=(0, 0, 0, 140))
            # 文本
            text_x = rect_left + pad
            text_y = rect_top + pad
            draw.text((text_x, text_y), label, fill=(255, 255, 255, 255), font=font)

        ext = os.path.splitext(output_path)[1].lower()
        if ext in [".jpg", ".jpeg"]:
            # JPEG 不支持透明：铺白
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])  # alpha 作为掩码
            background.save(output_path, quality=95)
        else:
            img.save(output_path)

    log(f"标注后的图像已保存至 {output_path}")


import os
import time

def main():
    image_size = get_image_size(INPUT_IMAGE_PATH)
    log(f"图像大小: {image_size}")

    image_b64 = image_to_base64(INPUT_IMAGE_PATH)

    attempt = 0
    while attempt < MAX_RETRIES:
        try:
            result = call_model(image_b64)
            if not result:
                log("未能获取有效的分析结果。")
                return

            dishes = result.get("dishes", [])
            if not dishes:
                log("未识别到任何菜品，请检查图像或API响应。")
                return

            # 统一坐标
            dishes_norm = normalize_positions(dishes, image_size, POSITION_MODE)

            if validate_coordinates(dishes_norm, image_size):
                # ==== 动态生成输出文件名 ====
                base_name = os.path.splitext(os.path.basename(INPUT_IMAGE_PATH))[0]  # 原文件名（无扩展）
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                file_name = f"{base_name}_{MODEL_NAME}_{timestamp}.png"
                output_path = os.path.join(OUTPUT_IMAGE_PATH, file_name)
                # ==========================

                annotate_image(INPUT_IMAGE_PATH, dishes_norm, output_path)
                return
            else:
                log("坐标校验失败，重新识别...")
                attempt += 1
                time.sleep(RETRY_SLEEP_SECONDS)
        except Exception as e:
            log(f"发生错误: {e}")
            attempt += 1
            time.sleep(RETRY_SLEEP_SECONDS)
    log("达到最大重试次数，操作失败。")


if __name__ == "__main__":
    main()