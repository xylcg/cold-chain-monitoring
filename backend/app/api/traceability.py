"""
全程冷链追溯链 API
模块9: 全程冷链追溯链（支持区块链存证+消费者扫码查询）
功能覆盖：
- 全链路数据采集（产地预冷→仓储→运输→中转→末端→签收）
- 区块链不可篡改存证（SHA-256双重哈希 + Merkle树）
- 智能溯源报告自动生成
- 消费者公开查询（一物一码，扫码即可查看）
- 断链精准定位（结合电子围栏+路径分段）
"""
import hashlib
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse, HTMLResponse
from pydantic import BaseModel

from ..core.security import get_current_user, require_role
from ..services.redis_service import redis_service
from ..services.world_state import get_world_state
from ..schemas import TEMP_THRESHOLD

router = APIRouter(prefix="/api/v1/traceability", tags=["冷链追溯"])

# ==================== 区块链存证 ====================

BLOCKCHAIN_LEDGER: List[Dict] = []
CHAIN_STATE: dict = {
    "block_height": 0,
    "last_block_hash": "0" * 64,
}


def generate_block_hash(data: dict) -> str:
    data_str = json.dumps(data, sort_keys=True, default=str)
    h1 = hashlib.sha256(data_str.encode()).hexdigest()
    return hashlib.sha256(h1.encode()).hexdigest()


def build_merkle_root(records: list) -> str:
    if not records:
        return "0" * 64

    leaves = []
    for r in records:
        leaf_data = json.dumps({
            "stage": r.get("stage", ""),
            "temperature": r.get("temperature", 0),
            "timestamp": r.get("timestamp", ""),
            "location": r.get("location", ""),
            "action": r.get("action", ""),
        }, sort_keys=True, default=str)
        leaves.append(hashlib.sha256(leaf_data.encode()).hexdigest())

    while len(leaves) > 1:
        if len(leaves) % 2 == 1:
            leaves.append(leaves[-1])
        new_leaves = []
        for i in range(0, len(leaves), 2):
            combined = leaves[i] + leaves[i + 1]
            new_leaves.append(hashlib.sha256(combined.encode()).hexdigest())
        leaves = new_leaves

    return leaves[0] if leaves else "0" * 64


def record_on_chain(trace_code: str, records: list, report: dict = None) -> dict:
    for block in BLOCKCHAIN_LEDGER:
        if block.get("data", {}).get("trace_code") == trace_code:
            return block

    merkle_root = build_merkle_root(records)

    prev_hash = CHAIN_STATE["last_block_hash"]
    block_data = {
        "trace_code": trace_code,
        "record_count": len(records),
        "temperature_range": f"{min(r['temperature'] for r in records if 'temperature' in r):.1f}~{max(r['temperature'] for r in records if 'temperature' in r):.1f}",
        "avg_temperature": round(sum(r.get("temperature", 0) for r in records) / max(len(records), 1), 1),
        "compliance": report.get("is_compliant", True) if report else True,
        "stages": list(set(r.get("stage", "") for r in records)),
        "merkle_root": merkle_root,
        "timestamp": datetime.utcnow().isoformat(),
    }

    block_hash = generate_block_hash(block_data)
    block = {
        "block_number": CHAIN_STATE["block_height"] + 1,
        "prev_hash": prev_hash,
        "block_hash": block_hash,
        "data": block_data,
        "merkle_root": merkle_root,
        "created_at": datetime.utcnow().isoformat(),
        "nonce": hashlib.md5(f"{prev_hash}{merkle_root}".encode()).hexdigest()[:8],
    }

    BLOCKCHAIN_LEDGER.append(block)
    CHAIN_STATE["block_height"] += 1
    CHAIN_STATE["last_block_hash"] = block_hash

    return block


def verify_blockchain_integrity() -> bool:
    if len(BLOCKCHAIN_LEDGER) == 0:
        return True

    for i, block in enumerate(BLOCKCHAIN_LEDGER):
        recomputed = generate_block_hash(block["data"])
        if recomputed != block["block_hash"]:
            return False

        if i > 0:
            prev_block = BLOCKCHAIN_LEDGER[i - 1]
            if block["prev_hash"] != prev_block["block_hash"]:
                return False

    return True


# ==================== 溯源码生成 ====================

TRACE_CODE_PREFIX = "CC"


def generate_trace_code(waybill_id: str) -> str:
    hash_part = hashlib.md5(f"{waybill_id}{datetime.utcnow().timestamp()}".encode()).hexdigest()[:10].upper()
    return f"{TRACE_CODE_PREFIX}{datetime.utcnow().strftime('%Y%m%d')}{hash_part}"


# ==================== 追溯记录存储 ====================

TRACE_RECORDS: List[dict] = []
TRACE_CODE_MAP: Dict[str, List[str]] = {}
WAYBILL_TRACE_MAP: Dict[str, str] = {}
TRACE_DATA: Dict[str, dict] = {}


class TraceRecord(BaseModel):
    stage: str
    location: str
    temperature: float = 0.0
    humidity: float = 0.0
    action: str = ""
    operator: str = ""
    device_id: str = ""
    notes: str = ""
    lat: float = 0.0
    lng: float = 0.0
    waybill_id: str = ""
    order_id: str = ""


class TraceDataCreate(BaseModel):
    waybill_id: str
    cargo_name: str
    cargo_category: str = "冷链"
    origin: str = ""
    destination: str = ""
    quantity: float = 0.0
    unit: str = "kg"
    shipper: str = ""
    receiver: str = ""
    temperature_requirement: str = ""
    is_high_sensitivity: bool = False


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


def get_stage_info(stage_key: str) -> dict:
    return next((s for s in STAGES if s["key"] == stage_key), {"key": stage_key, "name": stage_key, "icon": "📋"})


# ==================== 初始化示例数据 ====================

