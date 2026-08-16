from typing import Any

import pytest

from app.graphql_client import GraphQLError
from app.tools.datasets import get_dataset_impl, search_datasets_impl


class FakeGraphQL:
    def __init__(self, data: dict[str, Any] | None = None, error: Exception | None = None) -> None:
        self.data = data or {}
        self.error = error
        self.calls: list[dict[str, Any]] = []

    async def execute(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        self.calls.append({"query": query, "variables": variables})
        if self.error:
            raise self.error
        return self.data


def table_row() -> dict[str, Any]:
    return {
        "STATDISPID": "000001",
        "TITLE": "人口推計",
        "STATCODE": "00200524",
        "SURVEY_DATE": "2024-10",
        "YEAR_S": 2020,
        "YEAR_E": 2024,
        "CYCLE": "年次",
        "STATLIST": {
            "STATCODE": "00200524",
            "STATNAME": "人口推計",
            "GOVCODE": "00200",
            "GOVLIST": {"GOVCODE": "00200", "GOVNAME": "総務省"},
            "STAT_ATTRIBUTE_VALUEs": [
                {
                    "VALUE": "基幹統計",
                    "STAT_ATTRIBUTE": {"CODE": "statistics_type", "NAME_JA": "統計種別"},
                }
            ],
        },
        "TABLE_DIMENSIONs": [{"CLASS_NAME": "area"}, {"CLASS_NAME": "sex"}],
        "TABLE_MEASUREs": [{"NAME": "population"}],
        "TABLE_REGIONs": [{"NAME": "全国"}],
        "TABLE_REGIONTYPEs": [{"REGIONTYPE": "country"}],
        "TABLE_TAGs": [{"TAG_NAME": "人口"}],
        "TABLE_TIMEs": [{"YEAR": 2024, "MONTH": 10, "TERM": "2024", "PERIOD_TYPE": "month"}],
    }


@pytest.mark.asyncio
async def test_search_datasets_returns_summaries() -> None:
    graphql = FakeGraphQL({"TABLELIST": [table_row()]})

    result = await search_datasets_impl(graphql, keyword="人口", limit=10)

    assert result == [
        {
            "id": "000001",
            "title": "人口推計",
            "description": "人口推計 / 2024-10 / 2020-2024 / 年次",
            "organization": "総務省",
            "metadata": {
                "statcode": "00200524",
                "statname": "人口推計",
                "survey_date": "2024-10",
                "year_start": 2020,
                "year_end": 2024,
                "cycle": "年次",
                "govcode": "00200",
            },
        }
    ]
    assert graphql.calls[0]["variables"] == {"keyword": "%人口%", "limit": 10}
    assert "TABLELIST" in graphql.calls[0]["query"]


@pytest.mark.asyncio
async def test_search_datasets_propagates_graphql_error() -> None:
    graphql = FakeGraphQL(error=GraphQLError("GraphQL failed"))

    with pytest.raises(GraphQLError, match="GraphQL failed"):
        await search_datasets_impl(graphql, keyword="population")


@pytest.mark.asyncio
async def test_search_datasets_returns_empty_list() -> None:
    graphql = FakeGraphQL({"TABLELIST": []})

    result = await search_datasets_impl(graphql, keyword="missing")

    assert result == []


@pytest.mark.asyncio
async def test_get_dataset_returns_detail() -> None:
    graphql = FakeGraphQL({"TABLELIST_by_pk": table_row()})

    result = await get_dataset_impl(graphql, dataset_id="000001")

    assert result["id"] == "000001"
    assert result["title"] == "人口推計"
    assert result["organization"] == "総務省"
    assert result["metadata"]["attributes"] == [
        {"code": "statistics_type", "name": "統計種別", "value": "基幹統計"}
    ]
    assert result["metadata"]["dimensions"] == ["area", "sex"]
    assert result["metadata"]["measures"] == ["population"]
    assert result["metadata"]["regions"] == ["全国"]
    assert result["metadata"]["region_types"] == ["country"]
    assert result["metadata"]["tags"] == ["人口"]
    assert result["metadata"]["times"] == [
        {"year": 2024, "month": 10, "term": "2024", "period_type": "month"}
    ]
    assert result["raw"]["STATDISPID"] == "000001"
    assert "TABLELIST_by_pk" in graphql.calls[0]["query"]


@pytest.mark.asyncio
async def test_get_dataset_propagates_graphql_error() -> None:
    graphql = FakeGraphQL(error=GraphQLError("GraphQL failed"))

    with pytest.raises(GraphQLError, match="GraphQL failed"):
        await get_dataset_impl(graphql, dataset_id="000001")


@pytest.mark.asyncio
async def test_get_dataset_raises_when_not_found() -> None:
    graphql = FakeGraphQL({"TABLELIST_by_pk": None})

    with pytest.raises(GraphQLError, match="not found"):
        await get_dataset_impl(graphql, dataset_id="missing")
