from typing import Any, Dict, Optional
import logging
from app.roles import models

log = logging.getLogger(__name__)

def mask_email(email: str) -> str:
    if not email or "@" not in email: return "***"
    local, domain = email.split("@", 1)
    return (local[:2] + "***@" + domain)

def build_login_meta(result: str, reason: str = None, **extras):
    meta = {"result": result}
    if reason: meta["reason"] = reason
    meta.update(extras)
    return meta


def get_permission_description(db_session, permission_id: Optional[int]) -> Optional[str]:
    """Resolver la descripción de un permiso por id. Safe: captura errores y devuelve None."""
    if permission_id is None:
        return None
    try:
        perm = db_session.query(models.Permission).filter(models.Permission.id == int(permission_id)).first()
        if not perm:
            return None
        return getattr(perm, "description", None) or getattr(perm, "name", None)
    except Exception:
        log.debug("permission lookup failed for id=%s", permission_id, exc_info=True)
        return None