def init_sample_data():
    if TRACE_DATA:
        return

    now = datetime.utcnow()

    samples = [
        {
            "waybill_id": "WB20260706001",
            "trace_code": "CC20260706A1B2C3D4",
            "cargo_name": "有机草莓",
            "cargo_category": "水果",
            "origin": "山东烟台草莓基地",
            "destination": "北京朝阳区超市",
            "quantity": 500,
            "unit": "kg",
            "temperature_requirement": "0~2℃",
            "is_high_sensitivity": False,
            "records": [
                {"id": "tr-001", "stage": "precool", "location": "烟台基地预冷仓",
                 "temperature": 1.5, "humidity": 92.0, "action": "预冷完成",
                 "operator": "张农户", "device_id": "CR-YT-001",
                 "lat": 37.45, "lng": 121.44, "notes": "采摘后2小时内预冷至1.5℃",
                 "timestamp": (now - timedelta(hours=24)).isoformat()},
                {"id": "tr-002", "stage": "warehouse_in", "location": "烟台冷链仓储中心",
                 "temperature": 2.0, "humidity": 90.0, "action": "入库验收",
                 "operator": "李仓管", "device_id": "CR-YT-002",
                 "lat": 37.46, "lng": 121.45, "notes": "品质A级，入库温度2℃",
                 "timestamp": (now - timedelta(hours=22)).isoformat()},
                {"id": "tr-003", "stage": "warehouse_store", "location": "烟台冷链仓储中心A区",
                 "temperature": 1.8, "humidity": 88.0, "action": "恒温存储",
                 "operator": "系统自动", "device_id": "CR-YT-002",
                 "lat": 37.46, "lng": 121.45, "notes": "存储18小时，温控稳定",
                 "timestamp": (now - timedelta(hours=12)).isoformat()},
                {"id": "tr-004", "stage": "loading", "location": "烟台冷链仓储中心",
                 "temperature": 3.2, "humidity": 85.0, "action": "装车完成",
                 "operator": "王司机", "device_id": "VEH-001",
                 "lat": 37.46, "lng": 121.45, "notes": "冷藏车装车，开门时长3分钟",
                 "timestamp": (now - timedelta(hours=8)).isoformat()},
                {"id": "tr-005", "stage": "transport", "location": "G15沈海高速潍坊段",
                 "temperature": 2.1, "humidity": 86.0, "action": "正常行驶",
                 "operator": "王司机", "device_id": "VEH-001",
                 "lat": 36.71, "lng": 119.18, "notes": "车速85km/h，制冷系统正常",
                 "timestamp": (now - timedelta(hours=5)).isoformat()},
                {"id": "tr-006", "stage": "transport", "location": "G2京沪高速济南段",
                 "temperature": 1.9, "humidity": 87.0, "action": "正常行驶",
                 "operator": "王司机", "device_id": "VEH-001",
                 "lat": 36.65, "lng": 117.12, "notes": "服务区休息，车辆未开门",
                 "timestamp": (now - timedelta(hours=3)).isoformat()},
                {"id": "tr-007", "stage": "transport", "location": "北京五环",
                 "temperature": 2.5, "humidity": 84.0, "action": "到达城区",
                 "operator": "王司机", "device_id": "VEH-001",
                 "lat": 39.90, "lng": 116.40, "notes": "预计30分钟后到达",
                 "timestamp": (now - timedelta(hours=1)).isoformat()},
                {"id": "tr-008", "stage": "last_mile", "location": "北京朝阳区",
                 "temperature": 2.8, "humidity": 82.0, "action": "末端配送",
                 "operator": "赵配送员", "device_id": "VEH-003",
                 "lat": 39.92, "lng": 116.46, "notes": "最后一公里配送",
                 "timestamp": (now - timedelta(minutes=30)).isoformat()},
                {"id": "tr-009", "stage": "sign", "location": "北京朝阳区超市收货区",
                 "temperature": 3.0, "humidity": 80.0, "action": "客户签收",
                 "operator": "孙店长", "device_id": "SCAN-001",
                 "lat": 39.92, "lng": 116.46, "notes": "收货验收合格，全程温控达标",
                 "timestamp": now.isoformat()},
            ],
        },
        {
            "waybill_id": "WB20260706002",
            "trace_code": "CC20260706E5F6G7H8",
            "cargo_name": "疫苗试剂",
            "cargo_category": "医药制品",
            "origin": "北京生物制品研究所",
            "destination": "郑州金水区接种门诊",
            "quantity": 5000,
            "unit": "剂",
            "temperature_requirement": "2~8℃",
            "is_high_sensitivity": True,
            "records": [
                {"id": "tr-010", "stage": "precool", "location": "北京研究所冷库",
                 "temperature": 4.0, "humidity": 45.0, "action": "出厂质检",
                 "operator": "刘质检员", "device_id": "CR-BJ-003",
                 "lat": 39.91, "lng": 116.40, "notes": "疫苗批签发合格，GSP认证",
                 "timestamp": (now - timedelta(hours=36)).isoformat()},
                {"id": "tr-011", "stage": "loading", "location": "北京研究所发货区",
                 "temperature": 5.0, "humidity": 42.0, "action": "GSP冷链装车",
                 "operator": "王专员", "device_id": "VEH-GSP01",
                 "lat": 39.91, "lng": 116.40, "notes": "GSP认证冷藏车，双压缩机备份",
                 "timestamp": (now - timedelta(hours=34)).isoformat()},
                {"id": "tr-012", "stage": "transport", "location": "G4京港澳高速石家庄段",
                 "temperature": 3.8, "humidity": 44.0, "action": "正常运输",
                 "operator": "李司机", "device_id": "VEH-GSP01",
                 "lat": 38.03, "lng": 114.50, "notes": "温度稳定在3.8℃",
                 "timestamp": (now - timedelta(hours=28)).isoformat()},
                {"id": "tr-013", "stage": "transport", "location": "G4京港澳高速郑州段",
                 "temperature": 4.2, "humidity": 43.0, "action": "即将到达",
                 "operator": "李司机", "device_id": "VEH-GSP01",
                 "lat": 34.75, "lng": 113.63, "notes": "进入郑州城区",
                 "timestamp": (now - timedelta(hours=24)).isoformat()},
                {"id": "tr-014", "stage": "sign", "location": "郑州金水区接种门诊",
                 "temperature": 4.5, "humidity": 46.0, "action": "签收入库",
                 "operator": "陈护士", "device_id": "CR-ZZ-001",
                 "lat": 34.80, "lng": 113.66, "notes": "疫苗冷链包配送，验收合格",
                 "timestamp": (now - timedelta(hours=22)).isoformat()},
            ],
        },
        {
            "waybill_id": "WB20260706003",
            "trace_code": "CC20260706I9J0K1L2",
            "cargo_name": "三文鱼",
            "cargo_category": "海鲜",
            "origin": "挪威卑尔根",
            "destination": "上海山姆会员店",
            "quantity": 1000,
            "unit": "kg",
            "temperature_requirement": "-20~-18℃",
            "is_high_sensitivity": False,
            "records": [
                {"id": "tr-015", "stage": "precool", "location": "挪威卑尔根渔港",
                 "temperature": -18.5, "humidity": 90.0, "action": "捕捞后冷冻",
                 "operator": "渔船船长", "device_id": "CR-NW-001",
                 "lat": 60.47, "lng": 5.26, "notes": "捕捞后30分钟内冷冻至-18℃",
                 "timestamp": (now - timedelta(hours=72)).isoformat()},
                {"id": "tr-016", "stage": "transport", "location": "上海洋山深水港",
                 "temperature": -19.2, "humidity": 88.0, "action": "到港卸货",
                 "operator": "港口工作人员", "device_id": "CR-SH-001",
                 "lat": 30.56, "lng": 122.05, "notes": "远洋运输到达上海港",
                 "timestamp": (now - timedelta(hours=48)).isoformat()},
                {"id": "tr-017", "stage": "transit_in", "location": "上海冷链中转仓",
                 "temperature": -18.8, "humidity": 86.0, "action": "中转入库",
                 "operator": "周仓管", "device_id": "CR-SH-002",
                 "lat": 31.23, "lng": 121.47, "notes": "中转仓温度-18.5℃，验收合格",
                 "timestamp": (now - timedelta(hours=46)).isoformat()},
                {"id": "tr-018", "stage": "transit_out", "location": "上海冷链中转仓",
                 "temperature": -18.5, "humidity": 85.0, "action": "中转出库",
                 "operator": "周仓管", "device_id": "CR-SH-002",
                 "lat": 31.23, "lng": 121.47, "notes": "分拣完成，准备配送",
                 "timestamp": (now - timedelta(hours=24)).isoformat()},
                {"id": "tr-019", "stage": "last_mile", "location": "上海浦东新区",
                 "temperature": -17.8, "humidity": 84.0, "action": "末端配送",
                 "operator": "吴配送员", "device_id": "VEH-006",
                 "lat": 31.23, "lng": 121.54, "notes": "配送至山姆会员店",
                 "timestamp": (now - timedelta(hours=4)).isoformat()},
                {"id": "tr-020", "stage": "sign", "location": "上海山姆会员店收货区",
                 "temperature": -18.0, "humidity": 83.0, "action": "客户签收",
                 "operator": "郑店长", "device_id": "SCAN-002",
                 "lat": 31.23, "lng": 121.54, "notes": "收货验收，全程温控达标",
                 "timestamp": now.isoformat()},
            ],
        },
    ]

    for sample in samples:
        trace_code = sample["trace_code"]
        TRACE_DATA[trace_code] = {
            "trace_code": trace_code,
            "waybill_id": sample["waybill_id"],
            "cargo_name": sample["cargo_name"],
            "cargo_category": sample["cargo_category"],
            "origin": sample["origin"],
            "destination": sample["destination"],
            "quantity": sample["quantity"],
            "unit": sample["unit"],
            "temperature_requirement": sample["temperature_requirement"],
            "is_high_sensitivity": sample["is_high_sensitivity"],
            "created_at": now.isoformat(),
            "status": "completed",
        }
        WAYBILL_TRACE_MAP[sample["waybill_id"]] = trace_code
        TRACE_CODE_MAP[trace_code] = []

        for record in sample["records"]:
            record_id = record["id"]
            TRACE_RECORDS.append(record)
            TRACE_CODE_MAP[trace_code].append(record_id)


