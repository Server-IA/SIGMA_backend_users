from typing import Optional, Tuple, List, Dict, Any
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

# ORM (login)
def pick_primary_role_and_ids(user_obj) -> Tuple[Optional[str], List[int]]:
    """
    Devuelve (actor_role_principal, lista_ids_roles) usando ORM.

    Reglas:
      1) Si tiene "Administrador" (case-insensitive), ese es el principal.
      2) Si no, el primero de la lista.
      3) Si no tiene roles, principal=None y lista vacía.
    """
    roles = getattr(user_obj, "roles", None) or []
    if not roles:
        return None, []

    # Buscar admin normalizado
    admin = next(
        (r for r in roles if (getattr(r, "name", "") or "").strip().lower() == "administrador"),
        None
    )
    primary = getattr(admin, "name", None) if admin else getattr(roles[0], "name", None)
    ids = [getattr(r, "id", None) for r in roles if getattr(r, "id", None) is not None]

    return primary, ids

# TOKEN (Internal endpoints)
def pick_primary_role_and_ids_from_current_user(current_user: Dict[str, Any]) -> Tuple[Optional[str], List[int]]:
    """
    Devuelve (actor_role_principal, lista_ids_roles) usando payload del JWT.

    current_user: dict con al menos la clave "rol" (lista de roles).

    Reglas:
      1) Si tiene un rol "Administrador" → ese es el principal.
      2) Si no, el primero de la lista.
      3) Si no tiene roles, principal=None y lista vacía.
    """
    roles = current_user.get("rol", []) or []
    if not roles:
        return None, []

    admin = next(
        (r for r in roles if (r.get("name") or "").strip().lower() == "administrador"),
        None
    )
    primary = admin.get("name") if admin else roles[0].get("name")
    ids = [r["id"] for r in roles if "id" in r]

    return primary, ids