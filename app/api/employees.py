from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, func
from app.db.models import Employee, User
from app.db.session import get_db
from app.middleware.auth import get_current_user
from app.config.org_cache import get_org_config
from app.middleware.rate_limit import rate_limiter
from app.config.employee_count_cache import get_employee_count_from_cache, set_employee_count_cache

router = APIRouter()


@router.get("/employees")
async def list_employees(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: str = Query(None),
    location: str = Query(None),
    company: str = Query(None),
    department: str = Query(None),
    position: str = Query(None),
    _: None = Depends(rate_limiter),
):
    org_id = current_user.org_id
    # Get org config from cache
    employee_fields = await get_org_config(org_id, db)
    if not employee_fields:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Build filters
    filters = [Employee.org_id == org_id]
    if status:
        filters.append(Employee.status == status)
    if location:
        filters.append(Employee.location == location)
    if company:
        filters.append(Employee.company == company)
    if department:
        filters.append(Employee.department == department)
    if position:
        filters.append(Employee.position == position)
    
    # Build query with ordering
    stmt = select(Employee).where(and_(*filters))
    
    # Try to get count from cache
    total_count = await get_employee_count_from_cache(org_id, status, location, company, department, position)
    if total_count is None:
        # Count total matching employees (without pagination)
        count_stmt = select(func.count()).select_from(Employee).where(and_(*filters))
        total_count = (await db.execute(count_stmt)).scalar()
        await set_employee_count_cache(org_id, status, location, company, department, position, total_count, ttl=60)
    
    # Add pagination
    stmt = stmt.offset(offset).limit(limit)
    
    employees = (await db.execute(stmt)).scalars().all()
    
    # Only return fields configured for the org
    result = []
    for emp in employees:
        emp_dict = {
            field: getattr(emp, field)
            for field in employee_fields
            if hasattr(emp, field)
        }
        result.append(emp_dict)
    
    return {"limit": limit, "offset": offset, "count": total_count, "results": result}