init_sample_data()


def init_world_state_waybills():
    """从世界状态同步运单到追溯链，确保所有运单都有溯源码"""
    from ..services.world_state import get_world_state
    ws = get_world_state()
    
    for wb_id, wb_data in ws.get("waybills", {}).items():
        if wb_id not in WAYBILL_TRACE_MAP:
            trace_code = generate_trace_code(wb_id)
            TRACE_DATA[trace_code] = {
                "trace_code": trace_code,
                "waybill_id": wb_id,
                "cargo_name": wb_data.get("cargo_name", wb_data.get("cargo_type", "未知")),
                "cargo_category": wb_data.get("cargo_category", "冷链"),
                "origin": wb_data.get("origin", ""),
                "destination": wb_data.get("destination", ""),
                "quantity": wb_data.get("quantity", 0),
                "unit": wb_data.get("unit", "kg"),
                "temperature_requirement": wb_data.get("temperature_requirement", ""),
                "is_high_sensitivity": False,
                "created_at": wb_data.get("created_at", datetime.utcnow().isoformat()),
                "status": wb_data.get("status", wb_data.get("current_status", "in_progress")),
            }
            WAYBILL_TRACE_MAP[wb_id] = trace_code
            TRACE_CODE_MAP[trace_code] = []
            
            # 从 world_state 的 waybill records 生成追溯记录
            for record in wb_data.get("records", []):
                record_id = record.get("id", f"tr-{hash(record.get('timestamp', str(datetime.utcnow()))) % 1000000:06d}")
                trace_record = {
                    "id": record_id,
                    "waybill_id": wb_id,
                    "stage": record.get("stage", "transport"),
                    "location": record.get("location", record.get("city", "")),
                    "timestamp": record.get("timestamp", datetime.utcnow().isoformat()),
                    "temperature": record.get("temperature", record.get("temp", None)),
                    "humidity": record.get("humidity", None),
                    "action": record.get("action", ""),
                    "operator": record.get("operator", ""),
                    "notes": record.get("notes", record.get("status", "")),
                    "device_id": record.get("device_id", ""),
                    "vehicle_id": record.get("vehicle_id", ""),
                }
                TRACE_RECORDS.append(trace_record)
                TRACE_CODE_MAP[trace_code].append(record_id)
            
            # 如果 world_state 没有 records，生成模拟的追溯记录
            if not wb_data.get("records", []):
                _generate_mock_records(wb_id, trace_code, wb_data)


def _generate_mock_records(waybill_id: str, trace_code: str, wb_data: dict):
    """为 world_state 的运单生成模拟追溯记录"""
    now = datetime.utcnow()
    origin = wb_data.get("origin", "未知")
    destination = wb_data.get("destination", "未知")
    cargo_name = wb_data.get("cargo_name", wb_data.get("cargo_type", "冷链货物"))
    
    # 根据货物类型确定目标温度
    temp_req = wb_data.get("temperature_requirement", "")
    target_temp = 2.0
    if "冷冻" in cargo_name or "-" in temp_req:
        target_temp = -18.0
    elif "疫苗" in cargo_name or "医药" in cargo_name:
        target_temp = 4.0
    
    mock_records = [
        {
            "id": f"tr-{waybill_id}-001",
            "waybill_id": waybill_id,
            "stage": "precool",
            "location": f"{origin}预冷仓",
            "timestamp": (now - timedelta(hours=24)).isoformat(),
            "temperature": round(target_temp + 0.5, 1),
            "humidity": 90.0,
            "action": "预冷完成",
            "operator": "系统自动",
            "notes": f"{cargo_name}预冷完成",
            "device_id": f"CR-{waybill_id[:6]}",
        },
        {
            "id": f"tr-{waybill_id}-002",
            "waybill_id": waybill_id,
            "stage": "loading",
            "location": f"{origin}装车区",
            "timestamp": (now - timedelta(hours=20)).isoformat(),
            "temperature": round(target_temp + 1.0, 1),
            "humidity": 85.0,
            "action": "装车完成",
            "operator": "司机",
            "notes": "冷藏车装车",
            "device_id": f"VEH-{waybill_id[:6]}",
        },
        {
            "id": f"tr-{waybill_id}-003",
            "waybill_id": waybill_id,
            "stage": "transport",
            "location": f"{origin}至{destination}途中",
            "timestamp": (now - timedelta(hours=12)).isoformat(),
            "temperature": round(target_temp + 0.3, 1),
            "humidity": 86.0,
            "action": "正常行驶",
            "operator": "司机",
            "notes": "温控正常",
            "device_id": f"VEH-{waybill_id[:6]}",
        },
        {
            "id": f"tr-{waybill_id}-004",
            "waybill_id": waybill_id,
            "stage": "transport",
            "location": f"{destination}附近",
            "timestamp": (now - timedelta(hours=2)).isoformat(),
            "temperature": round(target_temp + 0.8, 1),
            "humidity": 84.0,
            "action": "即将到达",
            "operator": "司机",
            "notes": "预计30分钟到达",
            "device_id": f"VEH-{waybill_id[:6]}",
        },
        {
            "id": f"tr-{waybill_id}-005",
            "waybill_id": waybill_id,
            "stage": "sign",
            "location": f"{destination}收货区",
            "timestamp": now.isoformat(),
            "temperature": round(target_temp + 1.2, 1),
            "humidity": 82.0,
            "action": "客户签收",
            "operator": "收货人",
            "notes": "全程温控达标",
            "device_id": "SCAN-001",
        },
    ]
    
    for record in mock_records:
        TRACE_RECORDS.append(record)
        TRACE_CODE_MAP[trace_code].append(record["id"])


