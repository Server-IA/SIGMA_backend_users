from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form , BackgroundTasks, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session, joinedload
from typing import Optional, List
from datetime import datetime
from app.roles.models import Role
from app.database import get_db
from app.users import schemas
from app.users.models import ChangeUserStatusRequest, Notification, User
from app.roles.models import role_permission_table, user_role_table    
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
    MarkReadRequest,
    TechnicianNotificationRequest,
    TechnicianNotificationResponse,
    UserUpdateRequest
)
from app.users.services import UserService
from app.auth.services import AuthService

router = APIRouter(tags=["Users"])

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

############################################
# Endpoints para pre-registro y activación #
############################################

@router.post("/pre-register/validate", response_model=PreRegisterResponse)
async def validate_document_for_pre_register(
    body: PreRegisterValidationRequest,
    db: Session = Depends(get_db)
):
    """
    Valida que el documento exista y esté asociado a un usuario que aún no ha completado el pre-registro.
    """
    try:
        user_service = UserService(db)
        return await user_service.validate_for_pre_register(
            document_type_id=body.document_type_id,
            document_number=body.document_number,
            date_issuance_document=body.date_issuance_document
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la validación: {str(e)}")

@router.post("/pre-register/complete", response_model=PreRegisterResponse)
async def complete_pre_register(
    body: PreRegisterCompleteRequest,
    db: Session = Depends(get_db)
):
    """
    Completa el pre-registro del usuario añadiendo email y contraseña, y envía un correo con enlace de activación.
    """
    try:
        user_service = UserService(db)
        return await user_service.complete_pre_register(
            token=body.token,
            email=body.email,
            password=body.password
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
    request: Request,
    db: Session = Depends(get_db),

):
    """
    Activa la cuenta del usuario a través del enlace enviado por email.
    """
    try:
        user_service = UserService(db)
        return await user_service.activate_account(activation_token, request=request)
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
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    permission_id = 8
    """
    Permite a un usuario normal editar su perfil básico: país, departamento, ciudad, dirección y teléfono.
    """
    # Verificar permiso o si es administrador (users.profile.edit -> ID 8)
    if not check_permission(current_user, permission_id):
        raise HTTPException(status_code=403, detail="No tiene permisos para editar perfiles de usuario")
    
    # Si no es admin, solo puede editar su propio perfil
    if not any(role.get("id") == 1 for role in current_user.get("rol", [])):
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
            request=request,
            current_user=current_user,
            permission_id=permission_id
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
    # Verificar permiso o si es administrador (users.photo.update -> ID 9)
    if not check_permission(current_user, 9):
        raise HTTPException(status_code=403, detail="No tiene permisos para actualizar fotos de usuario")
    
    # Si no es admin, solo puede actualizar su propia foto
    if not any(role.get("id") == 1 for role in current_user.get("rol", [])):
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
    user_data: AdminUserCreateRequest, request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    permission_id = 3
    """
    Crea un nuevo usuario en el sistema (vía Admin).
    Campos requeridos:
      - name, first_last_name, second_last_name,
      - type_document_id, document_number, date_issuance_document,
      - birthday, gender_id, roles.
    """
    # Verificar permiso o si es administrador (users.create -> ID 3)
    if not check_permission(current_user, permission_id):
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
            admin_id=current_user["id"],
            request=request,
            current_user=current_user,
            permission_id=permission_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear el usuario: {str(e)}")


@router.put("/admin/edit/{user_id}", summary="Editar información completa del usuario (Admin)")
def admin_edit_user(
    user_id: int,
    update_data: AdminUserUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    permission_id = 4
    """
    Permite a un administrador editar la información completa de un usuario.
    Campos actualizables:
        - name, first_last_name, second_last_name,
        - type_document_id, document_number, date_issuance_document,
        - birthday, gender_id y roles.
    """
    # Verificar permiso o si es administrador (users.edit -> ID 4)
    if not check_permission(current_user, permission_id):
        raise HTTPException(status_code=403, detail="No tiene permisos para editar usuarios")
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
        result = user_service.update_user(user_id, admin_update=True, request=request, admin_id=current_user["id"], **update_fields, current_user=current_user, permission_id=permission_id)
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
    body: ChangeUserStatusRequest,         
    request: Request,                     
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user),
):
    permission_id = 10
    """
    Cambia el estado de un usuario.
    """
    # Verificar permiso o si es administrador (users.status.change -> ID 10)
    if not check_permission(current_user, permission_id):
        raise HTTPException(status_code=403, detail="No tiene permisos para cambiar estado de usuarios")

    try:
        user_service = UserService(db)
        return user_service.change_user_status(body.user_id, body.new_status, request, current_user=current_user, permission_id=permission_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al cambiar el estado del usuario: {str(e)}")

@router.post("/{user_id}/change-password", response_model=dict)
def change_password(
    user_id: int,
    body: ChangePasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user),
):
    permission_id = 11
    """
    Actualiza la contraseña del usuario verificando la contraseña actual
    y genera una notificación de seguridad.
    Solo el propio usuario o un admin pueden cambiar la contraseña.
    """
    # 1) Permiso por ID (users.password.change -> 11)
    if not check_permission(current_user, permission_id):
        raise HTTPException(status_code=403, detail="No tiene permisos para cambiar contraseñas de usuario")

    # 2) Si NO es admin, solo puede cambiar su propia contraseña
    es_admin = any(role.get("id") == 1 for role in current_user.get("rol", []))
    if not es_admin and current_user["id"] != user_id:
        raise HTTPException(status_code=403, detail="No tienes permiso para cambiar esta contraseña")

    # 3) Ejecutar servicio
    service = UserService(db)
    return service.change_user_password(
        user_id=user_id,
        password_data=body,     # ← pasamos el schema completo
        request=request,
        current_user=current_user,
        permission_id=permission_id
    )


