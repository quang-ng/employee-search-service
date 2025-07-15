from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, func
from app.db.models import Employee, User
from app.db.session import get_db
from app.middleware.auth import get_current_user, create_access_token
from app.config.org_cache import get_org_config
from app.middleware.rate_limit import rate_limiter
from app.config.employee_count_cache import get_employee_count_from_cache, set_employee_count_cache
import bcrypt

router = APIRouter()


@router.get("/hr/{org_id}/employees/search")
async def list_employees(
    org_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    cursor: int = Query(None, description="The last seen employee id for key-set pagination"),
    status: str = Query(None),
    location: str = Query(None),
    company: str = Query(None),
    department: str = Query(None),
    position: str = Query(None),
    _: None = Depends(rate_limiter),
):
    if org_id != current_user.org_id:
        raise HTTPException(status_code=404, detail="Organization not found")
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
    if cursor is not None:
        filters.append(Employee.id > cursor)
    
    # Build query with ordering
    stmt = (
        select(Employee, func.count().over().label("total_count"))
        .where(and_(*filters))
        .order_by(Employee.id)
        .limit(limit)
    )
    
    # Try to get count from cache
    total_count = await get_employee_count_from_cache(org_id, status, location, company, department, position)
    if total_count is None:
        # Count total matching employees (without pagination)
        count_stmt = select(func.count()).select_from(Employee).where(and_(*filters))
        total_count = (await db.execute(count_stmt)).scalar()
        await set_employee_count_cache(org_id, status, location, company, department, position, total_count, ttl=60)
    
    # Add pagination
    # stmt = stmt.offset(offset).limit(limit) # This line is removed as per the new_code
    
    result = await db.execute(stmt)
    rows = result.all()
    employees = [row[0] for row in rows]
    total_count = rows[0][1] if rows else 0

    # Only return fields configured for the org, but always include 'id'
    result_list = [
        {**({'id': emp.id}), **{field: getattr(emp, field) for field in employee_fields if hasattr(emp, field) and field != 'id'}}
        for emp in employees
    ]

    next_cursor = employees[-1].id if len(employees) == limit else None

    return {
        "limit": limit,
        "cursor": cursor,
        "next_cursor": next_cursor,
        "count": total_count,
        "results": result_list,
    }


@router.post("/login")
async def login(
    username: str = Body(...),
    password: str = Body(...),
    db: AsyncSession = Depends(get_db),
):
    user = (await db.execute(select(User).where(User.username == username))).scalar_one_or_none()
    if not user or not bcrypt.checkpw(password.encode(), user.hashed_password.encode()):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}
