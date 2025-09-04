from typing import Any, Dict

def user_snapshot(user_obj) -> dict:
    """Snapshot compacto para auditoría de usuario."""
    roles = getattr(user_obj, "roles", []) or []
    return {
        "id": getattr(user_obj, "id", None),
        "email": getattr(user_obj, "email", None),
        "name": getattr(user_obj, "name", None),
        "first_last_name": getattr(user_obj, "first_last_name", None),
        "second_last_name": getattr(user_obj, "second_last_name", None),
        "gender_id": getattr(user_obj, "gender_id", None),
        "status_id": getattr(user_obj, "status_id", None),
        "roles": sorted([getattr(r, "id", None) for r in roles if getattr(r, "id", None) is not None]),
    }

def mask_doc(doc: str | None) -> str | None:
    """Enmascara documento: deja últimos 3 dígitos."""
    if not doc:
        return doc
    d = str(doc)
    if len(d) <= 3:
        return "***"
    return "*" * (len(d) - 3) + d[-3:]

def prereg_attempt_meta(
    *,
    document_type_id: int,
    document_number: str,
    date_issuance_document,
    result: str,
    reason: str | None = None,
) -> dict:
    """Meta compacta y sin PII cruda para eventos de validación de pre-registro."""
    return {
        "action": "pre_register_validate",
        "document_type_id": document_type_id,
        "document_number_masked": mask_doc(document_number),
        "date_issuance_document": str(date_issuance_document),
        "result": result,   # "allowed" | "denied" | "error"
        "reason": reason,
    }