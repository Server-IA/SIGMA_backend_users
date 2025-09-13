from typing import Any, Dict

def mask_email(email: str) -> str:
    if not email or "@" not in email: return "***"
    local, domain = email.split("@", 1)
    return (local[:2] + "***@" + domain)

def build_login_meta(result: str, reason: str = None, **extras):
    meta = {"result": result}
    if reason: meta["reason"] = reason
    meta.update(extras)
    return meta