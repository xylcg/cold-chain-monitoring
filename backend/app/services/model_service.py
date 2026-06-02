"""
深度学习模型推理服务
- LSTM 异常检测
- LSTM/Transformer 温度预测
支持 GPU/CPU 自动切换，含降级策略
"""
import os
import sys
import numpy as np
from typing import Optional
from loguru import logger
from dataclasses import dataclass

from ..schemas import TEMP_THRESHOLD

# 添加 models 目录到 Python 路径
_MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "models")
if _MODELS_DIR not in sys.path:
    sys.path.insert(0, _MODELS_DIR)

# 预检测 PyTorch 是否可用（避免运行时 500 错误）
_PYTORCH_AVAILABLE = False
try:
    import torch
    _PYTORCH_AVAILABLE = True
except ImportError:
    pass

# NumPy 模型始终可用（无需 PyTorch 依赖）
_NUMPY_MODELS_AVAILABLE = True

# 模型实例（延迟加载）
_anomaly_detector = None
_temperature_predictor = None
_numpy_anomaly_detector = None
_numpy_temperature_predictor = None


@dataclass
class AnomalyDetectionResult:
    is_anomaly: bool
    score: float
    threshold: float
    device_id: str
    timestamp: str
    method: str = "lstm"


@dataclass
class TemperaturePredictionResult:
    device_id: str
    current_temperature: float
    predictions: list[float]
    confidence_upper: list[float]
    confidence_lower: list[float]
    risk_level: str
    method: str = "lstm_transformer"


def get_anomaly_detector():
    """获取异常检测器单例（延迟加载）"""
    global _anomaly_detector
    if _anomaly_detector is None:
        if not _PYTORCH_AVAILABLE:
            logger.info("[模型服务] PyTorch 未安装，异常检测将使用统计方法")
            return None
        try:
            from lstm_anomaly_detector import AnomalyDetector
            model_path = os.path.join(_MODELS_DIR, "lstm_anomaly_detector.pt")
            _anomaly_detector = AnomalyDetector(
                input_dim=5,
                window_size=60,
                threshold_percentile=99.0,
                model_path=model_path if os.path.exists(model_path) else None,
            )
            logger.info(f"[模型服务] LSTM异常检测器已加载 (模型文件: {'存在' if os.path.exists(model_path) else '使用未训练模型'})")
        except Exception as e:
            logger.warning(f"[模型服务] 异常检测器加载失败: {e}，将使用统计方法")
            _anomaly_detector = None
    return _anomaly_detector


def get_numpy_anomaly_detector():
    """获取 NumPy 异常检测器（无需 PyTorch）"""
    global _numpy_anomaly_detector
    if _numpy_anomaly_detector is None:
        try:
            from numpy_anomaly_detector import NumpyAnomalyDetector, generate_training_data
            model_path = os.path.join(_MODELS_DIR, "lstm_anomaly_detector_np.pkl")
            _numpy_anomaly_detector = NumpyAnomalyDetector(
                input_dim=5, window_size=60, threshold_percentile=99.0,
                model_path=model_path if os.path.exists(model_path) else None,
            )
            # 首次加载时训练并保存
            if not os.path.exists(model_path):
                train_data = generate_training_data(5000)
                _numpy_anomaly_detector.train(train_data, epochs=10)
                _numpy_anomaly_detector.save(model_path)
                logger.info("[模型服务] NumPy异常检测器训练完成并保存")
            logger.info("[模型服务] NumPy异常检测器已加载")
        except Exception as e:
            logger.warning(f"[模型服务] NumPy异常检测器加载失败: {e}")
            _numpy_anomaly_detector = None
    return _numpy_anomaly_detector


def get_numpy_temperature_predictor():
    """获取 NumPy 温度预测器（无需 PyTorch）"""
    global _numpy_temperature_predictor
    if _numpy_temperature_predictor is None:
        try:
            from numpy_temperature_predictor import NumpyTemperaturePredictor, generate_temperature_data
            model_path = os.path.join(_MODELS_DIR, "temperature_predictor_np.pkl")
            _numpy_temperature_predictor = NumpyTemperaturePredictor(
                input_dim=6, window_size=60, horizon=30,
                model_path=model_path if os.path.exists(model_path) else None,
            )
            # 首次加载时训练并保存
            if not os.path.exists(model_path):
                train_data = generate_temperature_data(5000)
                _numpy_temperature_predictor.fit_scaler(train_data)
                _numpy_temperature_predictor.save(model_path)
                logger.info("[模型服务] NumPy温度预测器训练完成并保存")
            logger.info("[模型服务] NumPy温度预测器已加载")
        except Exception as e:
            logger.warning(f"[模型服务] NumPy温度预测器加载失败: {e}")
            _numpy_temperature_predictor = None
    return _numpy_temperature_predictor


