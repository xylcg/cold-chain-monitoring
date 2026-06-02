"""
生鲜品质AI评估 API
模块7: 生鲜品质AI评估
- 基于计算机视觉的生鲜新鲜度无损检测
- 品质分级与剩余保鲜期预测
- 入库/出库品质记录
"""
import random
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from ..core.security import get_current_user

router = APIRouter(prefix="/api/v1/quality", tags=["品质评估"])

# ==================== 品类品质指标 ====================

PRODUCT_CATEGORIES = {
    "apple": {"name": "苹果", "category": "水果", "freshness_days": 60, "indicators": ["色泽", "硬度", "糖度", "表皮完整度"]},
    "strawberry": {"name": "草莓", "category": "水果", "freshness_days": 5, "indicators": ["色泽", "硬度", "腐烂率", "表皮完整度"]},
    "grape": {"name": "葡萄", "category": "水果", "freshness_days": 14, "indicators": ["色泽", "硬度", "糖度", "脱粒率"]},
    "lettuce": {"name": "生菜", "category": "蔬菜", "freshness_days": 7, "indicators": ["色泽", "水分", "萎蔫程度", "黄叶率"]},
    "tomato": {"name": "番茄", "category": "蔬菜", "freshness_days": 14, "indicators": ["色泽", "硬度", "表皮裂纹", "成熟度"]},
    "spinach": {"name": "菠菜", "category": "蔬菜", "freshness_days": 5, "indicators": ["色泽", "水分", "黄叶率", "萎蔫程度"]},
    "beef": {"name": "牛肉", "category": "肉类", "freshness_days": 21, "indicators": ["色泽", "pH值", "挥发性盐基氮", "弹性"]},
    "pork": {"name": "猪肉", "category": "肉类", "freshness_days": 14, "indicators": ["色泽", "pH值", "挥发性盐基氮", "弹性"]},
    "salmon": {"name": "三文鱼", "category": "海鲜", "freshness_days": 7, "indicators": ["色泽", "弹性", "挥发性盐基氮", "眼清度"]},
    "shrimp": {"name": "虾", "category": "海鲜", "freshness_days": 5, "indicators": ["色泽", "弹性", "黑变率", "气味"]},
    "milk": {"name": "鲜奶", "category": "乳制品", "freshness_days": 7, "indicators": ["酸度", "菌落数", "感官", "蛋白质含量"]},
    "yogurt": {"name": "酸奶", "category": "乳制品", "freshness_days": 14, "indicators": ["酸度", "菌落数", "感官", "乳清分离"]},
}

GRADE_LEVELS = ["S级(特优)", "A级(优)", "B级(良好)", "C级(合格)", "D级(不合格)"]
GRADE_COLORS = {"S级(特优)": "#00d2a0", "A级(优)": "#22c55e", "B级(良好)": "#f59e0b", "C级(合格)": "#f97316", "D级(不合格)": "#ef4444"}


