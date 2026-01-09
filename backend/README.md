# AI Context Bridge - FastAPI Backend

Cloud storage and AI-powered summarization backend for the AI Context Bridge Chrome extension.

## Features

- **Cloud Storage**: Persistent PostgreSQL storage for conversation contexts
- **AI Summarization**: GPT-4 powered intelligent summarization
- **RESTful API**: FastAPI-based async API with automatic OpenAPI docs
- **Google Cloud Ready**: Configured for deployment to Cloud Run + Cloud SQL

## Tech Stack

- FastAPI (Python async web framework)
- PostgreSQL (via Cloud SQL or local)
- SQLAlchemy 2.0 (async ORM)
- Alembic (database migrations)
- OpenAI API (GPT-4 summarization)
- Docker (containerization)

## Local Development Setup

### Prerequisites

- Python 3.11+
- pip and venv

### Installation

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt greenlet
   ```

4. **Create `.env` file:**
   ```bash
   cp .env.example .env
   ```

5. **Edit `.env` and add your OpenAI API key** (optional for local testing):
   ```
   OPENAI_API_KEY=sk-your-api-key-here
   ```

### Running Locally

1. **Run database migrations:**
   ```bash
   alembic upgrade head
   ```

2. **Start the server:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

3. **Access the API:**
   - API: http://localhost:8000
   - Interactive API docs: http://localhost:8000/docs
   - Alternative docs: http://localhost:8000/redoc

### Testing the API

**Health check:**
```bash
curl http://localhost:8000/api/v1/health
```

**Create a context:**
```bash
curl -X POST http://localhost:8000/api/v1/contexts \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "chatgpt",
    "messages": [
      {"role": "user", "content": "Hello", "timestamp": "2025-01-08T10:00:00Z"},
      {"role": "assistant", "content": "Hi there!", "timestamp": "2025-01-08T10:00:05Z"}
    ],
    "formatted": "**USER**: Hello\n\n**ASSISTANT**: Hi there!",
    "generate_ai_summary": true
  }'
