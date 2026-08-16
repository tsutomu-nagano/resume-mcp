import logging

from app.config import settings
from app.mcp_server import create_mcp


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def main() -> None:
    configure_logging()
    logging.getLogger(__name__).info(
        "Starting resume-mcp on %s:%s", settings.mcp_host, settings.mcp_port
    )
    create_mcp(settings).run(transport="streamable-http")


if __name__ == "__main__":
    main()

