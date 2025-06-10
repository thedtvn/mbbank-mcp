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
                "thedtvn/mbbank-lib:latest"
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

## Tools

### `get_balances`

Get the balance from all accounts in MB Bank.

### `get_today_date`

Returns the current date in YYYY-MM-DD format. Useful for transaction processing when model cannot access real time clock.

### `get_transactions`

Get the transactions from account in MB Bank for a given date.

**Parameters:**
- `account_number` (string): The account number to get transactions for
- `from_date` (string): The start date for the transactions in the format dd-mm-yyyy
- `to_date` (string): The end date for the transactions in the format dd-mm-yyyy

### `get_cards`

Get the cards information from MB Bank.

### `get_card_transactions`

Get the transactions for a specific card in MB Bank.

**Parameters:**
- `card_id` (string): The card ID to get transactions from. Obtain this from the get_cards tool
- `from_date` (string): The start date for the transactions in the format dd-mm-yyyy
- `to_date` (string): The end date for the transactions in the format dd-mm-yyyy

### `get_savings`

Get the savings accounts information from MB Bank.

### `get_saving_details`

Get the details of a specific savings account in MB Bank.

**Parameters:**
- `account_number` (string): The ID of the savings account to get details for. Obtain this from the get_savings tool
- `account_type` (Literal["OSA", "SBA"]): The type of the account, either "OSA" for Online Savings Account or "SBA" for Saving Bank Account

### `get_interest_rates`

Get the interest rates for savings accounts in MB Bank.

**Parameters:**
- `currency` (Literal["VND", "USD", "EUR"]): The currency for which to get the interest rates

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## FAQ

### Is this MCP server free to use?
Yes, this MCP server is free to use.

### Dose this MCP is safe to use?
Yes this mcp core is `mbbank-lib` you can check it [FAQ](https://mbbank.readthedocs.io/en/stable/#faq)

### Can this MCP Server transfer or withdraw money?
No, this MCP server does not support transferring or withdrawing money. It is designed for monitoring and analytics purposes only, such as checking balances and transactions.

However you should becareful when using this MCP server, as it read your sensitive data such as your account balances and transactions. Make sure to only use it with trusted applications and environments.


