import pytest

from db.repository import RequestLogRepository


@pytest.fixture
def repo(in_memory_session):
    return RequestLogRepository()


def _save(repo, endpoint="/api/users", method="GET", base_url="https://example.com", status=200):
    return repo.save(
        method=method,
        base_url=base_url,
        endpoint=endpoint,
        request_headers={"Content-Type": "application/json"},
        request_params={},
        request_body={},
        response_status=status,
        response_headers={"Content-Type": "application/json"},
        response_body={"id": 1, "name": "Alice"},
    )


class TestSave:
    def test_saved_log_has_correct_fields(self, repo):
        log = _save(repo)
        assert log.id is not None
        assert log.method == "GET"
        assert log.endpoint == "/api/users"
        assert log.response_status == 200

    def test_response_body_is_stored_as_json(self, repo):
        log = _save(repo)
        assert log.response_body_dict() == {"id": 1, "name": "Alice"}

    def test_request_headers_are_stored(self, repo):
        log = _save(repo)
        assert log.request_headers_dict() == {"Content-Type": "application/json"}


class TestGetAll:
    def test_returns_empty_list_when_no_logs(self, repo):
        assert repo.get_all() == []

    def test_returns_all_saved_logs(self, repo):
        _save(repo, endpoint="/api/users")
        _save(repo, endpoint="/api/products")
        logs = repo.get_all()
        assert len(logs) == 2

    def test_ordered_by_timestamp_desc(self, repo):
        _save(repo, endpoint="/api/first")
        _save(repo, endpoint="/api/second")
        logs = repo.get_all()
        assert logs[0].endpoint == "/api/second"


class TestGetByEndpoint:
    def test_filters_by_endpoint(self, repo):
        _save(repo, endpoint="/api/users")
        _save(repo, endpoint="/api/products")
        logs = repo.get_by_endpoint("/api/users")
        assert len(logs) == 1
        assert logs[0].endpoint == "/api/users"

    def test_returns_empty_for_unknown_endpoint(self, repo):
        _save(repo, endpoint="/api/users")
        assert repo.get_by_endpoint("/api/unknown") == []


class TestGetUniqueEndpoints:
    def test_returns_unique_method_endpoint_pairs(self, repo):
        _save(repo, method="GET", endpoint="/api/users")
        _save(repo, method="GET", endpoint="/api/users")  # 重複
        _save(repo, method="POST", endpoint="/api/users")
        result = repo.get_unique_endpoints()
        assert len(result) == 2
        assert ("GET", "/api/users") in result
        assert ("POST", "/api/users") in result
