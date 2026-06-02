-- ============================================================
-- 冷链物流智能监控平台 — 数据库初始化 DDL 脚本
-- ============================================================

-- ============================================================
-- 表 1：传感器实时采集数据（时序表 — TDengine 超级表）
-- ============================================================
-- 注意：TDengine 建表通过 tdengine_service.py 自动执行，
-- 此 DDL 仅作为参考文档。实际执行逻辑见 app/services/tdengine_service.py

-- CREATE DATABASE IF NOT EXISTS coldchain KEEP 180 DURATION 10 BUFFER 256;
-- USE coldchain;

-- CREATE STABLE IF NOT EXISTS sensor_data (
--     ts            TIMESTAMP,      -- 数据采集上传时间
--     temperature   FLOAT,          -- 实时采集环境温度（℃）
--     target_temp   FLOAT,          -- 目标设定温度（℃）
--     humidity      FLOAT,          -- 实时采集环境湿度（%RH）
--     latitude      FLOAT,          -- GPS 纬度
--     longitude     FLOAT,          -- GPS 经度
--     vehicle_speed FLOAT,          -- 车辆行驶速度（km/h）
--     door_status   INT,            -- 车门状态：0关闭，1开启
--     vibration     FLOAT,          -- 振动加速度幅值（g）
--     data_quality  FLOAT,          -- 数据质量评分（0~1）
--     battery_level FLOAT,          -- 传感器电池电量（%）
--     signal_strength INT,          -- 设备信号强度（dBm）
--     cold_car_status INT,          -- 冷机运行状态：0故障，1正常运行
--     external_temp FLOAT,          -- 外部环境温度（℃）
--     waybill_no    BINARY(64)      -- 关联订单运单唯一编号
-- ) TAGS (
--     device_id     BINARY(20),     -- 冷链设备唯一编码
--     device_type   BINARY(10)      -- 设备类型：vehicle/cold_room/freezer
-- );

-- 子表示例（按设备创建）：
-- CREATE TABLE IF NOT EXISTS sensor_veh_0001 USING sensor_data TAGS ('VEH-0001', 'vehicle');


