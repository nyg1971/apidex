from abc import ABC, abstractmethod


class AuthStrategy(ABC):
    @abstractmethod
    def apply(self, headers: dict, params: dict) -> tuple[dict, dict]:
        raise NotImplementedError


class NoAuth(AuthStrategy):
    def apply(self, headers: dict, params: dict) -> tuple[dict, dict]:
        return headers, params


class BearerTokenAuth(AuthStrategy):
    def __init__(self, token: str):
        self.token = token

    def apply(self, headers: dict, params: dict) -> tuple[dict, dict]:
        headers["Authorization"] = f"Bearer {self.token}"
        return headers, params


class ApiKeyHeaderAuth(AuthStrategy):
    def __init__(self, key_name: str, key_value: str):
        self.key_name = key_name
        self.key_value = key_value

    def apply(self, headers: dict, params: dict) -> tuple[dict, dict]:
        headers[self.key_name] = self.key_value
        return headers, params


class ApiKeyQueryAuth(AuthStrategy):
    def __init__(self, key_name: str, key_value: str):
        self.key_name = key_name
        self.key_value = key_value

    def apply(self, headers: dict, params: dict) -> tuple[dict, dict]:
        params[self.key_name] = self.key_value
        return headers, params


AUTH_STRATEGIES = {
    "なし": NoAuth,
    "Bearer Token": BearerTokenAuth,
    "APIキー(ヘッダー)": ApiKeyHeaderAuth,
    "APIキー(クエリ)": ApiKeyQueryAuth,
}
