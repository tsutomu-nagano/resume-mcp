from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    graphql_url: str = Field(
        ...,
        validation_alias=AliasChoices("HASURA_GRAPHQL_ENDPOINT", "GRAPHQL_URL"),
    )
    graphql_token: str | None = Field(default=None, alias="GRAPHQL_TOKEN")
    graphql_api_key: str | None = Field(default=None, alias="GRAPHQL_API_KEY")
    hasura_admin_secret: str | None = Field(default=None, alias="HASURA_ADMIN_SECRET")
    hasura_graphql_role: str | None = Field(default=None, alias="HASURA_GRAPHQL_ROLE")
    graphql_timeout_seconds: float = Field(default=20.0, alias="GRAPHQL_TIMEOUT_SECONDS")

    mcp_host: str = Field(default="0.0.0.0", alias="MCP_HOST")
    mcp_port: int = Field(default=8000, alias="MCP_PORT")


settings = Settings()