```

**List contexts:**
```bash
curl http://localhost:8000/api/v1/contexts
```

## API Endpoints

### Health & Info
- `GET /` - Root endpoint
- `GET /api/v1/health` - Health check
- `GET /docs` - Interactive API documentation

### Contexts
- `POST /api/v1/contexts` - Create new context (with optional AI summarization)
- `GET /api/v1/contexts` - List contexts (with pagination)
- `GET /api/v1/contexts/{id}` - Get specific context
- `DELETE /api/v1/contexts/{id}` - Delete context

### Summarization
- `POST /api/v1/summarize` - Standalone AI summarization

## Database

### Local (SQLite)
By default, uses SQLite for local development:
```
DATABASE_URL=sqlite+aiosqlite:///./ai_context_bridge.db
```

### Production (PostgreSQL)
For Google Cloud deployment:
```
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname
```

### Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "Description"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback:
```bash
alembic downgrade -1
```

## Google Cloud Deployment

### Prerequisites
- Google Cloud account
- `gcloud` CLI installed and configured
- Docker installed (for local testing)

### Setup Steps

1. **Create Google Cloud project:**
   ```bash
   gcloud projects create ai-context-bridge
   gcloud config set project ai-context-bridge
   ```

2. **Enable required APIs:**
   ```bash
   gcloud services enable \
     cloudbuild.googleapis.com \
     run.googleapis.com \
     sqladmin.googleapis.com \
     secretmanager.googleapis.com
   ```

3. **Create Cloud SQL PostgreSQL instance:**
   ```bash
   gcloud sql instances create ai-context-db \
     --database-version=POSTGRES_14 \
     --tier=db-f1-micro \
     --region=us-central1 \
     --root-password=YOUR_SECURE_PASSWORD
   ```

4. **Create database:**
   ```bash
   gcloud sql databases create ai_context_bridge --instance=ai-context-db
   ```

5. **Store secrets:**
   ```bash
   # OpenAI API Key
   echo -n "sk-your-key" | gcloud secrets create openai-api-key --data-file=-

   # Database URL
   echo -n "postgresql+asyncpg://postgres:PASSWORD@/ai_context_bridge?host=/cloudsql/PROJECT:REGION:ai-context-db" | \
     gcloud secrets create database-url --data-file=-
   ```

6. **Build and deploy:**
   ```bash
   # Build container
   gcloud builds submit --tag gcr.io/ai-context-bridge/api

   # Deploy to Cloud Run
   gcloud run deploy ai-context-api \
     --image gcr.io/ai-context-bridge/api \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --add-cloudsql-instances ai-context-bridge:us-central1:ai-context-db \
     --set-secrets DATABASE_URL=database-url:latest,OPENAI_API_KEY=openai-api-key:latest \
     --memory 512Mi \
     --cpu 1
   ```

7. **Get service URL:**
   ```bash
   gcloud run services describe ai-context-api \
     --platform managed \
     --region us-central1 \
     --format 'value(status.url)'
   ```

8. **Update extension config:**
   - Edit `/config.js` in the extension
   - Update `PROD_BASE_URL` with your Cloud Run URL
   - Change `getBaseURL()` to return `PROD_BASE_URL`

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite+aiosqlite:///./ai_context_bridge.db` |
| `OPENAI_API_KEY` | OpenAI API key for GPT-4 | Required for AI features |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-4-turbo-preview` |
| `PORT` | Server port | `8000` |
| `LOG_LEVEL` | Logging level | `info` |
| `ENV` | Environment (development/production) | `development` |

## Cost Estimates

### Google Cloud
- **Cloud SQL (db-f1-micro)**: ~$9/month
- **Cloud Run**: ~$0-5/month (low traffic)
- **Total GCP**: ~$10-15/month

### OpenAI API
- **GPT-4 Turbo**: ~$0.007 per summary
- **100 summaries/day**: ~$21/month
- **Alternative**: Use GPT-3.5-turbo (~$2/month)

## Security Notes

⚠️ **No Authentication**: This API has no authentication. Anyone can:
- Save contexts to your database
- Trigger OpenAI API calls (cost)
- List/read/delete any context

**Mitigations in place:**
- IP-based rate limiting (100 req/hour)
- Content size limits (1MB max, 500 messages max)
- Auto-delete after 30 days
- Input validation

**To add authentication later:**
- Implement JWT or API key authentication
- Add `user_id` column to contexts
- Filter contexts by authenticated user

## Project Structure

```
backend/
├── app/
│   ├── main.py           # FastAPI app entry point
│   ├── config.py         # Configuration
│   ├── database.py       # Database connection
│   ├── models.py         # SQLAlchemy models
│   ├── schemas.py        # Pydantic schemas
│   ├── api/routes/       # API endpoints
│   │   ├── contexts.py
│   │   ├── summarize.py
│   │   └── health.py
│   └── services/         # Business logic
│       ├── context_service.py
│       └── openai_service.py
├── alembic/              # Database migrations
├── Dockerfile            # Container config
├── requirements.txt      # Python dependencies
└── .env                  # Environment variables
```

## Troubleshooting

### "No module named 'greenlet'"
```bash
pip install greenlet
```

### Database connection errors
- Check `DATABASE_URL` in `.env`
- Ensure database exists
- Run migrations: `alembic upgrade head`

### OpenAI API errors
- Verify `OPENAI_API_KEY` is set
- Check API quota/billing
- Try setting `generate_ai_summary: false` in requests

### CORS errors in extension
- Check `CORS_ORIGINS` in config
- Ensure extension URL is allowed
- Verify API is running

## Development

**Run with auto-reload:**
```bash
uvicorn app.main:app --reload
```

**View logs:**
```bash
# Local
tail -f logs/app.log

# Cloud Run
gcloud run logs tail ai-context-api --region us-central1
```

**Database shell:**
```bash
# SQLite
sqlite3 ai_context_bridge.db

# PostgreSQL (Cloud SQL)
gcloud sql connect ai-context-db --user=postgres
```

## License

This is part of the AI Context Bridge project.
