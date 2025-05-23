import io
import time
import base64
import ssl
import logging
import json
import configparser

from pydub import AudioSegment
import websocket

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

# 打开 websocket-client 的 trace，如果要看底层帧可以打开
websocket.enableTrace(False)


# ———— 配置读取 ————
def read_config():
    cfg = configparser.ConfigParser()
    cfg.read('../config.ini')
    return cfg.get('step_api_prod', 'key'), cfg.get('step_api_prod', 'wsurl')

STEPFUN_KEY, WS_BASE_URL = read_config()
MODEL = "step-asr-mini"
URL = f"{WS_BASE_URL}/realtime/transcriptions?model={MODEL}"
HEADERS = [f"Authorization: Bearer {STEPFUN_KEY}"]


# ———— Client Event 构造 ————

def event_connection_create(session_id: str, language: str = "auto") -> str:
    """
    transcript.session.create
    """
    return json.dumps({
        "connection_id": session_id,
        "type": "transcript.session.create",
        "data": {
            "language": language
        }
    })


def event_audio_append(session_id: str, audio_b64: str) -> str:
    """
    transcript.input_audio_buffer.append
    """
    return json.dumps({
        "connection_id": session_id,
        "type": "transcript.input_audio_buffer.append",
        "data": {
            "audio": audio_b64
        }
    })


def event_audio_done(session_id: str) -> str:
    """
    transcript.input_audio_buffer.done
    """
    return json.dumps({
        "connection_id": session_id,
        "type": "transcript.input_audio_buffer.done"
    })


session_id: str = None


# ———— WebSocket 回调 ————

def on_open(ws):
    logging.info("WebSocket 已打开")


def on_message(ws, message):
    global session_id
    msg = json.loads(message)
    t = msg.get("type")

    if t == "transcript.connection.created":
        session_id = msg["connection_id"]
        # 按文档在这里创建会话
        ws.send(event_connection_create(session_id, language="auto"))

    elif t == "transcript.session.created":
        # 会话就绪，开始切片并发送
        send_audio_chunks(ws, session_id, "combined_audio.wav",
                          chunk_duration_ms=240, pause_ms=100)

    elif t == "transcript.text.delta":
        logging.info("实时中间结果: %s", msg["data"]["result"])

    elif t == "transcript.text.slice":
        logging.info("分片识别结果: %s", msg["data"]["result"])

    elif t == "transcript.response.done":
        # 最终结果来了，主动关闭连接
        logging.info("完整识别结果: %s", msg["data"]["result"])
        ws.close()  # 按文档：服务端会释放连接，这里我们也主动关闭

    elif t == "transcript.response.error":
        code = msg["data"]["code"]
        err  = msg["data"]["error"]
        logging.error("服务端错误 %s: %s", code, err)


def on_error(ws, error):
    # “Connection to remote host was lost” 很可能是正常关闭后的日志，忽略
    if "Connection to remote host was lost" in str(error):
        return
    logging.error("WebSocket 错误: %s", error)


def on_close(ws, code, reason):
    logging.info("WebSocket 关闭: %s %s", code, reason)


# ———— 音频切片 & 发送 ————

def split_audio(audio_file: str,
                chunk_duration_ms: int = 240,
                output_format: str = 'wav') -> list[bytes]:
    """
    用 pydub 将任意格式音频切成若干 chunk_duration_ms 大小的片段，
    返回每段导出为 WAV 格式后的原始 bytes 列表（带 RIFF 头）。
    """
    audio = AudioSegment.from_file(audio_file)
    total_duration = len(audio)  # 毫秒
    num_chunks = (total_duration + chunk_duration_ms - 1) // chunk_duration_ms

    chunks: list[bytes] = []
    for i in range(num_chunks):
        start = i * chunk_duration_ms
        end   = min((i + 1) * chunk_duration_ms, total_duration)
        segment = audio[start:end]

        buf = io.BytesIO()
        try:
            # 强制输出 WAV（带 RIFF header，PCM 编码）
            segment.export(buf, format=output_format)
            buf.seek(0)
            chunks.append(buf.read())
        except Exception as e:
            logging.error("切片 %d 导出失败：%s", i, e)

    return chunks


def send_audio_chunks(ws, conn_id: str, audio_file: str, *,
                      chunk_duration_ms: int = 240,
                      pause_ms: int = 100):
    """
    1) 先按时长切片
    2) 逐片 base64 发送 transcript.input_audio_buffer.append
    3) 全部发完后发 transcript.input_audio_buffer.done
    """
    wav_chunks = split_audio(audio_file, chunk_duration_ms)
    logging.info("总片数：%d", len(wav_chunks))

    for idx, raw_wav in enumerate(wav_chunks, start=1):
        b64 = base64.b64encode(raw_wav).decode('ascii')
        ws.send(event_audio_append(conn_id, b64))
        logging.debug("已发送第 %d/%d 片", idx, len(wav_chunks))
        time.sleep(pause_ms / 1000.0)

    ws.send(event_audio_done(conn_id))
    logging.info("全部音频片段发送完成")


# ———— 主程序 ————

if __name__ == "__main__":
    ws = websocket.WebSocketApp(
        URL,
        header=HEADERS,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})