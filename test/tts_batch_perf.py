# tts_batch_perf.py
import websocket, json, time, csv, os, configparser, logging
import pandas as pd
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# -------------------------------------------------
# 1) 读取配置 & 输入
# -------------------------------------------------
def read_config():
    cfg = configparser.ConfigParser()
    cfg.read('../config.ini', encoding='utf-8')
    key  = cfg.get('step_api_prod', 'key')
    wsurl= cfg.get('step_api_prod', 'wsurl')
    return key, wsurl

API_KEY, WS_BASE = read_config()
VOICE_ID = "voice-tone-Eog0tIPGwy"
WS_URL   = WS_BASE + "/realtime/audio?model=step-tts-mini"

cases = []
with open('cases.csv', newline='', encoding='utf-8') as f:
    for row in csv.reader(f):
        if row and row[0].strip():
            cases.append(row[0].strip())

results = []

# -------------------------------------------------
# 2) WebSocket 事件处理
# -------------------------------------------------
def run_single(text: str):
    perf   = dict(text=text, interval_ms=0, connect_time='', done_time='', sid='')
    t_text = 0.0
    last   = 0.0

    def on_message(ws, message):
        nonlocal perf, t_text, last
        msg = json.loads(message)
        tp  = msg.get("type")

        if tp == "tts.connection.done":
            perf['sid'] = msg['data']['session_id']
            perf['connect_time'] = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            ws.send(json.dumps({        # tts.create
                "type":"tts.create",
                "data":{
                    "session_id": perf['sid'],
                    "voice_id": VOICE_ID,
                    "response_format":"mp3",
                    "mode":"sentence"
                }
            }))
        elif tp == "tts.response.created":
            t_text = time.time()
            ws.send(json.dumps({        # tts.text.delta
                "type":"tts.text.delta",
                "data":{"session_id": perf['sid'], "text": text}
            }))
            ws.send(json.dumps({        # tts.text.done
                "type":"tts.text.done",
                "data":{"session_id": perf['sid']}
            }))
        elif tp == "tts.response.audio.delta":
            now = time.time()
            if perf['interval_ms']==0 and t_text:          # 首包
                perf['interval_ms'] = int((now - t_text)*1000)
            last = now
        elif tp in ("tts.response.audio.done", "tts.response.error"):
            perf['done_time'] = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            ws.close()

    ws = websocket.WebSocketApp(
        WS_URL,
        header=[f"authorization: {API_KEY}"],
        on_message=on_message,
        on_error=lambda ws,e: logging.error("WS error %s",e),
        on_close=lambda ws,code,msg: None
    )
    ws.run_forever()
    return perf

# -------------------------------------------------
# 3) 顺序执行所有 Case
# -------------------------------------------------
for idx, text in enumerate(cases, 1):
    logging.info(">>> [%d/%d] %s", idx, len(cases), text[:30]+"..." if len(text)>30 else text)
    res = run_single(text)
    results.append(res)
    logging.info("<<< 完成，首包时延 %d ms\n", res['interval_ms'])

# -------------------------------------------------
# 4) 导出结果 CSV
# -------------------------------------------------
df = pd.DataFrame(results)
outfile = f"perf_results_{datetime.now():%Y%m%d_%H%M%S}.csv"
df.rename(columns={
    'text':'Case 文本',
    'interval_ms':'时延 (ms)',
    'connect_time':'建连 Time',
    'done_time':'完成 Time',
    'sid':'Session ID'
}).to_csv(outfile, index=False, encoding='utf-8-sig')
logging.info("结果已导出到 %s", outfile)