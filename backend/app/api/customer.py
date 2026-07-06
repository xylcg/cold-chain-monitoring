"""
客户温控查询服务 API
模块：客户温控查询服务（货主+消费者双端查询）

核心功能：
- 运单号精准检索匹配（支持模糊匹配）
- 全链路温度曲线可视化数据
- 冷链详情可视化展示
- 标准化温控证明文件下载
- 分层查询权限机制（消费者/货主）
- 与追溯链、传感器、预警模块深度联动
"""
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse, HTMLResponse
from pydantic import BaseModel

from ..core.security import get_current_user, require_role
from ..services.world_state import get_world_state
from ..services.redis_service import redis_service

router = APIRouter(prefix="/api/v1/customer", tags=["客户温控查询"])

# ==================== 数据模型 ====================

class QueryResult(BaseModel):
    waybill_id: str
    trace_code: str = ""
    cargo_name: str = ""
    cargo_category: str = ""
    temperature_requirement: str = ""
    is_high_sensitivity: bool = False
    origin: str = ""
    destination: str = ""
    quantity: float = 0.0
    unit: str = "kg"
    status: str = ""
    is_compliant: bool = True
    violations_count: int = 0
    temperature_summary: dict = None
    current_temperature: float = 0.0
    humidity: float = 0.0
    last_update: str = ""
    completed_stages: int = 0
    total_stages: int = 0
    stages: list = None
    violations: list = None
    blockchain: dict = None


class TemperatureCurveData(BaseModel):
    waybill_id: str
    trace_code: str
    cargo_name: str
    temperature_requirement: str
    threshold: dict = None
    point_count: int = 0
    points: list = None
    door_events: list = None


# ==================== 运单号标准化与匹配 ====================

def normalize_waybill_id(waybill_id: str) -> str:
    """标准化运单号格式"""
    if not waybill_id:
        return ""
    normalized = ''.join(filter(str.isalnum, waybill_id.upper()))
    if normalized.isdigit():
        normalized = f"WB{normalized}"
    return normalized


def match_waybill_pattern(input_str: str, stored_id: str) -> bool:
    """运单号模糊匹配"""
    input_norm = normalize_waybill_id(input_str)
    stored_norm = normalize_waybill_id(stored_id)
    if input_norm == stored_norm:
        return True
    if input_norm and stored_norm.startswith(input_norm):
        return True
    if input_norm and input_norm in stored_norm:
        return True
    return False


# ==================== 全链路阶段定义 ====================

STAGES = [
    {"key": "precool", "name": "产地预冷", "icon": "❄️"},
    {"key": "warehouse_in", "name": "仓储入库", "icon": "🏭"},
    {"key": "warehouse_store", "name": "仓储存储", "icon": "📦"},
    {"key": "loading", "name": "装车发车", "icon": "🚛"},
    {"key": "transport", "name": "干线运输", "icon": "🛣️"},
    {"key": "transit_in", "name": "枢纽中转入仓", "icon": "🔄"},
    {"key": "transit_out", "name": "枢纽中转出仓", "icon": "🔄"},
    {"key": "last_mile", "name": "末端配送", "icon": "🚴"},
    {"key": "sign", "name": "消费者签收", "icon": "✅"},
]


def get_stage_name(stage_key: str) -> str:
    return next((s["name"] for s in STAGES if s["key"] == stage_key), stage_key)


def get_stage_icon(stage_key: str) -> str:
    return next((s["icon"] for s in STAGES if s["key"] == stage_key), "📋")


# ==================== 核心数据获取函数 ====================

def get_trace_data_by_waybill(waybill_id: str) -> Dict[str, Any]:
    """根据运单号获取追溯数据"""
    from .traceability import (
        TRACE_DATA, TRACE_RECORDS, TRACE_CODE_MAP, WAYBILL_TRACE_MAP,
        init_world_state_waybills,
    )

    trace_code = WAYBILL_TRACE_MAP.get(waybill_id)
    
    if not trace_code:
        for wb_id, tc in WAYBILL_TRACE_MAP.items():
            if match_waybill_pattern(waybill_id, wb_id):
                trace_code = tc
                waybill_id = wb_id
                break

    if not trace_code:
        init_world_state_waybills()
        trace_code = WAYBILL_TRACE_MAP.get(waybill_id)
        if not trace_code:
            for wb_id, tc in WAYBILL_TRACE_MAP.items():
                if match_waybill_pattern(waybill_id, wb_id):
                    trace_code = tc
                    waybill_id = wb_id
                    break

    if not trace_code or trace_code not in TRACE_DATA:
        return None

    data = TRACE_DATA[trace_code]
    record_ids = TRACE_CODE_MAP.get(trace_code, [])
    records = [r for r in TRACE_RECORDS if r["id"] in record_ids]
    records = sorted(records, key=lambda r: r.get("timestamp", ""))

    return {
        "waybill_id": data["waybill_id"],
        "trace_code": trace_code,
        "data": data,
        "records": records,
    }


