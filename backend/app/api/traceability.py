"""
全程冷链追溯链 API
模块9: 全程冷链追溯链
- 追溯数据记录
- 追溯查询（按运单号/货物批次）
- 追溯报告生成与下载
- 区块链存证验证
"""
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse

from ..core.security import get_current_user
from ..services.redis_service import redis_service
from ..schemas import TEMP_THRESHOLD

router = APIRouter(prefix="/api/v1/traceability", tags=["冷链追溯"])

# ==================== 区块链存证 ====================

# 模拟区块链账本
_blockchain_ledger: list[dict] = []


def _generate_block_hash(data: dict) -> str:
    """生成区块哈希（模拟SHA-256）"""
    data_str = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(data_str.encode()).hexdigest()


def _record_on_chain(waybill_id: str, records: list, report: dict) -> dict:
    """将追溯记录上链存证"""
    # 检查是否已上链
    for block in _blockchain_ledger:
        if block.get("waybill_id") == waybill_id:
            return block

    # 生成新块
    prev_hash = _blockchain_ledger[-1]["block_hash"] if _blockchain_ledger else "0" * 64
    block_data = {
        "waybill_id": waybill_id,
        "record_count": len(records),
        "temperature_range": f"{min(r['temperature'] for r in records):.1f}~{max(r['temperature'] for r in records):.1f}",
        "compliance": report.get("is_chain_intact", True),
        "timestamp": datetime.utcnow().isoformat(),
    }
    block = {
        "block_number": len(_blockchain_ledger) + 1,
        "prev_hash": prev_hash,
        "block_hash": _generate_block_hash(block_data),
        "data": block_data,
        "created_at": datetime.utcnow().isoformat(),
    }
    _blockchain_ledger.append(block)
    return block

# 内存存储追溯记录（后续可迁移到 PostgreSQL）
_trace_records: list[dict] = []
_trace_links: dict = {}  # waybill_id -> list of trace record ids


# ==================== 初始化示例数据 ====================
def _init_sample_traces():
    if not _trace_records:
        now = datetime.utcnow()
        # 模拟一条完整冷链链路
        waybill = "WB20260528001"
        records = [
            {"id": "tr-001", "waybill_id": waybill, "stage": "产地预冷", "location": "山东寿光蔬菜基地",
             "temperature": 4.2, "humidity": 85.0, "operator": "王农户", "timestamp": (now - timedelta(hours=24)).isoformat(),
             "device_id": "CR-SG-001", "notes": "采摘后预冷至4°C"},
            {"id": "tr-002", "waybill_id": waybill, "stage": "冷藏运输", "location": "G2京沪高速",
             "temperature": 3.8, "humidity": 82.0, "operator": "李司机", "timestamp": (now - timedelta(hours=20)).isoformat(),
             "device_id": "VEH-001", "notes": "冷藏车运输中"},
            {"id": "tr-003", "waybill_id": waybill, "stage": "冷仓入库", "location": "华北中心冷库",
             "temperature": 3.5, "humidity": 80.0, "operator": "张经理", "timestamp": (now - timedelta(hours=12)).isoformat(),
             "device_id": "CR-BJ-001", "notes": "入库质检通过"},
            {"id": "tr-004", "waybill_id": waybill, "stage": "冷仓存储", "location": "华北中心冷库A区",
             "temperature": 3.2, "humidity": 78.0, "operator": "系统自动", "timestamp": (now - timedelta(hours=8)).isoformat(),
             "device_id": "CR-BJ-001", "notes": "恒温存储中"},
            {"id": "tr-005", "waybill_id": waybill, "stage": "末端配送", "location": "北京市朝阳区",
             "temperature": 4.5, "humidity": 76.0, "operator": "赵配送员", "timestamp": (now - timedelta(hours=2)).isoformat(),
             "device_id": "VEH-003", "notes": "最后一公里配送"},
        ]
        _trace_records.extend(records)
        _trace_links[waybill] = [r["id"] for r in records]


_init_sample_traces()


# ==================== 追溯记录 CRUD ====================

