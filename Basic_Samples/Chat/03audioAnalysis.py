import time
import base64
import os
import subprocess
from openai import OpenAI


# 20250826:chat的audio输入存在已知问题，目前会出现500报错，在修

################################################
# 1) 读取配置
################################################
STEP_API_KEY = os.environ["STEPFUN_API_KEY"]
BASE_URL= os.environ['STEPFUN_ENDPOINT']

################################################
# 2) 使用 FFmpeg 将任意音频转成 16kHz 单声道 WAV
################################################
def convert_to_wav(input_path, output_path, sr=16000):
    """
    调用 FFmpeg 将任意音频转码成 WAV (16kHz, 单声道).
    如果 input_path 已经是合格的 WAV/MP3，可直接跳过此函数.
    """
    command = [
        "ffmpeg",
        "-y",             # 覆盖输出文件（若已存在）
        "-i", input_path,
        "-ar", str(sr),   # 采样率 16kHz
        "-ac", "1",       # 单声道
        output_path
    ]
    print(f"Running ffmpeg: {' '.join(command)}")
    subprocess.run(command, check=True)

################################################
# 3) 将音频文件转换为 Base64
################################################
def audio_to_base64(audio_path):
    with open(audio_path, "rb") as audio_file:
        encoded_string = base64.b64encode(audio_file.read())
    return encoded_string.decode('utf-8')

################################################
# 主逻辑
################################################
if __name__ == "__main__":
    
    # 初始化客户端
    client = OpenAI(api_key=STEP_API_KEY, base_url=BASE_URL)

    # 输入文件 (原始 MP3 或其他格式)
    input_audio_path = "../Audio/output/combined_audio.wav"
    # 转码后的文件
    converted_audio_path = "../Audio/output/converted_audio.wav"

    # 将输入文件转为标准 WAV
    convert_to_wav(input_audio_path, converted_audio_path, sr=16000)

    # 转成 Base64
    audio_base64 = audio_to_base64(converted_audio_path)

    # 加格式标识前缀
    full_audio_base64=f"data:audio/wav;base64,{audio_base64}"

    # 构造消息
    sys_prompt = "你可以分析语音"
    user_prompt = "音频内容是什么"

    # 这里设置最终调用的模型
    COMPLETION_MODEL = "step-1o-audio"

    messages = [
        {"role": "system", "content": sys_prompt},
        {
            "role": "user",
            "content": [
                {
                    "type": "input_audio",
                    "input_audio": {
                        "data": full_audio_base64,  # Base64+格式前缀
                        "format": "wav"       # 与最终文件一致
                    }
                },
                {
                    "type": "text",
                    "text": user_prompt
                }
            ]
        }
    ]

    time_start = time.time()
    # 发起请求 (stream=True 表示流式输出)
    response = client.chat.completions.create(
        messages=messages,
        model=COMPLETION_MODEL,
        stream=True
    )

    # 逐块打印输出
    i = 0
    for chunk in response:
        delta_text = chunk.choices[0].delta.content
        print(delta_text, end='', flush=True)

        # 记录首个字生成时间
        if i == 0:
            time_firstWord = time.time()
            elapsed_time = time_firstWord - time_start
            print(f"\n首字生成时间: {elapsed_time:.2f} 秒", end='')
        i += 1

    time_end = time.time()
    total_elapsed = time_end - time_start
    print(f"\n\n当前模型为 {COMPLETION_MODEL}")
    print(f"总生成时间: {total_elapsed:.2f} 秒")