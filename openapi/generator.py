import yaml

from core.schema import build_merged_schema
from db.repository import RequestLogRepository


def generate_openapi(base_url: str, title: str = "apidex") -> dict:
    repo = RequestLogRepository()
    all_logs = repo.get_all()

    # base_url でフィルタ
    logs = [log for log in all_logs if log.base_url == base_url]

    # (method, endpoint) ごとにレスポンスボディを集約
    endpoint_map: dict[tuple[str, str], list[dict]] = {}
    for log in logs:
        key = (log.method.upper(), log.endpoint)
        endpoint_map.setdefault(key, []).append(log.response_body_dict())

    paths: dict = {}
    for (method, endpoint), bodies in endpoint_map.items():
        schema = build_merged_schema(bodies)
        path_item = paths.setdefault(endpoint, {})
        path_item[method.lower()] = {
            "summary": f"{method} {endpoint}",
            "responses": {
                "200": {
                    "description": "Success",
                    "content": {
                        "application/json": {
                            "schema": schema,
                        }
                    },
                }
            },
        }

    openapi_doc = {
        "openapi": "3.0.3",
        "info": {
            "title": title,
            "version": "0.1.0",
        },
        "servers": [{"url": base_url}],
        "paths": paths,
    }

    return openapi_doc


def to_yaml(openapi_doc: dict) -> str:
    return yaml.dump(openapi_doc, allow_unicode=True, sort_keys=False)