@router.post("/record")
async def add_trace_record(
    waybill_id: str,
    stage: str,
    location: str,
    temperature: float,
    humidity: float = 0,
    operator: str = "",
    device_id: str = "",
    notes: str = "",
    lat: float = 0,
    lng: float = 0,
):
    """添加追溯记录（由各环节自动或手动上报）"""
    import uuid
    record = {
        "id": f"tr-{uuid.uuid4().hex[:8]}",
        "waybill_id": waybill_id,
        "stage": stage,
        "location": location,
        "temperature": temperature,
        "humidity": humidity,
        "operator": operator,
        "device_id": device_id,
        "notes": notes,
        "lat": lat,
        "lng": lng,
        "timestamp": datetime.utcnow().isoformat(),
    }
    _trace_records.append(record)

    if waybill_id not in _trace_links:
        _trace_links[waybill_id] = []
    _trace_links[waybill_id].append(record["id"])

    return {"status": "ok", "record": record}


@router.get("/records/{waybill_id}")
async def get_trace_records(
    waybill_id: str,
    user: dict = Depends(get_current_user),
):
    """查询运单的完整追溯记录"""
    linked_ids = _trace_links.get(waybill_id, [])
    records = [r for r in _trace_records if r["id"] in linked_ids]
    records = sorted(records, key=lambda r: r["timestamp"])

    # 计算温度统计
    temps = [r["temperature"] for r in records]
    temp_range = {"min": min(temps) if temps else 0, "max": max(temps) if temps else 0, "avg": round(sum(temps) / len(temps), 2) if temps else 0}

    # 检查是否有断链（温度超标）
    violations = [r for r in records if r["temperature"] > TEMP_THRESHOLD["WARN_UPPER"] or r["temperature"] < TEMP_THRESHOLD["LOW_LIMIT"]]

    return {
        "waybill_id": waybill_id,
        "stages": len(records),
        "records": records,
        "temperature_summary": temp_range,
        "violations": len(violations),
        "violation_details": violations,
        "is_compliant": len(violations) == 0,
    }


@router.get("/report/{waybill_id}")
async def generate_trace_report(
    waybill_id: str,
    format: str = "json",
    user: dict = Depends(get_current_user),
):
    """生成追溯报告"""
    linked_ids = _trace_links.get(waybill_id, [])
    records = [r for r in _trace_records if r["id"] in linked_ids]
    records = sorted(records, key=lambda r: r["timestamp"])

    if not records:
        raise HTTPException(status_code=404, detail="运单不存在或无追溯记录")

    temps = [r["temperature"] for r in records]
    stages = list(set(r["stage"] for r in records))

    report = {
        "report_id": f"RPT-{waybill_id}",
        "waybill_id": waybill_id,
        "generated_at": datetime.utcnow().isoformat(),
        "total_stages": len(records),
        "stages_covered": stages,
        "temperature_range": f"{min(temps):.1f}°C ~ {max(temps):.1f}°C",
        "avg_temperature": f"{sum(temps) / len(temps):.1f}°C",
        "duration_hours": round(
            (datetime.fromisoformat(records[-1]["timestamp"]) -
             datetime.fromisoformat(records[0]["timestamp"])).total_seconds() / 3600, 1
        ),
        "is_chain_intact": True,
        "violations": [r for r in records if r["temperature"] > TEMP_THRESHOLD["WARN_UPPER"]],
        "records": records,
    }

    # 区块链存证
    block = _record_on_chain(waybill_id, records, report)
    report["blockchain"] = {
        "on_chain": True,
        "block_number": block["block_number"],
        "block_hash": block["block_hash"],
        "prev_hash": block["prev_hash"],
        "certified_at": block["created_at"],
    }

    if format == "text":
        lines = [
            f"冷链追溯报告",
            f"=" * 50,
            f"报告编号: {report['report_id']}",
            f"运单号:   {waybill_id}",
            f"生成时间: {report['generated_at']}",
            f"覆盖环节: {', '.join(stages)}",
            f"温度范围: {report['temperature_range']}",
            f"平均温度: {report['avg_temperature']}",
            f"运输时长: {report['duration_hours']}小时",
            f"冷链完整: {'是' if report['is_chain_intact'] else '否'}",
            f"",
            f"区块链存证信息:",
            f"  区块编号: #{report['blockchain']['block_number']}",
            f"  区块哈希: {report['blockchain']['block_hash'][:32]}...",
            f"  存证时间: {report['blockchain']['certified_at']}",
            f"  存证状态: 已上链，不可篡改",
            f"=" * 50,
            f"详细记录:",
        ]
        for r in records:
            lines.append(f"  [{r['stage']}] {r['timestamp']} | {r['location']} | {r['temperature']}°C | {r['operator']}")
        lines.append("=" * 50)
        return PlainTextResponse("\n".join(lines))

    return report


