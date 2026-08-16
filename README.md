# resume-mcp

ReSUME で参照している既存 GraphQL API を、ローカル MCP Client から利用するための read-only MCP Server です。

## 構成

```text
ChatGPT / MCP Client
        -> resume-mcp
        -> existing GraphQL API
```

`resume-mcp` はデータベースへ直接接続せず、GraphQL API を薄くラップします。初期 PoC では `search_datasets` と `get_dataset` の 2 tool を提供します。

## セットアップ

```bash
cp .env.example .env
```

`.env` で最低限 `HASURA_GRAPHQL_ENDPOINT` を設定してください。Hasura の admin secret を使う場合は `HASURA_ADMIN_SECRET`、特定 role で実行したい場合は `HASURA_GRAPHQL_ROLE` も設定します。

```text
HASURA_GRAPHQL_ENDPOINT=https://example.com/v1/graphql
HASURA_ADMIN_SECRET=...
HASURA_GRAPHQL_ROLE=...
```

Hasura 以外の GraphQL API に向ける場合は、従来どおり `GRAPHQL_URL`、`GRAPHQL_TOKEN`、`GRAPHQL_API_KEY` も利用できます。

`search_datasets` と `get_dataset` は、Hasura の `TABLELIST` / `TABLELIST_by_pk` を利用します。MCP の `dataset_id` は `TABLELIST.STATDISPID` です。

コンテナから候補を確認する場合は、`.env` を設定したうえで以下を実行できます。

```bash
docker compose run --rm app python scripts/introspect_hasura.py
```

スキーマ確認が必要な場合は、表示された候補や Hasura Console の API Explorer を確認してください。

## 起動

```bash
docker compose up --build
```

既定の接続先は以下です。

```text
http://localhost:8000/mcp
```

ポートを変更したい場合は `.env.app` の `MCP_PORT` を変更してください。

## OpenAI Tunnel Client

GPT など、ローカルPC外から MCP Server に接続する場合は、OpenAI の `tunnel-client` を使います。ChatGPT 側では Connection mode に `Tunnel` を選び、同じ `tunnel_id` を指定します。

### WSL/Linux amd64 で使う場合

WSL/Linux amd64 の場合は、Linux amd64 版の `tunnel-client` バイナリを `~/.local/bin/tunnel-client` に配置してください。

```bash
chmod +x ~/.local/bin/tunnel-client
```

`tunnel-client run --profile resume` で起動している場合は、通常 `~/.config/tunnel-client/resume.yaml` が使われます。Compose では `~/.config/tunnel-client` をコンテナへ読み取り専用でマウントします。

`.env.tunnel` に tunnel-client 用の値を設定します。

```text
CONTROL_PLANE_API_KEY=sk-...
CONTROL_PLANE_TUNNEL_ID=tunnel_0123456789abcdef0123456789abcdef
MCP_SERVER_URL=http://app:8000/mcp
HEALTH_LISTEN_ADDR=0.0.0.0:8080
HOME=/home/tunnel-client
TUNNEL_CLIENT_PROFILE=resume
TUNNEL_CLIENT_HEALTH_PORT=8080
```

MCP Server と tunnel-client を起動します。

```bash
docker compose up --build
```

Compose 内では `tunnel-client run --profile resume` が実行され、MCP Server には以下のURLで接続します。

```text
http://app:8000/mcp
```

ChatGPT 側には MCP Server URL ではなく、Tunnel connection として `CONTROL_PLANE_TUNNEL_ID` と同じ `tunnel_id` を指定します。

### tunnel-client.exe を使う場合

Windows 側の `tunnel-client.exe` を使う場合は、Docker Compose の Linux コンテナ内ではなく Windows 側で起動してください。

先に MCP Server を起動します。

```bash
docker compose up --build
```

別ターミナルで Windows 側の `tunnel-client.exe` を起動します。

```powershell
$env:CONTROL_PLANE_API_KEY="sk-..."
$env:CONTROL_PLANE_TUNNEL_ID="tunnel_0123456789abcdef0123456789abcdef"
$env:MCP_SERVER_URL="http://127.0.0.1:8000/mcp"
.\tunnel-client.exe run
```

## MCP Tool

MCP Tool と Hasura GraphQL の対応は [docs/API_GRAPHQL_MAPPING.md](docs/API_GRAPHQL_MAPPING.md) に整理しています。

### search_datasets

キーワードでデータセット候補を検索します。利用者が対象データセットをまだ特定していない場合に使います。

引数:

```text
keyword: string
limit: integer = 10
```

返却例:

```json
{
  "items": [
    {
      "id": "123456",
      "title": "人口推計",
      "description": "...",
      "organization": "..."
    }
  ],
  "count": 1
}
```

### get_dataset

データセット ID を指定して詳細情報を取得します。`search_datasets` で候補 ID を取得した後に使います。

引数:

```text
dataset_id: string
```

返却例:

```json
{
  "id": "123456",
  "title": "人口推計",
  "description": "...",
  "organization": "...",
  "metadata": {},
  "raw": {}
}
```

## テスト

依存関係のインストールも Docker 内で行います。

```bash
docker compose run --rm app python -m pytest
```

テストでは GraphQL API を直接呼ばず、GraphQL Client を mock して `search_datasets` / `get_dataset` の正常系・GraphQL Error・データなしを確認します。

## 実装メモ

- GraphQL の mutation は実装していません。
- MCP tool annotation には `readOnlyHint` を設定しています。
- GraphQL の token、API key、Hasura admin secret はログに出しません。
- Hasura の `TABLELIST` / `TABLELIST_by_pk` をデータセット API として利用します。
