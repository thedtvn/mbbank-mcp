from typing import List, Optional, Union
from pydantic import BaseModel

# This model use as proxy to rename fields from API responses to more friendly names

class AccountModel(BaseModel):
    accountNumber: str
    accountName: str
    currency: str
    balance: str

class BalancesModel(BaseModel):
    account: List[AccountModel]
    internationalAccount: List[AccountModel]
    # Add other fields as needed

class TransactionTransferModel(BaseModel):
    accountNumber: Optional[str]
    accountName: Optional[str]
    bankName: Optional[str]

class TransactionModel(BaseModel):
    transactionDate: str
    transactionId: Optional[str] = None
    description: str
    amount: str
    currency: str
    transferredTo: Optional[TransactionTransferModel] = None

class TransactionsModel(BaseModel):
    transactions: List[TransactionModel]
    # Add other fields as needed

class CardModel(BaseModel):
    cardId: str
    cardNumber: str
    cardName: str
    cardClassDetail: str
    cardType: str
    cardStatus: Optional[str] = None

class CardsModel(BaseModel):
    cardClosed: List[CardModel]
    cardsList: List[CardModel]
    cardOther: List[CardModel]

class SavingModel(BaseModel):
    accountNumber: str
    accountName: str
    currency: str
    principalAmount: Union[int, float]
    openDate: str
    maturityDate: str
    isDeposit: bool
    isWithDraw: bool
    ratePercentPerYear: Union[int, float]
    beneficiaryAccount: str

class SavingsModel(BaseModel):
    osaList: List[SavingModel]
    sbaList: List[SavingModel]

class SavingDetailModel(BaseModel):
    accountNumber: str
    productName: str
    principalAmount: str
    accruedInterestAmount: str
    totalMaturityAmount: str
    currency: str
    startDate: str
    maturityDate: str
    interestPaymentType: str
    maturityInstructions: str
    ratePercentPerYear: str
    beneficiaryAccount: str

class SavingDetailsModel(BaseModel):
    detailSaving: Optional[SavingDetailModel] = None
    error: Optional[str] = None
