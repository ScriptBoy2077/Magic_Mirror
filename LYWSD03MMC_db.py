# pip install bleak bthome-ble

'''
quick_read_and_save() 函数适合自动化脚本调用
get_latest_reading() 函数获取最新一条数据
clear_all_data() 函数清空所有数据
日常使用：运行 main() 进入交互菜单
自动化脚本：调用 asyncio.run(quick_read_and_save())
数据存储：每次读取的温湿度会保存为同一行，数据库永远只保留3条最新记录
'''


import asyncio
from bleak import BleakClient
from datetime import datetime
import struct
import sqlite3
import json
from typing import List, Dict, Optional
import os

from services.config import DEVICE_MAC


# 设备信息（根据你的发现）
DEVICE_MAC = DEVICE_MAC  # 替换为你的设备地址

# 服务UUID（标准蓝牙环境传感服务）
ENVIRONMENTAL_SENSING_SERVICE = "0000181a-0000-1000-8000-00805f9b34fb"

# 特征值UUID（标准定义）
TEMPERATURE_CHAR = "00002a6e-0000-1000-8000-00805f9b34fb"  # 温度
HUMIDITY_CHAR = "00002a6f-0000-1000-8000-00805f9b34fb"    # 湿度
BATTERY_SERVICE = "0000180f-0000-1000-8000-00805f9b34fb"   # 电池服务
BATTERY_CHAR = "00002a19-0000-1000-8000-00805f9b34fb"      # 电池电平

class SensorDatabase:
    """SQLite数据库管理器 - 仅保存最近3组数据"""
    
    def __init__(self, db_path: str = "sensor_data.db", max_records: int = 3):
        self.db_path = db_path
        self.max_records = max_records  # 最大保存记录数
        self.init_database()
    
    def init_database(self):
        """初始化数据库和表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建传感器数据表（简化版）
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            device_mac TEXT NOT NULL,
            temperature REAL,
            humidity REAL,
            battery INTEGER
        )
        ''')
        
        # 创建索引以提高查询性能
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_timestamp ON sensor_readings(timestamp)
        ''')
        
        conn.commit()
        conn.close()
        print(f"✓ 数据库已初始化: {self.db_path} (最多保存{self.max_records}条记录)")
    
    def save_reading(self, data: Dict) -> bool:
        """
        保存传感器数据到数据库，并确保只保留最近3组数据
        
        Args:
            data: 包含传感器数据的字典
            
        Returns:
            是否保存成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 准备数据
            timestamp = data.get("timestamp", datetime.now().isoformat())
            device_mac = data.get("device_mac", DEVICE_MAC)
            temperature = data.get("temperature")
            humidity = data.get("humidity")
            battery = data.get("battery")
            
            # 插入新数据
            cursor.execute('''
            INSERT INTO sensor_readings 
            (timestamp, device_mac, temperature, humidity, battery)
            VALUES (?, ?, ?, ?, ?)
            ''', (timestamp, device_mac, temperature, humidity, battery))
            
            # 检查并清理超出限制的旧数据
            self._cleanup_old_data(cursor)
            
            conn.commit()
            conn.close()
            
            print(f"✓ 数据已保存到数据库")
            return True
            
        except Exception as e:
            print(f"✗ 保存数据失败: {e}")
            return False
    
    def _cleanup_old_data(self, cursor):
        """清理超出最大记录数的旧数据"""
        # 获取总记录数
        cursor.execute('SELECT COUNT(*) FROM sensor_readings')
        count = cursor.fetchone()[0]
        
        # 如果超过最大记录数，删除最旧的记录
        if count > self.max_records:
            delete_count = count - self.max_records
            cursor.execute(f'''
            DELETE FROM sensor_readings 
            WHERE id IN (
                SELECT id FROM sensor_readings 
                ORDER BY timestamp ASC 
                LIMIT {delete_count}
            )
            ''')
            print(f"✓ 已清理 {delete_count} 条旧数据，保留最近 {self.max_records} 条")
    
    def get_recent_readings(self, limit: int = None) -> List[Dict]:
        """
        获取最近的传感器读数
        
        Args:
            limit: 返回的记录数，None表示返回所有（最多3条）
            
        Returns:
            传感器数据列表，按时间倒序排列
        """
        if limit is None:
            limit = self.max_records
            
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 使返回结果为字典形式
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM sensor_readings 
        ORDER BY timestamp DESC 
        LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        # 转换为字典列表
        result = []
        for row in rows:
            row_dict = dict(row)
            result.append(row_dict)
        
        return result
    
    def get_latest_reading(self) -> Optional[Dict]:
        """获取最新的一组数据"""
        readings = self.get_recent_readings(limit=1)
        return readings[0] if readings else None
    
    def clear_all_data(self):
        """清空所有数据"""
        confirm = input("确定要清空所有数据吗？(y/N): ").strip().lower()
        if confirm == 'y':
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM sensor_readings')
            conn.commit()
            conn.close()
            print("✓ 所有数据已清空")
            return True
        return False

