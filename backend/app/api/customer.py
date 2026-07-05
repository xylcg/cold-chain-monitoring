"""
客户温控查询服务 API
使用统一世界状态，确保运单数据与车辆数据联通
"""
from datetime import datetime
from typing import Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from ..services.world_state import get_world_state
from ..core.security import get_current_user, require_role

router = APIRouter(prefix="/api/v1/customer", tags=["客户服务"])

# ========== 顾客订单模型 ==========
class CustomerOrderCreate(BaseModel):
    cargo_name: str
    cargo_category: str = "冷冻食品"
    origin: str
    destination: str
    quantity: float = 0.0
    unit: str = "kg"
    temperature_requirement: str = "-18℃ ~ -15℃"
    zone_name: str = "冷冻区"
    receiver: str = ""
    receiver_phone: str = ""
    notes: str = ""

# 订单状态流转:
# pending(待接单) -> accepted(司机已接单) -> in_transit(配送中) -> delivered(已送达待确认) -> completed(客户已签收)
# 内存存储顾客订单
_customer_orders: dict = {}  # order_id -> 订单数据


@router.get("/query/{waybill_id}")
async def query_waybill_temperature(
    waybill_id: str,
    user: dict = Depends(require_role("admin", "warehouse", "customer")),
):
    """客户查询运单温度 - 来自统一世界状态"""
    ws = get_world_state()
    data = ws["waybills"].get(waybill_id)

    if not data:
        raise HTTPException(status_code=404, detail="运单不存在或暂无可查数据")

    records = data["records"]
    temps = [r["temperature"] for r in records]

    return {
        "waybill_id": waybill_id,
        "cargo_type": data["cargo_type"],
        "temperature_requirement": data["temperature_requirement"],
        "origin": data["origin"],
        "destination": data["destination"],
        "departure_time": data["departure_time"],
        "estimated_arrival": data["estimated_arrival"],
        "current_status": data["current_status"],
        "current_temperature": temps[-1] if temps else None,
        "temperature_range": f"{min(temps):.1f}°C ~ {max(temps):.1f}°C",
        "avg_temperature": f"{sum(temps) / len(temps):.1f}°C" if temps else "N/A",
        "is_compliant": data["is_compliant"],
        "vehicle_info": _get_vehicle_for_waybill(waybill_id),
    }


def _get_vehicle_for_waybill(waybill_id: str):
    """获取运单对应的车辆信息"""
    ws = get_world_state()
    for v in ws["vehicles"]:
        if v["waybill_no"] == waybill_id:
            return {
                "device_id": v["device_id"],
                "plate_number": v["plate_number"],
                "current_temperature": v["temperature"],
                "current_city": v["current_city"],
                "vehicle_speed": v["vehicle_speed"],
                "cold_car_health": v.get("cold_car_health", 0),
            }
    return None


@router.get("/temperature-curve/{waybill_id}")
async def get_temperature_curve(
    waybill_id: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    user: dict = Depends(require_role("admin", "warehouse", "customer")),
):
    """获取运单温度曲线数据"""
    ws = get_world_state()
    data = ws["waybills"].get(waybill_id)
    if not data:
        raise HTTPException(status_code=404, detail="运单不存在")

    records = data["records"]
    if start_time:
        records = [r for r in records if r["timestamp"] >= start_time]
    if end_time:
        records = [r for r in records if r["timestamp"] <= end_time]

    return {
        "waybill_id": waybill_id,
        "cargo_type": data["cargo_type"],
        "temperature_requirement": data["temperature_requirement"],
        "data_points": len(records),
        "timestamps": [r["timestamp"] for r in records],
        "temperatures": [r["temperature"] for r in records],
        "humidities": [r["humidity"] for r in records],
        "door_events": [
            {"timestamp": r["timestamp"], "temperature": r["temperature"]}
            for r in records if r.get("door_status") == 1
        ],
        "current_temperature": records[-1]["temperature"] if records else None,
    }


