import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class GraphQLError(RuntimeError):
    """User-facing GraphQL error with a concise message."""


class GraphQLClient:
    def __init__(
        self,
        url: str,
        *,
        token: str | None = None,
        api_key: str | None = None,
        hasura_admin_secret: str | None = None,
        hasura_role: str | None = None,
        timeout_seconds: float = 20.0,
    ) -> None:
        self.url = url
        self.token = token
        self.api_key = api_key
        self.hasura_admin_secret = hasura_admin_secret
        self.hasura_role = hasura_role
        self.timeout_seconds = timeout_seconds

    async def execute(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        headers = {"content-type": "application/json"}
        if self.token:
            headers["authorization"] = f"Bearer {self.token}"
        if self.api_key:
            headers["x-api-key"] = self.api_key
        if self.hasura_admin_secret:
            headers["x-hasura-admin-secret"] = self.hasura_admin_secret
        if self.hasura_role:
            headers["x-hasura-role"] = self.hasura_role

        payload = {"query": query, "variables": variables or {}}
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(self.url, json=payload, headers=headers)
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            logger.exception("GraphQL request timed out")
            raise GraphQLError("GraphQL API request timed out.") from exc
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            logger.exception("GraphQL API returned HTTP error: %s", status_code)
            raise GraphQLError(f"GraphQL API returned HTTP {status_code}.") from exc
        except httpx.HTTPError as exc:
            logger.exception("GraphQL API connection failed")
            raise GraphQLError("Could not connect to the GraphQL API.") from exc

        try:
            body = response.json()
        except ValueError as exc:
            logger.exception("GraphQL API returned invalid JSON")
            raise GraphQLError("GraphQL API returned invalid JSON.") from exc

        errors = body.get("errors")
        if errors:
            logger.error("GraphQL response contained errors: %s", errors)
            message = errors[0].get("message", "GraphQL API returned an error.") if isinstance(errors, list) else str(errors)
            raise GraphQLError(message)

        data = body.get("data")
        if not isinstance(data, dict):
            logger.error("GraphQL response did not contain an object data field")
            raise GraphQLError("GraphQL API returned an unexpected response shape.")

        logger.info("GraphQL request succeeded")
        return data