def analyze_temperature_violations(records: list, temperature_requirement: str) -> list:
    """分析温度异常记录"""
    violations = []
    if not temperature_requirement:
        return violations
    
    req_str = str(temperature_requirement)
    if "~" not in req_str:
        return violations
    
    try:
        parts = req_str.split("~")
        min_req = float(parts[0].replace("℃", "").strip())
        max_req = float(parts[1].replace("℃", "").strip())
        
        for r in records:
            if "temperature" in r and r["temperature"] is not None:
                temp = r["temperature"]
                if temp < min_req or temp > max_req:
                    violations.append(r)
    except Exception:
        pass
    
    return violations


def generate_temperature_summary(records: list) -> dict:
    """生成温度统计摘要"""
    temps = [r["temperature"] for r in records if "temperature" in r and r["temperature"] is not None]
    humidity_vals = [r["humidity"] for r in records if "humidity" in r and r["humidity"] is not None]
    
    if not temps:
        return {
            "min": 0, "max": 0, "avg": 0,
            "range": "N/A", "humidity_avg": 0,
        }
    
    return {
        "min": round(min(temps), 1),
        "max": round(max(temps), 1),
        "avg": round(sum(temps) / len(temps), 1),
        "range": f"{round(min(temps), 1)}~{round(max(temps), 1)}℃",
        "humidity_avg": round(sum(humidity_vals) / len(humidity_vals), 1) if humidity_vals else 0,
        "point_count": len(temps),
    }


def get_stage_info(records: list) -> list:
    """获取各阶段信息"""
    stages_info = []
    for stage in STAGES:
        stage_records = [r for r in records if r.get("stage") == stage["key"]]
        if stage_records:
            stage_temps = [r["temperature"] for r in stage_records if "temperature" in r and r["temperature"] is not None]
            stages_info.append({
                "key": stage["key"],
                "name": stage["name"],
                "icon": stage["icon"],
                "has_records": True,
                "count": len(stage_records),
                "first_time": stage_records[0].get("timestamp", ""),
                "last_time": stage_records[-1].get("timestamp", ""),
                "temp_range": f"{round(min(stage_temps), 1)}~{round(max(stage_temps), 1)}℃" if stage_temps else "N/A",
                "avg_temp": round(sum(stage_temps) / len(stage_temps), 1) if stage_temps else 0,
            })
        else:
            stages_info.append({
                "key": stage["key"],
                "name": stage["name"],
                "icon": stage["icon"],
                "has_records": False,
            })
    return stages_info


def get_blockchain_info(trace_code: str) -> dict:
    """获取区块链存证信息"""
    from .traceability import BLOCKCHAIN_LEDGER
    
    for block in BLOCKCHAIN_LEDGER:
        if block["data"].get("trace_code") == trace_code:
            return {
                "on_chain": True,
                "block_number": block["block_number"],
                "block_hash": block["block_hash"],
                "merkle_root": block["merkle_root"],
                "certified_at": block["created_at"],
                "prev_hash": block["prev_hash"],
            }
    return {"on_chain": False}


# ==================== 公开查询接口（消费者） ====================

@router.get("/query")
async def query_by_waybill(
    waybill_id: str = Query(..., description="运单号"),
):
    """
    公开查询接口（消费者扫码查询，无需登录）
    输入运单号查询货物全运输链路温控信息
    """
    result = get_trace_data_by_waybill(waybill_id)
    if not result:
        return {"error": "未找到该运单号对应的冷链记录"}

    waybill_id = result["waybill_id"]
    trace_code = result["trace_code"]
    data = result["data"]
    records = result["records"]

    temperature_summary = generate_temperature_summary(records)
    violations = analyze_temperature_violations(records, data.get("temperature_requirement", ""))
    stages_info = get_stage_info(records)
    blockchain = get_blockchain_info(trace_code)

    temps = [r["temperature"] for r in records if "temperature" in r and r["temperature"] is not None]
    humidity_vals = [r["humidity"] for r in records if "humidity" in r and r["humidity"] is not None]
    
    current_temp = temps[-1] if temps else 0
    current_humidity = humidity_vals[-1] if humidity_vals else 0
    last_update = records[-1].get("timestamp", "") if records else datetime.utcnow().isoformat()

    return {
        "success": True,
        "waybill_id": waybill_id,
        "trace_code": trace_code,
        "cargo_name": data["cargo_name"],
        "cargo_category": data["cargo_category"],
        "temperature_requirement": data["temperature_requirement"],
        "is_high_sensitivity": data["is_high_sensitivity"],
        "origin": data["origin"],
        "destination": data["destination"],
        "quantity": data["quantity"],
        "unit": data["unit"],
        "status": data["status"],
        "is_compliant": len(violations) == 0,
        "violations_count": len(violations),
        "violations": violations,
        "temperature_summary": temperature_summary,
        "current_temperature": current_temp,
        "current_humidity": current_humidity,
        "last_update": last_update,
        "total_stages": len(stages_info),
        "completed_stages": len([s for s in stages_info if s["has_records"]]),
        "stages": stages_info,
        "records": records,
        "blockchain": blockchain,
    }