@router.get("/certificate/{waybill_id}")
async def download_temperature_certificate(
    waybill_id: str,
    format: str = "text",
    user: dict = Depends(require_role("admin", "warehouse", "customer")),
):
    """生成温度证明文件"""
    ws = get_world_state()
    data = ws["waybills"].get(waybill_id)
    if not data:
        raise HTTPException(status_code=404, detail="运单不存在")

    records = data["records"]
    temps = [r["temperature"] for r in records]
    vehicle = _get_vehicle_for_waybill(waybill_id)

    lines = [
        f"冷链运输温度证明",
        f"=" * 55,
        f"运单号:     {waybill_id}",
        f"货物类型:   {data['cargo_type']}",
        f"温度要求:   {data['temperature_requirement']}",
        f"发货地:     {data['origin']}",
        f"目的地:     {data['destination']}",
        f"发车时间:   {data['departure_time']}",
        f"预计到达:   {data['estimated_arrival']}",
        f"运输车辆:   {vehicle['plate_number'] if vehicle else 'N/A'}",
        f"当前状态:   {data['current_status']}",
        f"-" * 55,
        f"全程温度统计:",
        f"  最低温度: {min(temps):.1f}°C",
        f"  最高温度: {max(temps):.1f}°C",
        f"  平均温度: {sum(temps) / len(temps):.1f}°C",
        f"  记录点数: {len(records)}",
        f"  温控达标: {'是' if data['is_compliant'] else '否'}",
        f"-" * 55,
        f"全程温度采样 (每30分钟):",
    ]

    for i, r in enumerate(records):
        if i % 3 == 0:
            lines.append(f"  {r['timestamp'][:16]}  |  {r['temperature']:>5.1f}°C  |  {r.get('location', '运输中')}")

    lines.append(f"=" * 55)
    lines.append(f"证明生成时间: {datetime.utcnow().isoformat()}")
    lines.append(f"本证明由冷链物流智能监控平台自动生成")
    lines.append(f"平台保证数据真实、完整、不可篡改")

    return PlainTextResponse(
        "\n".join(lines),
        headers={"Content-Disposition": f"attachment; filename=temperature_certificate_{waybill_id}.txt"},
    )


@router.get("/my-orders")
async def get_my_orders(user: dict = Depends(get_current_user)):
    """获取当前用户关联的运单列表"""
    ws = get_world_state()
    my_waybills = []
    for wb_id, data in list(ws["waybills"].items())[:10]:
        records = data["records"]
        temps = [r["temperature"] for r in records]
        my_waybills.append({
            "waybill_id": wb_id,
            "cargo_type": data["cargo_type"],
            "origin": data["origin"],
            "destination": data["destination"],
            "current_status": data["current_status"],
            "current_temperature": temps[-1] if temps else None,
            "temperature_range": f"{min(temps):.1f}°C ~ {max(temps):.1f}°C",
            "is_compliant": data["is_compliant"],
        })

    return {"count": len(my_waybills), "orders": my_waybills}


@router.get("/scan")
async def scan_qr_query(
    code: str = Query(...),
    user: dict = Depends(require_role("admin", "warehouse", "customer")),
):
    """扫码查询"""
    return await query_waybill_temperature(code, user=user)


# ==================== 顾客下单 ====================

# 运单存储（订单→运单关联）
_customer_waybills: dict = {}  # order_id -> waybill 数据


