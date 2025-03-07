import websocket
import json
import time
import base64
import configparser


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
# 初始 session_id 为空，等待服务器在 tts.connection.done 消息中返回有效的 session_id
session_id = ""
voice_id = "linjiameimei"  # 替换为实际的音色 ID
auth_token = STEP_API_KEY  # 鉴权 TOKEN

# WebSocket 地址（假设使用 wss 协议）
ws_url = WS_BASE_URL + "/realtime/audio?model=step-tts-mini"

# 用于存储返回的音频数据（多个片段后拼接）
audio_chunks = []

# 标志：是否已经发送文本消息（避免重复发送）
text_sent = False


# ---------------------------
# 辅助函数：发送 tts.create 消息（用于创建会话）
# ---------------------------
def send_create(ws):
    create_msg = {
        "type": "tts.create",
        "data": {
            "session_id": session_id,  # 使用服务器返回的有效 session_id
            "voice_id": voice_id,
            "response_format": "wav",  # 可选：wav、mp3、flac、opus
            "volumn_ratio": 1.0,  # 音量比例：0.1~2.0
            "speed_ratio": 1.0,  # 语速比例：0.5~2.0
            "sample_rate": 16000  # 采样率：8000~96000
        }
    }
    ws.send(json.dumps(create_msg))
    print("发送 tts.create 消息（使用更新后的 session_id）：", session_id)


# ---------------------------
# 辅助函数：发送文本消息（包括 tts.text.delta 和 tts.text.done）
# ---------------------------
def send_text(ws):
    global text_sent
    if text_sent:
        return
    # 构造并发送文本消息
    text_msg = {
        "type": "tts.text.delta",
        "data": {
            "session_id": session_id,  # 使用有效 session_id
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
# 回调函数：接收消息
# ---------------------------
def on_message(ws, message):
    global session_id
    try:
        resp = json.loads(message)
        msg_type = resp.get("type")
        # 对于音频消息，打印时将 audio 字段替换为占位符
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
                # 此时发送 tts.create 消息，使用有效 session_id创建会话
                send_create(ws)
            else:
                print("未能获取新的 session_id")
        elif msg_type == "tts.response.created":
            print("会话创建成功:", resp)
            # 会话创建成功后，发送文本消息
            send_text(ws)
        elif msg_type == "tts.response.audio.delta":
            data = resp.get("data", {})
            status = data.get("status")
            duration = data.get("duration")
            print(f"音频片段生成，状态: {status}，时长: {duration} 秒")
            # 从原始消息中获取完整的 audio 数据用于保存（打印时已替换）
            original_resp = json.loads(message)
            audio_b64 = original_resp.get("data", {}).get("audio")
            if audio_b64:
                audio_chunks.append(audio_b64)
        elif msg_type == "tts.response.audio.done":
            print("音频生成完成，保存完整音频")
            full_audio_b64 = resp.get("data", {}).get("audio")
            if full_audio_b64:
                save_audio(full_audio_b64)
            else:
                combined_audio = "".join(audio_chunks)
                save_audio(combined_audio)
        elif msg_type == "tts.response.error":
            print("服务端返回错误:", resp)
        else:
            print("收到未处理的消息类型:", msg_type)
    except Exception as e:
        print("解析消息出错:", e)


def on_error(ws, error):
    print("WebSocket 错误:", error)


def on_close(ws, close_status_code, close_msg):
    print("WebSocket 连接关闭:", close_status_code, close_msg)


# ---------------------------
# 回调函数：连接打开时不发送消息，而是等待 tts.connection.done 消息
# ---------------------------
def on_open(ws):
    print("WebSocket 连接已打开")
    # 注意：不在 on_open 中发送 tts.create 消息，因为初始 session_id 为空
    # 等待服务器发送 tts.connection.done 消息获取有效 session_id


# ---------------------------
# 辅助函数：保存音频文件
# ---------------------------
def save_audio(audio_b64):
    try:
        # 自动补全 Base64 填充字符
        missing_padding = len(audio_b64) % 4
        if missing_padding:
            audio_b64 += '=' * (4 - missing_padding)
        audio_data = base64.b64decode(audio_b64)
        output_filename = "./output_audio.wav"
        with open(output_filename, "wb") as f:
            f.write(audio_data)
        print(f"音频已保存到 {output_filename}")
    except Exception as e:
        print("保存音频出错:", e)


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