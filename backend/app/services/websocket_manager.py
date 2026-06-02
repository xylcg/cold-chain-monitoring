"""
WebSocket 连接管理器
管理所有客户端 WebSocket 连接，支持设备实时数据推送
"""
import json
import asyncio
from typing import Optional
from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        # 设备频道: device_id -> [websocket, ...]
        self.device_connections: dict[str, list[WebSocket]] = {}
        # 告警频道: user_role -> [websocket, ...]
        self.alert_connections: dict[str, list[WebSocket]] = {
            "driver": [],
            "manager": [],
            "repair": [],
            "customer": [],
        }
        # 所有连接
        self.all_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """接受 WebSocket 连接"""
        await websocket.accept()
        self.all_connections.append(websocket)
        logger.info(f"WebSocket 连接: {websocket.client}")

    def disconnect(self, websocket: WebSocket):
        """断开 WebSocket 连接"""
        if websocket in self.all_connections:
            self.all_connections.remove(websocket)

        for conns in self.device_connections.values():
            if websocket in conns:
                conns.remove(websocket)

        for conns in self.alert_connections.values():
            if websocket in conns:
                conns.remove(websocket)

        logger.info(f"WebSocket 断开: {websocket.client}")

    async def subscribe_device(self, device_id: str, websocket: WebSocket):
        """订阅设备数据"""
        if device_id not in self.device_connections:
            self.device_connections[device_id] = []
        self.device_connections[device_id].append(websocket)

    async def subscribe_alerts(self, role: str, websocket: WebSocket):
        """订阅告警频道"""
        if role in self.alert_connections:
            self.alert_connections[role].append(websocket)

    async def broadcast_device_data(self, device_id: str, data: dict):
        """向订阅该设备的所有客户端推送数据"""
        if device_id not in self.device_connections:
            return

        message = json.dumps({
            "type": "device_data",
            "device_id": device_id,
            "data": data,
        }, ensure_ascii=False)

        dead = []
        for ws in self.device_connections[device_id]:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)

        for ws in dead:
            self.disconnect(ws)

    async def broadcast_alert(self, alert: dict):
        """向订阅告警的用户推送"""
        targets = alert.get("targets", [])
        message = json.dumps({
            "type": "alert",
            "alert": alert,
        }, ensure_ascii=False)

        for target in targets:
            if target in self.alert_connections:
                dead = []
                for ws in self.alert_connections[target]:
                    try:
                        await ws.send_text(message)
                    except Exception:
                        dead.append(ws)
                for ws in dead:
                    self.disconnect(ws)

    @property
    def active_connections(self) -> int:
        return len(self.all_connections)


# 全局单例
ws_manager = ConnectionManager()
