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
voice_id = "voice-tone-Eog0tIPGwy"  # 克隆的音色
auth_token = STEP_API_KEY
ws_url = WS_BASE_URL + "/realtime/audio?model=step-tts-mini"

audio_chunks = []
audio_chunk_files = []
chunk_index = 1

text_start_time = None
last_audio_time = None

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
            "session_id": session_id,
            "voice_id": voice_id,
            "response_format": "mp3",
            "volumn_ratio": 1.0,
            "speed_ratio": 1.0,
            "sample_rate": 16000,
            "mode": "sentence"
        }
    }
    ws.send(json.dumps(create_msg))
    logging.info("发送 tts.create 消息（使用更新后的 session_id）：%s", session_id)

# ---------------------------
# 辅助函数：发送文本消息（仅 tts.text.delta）
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
            "text":"根据一个日本注意!简介为什具有可能;文化程序是否如何影响新闻' 能够自己原因关于注\ 一定重要能力网上资料您的应用新闻~` 一般作为重要发布很多!图片能够合作发表网络信息感觉出现怎么活动已经怎么|中文最后没有其中自己而且. 行业应用情况图片. 他们空间功能浏览具有时间. 留言教育帖子完成网络支持需要. 组织关于科技精华. 网上可能上海搜索. 这里各种发展还有认为. 密码类别情况作者. 研究广告怎么认为部门销售. 文化工作业务日本拥有更多空间显示. 到了这种学校一切."
            # "text": "我在测试新的语音合成，这是我3新建的一个模板，我在这个开场白里面测试，我继续测试，今天是二零二五年五月十三号，我这边写这么长的文字是用来凑字数的，因为太长了，所以要多打点字，是现实想不出多少字了，需要二百左右个字，我这边随便编一下，多写一点，多写一点字数应该就够长了吧，这样好像还不够，我这边再多写一点，写长一点。"
        }
    }
    ws.send(json.dumps(text_msg))
    text_start_time = time.time()
    logging.info("发送 tts.text.delta 消息（使用 session_id）：%s", session_id)

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
        # 打印日志
        if msg_type in ["tts.response.audio.delta"]:
            audio_b64 = resp.get("data", {}).get("audio", "")
            preview = audio_b64[:50] if audio_b64 else ""
            logging.info("接收到音频流的前50字符: %s", preview)
        else:
            logging.info("接收到消息: %s", message)

        if msg_type == "tts.connection.done":
            new_session_id = resp.get("data", {}).get("session_id")
            if new_session_id:
                session_id = new_session_id
                send_create(ws)
            else:
                logging.error("未能获取新的 session_id")
        elif msg_type == "tts.response.created":
            send_text(ws)
        elif msg_type == "tts.response.audio.delta":
            # 统计接收间隔
            current_time = time.time()
            if last_audio_time is None and text_start_time is not None:
                logging.info("从发送文本到接收第一个音频的间隔: %.3f 秒", current_time - text_start_time)
            elif last_audio_time is not None:
                logging.info("连续收到音频片段之间的间隔: %.3f 秒", current_time - last_audio_time)
            last_audio_time = current_time

            # 保存片段
            original_resp = resp
            audio_b64 = original_resp.get("data", {}).get("audio")
            status = original_resp.get("data", {}).get("status")
            if audio_b64:
                audio_chunks.append(audio_b64)
                chunk_file = save_chunk_audio(audio_b64, chunk_index)
                if chunk_file:
                    audio_chunk_files.append(chunk_file)
                chunk_index += 1

            # 若检测到 status 为 finished，则合并所有片段
            if status == "finished":
                logging.info("检测到 status finished，开始合并所有片段生成完整音频")
                merge_audio_chunks(audio_chunk_files)
        elif msg_type == "tts.response.error":
            logging.error("服务端返回错误: %s", resp)
        else:
            logging.warning("收到未处理的消息类型: %s", msg_type)
    except Exception as e:
        logging.error("解析消息出错: %s", e)

# ---------------------------
# 错误与关闭回调
# ---------------------------
def on_error(ws, error):
    if "Connection to remote host was lost" in str(error):
        return
    logging.error("WebSocket 错误: %s", error)

def on_close(ws, close_status_code, close_msg):
    logging.info("WebSocket 连接关闭: %s %s", close_status_code, close_msg)

def on_open(ws):
    logging.info("WebSocket 连接已打开")

# ---------------------------
# 主入口：启动 WebSocket 客户端
# ---------------------------
if __name__ == "__main__":
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