from typing import Any, Dict

def role_snapshot(role_obj) -> Dict[str, Any]:
    return {
        "id": role_obj.id,
        "name": role_obj.name,
        "description": role_obj.description,
        "status": role_obj.status,
        "permissions": sorted([p.id for p in getattr(role_obj, "permissions", [])]),
    }

def user_roles_snapshot(user_obj) -> dict:
    roles = getattr(user_obj, "roles", []) or []
    return {
        "user_id": getattr(user_obj, "id", None),
        "roles": sorted([getattr(r, "id", None) for r in roles if getattr(r, "id", None) is not None]),
    }

def permission_snapshot(perm_obj) -> dict:
    return {
        "id": perm_obj.id,
        "name": perm_obj.name,
        "description": perm_obj.description,
        "category": perm_obj.category,
    }