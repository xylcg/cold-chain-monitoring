"""
Redis 缓存服务
支持 Redis 服务器和内存 Fallback 两种模式
"""
import asyncio
import json
import time
import redis.asyncio as aioredis
from typing import Optional, Any
from loguru import logger
from ..core.config import get_settings

settings = get_settings()

# Redis 操作超时（秒）
_REDIS_OP_TIMEOUT = 1.5


class _MemoryStore:
    """内存数据存储（Redis 不可用时的 fallback）"""

    def __init__(self):
        self._data: dict[str, Any] = {}       # key -> value (string)
        self._hashes: dict[str, dict] = {}     # key -> {field: value}
        self._sets: dict[str, set] = {}        # key -> set()
        self._lists:dict[str, list] = {}       # key -> []
        self._expiry: dict[str, float] = {}    # key -> expiry timestamp

    def _cleanup(self):
        """清理过期键"""
        now = time.time()
        expired = [k for k, t in self._expiry.items() if t < now]
        for k in expired:
            self._data.pop(k, None)
            self._hashes.pop(k, None)
            self._sets.pop(k, None)
            self._lists.pop(k, None)
            self._expiry.pop(k, None)

    # --- string ---
    async def set(self, key: str, value: str, ex: int | None = None, **kwargs):
        self._cleanup()
        self._data[key] = value
        if ex:
            self._expiry[key] = time.time() + ex

    async def setex(self, key: str, seconds: int, value: str):
        """set with expiry (alias)"""
        await self.set(key, value, ex=seconds)

    async def get(self, key: str) -> str | None:
        self._cleanup()
        if key in self._expiry and self._expiry[key] < time.time():
            return None
        return self._data.get(key)

    async def incr(self, key: str) -> int:
        self._cleanup()
        v = int(self._data.get(key, "0")) + 1
        self._data[key] = str(v)
        return v

    async def decr(self, key: str) -> int:
        self._cleanup()
        v = max(0, int(self._data.get(key, "0")) - 1)
        self._data[key] = str(v)
        return v

    async def exists(self, key: str) -> int:
        self._cleanup()
        if key in self._expiry and self._expiry[key] < time.time():
            return 0
        return 1 if (key in self._data or key in self._hashes or key in self._sets) else 0

    # --- hash ---
    async def hset(self, key: str, mapping: dict, **kwargs):
        self._cleanup()
        if key not in self._hashes:
            self._hashes[key] = {}
        self._hashes[key].update(mapping)

    async def hgetall(self, key: str) -> dict:
        self._cleanup()
        if key in self._expiry and self._expiry[key] < time.time():
            return {}
        return self._hashes.get(key, {})

    # --- set ---
    async def sadd(self, key: str, *members: str):
        self._cleanup()
        if key not in self._sets:
            self._sets[key] = set()
        self._sets[key].update(members)

    async def srem(self, key: str, *members: str):
        self._cleanup()
        s = self._sets.get(key)
        if s:
            for m in members:
                s.discard(m)

    async def smembers(self, key: str) -> set:
        self._cleanup()
        if key in self._expiry and self._expiry[key] < time.time():
            return set()
        return self._sets.get(key, set())

    async def sismember(self, key: str, member: str) -> bool:
        self._cleanup()
        s = self._sets.get(key)
        return member in s if s else False

    # --- list ---
    async def rpush(self, key: str, *values):
        self._cleanup()
        if key not in self._lists:
            self._lists[key] = []
        self._lists[key].extend(str(v) for v in values)

    async def lrange(self, key: str, start: int, end: int) -> list:
        self._cleanup()
        lst = self._lists.get(key, [])
        if end == -1:
            return lst[start:]
        return lst[start:end + 1]

    async def ltrim(self, key: str, start: int, end: int):
        self._cleanup()
        lst = self._lists.get(key, [])
        if end == -1:
            self._lists[key] = lst[start:]
        else:
            self._lists[key] = lst[start:end + 1]

    # --- ttl ---
    async def expire(self, key: str, seconds: int):
        self._expiry[key] = time.time() + seconds

    # --- pipeline stub ---
    class _Pipeline:
        def __init__(self, store: '_MemoryStore'):
            self._store = store
            self._ops: list[callable] = []

        def rpush(self, key, *v):
            self._ops.append(lambda k=key, v=v: self._store.rpush(k, *v))
            return self

        def ltrim(self, start, end):
            self._ops.append(lambda s=start, e=end: self._store.ltrim(s, e))
            return self

        def expire(self, key, seconds):
            self._ops.append(lambda k=key, s=seconds: self._store.expire(k, s))
            return self

        def hset(self, key, mapping, **kw):
            self._ops.append(lambda k=key, m=mapping, kw=kw: self._store.hset(k, m, **kw))
            return self

        async def execute(self):
            results = []
            for op in self._ops:
                r = op()
                results.append(r if not asyncio.iscoroutine(r) else await r)
            return results

    def pipeline(self):
        return self._Pipeline(self)


