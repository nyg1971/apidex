from unittest.mock import MagicMock, patch

import pytest
import requests

from auth.strategies import BearerTokenAuth, NoAuth
from core.client import ApiClient
from db.repository import RequestLogRepository


@pytest.fixture
def repo(in_memory_session):
    return RequestLogRepository()


@pytest.fixture
def client(repo):
    return ApiClient(repo)


def _mock_response(status_code=200, json_body=None, headers=None):
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_body or {"id": 1}
    mock.headers = headers or {"Content-Type": "application/json"}
    return mock


class TestApiClientRequest:
    @patch("core.client.requests.request")
    def test_successful_get_request(self, mock_request, client, repo):
        mock_request.return_value = _mock_response(200, {"id": 1, "name": "Alice"})

        result = client.request(
            method="GET",
            base_url="https://example.com",
            endpoint="/api/users",
            auth=NoAuth(),
        )

        assert result["status_code"] == 200
        assert result["body"] == {"id": 1, "name": "Alice"}

    @patch("core.client.requests.request")
    def test_request_is_logged_to_db(self, mock_request, client, repo):
        mock_request.return_value = _mock_response(200, {"id": 1})

        client.request(
            method="GET",
            base_url="https://example.com",
            endpoint="/api/users",
            auth=NoAuth(),
        )

        logs = repo.get_all()
        assert len(logs) == 1
        assert logs[0].endpoint == "/api/users"
        assert logs[0].response_status == 200

    @patch("core.client.requests.request")
    def test_bearer_auth_is_applied(self, mock_request, client):
        mock_request.return_value = _mock_response()

        client.request(
            method="GET",
            base_url="https://example.com",
            endpoint="/api/users",
            auth=BearerTokenAuth("my-token"),
        )

        called_headers = mock_request.call_args.kwargs["headers"]
        assert called_headers["Authorization"] == "Bearer my-token"

    @patch("core.client.requests.request")
    def test_url_is_correctly_assembled(self, mock_request, client):
        mock_request.return_value = _mock_response()

        client.request(
            method="GET",
            base_url="https://example.com",
            endpoint="/api/users",
            auth=NoAuth(),
        )

        called_url = mock_request.call_args.kwargs["url"]
        assert called_url == "https://example.com/api/users"

    @patch("core.client.requests.request")
    def test_non_json_response_stored_as_raw(self, mock_request, client, repo):
        mock = MagicMock()
        mock.status_code = 200
        mock.json.side_effect = ValueError("No JSON")
        mock.text = "plain text response"
        mock.headers = {}
        mock_request.return_value = mock

        result = client.request(
            method="GET",
            base_url="https://example.com",
            endpoint="/api/plain",
            auth=NoAuth(),
        )

        assert result["body"] == {"_raw": "plain text response"}

    @patch("core.client.requests.request")
    def test_error_response_is_logged(self, mock_request, client, repo):
        mock_request.return_value = _mock_response(404, {"error": "Not found"})

        client.request(
            method="GET",
            base_url="https://example.com",
            endpoint="/api/missing",
            auth=NoAuth(),
        )

        logs = repo.get_all()
        assert logs[0].response_status == 404

    @patch("core.client.requests.request")
    def test_successful_request_has_no_db_error(self, mock_request, client):
        mock_request.return_value = _mock_response(200, {"id": 1})

        result = client.request(
            method="GET",
            base_url="https://example.com",
            endpoint="/api/users",
            auth=NoAuth(),
        )

        assert result["db_error"] is None

    @patch("core.client.requests.request")
    def test_db_save_failure_returns_response_with_db_error(self, mock_request, client, repo):
        mock_request.return_value = _mock_response(200, {"id": 1})

        with patch.object(repo, "save", side_effect=Exception("DB接続エラー")):
            result = client.request(
                method="GET",
                base_url="https://example.com",
                endpoint="/api/users",
                auth=NoAuth(),
            )

        # レスポンスは返る
        assert result["status_code"] == 200
        assert result["body"] == {"id": 1}
        # DB保存失敗が通知される
        assert result["db_error"] == "DB接続エラー"

    @patch("core.client.requests.request")
    def test_ssl_error_propagates(self, mock_request, client):
        mock_request.side_effect = requests.exceptions.SSLError("cert verify failed")

        with pytest.raises(requests.exceptions.SSLError):
            client.request(
                method="GET",
                base_url="https://example.com",
                endpoint="/api/users",
                auth=NoAuth(),
            )

    @patch("core.client.requests.request")
    def test_timeout_propagates(self, mock_request, client):
        mock_request.side_effect = requests.exceptions.Timeout("timed out")

        with pytest.raises(requests.exceptions.Timeout):
            client.request(
                method="GET",
                base_url="https://example.com",
                endpoint="/api/users",
                auth=NoAuth(),
            )

    @patch("core.client.requests.request")
    def test_connection_error_propagates(self, mock_request, client):
        mock_request.side_effect = requests.exceptions.ConnectionError("connection refused")

        with pytest.raises(requests.exceptions.ConnectionError):
            client.request(
                method="GET",
                base_url="https://example.com",
                endpoint="/api/users",
                auth=NoAuth(),
            )