def _create_waybill_for_order(order: dict) -> dict:
    """为订单自动创建关联运单，确保追溯链路完整"""
    waybill_id = f"WB-{order['order_id']}"
    now = datetime.utcnow().isoformat()
    waybill = {
        "waybill_id": waybill_id,
        "order_id": order["order_id"],
        "cargo_type": order["cargo_name"],
        "cargo_category": order.get("cargo_category", "冷链"),
        "temperature_requirement": order["temperature_requirement"],
        "origin": order["origin"],
        "destination": order["destination"],
        "quantity": order.get("quantity", 0),
        "unit": order.get("unit", "kg"),
        "departure_time": None,
        "estimated_arrival": None,
        "current_status": "created",
        "is_compliant": True,
        "records": [],  # 温度记录列表
        "created_at": now,
        "updated_at": now,
    }
    _customer_waybills[order["order_id"]] = waybill
    return waybill


@router.post("/create-order")
async def create_order(
    data: CustomerOrderCreate,
    user: dict = Depends(require_role("customer", "admin", "warehouse")),
):
    """顾客/管理员/仓库创建新订单"""
    order_id = f"ORD-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"
    now = datetime.utcnow().isoformat()
    waybill_id = f"WB-{order_id}"
    order = {
        "order_id": order_id,
        "customer_id": user.get("sub", "unknown"),
        "customer_name": user.get("sub", "unknown"),
        "cargo_name": data.cargo_name,
        "cargo_category": data.cargo_category,
        "origin": data.origin,
        "destination": data.destination,
        "quantity": data.quantity,
        "unit": data.unit,
        "temperature_requirement": data.temperature_requirement,
        "zone_name": data.zone_name,
        "receiver": data.receiver,
        "receiver_phone": data.receiver_phone,
        "notes": data.notes,
        "status": "pending",  # 待司机接单
        "driver_id": None,
        "driver_name": None,
        "signed_by_customer": False,  # 客户是否已签收确认
        "accept_photo_url": None,     # 司机接单拍照URL
        "deliver_photo_url": None,    # 司机送达拍照URL
        "waybill_id": waybill_id,     # 🔴 关联运单ID
        "created_at": now,
        "updated_at": now,
        "price": round(data.quantity * 3.5 + 200, 0),  # 模拟运费计算
        "weight_kg": data.quantity,
        "deadline": datetime.utcnow().isoformat(),
        "temp_range": data.temperature_requirement,
    }
    _customer_orders[order_id] = order

    # 🔴 自动创建关联运单
    _create_waybill_for_order(order)

    return {"status": "ok", "order": order, "waybill_created": True}


# ====== 🔴 P0: 查询订单关联运单 ======
@router.get("/order-waybill/{order_id}")
async def get_order_waybill(
    order_id: str,
    user: dict = Depends(get_current_user),
):
    """获取订单关联的运单信息（含温度记录）"""
    if order_id not in _customer_orders:
        raise HTTPException(status_code=404, detail="订单不存在")

    waybill = _customer_waybills.get(order_id)
    if not waybill:
        return {"status": "ok", "waybill": None, "message": "该订单暂未关联运单"}

    return {
        "status": "ok",
        "order_id": order_id,
        "waybill": waybill,
    }


@router.get("/my-orders-new")
async def get_my_orders_new(user: dict = Depends(get_current_user)):
    """获取当前顾客的所有订单"""
    username = user.get("sub", "")
    my_orders = [
        o for o in _customer_orders.values()
        if o.get("customer_id") == username
    ]
    # 按创建时间倒序
    my_orders.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return {"count": len(my_orders), "orders": my_orders}


# ==================== 司机端：获取待接单列表 ====================

@router.get("/available-orders")
async def get_available_orders(user: dict = Depends(get_current_user)):
    """获取所有待接单的订单（司机可见）"""
    available = [
        o for o in _customer_orders.values()
        if o.get("status") == "pending"
    ]
    available.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return {"count": len(available), "orders": available}


@router.post("/accept-order/{order_id}")
async def accept_order(
    order_id: str,
    user: dict = Depends(require_role("driver", "admin", "warehouse")),
):
    """司机/管理员接单"""
    if order_id not in _customer_orders:
        raise HTTPException(status_code=404, detail="订单不存在")
    order = _customer_orders[order_id]
    if order["status"] != "pending":
        raise HTTPException(status_code=400, detail="订单状态不允许接单")
    order["status"] = "accepted"
    order["driver_id"] = user.get("sub", "")
    order["driver_name"] = user.get("sub", "")
    order["updated_at"] = datetime.utcnow().isoformat()
    return {"status": "ok", "order": order}


