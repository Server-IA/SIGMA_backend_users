from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.database import get_db
from app.roles import schemas, services
from app.roles.models import ChangeRoleStatusRequest
from app.auth.services import AuthService

router = APIRouter(tags=["Roles"])

def check_permission_or_admin(current_user: dict, required_permission_id: int):
    """
    Verifica si el usuario tiene el permiso (por ID) o es administrador (rol ID: 1)
    """
    # Verificar si es administrador
    user_roles = current_user.get("rol", [])
    for role in user_roles:
        if role.get("id") == 1:  # Rol Administrador
            return True

    # Verificar permisos específicos por ID
    permisos_usuario = [
        perm.get("id")
        for rol in user_roles
        for perm in rol.get("permisos", [])
    ]

    return required_permission_id in permisos_usuario

@router.get("/")
def list_roles(
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    # Verificar permiso o si es administrador (roles.view -> ID 6)
    if not check_permission_or_admin(current_user, 6):
        raise HTTPException(status_code=403, detail="No tiene permisos para ver roles")
    
    role_service = services.RoleService(db)
    return role_service.get_roles()

@router.get("/{role_id}")
def detail_rol(
    role_id: int, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    # Verificar permiso o si es administrador (roles.detail -> ID 57)
    if not check_permission_or_admin(current_user, 57):
        raise HTTPException(status_code=403, detail="No tiene permisos para ver detalles de roles")
    
    role_service = services.RoleService(db)
    return role_service.get_rol(role_id)

@router.get("/permissions/", response_model=list[schemas.PermissionResponse])
def list_permissions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    # Verificar permiso o si es administrador (permissions.view -> ID 58)
    if not check_permission_or_admin(current_user, 58):
        raise HTTPException(status_code=403, detail="No tiene permisos para ver permisos")
    
    permission_service = services.PermissionService(db)
    return permission_service.get_permissions()
    # return services.get_permissions(db)

@router.post("/", response_model=schemas.RoleResponse)
def create_role(
    role: schemas.RoleCreate, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    # Verificar permiso o si es administrador (roles.create -> ID 7)
    if not check_permission_or_admin(current_user, 7):
        raise HTTPException(status_code=403, detail="No tiene permisos para crear roles")
    
    role_service = services.RoleService(db)
    return role_service.create_role(role)
    # return services.create_role(db, role)

@router.post("/{role_id}/edit", response_model=schemas.EditRoleResponse)
def edit_rol(
    role_id: int, 
    role: schemas.RoleCreate, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    # Verificar permiso o si es administrador (roles.edit -> ID 8)
    if not check_permission_or_admin(current_user, 8):
        raise HTTPException(status_code=403, detail="No tiene permisos para editar roles")
    
    role_service = services.RoleService(db)
    return role_service.edit_role(role_id, role)

@router.delete("/{role_id}/delete", response_model=schemas.GenericResponse)
def delete_rol(
    role_id: int, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    # Verificar permiso o si es administrador (roles.delete -> ID 9)
    if not check_permission_or_admin(current_user, 9):
        raise HTTPException(status_code=403, detail="No tiene permisos para eliminar roles")
    
    role_service = services.RoleService(db)
    return role_service.delete_role(role_id)

@router.post("/change-rol-status/")
def change_role_status(
    request: ChangeRoleStatusRequest, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    """Cambiar el estado de un rol"""
    # Verificar permiso o si es administrador (roles.status_change -> ID 60)
    if not check_permission_or_admin(current_user, 60):
        raise HTTPException(status_code=403, detail="No tiene permisos para cambiar estado de roles")
    
    try:
        user_service = services.RoleService(db)
        return user_service.change_role_status(request.rol_id, request.new_status)
    except HTTPException as e:
        raise e  # Re-raise HTTPException for known errors
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar el cambio de estado del rol: {str(e)}")


@router.get("/user/{user_id}/roles", tags=["Usuarios"])
def get_user_roles(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    """Obtener la información de un usuario y sus roles asignados"""
    # Verificar permiso o si es administrador (user_roles.view -> ID 61)
    if not check_permission_or_admin(current_user, 61):
        raise HTTPException(status_code=403, detail="No tiene permisos para ver roles de usuarios")
    
    user_role_service = services.UserRoleService(db)
    return user_role_service.get_user_with_roles(user_id)

@router.post("/permissions/", response_model=schemas.SimpleResponse)
def create_permission(
    permission: schemas.PermissionBase, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    # Verificar permiso o si es administrador (permissions.create -> ID 59)
    if not check_permission_or_admin(current_user, 59):
        raise HTTPException(status_code=403, detail="No tiene permisos para crear permisos")
    
    permission_service = services.PermissionService(db)
    return permission_service.create_permission(permission)
    # return services.create_permission(db, permission)



@router.put("/{role_id}/permissions", tags=["Roles"])
def update_permissions(
    role_id: int,
    request: schemas.UpdateRolePermissions,
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    """Actualizar los permisos de un rol."""
    # Verificar permiso o si es administrador (roles.permissions_update -> ID 63)
    if not check_permission_or_admin(current_user, 63):
        raise HTTPException(status_code=403, detail="No tiene permisos para actualizar permisos de roles")
    
    role_service = services.RoleService(db)
    return role_service.update_role_permissions(role_id, request.permissions)
    # return services.update_role_permissions(db, role_id, request.permissions)

@router.post("/assign_role/")
def assign_role(
    request: schemas.AssignRoleRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    # Verificar permiso o si es administrador (user_roles.manage -> ID 62)
    if not check_permission_or_admin(current_user, 62):
        raise HTTPException(status_code=403, detail="No tiene permisos para gestionar roles de usuarios")
    
    user_role_service = services.UserRoleService(db)
    return user_role_service.assign_role_to_user(request.user_id, request.role_id)
    # user = services.assign_role_to_user(db, request.user_id, request.role_id)



@router.put("/user/{user_id}/roles", tags=["Usuarios"])
def update_user_roles(
    user_id: int, 
    request: schemas.UpdateUserRoles, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    """Actualizar los roles de un usuario, asegurando que tenga al menos 1"""
    # Verificar permiso o si es administrador (user_roles.manage -> ID 62)
    if not check_permission_or_admin(current_user, 62):
        raise HTTPException(status_code=403, detail="No tiene permisos para gestionar roles de usuarios")
    
    user_role_service = services.UserRoleService(db)
    return user_role_service.update_user_roles(user_id, request.roles)

@router.delete("/user/{user_id}/role/{role_id}", tags=["Usuarios"])
def revoke_role(
    user_id: int, 
    role_id: int, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    """Revocar un rol de un usuario, asegurando que tenga al menos 1 rol"""
    # Verificar permiso o si es administrador
    if not check_permission_or_admin(current_user, "user_roles.manage"):
        raise HTTPException(status_code=403, detail="No tiene permisos para gestionar roles de usuarios")
    
    user_role_service = services.UserRoleService(db)
    return user_role_service.revoke_role_from_user(user_id, role_id)



