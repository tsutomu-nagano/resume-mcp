import asyncio
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings
from app.graphql_client import GraphQLClient
from app.tools.datasets import get_dataset_impl


async def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("dataset_id is required.")
    graphql = GraphQLClient(
        settings.graphql_url,
        token=settings.graphql_token,
        api_key=settings.graphql_api_key,
        hasura_admin_secret=settings.hasura_admin_secret,
        hasura_role=settings.hasura_graphql_role,
        timeout_seconds=settings.graphql_timeout_seconds,
    )
    result = await get_dataset_impl(graphql, dataset_id=sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