def parse_temperature(data: bytes) -> float:
    """
    解析温度数据 (特征值 0x2A6E)
    格式: 有符号16位整数，单位0.01°C (IEEE 11073-20601 FLOAT-Type)
    """
    if len(data) >= 2:
        # 小端序有符号16位整数
        raw_value = struct.unpack('<h', data[:2])[0]  # <h = little-endian short
        return raw_value / 100.0
    raise ValueError("温度数据长度不足")

def parse_humidity(data: bytes) -> float:
    """
    解析湿度数据 (特征值 0x2A6F)
    格式: 无符号16位整数，单位0.01% (IEEE 11073-20601 FLOAT-Type)
    """
    if len(data) >= 2:
        # 小端序无符号16位整数
        raw_value = struct.unpack('<H', data[:2])[0]  # <H = little-endian unsigned short
        return raw_value / 100.0
    raise ValueError("湿度数据长度不足")

def parse_battery(data: bytes) -> int:
    """
    解析电池数据 (特征值 0x2A19)
    格式: 无符号8位整数，单位1%
    """
    if len(data) >= 1:
        return data[0]
    raise ValueError("电池数据长度不足")

async def read_sensor_data():
    """连接设备并读取温湿度数据"""
    print(f"正在连接设备 {DEVICE_MAC}...")
    
    async with BleakClient(DEVICE_MAC) as client:
        # 检查连接状态
        if not client.is_connected:
            print("连接失败")
            return None
        
        print("✓ 设备已连接")
        print(f"设备名称: {await client.get_device_name()}")
        
        temperature = None
        humidity = None
        battery = None
        
        # 读取温度
        try:
            temp_data = await client.read_gatt_char(TEMPERATURE_CHAR)
            temperature = parse_temperature(temp_data)
            print(f"🌡️  温度: {temperature:.2f}°C")
        except Exception as e:
            print(f"读取温度失败: {e}")
        
        # 读取湿度
        try:
            hum_data = await client.read_gatt_char(HUMIDITY_CHAR)
            humidity = parse_humidity(hum_data)
            print(f"💧  湿度: {humidity:.2f}%")
        except Exception as e:
            print(f"读取湿度失败: {e}")
        
        # 尝试读取电池电量
        try:
            battery_data = await client.read_gatt_char(BATTERY_CHAR)
            battery = parse_battery(battery_data)
            print(f"🔋  电池: {battery}%")
        except Exception as e:
            print(f"读取电池失败 (可能不支持): {e}")
        
        # 显示原始数据（调试用）
        if temperature is not None:
            hex_data = temp_data.hex()
            print(f"温度原始数据: {hex_data}")
        
        if humidity is not None:
            hex_data = hum_data.hex()
            print(f"湿度原始数据: {hex_data}")
        
        # 只有当温度和湿度都读取成功时才返回完整数据
        if temperature is not None and humidity is not None:
            return {
                "temperature": temperature,
                "humidity": humidity,
                "battery": battery,
                "timestamp": datetime.now().isoformat(),
                "device_mac": DEVICE_MAC
            }
        else:
            print("✗ 读取数据不完整，未保存到数据库")
            return None

async def monitor_real_time(db: SensorDatabase):
    """实时监控模式（订阅通知）并自动保存到数据库"""
    print(f"启动实时监控 {DEVICE_MAC}...")
    
    # 存储临时数据
    temp_data = {'temperature': None, 'humidity': None, 'last_update': None}
    
    def temperature_handler(sender, data):
        """温度变化回调"""
        try:
            temp = parse_temperature(data)
            temp_data['temperature'] = temp
            temp_data['last_update'] = datetime.now()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🌡️ 温度更新: {temp:.2f}°C")
            
            # 检查是否应该保存数据（当温度和湿度都更新时）
            _check_and_save(db, temp_data)
        except Exception as e:
            print(f"解析温度通知失败: {e}")
    
    def humidity_handler(sender, data):
        """湿度变化回调"""
        try:
            hum = parse_humidity(data)
            temp_data['humidity'] = hum
            temp_data['last_update'] = datetime.now()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 💧 湿度更新: {hum:.2f}%")
            
            # 检查是否应该保存数据（当温度和湿度都更新时）
            _check_and_save(db, temp_data)
        except Exception as e:
            print(f"解析湿度通知失败: {e}")
    
    async with BleakClient(DEVICE_MAC) as client:
        # 启用温度通知
        await client.start_notify(TEMPERATURE_CHAR, temperature_handler)
        print("✓ 温度通知已启用")
        
        # 启用湿度通知
        await client.start_notify(HUMIDITY_CHAR, humidity_handler)
        print("✓ 湿度通知已启用")
        
        print("实时监控中... 按Ctrl+C停止")
        print("-" * 40)
        
        try:
            # 保持连接，等待通知
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n停止监控...")
            await client.stop_notify(TEMPERATURE_CHAR)
            await client.stop_notify(HUMIDITY_CHAR)

