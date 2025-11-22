from typing import Optional, Tuple, List, Dict, Any

def mask_email(email: str | None) -> str | None:
    if not email or "@" not in (email or ""):
        return email
    local, domain = email.split("@", 1)
    safe = (local[:2] + "***@" + domain) if local else "***@" + domain
    return safe

def mask_doc(doc: str | None) -> str | None:
    """Enmascara documento dejando últimos 3 dígitos."""
    if not doc:
        return doc
    d = str(doc)
    if len(d) <= 3:
        return "***"
    return "*" * (len(d) - 3) + d[-3:]

# snapshots
def user_snapshot(user_obj) -> Dict[str, Any]:
    """
    Snapshot compacto para auditoría general de usuario.
    Incluye solo campos necesarios para los diffs.
    Evita textos grandes o binarios (foto).
    """
    roles_attr = getattr(user_obj, "roles", None) or []
    # Soporta lista o related manager/queryset
    try:
        role_ids = [int(getattr(r, "id", r)) for r in roles_attr]
    except TypeError:
        role_ids = [int(getattr(r, "id", r)) for r in roles_attr.all()]

    return {
        "id": getattr(user_obj, "id", None),
        "email": mask_email(getattr(user_obj, "email", None)),
        "name": getattr(user_obj, "name", None),
        "first_last_name": getattr(user_obj, "first_last_name", None),
        "second_last_name": getattr(user_obj, "second_last_name", None),
        "gender_id": getattr(user_obj, "gender_id", None),
        "status_id": getattr(user_obj, "status_id", None),
        "roles": sorted([rid for rid in role_ids if rid is not None]),
    }

def snapshot_basic_profile(user_obj) -> Dict[str, Any]:
    """
    Snapshot reducido para cambios de perfil básico.
    Evita incluir `profile_picture` si es un binario/URL largo.
    """
    return {
        "country": getattr(user_obj, "country", None),
        "department": getattr(user_obj, "department", None),
        "city": getattr(user_obj, "city", None),
        "address": getattr(user_obj, "address", None),
        "phone": getattr(user_obj, "phone", None),
    }

def prereg_attempt_meta(
    *,
    document_type_id: int,
    document_number: str,
    date_issuance_document,
    result: str,
    reason: str | None = None,
    **extras: Any,
) -> Dict[str, Any]:
    """
    Meta compacta y sin PII cruda para eventos de validación de pre-registro.
    """
    meta = {
        "action": "pre_register_validate",
        "document_type_id": document_type_id,
        "document_number_masked": mask_doc(document_number),
        "date_issuance_document": str(date_issuance_document),
        "result": result,
        "reason": reason,
    }
    meta.update(extras)
    return meta

def pick_primary_role_and_ids(user_obj) -> Tuple[Optional[str], List[int]]:
    """
    Devuelve (actor_role_principal, lista_ids_roles) usando ORM.
    Elige 'Administrador' si existe; si no, el primero.
    """
    roles = getattr(user_obj, "roles", None) or []
    if not roles:
        return None, []
    try:
        roles_iter = list(roles) 
    except TypeError:
        roles_iter = list(roles.all())  
    admin = next(
        (r for r in roles_iter if (getattr(r, "name", "") or "").strip().lower() == "administrador"),
        None
    )
    primary = getattr(admin, "name", None) if admin else getattr(roles_iter[0], "name", None)
    ids = [getattr(r, "id", None) for r in roles_iter if getattr(r, "id", None) is not None]
    return primary, ids

def pick_primary_role_and_ids_from_current_user(current_user: Dict[str, Any]) -> Tuple[Optional[str], List[int]]:
    """
    Devuelve (actor_role_principal, lista_ids_roles) usando payload del JWT.
    """
    roles = current_user.get("rol", []) or []
    if not roles:
        return None, []
    admin = next((r for r in roles if (r.get("name") or "").strip().lower() == "administrador"), None)
    primary = (admin.get("name") if admin else roles[0].get("name")) if roles else None
    ids = [int(r["id"]) for r in roles if "id" in r]
    return primary, ids