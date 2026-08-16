import asyncio
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings
from app.graphql_client import GraphQLClient
from app.tools.datasets import search_datasets_impl


async def main() -> None:
    keyword = sys.argv[1] if len(sys.argv) > 1 else "人口"
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    graphql = GraphQLClient(
        settings.graphql_url,
        token=settings.graphql_token,
        api_key=settings.graphql_api_key,
        hasura_admin_secret=settings.hasura_admin_secret,
        hasura_role=settings.hasura_graphql_role,
        timeout_seconds=settings.graphql_timeout_seconds,
    )
    result = await search_datasets_impl(graphql, keyword=keyword, limit=limit)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
