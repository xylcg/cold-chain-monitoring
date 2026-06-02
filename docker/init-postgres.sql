-- PostgreSQL 初始化脚本
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 设备表
CREATE TABLE IF NOT EXISTS devices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_code VARCHAR(50) UNIQUE NOT NULL,
    device_name VARCHAR(100) NOT NULL,
    device_type VARCHAR(20) NOT NULL CHECK (device_type IN ('vehicle', 'cold_room', 'freezer')),
    plate_number VARCHAR(20),
    cargo_type VARCHAR(50),
    temperature_zone VARCHAR(30),
    min_temp DECIMAL(5,2),
    max_temp DECIMAL(5,2),
    max_humidity DECIMAL(5,2),
    status VARCHAR(20) DEFAULT 'online',
    token VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'manager', 'driver', 'repair', 'customer')),
    phone VARCHAR(20),
    email VARCHAR(100),
    real_name VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 告警规则表
CREATE TABLE IF NOT EXISTS alert_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_name VARCHAR(100) NOT NULL,
    rule_type VARCHAR(30) NOT NULL,
    device_type VARCHAR(20),
    condition_field VARCHAR(50) NOT NULL,
    condition_operator VARCHAR(10) NOT NULL,
    condition_value DECIMAL(10,2) NOT NULL,
    severity VARCHAR(10) NOT NULL CHECK (severity IN ('normal', 'severe', 'critical')),
    cooldown_seconds INT DEFAULT 300,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 告警事件表
CREATE TABLE IF NOT EXISTS alert_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_id UUID REFERENCES devices(id),
    rule_id UUID REFERENCES alert_rules(id),
    alert_type VARCHAR(30) NOT NULL,
    severity VARCHAR(10) NOT NULL,
    message TEXT,
    sensor_value DECIMAL(10,2),
    threshold_value DECIMAL(10,2),
    is_acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by UUID REFERENCES users(id),
    acknowledged_at TIMESTAMP,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 插入默认用户
INSERT INTO users (username, password_hash, role, real_name) VALUES
('admin', '$2b$12$LJ3m4ys3Lk0TSwHCpNqrFOsD5qhQZ0YHJzC6uPqjE0dSx4Oq5mP3O', 'admin', '系统管理员'),
('driver01', '$2b$12$LJ3m4ys3Lk0TSwHCpNqrFOsD5qhQZ0YHJzC6uPqjE0dSx4Oq5mP3O', 'driver', '配送员01'),
('manager01', '$2b$12$LJ3m4ys3Lk0TSwHCpNqrFOsD5qhQZ0YHJzC6uPqjE0dSx4Oq5mP3O', 'manager', '区域经理01')
ON CONFLICT (username) DO NOTHING;

-- 插入默认告警规则
INSERT INTO alert_rules (rule_name, rule_type, condition_field, condition_operator, condition_value, severity, cooldown_seconds) VALUES
('冷藏车厢温度上限', 'temperature_high', 'temperature', '>', 8.0, 'severe', 300),
('冷藏车厢温度下限', 'temperature_low', 'temperature', '<', 0.0, 'normal', 300),
('冷冻车厢温度上限', 'temperature_high', 'temperature', '>', -15.0, 'severe', 300),
('冷冻车厢温度下限', 'temperature_low', 'temperature', '<', -25.0, 'normal', 300),
('湿度上限', 'humidity_high', 'humidity', '>', 95.0, 'normal', 600),
('车门长时间开启', 'door_open_long', 'door_open_duration', '>', 300, 'severe', 600),
('疫苗温度失控', 'temperature_critical', 'temperature', '>', 8.0, 'critical', 60),
('振动异常', 'vibration_high', 'vibration', '>', 5.0, 'normal', 600)
ON CONFLICT DO NOTHING;
