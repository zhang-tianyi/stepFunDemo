import websocket
import json
import time
import base64
import configparser
import os
from pydub import AudioSegment

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
voice_id = "linjiameimei"  # 替换为实际的音色 ID
auth_token = STEP_API_KEY  # 鉴权 TOKEN

ws_url = WS_BASE_URL + "/realtime/audio?model=step-tts-mini"

# 用于存储返回的 base64 音频数据（原来的方法，备用）
audio_chunks = []
# 新增：用于存储每个片段的文件路径
audio_chunk_files = []
# 音频片段计数
chunk_index = 1

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
            "volumn_ratio": 1.0,  # 音量比例：0.1~2.0
            "speed_ratio": 1.0,  # 语速比例：0.5~2.0
            "sample_rate": 16000,  # 采样率：8000~96000
            "mode":"sentence"
        }
    }
    ws.send(json.dumps(create_msg))
    print("发送 tts.create 消息（使用更新后的 session_id）：", session_id)

# ---------------------------
# 辅助函数：发送文本消息（包括 tts.text.delta 和 tts.text.done）
# ---------------------------
text_sent = False
def send_text(ws):
    global text_sent
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
    print("发送 tts.text.delta 消息（使用 session_id）：", session_id)
    time.sleep(1)
    text_done_msg = {
        "type": "tts.text.done",
        "data": {
            "session_id": session_id
        }
    }
    ws.send(json.dumps(text_done_msg))
    print("发送 tts.text.done 消息（使用 session_id）：", session_id)
    text_sent = True

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
        print(f"片段 {index} 已保存到 {chunk_filename}")
        return chunk_filename
    except Exception as e:
        print(f"保存片段 {index} 出错:", e)
        return None

# ---------------------------
# 辅助函数：合并所有音频片段
# ---------------------------
def merge_audio_chunks(chunk_files):
    try:
        # 使用 pydub 合并音频片段
        combined = AudioSegment.empty()
        for file in chunk_files:
            segment = AudioSegment.from_mp3(file)
            combined += segment
        final_filename = os.path.join(output_dir, "combined_audio.mp3")
        combined.export(final_filename, format="mp3")
        print(f"所有片段已合并，完整音频保存到 {final_filename}")
    except Exception as e:
        print("合并音频出错:", e)

# ---------------------------
# 回调函数：接收消息
# ---------------------------
def on_message(ws, message):
    global session_id, chunk_index
    try:
        resp = json.loads(message)
        msg_type = resp.get("type")
        # 打印消息时对 audio 字段做替换
        if msg_type in ["tts.response.audio.delta", "tts.response.audio.done"]:
            temp_resp = dict(resp)
            if "data" in temp_resp and "audio" in temp_resp["data"]:
                temp_resp["data"]["audio"] = "[BASE64 DATA]"
            print("接收到消息:", json.dumps(temp_resp, ensure_ascii=False))
        else:
            print("接收到消息:", message)

        if msg_type == "tts.connection.done":
            print("建联成功:", resp)
            new_session_id = resp.get("data", {}).get("session_id")
            if new_session_id:
                print("服务器返回新 session_id：", new_session_id)
                session_id = new_session_id
                send_create(ws)
            else:
                print("未能获取新的 session_id")
        elif msg_type == "tts.response.created":
            print("会话创建成功:", resp)
            send_text(ws)
        elif msg_type == "tts.response.audio.delta":
            data = resp.get("data", {})
            status = data.get("status")
            duration = data.get("duration")
            print(f"音频片段生成，状态: {status}，时长: {duration} 秒")
            # 记录原始 base64 数据（备用）
            original_resp = json.loads(message)
            audio_b64 = original_resp.get("data", {}).get("audio")
            if audio_b64:
                audio_chunks.append(audio_b64)
                # 保存单个片段到文件，并记录文件路径
                chunk_file = save_chunk_audio(audio_b64, chunk_index)
                if chunk_file:
                    audio_chunk_files.append(chunk_file)
                    chunk_index += 1
        elif msg_type == "tts.response.audio.done":
            print("音频生成完成，开始合并所有片段生成完整音频")
            full_audio_b64 = resp.get("data", {}).get("audio")
            if full_audio_b64:
                save_audio(full_audio_b64)
            if audio_chunk_files:
                merge_audio_chunks(audio_chunk_files)
            else:
                print("未检测到保存的音频片段，无法合并")
        elif msg_type == "tts.response.error":
            print("服务端返回错误:", resp)
        else:
            print("收到未处理的消息类型:", msg_type)
    except Exception as e:
        print("解析消息出错:", e)

def on_error(ws, error):
    # 过滤正常关闭的错误信息
    if "Connection to remote host was lost" in str(error):
        return
    print("WebSocket 错误:", error)

def on_close(ws, close_status_code, close_msg):
    print("WebSocket 连接关闭:", close_status_code, close_msg)

def on_open(ws):
    print("WebSocket 连接已打开")
    # 等待服务器返回 tts.connection.done 消息

# ---------------------------
# 原有辅助函数：保存音频文件（备用）
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
        print(f"完整音频已保存到 {output_filename}")
    except Exception as e:
        print("保存完整音频出错:", e)

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