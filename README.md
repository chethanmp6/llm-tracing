# LiteLLM Analytics API

A FastAPI service for analyzing LiteLLM proxy analytics data stored in PostgreSQL. This service provides endpoints to retrieve metrics about agent usage, sessions, messages, and users.

## Features

- **Agent Analytics**: Get detailed metrics for specific agents and versions
- **Activity Timeline**: Daily session activity tracking
- **Token Usage Analytics**: Daily and total token consumption metrics
- **Recent Messages**: Retrieve recent message content with metadata
- **Time-based Filtering**: Analyze data over configurable time periods
- **Health Monitoring**: Built-in health check endpoint
- **OpenAPI Documentation**: Automatic API documentation
- **Error Handling**: Comprehensive error handling and logging
- **CORS Support**: Cross-origin resource sharing enabled
- **Async Support**: Built with async/await for high performance

## API Endpoints

### GET /analytics/agent

Get analytics metrics for a specific agent and version.

**Query Parameters:**
- `agent_name` (required): Filter by agent name
- `agent_version` (required): Filter by agent version
- `days` (required): Number of days to look back (1, 2, 7, 15, or 20)

**Example Request:**
```bash
curl "http://localhost:8000/analytics/agent?agent_name=Calculator%20Bot&agent_version=1.0.0&days=7"
```

**Example Response:**
```json
{
  "agent_name": "Calculator Bot",
  "agent_version": "1.0.0",
  "metrics": {
    "total_sessions": 150,
    "total_messages": 1200,
    "avg_daily_messages": 40.5,
    "total_users": 45
  },
  "date_range": {
    "start_date": "2024-01-01",
    "end_date": "2024-12-05"
  }
}
```

### GET /activitytimeline

Get daily session activity timeline for a specific agent and version.

**Query Parameters:**
- `agent_name` (required): Filter by agent name
- `agent_version` (required): Filter by agent version
- `days` (required): Number of days to look back (1, 2, 7, 15, or 20)

**Example Request:**
```bash
curl "http://localhost:8000/activitytimeline?agent_name=Calculator%20Bot&agent_version=1.0.0&days=7"
```

**Example Response:**
```json
{
  "agent_name": "Calculator Bot",
  "agent_version": "1.0.0",
  "date_range": {
    "start_date": "2024-11-28",
    "end_date": "2024-12-05"
  },
  "daily_sessions": [
    {
      "date": "2024-11-28",
      "sessions": 12
    },
    {
      "date": "2024-11-29",
      "sessions": 8
    }
  ]
}
```

### GET /tokens-usage

Get daily token usage (prompt and completion tokens) for a specific agent and version.

**Query Parameters:**
- `agent_name` (required): Filter by agent name
- `agent_version` (required): Filter by agent version
- `days` (required): Number of days to look back (1, 2, 7, 15, or 20)

**Example Request:**
```bash
curl "http://localhost:8000/tokens-usage?agent_name=Calculator%20Bot&agent_version=1.0.0&days=7"
```

**Example Response:**
```json
{
  "agent_name": "Calculator Bot",
  "agent_version": "1.0.0",
  "date_range": {
    "start_date": "2024-11-28",
    "end_date": "2024-12-05"
  },
  "daily_tokens": [
    {
      "date": "2024-11-28",
      "prompt_tokens": 1250,
      "completion_tokens": 875
    },
    {
      "date": "2024-11-29",
      "prompt_tokens": 980,
      "completion_tokens": 650
    }
  ]
}
```

### GET /total-tokens

Get total token consumption summary for a specific agent and version.

**Query Parameters:**
- `agent_name` (required): Filter by agent name
- `agent_version` (required): Filter by agent version
- `days` (required): Number of days to look back (1, 2, 7, 15, or 20)

**Example Request:**
```bash
curl "http://localhost:8000/total-tokens?agent_name=Calculator%20Bot&agent_version=1.0.0&days=7"
```

**Example Response:**
```json
{
  "agent_name": "Calculator Bot",
  "agent_version": "1.0.0",
  "date_range": {
    "start_date": "2024-11-28",
    "end_date": "2024-12-05"
  },
  "total_prompt_tokens": 8750,
  "total_completion_tokens": 6250
}
```

