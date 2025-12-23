import time
import requests
from sqlalchemy import select, func

from app.db import SessionLocal
from app.models import Email, Case, CaseEvent, Draft


API = "http://127.0.0.1:8000"


# ---------------------------
# Helpers
# ---------------------------
def wait_for_api(timeout=20):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(f"{API}/docs", timeout=2)
            if r.status_code == 200:
                print("API OK")
                return
        except Exception:
            pass
        time.sleep(1)
    raise RuntimeError("API did not start")


def db_counts():
    db = SessionLocal()
    counts = {
        "emails": db.scalar(select(func.count()).select_from(Email)),
        "cases": db.scalar(select(func.count()).select_from(Case)),
        "events": db.scalar(select(func.count()).select_from(CaseEvent)),
        "drafts": db.scalar(select(func.count()).select_from(Draft)),
        "stall_detected": db.scalar(
            select(func.count())
            .select_from(CaseEvent)
            .where(CaseEvent.event_type == "stall_detected")
        ),
    }
    db.close()
    return counts


def print_counts(label, counts):
    print(f"\n[{label}]")
    for k, v in counts.items():
        print(f"{k:16}: {v}")


# ---------------------------
# Tests
# ---------------------------
def test_poller_idempotency():
    print("\nTEST: Poller idempotency")

    before = db_counts()
    print_counts("before poller", before)

    # poller is assumed running, but we still trigger once
    import subprocess
    subprocess.run(["python", "-m", "app.worker.poller"], check=True)

    mid = db_counts()
    print_counts("after poller #1", mid)

    subprocess.run(["python", "-m", "app.worker.poller"], check=True)

    after = db_counts()
    print_counts("after poller #2", after)

    assert mid["emails"] == after["emails"], "Emails duplicated"
    assert mid["events"] == after["events"], "Events duplicated"

    print("PASS: poller idempotent")


def pick_case():
    r = requests.get(f"{API}/cases?limit=5")
    r.raise_for_status()
    items = r.json().get("items") or r.json()
    if not items:
        raise RuntimeError("No cases found")
    return items[0]["id"]


def test_stage2_staffing(case_id):
    print("\nTEST: Stage 2 staffing confirm")

    r = requests.post(
        f"{API}/cases/{case_id}/staffing/confirm",
        json={
            "therapist_name": "QA Tester",
            "discipline": "OT",
            "availability": "Mon/Wed",
            "referral_source_email": "qa@example.com",
        },
    )
    r.raise_for_status()

    case = requests.get(f"{API}/cases/{case_id}").json()
    assert case["status"] == "staffed", "Case not moved to staffed"

    print("PASS: Stage 2 staffing confirm")


def test_stage3_acceptance_draft(case_id):
    print("\nTEST: Stage 3 acceptance draft")

    r = requests.post(f"{API}/cases/{case_id}/drafts/acceptance")
    r.raise_for_status()
    data = r.json()

    assert "draft_id" in data, "No draft_id returned"
    assert data.get("graph_draft_message_id"), "No graph draft created"

    case = requests.get(f"{API}/cases/{case_id}").json()
    assert case["status"] == "acceptance drafted", "Status not updated"

    print("PASS: Stage 3 acceptance draft")


def test_case_watcher_dedupe():
    print("\nTEST: Case watcher dedupe")

    before = db_counts()["stall_detected"]

    import subprocess
    import sys

    subprocess.run([sys.executable, "-m", "app.worker.poller"], check=True)
    subprocess.run([sys.executable, "-m", "app.worker.poller"], check=True)

    subprocess.run([sys.executable, "-m", "app.worker.case_watcher"], check=True)
    subprocess.run([sys.executable, "-m", "app.worker.case_watcher"], check=True)

    after = db_counts()["stall_detected"]

    assert after == before or after == before + 1, "Watcher duplicating stalls"

    print("PASS: watcher dedupe")


# ---------------------------
# Runner
# ---------------------------
def main():
    wait_for_api()

    test_poller_idempotency()

    case_id = pick_case()
    print(f"\nUsing case_id={case_id}")

    test_stage2_staffing(case_id)
    test_stage3_acceptance_draft(case_id)
    test_case_watcher_dedupe()

    print("\n==============================")
    print("ALL BACKEND TESTS PASSED")
    print("FRONTEND CAN START SAFELY")
    print("==============================")


if __name__ == "__main__":
    main()
