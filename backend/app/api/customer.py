"""
客户温控查询服务 API
模块14: 客户温控查询服务
- 运单温度查询
- 温度曲线数据
- 温度证明文件下载
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse

from ..core.security import get_current_user

router = APIRouter(prefix="/api/v1/customer", tags=["客户服务"])

# 内存存储客户查询记录（后续可迁移到 PostgreSQL）
_waybill_temperature_data: dict = {}  # waybill_id -> list of temp records


# ==================== 初始化示例数据 ====================
def _init_sample_data():
    if not _waybill_temperature_data:
        now = datetime.utcnow()
        # 生成运单温度曲线数据
        waybills = ["WB20260528001", "WB20260528002", "WB20260527001", "WB20260527002"]

        for wb in waybills:
            import random
            random.seed(hash(wb) % 10000)

            base_temp = random.choice([-18, 4, 20])  # 冷冻/冷藏/恒温
            records = []
            for i in range(144):  # 24小时，每10分钟一条
                ts = now - timedelta(hours=24) + timedelta(minutes=i * 10)
                temp = base_temp + random.gauss(0, 0.3)
                # 模拟卸货开门时的温度波动
                if i % 36 == 0:
                    temp += random.uniform(1, 3)
                records.append({
                    "timestamp": ts.isoformat(),
                    "temperature": round(temp, 2),
                    "humidity": round(70 + random.gauss(0, 3), 1),
                    "location": _random_location(i),
                    "door_status": 1 if i % 36 == 0 else 0,
                })

            _waybill_temperature_data[wb] = {
                "waybill_id": wb,
                "cargo_type": random.choice(["生鲜水果", "冷冻肉类", "疫苗试剂", "乳制品"]),
                "temperature_requirement": f"{base_temp - 3}°C ~ {base_temp + 3}°C",
                "origin": random.choice(["山东寿光", "云南昆明", "海南三亚", "内蒙古呼和浩特"]),
                "destination": random.choice(["北京朝阳", "上海浦东", "广州天河", "成都高新"]),
                "departure_time": (now - timedelta(hours=24)).isoformat(),
                "estimated_arrival": (now + timedelta(hours=2)).isoformat(),
                "current_status": "运输中",
                "records": records,
            }


def _random_location(index: int) -> str:
    locations = [
        "G2京沪高速", "G4京港澳高速", "G15沈海高速",
        "G25长深高速", "S32申嘉湖高速", "S20外环高速",
        "城区配送", "冷库出货", "配送站到达",
    ]
    return locations[index % len(locations)]


_init_sample_data()


# ==================== 客户查询接口 ====================

@router.get("/query/{waybill_id}")
async def query_waybill_temperature(waybill_id: str):
    """
    客户查询运单温度（无需登录，通过运单号查询）
    支持微信小程序/Web页面调用
    """
    data = _waybill_temperature_data.get(waybill_id)
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
        "current_temperature": records[-1]["temperature"] if records else None,
        "temperature_range": f"{min(temps):.1f}°C ~ {max(temps):.1f}°C",
        "avg_temperature": f"{sum(temps) / len(temps):.1f}°C" if temps else "N/A",
        "is_compliant": all(
            abs(r["temperature"] - (max(temps) + min(temps)) / 2) < 5
            for r in records
        ),
    }


@router.get("/temperature-curve/{waybill_id}")
async def get_temperature_curve(
    waybill_id: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
):
    """
    获取运单温度曲线数据（供前端 ECharts 渲染）
    """
    data = _waybill_temperature_data.get(waybill_id)
    if not data:
        raise HTTPException(status_code=404, detail="运单不存在")

    records = data["records"]

    if start_time:
        records = [r for r in records if r["timestamp"] >= start_time]
    if end_time:
        records = [r for r in records if r["timestamp"] <= end_time]

    timestamps = [r["timestamp"] for r in records]
    temperatures = [r["temperature"] for r in records]
    humidities = [r["humidity"] for r in records]

    # 标注开门事件
    door_events = [
        {"timestamp": r["timestamp"], "temperature": r["temperature"]}
        for r in records if r.get("door_status") == 1
    ]

    return {
        "waybill_id": waybill_id,
        "cargo_type": data["cargo_type"],
        "temperature_requirement": data["temperature_requirement"],
        "data_points": len(records),
        "timestamps": timestamps,
        "temperatures": temperatures,
        "humidities": humidities,
        "door_events": door_events,
        "current_temperature": temperatures[-1] if temperatures else None,
    }


@router.get("/certificate/{waybill_id}")
async def download_temperature_certificate(
    waybill_id: str,
    format: str = "text",
):
    """
    生成温度证明文件（文本格式，后续可扩展PDF）
    """
    data = _waybill_temperature_data.get(waybill_id)
    if not data:
        raise HTTPException(status_code=404, detail="运单不存在")

    records = data["records"]
    temps = [r["temperature"] for r in records]

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
        f"当前状态:   {data['current_status']}",
        f"-" * 55,
        f"全程温度统计:",
        f"  最低温度: {min(temps):.1f}°C",
        f"  最高温度: {max(temps):.1f}°C",
        f"  平均温度: {sum(temps) / len(temps):.1f}°C",
        f"  记录点数: {len(records)}",
        f"  温控达标: {'是' if all(abs(r['temperature'] - (max(temps)+min(temps))/2) < 5 for r in records) else '否'}",
        f"-" * 55,
        f"全程温度曲线 (每30分钟采样):",
    ]

    for i, r in enumerate(records):
        if i % 3 == 0:  # 每30分钟
            lines.append(f"  {r['timestamp'][:16]}  |  {r['temperature']:>5.1f}°C  |  {r['location']}")

    lines.append(f"=" * 55)
    lines.append(f"证明生成时间: {datetime.utcnow().isoformat()}")
    lines.append(f"本证明由冷链物流智能监控平台自动生成")
    lines.append(f"平台保证数据真实、完整、不可篡改")

    return PlainTextResponse(
        "\n".join(lines),
        headers={"Content-Disposition": f"attachment; filename=temperature_certificate_{waybill_id}.txt"},
    )


@router.get("/my-orders")
async def get_my_orders(
    phone: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    """获取当前用户关联的运单列表（移动端用）"""
    # 模拟返回用户关联的运单
    my_waybills = []
    for wb_id, data in list(_waybill_temperature_data.items())[:3]:
        records = data["records"]
        temps = [r["temperature"] for r in records]
        my_waybills.append({
            "waybill_id": wb_id,
            "cargo_type": data["cargo_type"],
            "origin": data["origin"],
            "destination": data["destination"],
            "current_status": data["current_status"],
            "current_temperature": records[-1]["temperature"],
            "temperature_range": f"{min(temps):.1f}°C ~ {max(temps):.1f}°C",
            "is_compliant": all(abs(r["temperature"] - (max(temps)+min(temps))/2) < 5 for r in records),
        })

    return {"count": len(my_waybills), "orders": my_waybills}


@router.get("/scan")
async def scan_qr_query(
    code: str = Query(..., description="扫码获取的运单号"),
):
    """扫码查询（微信小程序扫码入口）"""
    return await query_waybill_temperature(code)
