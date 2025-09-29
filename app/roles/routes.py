from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.roles import schemas, services
from app.roles.models import ChangeRoleStatusRequest
from app.auth.services import AuthService

router = APIRouter(tags=["Roles"])

def check_permission(current_user: dict, required_permission_id: int):
    """
    Verifica si el usuario tiene el permiso (por ID).
    """
    user_roles = current_user.get("rol", [])
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
    # Verificar permiso o si es administrador (roles.view -> ID 13)
    if not check_permission(current_user, 13):
        raise HTTPException(status_code=403, detail="No tiene permisos para ver roles")
    
    role_service = services.RoleService(db)
    return role_service.get_roles()

@router.get("/{role_id}")
def detail_rol(
    role_id: int, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    # Verificar permiso o si es administrador (roles.detail -> ID 17)
    if not check_permission(current_user, 17):
        raise HTTPException(status_code=403, detail="No tiene permisos para ver detalles de roles")
    
    role_service = services.RoleService(db)
    return role_service.get_rol(role_id)

@router.get("/permissions/", response_model=list[schemas.PermissionResponse])
def list_permissions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    # Verificar permiso o si es administrador (permissions.view -> ID 20)
    if not check_permission(current_user, 20):
        raise HTTPException(status_code=403, detail="No tiene permisos para ver permisos")
    
    permission_service = services.PermissionService(db)
    return permission_service.get_permissions()
    # return services.get_permissions(db)

@router.post("/", response_model=schemas.RoleResponse)
def create_role(
    role: schemas.RoleCreate,
    request: Request, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user),  
):
    permission_id = 14
    # Verificar permiso o si es administrador (roles.create -> ID 14)
    if not check_permission(current_user, permission_id):
        raise HTTPException(status_code=403, detail="No tiene permisos para crear roles")
    
    role_service = services.RoleService(db)
    return role_service.create_role(role, request, current_user, permission_id=permission_id)

@router.post("/{role_id}/edit", response_model=schemas.EditRoleResponse)
def edit_rol(
    role_id: int,
    role: schemas.RoleCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user),
):
    permission_id = 15
    # Verificar permiso o si es administrador (roles.edit -> ID 15)
    if not check_permission(current_user, permission_id):
        raise HTTPException(status_code=403, detail="No tiene permisos para editar roles")

    role_service = services.RoleService(db)
    return role_service.edit_role(role_id, role, request, current_user, permission_id=permission_id)

@router.delete("/{role_id}/delete", response_model=schemas.GenericResponse)
def delete_rol(
    role_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user),
):
    permission_id = 16
    # Verificar permiso o si es administrador (roles.delete -> ID 16)
    if not check_permission(current_user, permission_id):
        raise HTTPException(status_code=403, detail="No tiene permisos para eliminar roles")

    role_service = services.RoleService(db)
    return role_service.delete_role(role_id, request, current_user, permission_id=permission_id)


@router.post("/change-rol-status/")
def change_role_status(
    payload: schemas.ChangeRoleStatusRequest,
    request: Request,                           # auditoría
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user),
):
    """Cambiar el estado de un rol y registrar auditoría."""
    permission_id = 18
    # Verificar permiso o si es administrador (roles.status_change -> ID 18)
    if not check_permission(current_user, permission_id):
        raise HTTPException(status_code=403, detail="No tiene permisos para cambiar estado de roles")

    try:
        role_service = services.RoleService(db)
        return role_service.change_role_status(payload.rol_id, payload.new_status, request, current_user, permission_id=permission_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar el cambio de estado del rol: {str(e)}"
        )


@router.get("/user/{user_id}/roles", tags=["Usuarios"])
def get_user_roles(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    """Obtener la información de un usuario y sus roles asignados"""
    # Verificar permiso o si es administrador (user_roles.view -> ID 6)
    if not check_permission(current_user, 6):
        raise HTTPException(status_code=403, detail="No tiene permisos para ver roles de usuarios")
    
    user_role_service = services.UserRoleService(db)
    return user_role_service.get_user_with_roles(user_id)

@router.post("/permissions/", response_model=schemas.SimpleResponse)
def create_permission(
    permission: schemas.PermissionBase,
    request: Request,                            
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user),  
):
    permission_id = 21
    if not check_permission(current_user, permission_id):
        raise HTTPException(status_code=403, detail="No tiene permisos para crear permisos")

    permission_service = services.PermissionService(db)
    return permission_service.create_permission(permission, request, current_user, permission_id=permission_id)


@router.put("/{role_id}/permissions", tags=["Roles"])
def update_permissions(
    role_id: int,
    body: schemas.UpdateRolePermissions,   
    request: Request,                   
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user),  # <-- viene del HEAD
):
    permission_id = 19
    """Actualizar los permisos de un rol."""
    # Verificar permiso o si es administrador (roles.permissions_update -> ID 19)
    if not check_permission(current_user, permission_id):
        raise HTTPException(status_code=403, detail="No tiene permisos para actualizar permisos de roles")

    role_service = services.RoleService(db)
    return role_service.update_role_permissions(role_id, body.permissions, request, current_user, permission_id=permission_id)

@router.post("/assign_role/")
def assign_role(
    body: schemas.AssignRoleRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user),
):
    permission_id = 7
    # Verificar permiso o si es administrador (user_roles.manage -> ID 7)
    if not check_permission(current_user, permission_id):
        raise HTTPException(status_code=403, detail="No tiene permisos para gestionar roles de usuarios")

    user_role_service = services.UserRoleService(db)
    return user_role_service.assign_role_to_user(
        body.user_id,
        body.role_id,
        request,
        current_user,
        permission_id=permission_id
    )


@router.put("/user/{user_id}/roles", tags=["Usuarios"])
def update_user_roles(
    user_id: int,
    body: schemas.UpdateUserRoles,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user),  
):
    """Actualizar los roles de un usuario, asegurando que tenga al menos 1"""
    permission_id = 7
    # Verificar permiso o si es administrador (user_roles.manage -> ID 7)
    if not check_permission(current_user, permission_id):
        raise HTTPException(status_code=403, detail="No tiene permisos para gestionar roles de usuarios")

    user_role_service = services.UserRoleService(db)
    return user_role_service.update_user_roles(user_id, body.roles, request, current_user, permission_id=permission_id)

@router.delete("/user/{user_id}/role/{role_id}", tags=["Usuarios"])
def revoke_role(
    user_id: int,
    role_id: int,
    request: Request,                         
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user),  
):
    permission_id = 7
    """Revocar un rol de un usuario, asegurando que tenga al menos 1 rol"""
    # Verificar permiso o si es administrador
    if not check_permission(current_user, permission_id):
        raise HTTPException(status_code=403, detail="No tiene permisos para gestionar roles de usuarios")

    user_role_service = services.UserRoleService(db)
    return user_role_service.revoke_role_from_user(user_id, role_id, request, current_user, permission_id=permission_id)



