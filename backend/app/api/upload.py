"""
温度记录纸拍照上传 API - 含司机拍照审核流程
"""
import os
import json
import uuid
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, Query, Depends
from fastapi.responses import JSONResponse
from typing import List
from pydantic import BaseModel
from loguru import logger

from ..core.security import get_current_user, require_role

router = APIRouter(prefix="/api/v1/upload", tags=["文件上传"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# JSON 持久化文件路径
RECORDS_FILE = os.path.join(UPLOAD_DIR, "_records.json")

# 内存存储，启动时从 JSON 文件加载
upload_records = []


def _save_records():
    """将上传记录持久化到 JSON 文件"""
    try:
        with open(RECORDS_FILE, "w", encoding="utf-8") as f:
            json.dump(upload_records, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"保存上传记录失败: {e}")


def _load_records():
    """从 JSON 文件加载上传记录"""
    global upload_records
    if os.path.exists(RECORDS_FILE):
        try:
            with open(RECORDS_FILE, "r", encoding="utf-8") as f:
                upload_records = json.load(f)
            logger.info(f"已加载 {len(upload_records)} 条上传记录")
        except Exception as e:
            logger.warning(f"加载上传记录失败: {e}，使用空列表")
            upload_records = []


# 启动时加载
_load_records()

# 审核状态: pending_review / approved / rejected
class ReviewRequest(BaseModel):
    action: str  # "approve" 或 "reject"
    notes: str = ""


@router.post("/temperature-record")
async def upload_temperature_record(
    file: UploadFile = File(...),
    device_id: str = Form(...),
    waybill_id: str = Form(default=""),
    order_id: str = Form(default=""),
    photo_type: str = Form(default="deliver"),  # "accept"(出发) 或 "deliver"(送达)
    notes: str = Form(default=""),
    latitude: float = Form(default=0),
    longitude: float = Form(default=0),
    user: dict = Depends(require_role("driver", "admin", "warehouse")),
):
    """
    配送人员拍照上传温度记录纸
    
    - **file**: 图片文件 (jpg/png)
    - **device_id**: 车辆设备ID
    - **waybill_id**: 运单号（可选）
    - **order_id**: 配送订单ID（可选）
    - **photo_type**: 拍照类型 accept=出发拍照 / deliver=送达拍照
    - **notes**: 备注说明（可选）
    - **latitude/longitude**: 拍摄位置（可选）
    """
    # 验证文件类型
    allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
    if file.content_type not in allowed_types:
        return JSONResponse(
            status_code=400,
            content={"code": 400, "message": f"不支持的文件类型: {file.content_type}，仅支持 jpg/png/webp"}
        )

    # 验证大小 < 10MB
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        return JSONResponse(
            status_code=400,
            content={"code": 400, "message": "文件大小超过10MB限制"}
        )

    # 生成唯一文件名
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{device_id}_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    # 保存文件
    with open(filepath, "wb") as f:
        f.write(content)

    record = {
        "id": str(uuid.uuid4()),
        "filename": filename,
        "original_name": file.filename,
        "device_id": device_id,
        "waybill_id": waybill_id,
        "order_id": order_id,
        "photo_type": photo_type,
        "notes": notes,
        "latitude": latitude,
        "longitude": longitude,
        "size_bytes": len(content),
        "content_type": file.content_type,
        "upload_time": datetime.now().isoformat(),
        "uploaded_by": user.get("sub", "unknown"),
        "url": f"/uploads/{filename}",
        # 审核状态字段
        "review_status": "pending_review",  # pending_review / approved / rejected
        "review_notes": "",
        "reviewed_by": "",
        "reviewed_at": None,
    }
    upload_records.append(record)
    _save_records()

    logger.info(f"温度记录纸上传成功: {filename} (设备:{device_id}, 类型:{photo_type}, 待审核)")

    return {
        "code": 200,
        "message": "上传成功，等待仓管审核",
        "data": record,
    }


@router.get("/temperature-records")
async def list_temperature_records(
    device_id: str = Query(default=""),
    waybill_id: str = Query(default=""),
    limit: int = Query(default=20),
    user: dict = Depends(require_role("admin", "warehouse", "driver")),
):
    """
    查询温度记录纸上传列表
    
    - 可按设备ID或运单号筛选
    """
    records = upload_records
    if device_id:
        records = [r for r in records if r["device_id"] == device_id]
    if waybill_id:
        records = [r for r in records if r["waybill_id"] == waybill_id]
    records = sorted(records, key=lambda x: x["upload_time"], reverse=True)[:limit]

    return {
        "code": 200,
        "message": "查询成功",
        "data": {
            "total": len(records),
            "records": records,
        },
    }


@router.get("/pending-reviews")
async def list_pending_reviews(
    review_status: str = Query(default="pending_review"),
    limit: int = Query(default=50),
    user: dict = Depends(require_role("admin", "warehouse")),
):
    """
    仓管/维修查询待审核的拍照记录
    
    - **review_status**: 审核状态筛选 (pending_review/approved/rejected/all)
    """
    if review_status == "all":
        records = upload_records
    else:
        records = [r for r in upload_records if r.get("review_status") == review_status]
    records = sorted(records, key=lambda x: x["upload_time"], reverse=True)[:limit]

    return {
        "code": 200,
        "message": "查询成功",
        "data": {
            "total": len(records),
            "records": records,
        },
    }


@router.post("/review/{record_id}")
async def review_photo(
    record_id: str,
    body: ReviewRequest,
    user: dict = Depends(require_role("admin", "warehouse")),
):
    """
    仓管审核司机上传的拍照记录
    
    - **action**: "approve" 通过审核 / "reject" 驳回
    - **notes**: 审核备注（驳回时必填原因）
    """
    if body.action not in ("approve", "reject"):
        return JSONResponse(
            status_code=400,
            content={"code": 400, "message": "action 必须是 approve 或 reject"}
        )

    target = None
    for r in upload_records:
        if r["id"] == record_id:
            target = r
            break

    if not target:
        return JSONResponse(
            status_code=404,
            content={"code": 404, "message": f"未找到记录: {record_id}"}
        )

    if target.get("review_status") != "pending_review":
        return JSONResponse(
            status_code=400,
            content={"code": 400, "message": f"该记录已审核，当前状态: {target.get('review_status')}"}
        )

    if body.action == "reject" and not body.notes.strip():
        return JSONResponse(
            status_code=400,
            content={"code": 400, "message": "驳回时必须填写审核备注/原因"}
        )

    now = datetime.now().isoformat()
    target["review_status"] = "approved" if body.action == "approve" else "rejected"
    target["review_notes"] = body.notes
    target["reviewed_by"] = user.get("sub", "warehouse")
    target["reviewed_at"] = now
    _save_records()

    action_label = "通过" if body.action == "approve" else "驳回"
    logger.info(f"拍照审核{action_label}: {target['filename']} (ID:{record_id})")

    return {
        "code": 200,
        "message": f"审核{action_label}",
        "data": target,
    }


# ====== 🔴 P0: 批量审核照片 ======
class BatchReviewRequest(BaseModel):
    record_ids: List[str]
    action: str  # "approve" 或 "reject"
    notes: str = ""


@router.post("/review/batch")
async def batch_review_photos(
    body: BatchReviewRequest,
    user: dict = Depends(require_role("admin", "warehouse")),
):
    """
    批量审核司机上传的拍照记录
    
    - **record_ids**: 审核记录 ID 列表
    - **action**: "approve" 批量通过 / "reject" 批量驳回
    - **notes**: 审核备注
    """
    if body.action not in ("approve", "reject"):
        return JSONResponse(
            status_code=400,
            content={"code": 400, "message": "action 必须是 approve 或 reject"}
        )

    if body.action == "reject" and not body.notes.strip():
        return JSONResponse(
            status_code=400,
            content={"code": 400, "message": "批量驳回时必须填写审核备注/原因"}
        )

    if not body.record_ids:
        return JSONResponse(
            status_code=400,
            content={"code": 400, "message": "record_ids 不能为空"}
        )

    now = datetime.now().isoformat()
    reviewer = user.get("sub", "warehouse")
    success = 0
    skipped = 0
    not_found = 0

    for rid in body.record_ids:
        target = None
        for r in upload_records:
            if r["id"] == rid:
                target = r
                break
        if not target:
            not_found += 1
            continue
        if target.get("review_status") != "pending_review":
            skipped += 1
            continue
        target["review_status"] = "approved" if body.action == "approve" else "rejected"
        target["review_notes"] = body.notes
        target["reviewed_by"] = reviewer
        target["reviewed_at"] = now
        success += 1

    _save_records()
    action_label = "通过" if body.action == "approve" else "驳回"
    logger.info(f"批量审核{action_label}: 成功{success}, 跳过{skipped}, 未找到{not_found}")

    return {
        "code": 200,
        "message": f"批量审核完成: {action_label} {success}条",
        "data": {
            "success": success,
            "skipped": skipped,
            "not_found": not_found,
            "total_requested": len(body.record_ids),
        },
    }


@router.get("/review-stats")
async def review_stats(
    user: dict = Depends(require_role("admin", "warehouse")),
):
    """获取审核统计数据"""
    total = len(upload_records)
    pending = sum(1 for r in upload_records if r.get("review_status") == "pending_review")
    approved = sum(1 for r in upload_records if r.get("review_status") == "approved")
    rejected = sum(1 for r in upload_records if r.get("review_status") == "rejected")

    return {
        "code": 200,
        "message": "查询成功",
        "data": {
            "total": total,
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
        },
    }


@router.get("/driver-photos")
async def get_driver_photos(
    order_id: str = Query(default=""),
    user: dict = Depends(get_current_user),
):
    """
    司机查询自己订单的拍照审核状态
    
    - **order_id**: 订单ID（可选，为空则返回全部）
    """
    records = upload_records
    if order_id:
        records = [r for r in records if r.get("order_id") == order_id]
    records = sorted(records, key=lambda x: x["upload_time"], reverse=True)

    # 为司机返回精简信息
    results = []
    for r in records:
        results.append({
            "id": r["id"],
            "order_id": r.get("order_id", ""),
            "photo_type": r.get("photo_type", ""),
            "review_status": r.get("review_status", "pending_review"),
            "review_notes": r.get("review_notes", ""),
            "upload_time": r["upload_time"],
            "reviewed_at": r.get("reviewed_at"),
            "url": r["url"],
            "notes": r.get("notes", ""),
        })

    return {
        "code": 200,
        "message": "查询成功",
        "data": {
            "total": len(results),
            "records": results,
        },
    }
