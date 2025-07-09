import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.models import Base, Organization, User, Employee
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.session import get_db
import redis
import secrets
from fastapi import status
from app.middleware.auth import get_current_user
from fastapi.security import HTTPBasicCredentials

# --- Test DB setup ---
SQLALCHEMY_DATABASE_URL = "sqlite://"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Test Redis setup ---
redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(autouse=True)
def flush_redis():
    redis_client.flushdb()
    yield
    redis_client.flushdb()

@pytest.fixture
def db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def test_data(db):
    org = Organization(name="TestOrg", employee_fields=["id", "name", "department"])
    db.add(org)
    db.commit()
    db.refresh(org)
    user = User(username="testuser", hashed_password="testpass", org_id=org.id)
    db.add(user)
    db.commit()
    db.refresh(user)
    emp = Employee(org_id=org.id, name="Alice", department="HR")
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return {"org": org, "user": user, "employee": emp}

# --- Dependency overrides ---
async def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def override_get_current_user(db=pytest.lazy_fixture('db'), test_data=pytest.lazy_fixture('test_data')):
    return test_data["user"]

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_unauthenticated_access(client):
    response = client.get("/employees")
    assert response.status_code == 401
    assert "Invalid authentication credentials" in response.text

def test_authenticated_access(client):
    response = client.get(
        "/employees",
        auth=("testuser", "testpass")
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["results"][0]["name"] == "Alice"

def test_rate_limit(client):
    # 10 requests should succeed
    for _ in range(10):
        response = client.get("/employees", auth=("testuser", "testpass"))
        assert response.status_code == 200
    # 11th request should fail
    response = client.get("/employees", auth=("testuser", "testpass"))
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.text 