def _check_and_save(db: SensorDatabase, temp_data: dict):
    """检查并保存数据（当温度和湿度都有效时）"""
    if temp_data['temperature'] is not None and temp_data['humidity'] is not None:
        # 保存到数据库
        db.save_reading({
            "temperature": temp_data['temperature'],
            "humidity": temp_data['humidity'],
            "timestamp": datetime.now().isoformat(),
            "device_mac": DEVICE_MAC
        })
        # 重置临时数据
        temp_data['temperature'] = None
        temp_data['humidity'] = None

async def discover_services():
    """发现设备所有服务和特征值（调试用）"""
    print(f"扫描设备 {DEVICE_MAC} 的服务...")
    
    async with BleakClient(DEVICE_MAC) as client:
        services = await client.get_services()
        
        print(f"找到 {len(services.services)} 个服务:")
        print("=" * 60)
        
        for service in services:
            print(f"\n服务: {service.uuid}")
            print(f"描述: {service.description}")
            print(f"特征值数量: {len(service.characteristics)}")
            
            for char in service.characteristics:
                props = char.properties
                prop_str = ', '.join(props)
                print(f"  └─ 特征值: {char.uuid}")
                print(f"     描述: {char.description}")
                print(f"     属性: {prop_str}")
                
                # 尝试读取可读特征值
                if "read" in props:
                    try:
                        value = await client.read_gatt_char(char.uuid)
                        hex_str = value.hex()
                        print(f"     数据({len(value)}字节): {hex_str}")
                    except Exception as e:
                        print(f"     读取失败: {e}")

def display_recent_data(db: SensorDatabase):
    """显示最近的3组数据"""
    print("\n" + "="*60)
    print(f"最近{db.max_records}组传感器数据:")
    print("="*60)
    
    recent_data = db.get_recent_readings()
    
    if not recent_data:
        print("暂无数据")
        return
    
    for i, data in enumerate(recent_data, 1):
        print(f"\n记录 #{i}:")
        print(f"  时间: {data['timestamp']}")
        print(f"  温度: {data['temperature']:.2f}°C")
        print(f"  湿度: {data['humidity']:.2f}%")
        
        if data.get('battery') is not None:
            print(f"  电池: {data['battery']}%")
        
        print(f"  设备: {data['device_mac']}")

def main():
    """主菜单"""
    import sys
    
    # 初始化数据库（只保存3条记录）
    db = SensorDatabase(max_records=3)
    
    while True:
        print("\n" + "=" * 50)
        print("米家温湿度计2 (ATC固件) 数据获取工具")
        print("=" * 50)
        print("1. 单次读取温湿度并保存")
        print("2. 实时监控模式（自动保存）")
        print("3. 发现所有服务（调试）")
        print("4. 查看最近数据")
        print("5. 清空所有数据")
        print("6. 退出")
        print("-" * 50)
        
        choice = input("请选择 (1-6): ").strip()
        
        try:
            if choice == "1":
                # 单次读取并保存到数据库
                data = asyncio.run(read_sensor_data())
                
                if data:
                    # 保存到数据库
                    success = db.save_reading(data)
                    if success:
                        # 显示最新数据
                        display_recent_data(db)
                else:
                    print("读取数据失败或数据不完整")
                    
            elif choice == "2":
                # 实时监控
                asyncio.run(monitor_real_time(db))
                
            elif choice == "3":
                # 发现服务
                asyncio.run(discover_services())
                
            elif choice == "4":
                # 查看最近数据
                display_recent_data(db)
                
            elif choice == "5":
                # 清空所有数据
                db.clear_all_data()
                
            elif choice == "6":
                print("再见！")
                sys.exit(0)
                
            else:
                print("无效选择，请重试")
                
        except KeyboardInterrupt:
            print("\n操作中断")
        except Exception as e:
            print(f"错误: {e}")

# 简化版本：直接读取并保存，适合自动化脚本
async def quick_read_and_save():
    """快速读取并保存数据，适合自动化任务"""
    db = SensorDatabase(max_records=3)
    data = await read_sensor_data()
    
    if data:
        success = db.save_reading(data)
        if success:
            latest = db.get_latest_reading()
            if latest:
                print(f"最新数据: {latest['temperature']:.1f}°C, {latest['humidity']:.1f}%")
                return True
    return False

if __name__ == "__main__":
    # 快速模式：直接读取并保存，适合cron任务
    # result = asyncio.run(quick_read_and_save())
    # print(f"操作结果: {'成功' if result else '失败'}")
    
    # 交互式菜单模式
    main()