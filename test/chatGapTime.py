import requests
import time
import sys
from datetime import datetime

# ========== 配置部分 ==========
API_URL = 'https://api.stepfun.com/v1/chat/completions'
API_KEY = '536fPHX23plBixMRb91IqntadgDRJEpsl4WurhxlyG5sqB9Yr5vKFv7OEK08E57jm'

HEADERS = {
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json',
}

# 请求体
payload = {
    "enableReasoning": False,
    "extra": {},
    "maxTokens": 4096,
    "model": "step-1o-turbo-vision-h",
    "stream": True,
    "messages": [
        {
            "role": "system",
            "content": """## 角色
- 你是OPPO公司独立自研的人工智能助手AndesGPT-VL大模型，小布/Breeno。
- 你擅长理解用户问题，结合图片信息，以亲切热情的语气回答。

## 输入说明
- 图片为视频抽帧。
- 优先根据最后一帧回答，必要时结合前帧推理。"""
        },
        {
            "role": "user",
            "content": "这是什么景点？",
            "images": [
                {
                    "detail": "low",
                    "url": "https://ark-project.tos-cn-beijing.volces.com/images/view.jpeg"
                }
            ]
        }
    ]
}

def stream_line_by_line_bytewise():
    resp = requests.get(API_URL, headers=HEADERS, json=payload, stream=True)
    resp.raise_for_status()
    resp.raw.decode_content = True  # ensure raw read gives decoded bytes

    last_time = None
    buffer = b''
    # 按字节读取，防止任何行缓冲
    for byte in resp.iter_content(chunk_size=1):
        if not byte:
            continue
        buffer += byte
        # 检测到行结束
        if byte == b'\n':
            try:
                line = buffer.strip().decode('utf-8')
            except UnicodeDecodeError:
                line = buffer.strip().decode('utf-8', errors='replace')

            if line.startswith('data:'):
                now = time.time()
                ts = datetime.fromtimestamp(now).isoformat()
                delta_ms = (now - last_time) * 1000 if last_time else 0
                last_time = now
                print(f"[{ts}] (+{delta_ms:.0f}ms) {line}", flush=True)

            buffer = b''

if __name__ == '__main__':
    try:
        stream_line_by_line_bytewise()
    except Exception as e:
        print("Error:", e, file=sys.stderr, flush=True)