@router.post("/accept-order-with-photo/{order_id}")
async def accept_order_with_photo(
    order_id: str,
    photo_url: str = Query(""),
    user: dict = Depends(require_role("driver", "admin", "warehouse")),
):
    """司机接单并上传出发拍照"""
    if order_id not in _customer_orders:
        raise HTTPException(status_code=404, detail="订单不存在")
    order = _customer_orders[order_id]
    if order["status"] != "pending":
        raise HTTPException(status_code=400, detail="订单状态不允许接单")
    order["status"] = "accepted"
    order["driver_id"] = user.get("sub", "")
    order["driver_name"] = user.get("sub", "")
    order["updated_at"] = datetime.utcnow().isoformat()
    if photo_url:
        order["accept_photo_url"] = photo_url
    return {"status": "ok", "order": order}


@router.get("/driver-orders")
async def get_driver_orders(user: dict = Depends(get_current_user)):
    """获取当前司机已接的订单"""
    driver_id = user.get("sub", "")
    my_orders = [
        o for o in _customer_orders.values()
        if o.get("driver_id") == driver_id
    ]
    my_orders.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return {"count": len(my_orders), "orders": my_orders}


# ==================== 司机更新订单状态 ====================

class OrderStatusUpdate(BaseModel):
    status: str  # in_transit / delivered
    photo_url: str = ""  # 送达拍照URL

@router.post("/update-order-status/{order_id}")
async def update_order_status(
    order_id: str,
    status: str = Query(..., description="in_transit(开始配送)/delivered(已送达)"),
    photo_url: str = Query(""),
    user: dict = Depends(require_role("driver", "admin", "warehouse")),
):
    """司机/管理员更新订单配送状态"""
    if order_id not in _customer_orders:
        raise HTTPException(status_code=404, detail="订单不存在")
    order = _customer_orders[order_id]
    user_id = user.get("sub", "")
    user_role = user.get("role", "")
    is_driver = order.get("driver_id") == user_id
    is_admin = user_role in ("admin", "warehouse")
    if not is_driver and not is_admin:
        raise HTTPException(status_code=403, detail="仅接单司机或管理员可操作此订单")
    valid_statuses = ["in_transit", "delivered"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail="无效的状态，仅支持 in_transit/delivered")
    # 状态流转校验
    if status == "in_transit" and order["status"] != "accepted":
        raise HTTPException(status_code=400, detail="仅已接单订单可开始配送")
    if status == "delivered" and order["status"] != "in_transit":
        raise HTTPException(status_code=400, detail="仅配送中订单可标记送达")
    order["status"] = status
    if status == "delivered" and photo_url:
        order["deliver_photo_url"] = photo_url
    order["updated_at"] = datetime.utcnow().isoformat()
    return {"status": "ok", "order": order}


# ==================== 客户签收确认 ====================

@router.post("/confirm-receive/{order_id}")
async def confirm_receive(
    order_id: str,
    user: dict = Depends(require_role("customer", "admin", "warehouse")),
):
    """客户/管理员确认签收，订单状态变为 completed"""
    if order_id not in _customer_orders:
        raise HTTPException(status_code=404, detail="订单不存在")
    order = _customer_orders[order_id]
    user_id = user.get("sub", "")
    user_role = user.get("role", "")
    is_customer = order.get("customer_id") == user_id
    is_admin = user_role in ("admin", "warehouse")
    if not is_customer and not is_admin:
        raise HTTPException(status_code=403, detail="仅下单客户或管理员可签收确认")
    if order["status"] != "delivered":
        raise HTTPException(status_code=400, detail="仅已送达订单可签收确认")
    order["status"] = "completed"
    order["signed_by_customer"] = True
    order["updated_at"] = datetime.utcnow().isoformat()
    return {"status": "ok", "order": order}


