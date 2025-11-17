import websocket
from websocket import enableTrace
import json
import base64
from pathlib import Path
import logging
 
# realtime-API调用案例 

"""
client event.type
session.update  更新 session 配置，任何字段都可能随时更新，除了 "voice" 之外
input_audio_buffer.append 添加音频数据到输入缓冲区
input_audio_buffer.commit 提交输入缓冲区内容，开始处理
input_audio_buffer.clear 清空输入缓冲区
conversation.item.create 创建新对话/会话消息添加
conversation.item.delete 删除对话/会话消息
response.create 推理提交,指示服务器创建 Response
response.cancel 取消推理
"""

"""
server event.type
error 错误事件
session.created 创建session响应
session.updated 更新session响应
input_audio_buffer.speech_started 音频输入激活开始 （VAD）
input_audio_buffer.speech_stopped 音频输入激活结束 （VAD）
response.audio.delta 音频内容流式返回
response.audio.done 音频内容流式结束
response.audio_transcript.delta 音频内容文字流返回
response.audio_transcript.done 音频内容文字流结束
conversation.item.created 会话消息创建响应
conversation.item.deleted 会话消息删除响应
conversation.item.input_audio_transcription.completed 用户提交音频的转录结果完成
input_audio_buffer.committed 音频内容提交响应
input_audio_buffer.cleared 音频内容删除响应
response.output_item.added 推理有输出项目产生
response.output_item.done 推理有输出项目完成
response.content_part.added 推理的输出项目中有新的内容生成
response.content_part.done 推理的输出项目中有新的内容完成
response.created 推理创建响应
response.done 推理结束响应
"""
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")
STEPFUN_KEY="7pCX3CCD8ETk1a91odXoc4mpMwsydCCryyg0w4PsrfyNIgHGu9uU4A2ECtNUhTVB9"
# STEPFUN_KEY="Rpuq7AB40DaxoCkaZSoSeVt038L5C2UccPRMVuQ5HBsNbYOU5Pqe9HvbSn0NaGLM"
url = "wss://api.stepfun.com/v1/realtime?model=step-1o-audio"


# url = "wss://realtime.c.stepfun-inc.net/v1/realtime?model=step-audio-2-mini"
# STEPFUN_KEY = "2IgxcDYHHXcN3BR7M1zgMgH5csRbW3gKH9vVFhYFSSbc1ACgWlW3ylzBGdBffABms"


headers = {
  "Authorization": STEPFUN_KEY
}
event_id = ""
voice_id = "tianmeinvsheng"
voice_id = "cixingnansheng"
voice_id="qingchunshaonv"

close_flag = False

# 更新session
def send_update_session(ws):
  update_msg = {
    "event_id": event_id,
    "type": "session.update",
    "session": {
        "modalities": ["text", "audio"],
        "instructions": "你是由阶跃星辰提供的AI聊天助手，你擅长中文，英文，以及多种其他语言的对话。请使用默认女声与用户交流。",
        "voice": voice_id,
        "input_audio_format": "pcm16",
        "output_audio_format": "pcm16",
        "tools": [
          {
            "type": "web_search",
            "function": {
              "description": "网络搜索工具",
              "options": {
                "top_k": 5,
                "timeout_seconds": 3
              }
            }
          },
        ]
        # "temperature": 0
        # "turn_detection": {
        #     "type": "server_vad"
        # }
      }
    }
  ws.send(json.dumps(update_msg))


  # {'session': {'modalities': ['text', 'audio'], 'input_audio_format': 'pcm16', 'output_audio_format': 'pcm16', 
  #              'turn_detection': {'type': 'server_vad'}, 
  #              'instructions': '你是由北京赛博创立科技有限公司提供的AI聊天助手，你擅长中文，英文，以及多种其他语言的对话。', 
  #              'voice': 'voice-tone-H7aGRm0J0K'}, 'type': 'session.update', 'event_id': 'cef5140c-34b3-4f7d-b661-ab3272c75269'}


