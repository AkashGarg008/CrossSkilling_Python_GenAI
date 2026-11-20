"""
FastAPI Microservice - Assignment 1
Endpoints for weather, jokes, and LLM-powered text summarization.
"""

import os
import asyncio
import httpx
from fastapi import FastAPI, Query, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import anthropic

load_dotenv()

app = FastAPI(
    title="FastAPI Microservice",
    description="Production-quality microservice with external API wrappers and LLM summarization",
    version="1.0.0"
)

# Configuration
VALID_API_KEY = os.getenv("VALID_API_KEY", "")
MAX_SUMMARY_LENGTH = int(os.getenv("MAX_SUMMARY_LENGTH", "5000"))

# Request/Response Models
class TextRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=MAX_SUMMARY_LENGTH)

class WeatherResponse(BaseModel):
    city: str
    temperature: float
    condition: str
    humidity: int

class JokeResponse(BaseModel):
    joke: str
    category: str

class SummaryResponse(BaseModel):
    summary: str

# Utility functions
def validate_api_key(api_key: str) -> bool:
    """Validate the provided API key."""
    return api_key == VALID_API_KEY

# Weather Endpoint
@app.get("/weather", response_model=list[WeatherResponse])
async def get_weather(city: str = Query(..., min_length=1, description="City name")):
    """
    Get current weather for all locations matching the city name.

    Returns 404 if no matching city found, 502 if upstream API fails.
    """
    try:
        async with httpx.AsyncClient() as client:
            geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
            geocoding_params = {
                "name": city,
                "count": 10,
                "language": "en",
                "format": "json"
            }

            geo_response = await client.get(geocoding_url, params=geocoding_params)
            geo_response.raise_for_status()
            geo_data = geo_response.json()

            if not geo_data.get("results"):
                raise HTTPException(
                    status_code=404,
                    detail=f"City '{city}' not found"
                )

            results = geo_data["results"]

            # Keep only locations whose name matches the query (case-insensitive)
            matched = [
                r for r in results
                if city.lower() in r.get("name", "").lower()
            ]
            if not matched:
                matched = results  # fall back to all results if none name-match

            async def fetch_weather(location: dict) -> WeatherResponse:
                weather_url = "https://api.open-meteo.com/v1/forecast"
                weather_params = {
                    "latitude": location["latitude"],
                    "longitude": location["longitude"],
                    "current": "temperature_2m,relative_humidity_2m,weather_code",
                    "temperature_unit": "celsius"
                }
                resp = await client.get(weather_url, params=weather_params)
                resp.raise_for_status()
                current = resp.json()["current"]
                return WeatherResponse(
                    city=location["name"],
                    temperature=current["temperature_2m"],
                    condition=get_weather_condition(current["weather_code"]),
                    humidity=current["relative_humidity_2m"]
                )

            weather_results = await asyncio.gather(
                *[fetch_weather(loc) for loc in matched]
            )
            return list(weather_results)

    except HTTPException:
        raise
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Upstream weather API failed")
    except Exception:
        raise HTTPException(status_code=502, detail="Upstream weather API failed")

def get_weather_condition(code: int) -> str:
    """Convert WMO weather code to condition string."""
    conditions = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Foggy",
        48: "Foggy",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with hail",
        99: "Thunderstorm with hail"
    }
    return conditions.get(code, "Unknown")

# Joke Endpoint
@app.get("/joke", response_model=JokeResponse)
async def get_joke():
    """
    Get a random joke.
    
    Returns 502 if the upstream joke API fails.
    """
    try:
        async with httpx.AsyncClient() as client:
            # Using Official Joke API (free)
            response = await client.get("https://official-joke-api.appspot.com/random_ten")
            response.raise_for_status()
            data = response.json()
            
            # Combine setup and punchline for the joke text
            joke_text = f"{data['setup']} {data['punchline']}"
            
            return JokeResponse(
                joke=joke_text,
                category=data.get("type", "general")
            )
    except httpx.HTTPError:
        raise HTTPException(
            status_code=502,
            detail="Upstream joke API failed"
        )

# Summary Endpoint
@app.post("/summary", response_model=SummaryResponse)
async def summarize_text(
    request: TextRequest,
    x_api_key: str | None = Header(None)
):
    """
    Generate a summary of provided text using Claude.
    
    Requires X-API-Key header authentication.
    Returns 401 if API key is missing or invalid.
    Returns 400 if text field is empty or exceeds max length.
    
    **Summary Details:**
    - Uses Claude 3.5 Sonnet for high-quality summarization
    - Generates concise summaries (200-400 words)
    - Maintains key information and context
    - Suitable for articles, documents, and general text
    """
    
    # Validate API Key
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="X-API-Key header is required"
        )
    
    if not validate_api_key(x_api_key):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    # Validate text
    if not request.text or len(request.text.strip()) == 0:
        raise HTTPException(
            status_code=400,
            detail="Text field cannot be empty"
        )
    
    if len(request.text) > MAX_SUMMARY_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Text exceeds maximum length of {MAX_SUMMARY_LENGTH} characters"
        )
    
    try:
        # Initialize Anthropic client
        client = anthropic.Anthropic(api_key=x_api_key)
        
        # Create message with Claude
        message = client.messages.create(
            model="claude-opus-5-5",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": f"""Please provide a concise summary of the following text. 
The summary should be 200-400 words, capturing the main points and key information.

Text to summarize:
{request.text}"""
                }
            ]
        )
        
        summary = next(
            (block.text for block in message.content if block.type == "text"),
            None
        )
        if not summary:
            raise HTTPException(status_code=500, detail="No text in model response")

        return SummaryResponse(summary=summary)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate summary: {str(e)}"
        )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
