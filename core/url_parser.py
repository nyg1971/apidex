from urllib.parse import urlparse, parse_qs


def parse_url(url: str) -> dict:
    """
    完全なURLをベースURL・エンドポイント・クエリパラメータに分解する。

    Returns:
        {"base_url": str, "endpoint": str, "params": dict}

    Raises:
        ValueError: scheme または netloc が存在しない場合
    """
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"有効なURLを入力してください: {url}")

    base_url = f"{parsed.scheme}://{parsed.netloc}"
    endpoint = parsed.path
    qs = parse_qs(parsed.query, keep_blank_values=True)
    params = {k: v[0] if len(v) == 1 else v for k, v in qs.items()}

    return {"base_url": base_url, "endpoint": endpoint, "params": params}