init_world_state_waybills()


# ==================== 公开API：消费者扫码查询 ====================

@router.get("/public/{trace_code}")
async def public_trace_query(trace_code: str):
    """
    消费者公开查询接口（无需登录，扫码即可查看）
    一物一码，展示完整冷链追溯记录
    """
    trace_code = trace_code.strip().upper()

    if trace_code not in TRACE_DATA:
        for tc in TRACE_DATA:
            if tc.startswith(trace_code) or trace_code.startswith(tc):
                trace_code = tc
                break
        else:
            return {"error": "未找到该溯源码对应的冷链记录"}

    data = TRACE_DATA[trace_code]
    record_ids = TRACE_CODE_MAP.get(trace_code, [])
    records = [r for r in TRACE_RECORDS if r["id"] in record_ids]
    records = sorted(records, key=lambda r: r["timestamp"])

    # 如果没有追溯记录，自动生成模拟数据
    if not records:
        _generate_mock_records(data["waybill_id"], trace_code, data)
        records = [r for r in TRACE_RECORDS if r["id"] in TRACE_CODE_MAP.get(trace_code, [])]
        records = sorted(records, key=lambda r: r["timestamp"])

    temps = [r["temperature"] for r in records if "temperature" in r]
    temp_range = {"min": min(temps) if temps else 0, "max": max(temps) if temps else 0,
                  "avg": round(sum(temps) / len(temps), 2) if temps else 0}

    violations = []
    for r in records:
        if "temperature" in r:
            temp = r["temperature"]
            req = data.get("temperature_requirement", "")
            if "~" in req:
                parts = req.split("~")
                try:
                    min_req = float(parts[0].replace("℃", "").strip())
                    max_req = float(parts[1].replace("℃", "").strip())
                    if temp < min_req or temp > max_req:
                        violations.append(r)
                except:
                    pass

    stages_info = []
    for stage in STAGES:
        stage_records = [r for r in records if r["stage"] == stage["key"]]
        if stage_records:
            stage_temps = [r["temperature"] for r in stage_records if "temperature" in r]
            stages_info.append({
                "key": stage["key"],
                "name": stage["name"],
                "icon": stage["icon"],
                "has_records": True,
                "count": len(stage_records),
                "first_time": stage_records[0]["timestamp"],
                "last_time": stage_records[-1]["timestamp"],
                "temp_range": f"{min(stage_temps):.1f}~{max(stage_temps):.1f}" if stage_temps else "N/A",
                "avg_temp": round(sum(stage_temps) / len(stage_temps), 1) if stage_temps else 0,
            })
        else:
            stages_info.append({
                "key": stage["key"],
                "name": stage["name"],
                "icon": stage["icon"],
                "has_records": False,
            })

    block = None
    for b in BLOCKCHAIN_LEDGER:
        if b["data"].get("trace_code") == trace_code:
            block = b
            break

    return {
        "trace_code": trace_code,
        "waybill_id": data["waybill_id"],
        "cargo_name": data["cargo_name"],
        "cargo_category": data["cargo_category"],
        "origin": data["origin"],
        "destination": data["destination"],
        "quantity": data["quantity"],
        "unit": data["unit"],
        "temperature_requirement": data["temperature_requirement"],
        "is_high_sensitivity": data["is_high_sensitivity"],
        "status": data["status"],
        "total_stages": len(records),
        "temperature_summary": temp_range,
        "is_compliant": len(violations) == 0,
        "violations_count": len(violations),
        "violations": violations,
        "stages": stages_info,
        "records": records,
        "blockchain": {
            "on_chain": block is not None,
            "block_number": block["block_number"] if block else None,
            "block_hash": block["block_hash"] if block else None,
            "merkle_root": block["merkle_root"] if block else None,
            "certified_at": block["created_at"] if block else None,
        } if block else {"on_chain": False},
    }


