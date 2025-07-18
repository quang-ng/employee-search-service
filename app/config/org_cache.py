import json
from app.config import get_redis
from app.db.models import Organization
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

async def get_org_config(org_id: int, db: AsyncSession):
    cache_key = f"org_config:{org_id}"
    redis_conn = await get_redis()
    config = await redis_conn.get(cache_key)
    if config:
        return json.loads(config)
    # Fetch from DB and cache
    org = (await db.execute(select(Organization).where(Organization.id == org_id))).scalar_one_or_none()
    if not org:
        return None
    await redis_conn.set(cache_key, json.dumps(org.employee_fields), ex=3600)
    return org.employee_fields

async def set_org_config(org_id: int, employee_fields):
    cache_key = f"org_config:{org_id}"
    redis_conn = await get_redis()
    await redis_conn.set(cache_key, json.dumps(employee_fields), ex=3600) 