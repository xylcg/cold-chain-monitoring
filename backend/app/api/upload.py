"""
温度记录纸拍照上传 API
"""
import os
import uuid
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse
from loguru import logger

router = APIRouter(prefix="/api/v1/upload", tags=["文件上传"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 内存存储（生产环境应存在数据库中）
upload_records = []


@router.post("/temperature-record")
async def upload_temperature_record(
    file: UploadFile = File(...),
    device_id: str = Form(...),
    waybill_id: str = Form(default=""),
    notes: str = Form(default=""),
    latitude: float = Form(default=0),
    longitude: float = Form(default=0),
):
    """
    配送人员拍照上传温度记录纸
    
    - **file**: 图片文件 (jpg/png)
    - **device_id**: 车辆设备ID
    - **waybill_id**: 运单号（可选）
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
        "notes": notes,
        "latitude": latitude,
        "longitude": longitude,
        "size_bytes": len(content),
        "content_type": file.content_type,
        "upload_time": datetime.now().isoformat(),
        "url": f"/uploads/{filename}",
    }
    upload_records.append(record)

    logger.info(f"温度记录纸上传成功: {filename} (设备:{device_id}, {len(content)} bytes)")

    return {
        "code": 200,
        "message": "上传成功",
        "data": record,
    }


@router.get("/temperature-records")
async def list_temperature_records(
    device_id: str = Query(default=""),
    waybill_id: str = Query(default=""),
    limit: int = Query(default=20),
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
