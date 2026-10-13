import argparse
from agent import OperationsAgent
from storage import Storage

def main():
    parser = argparse.ArgumentParser(description="OpenOps autonomous invoice-processing agent")
    parser.add_argument("task", help="Natural-language invoice task in quotes")
    parser.add_argument("--fail-first-save", action="store_true",
                        help="Simulate a transient write failure to demonstrate recovery")
    parser.add_argument("--db", default=None, help="Optional SQLite database path")
    args = parser.parse_args()
    storage = Storage(args.db)
    agent = OperationsAgent(storage, fail_first_save=args.fail_first_save)
    result = agent.run(args.task)
    print("\n=== OPENOPS RESULT ===")
    print(f"Success: {result.success}")
    print(result.message)
    if result.task_id:
        print(f"Task ID: {result.task_id}\n\n=== EXECUTION TRACE ===")
        for event in storage.get_events(result.task_id):
            print(f"[{event['status'].upper():6}] {event['step']}: {event['detail']}")
    raise SystemExit(0 if result.success else 1)

if __name__ == "__main__":
    main()
