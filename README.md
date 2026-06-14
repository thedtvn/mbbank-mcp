# MBBank MCP Server

MCP server for MBBank API helping monitoring and analytics transactions and balances.

## Requirements
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Python 3.10 or higher

## Usage

### Install in Claude Desktop

Follow the MCP install [guide](https://modelcontextprotocol.io/quickstart/user), use the following configuration:

> **Note**  
> Replace `<your_username>` and `<your_password>` with your actual MB Bank credentials.  
> You should not set `env` variables for username and password, as it errors python runtime.

```json
{
    "mcpServers": {
        "mbbank": {
            "command": "uvx",
            "args": [
                "mbbank-mcp",
                "--username=<your_username>",
                "--password=<your_password>"
            ]
        }
    }
}
```

With docker, you can use the following this configuration:

```json
{
    "mcpServers": {
        "mbbank": {
            "command": "docker",
            "args": [
                "run",
                "-i",
                "--rm",
                "-e",
                "MBBANK_USERNAME",
                "-e",
                "MBBANK_PASSWORD",
                "thedtvn/mbbank-mcp:latest"
            ],
            "env": {
                "MBBANK_USERNAME": "<your_username>",
                "MBBANK_PASSWORD": "<your_password>"
            }
        }
    }
}
```

### Standalone MCP Server

To run the MCP server standalone, add the `--sse` flag to enable SSE mode (default is stdio mode).

The `--username` and `--password` flags are optional - you can also set them as environment variables `MBBANK_USERNAME` and `MBBANK_PASSWORD`.

You can specify `--host` and `--port` flags for the server address (default: `localhost:3000`).

```bash
uvx mbbank-mcp --username=<your_username> --password=<your_password> --host=localhost --port=3000 --sse 
```

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## FAQ

### Is this MCP server free to use?
Yes, this MCP server is free to use.

### Dose this MCP is safe to use?
Yes this mcp core is `mbbank-lib` you can check it https://mbbank.readthedocs.io/en/stable/

## Disclaimer

This project is not affiliated with MBBank. Use it responsibly and at your own risk.

The author is not liable for any damage or loss resulting from the use of this library.

Always ensure you comply with MBBank's terms of service and security guidelines when using this mcp.

## Legal

Any takedown requests or legal problems from MBBank can contact the author at:

- Email: mbbankmcp-legal@thedt.id.vn


