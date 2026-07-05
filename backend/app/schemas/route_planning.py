from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class TransportMode(str, Enum):
    DIRECT = "direct"
    HUB_DISTRIBUTION = "hub_distribution"
    MULTI_DROP = "multi_drop"


class TemperatureSensitivity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class NodeLevel(str, Enum):
    HUB_PROVINCIAL = "hub_provincial"
    DISTRIBUTION_CITY = "distribution_city"
    END_NODE = "end_node"


class RouteNode(BaseModel):
    node_id: str
    name: str
    city: str
    level: NodeLevel
    lat: float
    lng: float
    type: str = "city"
    estimated_arrival_time: Optional[datetime] = None
    estimated_departure_time: Optional[datetime] = None
    actual_arrival_time: Optional[datetime] = None
    actual_departure_time: Optional[datetime] = None
    stop_duration_min: int = 0
    temperature_min: Optional[float] = None
    temperature_max: Optional[float] = None


class RouteSegment(BaseModel):
    segment_id: str
    from_node_id: str
    to_node_id: str
    from_city: str
    to_city: str
    distance_km: float
    estimated_duration_h: float
    actual_duration_h: Optional[float] = None
    speed_kmh: float
    toll_cost_yuan: float
    fuel_cost_yuan: float
    energy_consumption_kwh: float
    carbon_emission_kg: float
    temperature_min: float
    temperature_max: float
    risk_level: str = "low"
    congestion_probability: float = 0.0
    heat_risk_probability: float = 0.0
    fence_ids: List[str] = []


class RoutePlanRequest(BaseModel):
    origin: str = Field(..., description="出发城市")
    destination: str = Field(..., description="目的城市")
    transport_mode: TransportMode = TransportMode.DIRECT
    temperature_sensitivity: TemperatureSensitivity = TemperatureSensitivity.MEDIUM
    cargo_type: str = Field("冷藏生鲜", description="货物品类")
    cargo_weight_kg: float = Field(5000, ge=100, description="货物重量(kg)")
    cargo_volume_m3: Optional[float] = None
    delivery_time_window_start: Optional[datetime] = None
    delivery_time_window_end: Optional[datetime] = None
    allow_transit: bool = True
    is_medical_cold_chain: bool = False
    vehicle_model: Optional[str] = None
    multi_drop_points: List[Dict[str, Any]] = []
    driver_count: int = 1


class RoutePlanResponse(BaseModel):
    plan_id: str
    origin: str
    destination: str
    transport_mode: TransportMode
    temperature_sensitivity: TemperatureSensitivity
    cargo_type: str
    cargo_weight_kg: float
    created_at: datetime
    estimated_total_duration_h: float
    estimated_total_distance_km: float
    estimated_total_cost_yuan: float
    total_energy_consumption_kwh: float
    total_carbon_emission_kg: float
    overall_risk_score: float
    composite_score: float
    recommended: bool = False
    
    nodes: List[RouteNode]
    segments: List[RouteSegment]
    
    vehicle_allocation: Dict[str, Any]
    driver_schedule: Dict[str, Any]
    risk_report: Dict[str, Any]
    fence_summary: Dict[str, Any]
    
    scores: Dict[str, float]


class RoutePlanComparison(BaseModel):
    plans: List[RoutePlanResponse]
    best_plan_id: str
    comparison_metrics: Dict[str, Any]


class RouteExecutionStatus(BaseModel):
    plan_id: str
    route_id: str
    vehicle_id: str
    plate_number: str
    current_node_id: Optional[str] = None
    current_segment_id: Optional[str] = None
    progress_percent: float
    status: str
    temperature_c: float
    door_events: int
    heartbeat_status: str
    last_updated_at: datetime
    estimated_arrival_time: datetime


class RealTimeReplanRequest(BaseModel):
    plan_id: str
    trigger_reason: str
    current_location: Dict[str, float]
    temperature_c: Optional[float] = None
    heartbeat_status: str = "online"
    congestion_info: Optional[Dict[str, Any]] = None
    weather_info: Optional[Dict[str, Any]] = None