def _simulate_cv_assessment(product_key: str, storage_days: int = 0) -> dict:
    """模拟计算机视觉品质评估（模拟CNN/ResNet推理）"""
    product = PRODUCT_CATEGORIES.get(product_key, PRODUCT_CATEGORIES["apple"])
    total_days = product["freshness_days"]
    random.seed(hash(f"{product_key}{storage_days}{datetime.utcnow().hour}") % 10000)

    # 模拟品质衰减曲线
    remaining_ratio = max(0.05, 1 - (storage_days / total_days) * (0.7 + random.uniform(-0.15, 0.15)))
    remaining_days = max(0.5, round(total_days * remaining_ratio, 1))

    # 各指标评分
    indicators_score = {}
    for ind in product["indicators"]:
        base = remaining_ratio * 80 + random.uniform(10, 25)
        indicators_score[ind] = round(min(100, max(5, base + random.uniform(-8, 8))), 1)

    # 综合品质评分
    overall_score = round(sum(indicators_score.values()) / len(indicators_score), 1)

    # 分级
    if overall_score >= 90:
        grade_idx = 0
    elif overall_score >= 78:
        grade_idx = 1
    elif overall_score >= 60:
        grade_idx = 2
    elif overall_score >= 40:
        grade_idx = 3
    else:
        grade_idx = 4

    grade = GRADE_LEVELS[grade_idx]
    confidence = round(random.uniform(0.88, 0.99), 3)  # 模型置信度

    return {
        "product_type": product["name"],
        "category": product["category"],
        "assessment_id": f"QA-{datetime.utcnow().strftime('%Y%m%d%H%M')}-{random.randint(100, 999)}",
        "storage_days": storage_days,
        "overall_score": overall_score,
        "grade": grade,
        "grade_color": GRADE_COLORS[grade],
        "remaining_shelf_life_days": remaining_days,
        "remaining_ratio_percent": round(remaining_ratio * 100, 1),
        "model_confidence": confidence,
        "model_used": "ResNet50-CNN + Vision Transformer",
        "indicators": indicators_score,
        "defect_detected": overall_score < 70,
        "defect_details": (
            [
                random.choice(["表面褐变", "机械损伤", "霉斑", "冻伤痕迹"]),
                random.choice(["轻微脱水", "颜色异常", "质地软化"])
            ][:random.randint(0, 2)]
            if overall_score < 70 else []
        ),
        "assessed_at": datetime.utcnow().isoformat(),
        "recommendation": _get_recommendation(grade),
    }


def _get_recommendation(grade: str) -> str:
    recommendations = {
        "S级(特优)": "优先供货高端渠道，建议3日内配送至终端",
        "A级(优)": "可正常入库存储，按标准配送流程发货",
        "B级(良好)": "建议优先出库配送，缩短仓储时间",
        "C级(合格)": "近期尽快处理，可折扣销售或加工处理",
        "D级(不合格)": "不建议继续储存，立即退货或销毁处理",
    }
    return recommendations.get(grade, "常规处理")


