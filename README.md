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
└── tests/
``` 