# Employee Search Service (fast-api)

A simple, secure, and configurable employee directory microservice for HR organizations.

## Stack
- **Backend:** FastAPI (Python)
- **Database:** PostgreSQL
- **Caching:** Redis (for organization config and employee count)
- **Containerization:** Docker

## Features
- Organization-specific employee directory with configurable columns
- Secure, isolated data per organization
- RESTful API for employee search and listing
- Containerized for easy deployment

## Caching with Redis

This service uses **Redis** for caching in two main scenarios:

- **Organization Configuration Cache:**
  - Organization-specific configuration data is cached in Redis to reduce database load and improve response times for repeated config lookups.
- **Employee Count Cache:**
  - The total number of employees per organization is cached in Redis to speed up count queries, especially for large datasets or frequent requests.

Redis caching helps ensure the service remains fast and scalable, especially under high load or with large organizations.

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
## Demo: Using the Employees API with `curl` and `jq`

You can interact with the Employee Search API using standard HTTP tools. The API uses HTTP Basic Auth. Example users (all with password `testpass`) are seeded by default, e.g. `admin_techcorp`, `hr_manager`, etc. (all users info are in `init.sql`)

### List Employees (all, default pagination)

```bash
curl -u admin_techcorp:testpass "http://localhost:8000/employees" | jq
```

### Filter by Department

```bash
curl -u admin_techcorp:testpass "http://localhost:8000/employees?department=Engineering" | jq
```

### Paginate Results

```bash
curl -u admin_techcorp:testpass "http://localhost:8000/employees?limit=2&offset=2" | jq
```

### Show Only Employee Names

```bash
curl -u admin_techcorp:testpass "http://localhost:8000/employees" | jq '.results[].name'
```

### Example Response

```json
{
  "limit": 20,
  "offset": 0,
  "count": 10,
  "results": [
    {
      "name": "John Smith",
      "department": "Engineering",
      "position": "Senior Software Engineer",
      "location": "San Francisco",
      "contact_info": "john.smith@techcorp.com",
      "status": "active",
      "company": "TechCorp Inc.",
      "org_id": 1
    },
    ...
  ]
}
```

### Invalid credentials example 

```bash
curl -u fakeuser:testpass "http://localhost:8000/employees" | jq 
```
Response:
```json
{
  "detail": "Invalid credentials"
}
```

### Rate Limit Error Example

If you make too many requests in a short period, the API will return a rate limit error (HTTP 429). You can simulate this by sending multiple requests quickly:

```bash
for i in {1..20}; do
  curl -u admin_techcorp:testpass "http://localhost:8000/employees"
done
```

If the rate limit is exceeded, you will receive a response like:

```json
{
  "detail":"Rate limit exceeded. Please try again later"
}
```

You can also use `jq` to pretty-print the output and spot the error more easily:

```bash
for i in {1..20}; do
  curl -u admin_techcorp:testpass "http://localhost:8000/employees" | jq
done
```

**Note:**  
- You must use a valid username/password (see the `init.sql` for seeded users).

---

## OpenAPI & API Documentation

This service provides a fully documented OpenAPI (Swagger) schema, which you can use to explore, share, or generate client SDKs for the API.

- **Swagger UI:**
  - Interactive docs at: [http://localhost:8000/docs](http://localhost:8000/docs)

  ![Alt text](./screen_images/Swagger.png "Swagger UI")
- **ReDoc:**
  - Alternative docs at: [http://localhost:8000/redoc](http://localhost:8000/redoc)

  ![Alt text](./screen_images/ReDoc.png "Swagger UI")
- **Raw OpenAPI JSON:**
  - Download or share the OpenAPI schema at: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)
  - Example:
    ```bash
    curl http://localhost:8000/openapi.json | jq
    ```
   - Sample response:
    ```json
      {
         "openapi": "3.1.0",
         "info": {
            "title": "FastAPI",
            "version": "0.1.0"
         },
         "paths": {
         ......
         }
      }
   ```
You can import the OpenAPI JSON into tools like Postman, Swagger Editor, or use it to generate client SDKs in various languages.

---

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

---

## AI Tools & Best Practices

### What AI tools do our developers use?
- **Cursor with GPT-4.1 model of OpenAI**: For code completion, suggestions, and boilerplate generation.

### How do these tools assist?
- **Coding**: Suggest alternative implementations, and help generate repetitive code structures, speeding up development.
- **Debugging**: Developers use AI chat assistants to explain error messages, suggest fixes, and analyze stack traces.
- **Testing**: AI can help generate test cases, review test coverage, and suggest edge cases.
- **Documentation**: Tools like ChatGPT help me in drafting and refining documentation, README sections, and code comments.

### Best Practices for AI Tool Usage
- **Review All AI-Generated Code**: Always review, test, and understand code suggested by AI before merging.
- **Use AI for Ideation, Not as a Source of Truth**: Treat AI suggestions as starting points, not final answers.
- **Maintain Security & Privacy**: Never share sensitive code, credentials, or proprietary data with external AI tools.
- **Document AI-Assisted Changes**: Note in PRs or commit messages when significant code was generated or heavily influenced by AI.
- **Continuous Learning**: Stay updated on AI tool capabilities and limitations to maximize productivity and code quality. 