import configparser
import json
import urllib.parse
import http.client
from datetime import datetime

import requests
from openai import OpenAI

# ─────────────────────────────────────────────────────────
# 配置读取
# ─────────────────────────────────────────────────────────
def read_config():
    config = configparser.ConfigParser()
    config.read('../config.ini', encoding='utf-8')
    api_key = config.get('step_api_prod', 'key')
    api_url = config.get('step_api_prod', 'url')
    return api_key, api_url

STEPFUN_KEY, BASE_URL = read_config()


# ─────────────────────────────────────────────────────────
# 工具：从 choice 对象中提取 content
# ─────────────────────────────────────────────────────────
def extract_content(choice: dict) -> str:
    if "message" in choice:
        return choice["message"].get("content", "")
    if "delta" in choice:
        return choice["delta"].get("content", "")
    return ""  # 若无 content 字段，返回空串


# ─────────────────────────────────────────────────────────
# 1. 官方 SDK 流式请求
# ─────────────────────────────────────────────────────────
def test_sdk_stream():
    print("\n=== SDK Streaming ===")
    oai = OpenAI(api_key=STEPFUN_KEY, base_url=BASE_URL)
    with oai.chat.completions.with_streaming_response.create(
        messages=[{"role": "user", "content": "Say this is a test"}],
        model="step-1o-turbo-vision",
    ) as resp:
        t0 = datetime.now()
        trace_id = resp.headers.get("x-trace-id")
        print(f"[{t0.isoformat()}] SDK Trace ID: {trace_id}")

        for idx, line in enumerate(resp.iter_lines()):
            if not line:
                continue
            t1 = datetime.now()
            if idx == 0:
                delta = (t1 - t0).total_seconds() * 1000
                print(f"[{t1.isoformat()}] SDK first frame delay: {delta:.1f} ms")
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                print(f"  [SDK] 非 JSON 帧，跳过: {line!r}")
                continue

            choice = data["choices"][0]
            content = extract_content(choice)
            print("  →", content)


# ─────────────────────────────────────────────────────────
# 2. requests 库流式请求
# ─────────────────────────────────────────────────────────
def test_requests_stream():
    print("\n=== requests Streaming ===")
    url = f"{BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {STEPFUN_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "step-1o-turbo-vision",
        "stream": True,
        "messages": [{"role": "user", "content": "Say this is a test"}],
    }

    resp = requests.post(url, headers=headers, json=payload, stream=True)
    t0 = datetime.now()
    trace_id = resp.headers.get("x-trace-id")
    print(f"[{t0.isoformat()}] requests Trace ID: {trace_id}")

    for idx, raw in enumerate(resp.iter_lines()):
        if not raw:
            continue
        text = raw.decode('utf-8').strip()
        # 去除 SSE 前缀
        if text.startswith('data:'):
            text = text[len('data:'):].strip()
        # 跳过空行或结束符
        if text in ('', '[DONE]'):
            continue

        t1 = datetime.now()
        if idx == 0:
            delta = (t1 - t0).total_seconds() * 1000
            print(f"[{t1.isoformat()}] requests first frame delay: {delta:.1f} ms")

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            print(f"  [requests] 非 JSON 行，跳过: {text}")
            continue

        choice = data["choices"][0]
        content = extract_content(choice)
        print("  →", content)


# ─────────────────────────────────────────────────────────
# 3. http.client 标准库流式请求
# ─────────────────────────────────────────────────────────
def test_httpclient_stream():
    print("\n=== http.client Streaming ===")
    u = urllib.parse.urlparse(BASE_URL)
    conn = http.client.HTTPSConnection(u.netloc, timeout=30)

    path = u.path.rstrip('/') + '/chat/completions'
    body = json.dumps({
        "model": "step-1o-turbo-vision",
        "stream": True,
        "messages": [{"role": "user", "content": "Say this is a test"}],
    })
    req_headers = {
        "Authorization": f"Bearer {STEPFUN_KEY}",
        "Content-Type": "application/json",
    }

    conn.request("POST", path, body=body, headers=req_headers)
    resp = conn.getresponse()

    t0 = datetime.now()
    trace_id = resp.getheader("x-trace-id")
    print(f"[{t0.isoformat()}] http.client Trace ID: {trace_id}")

    idx = 0
    while True:
        line = resp.readline()
        if not line:
            break
        payload = line.strip()
        # 去除 SSE 前缀
        if payload.startswith(b"data:"):
            payload = payload[len(b"data:"):].strip()
        text = payload.decode('utf-8').strip()
        # 跳过空行或结束符
        if text in ('', '[DONE]'):
            continue

        t1 = datetime.now()
        if idx == 0:
            delta = (t1 - t0).total_seconds() * 1000
            print(f"[{t1.isoformat()}] http.client first frame delay: {delta:.1f} ms")

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            print(f"  [http.client] 非 JSON 行，跳过: {text}")
            idx += 1
            continue

        choice = data["choices"][0]
        content = extract_content(choice)
        print("  →", content)
        idx += 1

    conn.close()


# ─────────────────────────────────────────────────────────
# 主流程
# ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    test_sdk_stream()
    test_requests_stream()
    test_httpclient_stream()