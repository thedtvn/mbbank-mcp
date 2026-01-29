import asyncio
import datetime
import io
import json
import os
import time
import qrcode
from typing import Literal, TypedDict
from mbbank.modals import InterestRateResponseModal, SavingInfo, Card, TransferResponseModal
from mcp.server.fastmcp import FastMCP, Image
from mcp.types import ImageContent, TextContent
from mbbank import MBBankAsync, TransferContextAsync
from PIL import Image as PILImage
from .modals import (
    AccountModel, BalancesModel, TransactionTransferModel, TransactionModel, TransactionsModel,
    CardModel, CardsModel, SavingModel, SavingsModel, SavingDetailModel, SavingDetailsModel
)

class TransferState(TypedDict):
    create_time: float
    state: TransferContextAsync

def crate_mcp_server(mbbank: MBBankAsync, **setting) -> FastMCP:
    fast_mcp = FastMCP(
        name="mbbank-mcp",
        **setting,
    )

    transfer_manager: dict[str, TransferState] = {}

    @fast_mcp.tool()
    async def start_transfer(
        from_account: str,
        to_account: str,
        bank_code: str,
        amount: int,
        message: str
    ) -> list[TextContent | ImageContent]:
        """
        Start a transfer money from source account to destination account.

        Args:
            from_account (str): The source account number.
            to_account (str): The destination account number.
            bank_code (str): The bank code of the destination bank get from get_bank_list tool.
            amount (int): The amount to transfer.
            message (str): The message to include with the transfer.

        Returns:
            Qr code scan to confirm transfer and session id to verify transfer.
        """
        state = await mbbank.makeTransferAccountToAccount(
            src_account=from_account,
            dest_account=to_account,
            bank_code=bank_code,
            amount=amount,
            message=message
        )
        while True:
            # 4 * 2 = 8 characters 8 * 36 ( digits + letters ) = 288 possibilities so collision is very unlikely
            sid = os.urandom(4).hex()
            if sid not in transfer_manager: # check for super unlikely collision when this need precision
                break
        qr_content = await state.get_qr_code()
        transfer_manager[sid] = {
            "create_time": time.time(),
            "state": state,
        }
        img = qrcode.make(qr_content)
        img = img.resize((200, 200))
        new_img = PILImage.new("RGB", (400, 200), "white")
        new_img.paste(img, (100, 0))
        steam = io.BytesIO()
        new_img.save(steam, format="PNG")
        image_obj = Image(
            data=steam.getvalue(),
            format="PNG"
        )
        async def _remove_expired_transfers():
            await asyncio.sleep(130)  # 2 minutes and 10 seconds buffer
            current_time = time.time()
            expired_sids = [
                sid for sid, info in transfer_manager.items()
                if current_time - info["create_time"] > 120  # 2 minutes expiration
            ]
            for sid in expired_sids:
                del transfer_manager[sid]
        asyncio.create_task(_remove_expired_transfers())
        return [
            TextContent(type="text", text=json.dumps({
                "sid": sid,
                "amount": amount,
                "to_account": to_account,
                "bank_code": bank_code,
                "transfer_message": message,
                "message": "Then open MBBank app, "
                           "click on \"Xác Thực D-OTP\" on lock screen of MB Bank app to scan the QR code to get OTP code. "
                           "Also provide the sid to verify_transfer tool along with the OTP code."
            })),
            image_obj.to_image_content()
        ]

    @fast_mcp.tool()
    async def verify_transfer(sid: str, otp: str) -> str | TransferResponseModal:
        """
        Confirm the transfer with the provided OTP code.
        You Must call start_transfer first to get the session ID ask user to scan QR code to get OTP code.
        Args:
            sid (str): The session ID obtained from the start_transfer tool.
            otp (str): The OTP code received for the transfer ask user scan QR code in start_transfer tool.
        """
        if sid not in transfer_manager:
            return "The transfer session has expired or is invalid. Please start a new transfer."
        elif time.time() - transfer_manager[sid]["create_time"] > 120:
            del transfer_manager[sid]
            return "The transfer session has expired. Please start a new transfer."
        state = transfer_manager[sid]["state"]
        try:
            auth_type = await state.get_auth_list()
            result = await state.transfer(otp, auth_type.authList[0])
            del transfer_manager[sid]
            return result
        except Exception as e:
            del transfer_manager[sid]
            return f"Transfer failed: {str(e)}"

    @fast_mcp.tool()
    async def get_bank_list() -> dict[str, str]:
        """
        Get the list of banks and their corresponding bank codes.
        """
        bank_list = await mbbank.getBankList()
        return {bank.bankCode: bank.bankName for bank in bank_list.listBank}

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