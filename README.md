# FastAPI Microservice - Assignment 1

A production-quality FastAPI microservice that exposes external API wrappers and an authenticated LLM summary endpoint.

## Overview

This microservice provides three main endpoints:
- **GET /weather** - Fetch current weather for a city
- **GET /joke** - Fetch a random joke
- **POST /summary** - Generate an LLM-powered text summary (authenticated)

## Endpoints

### 1. GET /weather

**Description:** Returns current weather for all locations whose name matches the city query. Up to 10 candidates are fetched and filtered by name match.

**Parameters:**
- `city` (required, query string): City name

**Response (200 OK):** Array of matching locations
```json
[
  {
    "city": "London",
    "temperature": 12.3,
    "condition": "Overcast",
    "humidity": 78
  },
  {
    "city": "London",
    "temperature": 5.1,
    "condition": "Clear sky",
    "humidity": 60
  }
]
```

**Error Responses:**
- **404 Not Found:** No city found matching the query
- **502 Bad Gateway:** Upstream weather API failed

**Example:**
```bash
curl "http://localhost:8000/weather?city=London"
```

### 2. GET /joke

**Description:** Returns a random joke.

**Response (200 OK):**
```json
{
  "joke": "Why don't scientists trust atoms? Because they make up everything!",
  "category": "general"
}
```

**Error Responses:**
- **502 Bad Gateway:** Upstream joke API failed

**Example:**
```bash
curl "http://localhost:8000/joke"
```

### 3. POST /summary

**Description:** Generates a concise summary of provided text using Claude Opus 5.5. The `X-API-Key` header must be a valid Anthropic API key — it is used directly to authenticate with the Claude API.

**Headers:**
- `X-API-Key` (required): Your Anthropic API key (`sk-ant-...`)

**Request Body:**
```json
{
  "text": "Your text to summarize here..."
}
```

**Response (200 OK):**
```json
{
  "summary": "Generated summary of the provided text..."
}
```

**Error Responses:**
- **400 Bad Request:** Text field is empty or exceeds maximum length (5000 characters)
- **401 Unauthorized:** API key is missing or invalid

**Example:**
```bash
curl -X POST "http://localhost:8000/summary" \
  -H "X-API-Key: sk-ant-your-anthropic-key" \
  -H "Content-Type: application/json" \
  -d '{"text": "Your long text here..."}'
```

## Summary Specifications

- **LLM Provider:** Anthropic Claude Opus 5.5
- **Summary Length:** 200-400 words
- **Style:** Concise and informative, preserving key information
- **Max Input Length:** 5,000 characters

## Setup and Installation

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- An Anthropic API key — passed as `X-API-Key` on each `/summary` request

### Installation Steps

1. **Clone/Navigate to the project:**
```bash
cd /path/to/Assignments2026
```

2. **Create a virtual environment (optional but recommended):**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables:**
Copy the example and edit as needed:
```bash
cp .env.example .env
```
`.env` contents:
```
VALID_API_KEY=your_anthropic_api_key_here   # required
MAX_SUMMARY_LENGTH=5000                      # optional
```

5. **Run the server:**
```bash
python main.py
```

The server will start at `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- **Interactive API docs:** `http://localhost:8000/docs` (Swagger UI)
- **Alternative API docs:** `http://localhost:8000/redoc` (ReDoc)

## Testing

Run the test suite:
```bash
pytest test_main.py -v
```

Run with coverage:
```bash
pytest test_main.py --cov=main --cov-report=html
```

## Configuration

The following environment variables can be configured:

| Variable | Default | Description |
|----------|---------|-------------|
| `VALID_API_KEY` | (required) | Your Anthropic API key (passed as `X-API-Key` header) |
| `MAX_SUMMARY_LENGTH` | `5000` | Maximum allowed text length for summarization |

## External APIs Used

1. **Weather Data:**
   - **Provider:** Open-Meteo (free, no key required)
   - **Endpoints:** Geocoding API, Forecast API
   - **Features:** Current temperature, weather condition, humidity

2. **Jokes:**
   - **Provider:** Official Joke API (free)
   - **Features:** Random jokes with categories

3. **Text Summarization:**
   - **Provider:** Anthropic Claude
   - **Model:** Claude Opus 5.5
   - **Features:** High-quality, context-aware summarization

## Error Handling

The API follows HTTP status code conventions:

| Status | Meaning | Scenario |
|--------|---------|----------|
| 200 | OK | Request successful |
| 400 | Bad Request | Invalid input (empty text, exceeds max length) |
| 401 | Unauthorized | Missing or invalid API key |
| 404 | Not Found | City not found in weather API |
| 500 | Internal Server Error | Server-side error |
| 502 | Bad Gateway | Upstream API failure |

## Security

- **API Key Authentication:** The `/summary` endpoint requires a valid Anthropic API key in the `X-API-Key` header — it is used directly to call the Claude API, so no server-side key storage is needed
- **Input Validation:** Text length is validated to prevent abuse
- **HTTPS Ready:** Use a reverse proxy (nginx, Traefik) for HTTPS in production
- **CORS:** Can be configured as needed for frontend integration

## Production Deployment

For production deployment:

1. **Use a production ASGI server:**
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

2. **Use environment variables for secrets:**
   - Never commit `.env` files
   - Use secrets management (e.g., HashiCorp Vault, AWS Secrets Manager)

3. **Enable HTTPS:**
   - Use a reverse proxy (nginx, Traefik)
   - Obtain SSL certificates (Let's Encrypt)

4. **Monitor and logging:**
   - Set up centralized logging
   - Configure health checks at `/health`

## Health Check

A health check endpoint is available at:
```bash
curl "http://localhost:8000/health"
```

## Example Usage

### Get Weather (returns all matching locations)
```bash
curl "http://localhost:8000/weather?city=London"
```

### Get Joke
```bash
curl "http://localhost:8000/joke"
```

### Generate Summary
```bash
curl -X POST "http://localhost:8000/summary" \
  -H "X-API-Key: sk-ant-your-anthropic-key" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "FastAPI is a modern, fast web framework for building APIs with Python. It is based on standard Python type hints and offers automatic documentation, validation, and serialization. FastAPI provides excellent performance and developer experience with features like async support, dependency injection, and built-in security utilities."
  }'
```

## License

MIT

## Author

Assignment 1 - GenAI Training Program
