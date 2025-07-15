import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException
from app.api.employees import list_employees
from app.db.models import Employee, User, Organization
from app.main import app
import json
from unittest.mock import AsyncMock
from app.db.session import get_db
import bcrypt

# Test client
client = TestClient(app)

# Generate a valid bcrypt hash for "testpass"
hashed = bcrypt.hashpw("testpass".encode(), bcrypt.gensalt()).decode()

# Mock data
mock_user = User(
    id=1,
    username="testuser",
    hashed_password=hashed,  # Use the valid hash here
    org_id=1,
)

mock_organization = Organization(
    id=1,
    name="Test Org",
    employee_fields=[
        "id",
        "name",
        "department",
        "location",
        "position",
        "status",
        "company",
    ],
)

mock_employees = [
    Employee(
        id=1,
        org_id=1,
        name="John Doe",
        department="Engineering",
        location="San Francisco",
        position="Software Engineer",
        status="active",
        company="Tech Corp",
    ),
    Employee(
        id=2,
        org_id=1,
        name="Jane Smith",
        department="Marketing",
        location="New York",
        position="Marketing Manager",
        status="active",
        company="Tech Corp",
    ),
    Employee(
        id=3,
        org_id=1,
        name="Bob Johnson",
        department="Engineering",
        location="San Francisco",
        position="Senior Engineer",
        status="inactive",
        company="Tech Corp",
    ),
]


@pytest.fixture
def mock_org_config():
    """Mock organization configuration"""
    return ["id", "name", "department", "location", "position", "status", "company"]


def get_jwt_token(username, password):
    response = client.post("/login", json={"username": username, "password": password})
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]


