"""
冷链传感器数据模拟器
模拟 100 辆冷藏车 + 10 个冷库的传感器数据，支持正常数据和多种异常注入
"""

import json
import time
import random
import uuid
import math
import threading
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass, field

import requests


@dataclass
class VehicleConfig:
    """车辆配置"""
    device_id: str
    plate_number: str
    cargo_type: str
    target_temp: float  # 目标温度
    temp_range: tuple  # (min, max) 正常范围
    humidity_range: tuple
    route: list  # GPS 路线坐标列表


@dataclass
class ColdRoomConfig:
    """冷库配置"""
    device_id: str
    room_name: str
    target_temp: float
    temp_range: tuple
    humidity_range: tuple
    location: tuple  # 固定 GPS 坐标


class SensorSimulator:
    """传感器数据模拟器"""

    # 常见货物品类及温控要求
    CARGO_TYPES = {
        "冷冻肉类": {"target": -18, "range": (-22, -15), "humidity": (75, 90)},
        "冷冻海鲜": {"target": -22, "range": (-25, -18), "humidity": (80, 95)},
        "冷藏乳制品": {"target": 4, "range": (2, 6), "humidity": (80, 95)},
        "冷藏水果": {"target": 5, "range": (3, 8), "humidity": (85, 95)},
        "冷藏蔬菜": {"target": 4, "range": (2, 7), "humidity": (90, 98)},
        "疫苗": {"target": 4, "range": (2, 8), "humidity": (40, 60)},
        "生物试剂": {"target": -20, "range": (-25, -15), "humidity": (30, 50)},
        "恒温药品": {"target": 20, "range": (15, 25), "humidity": (45, 65)},
        "鲜花": {"target": 5, "range": (3, 8), "humidity": (90, 98)},
        "巧克力": {"target": 18, "range": (15, 20), "humidity": (40, 60)},
    }

    # 异常类型
    ANOMALY_TYPES = [
        "gradual_drift",      # 渐变漂移
        "sudden_spike",       # 突跳
        "periodic_oscillation",  # 周期性波动
        "sensor_stuck",       # 传感器卡死
        "refrigeration_failure",  # 制冷故障
        "door_stuck_open",    # 车门未关
    ]

    def __init__(
        self,
        num_vehicles: int = 100,
        num_cold_rooms: int = 10,
        api_url: str = "http://localhost:8000/api/v1/sensors/data",
        interval: float = 10.0,
        anomaly_probability: float = 0.02,
    ):
        self.num_vehicles = num_vehicles
        self.num_cold_rooms = num_cold_rooms
        self.api_url = api_url
        self.interval = interval
        self.anomaly_probability = anomaly_probability
        self.running = False

        # 异常状态追踪（必须在 _init_devices 之前初始化）
        self.active_anomalies: dict = {}  # device_id -> anomaly_info
        self.sensor_states: dict = {}     # device_id -> last_values

        # 初始化设备配置
        self.vehicles: list[VehicleConfig] = []
        self.cold_rooms: list[ColdRoomConfig] = []
        self._init_devices()

    def _init_devices(self):
        """初始化所有设备配置"""
        # 初始化车辆
        cargo_names = list(self.CARGO_TYPES.keys())
        for i in range(self.num_vehicles):
            cargo = random.choice(cargo_names)
            config = self.CARGO_TYPES[cargo]
            device_id = f"VEH-{i+1:04d}"

            # 生成模拟路线（北京周边经纬度范围）
            route = self._generate_vehicle_route()

            self.vehicles.append(VehicleConfig(
                device_id=device_id,
                plate_number=f"京A{random.randint(10000, 99999)}",
                cargo_type=cargo,
                target_temp=config["target"],
                temp_range=config["range"],
                humidity_range=config["humidity"],
                route=route,
            ))
            self.sensor_states[device_id] = {
                "temperature": config["target"],
                "humidity": sum(config["humidity"]) / 2,
                "route_index": 0,
            }

        # 初始化冷库
        cold_room_cargos = ["冷藏水果", "冷藏蔬菜", "冷冻肉类", "疫苗"]
        for i in range(self.num_cold_rooms):
            cargo = cold_room_cargos[i % len(cold_room_cargos)]
            config = self.CARGO_TYPES[cargo]
            device_id = f"COLD-{i+1:04d}"

            self.cold_rooms.append(ColdRoomConfig(
                device_id=device_id,
                room_name=f"冷库{i+1}号",
                target_temp=config["target"],
                temp_range=config["range"],
                humidity_range=config["humidity"],
                location=(39.9 + random.uniform(-0.1, 0.1), 116.4 + random.uniform(-0.1, 0.1)),
            ))
            self.sensor_states[device_id] = {
                "temperature": config["target"],
                "humidity": sum(config["humidity"]) / 2,
            }

        print(f"[模拟器] 初始化完成: {len(self.vehicles)} 辆车 + {len(self.cold_rooms)} 个冷库")

    def _generate_vehicle_route(self) -> list:
        """生成模拟车辆路线"""
        base_lat, base_lng = 39.9, 116.4  # 北京中心
        route = []
        num_points = random.randint(20, 50)
        current_lat, current_lng = base_lat + random.uniform(-0.15, 0.15), base_lng + random.uniform(-0.15, 0.15)

        for _ in range(num_points):
            current_lat += random.uniform(-0.005, 0.005)
            current_lng += random.uniform(-0.005, 0.005)
            route.append((round(current_lat, 6), round(current_lng, 6)))

        return route

    def _generate_temperature(self, device_id: str, target: float, temp_range: tuple,
                              is_anomaly: bool) -> float:
        """生成温度数据，支持正常波动和异常"""
        state = self.sensor_states[device_id]

        if is_anomaly and device_id not in self.active_anomalies:
            anomaly_type = random.choice(self.ANOMALY_TYPES)
            self.active_anomalies[device_id] = {
                "type": anomaly_type,
                "start_time": time.time(),
                "duration": random.randint(30, 120),
                "base_temp": state.get("temperature", target),
            }

        anomaly = self.active_anomalies.get(device_id)
        if anomaly:
            elapsed = time.time() - anomaly["start_time"]
            if elapsed > anomaly["duration"]:
                del self.active_anomalies[device_id]
                anomaly = None

        if anomaly:
            a_type = anomaly["type"]
            base = anomaly["base_temp"]

            if a_type == "gradual_drift":
                drift = (elapsed / anomaly["duration"]) * random.uniform(8, 15)
                temp = base + drift
            elif a_type == "sudden_spike":
                temp = base + random.uniform(10, 20) * (1 if random.random() > 0.3 else -1)
            elif a_type == "periodic_oscillation":
                temp = base + 8 * math.sin(elapsed * 0.5) + random.uniform(-1, 1)
            elif a_type == "sensor_stuck":
                temp = base  # 卡死在某个值
            elif a_type == "refrigeration_failure":
                temp = base + 0.15 * elapsed  # 缓慢升温
            elif a_type == "door_stuck_open":
                temp = base + random.uniform(5, 10)  # 门开温度升高
            else:
                temp = base + random.gauss(0, 0.5)
        else:
            # 正常波动
            temp = state.get("temperature", target) + random.gauss(0, 0.3)
            # 缓慢回归目标温度
            temp += (target - temp) * 0.1

        # 限制在合理范围
        temp = max(-40, min(50, temp))
        state["temperature"] = temp
        return round(temp, 2)

    def _generate_humidity(self, device_id: str, humidity_range: tuple, is_anomaly: bool) -> float:
        """生成湿度数据"""
        state = self.sensor_states[device_id]
        base = state.get("humidity", sum(humidity_range) / 2)
        noise = random.gauss(0, 1.5)

        if is_anomaly:
            noise += random.uniform(-10, 10)

        hum = base + noise
        hum = max(0, min(100, hum))
        hum += (sum(humidity_range) / 2 - hum) * 0.05
        state["humidity"] = hum
        return round(hum, 2)

    def _generate_vehicle_data(self, vehicle: VehicleConfig) -> dict:
        """生成单辆车传感器数据（对应数据字典表1全部字段）"""
        state = self.sensor_states[vehicle.device_id]
        is_anomaly = random.random() < self.anomaly_probability

        # GPS 位置
        route_idx = state.get("route_index", 0)
        lat, lng = vehicle.route[route_idx % len(vehicle.route)]
        state["route_index"] = (route_idx + 1) % len(vehicle.route)

        temperature = self._generate_temperature(
            vehicle.device_id, vehicle.target_temp, vehicle.temp_range, is_anomaly
        )
        humidity = self._generate_humidity(
            vehicle.device_id, vehicle.humidity_range, is_anomaly
        )

        # 车门状态
        anomaly = self.active_anomalies.get(vehicle.device_id)
        if anomaly and anomaly["type"] == "door_stuck_open":
            door_status = 1
        else:
            door_status = 1 if random.random() < 0.03 else 0

        # 振动
        vibration = abs(random.gauss(0, 0.3))
        if anomaly:
            vibration += random.uniform(0, 3)

        # 数据质量
        data_quality = 1.0
        if anomaly and anomaly["type"] in ("sensor_stuck", "sensor_fault"):
            data_quality = random.uniform(0.3, 0.7)

        # 冷机状态
        cold_car_status = 1
        if anomaly and anomaly["type"] == "refrigeration_failure":
            cold_car_status = 0

        # 外部环境温度（随经纬度和时间模拟）
        hour = datetime.now().hour
        base_external = 20 + 8 * math.sin((hour - 6) * math.pi / 12)  # 日周期
        external_temp = round(base_external + random.gauss(0, 1.5), 1)

        # 车辆行驶速度
        vehicle_speed = round(random.uniform(0, 80), 1)

        # 运单号（模拟格式）
        waybill_no = f"WB-{datetime.now().strftime('%Y%m%d')}-{vehicle.device_id[-4:]}"

        return {
            "device_id": vehicle.device_id,
            "device_type": "vehicle",
            "temperature": temperature,
            "target_temperature": vehicle.target_temp,
            "humidity": humidity,
            "latitude": lat,
            "longitude": lng,
            "vehicle_speed": vehicle_speed,
            "door_status": door_status,
            "vibration": round(vibration, 2),
            "data_quality": round(data_quality, 2),
            "battery_level": round(random.uniform(60, 100), 1),
            "signal_strength": random.randint(70, 100),
            "cold_car_status": cold_car_status,
            "external_temp": external_temp,
            "waybill_no": waybill_no,
        }

    def _generate_cold_room_data(self, room: ColdRoomConfig) -> dict:
        """生成单个冷库传感器数据（对应数据字典表1全部字段）"""
        is_anomaly = random.random() < (self.anomaly_probability * 0.5)

        temperature = self._generate_temperature(
            room.device_id, room.target_temp, room.temp_range, is_anomaly
        )
        humidity = self._generate_humidity(
            room.device_id, room.humidity_range, is_anomaly
        )

        # 冷库运单号
        waybill_no = f"WB-{datetime.now().strftime('%Y%m%d')}-{room.device_id[-4:]}"

        return {
            "device_id": room.device_id,
            "device_type": "cold_room",
            "temperature": temperature,
            "target_temperature": room.target_temp,
            "humidity": humidity,
            "latitude": room.location[0],
            "longitude": room.location[1],
            "vehicle_speed": None,
            "door_status": 1 if random.random() < 0.1 else 0,
            "vibration": round(abs(random.gauss(0, 0.1)), 2),
            "data_quality": 1.0,
            "battery_level": None,
            "signal_strength": 100,
            "cold_car_status": 1,
            "external_temp": round(room.target_temp + random.uniform(5, 15), 1),
            "waybill_no": waybill_no,
        }

    def _send_data(self, data: dict) -> bool:
        """发送数据到后端"""
        try:
            resp = requests.post(
                self.api_url,
                json=data,
                headers={"Authorization": f"Bearer device_{data['device_id']}"},
                timeout=5,
            )
            return resp.status_code == 200
        except requests.RequestException:
            return False

    def start(self):
        """启动模拟器"""
        self.running = True
        print(f"[模拟器] 启动 - 间隔: {self.interval}s, 异常概率: {self.anomaly_probability}")

        batch_count = 0
        while self.running:
            start_time = time.time()
            batch_data = []

            # 生成车辆数据
            for vehicle in self.vehicles:
                data = self._generate_vehicle_data(vehicle)
                batch_data.append(data)

            # 生成冷库数据
            for room in self.cold_rooms:
                data = self._generate_cold_room_data(room)
                batch_data.append(data)

            # 批量发送
            success_count = 0
            for data in batch_data:
                if self._send_data(data):
                    success_count += 1

            batch_count += 1
            active_anomaly_count = len(self.active_anomalies)

            print(f"[批次 {batch_count}] 发送: {success_count}/{len(batch_data)} 条, "
                  f"活跃异常: {active_anomaly_count}")

            # 等待下一轮
            elapsed = time.time() - start_time
            sleep_time = max(0, self.interval - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)

    def stop(self):
        """停止模拟器"""
        self.running = False
        print("[模拟器] 已停止")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="冷链传感器数据模拟器")
    parser.add_argument("--vehicles", type=int, default=100, help="车辆数量")
    parser.add_argument("--cold-rooms", type=int, default=10, help="冷库数量")
    parser.add_argument("--api-url", type=str,
                        default="http://localhost:8000/api/v1/sensors/data",
                        help="后端 API 地址")
    parser.add_argument("--interval", type=float, default=10.0,
                        help="采样间隔 (秒)")
    parser.add_argument("--anomaly-prob", type=float, default=0.02,
                        help="异常注入概率")

    args = parser.parse_args()

    simulator = SensorSimulator(
        num_vehicles=args.vehicles,
        num_cold_rooms=args.cold_rooms,
        api_url=args.api_url,
        interval=args.interval,
        anomaly_probability=args.anomaly_prob,
    )

    try:
        simulator.start()
    except KeyboardInterrupt:
        simulator.stop()


if __name__ == "__main__":
    main()
