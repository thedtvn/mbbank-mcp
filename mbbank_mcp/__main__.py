import asyncio
import os
import sys
import click
import uvicorn
from typing import Optional
from mbbank import MBBankAsync
from .core import crate_mcp_server
from starlette.applications import Starlette


def eprint(*args, **kwargs):
    """
    Print function that can be used to print stderr messages in MCP server mode stdio.
    """
    print(*args, file=sys.stderr, **kwargs)

@click.command()
@click.option("--username", default=None,
              help="MBBank username. If not provided, it will be read from the MBBANK_USERNAME environment variable.")
@click.option("--password", default=None,
              help="MBBank password. If not provided, it will be read from the MBBANK_PASSWORD environment variable.")
@click.option("--port", default=3000, help="Port to run the MCP server SSE mode. Default is 3000.")
@click.option("--host", default="localhost", help="Host to run the MCP server SSE mode. Default is localhost.")
@click.option("--sse", is_flag=True, help="Run the MCP server in SSE and Streamable HTTP mode. Default is Stdio mode.")
def main(username: Optional[str], password: Optional[str], port: int, host: str, sse: bool):
    username = username or os.getenv("MBBANK_USERNAME")
    password = password or os.getenv("MBBANK_PASSWORD")
    if not username or not password:
        eprint("Username and password must be provided check --help")
        sys.exit(1)
    mbbank_client = MBBankAsync(
        username=username,
        password=password
    )
    mcp_server = crate_mcp_server(mbbank_client, port=port)
    # check if the client is valid
    asyncio.run(mbbank_client._authenticate())
    eprint("Authenticated successfully.")
    if sse:
        streamable_http_app = mcp_server.streamable_http_app()
        sse_app = mcp_server.sse_app()
        async def lifespan(app):
            print("MCP server started in SSE mode.")
            print(f"You can access the SSE: http://{host}:{port}/sse")
            print(f"or streamable http: http://{host}:{port}/mcp")
            async with sse_app.router.lifespan_context(app), streamable_http_app.router.lifespan_context(app):
                yield
        starlette_app = Starlette(
            routes=streamable_http_app.routes + sse_app.routes,
            middleware=streamable_http_app.user_middleware + sse_app.user_middleware,
            lifespan=lifespan
        )
        config = uvicorn.Config(
            starlette_app,
            host=host,
            port=port,
            log_level=mcp_server.settings.log_level.lower(),
        )
        server = uvicorn.Server(config)
        server.run()
    else:
        eprint("Start Stdio server")
        mcp_server.run("stdio")


if __name__ == "__main__":
    main()