@router.get("/query/temperature-curve")
async def get_temperature_curve(
    waybill_id: str = Query(..., description="运单号"),
    include_humidity: bool = True,
    include_door_events: bool = True,
):
    """
    获取温度曲线数据（公开接口）
    返回全链路时序温湿度数据，用于前端图表渲染
    """
    result = get_trace_data_by_waybill(waybill_id)
    if not result:
        return {"error": "未找到该运单号"}

    trace_code = result["trace_code"]
    data = result["data"]
    records = result["records"]

    points = []
    door_events = []
    for r in records:
        temp = r.get("temperature")
        if temp is not None:
            points.append({
                "timestamp": r.get("timestamp", ""),
                "temperature": temp,
                "humidity": r.get("humidity", 0),
                "location": r.get("location", ""),
                "stage": r.get("stage", ""),
                "stage_name": get_stage_name(r.get("stage", "")),
                "action": r.get("action", ""),
                "device_id": r.get("device_id", ""),
                "notes": r.get("notes", ""),
                "lat": r.get("lat", 0),
                "lng": r.get("lng", 0),
            })

        if include_door_events:
            action = r.get("action", "")
            if action and ("车门" in action or action == "door_open"):
                door_events.append({
                    "timestamp": r.get("timestamp", ""),
                    "temperature": temp,
                    "location": r.get("location", ""),
                    "action": action,
                })

    req = data.get("temperature_requirement", "")
    threshold = {}
    if req:
        req_str = str(req)
        if "~" in req_str:
            try:
                parts = req_str.split("~")
                threshold["min"] = float(parts[0].replace("℃", "").strip())
                threshold["max"] = float(parts[1].replace("℃", "").strip())
            except Exception:
                pass

    return {
        "success": True,
        "waybill_id": waybill_id,
        "trace_code": trace_code,
        "cargo_name": data["cargo_name"],
        "temperature_requirement": data["temperature_requirement"],
        "threshold": threshold,
        "point_count": len(points),
        "points": points,
        "door_events": door_events,
    }


# ==================== 温控证明文件下载 ====================

@router.get("/certificate")
async def get_temperature_certificate(
    waybill_id: str = Query(..., description="运单号"),
    format: str = "text",
    version: str = "simple",
    user: dict = Depends(get_current_user),
):
    """
    获取标准化温控证明文件
    - version=simple: 简易版（消费者）
    - version=full: 完整版（货主企业）
    """
    result = get_trace_data_by_waybill(waybill_id)
    if not result:
        raise HTTPException(status_code=404, detail="未找到该运单号")

    waybill_id = result["waybill_id"]
    trace_code = result["trace_code"]
    data = result["data"]
    records = result["records"]

    if not records:
        raise HTTPException(status_code=404, detail="无温控记录")

    temperature_summary = generate_temperature_summary(records)
    violations = analyze_temperature_violations(records, data.get("temperature_requirement", ""))
    blockchain = get_blockchain_info(trace_code)

    time_diff = None
    if records:
        try:
            time_diff = datetime.fromisoformat(records[-1]["timestamp"]) - datetime.fromisoformat(records[0]["timestamp"])
        except Exception:
            pass

    if format == "html":
        return _generate_certificate_html(data, records, temperature_summary, violations, blockchain, version)

    return _generate_certificate_text(data, records, temperature_summary, violations, blockchain, version, time_diff)