def test_login_success():
    # Create a mock db session
    mock_db = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_db.execute = AsyncMock(return_value=mock_result)

    # Override the get_db dependency
    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db

    response = client.post(
        "/login", json={"username": "admin_techcorp", "password": "testpass"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Clean up the override
    app.dependency_overrides = {}


def test_login_failure():
    # Create a mock db session that returns None for user lookup
    mock_db = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None  # Simulate user not found
    mock_db.execute = AsyncMock(return_value=mock_result)

    # Override the get_db dependency
    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db

    response = client.post(
        "/login", json={"username": "fakeuser", "password": "wrongpass"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"

    # Clean up the override
    app.dependency_overrides = {}


def test_protected_endpoint_with_jwt():
    # Create a mock db session for login (returns mock_user)
    mock_db_login = MagicMock()
    mock_result_login = MagicMock()
    mock_result_login.scalar_one_or_none.return_value = mock_user
    mock_db_login.execute = AsyncMock(return_value=mock_result_login)

    # Override the get_db dependency for login
    async def override_get_db_login():
        yield mock_db_login

    app.dependency_overrides[get_db] = override_get_db_login

    token = get_jwt_token("admin_techcorp", "testpass")

    # Create a mock db session for employee search (returns empty list)
    mock_db_search = MagicMock()
    mock_result_search = MagicMock()
    mock_result_search.all.return_value = []
    mock_db_search.execute = AsyncMock(return_value=mock_result_search)

    # Override the get_db dependency for employee search
    async def override_get_db_search():
        yield mock_db_search

    app.dependency_overrides[get_db] = override_get_db_search

    response = client.get(
        "/hr/1/employees/search", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404
    # Should not leak secrets in response
    assert "access_token" not in response.text
    assert "password" not in response.text

    # Clean up the override
    app.dependency_overrides = {}


class TestListEmployees:
    """Test cases for the list_employees endpoint"""

    @pytest.mark.asyncio
    async def test_list_employees_success(self, mock_db, mock_org_config):
        """Test successful employee listing with default parameters"""

        # Mock dependencies
        with patch("app.api.employees.get_current_user", return_value=mock_user), patch(
            "app.api.employees.get_org_config", return_value=mock_org_config
        ), patch("app.api.employees.rate_limiter", return_value=None):

            # Mock database query result
            mock_db.execute = AsyncMock()
            mock_result = MagicMock()
            mock_result.all.return_value = [(emp, 3) for emp in mock_employees]
            mock_db.execute.return_value = mock_result

            # Call the function
            result = await list_employees(
                org_id=1,
                current_user=mock_user,
                db=mock_db,
                limit=3,
                cursor=None,
            )

            # Assertions
            assert result["limit"] == 3
            assert result["cursor"] is None
            assert result["count"] == 3
            assert len(result["results"]) == 3

            assert result["next_cursor"] == mock_employees[-1].id
            # Check that only configured fields are returned
            for emp in result["results"]:
                assert "id" in emp
                assert "name" in emp
                assert "department" in emp
                assert "location" in emp
                assert "position" in emp
                assert "status" in emp
                assert "company" in emp

    @pytest.mark.asyncio
    async def test_list_employees_with_filters(self, mock_db, mock_org_config):
        """Test employee listing with filters"""
        with patch("app.api.employees.get_current_user", return_value=mock_user), patch(
            "app.api.employees.get_org_config", return_value=mock_org_config
        ), patch("app.api.employees.rate_limiter", return_value=None):

            # Mock database query result for filtered results
            mock_db.execute = AsyncMock()
            mock_result = MagicMock()
            mock_result.all.return_value = [
                (emp, 1)
                for emp in mock_employees
                if emp.department == "Engineering" and emp.status == "active"
            ]
            mock_db.execute.return_value = mock_result

            # Call the function with filters
            result = await list_employees(
                org_id=1,
                current_user=mock_user,
                db=mock_db,
                limit=3,
                cursor=None,
                department="Engineering",
                status="active",
            )

            # Assertions
            assert result["count"] == 1
            assert result["results"][0]["department"] == "Engineering"
            assert result["results"][0]["status"] == "active"

    @pytest.mark.asyncio
    async def test_list_employees_pagination(self, mock_db, mock_org_config):
        """Test employee listing with pagination"""
        with patch("app.api.employees.get_current_user", return_value=mock_user), patch(
            "app.api.employees.get_org_config", return_value=mock_org_config
        ), patch("app.api.employees.rate_limiter", return_value=None):

            # Mock database query result
            mock_db.execute = AsyncMock()
            mock_result = MagicMock()
            mock_result.all.return_value = [
                (emp, 2) for emp in mock_employees[:2]
            ]  # First 2 employees
            mock_db.execute.return_value = mock_result

            # Call the function with pagination
            result = await list_employees(
                org_id=1, current_user=mock_user, db=mock_db, limit=3, cursor=None
            )

            # Assertions
            assert result["limit"] == 3
            assert result["cursor"] is None
            assert result["count"] == 2
            assert len(result["results"]) == 2
            assert result["next_cursor"] is None

    @pytest.mark.asyncio
    async def test_list_employees_organization_not_found(self, mock_db):
        """Test when organization configuration is not found"""
        with patch("app.api.employees.get_current_user", return_value=mock_user), patch(
            "app.api.employees.get_org_config", return_value=None
        ), patch("app.api.employees.rate_limiter", return_value=None):

            # Call the function and expect HTTPException
            with pytest.raises(HTTPException) as exc_info:
                await list_employees(
                    org_id=1, current_user=mock_user, db=mock_db, limit=3, cursor=None
                )

            assert exc_info.value.status_code == 404
            assert exc_info.value.detail == "Organization not found"

    @pytest.mark.asyncio
    async def test_list_employees_all_filters(self, mock_db, mock_org_config):
        """Test employee listing with all possible filters"""
        with patch("app.api.employees.get_current_user", return_value=mock_user), patch(
            "app.api.employees.get_org_config", return_value=mock_org_config
        ), patch("app.api.employees.rate_limiter", return_value=None):

            # Mock database query result
            mock_db.execute = AsyncMock()
            mock_result = MagicMock()
            mock_result.all.return_value = [
                (emp, 1)
                for emp in mock_employees
                if emp.status == "active"
                and emp.location == "San Francisco"
                and emp.company == "Tech Corp"
                and emp.department == "Engineering"
                and emp.position == "Software Engineer"
            ]
            mock_db.execute.return_value = mock_result

            # Call the function with all filters
            result = await list_employees(
                org_id=1,
                current_user=mock_user,
                db=mock_db,
                limit=3,
                cursor=None,
                status="active",
                location="San Francisco",
                company="Tech Corp",
                department="Engineering",
                position="Software Engineer",
            )

            # Assertions
            assert result["limit"] == 3
            assert result["count"] == 1
            assert result["results"][0]["status"] == "active"
            assert result["results"][0]["location"] == "San Francisco"
            assert result["results"][0]["company"] == "Tech Corp"
            assert result["results"][0]["department"] == "Engineering"
            assert result["results"][0]["position"] == "Software Engineer"

    @pytest.mark.asyncio
    async def test_list_employees_empty_result(self, mock_db, mock_org_config):
        """Test employee listing with no results"""
        with patch("app.api.employees.get_current_user", return_value=mock_user), patch(
            "app.api.employees.get_org_config", return_value=mock_org_config
        ), patch("app.api.employees.rate_limiter", return_value=None):

            # Mock database query result with empty list
            mock_db.execute = AsyncMock()
            mock_result = MagicMock()
            mock_result.all.return_value = []
            mock_db.execute.return_value = mock_result

            # Call the function
            result = await list_employees(
                org_id=1, current_user=mock_user, db=mock_db, limit=3, cursor=None
            )

            # Assertions
            assert result["count"] == 0
            assert len(result["results"]) == 0
            assert result["next_cursor"] is None

    @pytest.mark.asyncio
    async def test_list_employees_limited_fields(self, mock_db):
        """Test employee listing with limited configured fields"""
        limited_fields = ["id", "name", "department"]

        with patch("app.api.employees.get_current_user", return_value=mock_user), patch(
            "app.api.employees.get_org_config", return_value=limited_fields
        ), patch("app.api.employees.rate_limiter", return_value=None):

            # Mock database query result
            mock_db.execute = AsyncMock()
            mock_result = MagicMock()
            mock_result.all.return_value = [(emp, 3) for emp in mock_employees]
            mock_db.execute.return_value = mock_result

            # Call the function
            result = await list_employees(
                org_id=1, current_user=mock_user, db=mock_db, limit=3, cursor=None
            )

            # Assertions
            assert result["count"] == 3

            # Check that only configured fields are returned
            for emp in result["results"]:
                assert "id" in emp
                assert "name" in emp
                assert "department" in emp
                # These fields should NOT be present
                assert "location" not in emp
                assert "position" not in emp
                assert "status" not in emp
                assert "company" not in emp

    @pytest.mark.asyncio
    async def test_list_employees_org_id_mismatch(self, mock_db, mock_org_config):
        """Test 404 is raised if org_id does not match current_user.org_id"""
        with patch("app.api.employees.get_current_user", return_value=mock_user), patch(
            "app.api.employees.get_org_config", return_value=mock_org_config
        ), patch("app.api.employees.rate_limiter", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await list_employees(
                    org_id=999,  # Mismatched org_id
                    current_user=mock_user,
                    db=mock_db,
                    limit=3,
                    cursor=None,
                )
            assert exc_info.value.status_code == 404
            assert exc_info.value.detail == "Organization not found"