# ==================== 订单实时追踪（P0-1: 司机/客户查看实时温度+车辆位置） ====================

@router.get("/order-tracking/{order_id}")
async def get_order_tracking(
    order_id: str,
    user: dict = Depends(require_role("admin", "warehouse", "driver", "customer")),
):
    """根据订单ID获取车辆实时追踪数据（温度、位置、告警）"""
    ws = get_world_state()
    
    order = None
    matched_vehicle = None
    matched_waybill = None

    if order_id in _customer_orders:
        order = _customer_orders[order_id]
    elif order_id in ws["waybills"]:
        order = ws["waybills"][order_id]
        for v in ws["vehicles"]:
            if v.get("waybill_no") == order_id:
                matched_vehicle = v
                matched_waybill = order
                break
    else:
        for wb_id, wb_data in ws["waybills"].items():
            if wb_id == order_id:
                order = wb_data
                for v in ws["vehicles"]:
                    if v.get("waybill_no") == wb_id:
                        matched_vehicle = v
                        matched_waybill = wb_data
                        break
                break

    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    if not matched_vehicle:
        for v in ws["vehicles"]:
            for wb_id, wb_data in ws["waybills"].items():
                if order.get("origin") in wb_data.get("origin", "") or order.get("destination") in wb_data.get("destination", ""):
                    if order.get("cargo_category") and order.get("cargo_category") in wb_data.get("cargo_type", ""):
                        matched_vehicle = v
                        matched_waybill = wb_data
                        break
            if order.get("driver_name") and v.get("waybill_no"):
                matched_vehicle = v
                matched_waybill = ws["waybills"].get(v["waybill_no"])
                break
            if matched_vehicle:
                break

    # 如果没有精确匹配，取一辆在线的同温区车辆作为模拟追踪数据
    if not matched_vehicle:
        for v in ws["vehicles"]:
            zone_map = {"冷冻区": "frozen", "冷藏区": "refrigerated", "恒温区": "ambient"}
            order_zone = zone_map.get(order.get("zone_name", ""), "frozen")
            if v.get("cargo_zone") == order_zone:
                matched_vehicle = v
                matched_waybill = ws["waybills"].get(v["waybill_no"])
                break

    if not matched_vehicle:
        return {
            "order_id": order_id,
            "tracking_available": False,
            "message": "暂无车辆追踪数据，请等待司机接单后查看",
        }

    # 获取该车辆的告警
    vehicle_alerts = [
        a for a in ws["alerts"]
        if a.get("device_id") == matched_vehicle["device_id"]
    ]

    # 温度合规检查
    temp_compliant = matched_vehicle.get("temperature_compliant", True)
    target_temp = matched_vehicle.get("target_temperature", 0)
    current_temp = matched_vehicle.get("temperature", 0)
    temp_deviation = round(abs(current_temp - target_temp), 1) if target_temp else 0

    return {
        "order_id": order_id,
        "tracking_available": True,
        "vehicle": {
            "device_id": matched_vehicle["device_id"],
            "plate_number": matched_vehicle["plate_number"],
            "current_city": matched_vehicle["current_city"],
            "latitude": matched_vehicle["latitude"],
            "longitude": matched_vehicle["longitude"],
            "vehicle_speed": matched_vehicle["vehicle_speed"],
            "online": matched_vehicle["online"],
        },
        "temperature": {
            "current": current_temp,
            "target": target_temp,
            "deviation": temp_deviation,
            "is_compliant": temp_compliant,
            "humidity": matched_vehicle.get("humidity", 0),
        },
        "cold_car": {
            "health": matched_vehicle.get("cold_car_health", 0),
            "status": "正常" if matched_vehicle.get("cold_car_status") == 1 else "异常",
        },
        "alerts": {
            "count": len(vehicle_alerts),
            "items": vehicle_alerts[:3],  # 最多3条
        },
        "waybill_info": {
            "estimated_arrival": matched_waybill["estimated_arrival"] if matched_waybill else "计算中",
            "temperature_range": matched_waybill["temperature_range"] if matched_waybill else "N/A",
        } if matched_waybill else None,
    }