### GET /detailed-usage

Get detailed usage logs with individual request information.

**Query Parameters:**
- `agent_name` (required): Filter by agent name
- `agent_version` (required): Filter by agent version
- `days` (required): Number of days to look back (1, 2, 7, 15, or 20)

**Example Request:**
```bash
curl "http://localhost:8000/detailed-usage?agent_name=Calculator%20Bot&agent_version=1.0.0&days=7"
```

**Example Response:**
```json
{
  "agent_name": "Calculator Bot",
  "agent_version": "1.0.0",
  "date_range": {
    "start_date": "2024-11-28",
    "end_date": "2024-12-05"
  },
  "usage_logs": [
    {
      "timestamp": "2024-12-05T14:30:00",
      "agent_name": "Calculator Bot",
      "total_tokens": 125,
      "prompt_tokens": 75,
      "completion_tokens": 50,
      "duration_seconds": 2.5
    }
  ]
}
```

### GET /recentmessages

Get recent messages with content and metadata for a specific agent and version.

**Query Parameters:**
- `agent_name` (required): Filter by agent name
- `agent_version` (required): Filter by agent version
- `days` (required): Number of days to look back (1, 2, 7, 15, or 20)

**Example Request:**
```bash
curl "http://localhost:8000/recentmessages?agent_name=Customer%20Support%20Agent&agent_version=1.0.0&days=7"
```

**Example Response:**
```json
{
  "agent_name": "Customer Support Agent",
  "agent_version": "1.0.0",
  "date_range": {
    "start_date": "2024-11-28",
    "end_date": "2024-12-05"
  },
  "messages": [
    {
      "timestamp": "2024-12-05T14:30:00",
      "session_id": "session_abc123",
      "message_length": 147,
      "agent_name": "Customer Support Agent",
      "model_name": "gpt-4",
      "message": "Hello! I'm here to help you with your account. What specific issue are you experiencing today?"
    },
    {
      "timestamp": "2024-12-05T14:25:00",
      "session_id": "session_xyz789",
      "message_length": 89,
      "agent_name": "Customer Support Agent",
      "model_name": "gpt-4",
      "message": "Thank you for contacting support. Let me look into that billing question for you."
    }
  ]
}
```

### GET /health

Health check endpoint to verify API and database connectivity.

**Example Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-12-05T18:47:00.123456"
}
```

### GET /

Root endpoint with API information and links to documentation.

## Setup Instructions

### Prerequisites

- Python 3.8+
- PostgreSQL database with LiteLLM data
- LiteLLM proxy logging to PostgreSQL

### Installation

1. **Clone or download the project files**
   ```bash
   # Ensure you have all the project files in your directory
   ls -la
   # You should see: main.py, database.py, models.py, schemas.py, crud.py, requirements.txt, .env.example
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

5. **Set up your database connection**

   Edit `.env` file:
   ```env
   DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/your_litellm_db
   HOST=0.0.0.0
   PORT=8000
   ```

### Database Setup

The service expects LiteLLM data in PostgreSQL with agent metadata stored as JSONB. The main tables queried are:

- `LiteLLM_SpendLogs`
- `LiteLLM_RequestTable`

**Required metadata fields in JSONB:**
- `agent_name`
- `agent_version`
- `agent_user_id`
- `agent_session_id`
- `agent_app_name`

**Recommended database indexes for performance:**
```sql
-- Indexes for JSONB metadata columns
CREATE INDEX idx_spend_logs_metadata_agent ON "LiteLLM_SpendLogs" USING GIN (metadata);
CREATE INDEX idx_request_table_metadata_agent ON "LiteLLM_RequestTable" USING GIN (metadata);

-- Indexes for time-based queries
CREATE INDEX idx_spend_logs_starttime ON "LiteLLM_SpendLogs" (startTime);
CREATE INDEX idx_request_table_starttime ON "LiteLLM_RequestTable" (startTime);

-- Additional specific indexes for common queries
CREATE INDEX idx_spend_logs_agent_name ON "LiteLLM_SpendLogs" ((metadata->>'agent_name'));
CREATE INDEX idx_spend_logs_agent_version ON "LiteLLM_SpendLogs" ((metadata->>'agent_version'));
CREATE INDEX idx_request_table_agent_name ON "LiteLLM_RequestTable" ((metadata->>'agent_name'));
CREATE INDEX idx_request_table_agent_version ON "LiteLLM_RequestTable" ((metadata->>'agent_version'));
```

