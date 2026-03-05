def infer_schema(value: any) -> dict:
    """値からOpenAPIスキーマを再帰的に推論する"""
    if isinstance(value, bool):
        return {"type": "boolean"}
    elif isinstance(value, int):
        return {"type": "integer"}
    elif isinstance(value, float):
        return {"type": "number"}
    elif isinstance(value, str):
        return {"type": "string"}
    elif isinstance(value, list):
        if value:
            return {"type": "array", "items": infer_schema(value[0])}
        return {"type": "array", "items": {}}
    elif isinstance(value, dict):
        return {
            "type": "object",
            "properties": {k: infer_schema(v) for k, v in value.items()},
        }
    elif value is None:
        return {"type": "string", "nullable": True}
    return {}


def merge_schemas(base: dict, incoming: dict) -> dict:
    """
    同じエンドポイントの複数レスポンスからスキーマをマージする。
    - 片方にしかないキーはそのまま残す
    - 両方にあるキーは型が一致すれば維持、不一致なら anyOf に昇格
    """
    if not base:
        return incoming
    if not incoming:
        return base

    base_type = base.get("type")
    incoming_type = incoming.get("type")

    if base_type != incoming_type:
        return {"anyOf": [base, incoming]}

    if base_type == "object":
        base_props = base.get("properties", {})
        incoming_props = incoming.get("properties", {})
        merged_props = dict(base_props)
        for key, schema in incoming_props.items():
            if key in merged_props:
                merged_props[key] = merge_schemas(merged_props[key], schema)
            else:
                merged_props[key] = schema
        return {"type": "object", "properties": merged_props}

    if base_type == "array":
        merged_items = merge_schemas(base.get("items", {}), incoming.get("items", {}))
        return {"type": "array", "items": merged_items}

    return base


def build_merged_schema(response_bodies: list[dict]) -> dict:
    """複数のレスポンスボディからマージ済みスキーマを構築する"""
    schema = {}
    for body in response_bodies:
        schema = merge_schemas(schema, infer_schema(body))
    return schema
