"""
LSTM/Transformer 温控趋势预测模型
预测未来 30 分钟温度变化趋势
"""
import torch
import torch.nn as nn
import numpy as np
from typing import Optional, Tuple
import math


class PositionalEncoding(nn.Module):
    """Transformer 位置编码"""

    def __init__(self, d_model: int, max_len: int = 500):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len).unsqueeze(1).float()
        div_term = torch.exp(
            torch.arange(0, d_model, 2).float() * -(math.log(10000.0) / d_model)
        )
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer('pe', pe.unsqueeze(0))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.pe[:, :x.size(1)]


class TemperaturePredictor(nn.Module):
    """温度预测模型 - LSTM + Transformer 混合架构"""

    def __init__(
        self,
        input_dim: int = 6,
        hidden_dim: int = 128,
        num_lstm_layers: int = 2,
        num_transformer_layers: int = 2,
        nhead: int = 4,
        dropout: float = 0.2,
        output_horizon: int = 30,  # 预测未来30分钟
    ):
        super().__init__()

        self.output_horizon = output_horizon
        self.input_dim = input_dim

        # 输入投影
        self.input_proj = nn.Linear(input_dim, hidden_dim)

        # LSTM 时序编码
        self.lstm = nn.LSTM(
            hidden_dim, hidden_dim, num_lstm_layers,
            batch_first=True, dropout=dropout,
            bidirectional=True,
        )

        # Transformer 编码
        self.pos_encoder = PositionalEncoding(hidden_dim * 2)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_dim * 2, nhead=nhead,
            dropout=dropout, batch_first=True,
        )
        self.transformer = nn.TransformerEncoder(
            encoder_layer, num_transformer_layers
        )

        # 输出层
        self.output_fc = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, output_horizon),
        )

        # 置信区间输出
        self.confidence_fc = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, output_horizon * 2),  # upper + lower
        )

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        x: (batch, seq_len, input_dim)
        返回: (预测值, 上界, 下界)
        """
        # 投影
        x_proj = self.input_proj(x)

        # LSTM
        lstm_out, _ = self.lstm(x_proj)  # (batch, seq_len, hidden_dim*2)

        # Transformer
        encoded = self.pos_encoder(lstm_out)
        transformer_out = self.transformer(encoded)

        # 全局池化（取最后时刻 + 平均）
        last_out = transformer_out[:, -1, :]  # (batch, hidden_dim*2)
        mean_out = transformer_out.mean(dim=1)

        combined = (last_out + mean_out) / 2

        # 预测
        predictions = self.output_fc(combined)  # (batch, output_horizon)

        # 置信区间
        conf = self.confidence_fc(combined)
        upper = conf[:, :self.output_horizon]
        lower = conf[:, self.output_horizon:]

        return predictions, upper, lower


class TemperaturePredictionService:
    """温度预测服务封装"""

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

        self.model = TemperaturePredictor(
            input_dim=input_dim,
            output_horizon=horizon,
        )
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self._device)

        # 标准化参数
        self._mean: Optional[np.ndarray] = None
        self._std: Optional[np.ndarray] = None

        if model_path:
            self.load(model_path)

    def fit_scaler(self, data: np.ndarray):
        """拟合标准化参数"""
        self._mean = data.mean(axis=0)
        self._std = data.std(axis=0)
        self._std[self._std == 0] = 1

    def _normalize(self, data: np.ndarray) -> np.ndarray:
        if self._mean is not None:
            return (data - self._mean) / self._std
        return data

    def _denormalize(self, data: np.ndarray, feature_idx: int = 0) -> np.ndarray:
        """反标准化温度特征"""
        if self._mean is not None:
            return data * self._std[feature_idx] + self._mean[feature_idx]
        return data

    def predict(self, window_data: np.ndarray) -> dict:
        """
        预测未来30分钟温度
        window_data: (window_size, input_dim)
        """
        self.model.eval()

        # 预处理
        normalized = self._normalize(window_data)
        x = torch.FloatTensor(normalized).unsqueeze(0).to(self._device)

        with torch.no_grad():
            predictions, upper, lower = self.model(x)

        preds = predictions.squeeze(0).cpu().numpy()
        upper_bound = upper.squeeze(0).cpu().numpy()
        lower_bound = lower.squeeze(0).cpu().numpy()

        # 反标准化
        preds = self._denormalize(preds, 0)
        upper_bound = self._denormalize(upper_bound, 0)
        lower_bound = self._denormalize(lower_bound, 0)

        # 评估风险等级
        max_pred = preds.max()
        if max_pred > 15:
            risk_level = "critical"
        elif max_pred > 8:
            risk_level = "warning"
        else:
            risk_level = "normal"

        return {
            "predictions": preds.round(2).tolist(),
            "confidence_upper": upper_bound.round(2).tolist(),
            "confidence_lower": lower_bound.round(2).tolist(),
            "risk_level": risk_level,
        }

    def save(self, path: str):
        """保存模型"""
        torch.save({
            "model_state_dict": self.model.state_dict(),
            "mean": self._mean,
            "std": self._std,
            "config": {
                "input_dim": self.input_dim,
                "window_size": self.window_size,
                "horizon": self.horizon,
            },
        }, path)
        print(f"[温度预测] 模型已保存至 {path}")

    def load(self, path: str):
        """加载模型"""
        try:
            checkpoint = torch.load(path, map_location=self._device)
            self.model.load_state_dict(checkpoint["model_state_dict"])
            self._mean = checkpoint.get("mean")
            self._std = checkpoint.get("std")
            print(f"[温度预测] 模型已加载: {path}")
        except FileNotFoundError:
            print(f"[温度预测] 模型文件不存在: {path}，将使用未训练的模型")

    def train(self, train_data: np.ndarray, val_data: Optional[np.ndarray] = None,
              epochs: int = 100, batch_size: int = 32, lr: float = 0.001):
        """训练模型"""
        # 拟合标准化
        self.fit_scaler(train_data)
        normalized = self._normalize(train_data)

        self.model.train()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, patience=10, factor=0.5
        )
        pred_criterion = nn.MSELoss()

        # 准备训练数据 (滑动窗口 → 未来值)
        X, y = [], []
        for i in range(len(normalized) - self.window_size - self.horizon):
            X.append(normalized[i:i + self.window_size])
            y.append(normalized[i + self.window_size:i + self.window_size + self.horizon, 0])

        X = torch.FloatTensor(np.array(X)).to(self._device)
        y = torch.FloatTensor(np.array(y)).to(self._device)

        n_samples = len(X)
        print(f"[训练] 样本数: {n_samples}, 窗口: {self.window_size}, 预测: {self.horizon}")

        for epoch in range(epochs):
            epoch_loss = 0.0
            n_batches = 0

            indices = torch.randperm(n_samples)
            for i in range(0, n_samples, batch_size):
                batch_idx = indices[i:i + batch_size]
                batch_X = X[batch_idx]
                batch_y = y[batch_idx]

                optimizer.zero_grad()
                preds, upper, lower = self.model(batch_X)
                loss = pred_criterion(preds, batch_y)
                loss.backward()
                optimizer.step()

                epoch_loss += loss.item()
                n_batches += 1

            if n_batches > 0:
                avg_loss = epoch_loss / n_batches
                scheduler.step(avg_loss)

                if (epoch + 1) % 20 == 0:
                    print(f"Epoch {epoch + 1}/{epochs}, Loss: {avg_loss:.6f}")


def generate_temperature_data(num_samples: int = 20000) -> np.ndarray:
    """生成模拟温度训练数据"""
    np.random.seed(42)

    # 特征: [温度, 湿度, 外部温度, 车门状态, 振动, 制冷功率]
    data = []
    temp = 4.0

    for i in range(num_samples):
        # 温度变化模拟
        if i % 500 == 0:
            # 周期性开门卸货导致温度波动
            temp += np.random.uniform(1, 3)
        elif temp > 6:
            temp -= np.random.uniform(0.1, 0.3)  # 制冷降温
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
    print("温度预测模型训练")
    print("=" * 50)

    # 生成训练数据
    train_data = generate_temperature_data(30000)
    print(f"训练数据形状: {train_data.shape}")

    # 创建并训练模型
    predictor = TemperaturePredictionService(
        input_dim=6,
        window_size=60,
        horizon=30,
    )

    predictor.train(train_data, epochs=50)

    # 测试预测
    print("\n--- 预测测试 ---")
    test_window = train_data[-60:]
    result = predictor.predict(test_window)

    print(f"预测未来30分钟温度: {result['predictions'][:5]}...")
    print(f"风险等级: {result['risk_level']}")
    print(f"温度范围: {result['confidence_lower'][-1]:.1f} ~ {result['confidence_upper'][-1]:.1f}")

    # 保存模型
    predictor.save("lstm_temperature_predictor.pt")
    print("\n模型已保存!")
