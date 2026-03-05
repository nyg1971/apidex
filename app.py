import json

import requests
import streamlit as st

from auth.strategies import AUTH_STRATEGIES
from core.url_parser import parse_url
from core.batch import parse_csv
from core.client import ApiClient
from db.models import init_db
from db.repository import RequestLogRepository
from openapi.generator import generate_openapi, to_yaml

st.set_page_config(page_title="apidex", layout="wide")

init_db()

repo = RequestLogRepository()
client = ApiClient(repo)

st.title("apidex")

# ─────────────────────────────────────────
# セクション1: リクエスト実行
# ─────────────────────────────────────────
st.header("リクエスト実行")

col_form, col_result = st.columns([1, 1])

with col_form:
    with st.expander("URLからパース"):
        paste_url = st.text_input("完全なURLをペースト", placeholder="https://api.example.com/v1/endpoint?key=value")
        if st.button("URLを解析"):
            try:
                parsed = parse_url(paste_url)
                st.session_state["base_url"] = parsed["base_url"]
                st.session_state["endpoint"] = parsed["endpoint"]
                st.session_state["params_input"] = json.dumps(parsed["params"], ensure_ascii=False, indent=2)
                st.rerun()
            except ValueError as e:
                st.error(str(e))

    inner_col1, inner_col2 = st.columns([1, 3])
    with inner_col1:
        method = st.selectbox("メソッド", ["GET", "POST", "PUT", "PATCH", "DELETE"])
    with inner_col2:
        base_url = st.text_input("ベースURL", placeholder="https://api.example.com", key="base_url")

    endpoint = st.text_input("エンドポイント", placeholder="/api/v1/users", key="endpoint")

    # 認証設定
    auth_type = st.selectbox("認証方式", list(AUTH_STRATEGIES.keys()))

    auth = None
    if auth_type == "なし":
        auth = AUTH_STRATEGIES["なし"]()
    elif auth_type == "Bearer Token":
        token = st.text_input("トークン", type="password")
        if token:
            auth = AUTH_STRATEGIES["Bearer Token"](token)
    elif auth_type == "APIキー(ヘッダー)":
        key_name = st.text_input("ヘッダー名", value="X-API-Key")
        key_value = st.text_input("APIキー", type="password")
        if key_name and key_value:
            auth = AUTH_STRATEGIES["APIキー(ヘッダー)"](key_name, key_value)
    elif auth_type == "APIキー(クエリ)":
        key_name = st.text_input("パラメータ名", value="api_key")
        key_value = st.text_input("APIキー", type="password")
        if key_name and key_value:
            auth = AUTH_STRATEGIES["APIキー(クエリ)"](key_name, key_value)

    # 追加ヘッダー / クエリパラメータ
    with st.expander("追加ヘッダー（JSON）"):
        headers_input = st.text_area("ヘッダー", value="{}", height=80)

    with st.expander("クエリパラメータ（JSON）"):
        params_input = st.text_area("パラメータ", value="{}", height=80, key="params_input")

    if method in ("POST", "PUT", "PATCH"):
        with st.expander("リクエストボディ（JSON）", expanded=True):
            body_input = st.text_area("ボディ", value="{}", height=120)
    else:
        body_input = "{}"

    if st.button("送信", type="primary"):
        if not base_url or not endpoint:
            st.error("ベースURLとエンドポイントを入力してください。")
        elif not base_url.startswith(("http://", "https://")):
            st.error("ベースURLは http:// または https:// から始めてください。")
        elif auth is None:
            st.error("認証情報を入力してください。")
        else:
            full_url = base_url.rstrip("/") + "/" + endpoint.lstrip("/")
            st.session_state["last_request"] = {
                "method": method,
                "url": full_url,
                "headers": headers_input,
                "params": params_input,
                "body": body_input,
            }

            json_error = None
            try:
                headers = json.loads(headers_input)
                params = json.loads(params_input)
                body = json.loads(body_input)
            except json.JSONDecodeError as e:
                json_error = str(e)

            if json_error:
                st.session_state["last_response"] = {"status_code": None, "body": None, "db_error": None, "error": f"JSON の形式が不正です: {json_error}"}
            else:
                preview_headers, preview_params = auth.apply(dict(headers), dict(params))
                st.session_state["last_request"] = {
                    "method": method,
                    "url": full_url,
                    "headers": preview_headers,
                    "params": preview_params,
                    "body": body,
                }

                with st.spinner("リクエスト送信中..."):
                    try:
                        result = client.request(
                            method=method,
                            base_url=base_url,
                            endpoint=endpoint,
                            auth=auth,
                            headers=headers,
                            params=params,
                            body=body,
                        )
                        st.session_state["last_response"] = {
                            "status_code": result["status_code"],
                            "body": result["body"],
                            "db_error": result["db_error"],
                            "error": None,
                        }
                    except requests.exceptions.SSLError:
                        st.session_state["last_response"] = {"status_code": None, "body": None, "db_error": None, "error": "SSL証明書エラーです。証明書の設定を確認してください。"}
                    except requests.exceptions.Timeout:
                        st.session_state["last_response"] = {"status_code": None, "body": None, "db_error": None, "error": "タイムアウトしました（30秒）。ネットワーク状況を確認してください。"}
                    except requests.exceptions.ConnectionError:
                        st.session_state["last_response"] = {"status_code": None, "body": None, "db_error": None, "error": "接続できません。ベースURLとネットワーク接続を確認してください。"}
                    except requests.exceptions.RequestException as e:
                        st.session_state["last_response"] = {"status_code": None, "body": None, "db_error": None, "error": f"リクエストエラー: {e}"}

