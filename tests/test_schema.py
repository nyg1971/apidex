import pytest

from core.schema import build_merged_schema, infer_schema, merge_schemas


class TestInferSchema:
    def test_integer(self):
        assert infer_schema(42) == {"type": "integer"}

    def test_float(self):
        assert infer_schema(3.14) == {"type": "number"}

    def test_string(self):
        assert infer_schema("hello") == {"type": "string"}

    def test_boolean(self):
        # bool は int のサブクラスなので順序チェックが重要
        assert infer_schema(True) == {"type": "boolean"}
        assert infer_schema(False) == {"type": "boolean"}

    def test_none(self):
        assert infer_schema(None) == {"type": "string", "nullable": True}

    def test_list_with_items(self):
        result = infer_schema([1, 2, 3])
        assert result == {"type": "array", "items": {"type": "integer"}}

    def test_empty_list(self):
        result = infer_schema([])
        assert result == {"type": "array", "items": {}}

    def test_dict(self):
        result = infer_schema({"id": 1, "name": "Alice"})
        assert result == {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "name": {"type": "string"},
            },
        }

    def test_nested_dict(self):
        result = infer_schema({"user": {"id": 1}})
        assert result["properties"]["user"]["type"] == "object"
        assert result["properties"]["user"]["properties"]["id"] == {"type": "integer"}


class TestMergeSchemas:
    def test_merge_with_empty_base(self):
        incoming = {"type": "object", "properties": {"id": {"type": "integer"}}}
        assert merge_schemas({}, incoming) == incoming

    def test_merge_with_empty_incoming(self):
        base = {"type": "object", "properties": {"id": {"type": "integer"}}}
        assert merge_schemas(base, {}) == base

    def test_same_type_objects_merge_properties(self):
        base = {"type": "object", "properties": {"id": {"type": "integer"}}}
        incoming = {"type": "object", "properties": {"name": {"type": "string"}}}
        result = merge_schemas(base, incoming)
        assert result["type"] == "object"
        assert "id" in result["properties"]
        assert "name" in result["properties"]

    def test_type_mismatch_produces_anyof(self):
        base = {"type": "integer"}
        incoming = {"type": "string"}
        result = merge_schemas(base, incoming)
        assert "anyOf" in result
        assert {"type": "integer"} in result["anyOf"]
        assert {"type": "string"} in result["anyOf"]

    def test_merge_adds_new_key_from_incoming(self):
        base = {"type": "object", "properties": {"id": {"type": "integer"}}}
        incoming = {"type": "object", "properties": {"id": {"type": "integer"}, "name": {"type": "string"}}}
        result = merge_schemas(base, incoming)
        assert "name" in result["properties"]

    def test_merge_array_items(self):
        base = {"type": "array", "items": {"type": "integer"}}
        incoming = {"type": "array", "items": {"type": "integer"}}
        result = merge_schemas(base, incoming)
        assert result == {"type": "array", "items": {"type": "integer"}}


class TestBuildMergedSchema:
    def test_single_response(self):
        bodies = [{"id": 1, "name": "Alice"}]
        result = build_merged_schema(bodies)
        assert result["type"] == "object"
        assert "id" in result["properties"]
        assert "name" in result["properties"]

    def test_multiple_responses_merge_keys(self):
        bodies = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"},
        ]
        result = build_merged_schema(bodies)
        assert "id" in result["properties"]
        assert "name" in result["properties"]
        assert "email" in result["properties"]

    def test_empty_list(self):
        assert build_merged_schema([]) == {}
