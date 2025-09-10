import requests
import os

STEP_API_KEY = os.environ["STEPFUN_API_KEY"]
BASE_URL= os.environ['STEPFUN_ENDPOINT']

def generate_speech(url, api_key, model, input_text, voice,voice_label, output_file):
    """
    发送请求生成语音并保存为MP3文件。
    :param api_key: 步进API密钥
    :param model: 使用的模型名称
    :param input_text: 要转换为语音的文本
    :param voice: 选择的声音类型
    :param output_file: 保存音频的文件名
    """
    # 请求头
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    # 请求数据
    data = {
        "model": model,
        "input": input_text,
        "voice": voice,
        "voice_label":voice_label,
        "response_format":"wav"
        # "speed":2,
        # "volume":0.1
    }

    try:
        # 发送POST请求
        response = requests.post(url, headers=headers, json=data)
        print("响应对象:", response)
        response.raise_for_status()  # 如果响应状态码不是200，将抛出HTTPError异常

        # 打印接收到的headers
        print("接收到的headers:", response.headers)

        # 将响应内容写入MP3文件
        with open(output_file, 'wb') as f:
            f.write(response.content)

        print(f"语音已成功保存为 {output_file}")

    except requests.exceptions.HTTPError as http_err:
        print(f'HTTP错误: {http_err} - {response.text}')
    except Exception as err:
        print(f'其他错误: {err}')


if __name__ == "__main__":
    # 从环境变量获取API密钥
    url = BASE_URL + "/audio/speech"

    if not STEP_API_KEY:
        raise ValueError("请设置环境变量 STEP_API_KEY")

    # 设置请求参数
    model = "step-tts-mini"
    input_text = "一个知己就像一面镜子，反应出我们天性中最优美的一部分。人的一生中有大大小小的等待，人渐渐忘记了自己等待的是什么。"
    voice = "wenrougongzi"
    voice_label={"language":"粤语"}#{"style":"慢速"}#{"emotion":"非常生气"} 
    output_file = "output/测试音频1.wav"

    # 生成语音并保存
    generate_speech(url, STEP_API_KEY, model, input_text, voice,voice_label, output_file)