# 创建新对话/会话消息
def send_conversation_item_create(ws):
  conversation_item_create_msg = {
        "event_id": event_id,
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": "昨天发生了什么重大事件？"
                }
            ]
        }
    }
  ws.send(json.dumps(conversation_item_create_msg))

# 创建推理
def send_response_create(ws):
  response_create_msg = {
      "event_id": event_id,
      "type": "response.create",
      "response": {
        "modalities": [ "text" ]
      }
    }
  ws.send(json.dumps(response_create_msg))

# 添加音频数据到输入缓冲区event
def send_input_audio_buffer_append(ws):
  filepath=Path(__file__).parent / "./media/02_realtime_input.wav"
  # filepath=Path(__file__).parent / "input_audio/huhuibao.wav"
  audio_base64 = audio_to_base64(filepath)
  input_audio_buffer_append_msg = {
        "event_id": event_id,
        "type": "input_audio_buffer.append",
        "audio": audio_base64
    }
  ws.send(json.dumps(input_audio_buffer_append_msg))

# 提交输入缓冲区event
def send_input_audio_buffer_commit(ws):
  input_audio_buffer_commit_msg = {
        "event_id": event_id,
        "type": "input_audio_buffer.commit"
    }
  ws.send(json.dumps(input_audio_buffer_commit_msg))



# 清空输入缓冲区event
def send_input_audio_buffer_clear(ws):
  return json.dumps(
    {
        "event_id": event_id,
        "type": "input_audio_buffer.clear"
    }
  )

# 将音频文件转换为Base64编码字符串
def audio_to_base64(file_path):
    """
    将音频文件转换为Base64编码字符串
    
    参数:
        file_path (str): 音频文件路径(如: "audio.wav")
    
    返回:
        str: Base64编码的字符串
    """
    with open(file_path, "rb") as audio_file:
        audio_bytes = audio_file.read()
        return base64.b64encode(audio_bytes).decode('utf-8')

def on_message(ws, message):
  global event_id, close_flag
  try:
    data = json.loads(message)
    msg_type = data["type"]
    event_id = data["event_id"]
    # 针对音频消息，打印出 base64 字符串的前50字符
    if msg_type in ["response.audio.delta", "response.audio.done"]:
        audio_b64 = data.get("delta", "")
        temp_resp = dict(data)
        if "delta" in temp_resp:
            temp_resp["delta"] = audio_b64[:50] + "..."
        logging.info("接收到消息: %s", json.dumps(temp_resp, ensure_ascii=False))
    else:
        logging.info("接收到消息: %s", message) 
        pass
    
    if msg_type == "response.audio.delta":
        # 音频流式返回，处理base64保存音频
        pass
    elif msg_type == "response.audio_transcript.delta":
        # 音频文字流式返回
        print(data["delta"])
        pass
    elif msg_type == "response.done":
        # 推理结束，获取完整的响应文字
        pass
       
    if msg_type == "session.created":
      send_update_session(ws)
    elif msg_type == "session.updated":
      # 创建新对话/用户发送文字
      send_conversation_item_create(ws)
      # 启动推理
      send_response_create(ws)
    elif msg_type == "response.done" and not close_flag:
       # 初始化对话完成，发送音频到缓冲区
       send_input_audio_buffer_append(ws)
       # 提交缓冲区，开始处理
       send_input_audio_buffer_commit(ws)
       # 启动推理
       send_response_create(ws)
       close_flag = True
    elif msg_type == "response.audio_transcript.done":
       print(data["transcript"])
       pass
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
 
 
if __name__ == "__main__":
  print("StepFun Realtime 实时语音通话")
  print("连接服务器中...（按Ctrl+C退出）")
  # websocket.enableTrace(True)
  ws = websocket.WebSocketApp(
      url,
      header=headers,
      on_message=on_message,
      on_error=on_error,
      on_close=on_close,
      on_open=on_open
  )
 
  ws.run_forever(
    #dispatcher=rel, reconnect=5
  )  
  # rel.signal(2, rel.abort) 
  # rel.dispatch()