"""
Test suite for the FastAPI Microservice
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from main import app, validate_api_key

client = TestClient(app)


class TestAPIKeyValidation:
    """Test API key validation"""

    def test_valid_api_key(self):
        with patch("main.VALID_API_KEY", "sk-test-key-1"):
            assert validate_api_key("sk-test-key-1") is True

    def test_invalid_api_key(self):
        with patch("main.VALID_API_KEY", "sk-test-key-1"):
            assert validate_api_key("wrong-key") is False
            assert validate_api_key("") is False


class TestWeatherEndpoint:
    """Test /weather endpoint"""

    @patch("httpx.AsyncClient.get")
    async def test_weather_success_single_result(self, mock_get):
        """Single matching city returns a one-element list"""
        geo_response = MagicMock()
        geo_response.json.return_value = {
            "results": [{"latitude": 48.85, "longitude": 2.35, "name": "Paris"}]
        }
        weather_response = MagicMock()
        weather_response.json.return_value = {
            "current": {
                "temperature_2m": 15.5,
                "relative_humidity_2m": 65,
                "weather_code": 2,
            }
        }
        mock_get.side_effect = [geo_response, weather_response]

        response = client.get("/weather?city=Paris")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["city"] == "Paris"
        assert data[0]["temperature"] == 15.5
        assert data[0]["humidity"] == 65

    @patch("httpx.AsyncClient.get")
    async def test_weather_success_multiple_results(self, mock_get):
        """Multiple matching cities all returned"""
        geo_response = MagicMock()
        geo_response.json.return_value = {
            "results": [
                {"latitude": 51.51, "longitude": -0.13, "name": "London"},
                {"latitude": 42.98, "longitude": -81.23, "name": "London"},
            ]
        }
        weather_uk = MagicMock()
        weather_uk.json.return_value = {
            "current": {"temperature_2m": 12.0, "relative_humidity_2m": 80, "weather_code": 3}
        }
        weather_ca = MagicMock()
        weather_ca.json.return_value = {
            "current": {"temperature_2m": 5.0, "relative_humidity_2m": 60, "weather_code": 1}
        }
        mock_get.side_effect = [geo_response, weather_uk, weather_ca]

        response = client.get("/weather?city=London")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

    @patch("httpx.AsyncClient.get")
    async def test_weather_city_not_found(self, mock_get):
        geo_response = MagicMock()
        geo_response.json.return_value = {"results": []}
        mock_get.return_value = geo_response

        response = client.get("/weather?city=NonexistentCity")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_weather_missing_city_parameter(self):
        response = client.get("/weather")
        assert response.status_code == 422


class TestJokeEndpoint:
    """Test /joke endpoint"""

    @patch("httpx.AsyncClient.get")
    async def test_joke_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "setup": "Why don't scientists trust atoms?",
            "punchline": "Because they make up everything!",
            "type": "general",
        }
        mock_get.return_value = mock_response

        response = client.get("/joke")
        assert response.status_code == 200
        data = response.json()
        assert "Why don't scientists trust atoms?" in data["joke"]
        assert "Because they make up everything!" in data["joke"]
        assert data["category"] == "general"


class TestSummaryEndpoint:
    """Test /summary endpoint"""

    def test_summary_missing_api_key(self):
        response = client.post("/summary", json={"text": "Some text to summarize"})
        assert response.status_code == 401
        assert "X-API-Key header is required" in response.json()["detail"]

    def test_summary_invalid_api_key(self):
        with patch("main.VALID_API_KEY", "sk-test-key-1"):
            response = client.post(
                "/summary",
                headers={"X-API-Key": "invalid-key"},
                json={"text": "Some text to summarize"},
            )
        assert response.status_code == 401
        assert "Invalid API key" in response.json()["detail"]

    def test_summary_empty_text(self):
        with patch("main.VALID_API_KEY", "sk-test-key-1"):
            response = client.post(
                "/summary",
                headers={"X-API-Key": "sk-test-key-1"},
                json={"text": ""},
            )
        assert response.status_code == 422

    def test_summary_text_exceeds_max_length(self):
        # Pydantic model is built at import time, so patching MAX_SUMMARY_LENGTH
        # only affects the manual length check in the endpoint → 400, not 422.
        with patch("main.MAX_SUMMARY_LENGTH", 100):
            with patch("main.VALID_API_KEY", "sk-test-key-1"):
                response = client.post(
                    "/summary",
                    headers={"X-API-Key": "sk-test-key-1"},
                    json={"text": "a" * 101},
                )
        assert response.status_code == 400
        assert "exceeds maximum length" in response.json()["detail"]

    @patch("anthropic.Anthropic")
    def test_summary_success(self, mock_anthropic):
        """x_api_key is passed directly to the Anthropic client"""
        mock_client = MagicMock()
        mock_block = MagicMock()
        mock_block.type = "text"
        mock_block.text = "This is a summary of the text."
        mock_client.messages.create.return_value = MagicMock(content=[mock_block])
        mock_anthropic.return_value = mock_client

        with patch("main.VALID_API_KEY", "sk-test-key-1"):
            response = client.post(
                "/summary",
                headers={"X-API-Key": "sk-test-key-1"},
                json={"text": "This is some text that needs to be summarized."},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["summary"] == "This is a summary of the text."
        # Confirm the header key was forwarded to the Anthropic client
        mock_anthropic.assert_called_once_with(api_key="sk-test-key-1")

    @patch("anthropic.Anthropic")
    def test_summary_thinking_block_skipped(self, mock_anthropic):
        """Thinking blocks before the text block are ignored"""
        mock_client = MagicMock()
        thinking_block = MagicMock()
        thinking_block.type = "thinking"
        thinking_block.text = None
        text_block = MagicMock()
        text_block.type = "text"
        text_block.text = "Actual summary."
        mock_client.messages.create.return_value = MagicMock(
            content=[thinking_block, text_block]
        )
        mock_anthropic.return_value = mock_client

        with patch("main.VALID_API_KEY", "sk-test-key-1"):
            response = client.post(
                "/summary",
                headers={"X-API-Key": "sk-test-key-1"},
                json={"text": "Some text."},
            )

        assert response.status_code == 200
        assert response.json()["summary"] == "Actual summary."


class TestHealthEndpoint:
    """Test /health endpoint"""

    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
