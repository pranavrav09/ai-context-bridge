# AI Context Bridge

A Chrome extension that enables seamless transfer of conversation context between different AI platforms (ChatGPT, Claude, Gemini, Poe) with cloud storage and AI-powered summarization.

[![Deploy to Cloud Run](https://github.com/pranavrav09/ai-context-bridge/actions/workflows/deploy-backend.yml/badge.svg)](https://github.com/pranavrav09/ai-context-bridge/actions/workflows/deploy-backend.yml)

## Features

- **Cross-Platform Context Transfer**: Extract conversations from one AI platform and inject them into another
- **Cloud Storage**: Save and sync conversation contexts across devices
- **AI Summarization**: Automatically generate intelligent summaries using GPT-4
- **Multi-Platform Support**: Works with ChatGPT, Claude, Gemini, and Poe
- **Privacy-Focused**: Client-side extraction with optional cloud backup
- **Automated CI/CD**: GitHub Actions pipeline for zero-downtime deployments

## Architecture

```
┌─────────────────┐
│ Chrome Extension│
│  (Frontend)     │
└────────┬────────┘
         │
         │ HTTPS
         │
┌────────▼────────┐      ┌──────────────┐      ┌──────────────┐
│   Cloud Run     │─────▶│  Cloud SQL   │      │   OpenAI     │
│  (FastAPI)      │      │ (PostgreSQL) │      │   API        │
└─────────────────┘      └──────────────┘      └──────────────┘
```

### Tech Stack

**Frontend (Chrome Extension)**:
- Vanilla JavaScript
- Chrome Extension Manifest V3
- Content Scripts for platform integration

**Backend (API)**:
- FastAPI (Python 3.11)
- SQLAlchemy (async)
- Alembic (migrations)
- OpenAI API integration

**Infrastructure**:
- Google Cloud Run (serverless containers)
- Cloud SQL (PostgreSQL 14)
- Google Container Registry
- GitHub Actions (CI/CD)

## Getting Started

### Prerequisites

- Google Chrome browser
- Python 3.11+ (for local backend development)
- Google Cloud account (for deployment)
- OpenAI API key (optional, for AI summaries)

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/pranavrav09/ai-context-bridge.git
cd ai-context-bridge
```

#### 2. Set Up Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload --port 8000
```

#### 3. Install Chrome Extension

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top-right)
3. Click "Load unpacked"
4. Select the `ai-context-bridge` directory (root folder)
5. The extension icon should appear in your toolbar

#### 4. Configure Extension

Edit `config.js` to point to your backend:

```javascript
// For local development
DEV_BASE_URL: "http://localhost:8000/api/v1",

// For production
PROD_BASE_URL: "https://your-cloud-run-url.run.app/api/v1",
```

## Usage

### Basic Workflow

1. **Extract Context**:
   - Go to ChatGPT, Claude, Gemini, or Poe
   - Have a conversation
   - Click the extension icon
   - Click "Extract Context"

2. **Save to Cloud** (Optional):
   - Click "Save to Cloud" 💾
   - AI-powered summary is automatically generated
   - Context is stored in cloud database

3. **Transfer Context**:
   - Open a different AI platform
   - Click the extension icon
   - Click "Load from Cloud" 📥 (if using cloud)
   - Or paste directly from clipboard
   - Click "Inject Context"

4. **Continue Conversation**:
   - The AI now has full context from the previous conversation
   - Continue seamlessly across platforms

### Example Use Cases

- **Compare AI Responses**: Ask the same question across multiple AI platforms
- **Specialized Tasks**: Use ChatGPT for coding, Claude for writing, Gemini for research
- **Context Preservation**: Save important conversations for later reference
- **Cross-Device Sync**: Access conversation contexts from any device

## API Endpoints

### Health Check
```bash
GET /api/v1/health
```

### Context Management
```bash
POST   /api/v1/contexts        # Create new context
GET    /api/v1/contexts        # List contexts (paginated)
GET    /api/v1/contexts/{id}   # Get specific context
DELETE /api/v1/contexts/{id}   # Delete context
```

### AI Summarization
```bash
POST   /api/v1/summarize       # Generate AI summary
```

Full API documentation available at: `http://localhost:8000/docs`

## Deployment

This project includes automated CI/CD with GitHub Actions.

### Quick Deploy to Google Cloud

See [CI-CD-SETUP.md](CI-CD-SETUP.md) for comprehensive deployment guide.

```bash
# 1. Set up GCP project
gcloud projects create ai-context-bridge

# 2. Enable required APIs
gcloud services enable cloudbuild.googleapis.com run.googleapis.com sqladmin.googleapis.com

# 3. Create Cloud SQL instance
gcloud sql instances create ai-context-db \
  --database-version=POSTGRES_14 \
  --tier=db-f1-micro \
  --region=us-central1

# 4. Deploy with GitHub Actions (automatic on push to main)
git push origin main
```

### Manual Deployment

```bash
cd backend

# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT_ID/api
gcloud run deploy ai-context-api \
  --image gcr.io/PROJECT_ID/api \
  --region us-central1 \
  --allow-unauthenticated
```

## Development

### Project Structure

```
ai-context-bridge/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/routes/        # API endpoints
│   │   ├── services/          # Business logic
│   │   ├── models.py          # Database models
│   │   └── main.py            # FastAPI app
│   ├── alembic/               # Database migrations
│   ├── Dockerfile             # Container configuration
│   └── requirements.txt       # Python dependencies
├── .github/workflows/         # CI/CD pipelines
├── background.js              # Extension service worker
├── content.js                 # Platform integration
├── popup.js                   # Extension UI logic
├── popup.html                 # Extension UI
├── manifest.json              # Extension configuration
└── config.js                  # API configuration
```

### Running Tests

```bash
cd backend
pytest
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Configuration

### Environment Variables

Create `backend/.env`:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/ai_context_bridge

# OpenAI (optional)
OPENAI_API_KEY=sk-your-api-key

# API Settings
CORS_ORIGINS=["chrome-extension://*","http://localhost:*"]
MAX_CONTEXT_SIZE=1000000
DEFAULT_RETENTION_DAYS=30

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600
```

### Extension Configuration

Edit `config.js`:

```javascript
const API_CONFIG = {
  DEV_BASE_URL: "http://localhost:8000/api/v1",
  PROD_BASE_URL: "https://your-cloud-run-url/api/v1",

  getBaseURL: function() {
    return this.PROD_BASE_URL;  // Change for environment
  }
};
```

## Security

- ✅ No API keys or secrets in code
- ✅ Environment variables for sensitive data
- ✅ Service account keys stored in GitHub Secrets
- ✅ Database credentials in GCP Secret Manager
- ✅ CORS protection for extension-only access
- ✅ Rate limiting (100 requests/hour per IP)
- ✅ Input validation and sanitization
- ✅ Automatic context expiration (30 days)

## Cost Estimates

### Google Cloud Platform
- **Cloud SQL** (db-f1-micro): ~$9/month
- **Cloud Run** (low traffic): ~$0-5/month
- **Storage & Bandwidth**: ~$1/month
- **Total**: ~$10-15/month

### OpenAI API (Optional)
- **GPT-4 Turbo**: ~$0.007 per summary
- **100 summaries/day**: ~$21/month
- **Alternative GPT-3.5**: ~$2/month

## Roadmap

- [ ] Add user authentication and multi-user support
- [ ] Implement context versioning and history
- [ ] Add support for more AI platforms (Perplexity, Bard, etc.)
- [ ] Create Firefox and Edge extensions
- [ ] Add context sharing and collaboration features
- [ ] Implement local-only mode (no cloud storage)
- [ ] Add export to Markdown, PDF, JSON
- [ ] Create mobile app version

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Acknowledgments

- Built with FastAPI and modern Python async patterns
- Deployed on Google Cloud Platform
- Uses OpenAI's GPT-4 for intelligent summarization
- Chrome Extension Manifest V3 for future compatibility

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review the documentation in `backend/README.md` and `CI-CD-SETUP.md`

---

**Made with ❤️ for seamless AI conversations across platforms**