-- ============================================================
-- 表 2：设备台账信息（PostgreSQL）
-- ============================================================
CREATE TABLE IF NOT EXISTS devices (
    id                    SERIAL PRIMARY KEY,
    device_id             VARCHAR(20)    NOT NULL UNIQUE,   -- 设备唯一编码
    device_name           VARCHAR(100)   NOT NULL,          -- 设备名称
    device_type           SMALLINT       NOT NULL DEFAULT 1, -- 1冷藏车 2冷库 3冷柜
    zone_id               VARCHAR(20),                      -- 所属区域/园区编码
    cargo_category        SMALLINT,                         -- 1冷冻食品 2冷藏生鲜 3疫苗医药 4化工制剂 5其他
    temp_lower_limit      FLOAT          NOT NULL,          -- 温控下限阈值（℃）
    temp_upper_limit      FLOAT          NOT NULL,          -- 温控上限阈值（℃）
    humidity_lower_limit  FLOAT,                            -- 湿度下限阈值（%RH）
    humidity_upper_limit  FLOAT,                            -- 湿度上限阈值（%RH）
    install_date          DATE           NOT NULL DEFAULT CURRENT_DATE,  -- 安装/注册日期
    last_maintenance_date DATE,                             -- 最近一次维护日期
    status                SMALLINT       NOT NULL DEFAULT 1, -- 0停用 1正常在线 2离线 3故障
    remark                TEXT,                             -- 备注说明
    created_at            TIMESTAMP      NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMP      NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  devices IS '设备台账信息';
COMMENT ON COLUMN devices.device_id   IS '设备唯一编码';
COMMENT ON COLUMN devices.device_name IS '设备名称（如沪A-12345冷藏车、浦东3号冷库）';
COMMENT ON COLUMN devices.device_type IS '设备类型：1冷藏车，2冷库，3冷柜';
COMMENT ON COLUMN devices.zone_id     IS '所属区域/园区编码';
COMMENT ON COLUMN devices.cargo_category IS '承运货物品类：1冷冻食品，2冷藏生鲜，3疫苗医药，4化工制剂，5其他';
COMMENT ON COLUMN devices.temp_lower_limit IS '温控下限阈值（℃）';
COMMENT ON COLUMN devices.temp_upper_limit IS '温控上限阈值（℃）';
COMMENT ON COLUMN devices.humidity_lower_limit IS '湿度下限阈值（%RH）';
COMMENT ON COLUMN devices.humidity_upper_limit IS '湿度上限阈值（%RH）';
COMMENT ON COLUMN devices.install_date IS '设备安装/注册日期';
COMMENT ON COLUMN devices.last_maintenance_date IS '最近一次维护日期';
COMMENT ON COLUMN devices.status IS '设备状态：0停用，1正常在线，2离线，3故障';

CREATE INDEX idx_devices_type   ON devices(device_type);
CREATE INDEX idx_devices_zone   ON devices(zone_id);
CREATE INDEX idx_devices_status ON devices(status);


-- ============================================================
-- 表 3：告警事件记录（PostgreSQL 主存储，TDengine 同步时序写入）
-- ============================================================
CREATE TABLE IF NOT EXISTS alert_events (
    id              SERIAL PRIMARY KEY,
    alert_id        VARCHAR(36)    NOT NULL UNIQUE,         -- 告警事件唯一标识（UUID）
    device_id       VARCHAR(20)    NOT NULL,                -- 触发告警的设备ID
    alarm_type      SMALLINT       NOT NULL,                -- 1温度越限 2湿度越限 3车门超时开启 4冷机故障 5设备离线 6振动异常 7数据质量异常 8温度骤变
    alarm_level     SMALLINT       NOT NULL DEFAULT 1,      -- 1一般 2严重 3紧急
    alert_message   TEXT           NOT NULL,                -- 告警描述文本
    sensor_value    FLOAT          NOT NULL,                -- 告警触发时刻传感器实际读数
    threshold_value FLOAT          NOT NULL,                -- 触发告警的阈值边界值
    alert_time      TIMESTAMP      NOT NULL,                -- 告警触发时间
    handler         VARCHAR(50),                            -- 处置人姓名/工号
    handle_time     TIMESTAMP,                              -- 确认处置时间
    handle_result   SMALLINT,                               -- 1已恢复 2误报消除 3转维修 4待跟进
    handle_remark   TEXT,                                   -- 处置备注
    resolved_time   TIMESTAMP,                              -- 告警解决/关闭时间
    created_at      TIMESTAMP      NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  alert_events IS '告警事件记录';
COMMENT ON COLUMN alert_events.alert_id    IS '告警事件唯一标识';
COMMENT ON COLUMN alert_events.device_id   IS '触发告警的设备ID';
COMMENT ON COLUMN alert_events.alarm_type  IS '异常预警类型编码：1温度越限，2湿度越限，3车门超时开启，4冷机故障，5设备离线，6振动异常，7数据质量异常，8温度骤变';
COMMENT ON COLUMN alert_events.alarm_level IS '预警等级：1一般，2严重，3紧急';
COMMENT ON COLUMN alert_events.alert_message IS '告警描述文本';
COMMENT ON COLUMN alert_events.sensor_value IS '告警触发时刻传感器实际读数';
COMMENT ON COLUMN alert_events.threshold_value IS '触发告警的阈值边界值';
COMMENT ON COLUMN alert_events.alert_time IS '告警触发时间';
COMMENT ON COLUMN alert_events.handler IS '处置人姓名/工号';
COMMENT ON COLUMN alert_events.handle_time IS '确认处置时间';
COMMENT ON COLUMN alert_events.handle_result IS '处置结果：1已恢复，2误报消除，3转维修，4待跟进';
COMMENT ON COLUMN alert_events.handle_remark IS '处置备注（如现场照片描述）';
COMMENT ON COLUMN alert_events.resolved_time IS '告警解决/关闭时间';

CREATE INDEX idx_alert_device   ON alert_events(device_id);
CREATE INDEX idx_alert_time     ON alert_events(alert_time DESC);
CREATE INDEX idx_alert_level    ON alert_events(alarm_level);
CREATE INDEX idx_alert_type     ON alert_events(alarm_type);


-- ============================================================
-- 表 4：温控预测结果（PostgreSQL 持久化，Redis 缓存热数据）
-- ============================================================
CREATE TABLE IF NOT EXISTS temperature_predictions (
    id               SERIAL PRIMARY KEY,
    prediction_id    VARCHAR(36)    NOT NULL UNIQUE,        -- 预测记录唯一标识（UUID）
    device_id        VARCHAR(20)    NOT NULL,               -- 目标设备ID
    predict_time     TIMESTAMP      NOT NULL,               -- 模型推理生成时间
    horizon_minutes  SMALLINT       NOT NULL DEFAULT 30,    -- 预测时间窗口长度（分钟）
    predicted_values JSONB          NOT NULL,               -- 未来每分钟温度预测值序列 [float,...]
    confidence_upper JSONB          NOT NULL,               -- 置信区间上界序列
    confidence_lower JSONB          NOT NULL,               -- 置信区间下界序列
    risk_level       SMALLINT       NOT NULL DEFAULT 0,     -- 0安全 1低风险 2中风险 3高风险
    created_at       TIMESTAMP      NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  temperature_predictions IS '温控预测结果';
COMMENT ON COLUMN temperature_predictions.prediction_id   IS '预测记录唯一标识';
COMMENT ON COLUMN temperature_predictions.device_id       IS '目标设备ID';
COMMENT ON COLUMN temperature_predictions.predict_time    IS '模型推理生成时间';
COMMENT ON COLUMN temperature_predictions.horizon_minutes IS '预测时间窗口长度（分钟）';
COMMENT ON COLUMN temperature_predictions.predicted_values IS '未来每分钟温度预测值序列';
COMMENT ON COLUMN temperature_predictions.confidence_upper IS '置信区间上界序列';
COMMENT ON COLUMN temperature_predictions.confidence_lower IS '置信区间下界序列';
COMMENT ON COLUMN temperature_predictions.risk_level      IS '越限风险等级：0安全，1低风险，2中风险，3高风险';

CREATE INDEX idx_pred_device ON temperature_predictions(device_id);
CREATE INDEX idx_pred_time   ON temperature_predictions(predict_time DESC);


-- ============================================================
-- 插入默认设备数据（示例，用于开发测试）
-- ============================================================
INSERT INTO devices (device_id, device_name, device_type, zone_id, cargo_category,
                     temp_lower_limit, temp_upper_limit, humidity_lower_limit, humidity_upper_limit,
                     install_date, status, remark)
VALUES
    ('VEH-0001', '京A12345 冷藏车', 1, 'ZONE-01', 2, -22, -15, 75, 90, '2025-01-15', 1, '冷冻肉类运输'),
    ('VEH-0002', '京A23456 冷藏车', 1, 'ZONE-01', 3,   2,   8, 40, 60, '2025-01-20', 1, '疫苗医药运输'),
    ('COLD-0001', '浦东1号冷库', 2, 'ZONE-02', 1, -25, -18, 80, 95, '2025-02-01', 1, '冷冻海鲜存储'),
    ('COLD-0002', '浦东2号冷库', 2, 'ZONE-02', 2,   3,   8, 85, 95, '2025-02-01', 1, '冷藏水果存储'),
    ('FREEZ-0001', '前置冷柜A1', 3, 'ZONE-03', 1, -22, -15, 75, 90, '2025-03-01', 1, '社区前置冷冻柜')
ON CONFLICT (device_id) DO NOTHING;
