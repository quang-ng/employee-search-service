from app.config import get_redis


def build_employee_count_cache_key(org_id, status, location, company, department, position):
    return f"employee_count:{org_id}:{status or ''}:{location or ''}:{company or ''}:{department or ''}:{position or ''}"

async def get_employee_count_from_cache(org_id, status, location, company, department, position):
    redis_conn = await get_redis()
    cache_key = build_employee_count_cache_key(org_id, status, location, company, department, position)
    cached_count = await redis_conn.get(cache_key)
    if cached_count is not None:
        return int(cached_count)
    return None

async def set_employee_count_cache(org_id, status, location, company, department, position, count, ttl=60):
    redis_conn = await get_redis()
    cache_key = build_employee_count_cache_key(org_id, status, location, company, department, position)
    await redis_conn.set(cache_key, str(count), ex=ttl) 