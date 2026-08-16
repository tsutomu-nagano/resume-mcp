import logging
from typing import Any, Protocol

from app.dataset_queries import (
    DATASET_DETAIL_FIELD,
    DATASET_LIST_FIELD,
    build_get_dataset_query,
    build_search_datasets_query,
    normalize_dataset,
    normalize_dataset_summary,
)
from app.graphql_client import GraphQLError

logger = logging.getLogger(__name__)


class ExecutesGraphQL(Protocol):
    async def execute(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        ...


async def search_datasets_impl(
    graphql: ExecutesGraphQL,
    *,
    keyword: str,
    limit: int = 10,
) -> list[dict[str, Any]]:
    logger.info("Tool called: search_datasets")
    normalized_limit = max(1, min(limit, 100))
    data = await graphql.execute(
        build_search_datasets_query(),
        {"keyword": f"%{keyword}%", "limit": normalized_limit},
    )
    rows = data.get(DATASET_LIST_FIELD)
    if rows is None:
        raise GraphQLError(f"GraphQL response did not include '{DATASET_LIST_FIELD}'.")
    if not isinstance(rows, list):
        raise GraphQLError(f"GraphQL field '{DATASET_LIST_FIELD}' was not a list.")
    return [normalize_dataset_summary(row) for row in rows if isinstance(row, dict)]


async def get_dataset_impl(
    graphql: ExecutesGraphQL,
    *,
    dataset_id: str,
) -> dict[str, Any]:
    logger.info("Tool called: get_dataset")
    data = await graphql.execute(build_get_dataset_query(), {"datasetId": dataset_id})
    row = data.get(DATASET_DETAIL_FIELD)
    if row is None:
        raise GraphQLError(f"Dataset '{dataset_id}' was not found.")
    if not isinstance(row, dict):
        raise GraphQLError("GraphQL API returned an unexpected dataset shape.")
    return normalize_dataset(row)
