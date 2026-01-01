# pip install requests

import requests
import json
from datetime import datetime

from services.config import CAIYUN_TOKEN, LONGITUDE, LATITUDE

def get_realtime_weather():
    """
    获取彩云天气实时数据
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36'
    }
    api_url = f"https://api.caiyunapp.com/v2.6/{CAIYUN_TOKEN}/{LONGITUDE},{LATITUDE}/realtime"  # ①使用官方文档中的token测试, 稳定需注册api. ②经纬度需换成所在地区经纬度. 
    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"请求API时发生错误: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"解析JSON数据时发生错误: {e}")
        return None

def convert_intensity_to_description(intensity):
    """
    将降水强度值转换为易读的描述
    """
    if intensity < 0.031:
        return "无雨/雪"
    elif 0.031 <= intensity < 0.25:
        return "小雨/雪"
    elif 0.25 <= intensity < 0.35:
        return "中雨/雪"
    elif 0.35 <= intensity < 0.48:
        return "大雨/雪"
    else:
        return "暴雨/雪"

def process_weather_data(data):
    """
    处理天气数据，提取并转换关注的内容
    """
    if not data or data.get('status') != 'ok':
        print("获取数据失败或数据状态异常")
        return None
    
    result = data.get('result', {})
    realtime = result.get('realtime', {})
    
    if not realtime:
        print("实时数据为空")
        return None
    
    # 1. 更新时间转换
    server_time = data.get('server_time', 0)
    update_time = datetime.fromtimestamp(server_time).strftime('%Y-%m-%d %H:%M:%S')
    
    # 2. 气温
    temperature = realtime.get('temperature', 'N/A')
    
    # 3. 湿度转换
    humidity_raw = realtime.get('humidity', 0)
    humidity_percent = round(humidity_raw * 100, 1) if humidity_raw != 'N/A' else 'N/A'
    
    # 4. 本地降水强度
    local_precipitation = realtime.get('precipitation', {}).get('local', {})
    local_intensity_raw = local_precipitation.get('intensity', 'N/A')
    local_intensity_desc = convert_intensity_to_description(local_intensity_raw) if local_intensity_raw != 'N/A' else 'N/A'
    
    # 5. 最近降水距离
    nearest_precipitation = realtime.get('precipitation', {}).get('nearest', {})
    nearest_distance = nearest_precipitation.get('distance', 'N/A')
    
    # 6. 最近降水强度
    nearest_intensity_raw = nearest_precipitation.get('intensity', 'N/A')
    nearest_intensity_desc = convert_intensity_to_description(nearest_intensity_raw) if nearest_intensity_raw != 'N/A' else 'N/A'
    
    # 提取更多有用信息（可选）
    skycon_map = {
        "PARTLY_CLOUDY_DAY": "多云（白天）",
        "PARTLY_CLOUDY_NIGHT": "多云（夜晚）",
        "CLEAR_DAY": "晴（白天）",
        "CLEAR_NIGHT": "晴（夜晚）",
        "CLOUDY": "阴",
        "LIGHT_RAIN": "小雨",
        "MODERATE_RAIN": "中雨",
        "HEAVY_RAIN": "大雨",
        "STORM_RAIN": "暴雨",
        "LIGHT_SNOW": "小雪",
        "MODERATE_SNOW": "中雪",
        "HEAVY_SNOW": "大雪",
        "STORM_SNOW": "暴雪"
    }
    
    skycon = realtime.get('skycon', 'N/A')
    skycon_desc = skycon_map.get(skycon, skycon)
    
    wind = realtime.get('wind', {})
    wind_speed = wind.get('speed', 'N/A')
    wind_direction = wind.get('direction', 'N/A')
    
    air_quality = realtime.get('air_quality', {})
    aqi = air_quality.get('aqi', {}).get('chn', 'N/A')
    
    return {
        '更新时间': update_time,
        '气温': f"{temperature}" if temperature != 'N/A' else 'N/A',
        '体感温度': f"{realtime.get('apparent_temperature', 'N/A')}" if realtime.get('apparent_temperature') != 'N/A' else 'N/A',
        '湿度': f"{humidity_percent}" if humidity_percent != 'N/A' else 'N/A',
        '天气状况': skycon_desc,
        '本地降水强度': local_intensity_desc,
        '本地降水强度值': local_intensity_raw,
        '最近降水距离': f"{nearest_distance}" if nearest_distance != 'N/A' else 'N/A',
        '最近降水强度': nearest_intensity_desc,
        '最近降水强度值': nearest_intensity_raw,
        '风速': f"{wind_speed}" if wind_speed != 'N/A' else 'N/A',
        '风向': f"{wind_direction}" if wind_direction != 'N/A' else 'N/A',
        '气压': f"{realtime.get('pressure', 'N/A')/100:.1f}" if realtime.get('pressure') != 'N/A' else 'N/A',
        '能见度': f"{realtime.get('visibility', 'N/A')}" if realtime.get('visibility') != 'N/A' else 'N/A',
        '空气质量指数(AQI)': aqi,
        'PM2.5': f"{air_quality.get('pm25', 'N/A')}" if air_quality.get('pm25') != 'N/A' else 'N/A'
    }

def display_weather_info(weather_info):
    """
    格式化显示天气信息
    """
    if not weather_info:
        return
    
    print("=" * 50)
    print("彩云天气实时数据")
    print("=" * 50)
    
    print(f"📅 更新时间: {weather_info['更新时间']}")
    print(f"🌡️  气温: {weather_info['气温']}")
    print(f"🤔 体感温度: {weather_info['体感温度']}")
    print(f"💧 湿度: {weather_info['湿度']}")
    print(f"☁️  天气状况: {weather_info['天气状况']}")
    print(f"🌧️  本地降水: {weather_info['本地降水强度']} (强度值: {weather_info['本地降水强度值']})")
    print(f"📍 最近降水距离: {weather_info['最近降水距离']}")
    print(f"🌧️  最近降水: {weather_info['最近降水强度']} (强度值: {weather_info['最近降水强度值']})")
    print(f"💨 风速: {weather_info['风速']}")
    print(f"🧭 风向: {weather_info['风向']}")
    print(f"📊 气压: {weather_info['气压']}")
    print(f"👁️  能见度: {weather_info['能见度']}")
    print(f"🌫️  空气质量(AQI): {weather_info['空气质量指数(AQI)']}")
    print(f"🌫️  PM2.5: {weather_info['PM2.5']}")
    print("=" * 50)

def main():
    
    print("正在获取实时天气数据...")
    
    # 获取天气数据
    weather_data = get_realtime_weather()
    
    if not weather_data:
        print("无法获取天气数据，请检查网络连接或API URL")
        return
    
    # 处理天气数据
    weather_info = process_weather_data(weather_data)
    
    # 显示天气信息
    display_weather_info(weather_info)
    
    # 可选：保存原始数据到文件
    save_raw = input("\n是否保存原始JSON数据到文件？(y/n): ")
    if save_raw.lower() == 'y':
        with open('weather_data.json', 'w', encoding='utf-8') as f:
            json.dump(weather_data, f, ensure_ascii=False, indent=2)
        print("原始数据已保存到 weather_data.json")

if __name__ == "__main__":
    main()