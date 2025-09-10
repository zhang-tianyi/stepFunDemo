import aiohttp
import asyncio
import base64
import os
import json
import ssl
import os
import logging
from pydub import AudioSegment

# -----------------------------
# 日志配置
# -----------------------------
logging.basicConfig(
    level=logging.DEBUG,  # DEBUG级别将打印所有日志（调试信息、信息、警告、错误）
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)




# -----------------------------
# 全局配置参数
# -----------------------------
STEP_API_KEY = os.environ["STEPFUN_API_KEY"]
WS_BASE_URL= os.environ['STEPFUN_WSS_ENDPOINT']

# 创建 SSL 上下文，并禁用证书验证（仅用于测试环境，不建议生产环境禁用）
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# 拼接 WebSocket URL，注意后面的路径和查询参数根据实际接口要求填写
url = WS_BASE_URL + "/realtime/audio?model=step-tts-mini"
response_format = "mp3"  # 输出音频格式，可选：mp3、wav、flac等
file_path_save = "./output"  # 输出目录
text = '''你好，我是科技小步，很高兴认识你！'''  # 待转换为语音的文本
voice = "linjiameimei"  # 音色ID，根据接口文档填写

# 全局变量：保存接收到的音频片段和会话ID
audio_list = []
session_id = ""


# -----------------------------
# 构建各类事件消息的函数
# -----------------------------
def build_start_event(voice_id, session_id, response_format=response_format, volume_ratio=1, speed_ratio=1):
    """
    构建 tts.create 消息，通知服务端开始创建会话。
    """
    event = {
        "type": "tts.create",
        "data": {
            "session_id": session_id,
            "voice_id": voice_id,
            "response_format": response_format,
            "volume_ratio": volume_ratio,
            "speed_ratio": speed_ratio,
        },
    }
    logging.debug("构建 tts.create 消息: %s", event)
    return json.dumps(event)


def build_text_event(text, uuid):
    """
    构建 tts.text.delta 消息，用于发送待转换文本内容。
    """
    event = {
        "type": "tts.text.delta",
        "data": {
            "text": text,
            "session_id": uuid,
        },
    }
    logging.debug("构建 tts.text.delta 消息: %s", event)
    return json.dumps(event)


def build_text_done_event(uuid):
    """
    构建 tts.text.done 消息，表示文本发送完毕。
    """
    event = {
        "type": "tts.text.done",
        "data": {
            "session_id": uuid,
        },
    }
    logging.debug("构建 tts.text.done 消息: %s", event)
    return json.dumps(event)


# -----------------------------
# 主异步函数：连接 WebSocket 并处理交互逻辑
# -----------------------------
async def test_submit(text, voice):
    global session_id, audio_list
    # 将鉴权信息通过 header 传递给服务端
    headers = {"Authorization": f"Bearer {STEP_API_KEY}"}
    logging.info("连接到 WebSocket URL: %s", url)

    # 使用 aiohttp 建立 WebSocket 连接
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(url, ssl=ssl_context, headers=headers) as ws:
            # 等待接收建立连接的消息（tts.connection.done）
            msg = await ws.receive()
            if msg.type == aiohttp.WSMsgType.TEXT:
                data = json.loads(msg.data)
                if data.get("type") == "tts.connection.done":
                    logging.info("成功连接到服务器")
                    session_id = data["data"]["session_id"]
                    logging.info("收到 session_id: %s", session_id)
                else:
                    logging.error("未收到 tts.connection.done 消息: %s", data)
                    return
            else:
                logging.error("WebSocket 连接异常，消息类型: %s", msg.type)
                return

            # 发送创建会话消息（tts.create）
            logging.info("发送 tts.create 消息")
            start_event = build_start_event(voice, session_id)
            await ws.send_str(start_event)

            # 等待接收创建会话成功的响应（tts.response.created）
            msg = await ws.receive()
            if msg.type == aiohttp.WSMsgType.TEXT:
                data = json.loads(msg.data)
                logging.info("收到创建会话响应: %s", data)
                if data.get("type") in ["tts.response.created", "tts.create"]:
                    logging.info("会话创建成功")
                else:
                    logging.error("会话创建返回异常: %s", data)
                    return
            else:
                logging.error("未收到会话创建消息")
                return

            # 发送文本消息（tts.text.delta）
            logging.info("发送文本信息: %s", text)
            text_event = build_text_event(text, session_id)
            await ws.send_str(text_event)

            # 发送文本结束消息（tts.text.done）
            logging.info("发送 tts.text.done 消息")
            done_event = build_text_done_event(session_id)
            await ws.send_str(done_event)

            # 循环接收服务端返回的音频数据消息，直到收到音频生成完成消息（tts.response.audio.done）
            logging.info("开始接收音频数据")
            while True:
                msg = await ws.receive()
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    msg_type = data.get("type")
                    if msg_type == "tts.response.audio.done":
                        logging.info("收到音频生成完成消息: %s", msg_type)
                        logging.info("完成 session 对话")
                        await asyncio.sleep(0.1)
                        break
                    elif msg_type == "tts.response.audio.delta":
                        status = data["data"].get("status")
                        logging.info("收到音频片段消息: %s, 状态: %s", msg_type, status)
                        audio_list.append(data["data"]["audio"])
                    elif msg_type == "tts.response.error":
                        logging.error("收到错误消息: %s", data["data"].get("message"))
                        break
                    else:
                        logging.debug("收到其他消息: %s", data)
                elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                    logging.error("WebSocket 连接关闭或发生错误: %s", msg.type)
                    break

            # 拼接所有接收到的音频片段，并保存到文件中
            if not os.path.exists(file_path_save):
                os.makedirs(file_path_save)
                logging.debug("创建输出目录: %s", file_path_save)
            file_path = os.path.join(file_path_save, f'{session_id}.{response_format}')
            if os.path.exists(file_path):
                os.remove(file_path)
                logging.debug("删除已存在的文件: %s", file_path)
            for audio in audio_list:
                audio_byte = base64.b64decode(audio)
                with open(file_path, 'ab') as f:
                    f.write(audio_byte)
            logging.info("音频已保存到 %s", file_path)


# -----------------------------
# 主入口
# -----------------------------
if __name__ == '__main__':
    logging.info("开始 TTS 流式转换测试")
    asyncio.run(test_submit(text, voice))