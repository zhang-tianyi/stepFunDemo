import websocket
import json
import time
import base64
import configparser
import os
import logging
import threading
from pydub import AudioSegment

# 配置日志，格式中包含时间戳
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

# ---------------------------
# 读取配置文件函数
# ---------------------------
def read_config():
    config = configparser.ConfigParser()
    config.read('../config.ini')
    api_key = config.get('step_api_prod', 'key')
    api_url = config.get('step_api_prod', 'wsurl')
    return api_key, api_url

STEP_API_KEY, WS_BASE_URL = read_config()

# ---------------------------
# 全局参数
# ---------------------------
session_id = ""
voice_id = "voice-tone-Eog0tIPGwy"
auth_token = STEP_API_KEY
ws_url = WS_BASE_URL + "/realtime/audio?model=step-tts-vivid"

audio_chunks = []
audio_chunk_files = []
chunk_index = 1

text_start_time = None
last_audio_time = None

# 标记会话创建完成
created_received = False

output_dir = "./output"
os.makedirs(output_dir, exist_ok=True)

# ---------------------------
# 发送 tts.create（创建会话），包含 create_mode 参数
# ---------------------------
def send_create(ws, create_mode):
    msg = {
        "type": "tts.create",
        "data": {
            "session_id": session_id,
            "voice_id": voice_id,
            "response_format": "wav",
            "volumn_ratio": 1.0,
            "speed_ratio": 1.0,
            "sample_rate": 16000,
            "mode": create_mode
        }
    }
    ws.send(json.dumps(msg))
    logging.info("已发送 tts.create，session_id=%s，create_mode=%s", session_id, create_mode)

# ---------------------------
# 保存单个音频片段到文件
# ---------------------------
def save_chunk_audio(audio_b64, index):
    try:
        missing_padding = len(audio_b64) % 4
        if missing_padding:
            audio_b64 += "=" * (4 - missing_padding)
        data = base64.b64decode(audio_b64)

        ext = "wav" if data.startswith(b"RIFF") else "mp3"
        filename = os.path.join(output_dir, f"chunk_{index}.{ext}")
        with open(filename, "wb") as f:
            f.write(data)
        logging.info("片段 %d 保存为 %s", index, filename)
        return filename
    except Exception as e:
        logging.error("保存片段 %d 出错: %s", index, e)
        return None

# ---------------------------
# 合并所有音频片段
# ---------------------------
def merge_audio_chunks(files):
    try:
        combined = AudioSegment.empty()
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext == ".wav":
                seg = AudioSegment.from_wav(f)
            elif ext == ".mp3":
                seg = AudioSegment.from_mp3(f)
            else:
                seg = AudioSegment.from_file(f)
            combined += seg

        first_ext = os.path.splitext(files[0])[1].lstrip('.')
        out_file = os.path.join(output_dir, f"combined_audio.{first_ext}")
        combined.export(out_file, format=first_ext)
        logging.info("合并完成，输出文件：%s", out_file)
    except Exception as e:
        logging.error("合并音频出错: %s", e)

# ---------------------------
# WebSocket 回调：接收消息
# ---------------------------
def on_message(ws, message):
    global session_id, chunk_index, last_audio_time, created_received
    try:
        resp = json.loads(message)
        msg_type = resp.get("type")

        if msg_type == "tts.response.audio.delta":
            preview = resp["data"].get("audio", "")[:50]
            logging.info("收到音频流片段预览: %s", preview)
        else:
            logging.info("收到消息: %s", message)

        if msg_type == "tts.connection.done":
            session_id = resp["data"].get("session_id", "")
            if session_id:
                send_create(ws, CREATE_MODE)
            else:
                logging.error("未获取到 session_id")
        elif msg_type == "tts.response.created":
            logging.info("会话创建成功，进入文本发送阶段")
            created_received = True
        elif msg_type == "tts.response.audio.delta":
            now = time.time()
            if last_audio_time is None and text_start_time:
                logging.info("首个音频延迟: %.3f 秒", now - text_start_time)
            elif last_audio_time:
                logging.info("片段间隔: %.3f 秒", now - last_audio_time)
            last_audio_time = now

            b64 = resp["data"].get("audio")
            if b64:
                audio_chunks.append(b64)
                fname = save_chunk_audio(b64, chunk_index)
                if fname:
                    audio_chunk_files.append(fname)
                chunk_index += 1

            if resp["data"].get("status") == "finished":
                logging.info("检测到 finished，开始合并")
                merge_audio_chunks(audio_chunk_files)
        elif msg_type == "tts.response.error":
            logging.error("合成出错: %s", resp)
        else:
            logging.debug("未处理类型: %s", msg_type)
    except Exception as e:
        logging.error("on_message 处理异常: %s", e)

# ---------------------------
def on_error(ws, error):
    if "Connection to remote host was lost" in str(error):
        return
    logging.error("WebSocket 错误: %s", error)


def on_close(ws, code, reason):
    logging.info("连接关闭: %s %s", code, reason)

# ---------------------------
# WebSocket 回调：打开后启动交互线程
# ---------------------------
def on_open(ws):
    logging.info("WebSocket 已打开")

    def text_interactive():
        global text_start_time
        while not created_received:
            time.sleep(0.1)

        logging.info(f"开始合成文本: {TEXT}")
        text_start_time = time.time()

        if SPLIT_TEXT:
            for ch in TEXT:
                ws.send(json.dumps({
                    "type": "tts.text.delta",
                    "data": {"session_id": session_id, "text": ch}
                }))
                time.sleep(0.05)
            logging.info("已按字符拆分发送文本")
        else:
            ws.send(json.dumps({
                "type": "tts.text.delta",
                "data": {"session_id": session_id, "text": TEXT}
            }))
            logging.info("已一次性发送完整文本")

        while True:
            cmd = input("输入 'flush' 发送 tts.text.flush，'done' 发送 tts.text.done：").strip()
            if cmd == "flush":
                ws.send(json.dumps({"type": "tts.text.flush", "data": {"session_id": session_id}}))
                logging.info("已发送 tts.text.flush")
            elif cmd == "done":
                ws.send(json.dumps({"type": "tts.text.done", "data": {"session_id": session_id}}))
                logging.info("已发送 tts.text.done，等待音频流")
                break

    threading.Thread(target=text_interactive, daemon=True).start()

# ---------------------------
# 主入口：在这里修改 CREATE_MODE, SPLIT_TEXT 和 TEXT 即可
# ---------------------------
if __name__ == "__main__":
    # 控制 send_create 里的 mode 参数
    CREATE_MODE = "default"   # 可选 "default" 或 "sentence"
    # CREATE_MODE = "sentence"
    # 控制文本是否按字符拆分发送
    SPLIT_TEXT = True          # True 按字符拆分，False 不拆分
    # 要合成的文本内容
    TEXT = "您好，欢迎来到我的家。我爱大家，大家好。"

    logging.info("启动 create_mode：%s, split_text：%s", CREATE_MODE, SPLIT_TEXT)

    headers = [f"authorization: {auth_token}"]
    ws_app = websocket.WebSocketApp(
        ws_url,
        header=headers,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws_app.run_forever()
