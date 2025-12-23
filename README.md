# Topptur og Frikjøring FastAPI

A FastAPI application for managing members and synchronizing member data from external sources for the Topptur og Frikjøring system.

## Live API

The API is deployed on Render and can be accessed at:
- **API Documentation (Swagger UI):** https://topptur-og-frikjoring-fastapi.onrender.com/docs
- **Alternative Documentation (ReDoc):** https://topptur-og-frikjoring-fastapi.onrender.com/redoc

## Project Structure

```
app/
├── main.py                     # Application entry point
├── api/
│   └── membership.py           # Member API endpoints
├── services/
│   ├── sync_members.py         # Member synchronization orchestrator
│   ├── external_tfshopAPI.py   # TF Shop WooCommerce API client
│   └── external_ntnuiAPI.py    # NTNUI API client
├── core/
│   └── security.py             # API key authentication
├── db/
│   └── database.py             # Database configuration
├── models/
│   └── member.py               # SQLAlchemy models and schemas
└── requirements.txt            # Python dependencies
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

```env
# Database connection
DATABASE_URL=postgresql://username:password@localhost:5432/topptur_frikjoring

# API Keys for authentication
fastapi_key_superuser=your-secure-superuser-key-here
fast_api_key_user=your-secure-user-key-here

# TF Shop WooCommerce API
consumer_key=ck_your_woocommerce_consumer_key
consumer_secret=cs_your_woocommerce_consumer_secret

# NTNUI API
devNTNUIApiKey=your-ntnui-api-key-here
```

**Security Notes:**
- Generate strong, random API keys (32+ characters recommended)
- Never commit `.env` file to version control
- Use different keys for development and production
- For production (Render/GitHub Actions), set these as environment variables

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

### Authentication

All endpoints except `/health` and `/` require API key authentication via the `X-API-Key` header.

**Two API Key Levels:**
1. **User API Key** (`fast_api_key_user`) - Read-only access (GET requests)
2. **Superuser API Key** (`fastapi_key_superuser`) - Full access (all operations)

### Public Endpoints (No API Key Required)
- **GET** `/` - Root endpoint with API information
- **GET** `/health` - Check application health status

### Protected Endpoints

#### Read Operations (User or Superuser API Key)
- **GET** `/api/members/` - Get all members
- **GET** `/api/members/{telephone_number}` - Get a specific member by phone number

#### Write Operations (Superuser API Key Only)
- **POST** `/api/members/` - Create a new member
  - Query parameters: `name`, `email`, `telephone_number`, `tf_valid`, `tf_valid_until`, `ntnui_valid`, `ntnui_valid_until`
- **POST** `/api/members/sync/tfshop` - Sync members from TF Shop WooCommerce API
- **POST** `/api/members/sync/ntnui` - Sync members from NTNUI API
- **POST** `/api/members/sync/all` - Sync members from both APIs in parallel
- **POST** `/api/members/sync` - Sync from provided JSON data (testing only)
  - Body: `{"tf_data": [...], "ntnui_data": [...]}`
- **DELETE** `/api/members/reset` - Reset database (delete all members) ⚠️

## Testing & CLI Commands

### Member Sync CLI

Run member synchronization from command line using JSON files:

```bash
# Sync from both TF and NTNUI data files
python sync_cli.py --tf tests/testdata/tf1.json --ntnui tests/testdata/ntnui1.json

# Sync only TF data
python sync_cli.py --tf tests/testdata/tf1.json

# Sync only NTNUI data
python sync_cli.py --ntnui tests/testdata/ntnui1.json
```

### API Calls from Terminal

**All API calls (except `/health` and `/`) require the `X-API-Key` header.**

#### Health check (no API key required)
```bash
# PowerShell
Invoke-WebRequest -Uri "http://localhost:8000/health" -Method GET

# Bash/curl
curl http://localhost:8000/health
```

#### Get all members (requires user or superuser API key)
```bash
# PowerShell
$headers = @{"X-API-Key" = "your-user-or-superuser-key"}
Invoke-WebRequest -Uri "http://localhost:8000/api/members/" -Method GET -Headers $headers

