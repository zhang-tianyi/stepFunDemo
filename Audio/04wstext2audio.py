import websocket
import json
import time
import base64
import configparser
import os
import logging
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
    # 读取 API 配置；测试环境将 step_api_prod 换成 step_api_test 即可
    api_key = config.get('step_api_prod', 'key')
    api_url = config.get('step_api_prod', 'wsurl')
    return api_key, api_url

STEP_API_KEY, WS_BASE_URL = read_config()

# ---------------------------
# 全局参数配置
# ---------------------------
session_id = ""
# voice_id = "linjiameimei"  # 替换为实际的音色 ID

voice_id = "voice-tone-Eog0tIPGwy"# 克隆的音色
auth_token = STEP_API_KEY  # 鉴权 TOKEN

ws_url = WS_BASE_URL + "/realtime/audio?model=step-tts-mini"

# 用于存储返回的 base64 音频数据（备用）
audio_chunks = []
# 用于存储每个片段的文件路径
audio_chunk_files = []
# 音频片段计数
chunk_index = 1

# 记录发送文本开始时间和上次收到音频片段的时间
text_start_time = None
last_audio_time = None

# 确保输出目录存在
output_dir = "./output"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# ---------------------------
# 辅助函数：发送 tts.create 消息（用于创建会话）
# ---------------------------
def send_create(ws):
    create_msg = {
        "type": "tts.create",
        "data": {
            "session_id": session_id,  # 使用服务器返回的有效 session_id
            "voice_id": voice_id,
            "response_format": "mp3",  # 可选：wav、mp3、flac、opus
            "volumn_ratio": 1.0,
            "speed_ratio": 1.0,
            "sample_rate": 16000,
            "mode": "sentence"
        }
    }
    ws.send(json.dumps(create_msg))
    logging.info("发送 tts.create 消息（使用更新后的 session_id）：%s", session_id)

# ---------------------------
# 辅助函数：发送文本消息（包括 tts.text.delta 和 tts.text.done）
# ---------------------------
text_sent = False
def send_text(ws):
    global text_sent, text_start_time
    if text_sent:
        return
    text_msg = {
        "type": "tts.text.delta",
        "data": {
            "session_id": session_id,
            "text": "你好，这是一个测试文本，用于生成语音。"
        }
    }
    ws.send(json.dumps(text_msg))
    # 记录发送文本开始的时间，即 tts.text.delta 消息发送的时间
    text_start_time = time.time()
    logging.info("发送 tts.text.delta 消息（使用 session_id）：%s", session_id)
    text_done_msg = {
        "type": "tts.text.done",
        "data": {
            "session_id": session_id
        }
    }
    ws.send(json.dumps(text_done_msg))
    logging.info("发送 tts.text.done 消息（使用 session_id）：%s", session_id)
    text_sent = True
    logging.info("文本开始发送时间戳: %.3f", text_start_time)

# ---------------------------
# 辅助函数：保存单个音频片段到文件
# ---------------------------
def save_chunk_audio(audio_b64, index):
    try:
        missing_padding = len(audio_b64) % 4
        if missing_padding:
            audio_b64 += '=' * (4 - missing_padding)
        audio_data = base64.b64decode(audio_b64)
        chunk_filename = os.path.join(output_dir, f"chunk_{index}.mp3")
        with open(chunk_filename, "wb") as f:
            f.write(audio_data)
        logging.info("片段 %d 已保存到 %s", index, chunk_filename)
        return chunk_filename
    except Exception as e:
        logging.error("保存片段 %d 出错: %s", index, e)
        return None

# ---------------------------
# 辅助函数：合并所有音频片段
# ---------------------------
def merge_audio_chunks(chunk_files):
    try:
        combined = AudioSegment.empty()
        for file in chunk_files:
            segment = AudioSegment.from_mp3(file)
            combined += segment
        final_filename = os.path.join(output_dir, "combined_audio.mp3")
        combined.export(final_filename, format="mp3")
        logging.info("所有片段已合并，完整音频保存到 %s", final_filename)
    except Exception as e:
        logging.error("合并音频出错: %s", e)

