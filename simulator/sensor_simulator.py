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

    # 全国主要城市坐标
    NATIONWIDE_CITIES = {
        "北京": (39.9042, 116.4074), "天津": (39.0842, 117.2009),
        "石家庄": (38.0428, 114.5149), "太原": (37.8706, 112.5489),
        "呼和浩特": (40.8424, 111.7490), "沈阳": (41.8057, 123.4315),
        "大连": (38.9140, 121.6147), "长春": (43.8171, 125.3235),
        "哈尔滨": (45.8038, 126.5350), "上海": (31.2304, 121.4737),
        "南京": (32.0603, 118.7969), "杭州": (30.2741, 120.1551),
        "合肥": (31.8206, 117.2272), "福州": (26.0745, 119.2965),
        "厦门": (24.4798, 118.0894), "南昌": (28.6820, 115.8579),
        "济南": (36.6512, 117.1201), "青岛": (36.0671, 120.3826),
        "郑州": (34.7466, 113.6253), "武汉": (30.5928, 114.3055),
        "长沙": (28.2282, 112.9388), "广州": (23.1291, 113.2644),
        "深圳": (22.5431, 114.0579), "南宁": (22.8167, 108.3669),
        "海口": (20.0442, 110.1999), "三亚": (18.2528, 109.5120),
        "成都": (30.5728, 104.0668), "重庆": (29.4316, 106.9123),
        "贵阳": (26.6470, 106.6302), "昆明": (25.0389, 102.7183),
        "拉萨": (29.6500, 91.1000), "西安": (34.3416, 108.9398),
        "兰州": (36.0611, 103.8343), "西宁": (36.6171, 101.7782),
        "银川": (38.4872, 106.2309), "乌鲁木齐": (43.8256, 87.6168),
    }

    # 车牌前缀
    PLATE_PREFIXES = {
        "北京": "京A", "天津": "津A", "上海": "沪A", "重庆": "渝A",
        "石家庄": "冀A", "太原": "晋A", "呼和浩特": "蒙A",
        "沈阳": "辽A", "大连": "辽B", "长春": "吉A", "哈尔滨": "黑A",
        "南京": "苏A", "杭州": "浙A", "合肥": "皖A", "福州": "闽A",
        "厦门": "闽D", "南昌": "赣A", "济南": "鲁A", "青岛": "鲁B",
        "郑州": "豫A", "武汉": "鄂A", "长沙": "湘A",
        "广州": "粤A", "深圳": "粤B", "南宁": "桂A", "海口": "琼A",
        "成都": "川A", "贵阳": "贵A", "昆明": "云A", "拉萨": "藏A",
        "西安": "陕A", "兰州": "甘A", "西宁": "青A", "银川": "宁A",
        "乌鲁木齐": "新A",
    }

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
        """初始化所有设备配置 - 车辆路线覆盖全国，冷库分布全国各地"""
        cargo_names = list(self.CARGO_TYPES.keys())
        city_names = list(self.NATIONWIDE_CITIES.keys())

        for i in range(self.num_vehicles):
            cargo = random.choice(cargo_names)
            config = self.CARGO_TYPES[cargo]
            device_id = f"VEH-{i+1:04d}"

            # 随机选择起止城市（跨区域运输）
            origin_city = random.choice(city_names)
            dest_city = random.choice([c for c in city_names if c != origin_city])
            mid_city = random.choice([c for c in city_names if c not in (origin_city, dest_city)])

            # 生成城市间路线
            route = self._generate_intercity_route(origin_city, mid_city, dest_city)
            plate_prefix = self.PLATE_PREFIXES.get(origin_city, "京A")

            self.vehicles.append(VehicleConfig(
                device_id=device_id,
                plate_number=f"{plate_prefix}{random.randint(10000, 99999)}",
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

        # 初始化冷库 — 分布在全国各地
        warehouse_cities = ["北京", "上海", "广州", "成都", "武汉", "西安", "沈阳", "深圳", "郑州", "重庆"]
        cold_room_cargos = ["冷藏水果", "冷藏蔬菜", "冷冻肉类", "疫苗"]
        for i in range(self.num_cold_rooms):
            city = warehouse_cities[i % len(warehouse_cities)]
            base_lat, base_lng = self.NATIONWIDE_CITIES[city]
            cargo = cold_room_cargos[i % len(cold_room_cargos)]
            config = self.CARGO_TYPES[cargo]
            device_id = f"COLD-{i+1:04d}"

            self.cold_rooms.append(ColdRoomConfig(
                device_id=device_id,
                room_name=f"{city}冷库{i+1}号",
                target_temp=config["target"],
                temp_range=config["range"],
                humidity_range=config["humidity"],
                location=(base_lat + random.uniform(-0.05, 0.05), base_lng + random.uniform(-0.05, 0.05)),
            ))
            self.sensor_states[device_id] = {
                "temperature": config["target"],
                "humidity": sum(config["humidity"]) / 2,
            }

        print(f"[模拟器] 初始化完成: {len(self.vehicles)} 辆车 + {len(self.cold_rooms)} 个冷库 (覆盖全国主要城市)")

    def _generate_intercity_route(self, origin: str, mid: str, dest: str) -> list:
        """生成跨城市模拟路线：起点 → 中转 → 终点，带 GPS 插值"""
        coords = self.NATIONWIDE_CITIES
        o_lat, o_lng = coords[origin]
        m_lat, m_lng = coords[mid]
        d_lat, d_lng = coords[dest]

        route = []
        # 第一段：起点 → 中转向城市
        seg1_points = random.randint(15, 30)
        for i in range(seg1_points):
            t = i / (seg1_points - 1) if seg1_points > 1 else 0
            lat = o_lat + (m_lat - o_lat) * t + random.uniform(-0.3, 0.3)
            lng = o_lng + (m_lng - o_lng) * t + random.uniform(-0.3, 0.3)
            route.append((round(lat, 6), round(lng, 6)))

        # 第二段：中转向城市 → 终点
        seg2_points = random.randint(15, 30)
        for i in range(1, seg2_points):  # start at 1 to avoid duplicate mid point
            t = i / (seg2_points - 1) if seg2_points > 1 else 0
            lat = m_lat + (d_lat - m_lat) * t + random.uniform(-0.3, 0.3)
            lng = m_lng + (d_lng - m_lng) * t + random.uniform(-0.3, 0.3)
            route.append((round(lat, 6), round(lng, 6)))

        return route

    def _generate_vehicle_route(self) -> list:
        """保留接口兼容性（已不使用）"""
        return self._generate_intercity_route("北京", "郑州", "武汉")

    def _generate_temperature(self, device_id: str, target: float, temp_range: tuple,
                              is_anomaly: bool) -> float:
        """生成温度数据，支持正常波动和异常。
        
        关键设计：异常参数在异常开始时一次性随机确定，整个异常期间保持不变，
        避免每次调用重新随机导致温度反复横跳。
        """
        state = self.sensor_states[device_id]
        target_min, target_max = temp_range

        # === 异常开始：一次性确定全部参数 ===
        if is_anomaly and device_id not in self.active_anomalies:
            anomaly_type = random.choice(self.ANOMALY_TYPES)
            hour = datetime.now().hour
            external_temp = 20 + 8 * math.sin((hour - 6) * math.pi / 12)
            base = state.get("temperature", target)

            anomaly_info = {
                "type": anomaly_type,
                "start_time": time.time(),
                "duration": random.randint(60, 300),
                "base_temp": base,
                "external_temp": external_temp,
            }

            # 为每种异常类型预生成固定参数
            if anomaly_type == "gradual_drift":
                anomaly_info["drift_amount"] = random.uniform(3, 6)        # 漂移终点偏移量
            elif anomaly_type == "sudden_spike":
                anomaly_info["spike_amount"] = random.uniform(3, 6)         # 突跳幅度
                anomaly_info["spike_direction"] = -1 if random.random() < 0.4 else 1  # 40%概率向下
            elif anomaly_type == "periodic_oscillation":
                anomaly_info["osc_amplitude"] = random.uniform(2, 4)        # 波动振幅
                anomaly_info["osc_frequency"] = random.uniform(0.2, 0.5)    # 波动频率
            elif anomaly_type == "door_stuck_open":
                temp_gap = external_temp - base
                anomaly_info["door_rise"] = min(abs(temp_gap) * 0.4, 8)     # 升温上限

            self.active_anomalies[device_id] = anomaly_info

        # === 检查异常是否结束 ===
        anomaly = self.active_anomalies.get(device_id)
        if anomaly:
            elapsed = time.time() - anomaly["start_time"]
            if elapsed > anomaly["duration"]:
                # 异常结束：记录结束时的温度，下一轮从该值向目标缓慢回归
                del self.active_anomalies[device_id]
                anomaly = None

        # === 生成温度 ===
        if anomaly:
            a_type = anomaly["type"]
            base = anomaly["base_temp"]

            if a_type == "gradual_drift":
                # 线性漂移，方向固定（升温），速率均匀
                progress = min(1.0, elapsed / anomaly["duration"])
                temp = base + anomaly["drift_amount"] * progress

            elif a_type == "sudden_spike":
                # 固定幅度的突跳（首次跳变后保持稳定）
                if "spike_applied" not in anomaly:
                    anomaly["spike_applied"] = True
                    anomaly["spike_value"] = base + anomaly["spike_amount"] * anomaly["spike_direction"]
                # 缓慢回归目标（模拟传感器/系统自我修正）
                recovery = (target - anomaly["spike_value"]) * min(1.0, elapsed / anomaly["duration"]) * 0.3
                temp = anomaly["spike_value"] + recovery

            elif a_type == "periodic_oscillation":
                # 固定振幅和频率的正弦波动
                osc = anomaly["osc_amplitude"] * math.sin(elapsed * anomaly["osc_frequency"])
                temp = base + osc

            elif a_type == "sensor_stuck":
                temp = base  # 卡死在异常发生时的值

            elif a_type == "refrigeration_failure":
                # 制冷故障：缓慢趋向环境温度
                ext = anomaly["external_temp"]
                progress = min(1.0, elapsed / anomaly["duration"])
                temp = base + (ext - base) * progress * 0.7

            elif a_type == "door_stuck_open":
                # 车门未关：温度缓慢升到固定值
                progress = min(1.0, elapsed / anomaly["duration"])
                temp = base + anomaly["door_rise"] * progress

            else:
                temp = base

            # 叠加微小噪声（±0.3°C），让曲线不单调
            temp += random.gauss(0, 0.3)

        else:
            # === 正常模式：压缩机制冷循环 ===
            current_temp = state.get("temperature", target)

            # 压缩机循环：周期约 3-5 分钟，不同车辆有不同相位
            phase = hash(device_id) % 628 / 100  # 转为弧度 0~2π
            compressor_cycle = 1.5 * math.sin(time.time() * 0.03 + phase)

            # 随机噪声 ±1.5°C (3σ)
            noise = random.gauss(0, 0.5)

            # 温度变化 = 压缩机影响 + 噪声 + 向目标回归
            temp = current_temp + compressor_cycle * 0.2 + noise
            temp += (target - temp) * 0.1

        # === 安全限幅 ===
        lower_bound = max(-40, target_min - 15)
        upper_bound = min(50, target_max + 20)
        temp = max(lower_bound, min(upper_bound, temp))
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

        # 外部环境温度（随纬度 + 时间模拟，中国南北温差显著）
        hour = datetime.now().hour
        # 日周期基础温度，纬度越低越热
        lat_factor = (35.0 - lat) * 0.6  # 北京纬度约40，广州约23，温差约10°C
        base_external = 20 + lat_factor + 8 * math.sin((hour - 6) * math.pi / 12)
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
            "external_temp": round(
                20 + (35.0 - room.location[0]) * 0.6 + 8 * math.sin((datetime.now().hour - 6) * math.pi / 12)
                + random.gauss(0, 1.5), 1
            ),
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
