import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from app.config import Settings
from app.graphql_client import GraphQLClient, GraphQLError
from app.tools.datasets import get_dataset_impl, search_datasets_impl

logger = logging.getLogger(__name__)


def create_mcp(settings: Settings) -> FastMCP:
    mcp = FastMCP("resume-mcp", host=settings.mcp_host, port=settings.mcp_port)
    graphql = GraphQLClient(
        settings.graphql_url,
        token=settings.graphql_token,
        api_key=settings.graphql_api_key,
        hasura_admin_secret=settings.hasura_admin_secret,
        hasura_role=settings.hasura_graphql_role,
        timeout_seconds=settings.graphql_timeout_seconds,
    )
    @mcp.tool(
        annotations={"readOnlyHint": True},
        description=(
            "Search read-only dataset summaries from the existing GraphQL API. "
            "Use this when a user asks which datasets match a keyword before choosing one dataset ID."
        ),
    )
    async def search_datasets(keyword: str, limit: int = 10) -> dict[str, Any]:
        try:
            items = await search_datasets_impl(graphql, keyword=keyword, limit=limit)
            return {"items": items, "count": len(items)}
        except GraphQLError as exc:
            logger.error("search_datasets failed: %s", exc)
            return {"error": str(exc), "items": [], "count": 0}

    @mcp.tool(
        annotations={"readOnlyHint": True},
        description=(
            "Get read-only details for one dataset ID from the existing GraphQL API. "
            "Use this after search_datasets has returned a candidate dataset ID."
        ),
    )
    async def get_dataset(dataset_id: str) -> dict[str, Any]:
        try:
            return await get_dataset_impl(graphql, dataset_id=dataset_id)
        except GraphQLError as exc:
            logger.error("get_dataset failed: %s", exc)
            return {"error": str(exc), "id": dataset_id}

    return mcp
