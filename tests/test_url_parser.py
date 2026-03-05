import pytest

from core.url_parser import parse_url


class TestParseUrl:
    def test_basic_url(self):
        result = parse_url("https://api.example.com/v1/users")
        assert result["base_url"] == "https://api.example.com"
        assert result["endpoint"] == "/v1/users"
        assert result["params"] == {}

    def test_url_with_query_params(self):
        result = parse_url("https://api.open-meteo.com/v1/forecast?latitude=35.6785&longitude=139.6823")
        assert result["base_url"] == "https://api.open-meteo.com"
        assert result["endpoint"] == "/v1/forecast"
        assert result["params"]["latitude"] == "35.6785"
        assert result["params"]["longitude"] == "139.6823"

    def test_url_encoded_param(self):
        result = parse_url("https://api.example.com/v1/forecast?timezone=Asia%2FTokyo")
        assert result["params"]["timezone"] == "Asia/Tokyo"

    def test_multiple_values_for_same_key(self):
        result = parse_url("https://api.example.com/v1/data?tag=a&tag=b")
        assert result["params"]["tag"] == ["a", "b"]

    def test_single_value_is_not_list(self):
        result = parse_url("https://api.example.com/v1/data?page=1")
        assert result["params"]["page"] == "1"
        assert not isinstance(result["params"]["page"], list)

    def test_http_scheme(self):
        result = parse_url("http://localhost:8080/api/test")
        assert result["base_url"] == "http://localhost:8080"
        assert result["endpoint"] == "/api/test"

    def test_root_endpoint(self):
        result = parse_url("https://api.example.com/")
        assert result["endpoint"] == "/"

    def test_no_scheme_raises(self):
        with pytest.raises(ValueError):
            parse_url("api.example.com/v1/users")

    def test_empty_string_raises(self):
        with pytest.raises(ValueError):
            parse_url("")

    def test_invalid_url_raises(self):
        with pytest.raises(ValueError):
            parse_url("not-a-url")