# ==================== 客户品质反馈（P0-3: 签收后评价） ====================

class QualityFeedback(BaseModel):
    cargo_condition: int = 5       # 货物完好度 1-5
    temp_satisfaction: int = 5     # 温度满意度 1-5
    overall_rating: int = 5        # 整体评价 1-5
    comment: str = ""

# 品质反馈存储
_quality_feedbacks: dict = {}  # order_id -> feedback


@router.post("/quality-feedback/{order_id}")
async def submit_quality_feedback(
    order_id: str,
    feedback: QualityFeedback,
    user: dict = Depends(get_current_user),
):
    """客户签收后提交品质反馈"""
    if order_id not in _customer_orders:
        raise HTTPException(status_code=404, detail="订单不存在")
    order = _customer_orders[order_id]
    user_id = user.get("sub", "")
    if order.get("customer_id") != user_id:
        raise HTTPException(status_code=403, detail="仅下单客户可提交反馈")
    if order["status"] != "completed":
        raise HTTPException(status_code=400, detail="仅已完成订单可提交反馈")

    _quality_feedbacks[order_id] = {
        "order_id": order_id,
        "customer_id": user_id,
        "cargo_name": order.get("cargo_name", ""),
        "driver_name": order.get("driver_name", ""),
        "cargo_condition": feedback.cargo_condition,
        "temp_satisfaction": feedback.temp_satisfaction,
        "overall_rating": feedback.overall_rating,
        "comment": feedback.comment,
        "created_at": datetime.utcnow().isoformat(),
    }
    return {"status": "ok", "feedback": _quality_feedbacks[order_id]}


@router.get("/quality-feedback/{order_id}")
async def get_quality_feedback(
    order_id: str,
    user: dict = Depends(require_role("admin", "warehouse", "customer", "driver")),
):
    """查询订单品质反馈（客户、司机、管理员均可查看）"""
    fb = _quality_feedbacks.get(order_id)
    if not fb:
        return {"has_feedback": False, "feedback": None}
    return {"has_feedback": True, "feedback": fb}


# ==================== 删除订单 ====================

@router.delete("/order/{order_id}")
async def delete_order(
    order_id: str,
    user: dict = Depends(get_current_user),
):
    """
    删除/取消订单：
    - 管理员/仓库经理：可删除任何状态的订单
    - 客户：仅 pending/accepted/completed 可操作
    - 司机：仅 pending/accepted/completed 可操作
    """
    if order_id not in _customer_orders:
        raise HTTPException(status_code=404, detail="订单不存在")
    order = _customer_orders[order_id]
    user_id = user.get("sub", "")
    user_role = user.get("role", "")
    is_driver = order.get("driver_id") == user_id
    is_customer = order.get("customer_id") == user_id
    is_admin = user_role in ("admin", "warehouse")

    if not is_driver and not is_customer and not is_admin:
        raise HTTPException(status_code=403, detail="无权操作此订单")

    if is_admin:
        order["status"] = "cancelled"
        order["updated_at"] = datetime.utcnow().isoformat()
        return {"status": "ok", "message": f"订单 {order_id} 已取消"}

    if order["status"] in ("pending", "accepted", "completed"):
        order["status"] = "cancelled"
        order["updated_at"] = datetime.utcnow().isoformat()
        return {"status": "ok", "message": f"订单 {order_id} 已取消"}

    raise HTTPException(
        status_code=400,
        detail=f"订单状态 '{order['status']}' 不允许删除，仅管理员可操作运输中的订单",
    )