def _generate_certificate_text(data: dict, records: list, temp_summary: dict, violations: list, blockchain: dict, version: str, time_diff):
    """生成文本格式的温控证明"""
    lines = [
        "=" * 70,
        "                    冷链温控证明",
        "=" * 70,
        "",
        f"【证明编号】RPT-{data['trace_code']}",
        f"【运单号】   {data['waybill_id']}",
        f"【溯源码】   {data['trace_code']}",
        f"【生成时间】 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
        "",
        "【货品信息】",
        f"  名称: {data['cargo_name']}",
        f"  类别: {data['cargo_category']}",
        f"  数量: {data['quantity']} {data['unit']}",
        f"  高敏: {'是' if data['is_high_sensitivity'] else '否'}",
        "",
        "【运输路线】",
        f"  发货地: {data['origin']}",
        f"  收货地: {data['destination']}",
        f"  温度要求: {data['temperature_requirement']}",
        "",
        "【温控统计】",
        f"  温度范围: {temp_summary.get('range', 'N/A')}",
        f"  平均温度: {temp_summary.get('avg', 'N/A')}℃",
        f"  平均湿度: {temp_summary.get('humidity_avg', 'N/A')}%",
        f"  温控达标: {'是' if len(violations) == 0 else '否'}",
        f"  异常次数: {len(violations)}",
        "",
    ]

    if version == "full":
        lines.extend([
            "【运输时长】",
            f"  开始时间: {records[0]['timestamp'][:19]}" if records else "N/A",
            f"  结束时间: {records[-1]['timestamp'][:19]}" if records else "N/A",
            f"  总时长: {round(time_diff.total_seconds() / 3600, 1)}小时" if time_diff else "N/A",
            f"  记录总数: {len(records)}条",
            "",
            "【各环节温控详情】",
        ])

        stage_summary = {}
        for r in records:
            stage = r.get("stage", "unknown")
            if stage not in stage_summary:
                stage_summary[stage] = []
            if "temperature" in r and r["temperature"] is not None:
                stage_summary[stage].append(r["temperature"])

        for stage_key, stage_temps in stage_summary.items():
            if stage_temps:
                lines.extend([
                    f"  [{get_stage_icon(stage_key)} {get_stage_name(stage_key)}]",
                    f"    温度范围: {round(min(stage_temps), 1)}℃ ~ {round(max(stage_temps), 1)}℃",
                    f"    平均温度: {round(sum(stage_temps) / len(stage_temps), 1)}℃",
                    f"    记录数: {len(stage_temps)}",
                ])

        if violations:
            lines.extend([
                "",
                "【温度异常记录】",
            ])
            for v in violations:
                lines.append(f"  ⚠️ [{get_stage_name(v.get('stage', ''))}] {v.get('timestamp', '')[:16]} | {v.get('temperature', '')}℃ | {v.get('notes', '')}")

    lines.extend([
        "",
        "【区块链存证信息】",
        f"  存证状态: {'已上链' if blockchain.get('on_chain') else '待存证'}",
    ])

    if blockchain.get("on_chain"):
        lines.extend([
            f"  区块编号: #{blockchain['block_number']}",
            f"  区块哈希: {blockchain['block_hash'][:32]}...",
            f"  Merkle根: {blockchain['merkle_root'][:32]}...",
            f"  存证时间: {blockchain['certified_at'][:19]}",
        ])

    lines.extend([
        "",
        "=" * 70,
        "本证明由冷链追溯平台自动生成，数据来源于传感器实时采集，",
        "经区块链加密存证，不可篡改。",
        "=" * 70,
    ])

    return PlainTextResponse("\n".join(lines))


