import json
from datetime import datetime, timezone

from db.models import RequestLog, SessionLocal


class RequestLogRepository:
    def save(
        self,
        method: str,
        base_url: str,
        endpoint: str,
        request_headers: dict,
        request_params: dict,
        request_body: dict,
        response_status: int,
        response_headers: dict,
        response_body: dict,
    ) -> RequestLog:
        with SessionLocal() as session:
            log = RequestLog(
                method=method,
                base_url=base_url,
                endpoint=endpoint,
                request_headers=json.dumps(request_headers, ensure_ascii=False),
                request_params=json.dumps(request_params, ensure_ascii=False),
                request_body=json.dumps(request_body, ensure_ascii=False),
                response_status=response_status,
                response_headers=json.dumps(response_headers, ensure_ascii=False),
                response_body=json.dumps(response_body, ensure_ascii=False),
                timestamp=datetime.now(timezone.utc),
            )
            session.add(log)
            session.commit()
            session.refresh(log)
            return log

    def get_all(self) -> list[RequestLog]:
        with SessionLocal() as session:
            return session.query(RequestLog).order_by(RequestLog.timestamp.desc()).all()

    def get_by_endpoint(self, endpoint: str) -> list[RequestLog]:
        with SessionLocal() as session:
            return (
                session.query(RequestLog)
                .filter(RequestLog.endpoint == endpoint)
                .order_by(RequestLog.timestamp.desc())
                .all()
            )

    def get_unique_endpoints(self) -> list[tuple[str, str]]:
        """(method, endpoint) の一覧を返す（重複なし）"""
        with SessionLocal() as session:
            rows = (
                session.query(RequestLog.method, RequestLog.endpoint)
                .distinct()
                .all()
            )
            return [(row.method, row.endpoint) for row in rows]