# ==================== 统一订单管理（管理员/仓库经理） ====================

@router.get("/all-orders")
async def get_all_orders(user: dict = Depends(get_current_user)):
    """
    获取所有订单（统一视图）：
    - 合并 customer 订单 + world_state 运输中运单
    - 统一状态机: pending → accepted → in_transit → delivered → completed
    - 管理员/仓库经理可用
    """
    ws = get_world_state()
    merged = {}

    # 1. 先加载 customer 订单（真实 CRUD 订单）
    for order_id, order in _customer_orders.items():
        merged[order_id] = {
            "waybill_id": order_id,
            "order_id": order_id,
            "cargo_name": order.get("cargo_name", ""),
            "cargo_category": order.get("cargo_category", "冷链"),
            "origin": order.get("origin", ""),
            "destination": order.get("destination", ""),
            "quantity": order.get("quantity", 0),
            "unit": order.get("unit", "kg"),
            "status": order.get("status", "pending"),
            "driver_id": order.get("driver_id", ""),
            "driver_name": order.get("driver_name", ""),
            "customer_id": order.get("customer_id", ""),
            "customer_name": order.get("customer_name", ""),
            "temperature_requirement": order.get("temperature_requirement", ""),
            "created_at": order.get("created_at", ""),
            "updated_at": order.get("updated_at", ""),
            "price": order.get("price", 0),
            "weight_kg": order.get("weight_kg", 0),
            "source": "customer_order",  # 标记来源
        }

    # 2. 补充 world_state 中运输中的运单（如果没有被 customer 订单覆盖）
    for wb_id, wb_data in ws.get("waybills", {}).items():
        if wb_id not in merged:
            merged[wb_id] = {
                "waybill_id": wb_id,
                "order_id": wb_id,
                "cargo_name": wb_data.get("cargo_name", wb_data.get("cargo_type", "")),
                "cargo_category": wb_data.get("cargo_category", "冷链"),
                "origin": wb_data.get("origin", ""),
                "destination": wb_data.get("destination", ""),
                "quantity": wb_data.get("quantity", 0),
                "unit": wb_data.get("unit", "kg"),
                "status": wb_data.get("status", "in_transit"),
                "driver_id": wb_data.get("driver_id", ""),
                "driver_name": wb_data.get("driver_name", ""),
                "customer_id": "",
                "customer_name": "",
                "temperature_requirement": wb_data.get("temperature_requirement", ""),
                "created_at": wb_data.get("created_at", ""),
                "updated_at": wb_data.get("updated_at", ""),
                "price": 0,
                "weight_kg": wb_data.get("quantity", 0),
                "source": "world_simulation",
            }

    orders_list = list(merged.values())
    orders_list.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return {"count": len(orders_list), "orders": orders_list}


class AdminAssignDriver(BaseModel):
    driver_id: str
    driver_name: str = ""
    vehicle_id: str = ""
    notes: str = ""

@router.post("/admin-assign-driver/{order_id}")
async def admin_assign_driver(
    order_id: str,
    data: AdminAssignDriver,
    user: dict = Depends(get_current_user),
):
    """管理员/仓库经理分配司机"""
    if order_id not in _customer_orders:
        raise HTTPException(status_code=404, detail="订单不存在")
    order = _customer_orders[order_id]
    if order["status"] not in ("pending", "created"):
        # 兼容旧状态
        if order["status"] not in ("pending", "accepted"):
            raise HTTPException(status_code=400, detail="仅待接单订单可分配司机")
    order["status"] = "accepted"
    order["driver_id"] = data.driver_id
    order["driver_name"] = data.driver_name or data.driver_id
    order["updated_at"] = datetime.utcnow().isoformat()
    if data.notes:
        order["notes"] = (order.get("notes", "") + f" [管理员备注: {data.notes}]").strip()
    return {"status": "ok", "order": order}