def _generate_certificate_html(data: dict, records: list, temp_summary: dict, violations: list, blockchain: dict, version: str):
    """生成HTML格式的温控证明"""
    time_diff = None
    if records:
        try:
            time_diff = datetime.fromisoformat(records[-1]["timestamp"]) - datetime.fromisoformat(records[0]["timestamp"])
        except Exception:
            pass

    violations_html = ""
    if violations:
        violations_html = f"""
        <div style="background:#fff3cd;border:1px solid #ffeeba;border-radius:8px;padding:15px;margin-top:15px;">
        <h3 style="color:#856404;margin:0 0 10px;">⚠️ 温度异常记录 ({len(violations)}条)</h3>
        <table style="width:100%;font-size:12px;border-collapse:collapse;">
        <tr style="background:#fff8e7;"><th style="padding:6px;text-align:left;">时间</th><th style="padding:6px;text-align:left;">环节</th><th style="padding:6px;text-align:right;">温度</th><th style="padding:6px;text-align:left;">说明</th></tr>
        """
        for v in violations:
            violations_html += f"""
            <tr><td style="padding:6px;border-bottom:1px solid #ffeeba;">{v.get('timestamp', '')[:16]}</td>
            <td style="padding:6px;border-bottom:1px solid #ffeeba;">{get_stage_name(v.get('stage', ''))}</td>
            <td style="padding:6px;border-bottom:1px solid #ffeeba;text-align:right;color:#dc3545;">{v.get('temperature', '')}℃</td>
            <td style="padding:6px;border-bottom:1px solid #ffeeba;">{v.get('notes', '')}</td></tr>
            """
        violations_html += "</table></div>"

    stage_html = ""
    if version == "full":
        stage_summary = {}
        for r in records:
            stage = r.get("stage", "unknown")
            if stage not in stage_summary:
                stage_summary[stage] = []
            if "temperature" in r and r["temperature"] is not None:
                stage_summary[stage].append(r["temperature"])

        stage_html = """
        <div style="margin-top:15px;">
        <h3 style="font-size:15px;font-weight:600;color:#333;margin:0 0 10px;">📋 各环节温控详情</h3>
        <table style="width:100%;font-size:13px;border-collapse:collapse;">
        <tr style="background:#f8f9fa;"><th style="padding:8px;text-align:left;">环节</th><th style="padding:8px;text-align:center;">温度范围</th><th style="padding:8px;text-align:center;">平均温度</th><th style="padding:8px;text-align:center;">记录数</th></tr>
        """
        for stage_key, stage_temps in stage_summary.items():
            if stage_temps:
                stage_html += f"""
                <tr style="border-bottom:1px solid #eee;"><td style="padding:8px;">{get_stage_icon(stage_key)} {get_stage_name(stage_key)}</td>
                <td style="padding:8px;text-align:center;">{round(min(stage_temps), 1)}~{round(max(stage_temps), 1)}℃</td>
                <td style="padding:8px;text-align:center;">{round(sum(stage_temps) / len(stage_temps), 1)}℃</td>
                <td style="padding:8px;text-align:center;">{len(stage_temps)}</td></tr>
                """
        stage_html += "</table></div>"

    blockchain_html = ""
    if blockchain.get("on_chain"):
        blockchain_html = f"""
        <div style="margin-top:15px;">
        <h3 style="font-size:15px;font-weight:600;color:#333;margin:0 0 10px;">🔗 区块链存证信息</h3>
        <div style="background:#f8f9fa;border-radius:8px;padding:12px;font-size:12px;color:#666;">
        <div>存证状态: <strong style="color:#28a745;">已上链</strong></div>
        <div>区块编号: #{blockchain['block_number']}</div>
        <div>区块哈希: <code>{blockchain['block_hash'][:16]}...</code></div>
        <div>Merkle根: <code>{blockchain['merkle_root'][:16]}...</code></div>
        <div>存证时间: {blockchain['certified_at'][:19]}</div>
        </div>
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width,initial-scale=1.0">
    <title>冷链温控证明 - {data['cargo_name']}</title>
    <style>
    body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;margin:0;padding:30px;background:#f5f5f5;}}
    .certificate{{background:white;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,0.1);padding:40px;max-width:800px;margin:0 auto;}}
    .header{{text-align:center;border-bottom:2px solid #007bff;padding-bottom:20px;margin-bottom:20px;}}
    .title{{font-size:24px;font-weight:bold;color:#333;margin:0;}}
    .subtitle{{font-size:14px;color:#666;margin-top:5px;}}
    .info-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:15px;margin-bottom:20px;}}
    .info-item{{background:#f8f9fa;border-radius:8px;padding:12px;}}
    .info-label{{font-size:11px;color:#666;margin-bottom:4px;display:block;}}
    .info-value{{font-size:14px;font-weight:600;color:#333;}}
    .info-value.code{{font-family:monospace;color:#007bff;}}
    .temp-display{{text-align:center;padding:20px;background:linear-gradient(135deg,#e7f3ff,#fff);border-radius:12px;margin-bottom:20px;}}
    .temp-value{{font-size:36px;font-weight:bold;color:#007bff;}}
    .temp-unit{{font-size:18px;color:#666;}}
    .compliance{{text-align:center;padding:15px;border-radius:8px;margin-bottom:20px;}}
    .compliance.ok{{background:#d4edda;color:#155724;border:1px solid #c3e6cb;}}
    .compliance.fail{{background:#f8d7da;color:#721c24;border:1px solid #f5c6cb;}}
    .section-title{{font-size:15px;font-weight:600;color:#333;margin:20px 0 10px;padding-bottom:8px;border-bottom:2px solid #eee;}}
    table{{width:100%;border-collapse:collapse;font-size:13px;}}
    th{{background:#f8f9fa;padding:8px;text-align:left;color:#666;font-weight:600;}}
    td{{padding:8px;border-bottom:1px solid #eee;}}
    .footer{{text-align:center;margin-top:30px;padding-top:20px;border-top:1px solid #eee;font-size:12px;color:#888;}}
    code{{font-family:monospace;font-size:12px;background:#f4f4f4;padding:2px 4px;border-radius:3px;}}
    </style>
    </head>
    <body>
    <div class="certificate">
    <div class="header">
    <h1 class="title">冷链温控证明</h1>
    <div class="subtitle">Cold Chain Temperature Control Certificate</div>
    </div>

    <div class="info-grid">
    <div class="info-item"><div class="info-label">证明编号</div><div class="info-value code">RPT-{data['trace_code']}</div></div>
    <div class="info-item"><div class="info-label">运单号</div><div class="info-value code">{data['waybill_id']}</div></div>
    <div class="info-item"><div class="info-label">溯源码</div><div class="info-value code">{data['trace_code']}</div></div>
    <div class="info-item"><div class="info-label">生成时间</div><div class="info-value">{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</div></div>
    </div>

    <div class="section-title">📦 货品信息</div>
    <div class="info-grid">
    <div class="info-item"><div class="info-label">货品名称</div><div class="info-value">{data['cargo_name']}</div></div>
    <div class="info-item"><div class="info-label">货物类别</div><div class="info-value">{data['cargo_category']}</div></div>
    <div class="info-item"><div class="info-label">数量</div><div class="info-value">{data['quantity']} {data['unit']}</div></div>
    <div class="info-item"><div class="info-label">高敏货物</div><div class="info-value">{'是' if data['is_high_sensitivity'] else '否'}</div></div>
    </div>

    <div class="section-title">📍 运输路线</div>
    <div class="info-grid">
    <div class="info-item"><div class="info-label">发货地</div><div class="info-value">{data['origin']}</div></div>
    <div class="info-item"><div class="info-label">收货地</div><div class="info-value">{data['destination']}</div></div>
    <div class="info-item"><div class="info-label">温度要求</div><div class="info-value">{data['temperature_requirement']}</div></div>
    <div class="info-item"><div class="info-label">记录总数</div><div class="info-value">{len(records)}条</div></div>
    </div>

    <div class="section-title">🌡️ 温控统计</div>
    <div class="temp-display">
    <div class="temp-value">{temp_summary.get('avg', 'N/A')}</div>
    <div class="temp-unit">平均温度 (℃)</div>
    </div>
    <div class="info-grid">
    <div class="info-item"><div class="info-label">温度范围</div><div class="info-value">{temp_summary.get('range', 'N/A')}</div></div>
    <div class="info-item"><div class="info-label">温控达标</div><div class="info-value" style="color:{'#28a745' if len(violations)==0 else '#dc3545'};font-weight:bold;">{'✅ 是' if len(violations)==0 else '❌ 否'}</div></div>
    <div class="info-item"><div class="info-label">异常次数</div><div class="info-value" style="color:{'#28a745' if len(violations)==0 else '#dc3545'};">{len(violations)}</div></div>
    <div class="info-item"><div class="info-label">运输时长</div><div class="info-value">{round(time_diff.total_seconds() / 3600, 1)}小时</div></div>
    </div>

    {stage_html}
    {violations_html}
    {blockchain_html}

    <div class="footer">
    <p>本证明由冷链追溯平台自动生成，数据来源于传感器实时采集</p>
    <p>经区块链加密存证，不可篡改</p>
    <p style="margin-top:10px;font-size:11px;">Certificate generated by Cold Chain Traceability Platform</p>
    </div>
    </div>
    </body>
    </html>
    """
    return HTMLResponse(html)


