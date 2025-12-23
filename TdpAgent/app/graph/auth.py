from __future__ import annotations
import os
import time
import requests

_TOKEN_CACHE = {"access_token": None, "exp": 0}

def get_graph_token() -> str:
    tenant = os.getenv("MS_TENANT_ID", "")
    client_id = os.getenv("MS_CLIENT_ID", "")
    client_secret = os.getenv("MS_CLIENT_SECRET", "")
    scope = os.getenv("GRAPH_SCOPE", "https://graph.microsoft.com/.default")

    if not (tenant and client_id and client_secret):
        raise RuntimeError("MS_TENANT_ID/MS_CLIENT_ID/MS_CLIENT_SECRET missing")

    now = int(time.time())
    if _TOKEN_CACHE["access_token"] and now < (_TOKEN_CACHE["exp"] - 60):
        return _TOKEN_CACHE["access_token"]

    url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
        "scope": scope,
    }
    r = requests.post(url, data=data, timeout=30)
    if not r.ok:
        raise RuntimeError(f"Token request failed: {r.status_code} {r.text}")
    j = r.json()

    _TOKEN_CACHE["access_token"] = j["access_token"]
    _TOKEN_CACHE["exp"] = now + int(j.get("expires_in", 3600))
    return _TOKEN_CACHE["access_token"]
