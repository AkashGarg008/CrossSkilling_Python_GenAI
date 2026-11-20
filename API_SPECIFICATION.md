# API Specification - FastAPI Microservice

## Base URL
```
http://localhost:8000
```

## Overview

This document provides the complete API specification for the FastAPI Microservice.

---

## 1. Health Check

### Endpoint
```
GET /health
```

### Description
Check if the service is running and healthy.

### Request

No parameters required.

**Example:**
```bash
curl -X GET "http://localhost:8000/health"
```

### Response

**Status Code:** 200 OK

**Response Body:**
```json
{
  "status": "healthy"
}
```

**Content-Type:** `application/json`

---

## 2. Weather

### Endpoint
```
GET /weather
```

### Description
Retrieve current weather information for a specified city.

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| city | string | Yes | Name of the city (e.g., "London", "New York") |

**Query String Example:**
```
GET /weather?city=Paris
```

**Full URL Example:**
```bash
curl -X GET "http://localhost:8000/weather?city=Tokyo"
```

### Response

**Status Code:** 200 OK

**Response Body:**
```json
{
  "city": "Tokyo",
  "temperature": 18.5,
  "condition": "Partly cloudy",
  "humidity": 60
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| city | string | City name as returned by geocoding API |
| temperature | number | Current temperature in Celsius |
| condition | string | Weather condition description |
| humidity | integer | Relative humidity as percentage (0-100) |

### Error Responses

#### 404 Not Found
Returned when the city cannot be found in the geocoding database.

```json
{
  "detail": "City 'InvalidCity' not found"
}
```

#### 502 Bad Gateway
Returned when the upstream weather API fails or is unreachable.

```json
{
  "detail": "Upstream weather API failed"
}
```

#### 422 Unprocessable Entity
Returned when the city parameter is missing or empty.

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["query", "city"],
      "msg": "Field required"
    }
  ]
}
```

### Examples

**Request:**
```bash
curl -X GET "http://localhost:8000/weather?city=London"
```

**Response:**
```json
{
  "city": "London",
  "temperature": 12.3,
  "condition": "Rainy",
  "humidity": 75
}
```

---

## 3. Joke

### Endpoint
```
GET /joke
```

### Description
Retrieve a random joke.

### Request

No parameters required.

**Example:**
```bash
curl -X GET "http://localhost:8000/joke"
```

### Response

**Status Code:** 200 OK

**Response Body:**
```json
{
  "joke": "Why don't scientists trust atoms? Because they make up everything!",
  "category": "general"
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| joke | string | The complete joke (setup + punchline) |
| category | string | Category or type of the joke |

### Error Responses

#### 502 Bad Gateway
Returned when the upstream joke API fails or is unreachable.

```json
{
  "detail": "Upstream joke API failed"
}
```

### Examples

**Request:**
```bash
curl -X GET "http://localhost:8000/joke"
```

**Response:**
```json
{
  "joke": "What do you call a fake noodle? An impasta!",
  "category": "general"
}
```

---

## 4. Summary

### Endpoint
```
POST /summary
```

### Description
Generate a concise summary of provided text using Claude 3.5 Sonnet AI model.

### Request

**Method:** POST

**Headers Required:**
```
X-API-Key: <valid-api-key>
Content-Type: application/json
```

**Request Body:**
```json
{
  "text": "Your text to summarize here..."
}
```

**Body Parameters:**

| Parameter | Type | Required | Constraints | Description |
|-----------|------|----------|-------------|-------------|
| text | string | Yes | 1-5000 characters | Text to be summarized |

### Request Examples

**Example 1: Simple summary**
```bash
curl -X POST "http://localhost:8000/summary" \
  -H "X-API-Key: sk-test-key-1" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "FastAPI is a modern, fast web framework for building APIs with Python."
  }'
```

**Example 2: Longer text**
```bash
curl -X POST "http://localhost:8000/summary" \
  -H "X-API-Key: sk-test-key-1" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. It focuses on developing algorithms and statistical models that enable computers to learn patterns from data and make predictions or decisions based on those patterns. Applications of machine learning are widespread, from recommendation systems in e-commerce to natural language processing in virtual assistants."
  }'