# ==================== 企业货主批量查询接口 ====================

@router.get("/my-orders")
async def get_my_orders(
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    user: dict = Depends(require_role("customer", "admin", "warehouse")),
):
    """
    企业货主查询名下订单列表
    """
    from .traceability import TRACE_DATA, TRACE_RECORDS, TRACE_CODE_MAP

    results = []
    shipper = user.get("sub", "")

    for trace_code, data in TRACE_DATA.items():
        if status and data.get("status") != status:
            continue

        record_ids = TRACE_CODE_MAP.get(trace_code, [])
        records = [r for r in TRACE_RECORDS if r["id"] in record_ids]
        records = sorted(records, key=lambda r: r.get("timestamp", ""))

        temperature_summary = generate_temperature_summary(records)
        violations = analyze_temperature_violations(records, data.get("temperature_requirement", ""))

        results.append({
            "waybill_id": data["waybill_id"],
            "trace_code": trace_code,
            "cargo_name": data["cargo_name"],
            "cargo_category": data["cargo_category"],
            "origin": data["origin"],
            "destination": data["destination"],
            "quantity": data["quantity"],
            "unit": data["unit"],
            "temperature_requirement": data["temperature_requirement"],
            "status": data.get("status", ""),
            "current_temperature": temperature_summary.get("avg", 0),
            "is_compliant": len(violations) == 0,
            "violations_count": len(violations),
            "total_records": len(records),
            "created_at": data.get("created_at", ""),
            "temperature_summary": temperature_summary,
        })

    results.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    return {
        "count": len(results),
        "total": len(results),
        "orders": results[offset:offset + limit],
    }


