# Topptur og Frikjøring FastAPI

A FastAPI application for managing members and synchronizing member data from external sources for the Topptur og Frikjøring system.

## Project Structure

```
app/
├── main.py                 # Application entry point
├── api/
│   └── membership.py       # Member API endpoints
├── services/
│   ├── sync_members.py     # Member synchronization service
│   └── external_apis.py    # External API client
├── db/
│   └── database.py         # Database configuration
├── models/
│   └── member.py           # SQLAlchemy models and schemas
└── requirements.txt        # Python dependencies
```

## Requirements

- Python 3.8+
- PostgreSQL (for data persistence)
- pip (Python package manager)

### Dependencies

- **fastapi** - Modern web framework for building APIs
- **uvicorn** - ASGI server for running FastAPI
- **sqlalchemy** - SQL toolkit and ORM
- **psycopg2** - PostgreSQL database adapter
- **httpx** - Async HTTP client for external API calls

## Installation

### 1. Clone or extract the project

```bash
cd topptur-og-frikjoring-fastAPI
```

### 2. Create a virtual environment (recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r app/requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```
DATABASE_URL=postgresql://username:password@localhost:5432/topptur_frikjoring
EXTERNAL_API_URL=https://api.example.com
```

### 5. Initialize the database

```bash
python
>>> from app.models.member import Base
>>> from app.db.database import engine
>>> Base.metadata.create_all(bind=engine)
>>> exit()
```

## Running the Application

### Development Mode

```bash
# From the project root
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The application will be available at `http://localhost:8000`

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### Health Check
- **GET** `/health` - Check application health status

### Members
- **GET** `/api/members/` - Get all members
- **GET** `/api/members/{member_id}` - Get a specific member
- **POST** `/api/members/` - Create a new member
  - Query parameters: `name`, `email`, `phone` (optional)
- **POST** `/api/members/sync` - Sync members from external API

## Documentation

Once the application is running:

- **Swagger UI** - Interactive API docs: `http://localhost:8000/docs`
- **ReDoc** - Alternative API docs: `http://localhost:8000/redoc`

## Project Components

### Models (`app/models/member.py`)
- `Member` - SQLAlchemy ORM model for members table
- `MemberSchema` - Schema class for member data

### Database (`app/db/database.py`)
- Database engine configuration
- Session management
- `get_db()` dependency for FastAPI endpoints

### Services (`app/services/`)
- **sync_members.py** - Business logic for member operations
- **external_apis.py** - HTTP client for external API integration

### API Routes (`app/api/membership.py`)
- RESTful endpoints for member management
- Dependency injection for database sessions

## Configuration

### Database
Configure your PostgreSQL connection string in the `.env` file:
```
DATABASE_URL=postgresql://user:password@hostname:5432/database_name
```

### External API
Set the external API base URL in the `.env` file:
```
EXTERNAL_API_URL=https://api.example.com
```

## Development

### Adding New Endpoints
1. Create new router in `app/api/`
2. Include router in `app/main.py`

### Adding New Models
1. Define models in `app/models/`
2. Update database creation in `app/main.py`

### Adding New Services
1. Create service class in `app/services/`
2. Implement business logic
3. Use in API endpoints via dependency injection

## Error Handling

The API includes standard HTTP error responses:
- **400** - Bad Request (validation errors)
- **404** - Not Found (resource doesn't exist)
- **500** - Internal Server Error

## Logging

Logging is configured for all services. Check logs for:
- Database operations
- External API calls
- Member synchronization status

## Testing

Recommended testing approach:
1. Use the Swagger UI at `/docs` for manual testing
2. Create unit tests for services
3. Create integration tests for API endpoints

## Performance Considerations

- Database queries use SQLAlchemy ORM with indexing on common columns
- Async HTTP client for non-blocking external API calls
- Connection pooling for database connections

## Future Enhancements

- [ ] Authentication and authorization
- [ ] Rate limiting
- [ ] Pagination for member lists
- [ ] Advanced filtering and search
- [ ] Member activity tracking
- [ ] Bulk member import/export
- [ ] Email notifications
- [ ] Member reporting

## License

Add your license information here.

## Contact

For questions or issues, contact the development team.
