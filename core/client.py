import requests

from auth.strategies import AuthStrategy
from db.repository import RequestLogRepository


class ApiClient:
    def __init__(self, repository: RequestLogRepository):
        self.repository = repository

    def request(
        self,
        method: str,
        base_url: str,
        endpoint: str,
        auth: AuthStrategy,
        headers: dict | None = None,
        params: dict | None = None,
        body: dict | None = None,
        timeout: int = 30,
    ) -> dict:
        headers = dict(headers or {})
        params = dict(params or {})
        body = body or {}

        headers, params = auth.apply(headers, params)

        url = base_url.rstrip("/") + "/" + endpoint.lstrip("/")

        # ネットワークエラーは呼び出し元へ伝播させる
        # （SSLError / Timeout / ConnectionError を呼び出し元で種別ごとに処理）
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=body if body else None,
            timeout=timeout,
        )

        try:
            response_body = response.json()
        except Exception:
            response_body = {"_raw": response.text}

        response_headers = dict(response.headers)

        # DB保存失敗はレスポンス表示を妨げない
        db_error = None
        try:
            self.repository.save(
                method=method,
                base_url=base_url,
                endpoint=endpoint,
                request_headers=headers,
                request_params=params,
                request_body=body,
                response_status=response.status_code,
                response_headers=response_headers,
                response_body=response_body,
            )
        except Exception as e:
            db_error = str(e)

        return {
            "status_code": response.status_code,
            "headers": response_headers,
            "body": response_body,
            "db_error": db_error,
        }
