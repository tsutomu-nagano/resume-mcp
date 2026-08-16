import asyncio
import os
from pathlib import Path
import sys

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


QUERY = """
query QueryRootFields {
  __schema {
    queryType {
      fields {
        name
        args {
          name
        }
      }
    }
  }
}
"""


async def main() -> None:
    endpoint = os.getenv("HASURA_GRAPHQL_ENDPOINT") or os.getenv("GRAPHQL_URL")
    if not endpoint:
        raise SystemExit("HASURA_GRAPHQL_ENDPOINT or GRAPHQL_URL is required.")

    headers = {"content-type": "application/json"}
    admin_secret = os.getenv("HASURA_ADMIN_SECRET")
    role = os.getenv("HASURA_GRAPHQL_ROLE")
    if admin_secret:
        headers["x-hasura-admin-secret"] = admin_secret
    if role:
        headers["x-hasura-role"] = role

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(endpoint, json={"query": QUERY}, headers=headers)
        response.raise_for_status()
        body = response.json()

    if body.get("errors"):
        raise SystemExit(body["errors"])

    fields = body["data"]["__schema"]["queryType"]["fields"]
    print("query_root fields:")
    for field in fields:
        arg_names = ", ".join(arg["name"] for arg in field.get("args", []))
        print(f"- {field['name']}({arg_names})")


if __name__ == "__main__":
    asyncio.run(main())
