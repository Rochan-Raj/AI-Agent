import json
import os
import re
from dotenv import load_dotenv
from models import TaskIntent

load_dotenv()

def fallback_vendor(request):
    patterns = [
        r"from\s+([A-Za-z0-9][A-Za-z0-9 &._-]{0,50}?)(?:\s*[,.;]|\s+(?:and|into|enter|process|extract|verify|record)\b|$)",
        r"([A-Za-z0-9][A-Za-z0-9 &._-]{0,40}?)\s+invoice",
    ]
    for pattern in patterns:
        match = re.search(pattern, request, flags=re.IGNORECASE)
        if match:
            value = match.group(1).strip(" .,-")
            if value and value.lower() not in {"the latest", "latest", "an", "the"}:
                return value
    return "Acme Ltd"

def interpret_task(request):
    if not request.strip():
        raise ValueError("Please provide a task request.")
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and api_key != "replace_me":
        try:
            from openai import OpenAI
            kwargs = {"api_key": api_key}
            if os.getenv("OPENAI_BASE_URL"):
                kwargs["base_url"] = os.getenv("OPENAI_BASE_URL")
            client = OpenAI(**kwargs)
            response = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content":
                     "Return JSON with workflow and vendor. workflow must be "
                     "'process_invoice' only for invoice-processing requests, otherwise 'unsupported'. "
                     "vendor must be explicitly named in the request, or empty if unclear. Never invent it."},
                    {"role": "user", "content": request}
                ]
            )
            data = json.loads(response.choices[0].message.content or "{}")
            if data.get("workflow") != "process_invoice":
                raise ValueError("This prototype supports invoice-processing tasks only.")
            vendor = str(data.get("vendor", "")).strip()
            if not vendor:
                raise ValueError("I could not identify the vendor. Please specify it.")
            return TaskIntent("process_invoice", vendor, request)
        except ValueError:
            raise
        except Exception as exc:
            print(f"[planner] Hosted LLM unavailable; using local fallback ({type(exc).__name__}).")
    if "invoice" not in request.lower():
        raise ValueError("This prototype supports invoice-processing tasks only.")
    return TaskIntent("process_invoice", fallback_vendor(request), request)
