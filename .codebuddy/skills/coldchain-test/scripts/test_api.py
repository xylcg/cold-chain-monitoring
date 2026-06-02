"""
冷链物流监控平台 - 后端 API 测试脚本
测试所有 6 个 API 模块的端点

用法:
    python test_api.py                    # 默认测试 localhost:8000
    python test_api.py --host 192.168.1.1 # 指定后端地址
    python test_api.py --port 8080        # 指定端口
"""

import httpx
import json
import sys
import argparse
from datetime import datetime, timedelta

class APITester:
    """后端 API 测试器"""

    def __init__(self, host="localhost", port=8000):
        self.base_url = f"http://{host}:{port}"
        self.api_url = f"{self.base_url}/api/v1"
        self.client = httpx.Client(timeout=10)
        self.token = None
        self.results = {"pass": 0, "fail": 0, "skip": 0, "details": []}

    def _record(self, module: str, endpoint: str, passed: bool, message: str = "", skip: bool = False):
        status = "SKIP" if skip else ("PASS" if passed else "FAIL")
        icon = "?" if skip else ("[OK]" if passed else "[FAIL]")
        detail = f"  {icon} [{module}] {endpoint} - {message}"
        print(detail)
        if skip:
            self.results["skip"] += 1
        elif passed:
            self.results["pass"] += 1
        else:
            self.results["fail"] += 1
        self.results["details"].append({"module": module, "endpoint": endpoint, "status": status, "message": message})

    def _get(self, path, auth=True, params=None):
        headers = {}
        if auth and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return self.client.get(f"{self.api_url}{path}", headers=headers, params=params)

    def _post(self, path, data=None, auth=True):
        headers = {}
        if auth and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return self.client.post(f"{self.api_url}{path}", json=data or {}, headers=headers)

    def _delete(self, path, auth=True):
        headers = {}
        if auth and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return self.client.delete(f"{self.api_url}{path}", headers=headers)

    # ─── 健康检查 ──────────────────────────────────────
    def test_health(self):
        """测试健康检查端点"""
        print("\n=== 健康检查 ===")
        try:
            r = self.client.get(f"{self.base_url}/")
            ok = r.status_code == 200
            self._record("Health", "GET /", ok, f"status={r.status_code}, app={r.json().get('app', 'N/A')}")
        except Exception as e:
            self._record("Health", "GET /", False, str(e))

        try:
            r = self.client.get(f"{self.base_url}/health")
            ok = r.status_code == 200
            self._record("Health", "GET /health", ok, f"status={r.status_code}")
        except Exception as e:
            self._record("Health", "GET /health", False, str(e))

    # ─── 认证模块 ──────────────────────────────────────
    def test_auth(self):
        """测试认证 API"""
        print("\n=== 认证模块 (Auth) ===")

        # 1. 正确登录
        try:
            r = self._post("/auth/login", {"username": "admin", "password": "123456"}, auth=False)
            if r.status_code == 200:
                data = r.json()
                self.token = data.get("access_token")
                ok = bool(self.token) and data.get("username") == "admin"
                self._record("Auth", "POST /auth/login", ok, f"admin 登录成功, role={data.get('user_role')}")
            else:
                self._record("Auth", "POST /auth/login", False, f"status={r.status_code}, {r.json()}")
        except Exception as e:
            self._record("Auth", "POST /auth/login", False, str(e))

        # 2. 错误密码登录
        try:
            r = self._post("/auth/login", {"username": "admin", "password": "wrong"}, auth=False)
            ok = r.status_code == 401
            self._record("Auth", "POST /auth/login (wrong pw)", ok, f"正确拒绝错误密码, status={r.status_code}")
        except Exception as e:
            self._record("Auth", "POST /auth/login (wrong pw)", False, str(e))

        # 3. 获取当前用户信息
        try:
            r = self._get("/auth/me")
            if r.status_code == 200:
                data = r.json()
                ok = data.get("username") == "admin"
                self._record("Auth", "GET /auth/me", ok, f"当前用户: {data.get('username')}")
            else:
                self._record("Auth", "GET /auth/me", False, f"status={r.status_code}")
        except Exception as e:
            self._record("Auth", "GET /auth/me", False, str(e))

    # ─── 仪表盘模块 ────────────────────────────────────
    def test_dashboard(self):
        """测试仪表盘 API"""
        print("\n=== 仪表盘模块 (Dashboard) ===")

        if not self.token:
            self._record("Dashboard", "ALL", False, "无 token，跳过", skip=True)
            return

        # 1. KPI 数据
        try:
            r = self._get("/dashboard/kpi")
            if r.status_code == 200:
                data = r.json()
                ok = isinstance(data, dict)
                self._record("Dashboard", "GET /dashboard/kpi", ok, f"keys={list(data.keys()) if ok else 'N/A'}")
            else:
                self._record("Dashboard", "GET /dashboard/kpi", False, f"status={r.status_code}")
        except Exception as e:
            self._record("Dashboard", "GET /dashboard/kpi", False, str(e))

        # 2. 设备列表
        try:
            r = self._get("/dashboard/devices")
            if r.status_code == 200:
                data = r.json()
                ok = isinstance(data, (list, dict))
                count = len(data) if isinstance(data, list) else len(data.get("items", data))
                self._record("Dashboard", "GET /dashboard/devices", ok, f"设备数: {count}")
            else:
                self._record("Dashboard", "GET /dashboard/devices", False, f"status={r.status_code}")
        except Exception as e:
            self._record("Dashboard", "GET /dashboard/devices", False, str(e))

        # 3. 全局态势
        try:
            r = self._get("/dashboard/overview")
            ok = r.status_code in (200, 404)  # 404 可接受（无数据）
            self._record("Dashboard", "GET /dashboard/overview", ok, f"status={r.status_code}")
        except Exception as e:
            self._record("Dashboard", "GET /dashboard/overview", False, str(e))

        # 4. 告警摘要
        try:
            r = self._get("/dashboard/alerts/summary")
            ok = r.status_code in (200, 404)
            self._record("Dashboard", "GET /dashboard/alerts/summary", ok, f"status={r.status_code}")
        except Exception as e:
            self._record("Dashboard", "GET /dashboard/alerts/summary", False, str(e))

    # ─── 传感器模块 ────────────────────────────────────
    def test_sensors(self):
        """测试传感器数据 API"""
        print("\n=== 传感器模块 (Sensors) ===")

        if not self.token:
            self._record("Sensors", "ALL", False, "无 token，跳过", skip=True)
            return

        test_device = "DEV-TRUCK-001"

        # 1. 上报单条传感器数据
        try:
            sensor_data = {
                "device_id": test_device,
                "temperature": -18.5,
                "humidity": 65.0,
                "door_status": "CLOSED",
                "gps_lat": 31.23,
                "gps_lng": 121.47,
                "battery": 85.0,
                "signal_strength": 90,
                "timestamp": datetime.now().isoformat()
            }
            r = self._post("/sensors/data", sensor_data)
            ok = r.status_code in (200, 201, 202)
            self._record("Sensors", "POST /sensors/data", ok, f"上报数据, status={r.status_code}")
        except Exception as e:
            self._record("Sensors", "POST /sensors/data", False, str(e))

        # 2. 批量上报
        try:
            batch_data = [
                {
                    "device_id": test_device,
                    "temperature": -18.0 + i * 0.5,
                    "humidity": 65.0,
                    "door_status": "CLOSED",
                    "gps_lat": 31.23,
                    "gps_lng": 121.47,
                    "battery": 84.0 - i,
                    "signal_strength": 90,
                    "timestamp": (datetime.now() - timedelta(minutes=i*5)).isoformat()
                }
                for i in range(5)
            ]
            r = self._post("/sensors/data/batch", batch_data)
            ok = r.status_code in (200, 201, 202)
            self._record("Sensors", "POST /sensors/data/batch", ok, f"批量上报5条, status={r.status_code}")
        except Exception as e:
            self._record("Sensors", "POST /sensors/data/batch", False, str(e))

        # 3. 获取最新数据
        try:
            r = self._get(f"/sensors/latest/{test_device}")
            ok = r.status_code in (200, 404)
            self._record("Sensors", f"GET /sensors/latest/{test_device}", ok, f"status={r.status_code}")
        except Exception as e:
            self._record("Sensors", f"GET /sensors/latest/{test_device}", False, str(e))

        # 4. 获取历史数据
        try:
            end = datetime.now().isoformat()
            start = (datetime.now() - timedelta(hours=1)).isoformat()
            r = self._get(f"/sensors/history/{test_device}", params={"start": start, "end": end, "limit": 10})
            ok = r.status_code in (200, 404)
            self._record("Sensors", f"GET /sensors/history/{test_device}", ok, f"status={r.status_code}")
        except Exception as e:
            self._record("Sensors", f"GET /sensors/history/{test_device}", False, str(e))

    # ─── 温度模块 ──────────────────────────────────────
    def test_temperature(self):
        """测试温度监控 API"""
        print("\n=== 温度模块 (Temperature) ===")

        if not self.token:
            self._record("Temperature", "ALL", False, "无 token，跳过", skip=True)
            return

        test_device = "DEV-TRUCK-001"

        # 1. 当前温度
        try:
            r = self._get(f"/temperature/current/{test_device}")
            ok = r.status_code in (200, 404)
            self._record("Temperature", f"GET /temperature/current/{test_device}", ok, f"status={r.status_code}")
        except Exception as e:
            self._record("Temperature", f"GET /temperature/current/{test_device}", False, str(e))

        # 2. 趋势预测
        try:
            r = self._get(f"/temperature/trend/{test_device}", params={"horizon": 30})
            ok = r.status_code in (200, 404)
            self._record("Temperature", f"GET /temperature/trend/{test_device}", ok, f"status={r.status_code}")
        except Exception as e:
            self._record("Temperature", f"GET /temperature/trend/{test_device}", False, str(e))

        # 3. 历史温度
        try:
            r = self._get(f"/temperature/history/{test_device}", params={"minutes": 60})
            ok = r.status_code in (200, 404)
            self._record("Temperature", f"GET /temperature/history/{test_device}", ok, f"status={r.status_code}")
        except Exception as e:
            self._record("Temperature", f"GET /temperature/history/{test_device}", False, str(e))

        # 4. 异常检测
        try:
            r = self._get(f"/temperature/anomaly/{test_device}")
            ok = r.status_code in (200, 404)
            self._record("Temperature", f"GET /temperature/anomaly/{test_device}", ok, f"status={r.status_code}")
        except Exception as e:
            self._record("Temperature", f"GET /temperature/anomaly/{test_device}", False, str(e))

    # ─── 告警模块 ──────────────────────────────────────
    def test_alerts(self):
        """测试告警 API"""
        print("\n=== 告警模块 (Alerts) ===")

        if not self.token:
            self._record("Alerts", "ALL", False, "无 token，跳过", skip=True)
            return

        # 1. 告警列表
        try:
            r = self._get("/alerts")
            ok = r.status_code in (200, 404)
            self._record("Alerts", "GET /alerts", ok, f"status={r.status_code}")
        except Exception as e:
            self._record("Alerts", "GET /alerts", False, str(e))

        # 2. 活跃告警
        try:
            r = self._get("/alerts/active")
            ok = r.status_code in (200, 404)
            self._record("Alerts", "GET /alerts/active", ok, f"status={r.status_code}")
        except Exception as e:
            self._record("Alerts", "GET /alerts/active", False, str(e))

        # 3. 告警规则
        try:
            r = self._get("/alerts/rules")
            ok = r.status_code in (200, 404)
            self._record("Alerts", "GET /alerts/rules", ok, f"status={r.status_code}")
        except Exception as e:
            self._record("Alerts", "GET /alerts/rules", False, str(e))

        # 4. 创建规则
        try:
            rule = {
                "rule_type": "test_temp_high",
                "description": "测试规则-温度过高",
                "severity": "warning",
                "condition": {"metric": "temperature", "operator": "gt", "threshold": 0},
                "cooldown_minutes": 5,
                "enabled": True
            }
            r = self._post("/alerts/rules", rule)
            ok = r.status_code in (200, 201, 409)
            self._record("Alerts", "POST /alerts/rules", ok, f"status={r.status_code}")
        except Exception as e:
            self._record("Alerts", "POST /alerts/rules", False, str(e))

        # 5. 删除测试规则
        try:
            r = self._delete("/alerts/rules/test_temp_high")
            ok = r.status_code in (200, 204, 404)
            self._record("Alerts", "DELETE /alerts/rules/test_temp_high", ok, f"status={r.status_code}")
        except Exception as e:
            self._record("Alerts", "DELETE /alerts/rules/test_temp_high", False, str(e))

    # ─── 权限验证 ──────────────────────────────────────
    def test_auth_required(self):
        """验证需要认证的端点是否正确拒绝无 token 请求"""
        print("\n=== 权限验证 (Auth Required) ===")

        saved_token = self.token
        self.token = None

        endpoints = [
            ("GET", "/dashboard/kpi"),
            ("GET", "/dashboard/devices"),
            ("GET", "/alerts"),
            ("GET", "/alerts/active"),
            ("GET", "/alerts/rules"),
        ]

        for method, path in endpoints:
            try:
                if method == "GET":
                    r = self._get(path, auth=False)
                ok = r.status_code == 401
                self._record("AuthCheck", f"{method} {path}", ok, f"正确返回 401" if ok else f"返回 {r.status_code}，预期 401")
            except Exception as e:
                self._record("AuthCheck", f"{method} {path}", False, str(e))

        self.token = saved_token

    # ─── 汇总报告 ──────────────────────────────────────
    def report(self):
        """输出测试报告"""
        print("\n" + "=" * 60)
        print("  测试报告")
        print("=" * 60)
        total = self.results["pass"] + self.results["fail"] + self.results["skip"]
        print(f"  总计: {total} 个测试")
        print(f"  通过: {self.results['pass']} 个  [OK]")
        print(f"  失败: {self.results['fail']} 个  [FAIL]")
        print(f"  跳过: {self.results['skip']} 个  (--))")
        print("=" * 60)

        # 按模块统计
        modules = {}
        for d in self.results["details"]:
            m = d["module"]
            if m not in modules:
                modules[m] = {"pass": 0, "fail": 0, "skip": 0}
            if d["status"] == "PASS":
                modules[m]["pass"] += 1
            elif d["status"] == "FAIL":
                modules[m]["fail"] += 1
            else:
                modules[m]["skip"] += 1

        print("\n  按模块统计:")
        for m, stats in modules.items():
            total_m = stats["pass"] + stats["fail"] + stats["skip"]
            bar = "[OK]" * stats["pass"] + "[FAIL]" * stats["fail"] + "--" * stats["skip"]
            print(f"    {m:<20}: {bar} ({stats['pass']}/{total_m} 通过)")

        return self.results["fail"] == 0

    def run_all(self):
        """运行所有测试"""
        print("=" * 60)
        print(f"  冷链物流监控平台 API 测试")
        print(f"  目标: {self.base_url}")
        print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        self.test_health()
        self.test_auth()
        self.test_dashboard()
        self.test_sensors()
        self.test_temperature()
        self.test_alerts()
        self.test_auth_required()

        return self.report()


def main():
    parser = argparse.ArgumentParser(description="冷链物流监控平台 API 测试")
    parser.add_argument("--host", default="localhost", help="后端主机地址 (默认: localhost)")
    parser.add_argument("--port", type=int, default=8000, help="后端端口 (默认: 8000)")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式报告")
    args = parser.parse_args()

    tester = APITester(host=args.host, port=args.port)
    success = tester.run_all()

    if args.json:
        print(json.dumps(tester.results, ensure_ascii=False, indent=2))

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