@router.get("/batch/certificates")
async def batch_download_certificates(
    waybill_ids: str = Query(..., description="运单号列表，逗号分隔"),
    format: str = "text",
    user: dict = Depends(require_role("customer", "admin", "warehouse")),
):
    """
    批量下载温控证明（企业货主专用）
    """
    ids = [id.strip() for id in waybill_ids.split(",") if id.strip()]
    certificates = []

    for waybill_id in ids:
        try:
            cert = await get_temperature_certificate(waybill_id, format, "full", user)
            certificates.append({
                "waybill_id": waybill_id,
                "certificate": cert.body.decode() if hasattr(cert, 'body') else str(cert),
            })
        except HTTPException:
            certificates.append({
                "waybill_id": waybill_id,
                "certificate": f"错误: 未找到运单 {waybill_id}",
            })
        except Exception as e:
            certificates.append({
                "waybill_id": waybill_id,
                "certificate": f"错误: {str(e)}",
            })

    if format == "json":
        return {"success": True, "count": len(certificates), "certificates": certificates}

    content = "\n\n" + "=" * 80 + "\n\n".join([f"【运单 {c['waybill_id']}】\n{c['certificate']}" for c in certificates])
    return PlainTextResponse(content)


# ==================== 区块链核验接口 ====================

@router.get("/verify")
async def verify_blockchain(
    waybill_id: str = Query(..., description="运单号"),
):
    """
    公开区块链核验接口（消费者/货主均可使用）
    验证运单数据的区块链存证完整性
    """
    from .traceability import (
        TRACE_DATA, TRACE_RECORDS, TRACE_CODE_MAP, WAYBILL_TRACE_MAP,
        BLOCKCHAIN_LEDGER, generate_block_hash, build_merkle_root,
    )

    result = get_trace_data_by_waybill(waybill_id)
    if not result:
        return {"error": "未找到该运单号"}

    trace_code = result["trace_code"]
    records = result["records"]

    block = None
    for b in BLOCKCHAIN_LEDGER:
        if b["data"].get("trace_code") == trace_code:
            block = b
            break

    if not block:
        return {
            "success": True,
            "waybill_id": result["waybill_id"],
            "trace_code": trace_code,
            "on_chain": False,
            "message": "该运单尚未完成区块链存证",
        }

    recomputed = generate_block_hash(block["data"])
    is_valid = recomputed == block["block_hash"]

    chain_intact = True
    if block["block_number"] > 1:
        prev_block = BLOCKCHAIN_LEDGER[block["block_number"] - 2]
        chain_intact = block["prev_hash"] == prev_block["block_hash"]

    current_merkle = build_merkle_root(records)
    merkle_valid = current_merkle == block.get("merkle_root", "")

    return {
        "success": True,
        "waybill_id": result["waybill_id"],
        "trace_code": trace_code,
        "on_chain": True,
        "verified": is_valid and chain_intact and merkle_valid,
        "block_hash_valid": is_valid,
        "chain_integrity": chain_intact,
        "merkle_integrity": merkle_valid,
        "block_number": block["block_number"],
        "block_hash": block["block_hash"],
        "prev_hash": block["prev_hash"],
        "merkle_root": block.get("merkle_root", ""),
        "current_merkle_root": current_merkle,
        "certified_at": block["created_at"],
        "message": "追溯数据区块链存证验证通过" if (is_valid and chain_intact and merkle_valid) else "区块链验证失败",
    }


# ==================== 小程序端简化接口 ====================