# Bash/curl
curl -H "X-API-Key: your-user-or-superuser-key" http://localhost:8000/api/members/
```

#### Get specific member (requires user or superuser API key)
```bash
# PowerShell
$headers = @{"X-API-Key" = "your-user-or-superuser-key"}
Invoke-WebRequest -Uri "http://localhost:8000/api/members/+4791110001" -Method GET -Headers $headers

# Bash/curl
curl -H "X-API-Key: your-user-or-superuser-key" "http://localhost:8000/api/members/+4791110001"
```

#### Reset database (requires superuser API key only)
```bash
# PowerShell
$headers = @{"X-API-Key" = "your-superuser-key"}
Invoke-WebRequest -Uri "http://localhost:8000/api/members/reset" -Method DELETE -Headers $headers

# Bash/curl
curl -X DELETE -H "X-API-Key: your-superuser-key" http://localhost:8000/api/members/reset
```

#### Sync members via API (requires superuser API key only)
```bash
# Sync from TF Shop only
curl -X POST "http://localhost:8000/api/members/sync/tfshop" \
  -H "X-API-Key: your-superuser-key"

# Sync from NTNUI only
curl -X POST "http://localhost:8000/api/members/sync/ntnui" \
  -H "X-API-Key: your-superuser-key"

# Sync from both sources (recommended)
curl -X POST "http://localhost:8000/api/members/sync/all" \
  -H "X-API-Key: your-superuser-key"

# Sync with test data (PowerShell)
$headers = @{
    "X-API-Key" = "your-superuser-key"
    "Content-Type" = "application/json"
}
$body = @{
    tf_data = (Get-Content tests/testdata/tf1.json | ConvertFrom-Json)
    ntnui_data = (Get-Content tests/testdata/ntnui1.json | ConvertFrom-Json)
} | ConvertTo-Json -Depth 10

Invoke-WebRequest -Uri "http://localhost:8000/api/members/sync" -Method POST -Headers $headers -Body $body
```

### Complete Test Workflow

Run all three test scenarios sequentially:

```bash
# Set your API key (replace with your actual superuser key)
export SUPERUSER_KEY="your-superuser-key"  # Bash
$superuser_key = "your-superuser-key"      # PowerShell

# Reset database (requires superuser key)
curl -X DELETE -H "X-API-Key: $SUPERUSER_KEY" http://localhost:8000/api/members/reset

# Day 1 - Initial sync
python sync_cli.py --tf tests/testdata/tf1.json --ntnui tests/testdata/ntnui1.json

# Day 2 - New memberships added
python sync_cli.py --tf tests/testdata/tf2.json --ntnui tests/testdata/ntnui2.json

# Day 3 - Natural expiration + new member
python sync_cli.py --tf tests/testdata/tf3.json --ntnui tests/testdata/ntnui3.json

# Verify results (can use user or superuser key)
curl -H "X-API-Key: your-user-or-superuser-key" http://localhost:8000/api/members/
```

## Documentation

Once the application is running:

- **Swagger UI** - Interactive API docs: `http://localhost:8000/docs`
- **ReDoc** - Alternative API docs: `http://localhost:8000/redoc`

## Project Components

### Models (`app/models/member.py`)
- `Member` - SQLAlchemy ORM model (primary key: telephone_number with +47 prefix)
- `MemberSchema` - Schema for member data validation

### Database (`app/db/database.py`)
- PostgreSQL connection with SQLAlchemy
- Session management with `get_db()` dependency

### Services (`app/services/`)
- **sync_members.py** - Orchestrates member sync from multiple sources
- **external_tfshopAPI.py** - WooCommerce API client with pagination
  - Fetches orders, filters for membership products
  - Normalizes Norwegian phone numbers to +47 format
- **external_ntnuiAPI.py** - NTNUI API client with pagination
  - Fetches memberships (phone numbers already have country code)

### API Routes (`app/api/membership.py`)
- RESTful endpoints with async support
- Dependency injection for database and security
- Separate endpoints for each data source