### Running the Service

**Development mode:**
```bash
python main.py
```

**Production mode with uvicorn:**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

**With auto-reload for development:**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### API Documentation

Once running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Project Structure

```
tracing-api/
├── main.py          # FastAPI application and endpoints
├── database.py      # Database configuration and connection
├── models.py        # SQLAlchemy ORM models
├── schemas.py       # Pydantic models for request/response validation
├── crud.py          # Database query functions
├── requirements.txt # Python dependencies
├── .env.example     # Environment variables template
└── README.md        # This file
```

## Example SQL Queries

The service uses optimized SQL queries to extract metrics from JSONB metadata:

```sql
-- Get agent analytics from LiteLLM_SpendLogs
WITH agent_data AS (
    SELECT
        metadata->>'agent_session_id' as session_id,
        metadata->>'agent_user_id' as user_id,
        startTime as request_time,
        request_id
    FROM "LiteLLM_SpendLogs"
    WHERE metadata->>'agent_name' = 'Calculator Bot'
        AND metadata->>'agent_version' = '1.0.0'
        AND startTime >= '2024-11-28'
        AND startTime <= '2024-12-05'
        AND metadata->>'agent_session_id' IS NOT NULL
)
SELECT
    COUNT(DISTINCT session_id) as total_sessions,
    COUNT(*) as total_messages,
    COUNT(DISTINCT user_id) as total_users,
    MIN(request_time) as earliest_request,
    MAX(request_time) as latest_request
FROM agent_data;
```

## Error Handling

The API provides comprehensive error handling:

- **422**: Invalid parameters (e.g., invalid `days` value)
- **404**: No data found for the specified agent/version
- **500**: Internal server errors
- **503**: Service unavailable (database connection issues)

## Logging

The service includes structured logging for:
- Request processing
- Database operations
- Error conditions
- Health checks

Logs are written to stdout and can be redirected to files or log aggregation systems.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string with asyncpg driver | Required |
| `HOST` | Server host address | `0.0.0.0` |
| `PORT` | Server port number | `8000` |

## Production Deployment

For production deployment, consider:

1. **Use a production ASGI server** like Gunicorn with uvicorn workers
2. **Set up proper logging** with log rotation and centralized collection
3. **Configure environment-specific settings** for database connections
4. **Implement monitoring** and alerting for the service health
5. **Set up CORS policies** appropriate for your frontend domains
6. **Use connection pooling** for database connections
7. **Implement rate limiting** if needed

Example production command:
```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Testing the Service

Test the endpoints using curl or any HTTP client:

```bash
# Health check
curl http://localhost:8000/health

# Analytics endpoint
curl "http://localhost:8000/analytics/agent?agent_name=MyAgent&agent_version=1.0.0&days=7"

# Activity timeline
curl "http://localhost:8000/activitytimeline?agent_name=MyAgent&agent_version=1.0.0&days=7"

# Token usage
curl "http://localhost:8000/tokens-usage?agent_name=MyAgent&agent_version=1.0.0&days=7"

# Total tokens
curl "http://localhost:8000/total-tokens?agent_name=MyAgent&agent_version=1.0.0&days=7"

# Detailed usage logs
curl "http://localhost:8000/detailed-usage?agent_name=MyAgent&agent_version=1.0.0&days=7"

# Recent messages
curl "http://localhost:8000/recentmessages?agent_name=MyAgent&agent_version=1.0.0&days=7"

# API documentation
open http://localhost:8000/docs
```


Deployed endpoint url in aws 
http://k8s-default-tracinga-79a9c76211-872069928.ap-south-1.elb.amazonaws.com/docs
