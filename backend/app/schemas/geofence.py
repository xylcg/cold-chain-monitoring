from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class FenceType(str, Enum):
    CIRCLE = "circle"
    LINE_BUFFER = "line_buffer"
    POLYGON = "polygon"
    CITY = "city"


class FenceCategory(str, Enum):
    WAREHOUSE = "warehouse"
    HUB = "hub"
    SERVICE_AREA = "service_area"
    REPAIR_STATION = "repair_station"
    ROUTE_SEGMENT = "route_segment"
    FORBIDDEN = "forbidden"
    HIGH_TEMP = "high_temp"
    RESTRICTED = "restricted"
    CITY_ZONE = "city_zone"
    CHECKPOINT = "checkpoint"


class AlertLevel(str, Enum):
    SEVERE = "severe"
    WARNING = "warning"
    NORMAL = "normal"
    INFO = "info"


class GeoPoint(BaseModel):
    lat: float = Field(..., ge=-90, le=90, description="纬度")
    lng: float = Field(..., ge=-180, le=180, description="经度")


class CircleFenceData(BaseModel):
    center: GeoPoint
    radius_meters: float = Field(..., ge=50, le=5000, description="半径(米)")


class LineBufferFenceData(BaseModel):
    points: List[GeoPoint]
    buffer_meters: float = Field(..., ge=50, le=500, description="缓冲宽度(米)")


class PolygonFenceData(BaseModel):
    coordinates: List[List[GeoPoint]]


class CityFenceData(BaseModel):
    city_name: str
    province: str


class FenceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    fence_type: FenceType
    category: FenceCategory
    data: Dict[str, Any]
    description: Optional[str] = ""
    active: bool = True
    alert_level: AlertLevel = AlertLevel.WARNING
    speed_limit: Optional[float] = None
    allowed_stay_minutes: Optional[int] = None
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None
    tags: Optional[List[str]] = []
    route_id: Optional[str] = None


class FenceUpdate(BaseModel):
    name: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    active: Optional[bool] = None
    alert_level: Optional[AlertLevel] = None
    speed_limit: Optional[float] = None
    allowed_stay_minutes: Optional[int] = None
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None
    tags: Optional[List[str]] = None


class FenceInDB(BaseModel):
    fence_id: str
    name: str
    fence_type: FenceType
    category: FenceCategory
    data: Dict[str, Any]
    description: str
    active: bool
    alert_level: AlertLevel
    speed_limit: Optional[float]
    allowed_stay_minutes: Optional[int]
    effective_from: Optional[datetime]
    effective_to: Optional[datetime]
    tags: List[str]
    route_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class FenceEvent(BaseModel):
    event_id: str
    fence_id: str
    fence_name: str
    fence_type: FenceType
    fence_category: FenceCategory
    vehicle_id: str
    plate_number: str
    event_type: str
    event_time: datetime
    location: GeoPoint
    previous_location: Optional[GeoPoint] = None
    alert_level: AlertLevel
    description: str
    temperature_c: Optional[float] = None
    heartbeat_status: str = "online"
    stay_duration_minutes: Optional[int] = None
    city_section: Optional[str] = None
    resolved: bool = False


class FenceEventCreate(BaseModel):
    fence_id: str
    vehicle_id: str
    event_type: str
    location: GeoPoint
    previous_location: Optional[GeoPoint] = None
    temperature_c: Optional[float] = None
    heartbeat_status: str = "online"
    stay_duration_minutes: Optional[int] = None
    city_section: Optional[str] = None


class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    id: str
    geometry: Dict[str, Any]
    properties: Dict[str, Any]