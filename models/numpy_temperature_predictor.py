"""
纯 NumPy 实现温度趋势预测模型
无需 PyTorch，可在 Docker 环境中直接运行
基于滑动窗口 + 指数平滑 + 线性回归 + 季节性分解
"""
import numpy as np
import pickle
import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class PredictionResult:
    predictions: list[float]
    confidence_upper: list[float]
    confidence_lower: list[float]
    risk_level: str


class NumpyTemperaturePredictor:
    """
    纯 NumPy 温度预测器
    使用 Holt-Winters 指数平滑 + 线性趋势 + 季节性分解
    无需 PyTorch
    """

    def __init__(
        self,
        input_dim: int = 6,
        window_size: int = 60,
        horizon: int = 30,
        model_path: Optional[str] = None,
    ):
        self.input_dim = input_dim
        self.window_size = window_size
        self.horizon = horizon
        self._mean = None
        self._std = None
        self._seasonal_period = 12  # 季节性周期

    def fit_scaler(self, data: np.ndarray):
        """拟合标准化参数"""
        self._mean = data.mean(axis=0)
        self._std = data.std(axis=0)
        self._std[self._std == 0] = 1

    def _normalize(self, data: np.ndarray) -> np.ndarray:
        if self._mean is not None:
            return (data - self._mean) / self._std
        return data

    def _denormalize_temp(self, data: np.ndarray) -> np.ndarray:
        """反标准化温度"""
        if self._mean is not None:
            return data * self._std[0] + self._mean[0]
        return data

    def _exponential_smoothing(self, series: np.ndarray, alpha: float = 0.3) -> np.ndarray:
        """指数平滑"""
        result = np.zeros_like(series)
        result[0] = series[0]
        for i in range(1, len(series)):
            result[i] = alpha * series[i] + (1 - alpha) * result[i - 1]
        return result

    def _holt_winters(self, series: np.ndarray, alpha: float = 0.3,
                      beta: float = 0.1, gamma: float = 0.1,
                      period: int = 12) -> np.ndarray:
        """
        Holt-Winters 三指数平滑
        返回未来 horizon 步预测
        """
        n = len(series)
        if n < period * 2:
            # 数据太少，用简单线性趋势
            return self._simple_trend(series)

        # 初始化
        level = series[0]
        trend = (series[period] - series[0]) / period
        seasonal = np.zeros(period)
        for i in range(period):
            seasonal[i] = series[i] - level

        # 拟合历史
        smoothed = np.zeros(n)
        for i in range(n):
            s_idx = i % period
            val = series[i]
            last_level = level
            level = alpha * (val - seasonal[s_idx]) + (1 - alpha) * (level + trend)
            trend = beta * (level - last_level) + (1 - beta) * trend
            seasonal[s_idx] = gamma * (val - level) + (1 - gamma) * seasonal[s_idx]
            smoothed[i] = level + trend + seasonal[s_idx]

        # 预测未来
        predictions = np.zeros(self.horizon)
        for i in range(self.horizon):
            s_idx = (n + i) % period
            predictions[i] = level + (i + 1) * trend + seasonal[s_idx]

        return predictions

    def _simple_trend(self, series: np.ndarray) -> np.ndarray:
        """简单线性趋势预测"""
        n = len(series)
        smoothed = self._exponential_smoothing(series)
        # 用最后10个点拟合趋势
        recent = smoothed[-min(20, n):]
        t = np.arange(len(recent))
        coeffs = np.polyfit(t, recent, 1)  # 线性拟合
        slope = coeffs[0]
        last_val = smoothed[-1]

        predictions = np.zeros(self.horizon)
        for i in range(self.horizon):
            predictions[i] = last_val + slope * (i + 1) * 0.7  # 阻尼因子
        return predictions

    def _detect_pattern(self, series: np.ndarray) -> str:
        """检测数据模式"""
        n = len(series)
        if n < 30:
            return "simple"

        # 检查是否有周期性
        acf = np.correlate(series - series.mean(), series - series.mean(), mode='full')
        acf = acf[n - 1:] / acf[n - 1]
        if n > 20:
            peaks = 0
            for lag in range(6, min(25, n)):
                if acf[lag] > 0.3 and acf[lag] > acf[lag - 1] and acf[lag] > acf[lag + 1]:
                    peaks += 1
            if peaks > 0:
                return "seasonal"

        # 检查趋势
        early = series[:n // 3].mean()
        late = series[-n // 3:].mean()
        if abs(late - early) > series.std():
            return "trend"

        return "simple"

    def predict(self, window_data: np.ndarray) -> dict:
        """
        预测未来温度
        window_data: (window_size, input_dim)
        """
        # 提取温度序列
        temp_series = window_data[:, 0]

        # 检测数据模式
        pattern = self._detect_pattern(temp_series)

        if pattern == "seasonal" and len(temp_series) >= self._seasonal_period * 2:
            predictions = self._holt_winters(temp_series, period=self._seasonal_period)
            method = "holt_winters"
        elif pattern == "trend":
            predictions = self._simple_trend(temp_series)
            method = "linear_trend"
        else:
            predictions = self._simple_trend(temp_series)
            method = "exponential_smoothing"

        # 裁剪到合理范围
        predictions = np.clip(predictions, -30, 50)

        # 置信区间（基于预测距离 + 历史波动）
        hist_std = temp_series[-30:].std() if len(temp_series) >= 30 else 0.5
        upper = np.zeros(self.horizon)
        lower = np.zeros(self.horizon)
        for i in range(self.horizon):
            uncertainty = hist_std * np.sqrt(i + 1) * 1.96
            upper[i] = predictions[i] + uncertainty
            lower[i] = predictions[i] - uncertainty

        # 评估风险等级
        max_pred = predictions.max()
        if max_pred > 15:
            risk_level = "critical"
        elif max_pred > 8:
            risk_level = "warning"
        elif predictions[-1] > 5:
            risk_level = "warning"
        else:
            risk_level = "normal"

        return {
            "predictions": predictions.round(2).tolist(),
            "confidence_upper": upper.round(2).tolist(),
            "confidence_lower": lower.round(2).tolist(),
            "risk_level": risk_level,
            "method": method,
        }

    def save(self, path: str):
        config = {
            "input_dim": self.input_dim,
            "window_size": self.window_size,
            "horizon": self.horizon,
            "mean": self._mean,
            "std": self._std,
            "seasonal_period": self._seasonal_period,
        }
        with open(path, "wb") as f:
            pickle.dump(config, f)
        print(f"[NumPy温度预测] 配置已保存至 {path}")

    def load(self, path: str) -> bool:
        try:
            with open(path, "rb") as f:
                config = pickle.load(f)
            self._mean = config.get("mean")
            self._std = config.get("std")
            self._seasonal_period = config.get("seasonal_period", 12)
            print(f"[NumPy温度预测] 配置已加载: {path}")
            return True
        except (FileNotFoundError, KeyError):
            return False


def generate_temperature_data(num_samples: int = 20000) -> np.ndarray:
    """生成模拟温度数据"""
    np.random.seed(42)
    data = []
    temp = 4.0
    for i in range(num_samples):
        if i % 500 == 0 and i > 0:
            temp += np.random.uniform(1, 3)
        elif temp > 6:
            temp -= np.random.uniform(0.1, 0.3)
        else:
            temp += np.random.normal(0, 0.1)
        temp = np.clip(temp, -2, 12)

        external_temp = 25 + 5 * np.sin(i * 0.01) + np.random.normal(0, 1)
        humidity = 75 + np.random.normal(0, 3)
        door = 1 if np.random.random() < 0.03 else 0
        vibration = abs(np.random.normal(0, 0.2))
        cooling_power = max(0, (external_temp - temp) / external_temp) if external_temp > 0 else 0

        data.append([temp, humidity, external_temp, door, vibration, cooling_power])
    return np.array(data, dtype=np.float32)


if __name__ == "__main__":
    print("=" * 50)
    print("NumPy 温度预测模型测试")
    print("=" * 50)

    data = generate_temperature_data(5000)
    predictor = NumpyTemperaturePredictor(input_dim=6, window_size=60, horizon=30)

    # 测试预测
    window = data[-60:]
    result = predictor.predict(window)
    print(f"预测方法: {result['method']}")
    print(f"预测未来30分钟: {result['predictions'][:5]}...")
    print(f"风险等级: {result['risk_level']}")
    print(f"置信区间: {result['confidence_lower'][-1]:.1f} ~ {result['confidence_upper'][-1]:.1f}")

    predictor.save("temperature_predictor_np.pkl")
    print("\n配置已保存!")