# ---------------------------
# 回调函数：接收消息
# ---------------------------
def on_message(ws, message):
    global session_id, chunk_index, last_audio_time
    try:
        resp = json.loads(message)
        msg_type = resp.get("type")
        # 针对音频消息，打印出 base64 字符串的前50字符
        if msg_type in ["tts.response.audio.delta", "tts.response.audio.done"]:
            audio_b64 = resp.get("data", {}).get("audio", "")
            if audio_b64:
                preview = audio_b64[:50]
                logging.info("接收到音频流的前50字符: %s", preview)
            # 如果仍希望替换日志中的音频数据为预览内容
            temp_resp = dict(resp)
            if "data" in temp_resp and "audio" in temp_resp["data"]:
                temp_resp["data"]["audio"] = audio_b64[:50] + "..."
            logging.info("接收到消息: %s", json.dumps(temp_resp, ensure_ascii=False))
        else:
            logging.info("接收到消息: %s", message)

        if msg_type == "tts.connection.done":
            logging.info("建联成功: %s", resp)
            new_session_id = resp.get("data", {}).get("session_id")
            if new_session_id:
                logging.info("服务器返回新 session_id：%s", new_session_id)
                session_id = new_session_id
                send_create(ws)
            else:
                logging.error("未能获取新的 session_id")
        elif msg_type == "tts.response.created":
            logging.info("会话创建成功: %s", resp)
            send_text(ws)
        elif msg_type == "tts.response.audio.delta":
            current_time = time.time()
            if last_audio_time is None:
                if text_start_time is not None:
                    interval = current_time - text_start_time
                    logging.info("从发送文本到接收第一个音频的间隔: %.3f 秒", interval)
                else:
                    logging.warning("未记录文本发送开始时间")
            else:
                interval = current_time - last_audio_time
                logging.info("连续收到音频片段之间的间隔: %.3f 秒", interval)
            last_audio_time = current_time

            original_resp = json.loads(message)
            audio_b64 = original_resp.get("data", {}).get("audio")
            if audio_b64:
                audio_chunks.append(audio_b64)
                chunk_file = save_chunk_audio(audio_b64, chunk_index)
                if chunk_file:
                    audio_chunk_files.append(chunk_file)
                chunk_index += 1
        elif msg_type == "tts.response.audio.done":
            logging.info("音频生成完成，开始合并所有片段生成完整音频")
            full_audio_b64 = resp.get("data", {}).get("audio")
            if full_audio_b64:
                save_audio(full_audio_b64)
            if audio_chunk_files:
                merge_audio_chunks(audio_chunk_files)
            else:
                logging.error("未检测到保存的音频片段，无法合并")
        elif msg_type == "tts.response.error":
            logging.error("服务端返回错误: %s", resp)
        else:
            logging.warning("收到未处理的消息类型: %s", msg_type)
    except Exception as e:
        logging.error("解析消息出错: %s", e)

def on_error(ws, error):
    if "Connection to remote host was lost" in str(error):
        return
    logging.error("WebSocket 错误: %s", error)

def on_close(ws, close_status_code, close_msg):
    logging.info("WebSocket 连接关闭: %s %s", close_status_code, close_msg)

def on_open(ws):
    logging.info("WebSocket 连接已打开")
    # 等待服务器返回 tts.connection.done 消息

# ---------------------------
# 辅助函数：保存完整音频文件（备用）
# ---------------------------
def save_audio(audio_b64):
    try:
        missing_padding = len(audio_b64) % 4
        if missing_padding:
            audio_b64 += '=' * (4 - missing_padding)
        audio_data = base64.b64decode(audio_b64)
        output_filename = os.path.join(output_dir, "output_audio.mp3")
        with open(output_filename, "wb") as f:
            f.write(audio_data)
        logging.info("完整音频已保存到 %s", output_filename)
    except Exception as e:
        logging.error("保存完整音频出错: %s", e)

# ---------------------------
# 主入口：启动 WebSocket 客户端
# ---------------------------
if __name__ == "__main__":
    headers = [f"authorization: {auth_token}"]
    ws_app = websocket.WebSocketApp(ws_url,
                                    header=headers,
                                    on_open=on_open,
                                    on_message=on_message,
                                    on_error=on_error,
                                    on_close=on_close)
    ws_app.run_forever()