class RedisService:
    """Redis 缓存与实时数据服务"""

    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None
        self._connected = False
        # 内存 fallback 存储
        self._mem = _MemoryStore()

    @property
    def use_memory_fallback(self) -> bool:
        """是否正在使用内存 fallback"""
        return not self._connected

    async def connect(self):
        """连接 Redis，失败则使用内存 fallback"""
        try:
            self._redis = aioredis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                db=settings.REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            await asyncio.wait_for(self._redis.ping(), timeout=3)
            self._connected = True
            logger.info("Redis 连接成功")
        except Exception as e:
            self._redis = None
            self._connected = False
            logger.warning(f"Redis 连接失败，使用内存 Fallback 模式: {e}")

    async def close(self):
        if self._redis:
            try:
                await asyncio.wait_for(self._redis.close(), timeout=2)
            except Exception:
                pass
            self._redis = None
            self._connected = False

    @property
    def is_connected(self) -> bool:
        """是否已连接（含内存 fallback）— 始终返回 True 以便数据正常流动"""
        return True

    async def _safe_call(self, coro, default=None):
        """安全调用：优先 Redis，降级到内存 fallback"""
        if self._connected:
            try:
                return await asyncio.wait_for(coro, timeout=_REDIS_OP_TIMEOUT)
            except asyncio.TimeoutError:
                logger.warning("Redis 操作超时，尝试内存 fallback")
            except Exception as e:
                logger.warning(f"Redis 操作失败: {e}")
                if "Connection" in str(type(e).__name__) or "closed" in str(e).lower():
                    self._connected = False
                    logger.info("切换到内存 Fallback 模式")

        # 内存 fallback：coro 无法执行，返回 default
        # （对于写操作，调用方需要额外调用 _mem 方法）
        return default

    def _mem_or_redis(self):
        """获取可用的数据操作对象"""
        if self._connected and self._redis:
            return self._redis
        return self._mem

    # ==================== 设备实时状态 ====================
    async def set_device_status(self, device_id: str, status: dict):
        key = f"device:status:{device_id}"
        store = self._mem_or_redis()
        await store.hset(key, mapping={k: str(v) for k, v in status.items()})
        await store.expire(key, 60)

    async def get_device_status(self, device_id: str) -> Optional[dict]:
        key = f"device:status:{device_id}"
        store = self._mem_or_redis()
        data = await store.hgetall(key)
        return data if data else None

    # ==================== 设备最新数据 ====================
    async def set_latest_sensor_data(self, device_id: str, data: dict):
        key = f"device:latest:{device_id}"
        store = self._mem_or_redis()
        await store.set(key, json.dumps(data, ensure_ascii=False), ex=120)

    async def get_latest_sensor_data(self, device_id: str) -> Optional[dict]:
        key = f"device:latest:{device_id}"
        store = self._mem_or_redis()
        raw = await store.get(key)
        return json.loads(raw) if raw else None

    # ==================== 设备在线状态 ====================
    async def set_device_online(self, device_id: str):
        store = self._mem_or_redis()
        await store.sadd("devices:online", device_id)

    async def set_device_offline(self, device_id: str):
        store = self._mem_or_redis()
        await store.srem("devices:online", device_id)

    async def get_online_devices(self) -> set:
        store = self._mem_or_redis()
        result = await store.smembers("devices:online")
        return result if result is not None else set()

    async def is_device_online(self, device_id: str) -> bool:
        store = self._mem_or_redis()
        result = await store.sismember("devices:online", device_id)
        return bool(result)

    # ==================== 温度时序窗口 ====================
    async def push_temperature_window(self, device_id: str, temp: float, window_size: int = 60):
        key = f"temp:window:{device_id}"
        store = self._mem_or_redis()
        if isinstance(store, _MemoryStore):
            # 内存模式：直接操作
            await store.rpush(key, temp)
            lst = store._lists.get(key, [])
            store._lists[key] = lst[-window_size:]
            await store.expire(key, 300)
        else:
            # Redis 真实连接：使用 pipeline
            pipe = store.pipeline()
            pipe.rpush(key, temp)
            pipe.ltrim(key, -window_size, -1)
            pipe.expire(key, 300)
            await pipe.execute()

    async def get_temperature_window(self, device_id: str) -> list[float]:
        key = f"temp:window:{device_id}"
        store = self._mem_or_redis()
        data = await store.lrange(key, 0, -1)
        return [float(x) for x in (data or [])]

    # ==================== 告警冷却 ====================
    async def check_alert_cooldown(self, device_id: str, alert_type: str, cooldown_seconds: int = 300) -> bool:
        key = f"alert:cooldown:{device_id}:{alert_type}"
        store = self._mem_or_redis()
        exists = await store.exists(key)
        if exists:
            return False
        await store.set(key, "1", ex=cooldown_seconds)
        return True

    # ==================== 活跃告警计数 ====================
    async def incr_active_alerts(self, device_id: str):
        key = f"device:active_alerts:{device_id}"
        store = self._mem_or_redis()
        await store.incr(key)
        await store.expire(key, 3600)

    async def decr_active_alerts(self, device_id: str):
        key = f"device:active_alerts:{device_id}"
        store = self._mem_or_redis()
        await store.decr(key)

    async def get_active_alerts(self, device_id: str) -> int:
        key = f"device:active_alerts:{device_id}"
        store = self._mem_or_redis()
        count = await store.get(key)
        return int(count) if count else 0

    # ==================== WebSocket 频道 ====================
    async def publish(self, channel: str, message: str):
        if self._connected:
            await self._safe_call(self._redis.publish(channel, message))
        # 内存模式下 pub/sub 不支持，忽略

    async def subscribe(self, channel: str):
        if self._connected:
            from redis.asyncio.client import PubSub
            ps: PubSub = self._redis.pubsub()
            await self._safe_call(ps.subscribe(channel))
            return ps
        return None

    # ==================== 兼容属性 ====================
    @property
    def client(self) -> Any:
        """返回实际 Redis 客户端或内存存储"""
        if self._connected and self._redis is not None:
            return self._redis
        # 返回内存存储，让代码继续工作
        return self._mem


# 全局单例
redis_service = RedisService()