```

### Response

**Status Code:** 200 OK

**Response Body:**
```json
{
  "summary": "Machine learning is a subset of artificial intelligence that uses algorithms and statistical models to enable systems to learn from data and make predictions without explicit programming. It has widespread applications including recommendation systems and natural language processing."
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| summary | string | The generated summary (200-400 words) |

### Error Responses

#### 400 Bad Request
Returned when the text field is empty or exceeds the maximum length.

**Empty text:**
```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "text"],
      "msg": "String should have at least 1 character"
    }
  ]
}
```

**Text exceeds max length:**
```json
{
  "detail": [
    {
      "type": "string_too_long",
      "loc": ["body", "text"],
      "msg": "String should have at most 5000 characters"
    }
  ]
}
```

#### 401 Unauthorized
Returned when the X-API-Key header is missing or invalid.

**Missing header:**
```json
{
  "detail": "X-API-Key header is required"
}
```

**Invalid key:**
```json
{
  "detail": "Invalid API key"
}
```

#### 500 Internal Server Error
Returned when the LLM service fails.

```json
{
  "detail": "Failed to generate summary: <error-details>"
}
```

### Authentication

The `/summary` endpoint requires API key authentication.

**Valid API Keys (for testing):**
- `sk-test-key-1`
- `sk-test-key-2`

**Custom API Keys:**
Add to the `VALID_API_KEYS` environment variable (comma-separated):
```
VALID_API_KEYS=sk-custom-key-1,sk-custom-key-2
```

### Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| MAX_SUMMARY_LENGTH | 5000 | Maximum input text length in characters |
| LLM Model | claude-3-5-sonnet-20241022 | Claude model version used |
| Summary Length | 200-400 | Approximate word count of generated summary |

### Examples

**Request with authentication:**
```bash
curl -X POST "http://localhost:8000/summary" \
  -H "X-API-Key: sk-test-key-1" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Artificial Intelligence is transforming industries worldwide. From healthcare to finance, AI applications are improving efficiency, reducing costs, and enabling new innovations. Machine learning, deep learning, and natural language processing are driving this transformation. However, challenges like data privacy, algorithmic bias, and regulatory compliance need to be addressed for responsible AI development."
  }'
```

**Response:**
```json
{
  "summary": "Artificial Intelligence is transforming various industries by improving efficiency, reducing costs, and enabling innovations. Key technologies include machine learning, deep learning, and natural language processing. However, the development of AI must address challenges such as data privacy, algorithmic bias, and regulatory compliance for responsible implementation."
}
```

---

## Status Codes Reference

| Status Code | Description |
|-------------|-------------|
| 200 | OK - Request successful |
| 400 | Bad Request - Invalid input or validation error |
| 401 | Unauthorized - Missing or invalid API key |
| 404 | Not Found - Resource not found (e.g., city not found) |
| 422 | Unprocessable Entity - Validation error |
| 500 | Internal Server Error - Server-side error |
| 502 | Bad Gateway - Upstream API error |

---

## Content Types

All endpoints accept and return `application/json` content type.

**Request:** Add header `Content-Type: application/json` for POST requests.

**Response:** All responses have `Content-Type: application/json`.

---

## Rate Limiting

No rate limiting is currently implemented. For production, consider adding:
- Per-API-key rate limits
- IP-based rate limiting
- Burst allowances

---

## Timeouts

Default timeout values:
- Weather API: 30 seconds
- Joke API: 30 seconds
- LLM API: 60 seconds

---

## CORS Configuration

CORS is not currently enabled. To enable CORS in FastAPI:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Versioning

**Current API Version:** 1.0.0

API versioning can be implemented by prefixing routes:
- `/v1/weather`
- `/v2/weather` (future)

---

## OpenAPI Documentation

Auto-generated API documentation is available at:
- **Swagger UI:** `/docs`
- **ReDoc:** `/redoc`
- **OpenAPI JSON:** `/openapi.json`

---

## Deprecation Policy

Deprecated endpoints will be marked with a deprecation notice in documentation and given a 90-day notice period before removal.

---

## Support & Contact

For issues or questions:
1. Check the [README.md](README.md)
2. Review [TESTING_GUIDE.md](TESTING_GUIDE.md)
3. Check GitHub Issues (if applicable)

---

**Last Updated:** 2024-11-18
**API Version:** 1.0.0
