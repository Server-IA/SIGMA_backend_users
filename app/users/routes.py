from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form , BackgroundTasks
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session, joinedload
from typing import Optional, List
from datetime import datetime
from app.roles.models import Role
from app.database import get_db
from app.users import schemas
from app.users.models import ChangeUserStatusRequest, Notification
from app.users.schemas import (
    AdminUserCreateRequest,
    AdminUserCreateResponse,
    AdminUserUpdateRequest,
    ActivateAccountResponse,
    PreRegisterCompleteRequest,
    PreRegisterResponse,
    PreRegisterValidationRequest,
    UpdateUserRequest,
    UserResponse,
    UserCreateRequest,
    ChangePasswordRequest,
    UserUpdateInfo,
    FirstLoginProfileUpdate,
    UserEditRequest,
    NotificationList,
    NotificationCreate,
    MarkReadRequest
)
from app.users.services import UserService
from app.auth.services import AuthService

router = APIRouter(prefix="/users", tags=["Users"])

############################################
# Endpoints para pre-registro y activación #
############################################

@router.post("/pre-register/validate", response_model=PreRegisterResponse)
async def validate_document_for_pre_register(
    request: PreRegisterValidationRequest,
    db: Session = Depends(get_db)
):
    """
    Valida que el documento exista y esté asociado a un usuario que aún no ha completado el pre-registro.
    """
    try:
        user_service = UserService(db)
        return await user_service.validate_for_pre_register(
            document_type_id=request.document_type_id,
            document_number=request.document_number,
            date_issuance_document=request.date_issuance_document
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la validación: {str(e)}")

@router.post("/pre-register/complete", response_model=PreRegisterResponse)
async def complete_pre_register(
    request: PreRegisterCompleteRequest,
    db: Session = Depends(get_db)
):
    """
    Completa el pre-registro del usuario añadiendo email y contraseña, y envía un correo con enlace de activación.
    """
    try:
        user_service = UserService(db)
        return await user_service.complete_pre_register(
            token=request.token,
            email=request.email,
            password=request.password
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al completar el pre-registro: {str(e)}")

@router.get("/activate-account/{activation_token}", response_model=ActivateAccountResponse)
async def activate_account(
    activation_token: str,
    db: Session = Depends(get_db)
):
    """
    Activa la cuenta del usuario a través del enlace enviado por email.
    """
    try:
        user_service = UserService(db)
        return await user_service.activate_account(activation_token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al activar la cuenta: {str(e)}")

####################################
# Endpoints para usuarios normales #
####################################

@router.post("/first-login-register", response_model=dict)
async def register_after_first_login(
    user_id: int = Form(...),
    country: str = Form(...),
    department: str = Form(...),
    city: int = Form(...),
    address: str = Form(...),
    phone: str = Form(...),
    profile_picture: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Completa el registro del usuario después del primer inicio de sesión.
    Actualiza los datos básicos: país, departamento, ciudad, dirección, teléfono y, opcionalmente, la foto de perfil.
    """
    try:
        user_service = UserService(db)
        profile_picture_path = None
        if profile_picture:
            profile_picture_path = await user_service.save_profile_picture(profile_picture)
        return await user_service.complete_first_login_registration(
            user_id=user_id,
            country=country,
            department=department,
            city=city,
            address=address,
            phone=phone,
            profile_picture=profile_picture_path
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al completar el registro del usuario: {str(e)}")

@router.get("/profile/completion-status/{user_id}")
def check_profile_completion(user_id: int, db: Session = Depends(get_db)):
    """
    Verifica si el usuario ya ha completado su perfil después del primer login.
    """
    try:
        user_service = UserService(db)
        return user_service.check_profile_completion(user_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al verificar el estado del perfil: {str(e)}")

@router.put("/edit-profile/{user_id}", response_model=dict)
async def edit_profile(
    user_id: int,
    update_data: UserEditRequest,  
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    """
    Permite a un usuario normal editar su perfil básico: país, departamento, ciudad, dirección y teléfono.
    """
    if current_user.get("id") != user_id:
        raise HTTPException(status_code=403, detail="No tiene permisos para editar este usuario")
    try:
        user_service = UserService(db)
        return await user_service.update_basic_profile(
            user_id=user_id,
            country=update_data.country,
            department=update_data.department,
            city=update_data.city,
            address=update_data.address,
            phone=update_data.phone,
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar el perfil: {str(e)}")

@router.put("/update-photo/{user_id}", response_model=dict)
async def update_photo(
    user_id: int,
    profile_picture: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    """
    Permite a un usuario normal actualizar su foto de perfil.
    """
    if current_user.get("id") != user_id:
        raise HTTPException(status_code=403, detail="No tiene permisos para editar este usuario")
    try:
        user_service = UserService(db)
        photo_path = await user_service.save_profile_picture(profile_picture)
        return user_service.update_user(user_id, profile_picture=photo_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar la foto: {str(e)}")

###############################
# Endpoints para administradores #
###############################

@router.post("/admin/create", response_model=AdminUserCreateResponse, status_code=status.HTTP_201_CREATED)
def create_user_by_admin(
    user_data: AdminUserCreateRequest, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    """
    Crea un nuevo usuario en el sistema (vía Admin).
    Campos requeridos:
      - name, first_last_name, second_last_name,
      - type_document_id, document_number, date_issuance_document,
      - birthday, gender_id, roles.
    """
    if not current_user.get("rol") or "Administrador" not in [r.get("name") for r in current_user.get("rol", [])]:
        raise HTTPException(status_code=403, detail="No tiene permisos para crear usuarios")
    try:
        user_service = UserService(db)
        return user_service.create_user_by_admin(
            name=user_data.name,
            first_last_name=user_data.first_last_name,
            second_last_name=user_data.second_last_name,
            type_document_id=user_data.type_document_id,
            document_number=user_data.document_number,
            date_issuance_document=user_data.date_issuance_document,
            birthday=user_data.birthday,
            gender_id=user_data.gender_id,
            roles=user_data.roles,
            admin_id=current_user["id"]  
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear el usuario: {str(e)}")


@router.put("/admin/edit/{user_id}", summary="Editar información completa del usuario (Admin)")
def admin_edit_user(
    user_id: int,
    update_data: AdminUserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    """
    Permite a un administrador editar la información completa de un usuario.
    Campos actualizables:
      - name, first_last_name, second_last_name,
      - type_document_id, document_number, date_issuance_document,
      - birthday, gender_id y roles.
    """
    if not current_user.get("rol") or "Administrador" not in [r.get("name") for r in current_user.get("rol", [])]:
        raise HTTPException(status_code=403, detail="No tiene permisos para editar este usuario")
    try:
        user_service = UserService(db)
        
        update_fields = {
            "name": update_data.name,
            "first_last_name": update_data.first_last_name,
            "second_last_name": update_data.second_last_name,
            "type_document_id": update_data.type_document_id,
            "document_number": update_data.document_number,
            "date_issuance_document": update_data.date_issuance_document,
            "birthday": update_data.birthday,
            "gender_id": update_data.gender_id,    
        }
        if update_data.roles:
            roles_obj = db.query(Role).filter(Role.id.in_(update_data.roles)).all()
            update_fields["roles"] = roles_obj

        # Se pasa admin_update=True para generar la notificación correspondiente
        result = user_service.update_user(user_id, admin_update=True, **update_fields)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar el usuario: {str(e)}")


@router.get("/type-documents", tags=["Users"])
def get_document_types(db: Session = Depends(get_db)):
    """
    Obtiene todos los tipos de documentos disponibles.
    """
    try:
        user_service = UserService(db)
        return user_service.get_type_documents()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener los tipos de documentos: {str(e)}")

@router.get("/genders" , tags=["Users"])
def get_genders(db: Session = Depends(get_db)):
    """
    Obtiene todos los géneros disponibles.
    """
    try:
        user_service = UserService(db)
        return user_service.get_genders()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener los géneros: {str(e)}")

@router.post("/change-user-status/")
def change_user_status(
    request: ChangeUserStatusRequest,
    db: Session = Depends(get_db)
):
    """
    Cambia el estado de un usuario.
    """
    try:
        user_service = UserService(db)
        return user_service.change_user_status(request.user_id, request.new_status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al cambiar el estado del usuario: {str(e)}")

@router.post("/{user_id}/change-password", response_model=dict)
def change_password(
    user_id: int,
    request: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    """
    Actualiza la contraseña del usuario verificando la contraseña actual
    y genera una notificación de seguridad.
    Sólo el propio usuario puede cambiar su contraseña.
    """
    
    if current_user["id"] != user_id:
        raise HTTPException(status_code=403, detail="No tienes permiso para cambiar esta contraseña")

    
    service = UserService(db)
    return service.change_user_password(user_id, request)

@router.get("/{user_id}")
def list_user(user_id: int, db: Session = Depends(get_db)):
    """
    Obtiene información detallada de un usuario.
    """
    try:
        user_service = UserService(db)
        return user_service.list_user(user_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener el usuario: {str(e)}")

@router.get("/")
def list_users(db: Session = Depends(get_db)):
    """
    Lista todos los usuarios.
    """
    try:
        user_service = UserService(db)
        return user_service.list_users()
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar los usuarios: {str(e)}")


@router.get("/notifications/", response_model=schemas.NotificationList)
def get_user_notifications(
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    """
    Get all notifications for the currently logged in user
    """
    user_service = UserService(db)
    return user_service.get_user_notifications(current_user["id"])

@router.post("/notifications/mark-read", response_model=dict)
def mark_notifications_as_read(
    request: schemas.MarkReadRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    """
    Mark notifications as read.
    If mark_all is true, all notifications will be marked as read.
    Otherwise, only the notifications with IDs in notification_ids will be marked.
    """
    user_service = UserService(db)
    return user_service.mark_notifications_as_read(
        user_id=current_user["id"],
        notification_ids=request.notification_ids,
        mark_all=request.mark_all
    )

@router.post("/notifications/", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_notification(
    notification: schemas.NotificationCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    """
    Create a new notification (admin only)
    """
    # Check if the user has admin permissions
    has_admin_role = False
    for role in current_user.get("rol", []):
        if role.get("name") == "Administrador":
            has_admin_role = True
            break
    
    if not has_admin_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"success": False, "data": "No tiene permisos para crear notificaciones"}
        )
    
    user_service = UserService(db)
    return user_service.create_notification(notification)

@router.get("/notifications/unread-count", response_model=dict)
def get_unread_notification_count(
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    """
    Get count of unread notifications for the current user
    """
    user_service = UserService(db)
    return user_service.get_unread_notification_count(current_user["id"])