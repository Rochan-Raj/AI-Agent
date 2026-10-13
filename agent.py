import uuid
from finance_tools import FinanceTools, SimulatedTransientError
from invoice_tools import find_latest_invoice
from models import AgentResult
from planner import interpret_task
from storage import Storage

class OperationsAgent:
    def __init__(self, storage, invoice_dir=None, fail_first_save=False, max_retries=2):
        self.storage = storage
        self.invoice_dir = invoice_dir
        self.finance = FinanceTools(storage, fail_first_save=fail_first_save)
        self.max_retries = max(0, int(max_retries))

    def run(self, request):
        task_id = str(uuid.uuid4())
        self.storage.log_event(task_id, "task_received", "ok", {"request": request})
        try:
            intent = interpret_task(request)
            self.storage.log_event(task_id, "understand_goal", "ok",
                                   {"workflow": intent.workflow, "vendor": intent.vendor})
            invoice = find_latest_invoice(intent.vendor, self.invoice_dir) if self.invoice_dir else find_latest_invoice(intent.vendor)
            self.storage.log_event(task_id, "find_invoice", "ok",
                                   {"invoice_id": invoice.invoice_id, "source": invoice.source_path})
            self.storage.log_event(task_id, "extract_fields", "ok",
                                   {"amount": str(invoice.amount), "due_date": invoice.due_date})
            for attempt in range(self.max_retries + 1):
                try:
                    record = self.finance.create_or_get_record(invoice)
                    self.storage.log_event(task_id, "write_finance_record", "ok",
                                           {"attempt": attempt + 1, "record_id": record.record_id})
                    break
                except SimulatedTransientError as exc:
                    self.storage.log_event(task_id, "write_finance_record", "retry",
                                           {"attempt": attempt + 1, "error": str(exc)})
                    if attempt >= self.max_retries:
                        raise
            saved = self.finance.get_record(invoice.invoice_id)
            verified = bool(saved and saved.invoice_id == invoice.invoice_id
                            and saved.vendor.casefold() == invoice.vendor.casefold()
                            and saved.amount == invoice.amount and saved.due_date == invoice.due_date)
            self.storage.log_event(task_id, "verify_record", "ok" if verified else "failed",
                                   {"verified": verified, "record_id": saved.record_id if saved else None})
            if not verified:
                return AgentResult(False, "Record verification failed.", invoice, saved, task_id)
            self.storage.log_event(task_id, "task_completed", "ok", {"record_id": saved.record_id})
            message = (f"Verified invoice {invoice.invoice_id} for {invoice.vendor}: "
                       f"amount {invoice.amount}, due {invoice.due_date}; finance record #{saved.record_id}.")
            return AgentResult(True, message, invoice, saved, task_id)
        except Exception as exc:
            self.storage.log_event(task_id, "task_failed", "failed",
                                   {"error_type": type(exc).__name__, "error": str(exc)})
            return AgentResult(False, f"Task failed safely: {exc}", task_id=task_id)