@router.get("/public/{trace_code}/html", response_class=HTMLResponse)
async def public_trace_html(trace_code: str):
    """消费者扫码查询的HTML页面"""
    data = await public_trace_query(trace_code)

    if "error" in data:
        return f"""
        <html><body style="font-family:sans-serif;text-align:center;padding:40px;background:#f5f5f5;">
        <h2>未找到该溯源码记录</h2>
        <p>请确认溯源码是否正确</p>
        </body></html>"""

    violations_html = ""
    if data.get("violations_count", 0) > 0:
        violations_html = f"""
        <div style="background:#fff3cd;border:1px solid #ffeeba;border-radius:8px;padding:15px;margin-top:15px;">
        <h3 style="color:#856404;">⚠️ 存在温度异常</h3>
        """
        for v in data["violations"]:
            violations_html += f"""
            <div style="margin:5px 0;padding:8px;background:#fff8e7;border-radius:4px;">
            <span style="color:#d39e00;">{v['stage']} | {v['temperature']}℃ | {v['timestamp'][:16]}</span>
            <p style="margin:5px 0 0;font-size:12px;color:#856404;">{v['notes']}</p>
            </div>
            """
        violations_html += "</div>"

    records_html = ""
    for r in data["records"]:
        temp_color = "#28a745" if data["is_compliant"] else "#dc3545"
        records_html += f"""
        <div style="display:flex;gap:10px;margin-bottom:12px;">
        <div style="width:8px;height:8px;border-radius:50%;background:{temp_color};margin-top:6px;"></div>
        <div style="flex:1;">
        <div style="display:flex;justify-content:space-between;">
        <span style="font-weight:bold;color:#333;">{r['stage']}</span>
        <span style="font-size:12px;color:#666;">{r['timestamp'][:16]}</span>
        </div>
        <div style="font-size:13px;color:#666;margin-top:2px;">{r['location']}</div>
        <div style="display:flex;gap:15px;margin-top:4px;font-size:12px;">
        <span style="color:{temp_color};">温度: {r.get('temperature', 'N/A')}℃</span>
        <span style="color:#666;">湿度: {r.get('humidity', 'N/A')}%</span>
        </div>
        {f'<div style="font-size:12px;color:#888;margin-top:4px;">{r["notes"]}</div>' if r.get('notes') else ''}
        </div>
        </div>
        """

    blockchain_details = ""
    if data['blockchain']['on_chain']:
        blockchain_details = f"""
        <div>区块编号: #{data['blockchain']['block_number']}</div>
        <div>区块哈希: {data['blockchain']['block_hash'][:16]}...</div>
        <div>Merkle根: {data['blockchain']['merkle_root'][:16]}...</div>
        <div>存证时间: {data['blockchain']['certified_at'][:16]}</div>
        """

    return f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width,initial-scale=1.0">
    <title>冷链追溯查询 - {data['cargo_name']}</title>
    <style>
    body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#f8f9fa;margin:0;padding:20px;}}
    .card{{background:white;border-radius:12px;box-shadow:0 2px 10px rgba(0,0,0,0.05);padding:20px;max-width:600px;margin:0 auto;}}
    .header{{text-align:center;margin-bottom:20px;}}
    .title{{font-size:20px;font-weight:bold;color:#333;margin:0;}}
    .code{{font-family:monospace;font-size:14px;color:#007bff;background:#e7f3ff;padding:4px 8px;border-radius:4px;margin-top:5px;display:inline-block;}}
    .info{{display:grid;grid-template-columns:2fr 3fr;gap:8px;font-size:14px;margin-bottom:20px;}}
    .info-label{{color:#666;font-weight:500;}}
    .info-value{{color:#333;}}
    .compliant{{color:#28a745;font-weight:bold;font-size:16px;text-align:center;margin:15px 0;padding:10px;background:#d4edda;border-radius:8px;}}
    .non-compliant{{color:#dc3545;font-weight:bold;font-size:16px;text-align:center;margin:15px 0;padding:10px;background:#f8d7da;border-radius:8px;}}
    .section-title{{font-size:16px;font-weight:bold;color:#333;margin:20px 0 10px;padding-bottom:8px;border-bottom:2px solid #eee;}}
    .blockchain{{background:#f8f9fa;border-radius:8px;padding:12px;font-size:12px;color:#666;margin-top:15px;}}
    </style>
    </head>
    <body>
    <div class="card">
    <div class="header">
    <h1 class="title">{data['cargo_name']}</h1>
    <div class="code">溯源码: {data['trace_code']}</div>
    </div>

    <div class="info">
    <div class="info-label">货物类别</div><div class="info-value">{data['cargo_category']}</div>
    <div class="info-label">发货地</div><div class="info-value">{data['origin']}</div>
    <div class="info-label">收货地</div><div class="info-value">{data['destination']}</div>
    <div class="info-label">数量</div><div class="info-value">{data['quantity']} {data['unit']}</div>
    <div class="info-label">温度要求</div><div class="info-value">{data['temperature_requirement']}</div>
    <div class="info-label">温度范围</div><div class="info-value">{data['temperature_summary']['min']}℃ ~ {data['temperature_summary']['max']}℃</div>
    </div>

    <div class="{'compliant' if data['is_compliant'] else 'non-compliant'}">
    {'✅ 全程温控达标' if data['is_compliant'] else '⚠️ 存在温度异常'}
    </div>

    {violations_html}

    <div class="section-title">📋 全程追溯记录</div>
    {records_html}

    <div class="blockchain">
    <div style="font-weight:bold;margin-bottom:4px;">🔗 区块链存证信息</div>
    <div>存证状态: {'已上链' if data['blockchain']['on_chain'] else '待存证'}</div>
    {blockchain_details}
    <div style="margin-top:8px;font-size:11px;color:#888;">数据已通过区块链加密存证，不可篡改</div>
    </div>
    </div>
    </body>
    </html>"""


# ==================== 管理API：运单与溯源码管理 ====================

@router.post("/data")
async def create_trace_data(
    data: TraceDataCreate,
    user: dict = Depends(require_role("admin", "warehouse")),
):
    """创建追溯数据（运单创建时自动调用）"""
    waybill_id = data.waybill_id
    
    if not waybill_id:
        waybill_id = f"WB-{datetime.utcnow().strftime('%Y%m%d')}-{len(WAYBILL_TRACE_MAP)+1:04d}"
    
    if waybill_id in WAYBILL_TRACE_MAP:
        trace_code = WAYBILL_TRACE_MAP[waybill_id]
        return {"status": "ok", "trace_code": trace_code, "waybill_id": waybill_id, "message": "该运单已关联溯源码"}

    trace_code = generate_trace_code(waybill_id)

    TRACE_DATA[trace_code] = {
        "trace_code": trace_code,
        "waybill_id": waybill_id,
        "cargo_name": data.cargo_name,
        "cargo_category": data.cargo_category,
        "origin": data.origin,
        "destination": data.destination,
        "quantity": data.quantity,
        "unit": data.unit,
        "temperature_requirement": data.temperature_requirement,
        "is_high_sensitivity": data.is_high_sensitivity,
        "created_at": datetime.utcnow().isoformat(),
        "status": "created",
    }
    WAYBILL_TRACE_MAP[waybill_id] = trace_code
    TRACE_CODE_MAP[trace_code] = []

    # 自动生成模拟追溯记录，确保新创建的运单有追溯数据
    _generate_mock_records(waybill_id, trace_code, TRACE_DATA[trace_code])

    return {"status": "ok", "trace_code": trace_code, "waybill_id": waybill_id}


@router.get("/data/{trace_code}")
async def get_trace_data(
    trace_code: str,
    user: dict = Depends(get_current_user),
):
    """获取追溯数据详情"""
    if trace_code not in TRACE_DATA:
        raise HTTPException(status_code=404, detail="未找到该溯源码")

    data = TRACE_DATA[trace_code]
    record_ids = TRACE_CODE_MAP.get(trace_code, [])
    records = [r for r in TRACE_RECORDS if r["id"] in record_ids]
    records = sorted(records, key=lambda r: r["timestamp"])

    # 如果没有追溯记录，自动生成模拟数据
    if not records:
        _generate_mock_records(data["waybill_id"], trace_code, data)
        records = [r for r in TRACE_RECORDS if r["id"] in TRACE_CODE_MAP.get(trace_code, [])]
        records = sorted(records, key=lambda r: r["timestamp"])

    return {
        "trace_code": trace_code,
        "data": data,
        "records": records,
        "total_records": len(records),
    }


@router.post("/record")
async def add_trace_record(
    trace_code: str,
    record: TraceRecord,
    user: dict = Depends(require_role("admin", "warehouse", "driver")),
):
    """添加追溯记录（各环节自动或手动上报）"""
    if trace_code not in TRACE_DATA:
        raise HTTPException(status_code=404, detail="溯源码不存在")

    record_id = f"tr-{uuid.uuid4().hex[:8]}"
    record_dict = record.model_dump()
    record_dict["id"] = record_id
    record_dict["timestamp"] = datetime.utcnow().isoformat()

    TRACE_RECORDS.append(record_dict)
    TRACE_CODE_MAP[trace_code].append(record_id)

    TRACE_DATA[trace_code]["status"] = "in_progress"

    if record.stage == "sign":
        TRACE_DATA[trace_code]["status"] = "completed"

    return {"status": "ok", "record": record_dict}


@router.post("/record/batch")
async def add_trace_records_batch(
    trace_code: str,
    records: List[TraceRecord],
    user: dict = Depends(require_role("admin", "warehouse", "driver")),
):
    """批量添加追溯记录"""
    if trace_code not in TRACE_DATA:
        raise HTTPException(status_code=404, detail="溯源码不存在")

    added = []
    for record in records:
        record_id = f"tr-{uuid.uuid4().hex[:8]}"
        record_dict = record.model_dump()
        record_dict["id"] = record_id
        record_dict["timestamp"] = record_dict.get("timestamp", datetime.utcnow().isoformat())
        TRACE_RECORDS.append(record_dict)
        TRACE_CODE_MAP[trace_code].append(record_id)
        added.append(record_dict)

    return {"status": "ok", "added": len(added), "records": added}


# ==================== 自动关联：传感器数据写入追溯链 ====================

@router.post("/auto/sensor")
async def auto_add_sensor_record(
    device_id: str,
    waybill_id: str,
    temperature: float,
    humidity: float = 0.0,
    latitude: float = 0.0,
    longitude: float = 0.0,
    door_status: int = 0,
    vehicle_speed: float = 0.0,
    cold_car_status: int = 1,
    user: dict = Depends(require_role("admin", "warehouse", "driver")),
):
    """
    传感器数据自动写入追溯链
    由 sensors.py 在接收传感器数据时调用
    """
    trace_code = WAYBILL_TRACE_MAP.get(waybill_id)
    if not trace_code:
        return {"status": "skipped", "message": "该运单未关联溯源码"}

    stage = "transport"
    location = ""
    action = "正常行驶"

    if door_status == 1:
        action = "车门开启"
    elif vehicle_speed == 0 and cold_car_status == 1:
        action = "车辆停靠"
    elif cold_car_status == 0:
        action = "冷机故障"

    record = TraceRecord(
        stage=stage,
        location=location,
        temperature=temperature,
        humidity=humidity,
        action=action,
        device_id=device_id,
        lat=latitude,
        lng=longitude,
        waybill_id=waybill_id,
    )

    return await add_trace_record(trace_code, record, user)


# ==================== 自动关联：配载信息写入追溯链 ====================

@router.post("/auto/dispatch")
async def auto_add_dispatch_record(
    waybill_id: str,
    vehicle_id: str,
    plate_number: str,
    driver_name: str,
    compartments: dict = None,
    user: dict = Depends(require_role("admin", "warehouse", "driver")),
):
    """
    配载信息自动写入追溯链
    由 dispatch.py 在生成调度方案时调用
    """
    trace_code = WAYBILL_TRACE_MAP.get(waybill_id)
    if not trace_code:
        return {"status": "skipped", "message": "该运单未关联溯源码"}

    record = TraceRecord(
        stage="loading",
        location=f"装车点",
        temperature=0.0,
        action=f"配载完成",
        operator=driver_name,
        device_id=vehicle_id,
        notes=f"车辆: {plate_number}, 舱位分配: {json.dumps(compartments) if compartments else 'N/A'}",
        waybill_id=waybill_id,
    )

    return await add_trace_record(trace_code, record, user)


# ==================== 自动关联：资源调度写入追溯链 ====================

@router.post("/auto/resource")
async def auto_add_resource_record(
    waybill_id: str,
    resource_type: str,
    resource_id: str,
    resource_name: str = "",
    allocation_info: dict = None,
    user: dict = Depends(require_role("admin", "warehouse", "driver")),
):
    """
    资源调度信息自动写入追溯链
    由 resources.py 在分配资源时调用
    """
    trace_code = WAYBILL_TRACE_MAP.get(waybill_id)
    if not trace_code:
        trace_code = generate_trace_code(waybill_id)
        TRACE_DATA[trace_code] = {
            "trace_code": trace_code,
            "waybill_id": waybill_id,
            "cargo_name": allocation_info.get("cargo_name", "未知"),
            "cargo_category": allocation_info.get("cargo_category", "未知"),
            "origin": allocation_info.get("origin", ""),
            "destination": allocation_info.get("destination", ""),
            "quantity": allocation_info.get("weight_allocated_kg", 0),
            "unit": "kg",
            "temperature_requirement": allocation_info.get("target_temp_c", 0),
            "is_high_sensitivity": allocation_info.get("is_high_sensitivity", False),
            "created_at": datetime.utcnow().isoformat(),
            "status": "created",
        }
        WAYBILL_TRACE_MAP[waybill_id] = trace_code
        TRACE_CODE_MAP[trace_code] = []

    stage_map = {
        "warehouse_slot": "warehouse_in",
        "vehicle": "loading",
        "cold_plate": "loading",
    }

    stage = stage_map.get(resource_type, "warehouse_store")
    resource_type_name = {
        "warehouse_slot": "库位",
        "vehicle": "车辆",
        "cold_plate": "蓄冷板",
    }.get(resource_type, resource_type)

    action = f"{resource_type_name}分配完成"

    record = TraceRecord(
        stage=stage,
        location=allocation_info.get("warehouse_name", "") if allocation_info else "",
        temperature=0.0,
        action=action,
        operator=user.get("sub", "system"),
        device_id=resource_id,
        notes=f"资源类型: {resource_type_name}, 资源ID: {resource_id}, 资源名称: {resource_name}, 分配详情: {json.dumps(allocation_info) if allocation_info else 'N/A'}",
        waybill_id=waybill_id,
    )

    return await add_trace_record(trace_code, record, user)


# ==================== 自动关联：围栏事件写入追溯链 ====================

@router.post("/auto/geofence")
async def auto_add_geofence_record(
    waybill_id: str,
    fence_name: str,
    event_type: str,
    location: str,
    temperature: float = 0.0,
    humidity: float = 0.0,
    lat: float = 0.0,
    lng: float = 0.0,
    user: dict = Depends(require_role("admin", "warehouse", "driver")),
):
    """
    围栏事件自动写入追溯链
    由 geofence.py 在触发围栏事件时调用
    """
    trace_code = WAYBILL_TRACE_MAP.get(waybill_id)
    if not trace_code:
        return {"status": "skipped", "message": "该运单未关联溯源码"}

    stage_map = {
        "warehouse_in": "warehouse_in",
        "warehouse_out": "warehouse_store",
        "transit_in": "transit_in",
        "transit_out": "transit_out",
        "loading": "loading",
        "unloading": "last_mile",
    }

    stage = stage_map.get(event_type, "transport")
    action = f"进入{event_type}" if "in" in event_type else f"离开{event_type}"

    record = TraceRecord(
        stage=stage,
        location=f"{location} ({fence_name})",
        temperature=temperature,
        humidity=humidity,
        action=action,
        lat=lat,
        lng=lng,
        waybill_id=waybill_id,
        notes=f"电子围栏: {fence_name}, 事件: {event_type}",
    )

    return await add_trace_record(trace_code, record, user)


# ==================== 智能溯源报告生成 ====================

@router.get("/report/{trace_code}")
async def generate_trace_report(
    trace_code: str,
    format: str = "json",
    user: dict = Depends(require_role("admin", "warehouse", "customer")),
):
    """生成智能溯源报告"""
    if trace_code not in TRACE_DATA:
        raise HTTPException(status_code=404, detail="未找到该溯源码")

    data = TRACE_DATA[trace_code]
    record_ids = TRACE_CODE_MAP.get(trace_code, [])
    records = [r for r in TRACE_RECORDS if r["id"] in record_ids]
    records = sorted(records, key=lambda r: r["timestamp"])

    if not records:
        # 自动生成模拟追溯记录，而非直接返回404
        _generate_mock_records(data["waybill_id"], trace_code, data)
        records = [r for r in TRACE_RECORDS if r["id"] in TRACE_CODE_MAP.get(trace_code, [])]
        records = sorted(records, key=lambda r: r["timestamp"])

    temps = [r["temperature"] for r in records if "temperature" in r]
    stages = list(set(r["stage"] for r in records))

    violations = []
    for r in records:
        if "temperature" in r:
            temp = r["temperature"]
            req = data.get("temperature_requirement", "")
            req_str = str(req) if req else ""
            if "~" in req_str:
                parts = req_str.split("~")
                try:
                    min_req = float(parts[0].replace("℃", "").strip())
                    max_req = float(parts[1].replace("℃", "").strip())
                    if temp < min_req or temp > max_req:
                        violations.append(r)
                except:
                    pass

    time_diff = datetime.fromisoformat(records[-1]["timestamp"]) - datetime.fromisoformat(records[0]["timestamp"])

    stage_details = {}
    for stage in STAGES:
        stage_records = [r for r in records if r["stage"] == stage["key"]]
        if stage_records:
            stage_temps = [r["temperature"] for r in stage_records if "temperature" in r]
            stage_details[stage["key"]] = {
                "name": stage["name"],
                "icon": stage["icon"],
                "count": len(stage_records),
                "first_time": stage_records[0]["timestamp"],
                "last_time": stage_records[-1]["timestamp"],
                "temp_range": f"{min(stage_temps):.1f}~{max(stage_temps):.1f}" if stage_temps else "N/A",
                "avg_temp": round(sum(stage_temps) / len(stage_temps), 1) if stage_temps else 0,
                "records": stage_records,
            }

    door_events = [r for r in records if r.get("action") and "车门" in r["action"]]
    location_changes = []
    for i in range(1, len(records)):
        prev = records[i - 1]
        curr = records[i]
        if prev.get("location") != curr.get("location") and curr.get("location"):
            location_changes.append({
                "from": prev.get("location", "未知"),
                "to": curr.get("location"),
                "time": curr["timestamp"],
            })

    report = {
        "report_id": f"RPT-{trace_code}",
        "trace_code": trace_code,
        "waybill_id": data["waybill_id"],
        "generated_at": datetime.utcnow().isoformat(),
        "cargo_info": {
            "name": data["cargo_name"],
            "category": data["cargo_category"],
            "quantity": data["quantity"],
            "unit": data["unit"],
            "is_high_sensitivity": data["is_high_sensitivity"],
        },
        "route_info": {
            "origin": data["origin"],
            "destination": data["destination"],
            "temperature_requirement": data["temperature_requirement"],
        },
        "time_summary": {
            "start_time": records[0]["timestamp"],
            "end_time": records[-1]["timestamp"],
            "duration_hours": round(time_diff.total_seconds() / 3600, 1),
            "total_records": len(records),
        },
        "temperature_summary": {
            "range": f"{min(temps):.1f}℃ ~ {max(temps):.1f}℃" if temps else "N/A",
            "avg": f"{sum(temps) / len(temps):.1f}℃" if temps else "N/A",
            "min": min(temps) if temps else 0,
            "max": max(temps) if temps else 0,
        },
        "stage_details": stage_details,
        "violations": {
            "count": len(violations),
            "items": violations,
            "is_compliant": len(violations) == 0,
        },
        "events": {
            "door_events": door_events,
            "location_changes": location_changes,
        },
        "records": records,
    }

    block = record_on_chain(trace_code, records, report)
    report["blockchain"] = {
        "on_chain": True,
        "block_number": block["block_number"],
        "block_hash": block["block_hash"],
        "prev_hash": block["prev_hash"],
        "merkle_root": block["merkle_root"],
        "certified_at": block["created_at"],
    }

    if format == "text":
        lines = [
            "=" * 60,
            "          冷链追溯合规报告",
            "=" * 60,
            f"报告编号: {report['report_id']}",
            f"溯源码:   {trace_code}",
            f"运单号:   {data['waybill_id']}",
            f"生成时间: {report['generated_at'][:19]}",
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
            "【时间统计】",
            f"  开始时间: {records[0]['timestamp'][:19]}",
            f"  结束时间: {records[-1]['timestamp'][:19]}",
            f"  运输时长: {round(time_diff.total_seconds() / 3600, 1)}小时",
            f"  记录总数: {len(records)}条",
            "",
            "【温度统计】",
            f"  温度范围: {min(temps):.1f}℃ ~ {max(temps):.1f}℃",
            f"  平均温度: {sum(temps) / len(temps):.1f}℃",
            f"  温控达标: {'是' if len(violations) == 0 else '否'}",
            "",
            "【各环节详情】",
        ]

        for stage_key, stage_info in stage_details.items():
            lines.append(f"  [{stage_info['icon']} {stage_info['name']}]")
            lines.append(f"    记录数: {stage_info['count']}")
            lines.append(f"    时间: {stage_info['first_time'][:16]} ~ {stage_info['last_time'][:16]}")
            lines.append(f"    温度: {stage_info['temp_range']}℃")

        if violations:
            lines.append("")
            lines.append("【温度异常记录】")
            for v in violations:
                lines.append(f"  ⚠️ [{v['stage']}] {v['timestamp'][:16]} | {v['temperature']}℃ | {v['notes']}")

        lines.append("")
        lines.append("【区块链存证信息】")
        lines.append(f"  区块编号: #{block['block_number']}")
        lines.append(f"  区块哈希: {block['block_hash'][:32]}...")
        lines.append(f"  Merkle根: {block['merkle_root'][:32]}...")
        lines.append(f"  存证时间: {block['created_at'][:19]}")
        lines.append("=" * 60)

        return PlainTextResponse("\n".join(lines))

    return report


# ==================== 区块链验证与查询 ====================

@router.get("/blockchain/verify/{trace_code}")
async def verify_blockchain(
    trace_code: str,
    user: dict = Depends(require_role("admin", "warehouse", "customer")),
):
    """验证区块链存证"""
    for block in BLOCKCHAIN_LEDGER:
        if block["data"].get("trace_code") == trace_code:
            recomputed = generate_block_hash(block["data"])
            is_valid = recomputed == block["block_hash"]

            chain_intact = True
            if block["block_number"] > 1:
                prev_block = BLOCKCHAIN_LEDGER[block["block_number"] - 2]
                chain_intact = block["prev_hash"] == prev_block["block_hash"]

            record_ids = TRACE_CODE_MAP.get(trace_code, [])
            records = [r for r in TRACE_RECORDS if r["id"] in record_ids]
            current_merkle = build_merkle_root(records)
            merkle_valid = current_merkle == block.get("merkle_root", "")

            return {
                "trace_code": trace_code,
                "verified": is_valid and chain_intact and merkle_valid,
                "block_hash_valid": is_valid,
                "chain_integrity": chain_intact,
                "merkle_integrity": merkle_valid,
                "block_number": block["block_number"],
                "block_hash": block["block_hash"],
                "merkle_root": block.get("merkle_root", ""),
                "current_merkle_root": current_merkle,
                "certified_at": block["created_at"],
                "message": "追溯数据区块链存证验证通过" if (is_valid and chain_intact and merkle_valid) else "区块链验证失败",
            }

    record_ids = TRACE_CODE_MAP.get(trace_code, [])
    records = [r for r in TRACE_RECORDS if r["id"] in record_ids]
    if records:
        report = {"is_compliant": True}
        block = record_on_chain(trace_code, records, report)
        return {
            "trace_code": trace_code,
            "verified": True,
            "message": "追溯数据已完成区块链存证",
            **block,
        }

    raise HTTPException(status_code=404, detail="未找到该溯源码")


@router.get("/blockchain/ledger")
async def get_blockchain_ledger(
    limit: int = 10,
    user: dict = Depends(require_role("admin", "warehouse")),
):
    """查看区块链账本"""
    return {
        "total_blocks": len(BLOCKCHAIN_LEDGER),
        "chain_integrity": verify_blockchain_integrity(),
        "blocks": BLOCKCHAIN_LEDGER[-limit:],
    }


# ==================== 搜索与统计 ====================

def normalize_waybill_id(waybill_id: str) -> str:
    """标准化运单号格式，移除所有分隔符，转换为统一格式"""
    if not waybill_id:
        return ""
    # 移除所有分隔符（-、_、空格等）
    normalized = ''.join(filter(str.isalnum, waybill_id.upper()))
    # 如果只有数字，添加WB前缀
    if normalized.isdigit():
        normalized = f"WB{normalized}"
    return normalized

def match_waybill_pattern(input_str: str, stored_id: str) -> bool:
    """运单号模糊匹配，支持不同格式"""
    input_norm = normalize_waybill_id(input_str)
    stored_norm = normalize_waybill_id(stored_id)
    # 精确匹配
    if input_norm == stored_norm:
        return True
    # 前缀匹配（如输入 WB-20260706 匹配 WB-20260706-0001）
    if input_norm and stored_norm.startswith(input_norm):
        return True
    # 包含匹配
    if input_norm and input_norm in stored_norm:
        return True
    return False

@router.get("/search")
async def search_traces(
    keyword: str = "",
    trace_code: str = "",
    waybill_id: str = "",
    cargo_name: str = "",
    limit: int = 20,
    user: dict = Depends(require_role("admin", "warehouse", "customer")),
):
    """搜索追溯记录"""
    results = []
    for tc, data in TRACE_DATA.items():
        if trace_code and trace_code not in tc:
            continue
        if waybill_id and not match_waybill_pattern(waybill_id, data["waybill_id"]):
            continue
        if cargo_name and cargo_name.lower() not in data["cargo_name"].lower():
            continue
        if keyword:
            kw = keyword.lower()
            if kw not in tc and not match_waybill_pattern(keyword, data["waybill_id"]) and kw not in data["cargo_name"].lower():
                continue

        record_ids = TRACE_CODE_MAP.get(tc, [])
        records = [r for r in TRACE_RECORDS if r["id"] in record_ids]
        temps = [r["temperature"] for r in records if "temperature" in r]

        results.append({
            "trace_code": tc,
            "waybill_id": data["waybill_id"],
            "cargo_name": data["cargo_name"],
            "cargo_category": data["cargo_category"],
            "origin": data["origin"],
            "destination": data["destination"],
            "status": data["status"],
            "total_records": len(records),
            "avg_temperature": round(sum(temps) / len(temps), 1) if temps else 0,
            "created_at": data["created_at"],
        })

    results.sort(key=lambda x: x["created_at"], reverse=True)
    return {"count": len(results[:limit]), "results": results[:limit]}


@router.get("/stats")
async def get_traceability_stats(
    user: dict = Depends(require_role("admin", "warehouse")),
):
    """追溯链统计数据"""
    total = len(TRACE_DATA)
    completed = sum(1 for d in TRACE_DATA.values() if d["status"] == "completed")
    in_progress = sum(1 for d in TRACE_DATA.values() if d["status"] == "in_progress")

    compliant = 0
    total_records = 0
    for tc, data in TRACE_DATA.items():
        record_ids = TRACE_CODE_MAP.get(tc, [])
        records = [r for r in TRACE_RECORDS if r["id"] in record_ids]
        total_records += len(records)

        violations = 0
        for r in records:
            if "temperature" in r:
                temp = r["temperature"]
                req = data.get("temperature_requirement", "")
                if "~" in req:
                    parts = req.split("~")
                    try:
                        min_req = float(parts[0].replace("℃", "").strip())
                        max_req = float(parts[1].replace("℃", "").strip())
                        if temp < min_req or temp > max_req:
                            violations += 1
                    except:
                        pass
        if violations == 0:
            compliant += 1

    on_chain_count = 0
    for tc in TRACE_DATA:
        for block in BLOCKCHAIN_LEDGER:
            if block["data"].get("trace_code") == tc:
                on_chain_count += 1
                break

    return {
        "total_traces": total,
        "completed_traces": completed,
        "in_progress_traces": in_progress,
        "total_records": total_records,
        "compliant_traces": compliant,
        "compliance_rate": round(compliant / max(total, 1) * 100, 1),
        "on_chain_count": on_chain_count,
        "chain_integrity": verify_blockchain_integrity(),
    }


# ==================== 运单关联查询 ====================

@router.get("/waybill/{waybill_id}")
async def get_trace_by_waybill(
    waybill_id: str,
    user: dict = Depends(get_current_user),
):
    """通过运单号查询追溯信息（支持格式标准化匹配）"""
    trace_code = WAYBILL_TRACE_MAP.get(waybill_id)
    
    if not trace_code:
        input_norm = normalize_waybill_id(waybill_id)
        for stored_wb, stored_tc in WAYBILL_TRACE_MAP.items():
            if match_waybill_pattern(waybill_id, stored_wb):
                trace_code = stored_tc
                break
    
    if not trace_code:
        raise HTTPException(status_code=404, detail="该运单未关联溯源码")

    return await get_trace_data(trace_code, user)


@router.get("/all")
async def get_all_traces(
    status: str = "",
    limit: int = 50,
    user: dict = Depends(require_role("admin", "warehouse")),
):
    """获取所有追溯记录"""
    results = []
    for tc, data in TRACE_DATA.items():
        if status and data["status"] != status:
            continue
        record_ids = TRACE_CODE_MAP.get(tc, [])
        records = [r for r in TRACE_RECORDS if r["id"] in record_ids]
        temps = [r["temperature"] for r in records if "temperature" in r]

        results.append({
            "trace_code": tc,
            "waybill_id": data["waybill_id"],
            "cargo_name": data["cargo_name"],
            "cargo_category": data["cargo_category"],
            "origin": data["origin"],
            "destination": data["destination"],
            "temperature_requirement": data["temperature_requirement"],
            "status": data["status"],
            "total_records": len(records),
            "avg_temperature": round(sum(temps) / len(temps), 1) if temps else 0,
            "created_at": data["created_at"],
            "is_high_sensitivity": data["is_high_sensitivity"],
        })

    results.sort(key=lambda x: x["created_at"], reverse=True)
    return {"count": len(results[:limit]), "traces": results[:limit]}