import datetime
from typing import List, Literal
from mcp.server.fastmcp import FastMCP
from mbbank import MBBankAsync


def crate_mcp_server(mbbank: MBBankAsync, **setting) -> FastMCP:
    fast_mcp = FastMCP(
        name="mbbank-mcp",
        **setting,
    )

    @fast_mcp.tool()
    async def get_balances():
        """
        Get the balance from all accounts in MB Bank.
        """
        raw_balances: dict = await mbbank.getBalance()
        raw_balances.pop("refNo", None)
        accounts: List[dict] = raw_balances.pop("acct_list", [])
        raw_balances["account"] = [
            {
                "accountNumber": account["acctNo"],
                "accountName": account["acctAlias"],
                "currency": account["ccyCd"],
                "balance": account["currentBalance"],
            } for account in accounts
        ]
        international_accounts: List[dict] = raw_balances.pop("internationalAcctList", [])
        raw_balances["internationalAccount"] = [
            {
                "accountNumber": account["acctNo"],
                "accountName": account["acctAlias"],
                "currency": account["ccyCd"],
                "balance": account["currentBalance"],
            } for account in international_accounts
        ]
        return raw_balances

    @fast_mcp.tool()
    async def get_today_date() -> str:
        """
        Get today's date in the format dd-mm-yyyy used for MB Bank transactions.
        """
        today = datetime.datetime.now()
        return today.strftime("%d-%m-%Y")

    @fast_mcp.tool()
    async def get_transactions(account_nuber: str, from_date: str, to_date: str):
        """
        Get the transactions for a specific account in MB Bank.
        :param account_nuber: The account number to get transactions from. Obtain this from the get_balances tool.
        :param from_date: The start date for the transactions in the format dd-mm-yyyy.
        :param to_date: The end date for the transactions in the format dd-mm-yyyy.
        """
        from_date = datetime.datetime.strptime(from_date, "%d-%m-%Y")
        to_date = datetime.datetime.strptime(to_date, "%d-%m-%Y")
        raw_transaction: dict = await mbbank.getTransactionAccountHistory(
            accountNo=account_nuber,
            from_date=from_date,
            to_date=to_date
        )
        raw_transaction.pop("refNo", None)
        transactions: List[dict] = raw_transaction.pop("transactionHistoryList", [])
        raw_transaction["transactions"] = [
            {
                "transactionDate": transaction["transactionDate"],
                "transactionId": transaction["refNo"],
                "description": transaction["description"],
                "amount": '+' + transaction["creditAmount"] if int(transaction['creditAmount']) else '-' + transaction[
                    "debitAmount"],
                "currency": transaction["currency"],
                "tranferredTo": {
                    "accountNumber": transaction["benAccountNo"],
                    "accountName": transaction["benAccountName"],
                    "bankName": transaction["bankName"],
                } if transaction.get("benAccountNo") else None,
            } for transaction in transactions
        ]
        return raw_transaction

    @fast_mcp.tool()
    async def get_cards():
        """
        Get the cards associated with the MB Bank account.
        """
        raw_cards: dict = await mbbank.getCardList()
        raw_cards.pop("refNo", None)

        def _format_card(card):
            return {
                "cardId": card["cardNo"],
                "cardNumber": card["cardNumber"],
                "cardName": card["embossedName"],
                "cardClassDetail": card["cardClassDetail"],
                "cardType": card["cardCatCd"],
                "validThrough": f"{card['validThrough'][2:4]}/{card['validThrough'][0:2]}",
                "cardStatus": card["cardStatusDetail"]
            }

        card_closed: List[dict] = raw_cards.pop("cardClosed", [])
        raw_cards["cardClosed"] = [_format_card(card) for card in card_closed]

        cards: List[dict] = raw_cards.pop("cardList", [])
        raw_cards["cardsList"] = [
            _format_card(card) for card in cards
            if card["cardStatusDetail"] != "New Card"  # Exclude new cards that are not yet activated
        ]

        card_other: List[dict] = raw_cards.pop("cardOther", [])
        raw_cards["cardOther"] = [_format_card(card) for card in card_other]
        return raw_cards

    @fast_mcp.tool()
    async def get_card_transactions(card_id: str, from_date: str, to_date: str):
        """
        Get the transactions for a specific card in MB Bank.
        :param card_id: The card ID to get transactions from. Obtain this from the get_cards tool.
        :param from_date: The start date for the transactions in the format dd-mm-yyyy.
        :param to_date: The end date for the transactions in the format dd-mm-yyyy.
        """
        from_date = datetime.datetime.strptime(from_date, "%d-%m-%Y")
        to_date = datetime.datetime.strptime(to_date, "%d-%m-%Y")
        raw_transaction: dict = await mbbank.getCardTransactionHistory(
            cardNo=card_id,
            from_date=from_date,
            to_date=to_date
        )
        raw_transaction.pop("refNo", None)
        print(raw_transaction)
        transactions: List[dict] = raw_transaction.pop("transactionHistoryList", [])
        raw_transaction["transactions"] = [
            {
                "transactionDate": transaction["transactionDate"],
                "description": transaction["description"],
                "amount": '+' + transaction["creditAmount"] if int(transaction['creditAmount']) else '-' + transaction[
                    "debitAmount"],
                "currency": transaction["currency"],
            } for transaction in transactions
        ]
        return raw_transaction

    @fast_mcp.tool()
    async def get_savings():
        """
        Get the savings accounts associated with the MB Bank account.
        osa stands for Online Savings Account.
        sba stands for Saving Bank Account.
        """
        raw_savings: dict = await mbbank.getSavingList()
        raw_savings.pop("refNo", None)

        def _format_saving(saving):
            data = {
                "accountNumber": saving["accountNumber"],
                "accountName": saving["accountName"],
                "currency": saving["currency"],
                "principalAmount": saving["principalAmount"],
                "accruedInterestAmount": saving["accruedInterestAmount"],
                "openDate": saving["openDate"],
                "maturityDate": saving["maturityDate"],
                "isAddMoreAble": saving["isSendMore"],
                "ratePercentPerYear": saving["rate"],
                "beneficiaryAccount": saving["nominatedAccount"],
            }
            return data

        osa_savings: List[dict] = raw_savings.pop("osaList", [])
        raw_savings["osaList"] = [_format_saving(saving) for saving in osa_savings]

        sba_savings: List[dict] = raw_savings.pop("sbaList", [])
        raw_savings["sbaList"] = [_format_saving(saving) for saving in sba_savings]
        return raw_savings

    @fast_mcp.tool()
    async def get_saving_details(account_number: str, account_type: Literal["OSA", "SBA"]):
        """
        Get the details of a specific savings account in MB Bank.
        :param account_number: The account number to get details from. Obtain this from the get_savings tool.
        :param account_type: The type of the account, either "OSA" for Online Savings Account or "SBA" for Saving Bank Account
        """
        raw_saving_details: dict = await mbbank.getSavingDetail(accNo=account_number, accType=account_type)
        raw_saving_details.pop("refNo", None)
        detail_savings: dict | None = raw_saving_details.pop("detailSaving", None)
        if detail_savings is None:
            return {"error": "No details found for this account."}
        print(detail_savings)
        raw_saving_details["detailSaving"] = {
            "accountNumber": detail_savings["savingsAccountNo"],
            "productName": detail_savings["productName"],
            "principalAmount": detail_savings["principalAmount"],
            "accruedInterestAmount": detail_savings["accruedInterestAmount"],
            "totalMaturityAmount": detail_savings["totalMaturityAmount"],
            "currency": detail_savings["currency"],
            "startDate": detail_savings["startDate"],
            "maturityDate": detail_savings["maturityDate"],
            "interestPaymentType": detail_savings["interestPaymentType"],
            "maturityInstructions": detail_savings["maturityInstructions"],
            "ratePercentPerYear": detail_savings["interestRate"],
            "beneficiaryAccount": detail_savings["beneficiaryAccount"],
        }
        return raw_saving_details

    @fast_mcp.tool()
    async def get_interest_rates(currency: Literal["VND", "USD", "EUR"]):
        """
        Get the interest rates for savings accounts in MB Bank.
        :param currency: The currency for which to get the interest rates.
        """
        raw_interest_rates: dict = await mbbank.getInterestRate(currency=currency)
        raw_interest_rates.pop("refNo", None)

        def _format_interest_rate(interest_rate: dict):
            interest_rate.pop("productName", None)
            return interest_rate

        interest_rates: List[dict] = raw_interest_rates.pop("interestRateList", [])
        raw_interest_rates["interestRateList"] = [
            _format_interest_rate(interest_rate) for interest_rate in interest_rates
        ]

        return raw_interest_rates

    return fast_mcp
