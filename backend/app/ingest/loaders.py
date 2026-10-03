import pandas as pd
from sqlmodel import Session
from app.db import engine

class Dataset:
    def __init__(self):
        self.purchase_books = pd.read_sql("SELECT * FROM purchasebook", engine)
        self.gstr2b = pd.read_sql("SELECT * FROM gstr2bentry", engine)
        self.supplier_invoices = pd.read_sql("SELECT * FROM supplierinvoice", engine)
        self.sales = pd.read_sql("SELECT * FROM salesinvoice", engine)
        self.bank = pd.read_sql("SELECT * FROM banktransaction", engine)
        self.suppliers = pd.read_sql("SELECT * FROM supplier", engine)
        self.business = pd.read_sql("SELECT * FROM business", engine)
        self.rates = pd.read_sql("SELECT * FROM ratetable", engine)
        self.trade_links = pd.read_sql("SELECT * FROM tradelink", engine)

def load_all() -> Dataset:
    return Dataset()
