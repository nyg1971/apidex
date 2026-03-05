import pytest

from core.batch import parse_csv


class TestParseCsv:
    def test_basic_get_request(self):
        csv = "method,endpoint,params,body\nGET,/api/users,,\n"
        rows = parse_csv(csv)
        assert len(rows) == 1
        assert rows[0]["method"] == "GET"
        assert rows[0]["endpoint"] == "/api/users"
        assert rows[0]["params"] == {}
        assert rows[0]["body"] == {}

    def test_method_is_uppercased(self):
        csv = "method,endpoint\nget,/api/users\n"
        rows = parse_csv(csv)
        assert rows[0]["method"] == "GET"

    def test_multiple_rows(self):
        csv = "method,endpoint\nGET,/api/users\nPOST,/api/orders\n"
        rows = parse_csv(csv)
        assert len(rows) == 2
        assert rows[0]["endpoint"] == "/api/users"
        assert rows[1]["endpoint"] == "/api/orders"

    def test_params_as_json(self):
        csv = 'method,endpoint,params,body\nGET,/api/users,"{""page"": 1}",\n'
        rows = parse_csv(csv)
        assert rows[0]["params"] == {"page": 1}

    def test_body_as_json(self):
        csv = 'method,endpoint,params,body\nPOST,/api/orders,,"{""item"": ""abc""}"\n'
        rows = parse_csv(csv)
        assert rows[0]["body"] == {"item": "abc"}

    def test_invalid_json_falls_back_to_empty_dict(self):
        csv = "method,endpoint,params,body\nGET,/api/users,not-json,\n"
        rows = parse_csv(csv)
        assert rows[0]["params"] == {}

    def test_skips_row_without_method(self):
        csv = "method,endpoint\n,/api/users\nGET,/api/products\n"
        rows = parse_csv(csv)
        assert len(rows) == 1
        assert rows[0]["endpoint"] == "/api/products"

    def test_skips_row_without_endpoint(self):
        csv = "method,endpoint\nGET,\nGET,/api/products\n"
        rows = parse_csv(csv)
        assert len(rows) == 1
        assert rows[0]["endpoint"] == "/api/products"

    def test_empty_csv_returns_empty_list(self):
        csv = "method,endpoint\n"
        rows = parse_csv(csv)
        assert rows == []

    def test_whitespace_in_method_and_endpoint_is_stripped(self):
        csv = "method,endpoint\n  GET  ,  /api/users  \n"
        rows = parse_csv(csv)
        assert rows[0]["method"] == "GET"
        assert rows[0]["endpoint"] == "/api/users"

    def test_params_and_body_columns_optional(self):
        # params・body 列がない CSV でもパースできる
        csv = "method,endpoint\nGET,/api/users\n"
        rows = parse_csv(csv)
        assert rows[0]["params"] == {}
        assert rows[0]["body"] == {}