@router.put("/{user_id}/profile", response_model=dict)
async def update_user_profile(
    user_id: int,
    user_data: UserUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    """
    Actualiza la información del perfil de un usuario.
    
    Permite actualizar:
    - Tipo de documento
    - Número de documento (validando que no esté en uso)
    - Nombres
    - Apellidos
    - Correo electrónico (validando que no esté en uso)
    - Teléfono
    - Dirección
    
    Requiere autenticación. Puede ser usado por servicios externos para actualizar perfiles.
    """
    try:
        user_service = UserService(db)
        
        # Convertir el modelo Pydantic a dict y eliminar campos None
        update_data = user_data.dict(exclude_unset=True)
        
        # Actualizar el perfil
        result = await user_service.update_user_profile(
            user_id=user_id,
            update_data=update_data,
            current_user=current_user
        )
        
        return result
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar el perfil: {str(e)}"
        )

@router.post("/basic-user-list/by-ids")
def list_users_basic_by_ids(
    body: schemas.BasicUserIdsRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    """
    Lista básica de usuarios filtrando por una lista de IDs.
    Devuelve: id, name, first_last_name, second_last_name, document_number,
    type_document (ID), type_document_name (nombre) y email.
    """
    try:
        user_service = UserService(db)
        return user_service.list_users_basic_by_ids(body.ids)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar usuarios por IDs: {str(e)}")

@router.get("/by-document/{document_number}", response_model=dict)
async def get_user_by_document_number(
    document_number: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    """
    Obtiene la información básica de un usuario por su número de documento.
    
    Requiere autenticación pero no permisos específicos.
    Devuelve: id, name, first_last_name, second_last_name, document_number,
    type_document (ID), type_document_name (nombre), email y phone.
    """
    try:
        user_service = UserService(db)
        return user_service.get_user_by_document_number(document_number)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al buscar el usuario por documento: {str(e)}")

@router.get("/{user_id}")
def list_user(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    """
    Obtiene información detallada de un usuario.
    """
    # Verificar permiso o si es administrador (users.view -> ID 2)
    if not check_permission(current_user, 2):
        raise HTTPException(status_code=403, detail="No tiene permisos para ver usuarios")
    
    try:
        user_service = UserService(db)
        return user_service.list_user(user_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener el usuario: {str(e)}")


@router.get("/")
def list_users(
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    """
    Lista todos los usuarios.
    """
    # Verificar permiso o si es administrador (users.view -> ID 2)
    if not check_permission(current_user, 2):
        raise HTTPException(status_code=403, detail="No tiene permisos para ver usuarios")
    
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
    # Verificar permiso o si es administrador (users.notifications.view -> ID 12)
    if not check_permission(current_user, 12):
        raise HTTPException(status_code=403, detail="No tiene permisos para ver notificaciones")
    
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
    Create a new notification (any user)
    """
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

@router.get("/technicians/active", response_model=List[dict])
def get_active_technicians(
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    """
    Obtiene todos los usuarios técnicos activos (con permiso ID 116).
    Devuelve solo id, nombre, primer apellido y segundo apellido (opcional).
    Requiere autenticación y el permiso con ID 118.
    """
    # Verificar permiso (ID 118)
    if not check_permission(current_user, 118):
        raise HTTPException(status_code=403, detail="No tiene permisos para ver los técnicos activos")
        
    try:
        # Buscar todos los roles que tienen el permiso con ID 116
        roles_with_perm = db.query(Role).join(
            role_permission_table, 
            Role.id == role_permission_table.c.rol_id
        ).filter(
            role_permission_table.c.permission_id == 116
        ).all()
        
        if not roles_with_perm:
            return []
        
        # Obtener los IDs de los roles que tienen el permiso
        role_ids = [role.id for role in roles_with_perm]
        
        # Buscar usuarios con esos roles y que estén activos (status_id=1)
        users = db.query(
            User.id,
            User.name,
            User.first_last_name,
            User.second_last_name
        ).join(
            user_role_table,
            User.id == user_role_table.c.user_id
        ).filter(
            user_role_table.c.rol_id.in_(role_ids),
            User.status_id == 1
        ).all()
        
        # Convertir los resultados a diccionarios
        result = []
        for user in users:
            user_dict = {
                "id": user.id,
                "name": user.name,
                "first_last_name": user.first_last_name,
            }
            # Solo incluir el segundo apellido si no es None
            if user.second_last_name is not None:
                user_dict["second_last_name"] = user.second_last_name
                
            result.append(user_dict)
            
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener los técnicos activos: {str(e)}"
        )

@router.post("/send-technician-notification", response_model=TechnicianNotificationResponse)
def send_technician_notification(
    notification_data: TechnicianNotificationRequest,
    db: Session = Depends(get_db)
):
    """
    Envía un correo de notificación al técnico asignado con los detalles de la programación.
    """
    try:
        # Buscar el técnico por ID
        technician = db.query(User).filter(User.id == notification_data.assigned_technician).first()
        
        # Determinar email y nombre del técnico
        if technician:
            # Usuario existe en DB
            technician_email = technician.email
            technician_name = f"{technician.name} {technician.first_last_name}"
            if technician.second_last_name:
                technician_name += f" {technician.second_last_name}"
            
            if not technician_email:
                raise HTTPException(
                    status_code=400, 
                    detail=f"El técnico {technician.name} no tiene un email configurado en la base de datos"
                )
        else:
            # Usuario no existe en DB - error porque requerimos que esté registrado
            raise HTTPException(
                status_code=404,
                detail=f"El técnico con ID {notification_data.assigned_technician} no existe en la base de datos"
            )
        
        # Enviar el correo
        from app.email_service import EmailService
        email_service = EmailService()
        
        email_sent = email_service.send_technician_notification_email(
            to_email=technician_email,
            technician_name=technician_name,
            scheduled_at=notification_data.scheduled_at,
            details=notification_data.details
        )
        
        if email_sent:
            return TechnicianNotificationResponse(
                success=True,
                message=f"Correo de notificación enviado exitosamente a {technician_name}",
                technician_email=technician_email
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Error al enviar el correo de notificación"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar la notificación: {str(e)}"
        )

@router.post("/notifications/send-to-permission/", response_model=dict)
def send_notification_to_permission(
    permission_id: int,
    notification: NotificationCreate,  # title, message, type (user_id se ignora)
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    """
    Envía una notificación a todos los usuarios que tengan el permiso indicado en alguno de sus roles.
    """
    user_service = UserService(db)
    return user_service.send_notification_to_permission(permission_id, notification)
