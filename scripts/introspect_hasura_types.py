import asyncio
import os
from pathlib import Path
import sys

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


QUERY = """
query TypeFields($typeName: String!) {
  __type(name: $typeName) {
    name
    fields {
      name
      type {
        kind
        name
        ofType {
          kind
          name
          ofType {
            kind
            name
          }
        }
      }
    }
  }
}
"""


def type_name(type_ref: dict) -> str:
    parts = []
    current = type_ref
    while current:
        name = current.get("name")
        kind = current.get("kind")
        if name:
            parts.append(name)
        elif kind:
            parts.append(kind)
        current = current.get("ofType")
    return " -> ".join(parts)


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

    type_names = sys.argv[1:] or [
        "TABLELIST",
        "STATLIST",
        "STAT_ATTRIBUTE",
        "STAT_ATTRIBUTE_VALUES",
        "DIMENSIONLIST",
        "DIMENSION_ITEM",
        "TABLE_DIMENSION",
        "MEASURELIST",
        "TABLE_MEASURE",
        "REGIONLIST",
        "TABLE_REGION",
        "TABLE_TIME",
        "TAGLIST",
        "TABLE_TAG",
    ]

    async with httpx.AsyncClient(timeout=20.0) as client:
        for name in type_names:
            response = await client.post(
                endpoint,
                json={"query": QUERY, "variables": {"typeName": name}},
                headers=headers,
            )
            response.raise_for_status()
            body = response.json()
            if body.get("errors"):
                print(f"## {name}\nERROR: {body['errors']}\n")
                continue
            type_info = body["data"]["__type"]
            if not type_info:
                print(f"## {name}\nnot found\n")
                continue
            print(f"## {name}")
            for field in type_info["fields"]:
                print(f"- {field['name']}: {type_name(field['type'])}")
            print()


if __name__ == "__main__":
    asyncio.run(main())