def get_temperature_predictor():
    """获取温度预测器单例（延迟加载）"""
    global _temperature_predictor
    if _temperature_predictor is None:
        if not _PYTORCH_AVAILABLE:
            logger.info("[模型服务] PyTorch 未安装，温度预测将使用NumPy/统计方法")
            return None
        try:
            from temperature_predictor import TemperaturePredictionService
            model_path = os.path.join(_MODELS_DIR, "lstm_temperature_predictor.pt")
            _temperature_predictor = TemperaturePredictionService(
                input_dim=6,
                window_size=60,
                horizon=30,
                model_path=model_path if os.path.exists(model_path) else None,
            )
            logger.info(f"[模型服务] LSTM/Transformer温度预测器已加载 (模型文件: {'存在' if os.path.exists(model_path) else '使用未训练模型'})")
        except Exception as e:
            logger.warning(f"[模型服务] 温度预测器加载失败: {e}，将使用统计方法")
            _temperature_predictor = None
    return _temperature_predictor


async def detect_anomaly(
    device_id: str,
    window_data: list[float],
    humidity_data: Optional[list[float]] = None,
    door_data: Optional[list[float]] = None,
    vibration_data: Optional[list[float]] = None,
    external_temp_data: Optional[list[float]] = None,
) -> AnomalyDetectionResult:
    """
    使用深度学习模型检测温度异常
    优先顺序: NumPy模型 > PyTorch模型 > Z-score统计方法
    """
    from datetime import datetime
    n = min(60, len(window_data))

    # 1. 优先尝试 NumPy 模型（无需 PyTorch，Docker 友好）
    np_detector = get_numpy_anomaly_detector()
    if np_detector is not None and len(window_data) >= 30:
        try:
            features = []
            for i in range(n):
                idx = len(window_data) - n + i
                row = [
                    window_data[idx] if idx < len(window_data) else window_data[-1],
                    humidity_data[idx] if humidity_data and idx < len(humidity_data) else 65.0,
                    external_temp_data[idx] if external_temp_data and idx < len(external_temp_data) else 25.0,
                    door_data[idx] if door_data and idx < len(door_data) else 0,
                    vibration_data[idx] if vibration_data and idx < len(vibration_data) else 0.1,
                ]
                features.append(row)
            features = np.array(features, dtype=np.float32)
            result = np_detector.detect(features)
            return AnomalyDetectionResult(
                is_anomaly=result.is_anomaly,
                score=result.score,
                threshold=result.threshold,
                device_id=device_id,
                timestamp=datetime.utcnow().isoformat(),
                method="lstm_numpy",
            )
        except Exception as e:
            logger.error(f"[模型服务] NumPy异常检测失败: {e}")

    # 2. 尝试 PyTorch 模型
    detector = get_anomaly_detector()
    if detector is not None and len(window_data) >= 60:
        try:
            features = []
            for i in range(n):
                idx = len(window_data) - n + i
                row = [
                    window_data[idx] if idx < len(window_data) else window_data[-1],
                    humidity_data[idx] if humidity_data and idx < len(humidity_data) else 65.0,
                    external_temp_data[idx] if external_temp_data and idx < len(external_temp_data) else 25.0,
                    door_data[idx] if door_data and idx < len(door_data) else 0,
                    vibration_data[idx] if vibration_data and idx < len(vibration_data) else 0.1,
                ]
                features.append(row)
            features = np.array(features, dtype=np.float32)
            result = detector.detect(features)
            result.device_id = device_id
            result.timestamp = datetime.utcnow().isoformat()
            return result
        except Exception as e:
            logger.error(f"[模型服务] LSTM异常检测失败: {e}，降级为统计方法")

    # 3. 降级：Z-score 统计方法
    return _statistical_anomaly_detect(device_id, window_data)


def _statistical_anomaly_detect(device_id: str, window_data: list[float]) -> AnomalyDetectionResult:
    """统计方法异常检测（降级方案）"""
    from datetime import datetime

    if len(window_data) < 10:
        return AnomalyDetectionResult(
            is_anomaly=False, score=0.0, threshold=3.0,
            device_id=device_id, timestamp=datetime.utcnow().isoformat(),
            method="statistical",
        )

    recent = window_data[-10:]
    current = recent[-1]
    mean = np.mean(recent)
    std = np.std(recent) if np.std(recent) > 0 else 1
    z_score = abs(current - mean) / std

    is_anomaly = z_score > 3 or current > TEMP_THRESHOLD["DANGER_UPPER"] or current < TEMP_THRESHOLD["LOW_LIMIT"]
    return AnomalyDetectionResult(
        is_anomaly=is_anomaly,
        score=float(z_score),
        threshold=3.0,
        device_id=device_id,
        timestamp=datetime.utcnow().isoformat(),
        method="statistical",
    )


