"""
LSTM 时序异常检测模型
基于滑动窗口的 LSTM 自编码器，通过重构误差检测异常
"""
import torch
import torch.nn as nn
import numpy as np
from typing import Tuple, Optional
from dataclasses import dataclass
import json


class LSTMAutoEncoder(nn.Module):
    """LSTM 自编码器用于异常检测"""

    def __init__(self, input_dim: int = 5, hidden_dim: int = 64,
                 num_layers: int = 2, latent_dim: int = 16):
        super().__init__()

        # 编码器
        self.encoder_lstm = nn.LSTM(
            input_dim, hidden_dim, num_layers,
            batch_first=True, dropout=0.2
        )
        self.encoder_fc = nn.Linear(hidden_dim, latent_dim)

        # 解码器
        self.decoder_fc = nn.Linear(latent_dim, hidden_dim)
        self.decoder_lstm = nn.LSTM(
            hidden_dim, hidden_dim, num_layers,
            batch_first=True, dropout=0.2
        )
        self.output_fc = nn.Linear(hidden_dim, input_dim)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        x: (batch, seq_len, input_dim)
        返回: (重构, 潜在表示)
        """
        # 编码
        lstm_out, (hidden, _) = self.encoder_lstm(x)
        latent = self.encoder_fc(lstm_out[:, -1, :])  # 取最后时刻

        # 解码
        decoded = self.decoder_fc(latent)
        decoded = decoded.unsqueeze(1).repeat(1, x.size(1), 1)
        lstm_out, _ = self.decoder_lstm(decoded)
        reconstructed = self.output_fc(lstm_out)

        return reconstructed, latent

    def compute_anomaly_score(self, x: torch.Tensor) -> torch.Tensor:
        """计算异常分数（重构误差）"""
        reconstructed, _ = self.forward(x)
        # MSE 每个样本的平均重构误差
        error = torch.mean((x - reconstructed) ** 2, dim=(1, 2))
        return error


@dataclass
class AnomalyResult:
    """异常检测结果"""
    is_anomaly: bool
    score: float
    threshold: float
    device_id: str
    timestamp: str


class AnomalyDetector:
    """异常检测器封装"""

    def __init__(
        self,
        input_dim: int = 5,
        window_size: int = 60,
        hidden_dim: int = 64,
        num_layers: int = 2,
        threshold_percentile: float = 99.0,
        model_path: Optional[str] = None,
    ):
        self.input_dim = input_dim
        self.window_size = window_size
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.threshold_percentile = threshold_percentile

        self.model = LSTMAutoEncoder(input_dim, hidden_dim, num_layers)
        self.threshold: float = 0.5
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self._device)

        if model_path:
            self.load(model_path)

    def preprocess(self, data: np.ndarray) -> torch.Tensor:
        """预处理：标准化 + 转为 tensor"""
        if data.ndim == 1:
            data = data.reshape(-1, 1)

        # 简单 MinMax 标准化
        data_min = data.min(axis=0, keepdims=True)
        data_max = data.max(axis=0, keepdims=True)
        data_range = data_max - data_min
        data_range[data_range == 0] = 1
        normalized = (data - data_min) / data_range

        return torch.FloatTensor(normalized).unsqueeze(0).to(self._device)

    def detect(self, window_data: np.ndarray) -> AnomalyResult:
        """
        检测异常
        window_data: shape (window_size, input_dim)
        """
        self.model.eval()
        with torch.no_grad():
            x = self.preprocess(window_data)
            scores = self.model.compute_anomaly_score(x)
            score = scores.item()

        is_anomaly = score > self.threshold

        return AnomalyResult(
            is_anomaly=is_anomaly,
            score=round(score, 6),
            threshold=round(self.threshold, 6),
            device_id="",
            timestamp="",
        )

    def calibrate_threshold(self, normal_data: np.ndarray):
        """用正常数据校准阈值"""
        self.model.eval()
        scores = []

        with torch.no_grad():
            for i in range(0, len(normal_data) - self.window_size, self.window_size // 2):
                window = normal_data[i:i + self.window_size]
                if len(window) < self.window_size:
                    break
                x = self.preprocess(window)
                score = self.model.compute_anomaly_score(x)
                scores.append(score.item())

        if scores:
            self.threshold = float(np.percentile(scores, self.threshold_percentile))
            print(f"[异常检测] 阈值校准完成: {self.threshold:.6f} "
                  f"(百分位: {self.threshold_percentile}%)")

    def save(self, path: str):
        """保存模型"""
        torch.save({
            "model_state_dict": self.model.state_dict(),
            "threshold": self.threshold,
            "config": {
                "input_dim": self.input_dim,
                "window_size": self.window_size,
                "hidden_dim": self.hidden_dim,
                "num_layers": self.num_layers,
            },
        }, path)
        print(f"[异常检测] 模型已保存至 {path}")

    def load(self, path: str):
        """加载模型"""
        try:
            checkpoint = torch.load(path, map_location=self._device)
            self.model.load_state_dict(checkpoint["model_state_dict"])
            self.threshold = checkpoint.get("threshold", 0.5)
            print(f"[异常检测] 模型已加载: {path}")
        except FileNotFoundError:
            print(f"[异常检测] 模型文件不存在: {path}，将使用未训练的模型")

    def train(self, train_data: np.ndarray, val_data: Optional[np.ndarray] = None,
              epochs: int = 50, batch_size: int = 32, lr: float = 0.001):
        """训练模型"""
        self.model.train()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)
        criterion = nn.MSELoss()

        # 准备训练数据
        windows = []
        for i in range(0, len(train_data) - self.window_size):
            windows.append(train_data[i:i + self.window_size])
        windows = np.array(windows)

        dataset = torch.FloatTensor(windows).to(self._device)
        n_samples = len(dataset)

        print(f"[训练] 样本数: {n_samples}, 窗口大小: {self.window_size}")

        for epoch in range(epochs):
            epoch_loss = 0.0
            n_batches = 0

            for i in range(0, n_samples, batch_size):
                batch = dataset[i:i + batch_size]
                if len(batch) < 2:
                    continue

                optimizer.zero_grad()
                reconstructed, _ = self.model(batch)
                loss = criterion(reconstructed, batch)
                loss.backward()
                optimizer.step()

                epoch_loss += loss.item()
                n_batches += 1

            if n_batches > 0 and (epoch + 1) % 10 == 0:
                avg_loss = epoch_loss / n_batches
                print(f"Epoch {epoch + 1}/{epochs}, Loss: {avg_loss:.6f}")

        # 校准阈值
        self.calibrate_threshold(train_data[:5000])


def generate_training_data(num_samples: int = 10000) -> np.ndarray:
    """生成模拟训练数据"""
    np.random.seed(42)

    # 模拟正常冷链温度数据
    # 特征: [温度, 湿度, 外部温度, 车门状态, 振动]
    data = []

    for _ in range(num_samples):
        # 基础温度在 2-8 度之间波动
        base_temp = np.random.choice([4, -18, 20])  # 冷藏/冷冻/恒温
        temp = base_temp + np.random.normal(0, 0.5)
        humidity = 70 + np.random.normal(0, 5)
        external_temp = 25 + np.random.normal(0, 3)
        door = np.random.choice([0, 1], p=[0.95, 0.05])
        vibration = abs(np.random.normal(0, 0.2))

        data.append([temp, humidity, external_temp, door, vibration])

    return np.array(data, dtype=np.float32)


def generate_anomaly_data(num_samples: int = 1000) -> np.ndarray:
    """生成包含异常的训练数据"""
    np.random.seed(123)

    data = []
    for _ in range(num_samples):
        is_anomaly = np.random.random() < 0.02

        if is_anomaly:
            # 异常模式
            anomaly_type = np.random.choice(["spike", "drift", "oscillation"])
            if anomaly_type == "spike":
                temp = np.random.uniform(15, 30)
            elif anomaly_type == "drift":
                temp = 4 + np.random.uniform(5, 15)
            else:
                temp = 4 + 5 * np.sin(_ * 0.1)
            humidity = np.random.uniform(90, 100)
        else:
            temp = 4 + np.random.normal(0, 0.5)
            humidity = 70 + np.random.normal(0, 5)

        data.append([
            temp,
            humidity,
            25 + np.random.normal(0, 3),
            np.random.choice([0, 1], p=[0.95, 0.05]),
            abs(np.random.normal(0, 0.2)),
        ])

    return np.array(data, dtype=np.float32)


if __name__ == "__main__":
    # 训练示例
    print("=" * 50)
    print("LSTM 异常检测模型训练")
    print("=" * 50)

    # 生成训练数据
    train_data = generate_training_data(20000)
    print(f"训练数据形状: {train_data.shape}")

    # 创建并训练模型
    detector = AnomalyDetector(
        input_dim=5,
        window_size=60,
        threshold_percentile=99.0,
    )

    detector.train(train_data, epochs=30)

    # 测试异常检测
    print("\n--- 异常检测测试 ---")
    normal_data = generate_training_data(200)
    anomaly_data = generate_anomaly_data(200)

    # 检测正常数据
    window = normal_data[:60]
    result = detector.detect(window)
    print(f"正常数据: score={result.score:.6f}, is_anomaly={result.is_anomaly}")

    # 检测异常数据
    window = anomaly_data[:60]
    result = detector.detect(window)
    print(f"异常数据: score={result.score:.6f}, is_anomaly={result.is_anomaly}")

    # 保存模型
    detector.save("lstm_anomaly_detector.pt")
    print("\n模型已保存!")