### Security (`app/core/security.py`)
- Two-tier API key authentication (user/superuser)
- Header-based authentication (`X-API-Key`)

## Deployment

### Environment Variables for Production

```env
DATABASE_URL=postgresql://user:password@host:5432/database
fastapi_key_superuser=your-production-superuser-key
fast_api_key_user=your-production-user-key
consumer_key=ck_woocommerce_key
consumer_secret=cs_woocommerce_secret
devNTNUIApiKey=ntnui-api-key
```

### Render Deployment

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Set environment variables:
   - `DATABASE_URL`, `fastapi_key_superuser`, `fast_api_key_user`
   - `consumer_key`, `consumer_secret`, `devNTNUIApiKey`
4. Build: `pip install -r app/requirements.txt`
5. Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### GitHub Actions

Add secrets in repository Settings → Secrets and variables → Actions:
- `DATABASE_URL`
- `FASTAPI_KEY_SUPERUSER`
- `CONSUMER_KEY`, `CONSUMER_SECRET`
- `DEVNTNUIAPIKEY`

Example workflow:
```yaml
- name: Sync members
  env:
    API_KEY: ${{ secrets.FASTAPI_KEY_SUPERUSER }}
  run: |
    curl -X POST "https://your-api.com/api/members/sync/all" \
      -H "X-API-Key: $API_KEY"
```

## Configuration

### Database
PostgreSQL connection in `.env`:
```
DATABASE_URL=postgresql://user:password@hostname:5432/database_name
```

### External APIs
**TF Shop WooCommerce:**
- `consumer_key` - WooCommerce REST API consumer key
- `consumer_secret` - WooCommerce REST API consumer secret
- Fetches orders from product ID 4223 (membership)
- Filters orders containing "Medlemskap i NTNUI Topptur og Frikjøring"
- Normalizes phone numbers to +47 format

**NTNUI API:**
- `devNTNUIApiKey` - NTNUI dev API key
- Fetches memberships from `dev.api.ntnui.no/groups/esport/memberships/`
- Phone numbers already include country code

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
- **401** - Unauthorized (missing API key)
- **403** - Forbidden (invalid API key or insufficient permissions)
- **400** - Bad Request (validation errors)
- **404** - Not Found (resource doesn't exist)
- **500** - Internal Server Error

## Logging

Logging is configured for all services. Check logs for:
- Database operations
- External API calls
- Member synchronization status

## Testing

### Running Tests

The project includes comprehensive tests for API authentication and user scenarios.

**Install test dependencies:**
```bash
pip install -r app/requirements.txt
```

**Run all tests:**
```bash
# Run all tests with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/test_api_authentication.py -v
pytest tests/test_user_scenarios.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

### Test Structure

- **test_api_authentication.py** - Tests API key authentication
  - Public endpoints (no key required)
  - Missing/invalid API keys
  - User-level key permissions
  - Superuser-level key permissions
  - Key comparison tests

- **test_user_scenarios.py** - Tests different user types
  - Read-only user (user key)
  - Admin user (superuser key)
  - Anonymous user (no key)
  - Malicious user (security tests)
  - Automated system (batch operations)

### Manual Testing

Use the Swagger UI for interactive testing:
1. Go to `http://localhost:8000/docs`
2. Click "Authorize" button
3. Enter your API key in the `X-API-Key` field
4. Test endpoints interactively

## Performance Considerations

- Async/await for non-blocking API calls to TF Shop and NTNUI
- Parallel data fetching with `asyncio.gather()`
- Pagination for large datasets (100 items per page)
- Phone number normalization for consistent matching
- Database indexing on telephone_number (primary key)
- SQLAlchemy connection pooling

## Future Enhancements

- [x] API key authentication and authorization
- [x] Separate sync endpoints per data source
- [x] Async parallel API calls
- [x] Phone number normalization
- [ ] Rate limiting
- [ ] Pagination for member lists
- [ ] Caching for external API responses
- [ ] Member activity tracking
- [ ] Email notifications
- [ ] API key rotation mechanism
- [ ] Audit logging

## License

Add your license information here.

## Contact

For questions or issues, contact the development team.
