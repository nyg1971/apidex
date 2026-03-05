import pytest

from auth.strategies import (
    AUTH_STRATEGIES,
    ApiKeyHeaderAuth,
    ApiKeyQueryAuth,
    BearerTokenAuth,
    NoAuth,
)


class TestNoAuth:
    def test_headers_and_params_unchanged(self):
        auth = NoAuth()
        headers = {"Content-Type": "application/json"}
        params = {"page": "1"}
        result_headers, result_params = auth.apply(headers, params)
        assert result_headers == {"Content-Type": "application/json"}
        assert result_params == {"page": "1"}


class TestBearerTokenAuth:
    def test_authorization_header_is_set(self):
        auth = BearerTokenAuth("my-token")
        headers, params = auth.apply({}, {})
        assert headers["Authorization"] == "Bearer my-token"

    def test_params_unchanged(self):
        auth = BearerTokenAuth("my-token")
        _, params = auth.apply({}, {"page": "1"})
        assert params == {"page": "1"}

    def test_existing_headers_are_preserved(self):
        auth = BearerTokenAuth("my-token")
        headers, _ = auth.apply({"Content-Type": "application/json"}, {})
        assert headers["Content-Type"] == "application/json"
        assert "Authorization" in headers


class TestApiKeyHeaderAuth:
    def test_custom_header_is_set(self):
        auth = ApiKeyHeaderAuth("X-API-Key", "secret")
        headers, _ = auth.apply({}, {})
        assert headers["X-API-Key"] == "secret"

    def test_params_unchanged(self):
        auth = ApiKeyHeaderAuth("X-API-Key", "secret")
        _, params = auth.apply({}, {"q": "test"})
        assert params == {"q": "test"}

    def test_custom_header_name(self):
        auth = ApiKeyHeaderAuth("X-Custom-Auth", "value")
        headers, _ = auth.apply({}, {})
        assert headers["X-Custom-Auth"] == "value"


class TestApiKeyQueryAuth:
    def test_key_is_added_to_params(self):
        auth = ApiKeyQueryAuth("api_key", "secret")
        _, params = auth.apply({}, {})
        assert params["api_key"] == "secret"

    def test_headers_unchanged(self):
        auth = ApiKeyQueryAuth("api_key", "secret")
        headers, _ = auth.apply({"Content-Type": "application/json"}, {})
        assert headers == {"Content-Type": "application/json"}

    def test_existing_params_are_preserved(self):
        auth = ApiKeyQueryAuth("api_key", "secret")
        _, params = auth.apply({}, {"page": "1"})
        assert params["page"] == "1"
        assert params["api_key"] == "secret"


class TestAuthStrategiesRegistry:
    def test_all_strategies_registered(self):
        assert "なし" in AUTH_STRATEGIES
        assert "Bearer Token" in AUTH_STRATEGIES
        assert "APIキー(ヘッダー)" in AUTH_STRATEGIES
        assert "APIキー(クエリ)" in AUTH_STRATEGIES

    def test_strategies_are_instantiable(self):
        assert AUTH_STRATEGIES["なし"]() is not None
