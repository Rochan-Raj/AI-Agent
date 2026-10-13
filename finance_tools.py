from decimal import Decimal
from models import FinanceRecord

class SimulatedTransientError(RuntimeError):
    pass

class FinanceTools:
    def __init__(self, storage, fail_first_save=False):
        self.storage = storage
        self.fail_first_save = fail_first_save
        self.failure_used = False

    def create_or_get_record(self, invoice):
        if self.fail_first_save and not self.failure_used:
            self.failure_used = True
            raise SimulatedTransientError("Simulated transient finance-system timeout.")
        with self.storage.connect() as conn:
            conn.execute(
                "INSERT INTO finance_records(invoice_id, vendor, amount, due_date, source_path) "
                "VALUES (?, ?, ?, ?, ?) ON CONFLICT(invoice_id) DO NOTHING",
                (invoice.invoice_id, invoice.vendor, str(invoice.amount),
                 invoice.due_date, invoice.source_path)
            )
            row = conn.execute(
                "SELECT * FROM finance_records WHERE invoice_id = ?", (invoice.invoice_id,)
            ).fetchone()
        return self.to_record(row)

    def get_record(self, invoice_id):
        with self.storage.connect() as conn:
            row = conn.execute(
                "SELECT * FROM finance_records WHERE invoice_id = ?", (invoice_id,)
            ).fetchone()
        return self.to_record(row) if row else None

    @staticmethod
    def to_record(row):
        return FinanceRecord(
            row["record_id"], row["invoice_id"], row["vendor"],
            Decimal(row["amount"]), row["due_date"], row["source_path"]
        )
