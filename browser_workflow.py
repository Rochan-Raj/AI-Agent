"""Use Playwright to enter an invoice into the local OpenOps Finance website."""
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from invoice_tools import find_latest_invoice

BASE_URL = "http://127.0.0.1:5000"

def main():
    parser = argparse.ArgumentParser(description="Process an invoice through a real local browser UI")
    parser.add_argument("vendor", nargs="?", default="Acme Ltd", help="Vendor name, e.g. Acme Ltd")
    parser.add_argument("--headless", action="store_true", help="Run Chromium without showing a browser window")
    args = parser.parse_args()
    invoice = find_latest_invoice(args.vendor)
    print(f"[OK] Found {invoice.invoice_id} for {invoice.vendor}: {invoice.amount}, due {invoice.due_date}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=args.headless)
        page = browser.new_page()
        try:
            page.goto(BASE_URL, wait_until="domcontentloaded", timeout=10000)
            page.get_by_label("Invoice ID").fill(invoice.invoice_id)
            page.get_by_label("Vendor").fill(invoice.vendor)
            page.get_by_label("Amount").fill(f"{invoice.amount:.2f}")
            page.get_by_label("Due date").fill(invoice.due_date)
            page.locator('input[name="source_path"]').fill(invoice.source_path)
            print("[OK] Playwright filled the finance form")
            page.get_by_role("button", name="Save invoice").click()
            page.get_by_test_id("success-message").wait_for(timeout=5000)
            row = page.locator(f'tr[data-invoice-id="{invoice.invoice_id}"]')
            row.wait_for(timeout=5000)
            cells = [x.strip() for x in row.locator("td").all_text_contents()]
            expected = [invoice.invoice_id, invoice.vendor, f"{invoice.amount:.2f}", invoice.due_date]
            observed = cells[1:5]
            if observed != expected:
                raise RuntimeError(f"Read-back verification failed. Expected {expected}; got {observed}")
            print(f"[OK] Saved record #{cells[0]} through the browser")
            print(f"[OK] Read-after-write verification passed: {observed}")
            print("\nBROWSER WORKFLOW SUCCESS")
        except (PlaywrightTimeoutError, Exception) as exc:
            print(f"\nBROWSER WORKFLOW FAILED: {exc}")
            print("Check that finance_web.py is running at http://127.0.0.1:5000")
            raise SystemExit(1)
        finally:
            browser.close()

if __name__ == "__main__":
    main()