def _generate_batches() -> list:
    """生成品质批次记录"""
    random.seed(int(datetime.utcnow().timestamp()) // 60)
    batches = []
    origins = ["山东寿光", "云南昆明", "海南三亚", "新疆库尔勒", "辽宁大连", "浙江舟山", "内蒙古锡林郭勒"]
    product_keys = list(PRODUCT_CATEGORIES.keys())

    for i in range(1, 13):
        pk = random.choice(product_keys)
        product = PRODUCT_CATEGORIES[pk]
        storage = random.randint(0, product["freshness_days"] - 1)
        assessment = _simulate_cv_assessment(pk, storage)

        batches.append({
            "batch_id": f"BATCH-{datetime.utcnow().strftime('%Y%m')}-{i:04d}",
            "product_type": product["name"],
            "category": product["category"],
            "origin": random.choice(origins),
            "quantity_kg": random.randint(500, 5000),
            "storage_temp_c": round(random.uniform(-2, 4), 1),
            "warehouse": random.choice(["华北中心冷库", "华东配送中心", "华南前置仓", "西南冷链基地"]),
            "storage_days": storage,
            "grade": assessment["grade"],
            "overall_score": assessment["overall_score"],
            "remaining_shelf_life_days": assessment["remaining_shelf_life_days"],
            "defect_detected": assessment["defect_detected"],
            "status": "in_storage" if assessment["overall_score"] >= 40 else "to_dispose",
            "last_assessed": assessment["assessed_at"],
        })

    return batches


# ==================== API 接口 ====================

class AssessRequest(BaseModel):
    product_type: str  # 品类key，如 "apple", "strawberry"
    storage_days: int = 0

@router.post("/assess")
async def assess_quality(
    request: AssessRequest,
    user: dict = Depends(get_current_user),
):
    """模拟计算机视觉品质评估"""
    if request.product_type not in PRODUCT_CATEGORIES:
        product_list = ", ".join(PRODUCT_CATEGORIES.keys())
        return {
            "status": "error",
            "detail": f"不支持的品类: {request.product_type}，可选: {product_list}",
            "available_products": [
                {"key": k, "name": v["name"], "category": v["category"]}
                for k, v in PRODUCT_CATEGORIES.items()
            ],
        }

    product = PRODUCT_CATEGORIES[request.product_type]
    if request.storage_days > product["freshness_days"] * 1.5:
        return {"status": "error", "detail": f"储存天数超出{product['name']}最大保鲜期的150%"}

    result = _simulate_cv_assessment(request.product_type, request.storage_days)
    result["max_freshness_days"] = product["freshness_days"]
    return result


@router.get("/batches")
async def get_batches(
    category: Optional[str] = Query(None, description="品类过滤"),
    grade: Optional[str] = Query(None, description="等级过滤"),
    user: dict = Depends(get_current_user),
):
    """获取品质批次列表"""
    batches = _generate_batches()
    if category:
        batches = [b for b in batches if b["category"] == category]
    if grade:
        batches = [b for b in batches if b["grade"] == grade]

    grades_dist = {}
    for b in batches:
        g = b["grade"]
        grades_dist[g] = grades_dist.get(g, 0) + 1

    return {
        "total": len(batches),
        "grade_distribution": grades_dist,
        "batches": batches,
    }


@router.get("/batch/{batch_id}")
async def get_batch_detail(
    batch_id: str,
    user: dict = Depends(get_current_user),
):
    """获取批次详细品质报告"""
    batches = _generate_batches()
    batch = next((b for b in batches if b["batch_id"] == batch_id), None)
    if not batch:
        # 为请求的批次生成模拟数据
        product_key = next(
            (k for k, v in PRODUCT_CATEGORIES.items() if v["name"] == "苹果"), "apple"
        )
        batch = _generate_batches()[0]
        batch["batch_id"] = batch_id

    product_key = next(
        (k for k, v in PRODUCT_CATEGORIES.items() if v["name"] == batch["product_type"]),
        "apple"
    )
    detail = _simulate_cv_assessment(product_key, batch["storage_days"])

    # 添加历史品质趋势
    history = []
    for d in range(0, batch["storage_days"] + 1, max(1, batch["storage_days"] // 6)):
        hist = _simulate_cv_assessment(product_key, d)
        history.append({
            "day": d,
            "score": hist["overall_score"],
            "grade": hist["grade"],
        })

    batch["detail"] = detail
    batch["quality_trend"] = history
    return batch


@router.get("/stats")
async def get_quality_stats(
    user: dict = Depends(get_current_user),
):
    """品质统计概览"""
    batches = _generate_batches()
    total = len(batches)
    defective = sum(1 for b in batches if b["defect_detected"])

    grade_dist = {}
    for b in batches:
        g = b["grade"]
        grade_dist[g] = grade_dist.get(g, 0) + 1

    cat_dist = {}
    for b in batches:
        c = b["category"]
        cat_dist[c] = cat_dist.get(c, 0) + 1

    scores = [b["overall_score"] for b in batches]

    return {
        "total_batches": total,
        "defective_batches": defective,
        "defect_rate": round(defective / total * 100, 1) if total > 0 else 0,
        "avg_quality_score": round(sum(scores) / len(scores), 1),
        "grade_distribution": grade_dist,
        "category_distribution": cat_dist,
        "products_supported": len(PRODUCT_CATEGORIES),
    }


@router.get("/products")
async def get_products(
    user: dict = Depends(get_current_user),
):
    """获取支持评估的品类列表"""
    return {
        "count": len(PRODUCT_CATEGORIES),
        "products": [
            {
                "key": k,
                "name": v["name"],
                "category": v["category"],
                "max_freshness_days": v["freshness_days"],
                "indicators": v["indicators"],
            }
            for k, v in PRODUCT_CATEGORIES.items()
        ],
    }
