import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException
from app.api.employees import list_employees
from app.db.models import Employee, User, Organization
from app.main import app

# Test client
client = TestClient(app)

# Mock data
mock_user = User(
    id=1,
    username="testuser",
    # Raw passwords are: "testpass"
    hashed_password="mock_hash",
    org_id=1
)

mock_organization = Organization(
    id=1,
    name="Test Org",
    employee_fields=["id", "name", "department", "location", "position", "status", "company"]
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
        company="Tech Corp"
    ),
    Employee(
        id=2,
        org_id=1,
        name="Jane Smith",
        department="Marketing",
        location="New York",
        position="Marketing Manager",
        status="active",
        company="Tech Corp"
    ),
    Employee(
        id=3,
        org_id=1,
        name="Bob Johnson",
        department="Engineering",
        location="San Francisco",
        position="Senior Engineer",
        status="inactive",
        company="Tech Corp"
    )
]

@pytest.fixture
def mock_org_config():
    """Mock organization configuration"""
    return ["id", "name", "department", "location", "position", "status", "company"]

class TestListEmployees:
    """Test cases for the list_employees endpoint"""

    @pytest.mark.asyncio
    async def test_list_employees_success(self, mock_db, mock_org_config):
        """Test successful employee listing with default parameters"""
        # Mock dependencies
        with patch('app.api.employees.get_current_user', return_value=mock_user), \
             patch('app.api.employees.get_org_config', return_value=mock_org_config), \
             patch('app.api.employees.rate_limiter', return_value=None):
            
            # Mock database query result
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = mock_employees
            # Configure the AsyncMock to return our result when awaited
            mock_db.execute.side_effect = lambda *args, **kwargs: mock_result
            
            # Call the function
            result = await list_employees(
                current_user=mock_user,
                db=mock_db,
                limit=20,
                offset=0,
            )
            
            # Assertions
            assert result["limit"] == 20
            assert result["offset"] == 0
            assert result["count"] == 3
            assert len(result["results"]) == 3
            
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
        with patch('app.api.employees.get_current_user', return_value=mock_user), \
             patch('app.api.employees.get_org_config', return_value=mock_org_config), \
             patch('app.api.employees.rate_limiter', return_value=None):
            
            # Mock database query result for filtered results
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_employees[0]]  # Only Engineering dept
            mock_db.execute.return_value = mock_result
            
            # Call the function with filters
            result = await list_employees(
                current_user=mock_user,
                db=mock_db,
                limit=20,
                offset=0,
                department="Engineering",
                status="active"
            )
            
            # Assertions
            assert result["count"] == 1
            assert result["results"][0]["department"] == "Engineering"
            assert result["results"][0]["status"] == "active"

    @pytest.mark.asyncio
    async def test_list_employees_pagination(self, mock_db, mock_org_config):
        """Test employee listing with pagination"""
        with patch('app.api.employees.get_current_user', return_value=mock_user), \
             patch('app.api.employees.get_org_config', return_value=mock_org_config), \
             patch('app.api.employees.rate_limiter', return_value=None):
            
            # Mock database query result
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = mock_employees[:2]  # First 2 employees
            mock_db.execute.return_value = mock_result
            
            # Call the function with pagination
            result = await list_employees(
                current_user=mock_user,
                db=mock_db,
                limit=2,
                offset=0
            )
            
            # Assertions
            assert result["limit"] == 2
            assert result["offset"] == 0
            assert result["count"] == 2
            assert len(result["results"]) == 2

    @pytest.mark.asyncio
    async def test_list_employees_organization_not_found(self, mock_db):
        """Test when organization configuration is not found"""
        with patch('app.api.employees.get_current_user', return_value=mock_user), \
             patch('app.api.employees.get_org_config', return_value=None), \
             patch('app.api.employees.rate_limiter', return_value=None):
            
            # Call the function and expect HTTPException
            with pytest.raises(HTTPException) as exc_info:
                await list_employees(
                    current_user=mock_user,
                    db=mock_db,
                    limit=20,
                    offset=0
                )
            
            assert exc_info.value.status_code == 404
            assert exc_info.value.detail == "Organization not found"

    @pytest.mark.asyncio
    async def test_list_employees_all_filters(self, mock_db, mock_org_config):
        """Test employee listing with all possible filters"""
        with patch('app.api.employees.get_current_user', return_value=mock_user), \
             patch('app.api.employees.get_org_config', return_value=mock_org_config), \
             patch('app.api.employees.rate_limiter', return_value=None):
            
            # Mock database query result
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_employees[0]]
            mock_db.execute.return_value = mock_result
            
            # Call the function with all filters
            result = await list_employees(
                current_user=mock_user,
                db=mock_db,
                limit=10,
                offset=0,
                status="active",
                location="San Francisco",
                company="Tech Corp",
                department="Engineering",
                position="Software Engineer"
            )
            
            # Assertions
            assert result["limit"] == 10
            assert result["count"] == 1
            assert result["results"][0]["status"] == "active"
            assert result["results"][0]["location"] == "San Francisco"
            assert result["results"][0]["company"] == "Tech Corp"
            assert result["results"][0]["department"] == "Engineering"
            assert result["results"][0]["position"] == "Software Engineer"

    @pytest.mark.asyncio
    async def test_list_employees_empty_result(self, mock_db, mock_org_config):
        """Test employee listing with no results"""
        with patch('app.api.employees.get_current_user', return_value=mock_user), \
             patch('app.api.employees.get_org_config', return_value=mock_org_config), \
             patch('app.api.employees.rate_limiter', return_value=None):
            
            # Mock database query result with empty list
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_db.execute.return_value = mock_result
            
            # Call the function
            result = await list_employees(
                current_user=mock_user,
                db=mock_db,
                limit=20,
                offset=0
            )
            
            # Assertions
            assert result["count"] == 0
            assert len(result["results"]) == 0

    @pytest.mark.asyncio
    async def test_list_employees_limited_fields(self, mock_db):
        """Test employee listing with limited configured fields"""
        limited_fields = ["id", "name", "department"]
        
        with patch('app.api.employees.get_current_user', return_value=mock_user), \
             patch('app.api.employees.get_org_config', return_value=limited_fields), \
             patch('app.api.employees.rate_limiter', return_value=None):
            
            # Mock database query result
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = mock_employees
            mock_db.execute.return_value = mock_result
            
            # Call the function
            result = await list_employees(
                current_user=mock_user,
                db=mock_db,
                limit=20,
                offset=0
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