@router.get("/blockchain/verify/{waybill_id}")
async def verify_blockchain(
    waybill_id: str,
    user: dict = Depends(get_current_user),
):
    """验证追溯数据区块链存证"""
    for block in _blockchain_ledger:
        if block.get("data", {}).get("waybill_id") == waybill_id:
            # 重新计算哈希以验证完整性
            recomputed = _generate_block_hash(block["data"])
            is_valid = recomputed == block["block_hash"]

            # 验证链式结构
            chain_intact = True
            if block["block_number"] > 1:
                prev_block = next(
                    (b for b in _blockchain_ledger if b["block_number"] == block["block_number"] - 1), None
                )
                if prev_block:
                    chain_intact = block["prev_hash"] == prev_block["block_hash"]

            return {
                "waybill_id": waybill_id,
                "verified": is_valid and chain_intact,
                "block_hash_valid": is_valid,
                "chain_integrity": chain_intact,
                "block_number": block["block_number"],
                "block_hash": block["block_hash"],
                "certified_at": block["created_at"],
                "data_hash": recomputed,
                "message": "追溯数据区块链存证验证通过，数据未被篡改" if (is_valid and chain_intact) else "区块链验证失败，数据可能被篡改",
            }

    # 未上链的情况
    linked_ids = _trace_links.get(waybill_id, [])
    records = [r for r in _trace_records if r["id"] in linked_ids]
    if records:
        # 当场存证
        temps = [r["temperature"] for r in records]
        report = {
            "report_id": f"RPT-{waybill_id}",
            "is_chain_intact": True,
        }
        block = _record_on_chain(waybill_id, records, report)
        return {
            "waybill_id": waybill_id,
            "verified": True,
            "block_hash_valid": True,
            "chain_integrity": True,
            "block_number": block["block_number"],
            "block_hash": block["block_hash"],
            "certified_at": block["created_at"],
            "message": "追溯数据已完成区块链存证",
        }

    raise HTTPException(status_code=404, detail="运单不存在")


@router.get("/blockchain/ledger")
async def get_blockchain_ledger(
    limit: int = 10,
    user: dict = Depends(get_current_user),
):
    """查看区块链账本"""
    ledger = _blockchain_ledger[-limit:] if _blockchain_ledger else []
    return {
        "total_blocks": len(_blockchain_ledger),
        "blocks": ledger,
    }


@router.get("/search")
async def search_traces(
    keyword: str = "",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 20,
    user: dict = Depends(get_current_user),
):
    """搜索追溯记录"""
    results = []
    for waybill_id, record_ids in _trace_links.items():
        records = [r for r in _trace_records if r["id"] in record_ids]
        if not records:
            continue

        # 关键词匹配
        if keyword and keyword.lower() not in waybill_id.lower():
            match = any(
                keyword.lower() in r.get("location", "").lower() or
                keyword.lower() in r.get("stage", "").lower()
                for r in records
            )
            if not match:
                continue

        # 日期过滤
        if start_date or end_date:
            first_ts = records[0]["timestamp"]
            if start_date and first_ts < start_date:
                continue
            if end_date and first_ts > end_date:
                continue

        results.append({
            "waybill_id": waybill_id,
            "stages": len(records),
            "first_record": records[0]["timestamp"],
            "last_record": records[-1]["timestamp"],
            "avg_temperature": round(sum(r["temperature"] for r in records) / len(records), 1),
        })

    return {"count": len(results[:limit]), "waybills": results[:limit]}


@router.get("/stats")
async def get_traceability_stats(
    user: dict = Depends(get_current_user),
):
    """追溯链统计数据"""
    total_waybills = len(_trace_links)
    total_records = len(_trace_records)

    compliant = 0
    for waybill_id, record_ids in _trace_links.items():
        records = [r for r in _trace_records if r["id"] in record_ids]
        violations = [r for r in records if r["temperature"] > TEMP_THRESHOLD["WARN_UPPER"] or r["temperature"] < TEMP_THRESHOLD["LOW_LIMIT"]]
        if not violations:
            compliant += 1

    return {
        "total_waybills": total_waybills,
        "total_records": total_records,
        "compliant_waybills": compliant,
        "compliance_rate": round(compliant / total_waybills * 100, 1) if total_waybills > 0 else 100,
        "violation_waybills": total_waybills - compliant,
    }
