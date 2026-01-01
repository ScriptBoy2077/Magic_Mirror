# Raspberry Pi Magic Mirror

## Overview
Retrieve weather forecasts and actual environmental data from **Caiyun Weather API** and **Xiaomi Bluetooth Thermometer/Hygrometer 2**, then generate personalized clothing suggestions via AI services.

## Usage Instructions

### 1. Install Dependencies
```bash
pip install bleak bthome-ble requests openai fastapi uvicorn
```

### 2. Configure the Script
Edit the `services/config.py` file to configure the following parameters:
```python
# Device Configuration
DEVICE_MAC = "A4:C1:38:XX:XX:XX"  # MAC address of Xiaomi Bluetooth Thermometer/Hygrometer 2

# Caiyun Weather API
CAIYUN_TOKEN = "your_caiyun_token_here"  # Caiyun Weather API token
LONGITUDE = "116.404"  # Longitude (Example: Beijing)
LATITUDE = "39.915"    # Latitude (Example: Beijing)

# AI Service Configuration
AI_API_KEY = "sk-your-api-key-here"  # AI Service API Key (e.g., OpenAI)
AI_BASE_URL = "https://api.openai.com/v1"  # AI Service API Base URL

# Server Configuration
HOST = "127.0.0.1"  # Host address to listen on
PORT = 8000         # Port to listen on
```

#### Obtaining Configuration Information
- Device MAC Address:
> Use a Bluetooth scanning tool (e.g., `bluetoothctl`, `nRF Connect`)
> or obtain it via [Tokens-Extractor](https://github.com/PiotrMachowski/Xiaomi-cloud-tokens-extractor)

- Caiyun Weather Token:
> Visit the Caiyun Weather Open Platform
> Register a developer account and create an application

- Obtaining Latitude and Longitude Coordinates:
> Use a map service (e.g., Baidu Maps, Google Maps)
> or use an online coordinate lookup tool

- AI API Key:
> Register for the corresponding AI service (e.g., OpenAI, DeepSeek, Zhipu AI, etc.)
> Create an API key in your account settings
> If using a different service, modify the `AI_BASE_URL` accordingly

### 3. Initialize the Database
```bash
python LYWSD03MMC_db.py
```
After running, choose option 2 to start reading device data. Continue until the terminal displays "Data saved successfully".
Note: Ensure the device has Bluetooth enabled and is in a connectable state. Multiple attempts may be required.

### 4. Start the Application
```bash
python main.py
```

### 5. Access the Application
Open your browser and navigate to http://127.0.0.1:8000
Press F11 to enter fullscreen mode for the best viewing experience.
To adjust the auto-refresh time, edit line 245 in `index.html`:
```javascript
// Default: Automatically refresh the page daily at 06:50
// You can modify the time or comment out this line to disable scheduled refresh
scheduleClick(6, 50);
```

## Project Structure
```text
├── index.html              # Frontend page (HTML + CSS + JavaScript)
├── LYWSD03MMC_db.py        # Bluetooth thermometer data reading and storage module
├── main.py                 # FastAPI main application (backend service)
└── services/               # Service modules directory
    ├── cai_yun.py          # Caiyun Weather API wrapper
    ├── clothes_suggest.py  # AI clothing suggestion generation service
    ├── config.py           # Configuration file (to be edited by user)
    ├── get_db.py           # Local temperature/humidity database query interface
    └── get_rtsp.py         # RTSP camera interface (reserved for future use)
```
