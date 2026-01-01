# 树莓派魔镜
[ENGLISH](README_EN.md)

## 功能简介
从 **彩云天气 API** 和 **米家蓝牙温湿度计2** 获取预报天气与实际环境数据，并通过 AI 服务生成个性化的着装建议。

## 使用说明

### 1. 安装依赖
```bash
pip install bleak bthome-ble requests openai fastapi uvicorn
```
### 2. 配置脚本
编辑 services/config.py 文件，配置以下参数：
```python
# 设备配置
DEVICE_MAC = "A4:C1:38:XX:XX:XX"  # 米家蓝牙温湿度计2的MAC地址

# 彩云天气 API
CAIYUN_TOKEN = "your_caiyun_token_here"  # 彩云天气API令牌
LONGITUDE = "116.404"  # 经度（示例：北京）
LATITUDE = "39.915"    # 纬度（示例：北京）

# AI 服务配置
AI_API_KEY = "sk-your-api-key-here"  # AI服务API密钥（如OpenAI）
AI_BASE_URL = "https://api.openai.com/v1"  # AI服务API地址

# 服务器配置
HOST = "127.0.0.1"  # 监听地址
PORT = 8000         # 监听端口
```

#### 获取配置信息
- 设备 MAC 地址：
> 使用蓝牙扫描工具（如 bluetoothctl、nRF Connect）
> 或通过[Tokens-Extractor](https://github.com/PiotrMachowski/Xiaomi-cloud-tokens-extractor)获取

- 彩云天气 Token：
> 访问彩云天气开放平台
> 注册开发者账号并创建应用

- 获取经纬度坐标：
> 使用地图服务（如百度地图、Google地图）
> 或使用在线坐标查询工具

- AI API Key：
> 注册相应的AI服务（如OpenAI、DeepSeek、智谱AI等）
> 在账户设置中创建API密钥
> 如使用不同服务，需相应修改 AI_BASE_URL

### 3. 初始化数据库
```bash
python LYWSD03MMC_db.py
```
运行后选择选项 2 开始读取设备数据，直到终端提示"数据保存正常"。
注意：请确保设备已开启蓝牙并处于可连接状态，可能需要进行多次尝试。

### 4. 启动应用
```bash
python main.py
```

### 5. 访问应用
打开浏览器访问 http://127.0.0.1:8000
按 F11 键进入全屏模式，获得最佳显示效果
如需调整自动刷新时间，可编辑 index.html 第 245 行：
```javascript
// 默认每天 06:50 自动刷新页面
// 可修改时间或注释此行取消定时刷新
scheduleClick(6, 50);
```

## 项目结构
```text
├── index.html              # 前端页面（HTML + CSS + JavaScript）
├── LYWSD03MMC_db.py        # 蓝牙温度计数据读取与存储模块
├── main.py                 # FastAPI 主程序（后端服务）
└── services/               # 服务模块目录
    ├── cai_yun.py          # 彩云天气API接口封装
    ├── clothes_suggest.py  # AI着装建议生成服务
    ├── config.py           # 配置文件（需用户编辑）
    ├── get_db.py           # 本地温湿度数据库查询接口
    └── get_rtsp.py         # RTSP摄像头接口（预留功能）
```
