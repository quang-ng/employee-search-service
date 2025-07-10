# Employee Search Service (ast-api)

A simple, secure, and configurable employee directory microservice for HR organizations.

## Stack
- **Backend:** FastAPI (Python)
- **Database:** PostgreSQL
- **Containerization:** Docker

## Features
- Organization-specific employee directory with configurable columns
- Secure, isolated data per organization
- RESTful API for employee search and listing
- Containerized for easy deployment

## Project Structure
```
employee-search-service/
├── app/
│   ├── api/                # API route handlers
│   ├── config/             # Organization-level config logic
│   ├── db/                 # Database models and access
│   ├── middleware/         # Auth, org isolation, etc.
│   ├── services/           # Business logic
│   └── main.py             # FastAPI entrypoint
├── Dockerfile              # Containerization
├── requirements.txt        # Python dependencies
├── README.md
├── pytest.ini             # Test configuration
├── run_tests.py           # Test runner script
└── tests/
    └── test_api_employees.py  # API unit tests
```

## Testing

The project includes comprehensive unit tests for the employee search API. The tests cover:

- **Authentication and authorization**
- **Employee listing with various filters**
- **Pagination functionality**
- **Organization configuration handling**
- **Error cases and edge conditions**

### Running Tests

1. **Install test dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run tests using pytest:**
   ```bash
   pytest tests/ -v
   ```

3. **Run tests using the test runner script:**
   ```bash
   python run_tests.py
   ```

4. **Run specific test file:**
   ```bash
   pytest tests/test_api_employees.py -v
   ```

### Test Coverage

The tests cover the following scenarios:

- ✅ Successful employee listing with default parameters
- ✅ Employee filtering by department, status, location, company, position
- ✅ Pagination with limit and offset
- ✅ Organization not found error handling
- ✅ Empty result sets
- ✅ Limited field configuration
- ✅ Input validation (invalid limit/offset values)
- ✅ Unauthorized access handling

### Test Structure

- **TestListEmployees**: Unit tests for the `list_employees` function
- **TestEmployeeAPIEndpoints**: Integration tests for HTTP endpoints 