import pytest
import yaml

from db.repository import RequestLogRepository
from openapi.generator import generate_openapi, to_yaml


@pytest.fixture
def repo(in_memory_session):
    return RequestLogRepository()


def _save(repo, method="GET", endpoint="/api/users", base_url="https://example.com", body=None, status=200):
    repo.save(
        method=method,
        base_url=base_url,
        endpoint=endpoint,
        request_headers={},
        request_params={},
        request_body={},
        response_status=status,
        response_headers={},
        response_body=body or {"id": 1, "name": "Alice"},
    )


class TestGenerateOpenapi:
    def test_basic_structure(self, repo):
        _save(repo)
        doc = generate_openapi("https://example.com", title="Test API")

        assert doc["openapi"] == "3.0.3"
        assert doc["info"]["title"] == "Test API"
        assert doc["servers"][0]["url"] == "https://example.com"

    def test_endpoint_appears_in_paths(self, repo):
        _save(repo, method="GET", endpoint="/api/users")
        doc = generate_openapi("https://example.com")

        assert "/api/users" in doc["paths"]
        assert "get" in doc["paths"]["/api/users"]

    def test_response_schema_is_inferred(self, repo):
        _save(repo, body={"id": 1, "name": "Alice"})
        doc = generate_openapi("https://example.com")

        schema = doc["paths"]["/api/users"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
        assert schema["type"] == "object"
        assert "id" in schema["properties"]
        assert "name" in schema["properties"]

    def test_multiple_endpoints(self, repo):
        _save(repo, method="GET", endpoint="/api/users")
        _save(repo, method="POST", endpoint="/api/products")
        doc = generate_openapi("https://example.com")

        assert "/api/users" in doc["paths"]
        assert "/api/products" in doc["paths"]

    def test_multiple_logs_for_same_endpoint_are_merged(self, repo):
        _save(repo, endpoint="/api/users", body={"id": 1, "name": "Alice"})
        _save(repo, endpoint="/api/users", body={"id": 2, "name": "Bob", "email": "bob@example.com"})
        doc = generate_openapi("https://example.com")

        schema = doc["paths"]["/api/users"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
        props = schema["properties"]
        assert "id" in props
        assert "name" in props
        assert "email" in props

    def test_filters_by_base_url(self, repo):
        _save(repo, base_url="https://example.com", endpoint="/api/users")
        _save(repo, base_url="https://other.com", endpoint="/api/products")
        doc = generate_openapi("https://example.com")

        assert "/api/users" in doc["paths"]
        assert "/api/products" not in doc["paths"]

    def test_empty_db_returns_empty_paths(self, repo):
        doc = generate_openapi("https://example.com")
        assert doc["paths"] == {}


class TestToYaml:
    def test_output_is_valid_yaml(self, repo):
        _save(repo)
        doc = generate_openapi("https://example.com")
        yaml_str = to_yaml(doc)

        parsed = yaml.safe_load(yaml_str)
        assert parsed["openapi"] == "3.0.3"

    def test_unicode_preserved(self, repo):
        _save(repo, body={"名前": "テスト"})
        doc = generate_openapi("https://example.com")
        yaml_str = to_yaml(doc)

        assert "名前" in yaml_str
