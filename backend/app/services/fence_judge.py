import math
from typing import Tuple, List, Dict, Optional
from ..schemas.geofence import FenceInDB, FenceType, GeoPoint


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371000
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def is_point_in_circle(lat: float, lng: float, center_lat: float, center_lng: float, radius_meters: float) -> bool:
    distance = haversine_distance(lat, lng, center_lat, center_lng)
    return distance <= radius_meters


def ray_casting(lat: float, lng: float, polygon_coords: List[List[Tuple[float, float]]]) -> bool:
    for ring in polygon_coords:
        inside = False
        n = len(ring)
        for i in range(n):
            j = (i + 1) % n
            xi, yi = ring[i]
            xj, yj = ring[j]
            if ((yi > lat) != (yj > lat)) and (lng < (xj - xi) * (lat - yi) / (yj - yi) + xi):
                inside = not inside
        if inside:
            return True
    return False


def point_to_line_distance(lat: float, lng: float, line_points: List[Tuple[float, float]]) -> float:
    min_dist = float('inf')
    n = len(line_points)
    for i in range(n - 1):
        x1, y1 = line_points[i]
        x2, y2 = line_points[i + 1]
        A = lng - x1
        B = lat - y1
        C = x2 - x1
        D = y2 - y1
        dot = A * C + B * D
        len_sq = C * C + D * D
        if len_sq == 0:
            dist = haversine_distance(lat, lng, y1, x1)
        else:
            param = dot / len_sq
            if param < 0:
                xx, yy = x1, y1
            elif param > 1:
                xx, yy = x2, y2
            else:
                xx = x1 + param * C
                yy = y1 + param * D
            dist = haversine_distance(lat, lng, yy, xx)
        min_dist = min(min_dist, dist)
    return min_dist


def is_point_in_line_buffer(lat: float, lng: float, line_points: List[Tuple[float, float]], buffer_meters: float) -> bool:
    if len(line_points) < 2:
        return False
    dist = point_to_line_distance(lat, lng, line_points)
    return dist <= buffer_meters


def is_point_in_city(lat: float, lng: float, city_name: str, city_coords: Dict[str, Tuple[float, float]]) -> bool:
    if city_name not in city_coords:
        return False
    center_lat, center_lng = city_coords[city_name]
    return haversine_distance(lat, lng, center_lat, center_lng) <= 50000


def is_point_in_fence(lat: float, lng: float, fence: FenceInDB, city_coords: Dict[str, Tuple[float, float]] = None) -> bool:
    if not fence.active:
        return False

    fence_type = fence.fence_type
    data = fence.data

    if fence_type == FenceType.CIRCLE:
        center = data.get("center", {})
        radius = data.get("radius_meters", 100)
        return is_point_in_circle(lat, lng, center.get("lat", 0), center.get("lng", 0), radius)

    elif fence_type == FenceType.LINE_BUFFER:
        points = data.get("points", [])
        line_points = [(p.get("lng", 0), p.get("lat", 0)) for p in points]
        buffer = data.get("buffer_meters", 50)
        return is_point_in_line_buffer(lat, lng, line_points, buffer)

    elif fence_type == FenceType.POLYGON:
        coords = data.get("coordinates", [])
        polygon_coords = [[(p.get("lng", 0), p.get("lat", 0)) for p in ring] for ring in coords]
        return ray_casting(lat, lng, polygon_coords)

    elif fence_type == FenceType.CITY:
        city_name = data.get("city_name", "")
        city_coords = city_coords or {}
        return is_point_in_city(lat, lng, city_name, city_coords)

    return False


def get_distance_from_fence(lat: float, lng: float, fence: FenceInDB, city_coords: Dict[str, Tuple[float, float]] = None) -> float:
    if fence.fence_type == FenceType.CIRCLE:
        center = fence.data.get("center", {})
        return haversine_distance(lat, lng, center.get("lat", 0), center.get("lng", 0))

    elif fence.fence_type == FenceType.LINE_BUFFER:
        points = fence.data.get("points", [])
        line_points = [(p.get("lng", 0), p.get("lat", 0)) for p in points]
        return point_to_line_distance(lat, lng, line_points)

    elif fence.fence_type == FenceType.POLYGON:
        coords = fence.data.get("coordinates", [])
        min_dist = float('inf')
        for ring in coords:
            for i in range(len(ring)):
                j = (i + 1) % len(ring)
                x1, y1 = ring[i]["lng"], ring[i]["lat"]
                x2, y2 = ring[j]["lng"], ring[j]["lat"]
                dist = point_to_line_distance(lat, lng, [(x1, y1), (x2, y2)])
                min_dist = min(min_dist, dist)
        return min_dist

    elif fence.fence_type == FenceType.CITY:
        city_name = fence.data.get("city_name", "")
        if city_name in (city_coords or {}):
            center_lat, center_lng = city_coords[city_name]
            return haversine_distance(lat, lng, center_lat, center_lng)

    return float('inf')


def find_containing_fences(lat: float, lng: float, fences: List[FenceInDB], city_coords: Dict[str, Tuple[float, float]] = None) -> List[FenceInDB]:
    result = []
    for fence in fences:
        if is_point_in_fence(lat, lng, fence, city_coords):
            result.append(fence)
    return result


def find_closest_fence(lat: float, lng: float, fences: List[FenceInDB], city_coords: Dict[str, Tuple[float, float]] = None) -> Optional[FenceInDB]:
    closest = None
    min_dist = float('inf')
    for fence in fences:
        if not fence.active:
            continue
        dist = get_distance_from_fence(lat, lng, fence, city_coords)
        if dist < min_dist:
            min_dist = dist
            closest = fence
    return closest


def check_route_deviation(lat: float, lng: float, route_fences: List[FenceInDB], consecutive_off_count: int, city_coords: Dict[str, Tuple[float, float]] = None) -> Tuple[bool, int]:
    in_any_fence = False
    for fence in route_fences:
        if fence.fence_type == FenceType.LINE_BUFFER:
            if is_point_in_fence(lat, lng, fence, city_coords):
                in_any_fence = True
                break

    if in_any_fence:
        return False, 0
    else:
        new_count = consecutive_off_count + 1
        return new_count >= 3, new_count