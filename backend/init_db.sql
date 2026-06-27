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
-- 表 5：产品品类字典表（PostgreSQL）
-- ============================================================
CREATE TABLE IF NOT EXISTS product_categories (
    id                  SERIAL PRIMARY KEY,
    product_key         VARCHAR(50)    NOT NULL UNIQUE,   -- 产品唯一标识键
    product_name        VARCHAR(100)   NOT NULL,          -- 产品名称（中文）
    category            VARCHAR(20)    NOT NULL,          -- 品类：水果、蔬菜、肉类、海鲜、乳制品、豆制品、蛋类、其他
    freshness_days      INTEGER        NOT NULL DEFAULT 7,-- 保鲜期天数
    temp_min            FLOAT          DEFAULT NULL,      -- 最低存储温度（℃）
    temp_max            FLOAT          DEFAULT NULL,      -- 最高存储温度（℃）
    humidity_min        FLOAT          DEFAULT NULL,      -- 最低存储湿度（%）
    humidity_max        FLOAT          DEFAULT NULL,      -- 最高存储湿度（%）
    indicators          TEXT[]         DEFAULT '{}'::text[],  -- 品质指标列表
    is_active           BOOLEAN        NOT NULL DEFAULT TRUE,  -- 是否启用
    created_at          TIMESTAMP      NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP      NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  product_categories IS '产品品类字典表';
COMMENT ON COLUMN product_categories.product_key IS '产品唯一标识键';
COMMENT ON COLUMN product_categories.product_name IS '产品名称（中文）';
COMMENT ON COLUMN product_categories.category IS '品类：水果、蔬菜、肉类、海鲜、乳制品、豆制品、蛋类、医药制品、花卉、冷冻食品、熟食预制菜、饮料、其他';
COMMENT ON COLUMN product_categories.freshness_days IS '保鲜期天数';
COMMENT ON COLUMN product_categories.temp_min IS '最低存储温度（℃）';
COMMENT ON COLUMN product_categories.temp_max IS '最高存储温度（℃）';
COMMENT ON COLUMN product_categories.humidity_min IS '最低存储湿度（%）';
COMMENT ON COLUMN product_categories.humidity_max IS '最高存储湿度（%）';
COMMENT ON COLUMN product_categories.indicators IS '品质指标列表';

CREATE INDEX idx_product_category ON product_categories(category);
CREATE INDEX idx_product_name ON product_categories(product_name);
CREATE INDEX idx_product_key ON product_categories(product_key);

-- ============================================================
-- 表 6：生鲜品质评估记录（PostgreSQL）
-- ============================================================
CREATE TABLE IF NOT EXISTS quality_assessments (
    id                  SERIAL PRIMARY KEY,
    assessment_id       VARCHAR(36)    NOT NULL UNIQUE,   -- 评估记录唯一标识（UUID）
    product_key         VARCHAR(50)    NOT NULL,          -- 产品标识键
    product_name        VARCHAR(100)   NOT NULL,          -- 产品名称
    category            VARCHAR(20)    NOT NULL,          -- 品类
    image_path          VARCHAR(500),                     -- 评估图片路径
    quality_score       FLOAT          NOT NULL,          -- 品质评分（0-100）
    grade               VARCHAR(20)    NOT NULL,          -- 等级：S级(特优)/A级(优)/B级(良好)/C级(合格)/D级(不合格)
    defects             TEXT[]         DEFAULT '{}'::text[],  -- 缺陷列表
    confidence          FLOAT          NOT NULL,          -- 置信度（0-1）
    description         TEXT,                             -- 描述
    storage_days        INTEGER        DEFAULT 0,         -- 存储天数
    storage_avg_temp    FLOAT          DEFAULT NULL,      -- 平均存储温度（℃）
    remaining_shelf_life FLOAT         DEFAULT NULL,      -- 剩余保质期（天）
    recommendation      TEXT,                             -- 建议
    assessed_by         VARCHAR(50),                      -- 评估人
    assessed_at         TIMESTAMP      NOT NULL DEFAULT NOW(),
    created_at          TIMESTAMP      NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  quality_assessments IS '生鲜品质评估记录';
COMMENT ON COLUMN quality_assessments.assessment_id IS '评估记录唯一标识';
COMMENT ON COLUMN quality_assessments.product_key IS '产品标识键';
COMMENT ON COLUMN quality_assessments.product_name IS '产品名称';
COMMENT ON COLUMN quality_assessments.category IS '品类';
COMMENT ON COLUMN quality_assessments.image_path IS '评估图片路径';
COMMENT ON COLUMN quality_assessments.quality_score IS '品质评分（0-100）';
COMMENT ON COLUMN quality_assessments.grade IS '等级';
COMMENT ON COLUMN quality_assessments.defects IS '缺陷列表';
COMMENT ON COLUMN quality_assessments.confidence IS '置信度（0-1）';
COMMENT ON COLUMN quality_assessments.description IS '描述';
COMMENT ON COLUMN quality_assessments.storage_days IS '存储天数';
COMMENT ON COLUMN quality_assessments.storage_avg_temp IS '平均存储温度（℃）';
COMMENT ON COLUMN quality_assessments.remaining_shelf_life IS '剩余保质期（天）';
COMMENT ON COLUMN quality_assessments.recommendation IS '建议';

CREATE INDEX idx_assessment_product ON quality_assessments(product_key);
CREATE INDEX idx_assessment_category ON quality_assessments(category);
CREATE INDEX idx_assessment_grade ON quality_assessments(grade);
CREATE INDEX idx_assessment_date ON quality_assessments(assessed_at DESC);

-- ============================================================
-- 插入产品品类数据（所有品类均包含合理数据）
-- ============================================================
INSERT INTO product_categories (product_key, product_name, category, freshness_days, temp_min, temp_max, humidity_min, humidity_max, indicators) VALUES
-- 水果品类（34种）
('apple', '苹果', '水果', 60, 0, 4, 85, 95, ARRAY['色泽', '硬度', '表皮完整度', '损伤程度']),
('strawberry', '草莓', '水果', 5, 0, 2, 90, 95, ARRAY['色泽', '硬度', '腐烂程度', '表皮完整度']),
('grape', '葡萄', '水果', 14, 0, 4, 85, 95, ARRAY['色泽', '硬度', '脱粒程度', '表皮完整度']),
('orange', '橙子', '水果', 45, 4, 8, 85, 95, ARRAY['色泽', '硬度', '表皮完整度', '损伤程度']),
('banana', '香蕉', '水果', 12, 13, 15, 85, 95, ARRAY['色泽', '硬度', '表皮完整度', '损伤程度']),
('watermelon', '西瓜', '水果', 21, 4, 10, 80, 90, ARRAY['色泽', '硬度', '表皮完整度', '损伤程度']),
('pear', '梨', '水果', 60, 0, 4, 85, 95, ARRAY['色泽', '硬度', '表皮完整度', '损伤程度']),
('peach', '桃子', '水果', 7, 0, 2, 90, 95, ARRAY['色泽', '硬度', '表皮完整度', '损伤程度']),
('plum', '李子', '水果', 10, 0, 4, 85, 95, ARRAY['色泽', '硬度', '表皮完整度', '损伤程度']),
('apricot', '杏子', '水果', 7, 0, 2, 90, 95, ARRAY['色泽', '硬度', '表皮完整度', '损伤程度']),
('cherry', '樱桃', '水果', 5, 0, 2, 90, 95, ARRAY['色泽', '硬度', '腐烂程度', '表皮完整度']),
('blueberry', '蓝莓', '水果', 7, 0, 2, 90, 95, ARRAY['色泽', '硬度', '腐烂程度', '表皮完整度']),
('raspberry', '覆盆子', '水果', 3, 0, 2, 90, 95, ARRAY['色泽', '硬度', '腐烂程度', '表皮完整度']),
('mango', '芒果', '水果', 14, 13, 15, 85, 90, ARRAY['色泽', '硬度', '表皮完整度', '损伤程度']),
('durian', '榴莲', '水果', 7, 13, 15, 85, 90, ARRAY['色泽', '硬度', '表皮完整度', '气味']),
('pineapple', '菠萝', '水果', 21, 7, 10, 85, 90, ARRAY['色泽', '硬度', '表皮完整度', '损伤程度']),
('litchi', '荔枝', '水果', 5, 0, 2, 90, 95, ARRAY['色泽', '硬度', '表皮完整度', '损伤程度']),
('longan', '龙眼', '水果', 7, 0, 4, 90, 95, ARRAY['色泽', '硬度', '表皮完整度', '损伤程度']),
('kiwi', '猕猴桃', '水果', 21, 0, 4, 85, 95, ARRAY['色泽', '硬度', '表皮完整度', '损伤程度']),
('pomegranate', '石榴', '水果', 30, 4, 8, 85, 90, ARRAY['色泽', '硬度', '表皮完整度', '损伤程度']),
('dragonfruit', '火龙果', '水果', 14, 7, 10, 85, 90, ARRAY['色泽', '硬度', '表皮完整度', '损伤程度']),
('papaya', '木瓜', '水果', 10, 13, 15, 85, 90, ARRAY['色泽', '硬度', '表皮完整度', '损伤程度']),
('coconut', '椰子', '水果', 30, 15, 20, 80, 90, ARRAY['色泽', '硬度', '表皮完整度', '损伤程度']),
('guava', '番石榴', '水果', 14, 7, 10, 85, 90, ARRAY['色泽', '硬度', '表皮完整度', '损伤程度']),
('avocado', '牛油果', '水果', 10, 7, 13, 85, 90, ARRAY['色泽', '硬度', '成熟度', '表皮完整度']),
('lemon', '柠檬', '水果', 30, 4, 8, 85, 90, ARRAY['色泽', '硬度', '表皮完整度', '损伤程度']),
('lime', '青柠', '水果', 30, 4, 8, 85, 90, ARRAY['色泽', '硬度', '表皮完整度', '损伤程度']),
('passionfruit', '百香果', '水果', 14, 7, 10, 85, 90, ARRAY['色泽', '硬度', '表皮完整度', '损伤程度']),
('cantaloupe', '哈密瓜', '水果', 21, 4, 8, 85, 90, ARRAY['色泽', '硬度', '表皮完整度', '损伤程度']),
('honeydew', '白兰瓜', '水果', 21, 4, 8, 85, 90, ARRAY['色泽', '硬度', '表皮完整度', '损伤程度']),
('fig', '无花果', '水果', 3, 0, 2, 90, 95, ARRAY['色泽', '硬度', '表皮完整度', '损伤程度']),
('date', '枣', '水果', 30, 0, 4, 85, 90, ARRAY['色泽', '硬度', '表皮完整度', '损伤程度']),
('persimmon', '柿子', '水果', 14, 0, 4, 85, 90, ARRAY['色泽', '硬度', '表皮完整度', '损伤程度']),
('mulberry', '桑葚', '水果', 3, 0, 2, 90, 95, ARRAY['色泽', '硬度', '腐烂程度', '表皮完整度']),

-- 蔬菜品类（26种）
('cucumber', '黄瓜', '蔬菜', 10, 0, 4, 90, 95, ARRAY['色泽', '硬度', '表皮完整度', '损伤程度']),
('carrot', '胡萝卜', '蔬菜', 30, 0, 4, 85, 95, ARRAY['色泽', '硬度', '表皮完整度', '根须状态']),
('broccoli', '西兰花', '蔬菜', 7, 0, 2, 90, 95, ARRAY['色泽', '水分状态', '花球完整度', '茎叶状态']),
('celery', '芹菜', '蔬菜', 10, 0, 4, 90, 95, ARRAY['色泽', '水分状态', '茎叶完整性', '损伤程度']),
('potato', '土豆', '蔬菜', 60, 4, 8, 85, 90, ARRAY['色泽', '外观状态', '表皮完整度', '发芽情况']),
('onion', '洋葱', '蔬菜', 45, 0, 4, 85, 90, ARRAY['色泽', '外观状态', '表皮完整度', '发芽情况']),
('garlic', '大蒜', '蔬菜', 90, 0, 4, 60, 70, ARRAY['色泽', '外观状态', '表皮完整度', '发芽情况']),
('greenpepper', '青椒', '蔬菜', 10, 0, 4, 90, 95, ARRAY['色泽', '外观饱满度', '表皮完整度', '成熟度']),
('redpepper', '红椒', '蔬菜', 10, 0, 4, 90, 95, ARRAY['色泽', '外观饱满度', '表皮完整度', '成熟度']),
('eggplant', '茄子', '蔬菜', 10, 0, 4, 90, 95, ARRAY['色泽', '外观饱满度', '表皮完整度', '成熟度']),
('wintermelon', '冬瓜', '蔬菜', 60, 4, 8, 85, 90, ARRAY['色泽', '外观状态', '表皮完整度', '损伤程度']),
('pumpkin', '南瓜', '蔬菜', 60, 4, 8, 85, 90, ARRAY['色泽', '外观状态', '表皮完整度', '损伤程度']),
('cabbage', '白菜', '蔬菜', 21, 0, 4, 90, 95, ARRAY['色泽', '水分状态', '叶片完整性', '黄叶情况']),
('chinese cabbage', '青菜', '蔬菜', 7, 0, 2, 90, 95, ARRAY['色泽', '水分状态', '叶片完整性', '黄叶情况']),
('leek', '韭菜', '蔬菜', 5, 0, 2, 90, 95, ARRAY['色泽', '水分状态', '叶片完整性', '黄叶情况']),
('coriander', '香菜', '蔬菜', 3, 0, 2, 90, 95, ARRAY['色泽', '水分状态', '叶片完整性', '黄叶情况']),
('parsley', '欧芹', '蔬菜', 5, 0, 2, 90, 95, ARRAY['色泽', '水分状态', '叶片完整性', '黄叶情况']),
('basil', '罗勒', '蔬菜', 3, 0, 2, 90, 95, ARRAY['色泽', '水分状态', '叶片完整性', '黄叶情况']),
('lettuce', '生菜', '蔬菜', 7, 0, 2, 90, 95, ARRAY['色泽', '水分状态', '萎蔫程度', '黄叶情况']),
('tomato', '番茄', '蔬菜', 14, 0, 4, 90, 95, ARRAY['色泽', '外观饱满度', '表皮完整性', '成熟度']),
('sweetpotato', '红薯', '蔬菜', 45, 4, 8, 85, 90, ARRAY['色泽', '外观状态', '表皮完整度', '发芽情况']),
('yam', '山药', '蔬菜', 30, 4, 8, 85, 90, ARRAY['色泽', '外观状态', '表皮完整度', '损伤程度']),
('ginger', '生姜', '蔬菜', 60, 0, 4, 60, 70, ARRAY['色泽', '外观状态', '表皮完整度', '发芽情况']),
('shallot', '香葱', '蔬菜', 5, 0, 2, 90, 95, ARRAY['色泽', '水分状态', '叶片完整性', '黄叶情况']),
('spinach', '菠菜', '蔬菜', 5, 0, 2, 90, 95, ARRAY['色泽', '水分状态', '黄叶情况', '萎蔫程度']),
('green bean', '绿豆', '蔬菜', 180, 20, 25, 60, 70, ARRAY['色泽', '外观状态', '发芽情况', '霉变情况']),

-- 肉类品类（16种）
('beef', '牛肉', '肉类', 21, -18, -15, 75, 90, ARRAY['色泽', '肉质紧致度', '脂肪分布', '表面状态']),
('pork', '猪肉', '肉类', 14, -18, -15, 75, 90, ARRAY['色泽', '肉质紧致度', '脂肪分布', '表面状态']),
('lamb', '羊肉', '肉类', 14, -18, -15, 75, 90, ARRAY['色泽', '肉质紧致度', '脂肪分布', '表面状态']),
('chicken', '鸡肉', '肉类', 7, -18, -15, 75, 90, ARRAY['色泽', '肉质紧致度', '表皮完整性', '表面状态']),
('duck', '鸭肉', '肉类', 10, -18, -15, 75, 90, ARRAY['色泽', '肉质紧致度', '表皮完整性', '表面状态']),
('goose', '鹅肉', '肉类', 14, -18, -15, 75, 90, ARRAY['色泽', '肉质紧致度', '表皮完整性', '表面状态']),
('turkey', '火鸡', '肉类', 14, -18, -15, 75, 90, ARRAY['色泽', '肉质紧致度', '表皮完整性', '表面状态']),
('rabbit', '兔肉', '肉类', 7, -18, -15, 75, 90, ARRAY['色泽', '肉质紧致度', '表皮完整性', '表面状态']),
('beef liver', '牛肝', '肉类', 3, -18, -15, 75, 90, ARRAY['色泽', '表面状态', '质地均匀度', '损伤程度']),
('pork liver', '猪肝', '肉类', 3, -18, -15, 75, 90, ARRAY['色泽', '表面状态', '质地均匀度', '损伤程度']),
('chicken liver', '鸡肝', '肉类', 2, -18, -15, 75, 90, ARRAY['色泽', '表面状态', '质地均匀度', '损伤程度']),
('beef tongue', '牛舌', '肉类', 7, -18, -15, 75, 90, ARRAY['色泽', '表面状态', '质地均匀度', '损伤程度']),
('pork belly', '五花肉', '肉类', 7, -18, -15, 75, 90, ARRAY['色泽', '脂肪分布', '肉质紧致度', '表面状态']),
('beef brisket', '牛腩', '肉类', 10, -18, -15, 75, 90, ARRAY['色泽', '脂肪分布', '肉质紧致度', '表面状态']),
('pork chop', '猪排', '肉类', 7, -18, -15, 75, 90, ARRAY['色泽', '肉质紧致度', '表面状态', '损伤程度']),
('chicken breast', '鸡胸肉', '肉类', 5, -18, -15, 75, 90, ARRAY['色泽', '肉质紧致度', '表面状态', '损伤程度']),

-- 海鲜品类（17种）
('salmon', '三文鱼', '海鲜', 7, -20, -18, 80, 90, ARRAY['色泽', '肉质紧致度', '表面状态', '眼清度']),
('shrimp', '虾', '海鲜', 5, -18, -15, 80, 90, ARRAY['色泽', '肉质紧致度', '黑变程度', '表面状态']),
('crab', '螃蟹', '海鲜', 5, -18, -15, 80, 90, ARRAY['色泽', '活力状态', '表面状态', '壳完整度']),
('lobster', '龙虾', '海鲜', 3, -18, -15, 80, 90, ARRAY['色泽', '活力状态', '表面状态', '壳完整度']),
('scallop', '扇贝', '海鲜', 3, -18, -15, 80, 90, ARRAY['色泽', '肉质紧致度', '表面状态', '壳完整度']),
('oyster', '生蚝', '海鲜', 3, 2, 8, 85, 95, ARRAY['活力状态', '表面状态', '壳完整度']),
('clam', '蛤蜊', '海鲜', 3, 2, 8, 85, 95, ARRAY['活力状态', '表面状态', '壳完整度']),
('mussel', '贻贝', '海鲜', 3, 2, 8, 85, 95, ARRAY['活力状态', '表面状态', '壳完整度']),
('squid', '鱿鱼', '海鲜', 3, -18, -15, 80, 90, ARRAY['色泽', '肉质紧致度', '表面状态', '表皮完整度']),
('octopus', '章鱼', '海鲜', 3, -18, -15, 80, 90, ARRAY['色泽', '肉质紧致度', '表面状态', '表皮完整度']),
('cod', '鳕鱼', '海鲜', 7, -20, -18, 80, 90, ARRAY['色泽', '肉质紧致度', '表面状态', '眼清度']),
('tuna', '金枪鱼', '海鲜', 5, -20, -18, 80, 90, ARRAY['色泽', '肉质紧致度', '表面状态', '眼清度']),
('mackerel', '鲭鱼', '海鲜', 3, -18, -15, 80, 90, ARRAY['色泽', '肉质紧致度', '表面状态', '眼清度']),
('herring', '鲱鱼', '海鲜', 3, -18, -15, 80, 90, ARRAY['色泽', '肉质紧致度', '表面状态', '眼清度']),
('tilapia', '罗非鱼', '海鲜', 5, -18, -15, 80, 90, ARRAY['色泽', '肉质紧致度', '表面状态', '眼清度']),
('carp', '鲤鱼', '海鲜', 5, -18, -15, 80, 90, ARRAY['色泽', '肉质紧致度', '表面状态', '眼清度']),
('catfish', '鲶鱼', '海鲜', 5, -18, -15, 80, 90, ARRAY['色泽', '肉质紧致度', '表面状态', '眼清度']),

-- 乳制品品类（8种）
('milk', '鲜奶', '乳制品', 7, 0, 4, 75, 85, ARRAY['色泽', '质地均匀度', '表面洁净度', '包装完整性']),
('yogurt', '酸奶', '乳制品', 14, 0, 4, 75, 85, ARRAY['色泽', '质地均匀度', '表面状态', '包装完整性']),
('cheese', '奶酪', '乳制品', 60, 2, 8, 70, 80, ARRAY['色泽', '质地均匀度', '表面状态', '包装完整性']),
('butter', '黄油', '乳制品', 30, -18, -15, 70, 80, ARRAY['色泽', '质地均匀度', '表面状态', '包装完整性']),
('cream', '奶油', '乳制品', 7, 0, 4, 75, 85, ARRAY['色泽', '质地均匀度', '表面状态', '包装完整性']),
('icecream', '冰淇淋', '乳制品', 30, -22, -18, 75, 85, ARRAY['色泽', '质地均匀度', '融化程度', '包装完整性']),
('milk powder', '奶粉', '乳制品', 365, 20, 25, 40, 60, ARRAY['色泽', '结块程度', '表面状态', '包装完整性']),
('cream cheese', '奶油芝士', '乳制品', 14, 0, 4, 75, 85, ARRAY['色泽', '质地均匀度', '表面状态', '包装完整性']),

-- 豆制品品类（5种）
('tofu', '豆腐', '豆制品', 3, 0, 4, 80, 90, ARRAY['色泽', '质地均匀度', '表面状态', '损伤程度']),
('tofu skin', '豆皮', '豆制品', 5, 0, 4, 80, 90, ARRAY['色泽', '质地均匀度', '表面状态', '损伤程度']),
('soybean', '大豆', '豆制品', 180, 20, 25, 60, 70, ARRAY['色泽', '外观状态', '发芽情况', '霉变情况']),
('tofu pudding', '豆腐脑', '豆制品', 1, 0, 4, 80, 90, ARRAY['色泽', '质地均匀度', '表面状态', '损伤程度']),
('soy milk', '豆浆', '豆制品', 3, 0, 4, 75, 85, ARRAY['色泽', '质地均匀度', '表面状态', '包装完整性']),

-- 蛋类品类（4种）
('egg', '鸡蛋', '蛋类', 21, 0, 4, 75, 85, ARRAY['蛋壳完整度', '蛋壳色泽', '蛋壳状态', '清洁度']),
('duck egg', '鸭蛋', '蛋类', 28, 0, 4, 75, 85, ARRAY['蛋壳完整度', '蛋壳色泽', '蛋壳状态', '清洁度']),
('goose egg', '鹅蛋', '蛋类', 30, 0, 4, 75, 85, ARRAY['蛋壳完整度', '蛋壳色泽', '蛋壳状态', '清洁度']),
('quail egg', '鹌鹑蛋', '蛋类', 14, 0, 4, 75, 85, ARRAY['蛋壳完整度', '蛋壳色泽', '蛋壳状态', '清洁度']),

-- 医药制品品类（8种）
('vaccine', '疫苗', '医药制品', 365, -20, -8, 40, 60, ARRAY['外观完整性', '包装完整性', '标签清晰度', '有效期状态']),
('blood product', '血液制品', '医药制品', 35, 2, 8, 40, 60, ARRAY['外观完整性', '包装完整性', '标签清晰度', '有效期状态']),
('insulin', '胰岛素', '医药制品', 365, 2, 8, 40, 60, ARRAY['外观完整性', '包装完整性', '标签清晰度', '有效期状态']),
('biological agent', '生物制剂', '医药制品', 180, 2, 8, 40, 60, ARRAY['外观完整性', '包装完整性', '标签清晰度', '有效期状态']),
('plasma', '血浆', '医药制品', 35, 2, 8, 40, 60, ARRAY['外观完整性', '包装完整性', '标签清晰度', '有效期状态']),
('serum', '血清', '医药制品', 90, -20, -15, 40, 60, ARRAY['外观完整性', '包装完整性', '标签清晰度', '有效期状态']),
('reagent', '诊断试剂', '医药制品', 180, 2, 8, 40, 60, ARRAY['外观完整性', '包装完整性', '标签清晰度', '有效期状态']),
('antibody', '抗体药物', '医药制品', 365, -20, -8, 40, 60, ARRAY['外观完整性', '包装完整性', '标签清晰度', '有效期状态']),

-- 花卉品类（10种）
('rose', '玫瑰', '花卉', 7, 2, 8, 85, 95, ARRAY['色泽', '花头完整性', '叶片状态', '茎部状态']),
('lily', '百合', '花卉', 10, 2, 8, 85, 95, ARRAY['色泽', '花头完整性', '叶片状态', '茎部状态']),
('carnation', '康乃馨', '花卉', 14, 2, 8, 85, 95, ARRAY['色泽', '花头完整性', '叶片状态', '茎部状态']),
('tulip', '郁金香', '花卉', 7, 2, 8, 85, 95, ARRAY['色泽', '花头完整性', '叶片状态', '茎部状态']),
('orchid', '兰花', '花卉', 21, 15, 20, 85, 95, ARRAY['色泽', '花头完整性', '叶片状态', '茎部状态']),
('sunflower', '向日葵', '花卉', 7, 2, 8, 85, 95, ARRAY['色泽', '花头完整性', '叶片状态', '茎部状态']),
('daisy', '雏菊', '花卉', 10, 2, 8, 85, 95, ARRAY['色泽', '花头完整性', '叶片状态', '茎部状态']),
('peony', '牡丹', '花卉', 5, 2, 8, 85, 95, ARRAY['色泽', '花头完整性', '叶片状态', '茎部状态']),
('hydrangea', '绣球花', '花卉', 7, 2, 8, 85, 95, ARRAY['色泽', '花头完整性', '叶片状态', '茎部状态']),
('baby breath', '满天星', '花卉', 14, 2, 8, 85, 95, ARRAY['色泽', '花头完整性', '叶片状态', '茎部状态']),

-- 冷冻食品品类（10种）
('frozen dumpling', '速冻水饺', '冷冻食品', 180, -22, -18, 75, 85, ARRAY['外观状态', '冻结状态', '包装完整性', '标签清晰度']),
('frozen vegetable', '冷冻蔬菜', '冷冻食品', 365, -22, -18, 75, 85, ARRAY['色泽', '冻结状态', '包装完整性', '标签清晰度']),
('frozen meat', '冷冻肉类', '冷冻食品', 365, -25, -18, 75, 85, ARRAY['色泽', '冻结状态', '包装完整性', '标签清晰度']),
('frozen seafood', '冷冻海鲜', '冷冻食品', 180, -25, -18, 75, 85, ARRAY['色泽', '冻结状态', '包装完整性', '标签清晰度']),
('frozen bun', '速冻包子', '冷冻食品', 180, -22, -18, 75, 85, ARRAY['外观状态', '冻结状态', '包装完整性', '标签清晰度']),
('frozen noodle', '速冻面条', '冷冻食品', 180, -22, -18, 75, 85, ARRAY['外观状态', '冻结状态', '包装完整性', '标签清晰度']),
('frozen pizza', '冷冻披萨', '冷冻食品', 180, -22, -18, 75, 85, ARRAY['外观状态', '冻结状态', '包装完整性', '标签清晰度']),
('frozen dessert', '冷冻甜点', '冷冻食品', 180, -22, -18, 75, 85, ARRAY['外观状态', '冻结状态', '包装完整性', '标签清晰度']),
('ice cream', '冰淇淋', '冷冻食品', 180, -25, -18, 75, 85, ARRAY['外观状态', '冻结状态', '包装完整性', '标签清晰度']),
('popsicle', '冰棍', '冷冻食品', 180, -25, -18, 75, 85, ARRAY['外观状态', '冻结状态', '包装完整性', '标签清晰度']),

-- 熟食预制菜品类（8种）
('prepared meal', '预制菜', '熟食预制菜', 7, 0, 4, 75, 85, ARRAY['外观状态', '表面状态', '包装完整性', '标签清晰度']),
('deli meat', '卤味熟食', '熟食预制菜', 5, 0, 4, 75, 85, ARRAY['色泽', '表面状态', '质地均匀度', '包装完整性']),
('soup base', '火锅底料', '熟食预制菜', 90, 0, 4, 75, 85, ARRAY['外观状态', '表面状态', '包装完整性', '标签清晰度']),
('frozen meal', '速冻便当', '熟食预制菜', 180, -22, -18, 75, 85, ARRAY['外观状态', '冻结状态', '包装完整性', '标签清晰度']),
('cooked food', '即食熟食', '熟食预制菜', 3, 0, 4, 75, 85, ARRAY['色泽', '表面状态', '质地均匀度', '包装完整性']),
('sushi', '寿司', '熟食预制菜', 1, 0, 4, 75, 85, ARRAY['色泽', '表面状态', '质地均匀度', '包装完整性']),
('sandwich', '三明治', '熟食预制菜', 2, 0, 4, 75, 85, ARRAY['色泽', '表面状态', '质地均匀度', '包装完整性']),
('salad', '沙拉', '熟食预制菜', 1, 0, 4, 75, 85, ARRAY['色泽', '表面状态', '质地均匀度', '包装完整性']),

-- 饮料品类（8种）
('fresh juice', '鲜榨果汁', '饮料', 3, 0, 4, 75, 85, ARRAY['色泽', '质地均匀度', '表面状态', '包装完整性']),
('fruit juice', '果汁饮料', '饮料', 90, 0, 4, 75, 85, ARRAY['色泽', '质地均匀度', '表面状态', '包装完整性']),
('milk tea', '奶茶', '饮料', 3, 0, 4, 75, 85, ARRAY['色泽', '质地均匀度', '表面状态', '包装完整性']),
('yogurt drink', '酸奶饮品', '饮料', 7, 0, 4, 75, 85, ARRAY['色泽', '质地均匀度', '表面状态', '包装完整性']),
('iced coffee', '冰咖啡', '饮料', 3, 0, 4, 75, 85, ARRAY['色泽', '质地均匀度', '表面状态', '包装完整性']),
('energy drink', '能量饮料', '饮料', 365, 20, 25, 40, 60, ARRAY['外观状态', '表面状态', '包装完整性', '标签清晰度']),
('sports drink', '运动饮料', '饮料', 365, 20, 25, 40, 60, ARRAY['外观状态', '表面状态', '包装完整性', '标签清晰度']),
('tea beverage', '茶饮料', '饮料', 180, 20, 25, 40, 60, ARRAY['色泽', '表面状态', '包装完整性', '标签清晰度']),

-- 其他品类（5种）
('ice pack', '冰袋', '其他', 365, -25, -18, 40, 60, ARRAY['外观状态', '冻结状态', '包装完整性', '有效期']),
('dry ice', '干冰', '其他', 7, -78, -70, 30, 50, ARRAY['外观状态', '挥发程度', '包装完整性', '有效期']),
('insulation box', '保温箱', '其他', 365, -25, 25, 40, 60, ARRAY['外观状态', '密封程度', '结构完整性', '清洁度']),
('cold chain bag', '冷链运输袋', '其他', 365, -25, 25, 40, 60, ARRAY['外观状态', '密封程度', '结构完整性', '清洁度']),
('packaging material', '包装材料', '其他', 365, 20, 25, 40, 60, ARRAY['外观状态', '结构完整性', '清洁度', '有效期'])
ON CONFLICT (product_key) DO NOTHING;

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
