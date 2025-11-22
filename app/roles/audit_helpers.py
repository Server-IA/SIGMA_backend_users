from typing import Any, Dict, List

def role_snapshot(role_obj) -> Dict[str, Any]:
    """
    Snapshot mínimo para diffs:
    - Evita campos grandes (descriptions largas)
    - Ordena permisos para estabilidad del diff
    """
    perms: List[int] = []
    perms_attr = getattr(role_obj, "permissions", None)
    if perms_attr:
        # Permite tanto lista como related manager/queryset
        try:
            perms = [int(getattr(p, "id", p)) for p in perms_attr]
        except TypeError:
            # related manager (Django) -> iterar
            perms = [int(getattr(p, "id", p)) for p in perms_attr.all()]
    return {
        "id": getattr(role_obj, "id", None),
        "name": getattr(role_obj, "name", None),
        "description": getattr(role_obj, "description", None),  # ← AÑADIDO
        "status": getattr(role_obj, "status", None),
        "permissions": sorted([p for p in perms if p is not None]),
    }

def user_roles_snapshot(user_obj) -> Dict[str, Any]:
    roles = getattr(user_obj, "roles", None)
    ids: List[int] = []
    if roles:
        try:
            ids = [int(getattr(r, "id", r)) for r in roles]
        except TypeError:
            ids = [int(getattr(r, "id", r)) for r in roles.all()]
    return {
        "user_id": getattr(user_obj, "id", None),
        "roles": sorted([i for i in ids if i is not None]),
    }

def permission_snapshot(perm_obj) -> Dict[str, Any]:
    """
    Manténlo mínimo; si ‘category’ no es requerida para auditoría, omítela.
    """
    return {
        "id": getattr(perm_obj, "id", None),
        "name": getattr(perm_obj, "name", None),
        "category": getattr(perm_obj, "category", None),  
    }

