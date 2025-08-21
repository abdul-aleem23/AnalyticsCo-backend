# QR Analytics Platform - Backend

FastAPI backend for the QR Analytics Platform, providing comprehensive QR code tracking and analytics for marketing campaigns.

## Features

- **Campaign Management**: Create and manage QR code campaigns
- **Anonymous Tracking**: GDPR-compliant scan tracking without personal data
- **Real-time Analytics**: Live dashboard with charts and metrics  
- **Admin Authentication**: JWT-based admin authentication system
- **QR Code Generation**: Automatic QR code creation for campaigns
- **Client Dashboards**: Campaign ID-based access for clients
- **Data Export**: Excel export functionality for campaign data

## Quick Start

### Local Development

1. **Clone and setup**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Setup database**:
   ```bash
   # Make sure PostgreSQL is running
   alembic upgrade head
   ```

4. **Run the application**:
   ```bash
   uvicorn app.main:app --reload
   ```

5. **Access the API**:
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

### Railway Deployment

1. **Install Railway CLI**:
   ```bash
   npm install -g @railway/cli
   ```

2. **Deploy to Railway**:
   ```bash
   railway login
   railway new qr-analytics-backend
   railway up
   ```

3. **Set environment variables** in Railway dashboard:
   - `DATABASE_URL` (automatically provided)
   - `SECRET_KEY`
   - `ADMIN_EMAIL` 
   - `ADMIN_PASSWORD`
   - `BASE_URL`

## API Endpoints

### Public Endpoints
- `GET /scan/{campaign_id}` - Track scan and redirect to target URL
- `GET /api/campaigns/{campaign_id}/validate` - Validate campaign exists
- `GET /api/campaigns/{campaign_id}/stats` - Get campaign analytics (if enabled)

### Admin Endpoints
- `POST /admin/login` - Admin authentication
- `GET /admin/dashboard/stats` - System-wide statistics
- `GET /admin/campaigns` - List all campaigns
- `POST /admin/campaigns` - Create new campaign
- `GET /admin/campaigns/{id}/qr` - Download QR code image
- `PUT /admin/campaigns/{id}/archive` - Archive campaign
- `PUT /admin/campaigns/{id}/access` - Toggle client access

## Database Schema

The application uses PostgreSQL with these main tables:
- `campaigns` - Campaign information and settings
- `scans` - Anonymous scan tracking data
- `admin_users` - Admin user accounts
- `privacy_requests` - GDPR compliance requests

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `SECRET_KEY` | JWT secret key | Required |
| `BASE_URL` | Application base URL | `http://localhost:8000` |
| `ADMIN_EMAIL` | Initial admin email | `admin@example.com` |
| `ADMIN_PASSWORD` | Initial admin password | Required |
| `ENVIRONMENT` | Environment mode | `development` |

## Architecture

```
app/
├── api/           # FastAPI route handlers
├── models/        # SQLAlchemy database models  
├── schemas/       # Pydantic data validation schemas
├── services/      # Business logic services
├── utils/         # Utility functions
├── config.py      # Application configuration
├── database.py    # Database connection setup
└── main.py        # FastAPI application entry point
```

## Development

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app
```

## Production Considerations

- Set strong `SECRET_KEY` in production
- Use environment variables for all sensitive config
- Enable HTTPS and set proper CORS origins
- Monitor database performance and add indexes as needed
- Set up database backups
- Configure log aggregation and monitoring