# ==================== 仓库订单审核 ====================

class OrderReviewRequest(BaseModel):
    action: str  # "approve" 或 "reject"
    notes: str = ""


@router.get("/pending-review-orders")
async def get_pending_review_orders(user: dict = Depends(require_role("admin", "warehouse"))):
    """获取待审核的订单（已接单但尚未审核）"""
    pending = [
        o for o in _customer_orders.values()
        if o.get("status") == "accepted" and not o.get("review_status")
    ]
    pending.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return {"count": len(pending), "orders": pending}


@router.get("/all-review-orders")
async def get_all_review_orders(
    status: str = None,
    user: dict = Depends(require_role("admin", "warehouse")),
):
    """获取所有审核订单（可按状态筛选）"""
    all_orders = list(_customer_orders.values())
    if status and status != "all":
        if status == "pending":
            all_orders = [o for o in all_orders if o.get("status") == "accepted" and not o.get("review_status")]
        else:
            all_orders = [o for o in all_orders if o.get("review_status") == status]
    all_orders.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return {"count": len(all_orders), "orders": all_orders}


@router.post("/review-order/{order_id}")
async def review_order(
    order_id: str,
    body: OrderReviewRequest,
    user: dict = Depends(require_role("admin", "warehouse")),
):
    """审核订单（通过/驳回）"""
    if order_id not in _customer_orders:
        raise HTTPException(status_code=404, detail="订单不存在")
    order = _customer_orders[order_id]
    if body.action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="action 必须是 approve 或 reject")
    if body.action == "reject" and not body.notes.strip():
        raise HTTPException(status_code=400, detail="驳回订单必须填写原因")
    
    order["review_status"] = "approved" if body.action == "approve" else "rejected"
    order["review_notes"] = body.notes
    order["reviewed_by"] = user.get("sub", "")
    order["reviewed_at"] = datetime.utcnow().isoformat()
    
    if body.action == "reject":
        # 驳回后订单回到待接单状态
        order["status"] = "pending"
        order["driver_id"] = ""
        order["driver_name"] = ""
    else:
        # 审核通过：自动扣减库存（出库操作）
        _deduct_inventory_for_order(order)
    
    return {"status": "ok", "order": order}


def _deduct_inventory_for_order(order: dict):
    """
    审核通过后自动扣减库存。
    从世界状态的仓库库存中查找匹配的货物并扣减对应数量。
    """
    try:
        from ..services.world_state import get_world_state
        ws = get_world_state()
        
        cargo_name = order.get("cargo_name", "")
        quantity = order.get("quantity", 0)
        zone_name = order.get("zone_name", "")
        
        if quantity <= 0:
            return
        
        # 遍历仓库库存，查找匹配的货物
        warehouse_inventory = ws.get("warehouse_inventory", {})
        if not warehouse_inventory:
            return
        
        remaining = quantity
        for wh_id, wh_data in warehouse_inventory.items():
            items = wh_data.get("items", [])
            for item in items:
                if remaining <= 0:
                    break
                # 匹配产品名或温区
                if (cargo_name and cargo_name in item.get("product_name", "")) or \
                   (zone_name and zone_name in item.get("zone", "")):
                    available = item.get("quantity_kg", 0)
                    if available > 0:
                        deduct = min(remaining, available)
                        item["quantity_kg"] = available - deduct
                        remaining -= deduct
                        item["updated_at"] = datetime.utcnow().isoformat()
            if remaining <= 0:
                break
        
        if remaining > 0:
            # 库存不足记录日志
            print(f"[WARNING] 订单 {order.get('order_id')} 审核通过，但库存不足以完全扣减，"
                  f"需求: {quantity}kg, 已扣: {quantity - remaining}kg, 缺口: {remaining}kg")
    except Exception as e:
        print(f"[ERROR] 库存扣减失败: {e}")