with col_result:
    if "last_response" in st.session_state:
        resp = st.session_state["last_response"]
        if resp["error"]:
            st.error(resp["error"])
        else:
            status = resp["status_code"]
            color = "green" if status < 400 else "red"
            st.markdown(f"**ステータス**: :{color}[{status}]")
            st.json(resp["body"])
            if resp["db_error"]:
                st.warning(f"レスポンスの保存に失敗しました（ログには残りません）: {resp['db_error']}")

    if "last_request" in st.session_state:
        with st.expander("送信したリクエスト", expanded=True):
            st.json(st.session_state["last_request"])

st.divider()

# ─────────────────────────────────────────
# セクション2: ログ一覧
# ─────────────────────────────────────────
st.header("ログ一覧")

logs = repo.get_all()

if not logs:
    st.info("まだリクエストログがありません。")
else:
    for log in logs:
        status = log.response_status
        color = "green" if status and status < 400 else "red"
        label = f":{color}[{log.method} {log.endpoint}] — {status} — {log.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        with st.expander(label):
            st.markdown("**リクエスト**")
            st.json({
                "headers": log.request_headers_dict(),
                "params": log.request_params_dict(),
                "body": log.request_body_dict(),
            })
            st.markdown("**レスポンス**")
            st.json(log.response_body_dict())

st.divider()

# ─────────────────────────────────────────
# セクション3: OpenAPI生成
# ─────────────────────────────────────────
st.header("OpenAPI YAML 生成")

unique_base_urls = list({log.base_url for log in logs}) if logs else []

if not unique_base_urls:
    st.info("ログが蓄積されると、ここで OpenAPI YAML を生成できます。")
else:
    target_url = st.selectbox("対象ベースURL", unique_base_urls)
    api_title = st.text_input("API タイトル", value="My API")

    if st.button("YAML を生成"):
        try:
            openapi_doc = generate_openapi(base_url=target_url, title=api_title)
            yaml_str = to_yaml(openapi_doc)
            st.code(yaml_str, language="yaml")
            st.download_button(
                label="YAML をダウンロード",
                data=yaml_str,
                file_name="openapi.yaml",
                mime="text/yaml",
            )
        except Exception as e:
            st.error(f"OpenAPI YAML の生成に失敗しました: {e}")

st.divider()

# ─────────────────────────────────────────
# セクション4: バッチ実行
# ─────────────────────────────────────────
st.header("バッチ実行")