async def predict_temperature_trend(
    device_id: str,
    window_data: list[float],
    humidity_data: Optional[list[float]] = None,
    door_data: Optional[list[float]] = None,
    vibration_data: Optional[list[float]] = None,
    external_temp_data: Optional[list[float]] = None,
    cooling_power_data: Optional[list[float]] = None,
) -> TemperaturePredictionResult:
    """
    使用深度学习模型预测温度趋势
    优先顺序: NumPy模型(Holt-Winters) > PyTorch模型 > 线性外推
    """
    current_temp = window_data[-1] if window_data else 0.0
    n = min(60, len(window_data))

    # 1. 优先尝试 NumPy 模型（Holt-Winters + 指数平滑）
    np_predictor = get_numpy_temperature_predictor()
    if np_predictor is not None and len(window_data) >= 20:
        try:
            features = []
            for i in range(n):
                idx = len(window_data) - n + i
                row = [
                    window_data[idx] if idx < len(window_data) else window_data[-1],
                    humidity_data[idx] if humidity_data and idx < len(humidity_data) else 65.0,
                    external_temp_data[idx] if external_temp_data and idx < len(external_temp_data) else 25.0,
                    door_data[idx] if door_data and idx < len(door_data) else 0,
                    vibration_data[idx] if vibration_data and idx < len(vibration_data) else 0.1,
                    cooling_power_data[idx] if cooling_power_data and idx < len(cooling_power_data) else 0.5,
                ]
                features.append(row)
            features = np.array(features, dtype=np.float32)
            result = np_predictor.predict(features)
            return TemperaturePredictionResult(
                device_id=device_id,
                current_temperature=current_temp,
                predictions=result["predictions"],
                confidence_upper=result["confidence_upper"],
                confidence_lower=result["confidence_lower"],
                risk_level=result["risk_level"],
                method=f"numpy_{result.get('method', 'holt_winters')}",
            )
        except Exception as e:
            logger.error(f"[模型服务] NumPy温度预测失败: {e}")

    # 2. 尝试 PyTorch 模型
    predictor = get_temperature_predictor()
    if predictor is not None and len(window_data) >= 60:
        try:
            features = []
            for i in range(n):
                idx = len(window_data) - n + i
                row = [
                    window_data[idx] if idx < len(window_data) else window_data[-1],
                    humidity_data[idx] if humidity_data and idx < len(humidity_data) else 65.0,
                    external_temp_data[idx] if external_temp_data and idx < len(external_temp_data) else 25.0,
                    door_data[idx] if door_data and idx < len(door_data) else 0,
                    vibration_data[idx] if vibration_data and idx < len(vibration_data) else 0.1,
                    cooling_power_data[idx] if cooling_power_data and idx < len(cooling_power_data) else 0.5,
                ]
                features.append(row)
            features = np.array(features, dtype=np.float32)
            result = predictor.predict(features)
            return TemperaturePredictionResult(
                device_id=device_id,
                current_temperature=current_temp,
                predictions=result["predictions"],
                confidence_upper=result["confidence_upper"],
                confidence_lower=result["confidence_lower"],
                risk_level=result["risk_level"],
                method="lstm_transformer",
            )
        except Exception as e:
            logger.error(f"[模型服务] LSTM/Transformer预测失败: {e}，降级为统计方法")

    # 3. 降级：线性外推
    return _linear_extrapolation(device_id, window_data)


def _linear_extrapolation(device_id: str, window_data: list[float]) -> TemperaturePredictionResult:
    """线性外推预测（降级方案）"""
    if len(window_data) < 10:
        return TemperaturePredictionResult(
            device_id=device_id,
            current_temperature=window_data[-1] if window_data else 0.0,
            predictions=[0.0] * 30,
            confidence_upper=[0.0] * 30,
            confidence_lower=[0.0] * 30,
            risk_level="normal",
            method="linear",
        )

    recent = window_data[-30:]
    current = recent[-1]
    slope = (recent[-1] - recent[0]) / max(len(recent) - 1, 1)

    predictions = []
    upper = []
    lower = []
    predicted = current

    for i in range(30):
        predicted += slope * 0.7
        noise_std = 0.15 * (i + 1) ** 0.5
        predictions.append(round(predicted, 2))
        upper.append(round(predicted + 2 * noise_std, 2))
        lower.append(round(predicted - 2 * noise_std, 2))

    max_pred = max(predictions)
    if max_pred > 15:
        risk_level = "critical"
    elif max_pred > 8:
        risk_level = "warning"
    else:
        risk_level = "normal"

    return TemperaturePredictionResult(
        device_id=device_id,
        current_temperature=current,
        predictions=predictions,
        confidence_upper=upper,
        confidence_lower=lower,
        risk_level=risk_level,
        method="linear",
    )
