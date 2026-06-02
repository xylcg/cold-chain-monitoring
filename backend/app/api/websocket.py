"""
WebSocket API
实时数据推送与告警通知
"""
import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from loguru import logger

from ..services.websocket_manager import ws_manager
from ..services.redis_service import redis_service

router = APIRouter(prefix="/ws", tags=["WebSocket"])


@router.websocket("/device/{device_id}")
async def device_websocket(
    websocket: WebSocket,
    device_id: str,
    token: str = Query(None),
):
    """
    设备实时数据推送 WebSocket
    客户端订阅后可实时接收设备传感器数据和告警
    """
    # 验证用户
    if token:
        from ..core.security import decode_token
        user = decode_token(token)
        if not user:
            await websocket.close(code=4001, reason="无效的认证凭据")
            return
    else:
        await websocket.close(code=4001, reason="缺少认证凭据")
        return

    await ws_manager.connect(websocket)
    await ws_manager.subscribe_device(device_id, websocket)

    # 发送连接成功消息
    await websocket.send_text(json.dumps({
        "type": "connected",
        "device_id": device_id,
        "message": "已订阅设备实时数据",
    }, ensure_ascii=False))

    try:
        while True:
            # 保持连接，等待客户端消息（心跳）
            data = await websocket.receive_text()
            msg = json.loads(data)

            if msg.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
            elif msg.get("type") == "subscribe":
                target_device = msg.get("device_id", device_id)
                await ws_manager.subscribe_device(target_device, websocket)
                await websocket.send_text(json.dumps({
                    "type": "subscribed",
                    "device_id": target_device,
                }, ensure_ascii=False))

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket 错误: {e}")
        ws_manager.disconnect(websocket)


@router.websocket("/alerts")
async def alerts_websocket(
    websocket: WebSocket,
    token: str = Query(None),
    role: str = Query("driver"),
):
    """
    告警实时推送 WebSocket
    订阅后可接收对应角色的告警通知
    """
    if token:
        from ..core.security import decode_token
        user = decode_token(token)
        if not user:
            await websocket.close(code=4001, reason="无效的认证凭据")
            return
    else:
        await websocket.close(code=4001, reason="缺少认证凭据")
        return

    await ws_manager.connect(websocket)
    await ws_manager.subscribe_alerts(role, websocket)

    await websocket.send_text(json.dumps({
        "type": "connected",
        "role": role,
        "message": f"已订阅 {role} 角色告警通知",
    }, ensure_ascii=False))

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)

            if msg.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"告警 WebSocket 错误: {e}")
        ws_manager.disconnect(websocket)


@router.websocket("/dashboard")
async def dashboard_websocket(
    websocket: WebSocket,
    token: str = Query(None),
):
    """
    管理后台大屏 WebSocket
    全局态势图实时数据推送
    """
    if token:
        from ..core.security import decode_token
        user = decode_token(token)
        if not user:
            await websocket.close(code=4001, reason="无效的认证凭据")
            return

    await ws_manager.connect(websocket)

    await websocket.send_text(json.dumps({
        "type": "connected",
        "message": "已连接管理后台实时数据",
    }, ensure_ascii=False))

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)

            if msg.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"大屏 WebSocket 错误: {e}")
        ws_manager.disconnect(websocket)
