# pip install fastapi uvicorn

from fastapi import FastAPI
from fastapi.responses import FileResponse
import uvicorn

from services.cai_yun import get_realtime_weather, process_weather_data
from services.get_db import get_recent_readings
from services.clothes_suggest import ask_ai
from services.config import HOST, PORT

app = FastAPI()

@app.get("/")
def index():
    """返回前端页面"""
    return FileResponse("index.html")

@app.get("/weather")
async def weather():
    """天气数据API"""
    try:
        d = await get_realtime_weather() if hasattr(get_realtime_weather, '__await__') else get_realtime_weather()
        w = process_weather_data(d)
        m = await get_recent_readings(1) if hasattr(get_recent_readings, '__await__') else get_recent_readings(1)
        ww = float(w['气温'])
        tw, tm = round(ww, 1), round(m[0]['temperature'], 1)
        a = await ask_ai(tw, tm) if hasattr(ask_ai, '__await__') else ask_ai(tw, tm)
        
        return {
            "forecast": tw,
            "monitor": tm,
            "weather": w['本地降水强度'],
            "nearest": w['最近降水距离'],
            "rain": w['最近降水强度'],
            "advice": a,
            "update": w['更新时间']
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)