@router.get("/mini/query")
async def mini_query(
    code: str = Query(..., description="运单号或溯源码"),
):
    """
    小程序端简化查询接口
    支持运单号或溯源码查询，返回精简数据
    """
    from .traceability import TRACE_DATA, TRACE_RECORDS, TRACE_CODE_MAP, WAYBILL_TRACE_MAP

    trace_code = None
    waybill_id = None

    if code.startswith("CC"):
        for tc in TRACE_DATA:
            if tc.startswith(code) or code.startswith(tc):
                trace_code = tc
                break
    else:
        for wb_id, tc in WAYBILL_TRACE_MAP.items():
            if match_waybill_pattern(code, wb_id):
                trace_code = tc
                waybill_id = wb_id
                break

    if not trace_code or trace_code not in TRACE_DATA:
        return {"error": "未找到该运单记录"}

    data = TRACE_DATA[trace_code]
    record_ids = TRACE_CODE_MAP.get(trace_code, [])
    records = [r for r in TRACE_RECORDS if r["id"] in record_ids]
    records = sorted(records, key=lambda r: r.get("timestamp", ""))

    temperature_summary = generate_temperature_summary(records)
    violations = analyze_temperature_violations(records, data.get("temperature_requirement", ""))

    steps = []
    for stage in STAGES:
        stage_records = [r for r in records if r.get("stage") == stage["key"]]
        if stage_records:
            steps.append({
                "name": stage["name"],
                "icon": stage["icon"],
                "completed": True,
                "time": stage_records[-1].get("timestamp", "")[:16],
                "avg_temp": temperature_summary.get("avg", 0),
            })
        else:
            steps.append({
                "name": stage["name"],
                "icon": stage["icon"],
                "completed": False,
                "time": "",
                "avg_temp": 0,
            })

    return {
        "success": True,
        "waybill_id": data["waybill_id"],
        "trace_code": trace_code,
        "cargo_name": data["cargo_name"],
        "cargo_category": data["cargo_category"],
        "origin": data["origin"],
        "destination": data["destination"],
        "temperature_requirement": data["temperature_requirement"],
        "current_temperature": temperature_summary.get("avg", 0),
        "is_compliant": len(violations) == 0,
        "violations_count": len(violations),
        "status": data.get("status", ""),
        "steps": steps,
        "temperature_summary": temperature_summary,
    }


# ==================== 预警信息查询接口 ====================

@router.get("/alerts")
async def get_waybill_alerts(
    waybill_id: str = Query(..., description="运单号"),
):
    """
    查询运单相关的预警信息
    联动智能预警模块，展示运单全程异常告警记录
    """
    from ..services.alert_engine import alert_engine

    result = get_trace_data_by_waybill(waybill_id)
    if not result:
        return {"error": "未找到该运单号"}

    trace_code = result["trace_code"]
    waybill_id = result["waybill_id"]

    all_alerts = alert_engine.get_alert_history(limit=100)
    alerts = []
    for alert in all_alerts:
        alert_waybill = alert.get("waybill_id", "")
        alert_trace = alert.get("trace_code", "")
        alert_device = alert.get("device_id", "")
        
        if match_waybill_pattern(waybill_id, alert_waybill) or alert_trace == trace_code:
            alerts.append({
                "id": alert.get("alert_id", alert.get("id", "")),
                "type": alert.get("type", ""),
                "severity": alert.get("severity", ""),
                "message": alert.get("message", ""),
                "timestamp": alert.get("timestamp", ""),
                "status": alert.get("status", "active"),
                "location": alert.get("location", ""),
                "temperature": alert.get("temperature", 0),
                "threshold": alert.get("threshold", ""),
            })

    alerts.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    return {
        "success": True,
        "waybill_id": waybill_id,
        "trace_code": trace_code,
        "alert_count": len(alerts),
        "alerts": alerts,
    }


# ==================== 运单追踪接口（实时位置+温度） ====================

@router.get("/tracking")
async def get_order_tracking(
    waybill_id: str = Query(..., description="运单号"),
):
    """
    运单实时追踪接口
    返回运单当前状态、位置、温度等实时信息
    """
    result = get_trace_data_by_waybill(waybill_id)
    if not result:
        return {"error": "未找到该运单号"}

    waybill_id = result["waybill_id"]
    trace_code = result["trace_code"]
    data = result["data"]
    records = result["records"]

    latest_record = records[-1] if records else {}

    temperature_summary = generate_temperature_summary(records)
    violations = analyze_temperature_violations(records, data.get("temperature_requirement", ""))
    blockchain = get_blockchain_info(trace_code)

    return {
        "success": True,
        "waybill_id": waybill_id,
        "trace_code": trace_code,
        "cargo_name": data["cargo_name"],
        "status": data.get("status", ""),
        "current_location": latest_record.get("location", ""),
        "current_temperature": latest_record.get("temperature", 0),
        "current_humidity": latest_record.get("humidity", 0),
        "last_update": latest_record.get("timestamp", ""),
        "temperature_summary": temperature_summary,
        "is_compliant": len(violations) == 0,
        "violations_count": len(violations),
        "blockchain": blockchain,
    }
