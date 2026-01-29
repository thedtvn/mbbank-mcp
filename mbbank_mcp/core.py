import datetime
from typing import Literal

from mbbank.modals import InterestRateResponseModal, SavingInfo, Card
from mcp.server.fastmcp import FastMCP
from mbbank import MBBankAsync
from .modals import (
    AccountModel, BalancesModel, TransactionTransferModel, TransactionModel, TransactionsModel,
    CardModel, CardsModel, SavingModel, SavingsModel, SavingDetailModel, SavingDetailsModel
)

def crate_mcp_server(mbbank: MBBankAsync, **setting) -> FastMCP:
    fast_mcp = FastMCP(
        name="mbbank-mcp",
        **setting,
    )

    @fast_mcp.tool()
    async def get_balances() -> BalancesModel:
        """
        Get the balance from all accounts in MB Bank.
        """
        raw_balances = await mbbank.getBalance()
        return BalancesModel(
            account=[AccountModel(
                accountNumber=account.acctNo,
                accountName=account.acctAlias,
                currency=account.ccyCd,
                balance=account.currentBalance,
            ) for account in raw_balances.acct_list],
            internationalAccount=[AccountModel(
                accountNumber=account.acctNo,
                accountName=account.acctAlias,
                currency=account.ccyCd,
                balance=account.currentBalance,
            ) for account in raw_balances.internationalAcctList],
        )

    @fast_mcp.tool()
    async def get_today_date() -> str:
        """
        Get today's date in the format dd-mm-yyyy used for MB Bank transactions.
        """
        today = datetime.datetime.now()
        return today.strftime("%d-%m-%Y")

    @fast_mcp.tool()
    async def get_transactions(account_nuber: str, from_date: str, to_date: str) -> TransactionsModel:
        """
        Get the transactions for a specific account in MB Bank.
        :param account_nuber: The account number to get transactions from. Obtain this from the get_balances tool.
        :param from_date: The start date for the transactions in the format dd-mm-yyyy.
        :param to_date: The end date for the transactions in the format dd-mm-yyyy.
        """
        from_date_dt = datetime.datetime.strptime(from_date, "%d-%m-%Y")
        to_date_dt = datetime.datetime.strptime(to_date, "%d-%m-%Y")
        raw_transaction = await mbbank.getTransactionAccountHistory(
            accountNo=account_nuber,
            from_date=from_date_dt,
            to_date=to_date_dt
        )
        transactions = raw_transaction.transactionHistoryList
        return TransactionsModel(
            transactions=[TransactionModel(
                transactionDate=transaction.transactionDate,
                transactionId=transaction.refNo,
                description=transaction.description,
                amount=(
                    '+' + transaction.creditAmount if int(transaction.creditAmount)
                    else '-' + transaction.debitAmount
                ),
                currency=transaction.currency,
                transferredTo=TransactionTransferModel(
                    accountNumber=transaction.benAccountNo,
                    accountName=transaction.benAccountName,
                    bankName=transaction.bankName,
                ) if transaction.benAccountNo else None
            ) for transaction in transactions]
        )

    @fast_mcp.tool()
    async def get_cards() -> CardsModel:
        """
        Get the cards associated with the MB Bank account.
        """
        raw_cards = await mbbank.getCardList()
        def _format_card(card: Card):
            print(card)
            return CardModel(
                cardId=card.cardNo,
                cardNumber=card.cardCatCd,
                cardName=card.billingDt,
                cardClassDetail=card.cardLvl,
                cardType=card.cardCatCd,
                cardStatus=card.stsCard,
            )
        return CardsModel(
            cardClosed=[_format_card(card) for card in raw_cards.cardClosed],
            # Exclude new cards that are not yet activated
            cardsList=[_format_card(card) for card in raw_cards.cardList if card.stsCard != "New Card" ],
            cardOther=[_format_card(card) for card in raw_cards.cardOther],
        )

    @fast_mcp.tool()
    async def get_card_transactions(card_id: str, from_date: str, to_date: str) -> TransactionsModel:
        """
        Get the transactions for a specific card in MB Bank.
        :param card_id: The card ID to get transactions from. Obtain this from the get_cards tool.
        :param from_date: The start date for the transactions in the format dd-mm-yyyy.
        :param to_date: The end date for the transactions in the format dd-mm-yyyy.
        """
        from_date_dt = datetime.datetime.strptime(from_date, "%d-%m-%Y")
        to_date_dt = datetime.datetime.strptime(to_date, "%d-%m-%Y")
        raw_transaction = await mbbank.getCardTransactionHistory(
            cardNo=card_id,
            from_date=from_date_dt,
            to_date=to_date_dt
        )
        return TransactionsModel(
            transactions=[TransactionModel(
                transactionDate=transaction.transactionDate,
                description=transaction.description,
                amount=(
                    '+' + transaction.creditAmount if int(transaction.creditAmount)
                    else '-' + transaction.debitAmount
                ),
                currency=transaction.currency,
            ) for transaction in raw_transaction.transactionHistoryList]
        )

    @fast_mcp.tool()
    async def get_savings() -> SavingsModel:
        """
        Get the savings accounts associated with the MB Bank account.
        osa stands for Online Savings Account.
        sba stands for Saving Bank Account.
        """
        raw_savings = await mbbank.getSavingList()
        osa_savings = raw_savings.data.onlineFixedSaving.data
        sba_savings = raw_savings.data.branchSaving.data
        def _format_saving(saving: SavingInfo):
            return SavingModel(
                accountNumber=saving.savingAccountNumber,
                accountName=saving.customerName,
                currency=saving.currency,
                principalAmount=saving.principalAmount,
                openDate=saving.openDate,
                maturityDate=saving.maturityDate,
                isDeposit=saving.isDeposit,
                isWithDraw=saving.isWithDraw,
                ratePercentPerYear=saving.interestRate,
                beneficiaryAccount=saving.nominatedAccount,
            )
        return SavingsModel(
            osaList=[_format_saving(saving) for saving in osa_savings],
            sbaList=[_format_saving(saving) for saving in sba_savings],
        )

    @fast_mcp.tool()
    async def get_saving_details(account_number: str, account_type: Literal["OSA", "SBA"]) -> SavingDetailsModel:
        """
        Get the details of a specific savings account in MB Bank.
        :param account_number: The account number to get details from. Obtain this from the get_savings tool.
        :param account_type: The type of the account, either "OSA" for Online Savings Account or "SBA" for Saving Bank Account
        """
        raw_saving_details = await mbbank.getSavingDetail(accNo=account_number, accType=account_type)
        detail_savings = raw_saving_details.detailSaving
        return SavingDetailsModel(
            detailSaving=SavingDetailModel(
                accountNumber=detail_savings.savingsAccountNo,
                productName=detail_savings.productName,
                principalAmount=detail_savings.principalAmount,
                accruedInterestAmount=detail_savings.accruedInterestAmount,
                totalMaturityAmount=detail_savings.totalMaturityAmount,
                currency=detail_savings.currency,
                startDate=detail_savings.startDate,
                maturityDate=detail_savings.maturityDate,
                interestPaymentType=detail_savings.interestPaymentType,
                maturityInstructions=detail_savings.maturityInstructions,
                ratePercentPerYear=detail_savings.interestRate,
                beneficiaryAccount=detail_savings.beneficiaryAccount,
            )
        )

    @fast_mcp.tool()
    async def get_interest_rates(currency: Literal["VND", "USD", "EUR"]) -> InterestRateResponseModal:
        """
        Get the interest rates for savings accounts in MB Bank.
        :param currency: The currency for which to get the interest rates.
        """
        return await mbbank.getInterestRate(currency=currency)

    return fast_mcp