st.caption(
    "CSVでエンドポイント一覧を指定して順番に実行します。"
    " フォーマット: `method,endpoint,params,body`（params・body は JSON 形式、省略可）"
)

batch_base_url = st.text_input("ベースURL", placeholder="https://api.example.com", key="batch_base_url")

batch_auth_type = st.selectbox("認証方式", list(AUTH_STRATEGIES.keys()), key="batch_auth_type")

batch_auth = None
if batch_auth_type == "なし":
    batch_auth = AUTH_STRATEGIES["なし"]()
elif batch_auth_type == "Bearer Token":
    token = st.text_input("トークン", type="password", key="batch_token")
    if token:
        batch_auth = AUTH_STRATEGIES["Bearer Token"](token)
elif batch_auth_type == "APIキー(ヘッダー)":
    key_name = st.text_input("ヘッダー名", value="X-API-Key", key="batch_key_name")
    key_value = st.text_input("APIキー", type="password", key="batch_key_value")
    if key_name and key_value:
        batch_auth = AUTH_STRATEGIES["APIキー(ヘッダー)"](key_name, key_value)
elif batch_auth_type == "APIキー(クエリ)":
    key_name = st.text_input("パラメータ名", value="api_key", key="batch_query_key_name")
    key_value = st.text_input("APIキー", type="password", key="batch_query_key_value")
    if key_name and key_value:
        batch_auth = AUTH_STRATEGIES["APIキー(クエリ)"](key_name, key_value)

uploaded_file = st.file_uploader("CSVファイルをアップロード", type="csv")

if st.button("バッチ実行", type="primary"):
    if not batch_base_url:
        st.error("ベースURLを入力してください。")
    elif not batch_base_url.startswith(("http://", "https://")):
        st.error("ベースURLは http:// または https:// から始めてください。")
    elif batch_auth is None:
        st.error("認証情報を入力してください。")
    elif uploaded_file is None:
        st.error("CSVファイルをアップロードしてください。")
    else:
        content = uploaded_file.read().decode("utf-8")
        rows = parse_csv(content)

        if not rows:
            st.error("実行可能な行がCSVに含まれていません。フォーマット（method, endpoint 列が必須）を確認してください。")
        else:
            results = []
            progress_bar = st.progress(0)
            status_text = st.empty()

            for i, row in enumerate(rows):
                status_text.text(f"実行中 ({i + 1}/{len(rows)}): {row['method']} {row['endpoint']}")
                try:
                    result = client.request(
                        method=row["method"],
                        base_url=batch_base_url,
                        endpoint=row["endpoint"],
                        auth=batch_auth,
                        params=row["params"],
                        body=row["body"],
                    )
                    results.append({
                        "method": row["method"],
                        "endpoint": row["endpoint"],
                        "status": result["status_code"],
                        "error": result["db_error"] or "",
                        "success": result["status_code"] < 400,
                    })
                except requests.exceptions.SSLError:
                    results.append({"method": row["method"], "endpoint": row["endpoint"], "status": "-", "error": "SSLエラー", "success": False})
                except requests.exceptions.Timeout:
                    results.append({"method": row["method"], "endpoint": row["endpoint"], "status": "-", "error": "タイムアウト", "success": False})
                except requests.exceptions.ConnectionError:
                    results.append({"method": row["method"], "endpoint": row["endpoint"], "status": "-", "error": "接続エラー", "success": False})
                except Exception as e:
                    results.append({"method": row["method"], "endpoint": row["endpoint"], "status": "-", "error": str(e), "success": False})

                progress_bar.progress((i + 1) / len(rows))

            status_text.empty()

            success_count = sum(1 for r in results if r["success"])
            fail_count = len(results) - success_count
            st.markdown(f"**完了 — 成功: {success_count} / 失敗: {fail_count} / 合計: {len(results)}**")

            for r in results:
                icon = "✅" if r["success"] else "❌"
                line = f"{icon} `{r['method']} {r['endpoint']}` — {r['status']}"
                if r["error"]:
                    line += f" — {r['error']}"
                st.markdown(line)
