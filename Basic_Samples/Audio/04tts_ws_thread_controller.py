import base64
import json
import sys
import os

import pyaudio
from PyQt5.QtNetwork import QNetworkRequest
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QPushButton, QLabel
from PyQt5.QtWebSockets import QWebSocket
from PyQt5.QtCore import QUrl, QTimer


def get_start_event(sid):
    return json.dumps(
        {
            "type": "tts.create",
            "data": {
                "session_id": sid,
                "voice_id": "qinqienvsheng",
                "response_format": "wav",
                "volume_ratio": 1.0,
                "mode": 'sentence',  # 生成模式，可选项为 sentence 和 default。 default 表示按字生成，适合大模型流式生成场景，sentence 表示按句生成，
                "speed_ratio": 1.0,
                "sample_rate": 16000
            },
        }
    )

def get_end_event(sid):
    return json.dumps({
            # "type": "tts.text.done",
            "type": "tts.text.flush",
            "data": {
                "session_id": sid
            }
    })

def build_text(sid, text):
    return json.dumps(
        {
            "type": "tts.text.delta",
            "data": {
                "session_id": sid,
                "text": text
            }
        }
    )


class WebSocketClient(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('WebSocket 客户端')
        self.resize(500, 400)

        # UI组件
        self.status_label = QLabel('状态: 未连接')
        self.message_display = QTextEdit()
        self.message_display.setReadOnly(True)
        self.message_input = QTextEdit()
        self.send_button = QPushButton('发送')
        self.connect_button = QPushButton('连接')

        # 布局
        layout = QVBoxLayout()
        layout.addWidget(self.status_label)
        layout.addWidget(QLabel('接收消息:'))
        layout.addWidget(self.message_display)
        layout.addWidget(QLabel('发送消息:'))
        layout.addWidget(self.message_input)
        layout.addWidget(self.send_button)
        layout.addWidget(self.connect_button)
        self.setLayout(layout)

        # WebSocket
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_interval = 3000  # ms
        self.websocket = QWebSocket()
        self.websocket.connected.connect(self.on_connected)
        self.websocket.disconnected.connect(self.on_disconnected)
        self.websocket.textMessageReceived.connect(self.on_message_received)

        # 按钮事件
        self.send_button.clicked.connect(self.send_message)
        self.connect_button.clicked.connect(self.toggle_connection)

        # 连接状态
        self.is_connected = False
        self.session_id = ''

        self.audio_interface = pyaudio.PyAudio()
        self.stream = self.audio_interface.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            output=True,
            frames_per_buffer=1024,  # 添加缓冲区大小
            # stream_callback=self.callback
        )

    def toggle_connection(self):
        if not self.is_connected:
            # 连接WebSocket
            url = QUrl("wss://api.stepfun.com/v1/realtime/audio?model=step-tts-mini")
            request = QNetworkRequest(url)
            STEP_API_KEY = os.environ["STEPFUN_API_KEY"]
            auth_header = f"Bearer {STEP_API_KEY}".encode("utf-8")
            request.setRawHeader(b"Authorization", auth_header)
            
            self.websocket.open(request)
        else:
            self.websocket.close()

    def on_connected(self):
        self.is_connected = True
        self.status_label.setText('状态: 已连接')
        self.connect_button.setText('断开')
        self.message_display.append('已连接到服务器')

    def on_disconnected(self):
        self.is_connected = False
        self.status_label.setText('状态: 未连接')
        self.connect_button.setText('连接')
        self.message_display.append('已断开连接')
        self.schedule_reconnect()

    def get_bytes_after_wavefmt(self, binary_data):
        # 注意二进制数据中使用b前缀的字节串
        marker = b"WAVEfmt "
        index = binary_data.find(marker)

        if index == -1:
            return b""  # 返回空字节串
        else:
            # 从标记结束位置开始提取
            return binary_data[index + len(marker):]

    def get_data_before_brace(self, input_str):
        # 查找第一个'{'的位置
        try:
            brace_index = input_str.find('{')

            if brace_index == -1:
                # 如果没有找到'{'，返回原始字符串或空（根据需求选择）
                return input_str  # 或者 return ""
            else:
                # 返回'{'之前的所有字符（不包含'{'本身）
                return input_str[:brace_index]
        except BaseException as e:
            print(e)

    def extract_audio_data(self, wav_data):
        """
        从WAV数据中精确提取音频数据，跳过所有头部信息
        """
        try:
            # 验证WAV文件头
            if len(wav_data) < 12 or wav_data[:4] != b'RIFF' or wav_data[8:12] != b'WAVE':
                print("警告: 不是有效的WAV文件格式")
                return wav_data[44:]  # 回退到原来的方法
            
            # 查找"data"块的位置
            data_marker = b"data"
            data_index = wav_data.find(data_marker)
            
            if data_index == -1:
                print("警告: 未找到data标记，使用默认44字节偏移")
                return wav_data[44:]  # 回退到原来的方法
            
            # 找到data标记后，跳过"data"字符串(4字节)和数据长度(4字节)
            audio_start = data_index + 8  # 4字节"data" + 4字节长度
            
            # 验证是否超出数据范围
            if audio_start >= len(wav_data):
                print("警告: data标记位置超出数据范围")
                return wav_data[44:]  # 回退到原来的方法
            
            # 读取data块的长度（4字节小端序）
            data_length = int.from_bytes(wav_data[data_index+4:data_index+8], byteorder='little')
            print(f"WAV文件信息:")
            print(f"  - 文件总长度: {len(wav_data)} 字节")
            print(f"  - data标记位置: {data_index}")
            print(f"  - data块长度: {data_length} 字节")
            print(f"  - 音频数据开始位置: {audio_start}")
            print(f"  - 音频数据结束位置: {audio_start + data_length}")
            
            # 提取纯音频数据
            pure_audio = wav_data[audio_start:audio_start + data_length]
            
            # 验证提取的数据长度
            if len(pure_audio) != data_length:
                print(f"警告: 提取的音频数据长度({len(pure_audio)})与声明的长度({data_length})不匹配")
            
            return pure_audio
            
        except Exception as e:
            print(f"提取音频数据时出错: {e}")
            return wav_data[44:]  # 出错时回退到原来的方法

    def on_message_received(self, message):

        data = json.loads(message)

        self.session_id = data["data"]["session_id"]
        event_type = data["type"]
        if event_type == "tts.connection.done":
            self.websocket.sendTextMessage(get_start_event(self.session_id))
        if event_type == "tts.response.sentence.start":
            print("开始音频流播放...")
            try:
                self.stream.start_stream()
            except Exception as e:
                print(f"启动音频流失败: {e}")
        if event_type == "tts.response.audio.delta" and 'unfinished' == data['data']['status']:
            print("=" * 50)
            # 解码Base64音频数据
            audio_data = base64.b64decode(data['data']['audio'])
            print(f"原始音频数据长度: {len(audio_data)} 字节")
            
            # 精确提取音频数据
            pure_audio_data = self.extract_audio_data(audio_data)
            print(f"提取的纯音频数据长度: {len(pure_audio_data)} 字节")
            
            # 播放音频
            self.stream.write(pure_audio_data)
            print("=" * 50)
        if event_type == "tts.response.sentence.end":
            print("结束音频流播放...")
            try:
                self.stream.stop_stream()
            except Exception as e:
                print(f"停止音频流失败: {e}")

        if 'audio' in data['data']:
            data['data']['audio'] = ''
        self.message_display.append(f'收到: {json.dumps(data)}')

    def send_message(self):
        if not self.is_connected:
            self.message_display.append('错误: 未连接到服务器')
            return

        message = self.message_input.toPlainText()

        if message:
            self.websocket.sendTextMessage(build_text(self.session_id, message))
            self.websocket.sendTextMessage(get_end_event(self.session_id))
            self.message_input.clear()
            self.message_display.append(f'发送: {message}')

    def schedule_reconnect(self):
        if self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            delay = min(self.reconnect_interval * self.reconnect_attempts, 15000)
            print(f"Reconnecting in {delay / 1000} seconds (attempt {self.reconnect_attempts})")
            QTimer.singleShot(delay, self.toggle_connection)
        else:
            print("Max reconnection attempts reached")

    def closeEvent(self, event):
        """
        窗口关闭时的清理工作
        """
        try:
            if hasattr(self, 'stream') and self.stream:
                self.stream.stop_stream()
                self.stream.close()
            if hasattr(self, 'audio_interface') and self.audio_interface:
                self.audio_interface.terminate()
        except Exception as e:
            print(f"清理音频资源时出错: {e}")
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    client = WebSocketClient()
    client.show()
    sys.exit(app.exec_())
