import websocket
import logging
import json

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

# 模型名称
MODEL = "step-asr-mini"
# 接口地址
URL = "wss://api.stepfun.com/v1/realtime/transcriptions?model=" + MODEL
# 更新为你的 STEPFUN API KEY
STEPFUN_KEY = ""

header = {
    "Authorization": STEPFUN_KEY
}

language = "auto"
session_id = ""


def event_asr_session_create(session_id, language):
    return json.dumps(
        {
            "connection_id": session_id,
            "type": "transcript.session.create",
            "language": language
        }
    )


def event_audio_buffer_append(session_id, audio_base64):
    return json.dumps(
        {
            "connection_id": session_id,
            "type": "transcript.input_audio_buffer.append",
            "data": {"audio": audio_base64}
        }
    )


def event_audio_buffer_done(session_id):
    return json.dumps(
        {
            "connection_id": session_id,
            "type": "transcript.input_audio_buffer.done"
        }
    )


def on_message(ws, message):
    global session_id
    data = json.loads(message)
    # logging.info("接收到消息: %s", data) 
    event_type = data["type"]

    if (event_type == "transcript.connection.created"):
        # 连接成功，创建会话
        session_id = data["connection_id"]
        event_msg = event_asr_session_create(session_id, language)
        ws.send(event_msg)
    elif (event_type == "transcript.session.created"):
        # 会话创建成功，发送音频base64数据
        audio_base64 = "audio_base64_str"
        event_msg = event_audio_buffer_append(session_id, audio_base64)
        ws.send(event_msg)

        # 多个音频追加发送
        # event_msg = event_audio_buffer_append(session_id, audio_base64_2)
        # ws.send(event_msg)

        # 音频发送完成
        event_msg = event_audio_buffer_done(session_id)
        ws.send(event_msg)
    elif (event_type == "transcript.text.delta"):
        # ASR实时识别文本
        logging.info("transcript.text.delta: %s", data["data"]["result"])
    elif (event_type == "transcript.text.slice"):
        # ASR识别音频片段文本
        logging.info("transcript.text.slice: %s", data["data"]["result"])
    elif (event_type == "transcript.response.done"):
        # 最终完整识别文本
        logging.info("transcript.response.done: %s", data["data"]["result"])


def on_error(ws, error):
    if "Connection to remote host was lost" in str(error):
        return
    logging.error("WebSocket 错误: %s", error)


def on_close(ws, close_status_code, close_msg):
    logging.info("WebSocket 连接关闭: %s %s", close_status_code, close_msg)


def on_open(ws):
    logging.info("WebSocket 连接已打开")


if __name__ == "__main__":
    ws = websocket.WebSocketApp(
        URL,
        header=header,
        on_message=on_message,
        on_open=on_open,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever()