import csv
import io
import json


def parse_csv(content: str) -> list[dict]:
    """
    CSVコンテンツをパースしてリストを返す。
    method・endpoint が空の行はスキップ。
    params・body は JSON 文字列として解釈し、不正な場合は空 dict にフォールバック。

    想定フォーマット:
        method,endpoint,params,body
        GET,/api/v1/users,,
        POST,/api/v1/orders,,"{""item"": ""abc""}"
    """
    rows = []
    reader = csv.DictReader(io.StringIO(content))
    for row in reader:
        method = row.get("method", "").strip().upper()
        endpoint = row.get("endpoint", "").strip()
        if not method or not endpoint:
            continue
        rows.append({
            "method": method,
            "endpoint": endpoint,
            "params": _parse_json_field(row.get("params", "")),
            "body": _parse_json_field(row.get("body", "")),
        })
    return rows


def _parse_json_field(value: str) -> dict:
    value = value.strip()
    if not value:
        return {}
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return {}
