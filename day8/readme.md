# Step-by-Step RAG Tutorial

## Day 7: Production Ready

A comprehensive, production-ready RAG (Retrieval-Augmented Generation) system built incrementally over 7 days.

完整的、可投入生产的 RAG（检索增强生成）系统，通过 7 天循序渐进构建。

---

## Overview

This project demonstrates how to build an enterprise-grade RAG system step by step, with each day adding new capabilities while maintaining a fully functional application.

本项目演示如何循序渐进地构建企业级 RAG 系统，每天添加新功能，同时保持完整可运行的应用。

### Day Progression

| Day | Focus | Key Features |
|-----|-------|--------------|
| Day 1 | Minimal RAG | Document upload, vector search, basic Q&A |
| Day 2 | Data Preprocessing | Multi-format parsing, smart chunking |
| Day 3 | Retrieval Optimization | Hybrid search (Vector + BM25), re-ranking |
| Day 4 | Generation Enhancement | Streaming, citations, confidence scoring |
| Day 5 | Evaluation & Observability | RAGAS evaluation, request tracing |
| Day 6 | Security & Governance | JWT auth, ACL permissions, audit logs |
| **Day 7** | **Production Ready** | **Caching, metrics, Docker deployment** |

---

## Day 7 Features

### Performance Optimization
- **Caching Layer**: In-memory TTL cache with optional Redis support
- **Performance Metrics**: Latency tracking (P50, P95, P99), error rates
- **Retry Logic**: Exponential backoff for resilient API calls
- **Rate Limiting**: Request rate protection

### Docker Deployment
- **Multi-stage Builds**: Optimized image sizes
- **Docker Compose**: One-command deployment
- **Health Checks**: Container-level monitoring
- **Volume Persistence**: Data persistence across restarts

### Monitoring & Observability
- **Performance Dashboard**: Real-time metrics via `/metrics` endpoint
- **Cache Statistics**: Hit rates and configuration via `/cache/stats`
- **Request Timing**: X-Process-Time-Ms header on all responses

---

## Quick Start

### Prerequisites
- Docker and Docker Compose
- OpenAI API key (or compatible API)

### 1. Clone and Configure

```bash
# Clone the repository
git clone <repository-url>
cd step-by-step-rag/day7

# Create environment file
cat > .env << EOF
OPENAI_API_KEY=your-api-key-here
OPENAI_API_BASE=https://api.openai.com/v1  # Optional: use other providers
JWT_SECRET_KEY=change-me-in-production
EOF
```

### 2. Start with Docker Compose

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### 3. Access the Application

| Service | URL |
|---------|-----|
| Frontend | http://localhost |
| Backend API | http://localhost:8000 |
| API Documentation | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Metrics | http://localhost:8000/metrics |
| Cache Stats | http://localhost:8000/cache/stats |

### 4. Login

Default credentials:
- Username: `admin`
- Password: `admin123`

**⚠️ Change these credentials in production!**

---

## Development Setup

### Backend (without Docker)

```bash
cd day7/backend

# Install dependencies with uv
pip install uv
uv pip install -e .

# Set environment variables
export OPENAI_API_KEY=your-api-key
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/rag_db

# Run the server
uvicorn src.main:app --reload --port 8000
```

### Frontend (without Docker)

```bash
cd day7/frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │  Upload  │ │  Chat    │ │ Evaluation│ │  Audit   │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Backend (FastAPI)                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  Middleware Layer                     │   │
│  │  • Metrics  • Rate Limiting  • Auth  • Caching       │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  Service Layer                        │   │
│  │  • RAG Pipeline  • Evaluation  • Security            │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Data Layer                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                    │
│  │PostgreSQL│ │  Redis   │ │OpenAI API│                    │
│  │ pgvector │ │  Cache   │ │   LLM    │                    │
│  └──────────┘ └──────────┘ └──────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Configuration

### Environment Variables

```bash
# API Configuration
OPENAI_API_KEY=your-api-key
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo

# Database
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/rag_db

# Cache
CACHE_ENABLED=true
CACHE_TTL_SECONDS=3600
REDIS_URL=redis://redis:6379/0

# Security
JWT_SECRET_KEY=your-secret-key
AUTH_ENABLED=true

# Metrics
METRICS_ENABLED=true

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60
```

---

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login and get JWT token |
| POST | `/auth/logout` | Logout |
| GET | `/auth/me` | Get current user info |

### Documents
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/documents/upload` | Upload document |
| GET | `/documents` | List documents |
| DELETE | `/documents/{id}` | Delete document |

### Chat
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chat` | Chat with RAG (non-streaming) |
| POST | `/chat/stream` | Chat with streaming (SSE) |

### Evaluation
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/evaluation/rag` | Run RAGAS evaluation |
| POST | `/evaluation/retrieval` | Get retrieval metrics |

### Production (Day 7)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/metrics` | Performance metrics |
| GET | `/cache/stats` | Cache statistics |
| GET | `/health` | Detailed health check |

---

## Performance Features

### Caching
```python
# Automatic query caching with decorator
@cache_service.cached_query("embedding")
async def get_embedding(text: str) -> list:
    # Only executed if not in cache
    return await embedding_service.embed(text)
```

### Retry Logic
```python
# Automatic retry with exponential backoff
@with_retry(max_attempts=3, exception_types=(ConnectionError,))
async def call_external_api():
    # Automatically retried on failure
    return await api_client.request()
```

### Performance Tracking
```python
# Track function performance
@track_performance("vector_search")
async def search_vectors(query: str) -> list:
    # Latency and success automatically recorded
    return await vector_store.search(query)
```

---

## Monitoring

### Metrics Available
- **Latency**: Average, P50, P95, P99
- **Error Rate**: Per-operation error tracking
- **Throughput**: Requests per second
- **Cache Hit Rate**: Cache effectiveness

### Example Metrics Response
```json
{
  "enabled": true,
  "operations": {
    "POST /chat": {
      "total_requests": 150,
      "errors": 2,
      "error_rate": 0.013,
      "avg_latency_ms": 450.2,
      "p50_latency_ms": 380.0,
      "p95_latency_ms": 890.0,
      "p99_latency_ms": 1200.0
    }
  }
}
```

---

## Security

### Default Credentials (Development Only)
- Username: `admin`
- Password: `admin123`

### Production Security Checklist
- [ ] Change JWT secret key
- [ ] Change default admin password
- [ ] Enable HTTPS
- [ ] Configure CORS origins
- [ ] Set up rate limiting
- [ ] Enable audit logging

---

## License

MIT License

---

## Contributing

Contributions are welcome! Please read the contributing guidelines first.

---

## Support

For issues and questions, please open a GitHub issue.
