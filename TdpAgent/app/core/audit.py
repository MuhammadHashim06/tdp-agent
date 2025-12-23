import json
import time
from typing import Any, Dict

def audit_event(event: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "ts": int(time.time()),
        "event": event,
        "payload": payload,
    }

def audit_print(event: str, payload: Dict[str, Any]) -> None:
    print(json.dumps(audit_event(event, payload), ensure_ascii=False))
