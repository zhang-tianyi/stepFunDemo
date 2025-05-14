# tts_batch_perf_async.py
import asyncio, csv, json, time, ssl, logging, configparser
from datetime import datetime, timedelta, timezone
from pathlib import Path

import aiohttp, pandas as pd
from tqdm.asyncio import tqdm_asyncio

# ── 基本配置 ──────────────────────────────────────────────
CONF_FILE   = "../config.ini"
INPUT_CSV   = "cases.csv"
CONCURRENCY = 50
VOICE_ID    = "voice-tone-Eog0tIPGwy"

tz_cn = timezone(timedelta(hours=8))        # 东八区

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")

# ── 读取配置 & 文本 ───────────────────────────────────────
cfg = configparser.ConfigParser()
cfg.read(CONF_FILE, encoding="utf-8")
API_KEY = cfg.get("step_api_prod", "key")
WS_BASE = cfg.get("step_api_prod", "wsurl")
WS_URL  = WS_BASE.rstrip("/") + "/realtime/audio?model=step-tts-mini-hjzd"

with open(INPUT_CSV, newline="", encoding="utf-8") as f:
    cases = [row[0].strip() for row in csv.reader(f) if row and row[0].strip()]

# ── 辅助：返回“YYYY年MM月DD日 HH时MM分SS秒mmm毫秒” 字符串 ──────────
def fmt_cn(dt: datetime) -> str:
    """将 datetime -> 中文日期时间字符串（毫秒 3 位）"""
    return dt.strftime("%Y年%m月%d日 %H时%M分%S秒%f")[:-3] + "毫秒"

# ── 单条 Case 任务 ───────────────────────────────────────
async def run_case(session: aiohttp.ClientSession, text: str, sem: asyncio.Semaphore):
    result = {
        "Case 文本": text,
        "时延 (ms)": "",
        "建连 Time": "",
        "完成 Time": "",
        "Session ID": ""
    }

    async with sem:
        intervals, t_send, last = [], 0.0, 0.0

        async with session.ws_connect(
            WS_URL,
            headers={"authorization": API_KEY},
            max_msg_size=0
        ) as ws:

            # 建连 = 握手成功瞬间
            result["建连 Time"] = fmt_cn(datetime.now(tz_cn))

            async for m in ws:
                if m.type is not aiohttp.WSMsgType.TEXT:
                    continue
                data = json.loads(m.data)
                tp   = data.get("type")

                if tp == "tts.connection.done":
                    result["Session ID"] = data["data"]["session_id"]
                    await ws.send_json({
                        "type": "tts.create",
                        "data": {
                            "session_id": result["Session ID"],
                            "voice_id": VOICE_ID,
                            "response_format": "mp3",
                            "mode": "sentence"
                        }
                    })

                elif tp == "tts.response.created":
                    t_send = time.time()
                    await ws.send_json({
                        "type": "tts.text.delta",
                        "data": {"session_id": result["Session ID"], "text": text}
                    })
                    await ws.send_json({
                        "type": "tts.text.done",
                        "data": {"session_id": result["Session ID"]}
                    })

                elif tp == "tts.response.audio.delta":
                    now = time.time()
                    gap = int((now - (last or t_send)) * 1000)
                    intervals.append(gap)
                    last = now

                elif tp in ("tts.response.audio.done", "tts.response.error"):
                    result["完成 Time"] = fmt_cn(datetime.now(tz_cn))
                    await ws.close()
                    break

        result["时延 (ms)"] = ", ".join(map(str, intervals))
    return result

# ── 主流程 ────────────────────────────────────────────────
async def main():
    sem     = asyncio.Semaphore(CONCURRENCY)
    timeout = aiohttp.ClientTimeout(sock_read=None)
    ssl_ctx = ssl.create_default_context() if WS_URL.startswith("wss://") else None

    async with aiohttp.ClientSession(timeout=timeout,
                                     connector=aiohttp.TCPConnector(ssl=ssl_ctx)) as session:
        tasks   = [run_case(session, t, sem) for t in cases]
        results = []

        for coro in tqdm_asyncio.as_completed(tasks, total=len(tasks)):
            res = await coro
            results.append(res)
            first = res["时延 (ms)"].split(",")[0] if res["时延 (ms)"] else "-"
            logging.info("完成：首包 %s ms | 分片 %d | %s",
                         first, len(res["时延 (ms)"].split(",")) if res["时延 (ms)"] else 0,
                         res["Case 文本"][:30])

    df   = pd.DataFrame(results)
    name = f"perf_results_{datetime.now(tz_cn):%Y%m%d_%H%M%S}.csv"
    df.to_csv(Path(name), index=False, encoding="utf-8-sig")
    print("✅ 结果已导出", name)

if __name__ == "__main__":
    asyncio.run(main())