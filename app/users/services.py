import uuid
import os
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta, date
from typing import List, Optional
from fastapi import HTTPException, Depends, status, UploadFile
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc
from app.users.models import Notification
from app.users import schemas
from app.users.models import Gender, Status, TypeDocument, User, PasswordReset, PreRegisterToken, ActivationToken
from app.users.schemas import UserCreateRequest, ChangePasswordRequest, UserUpdateInfo, AdminUserCreateResponse, PreRegisterResponse, ActivateAccountResponse , NotificationCreate
from app.roles.models import Role
from Crypto.Protocol.KDF import scrypt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from app.auth.services import SECRET_KEY, ALGORITHM
from jose import jwt, JWTError
from fastapi.responses import JSONResponse
from app.firebase_config import bucket


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

_activation_resend_timestamps = {}
_RATE_LIMIT_SECONDS = 60


class UserService:
    """Clase para gestionar la creación y obtención de usuarios"""

    def __init__(self, db: Session):
        self.db = db

    async def save_profile_picture(self, file: UploadFile) -> str:
        """
        Guarda la imagen de perfil en Firebase Storage con un nombre único
        y retorna la URL pública del archivo.
        """
        try:
            file_content = await file.read()
            unique_filename = f"{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
            directory = "uploads/profile_pictures/"
            if not directory.endswith("/"):
                directory += "/"
            blob = bucket.blob(f"{directory}{unique_filename}")
            blob.upload_from_string(file_content, content_type=file.content_type)
            blob.make_public()
            return blob.public_url
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al guardar la imagen de perfil en Firebase: {str(e)}")
        
    def resend_activation_token(self, user: User) -> str:
        """
        Invalida los tokens de activación previos para el usuario y genera uno nuevo.
        Aplica un limitador de peticiones para evitar abusos (por user id).
        """
        try:
            now = datetime.utcnow()
            last_request = _activation_resend_timestamps.get(user.id)
            if last_request and (now - last_request).total_seconds() < _RATE_LIMIT_SECONDS:
                raise HTTPException(
                    status_code=429,
                    detail="Demasiadas peticiones. Por favor, espera un momento antes de solicitar un nuevo código de activación."
                )
            # Actualiza el timestamp de la última petición para este usuario
            _activation_resend_timestamps[user.id] = now

            # Marcar como usados todos los tokens de activación pendientes del usuario
            tokens = self.db.query(ActivationToken).filter(
                ActivationToken.user_id == user.id,
                ActivationToken.used == False
            ).all()
            for token_obj in tokens:
                token_obj.used = True
            self.db.commit()

            # Generar un nuevo token de activación
            new_activation_token = str(uuid.uuid4())
            expiration = datetime.utcnow() + timedelta(days=7)  # Token válido por 7 días
            token_obj = ActivationToken(
                token=new_activation_token,
                user_id=user.id,
                expires_at=expiration,
                used=False
            )
            self.db.add(token_obj)
            self.db.commit()

            # Aquí puedes incluir la lógica para enviar el correo con el nuevo token

            return new_activation_token

        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=429, detail=f"Error al reenviar código de activación: {str(e)}")

    async def complete_first_login_registration(self, user_id: int, country: str, 
                                        department: str, city: int, 
                                        address: str, phone: str, 
                                        profile_picture: str = None) -> dict:
        """
        Completa el registro del usuario después de su primer login.

        Args:
            user_id: ID del usuario
            country: País de residencia
            department: Departamento o provincia
            city: Código de municipio
            address: Dirección completa
            phone: Número de teléfono
            profile_picture: Ruta a la imagen de perfil (opcional)

        Returns:
            Diccionario con el resultado de la operación
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="Usuario no encontrado")

            user.country = country
            user.department = department
            user.city = city
            user.address = address
            user.phone = phone

            if profile_picture:
                user.profile_picture = profile_picture

            user.first_login_complete = True

            self.db.commit()
            self.db.refresh(user)

            return {
                "success": True,
                "data": {
                    "title": "Registro completo",
                    "message": "Datos de perfil guardados correctamente"
                }
            }
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error al completar el registro: {str(e)}"
            )

    def check_profile_completion(self, user_id: int) -> dict:
        """
        Verifica si el usuario ya ha completado su perfil después del primer login.

        Args:
            user_id: ID del usuario

        Returns:
            Diccionario con el estado de completitud del perfil
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="Usuario no encontrado")

            return {
                "success": True,
                "data": {
                    "first_login_complete": user.first_login_complete,
                    "has_profile_data": user.country is not None and user.department is not None and user.city is not None
                }
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al verificar el estado del perfil: {str(e)}")

    def get_user_by_username(self, username: str):
        try:
            user = self.db.query(User).filter(User.email == username).first()
            if not user:
                raise HTTPException(status_code=404, detail="Usuario no encontrado")
            return user
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Contacta con el administrador: {str(e)}")

    def create_user(self, user_data: UserCreateRequest):
        try:
            db_user = User(
                name=user_data.first_name,
                first_last_name=user_data.first_last_name,
                second_last_name=user_data.second_last_name,
                type_document_id=user_data.document_type,
                document_number=user_data.document_number,
                date_issuance_document=user_data.date_issuance_document
            )

            if user_data.role_id:
                roles = self.db.query(Role).filter(Role.id.in_(user_data.role_id)).all()
                db_user.roles = roles

            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)

            return {"success": True, "title": "Éxito", "data": "Usuario creado correctamente"}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail={"success": False, "data": {
                    "title": "Error al crear usuario",
                    "message": str(e),
                }}
            )

    def hash_password(self, password: str) -> tuple:
        """Genera un hash de la contraseña con salt aleatorio"""
        try:
            salt = os.urandom(16)
            key = scrypt(password.encode(), salt, key_len=32, N=2**14, r=8, p=1)
            return salt.hex(), key.hex()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Contacta con el administrador: {str(e)}")

    def verify_password(self, stored_salt: str, stored_hash: str, password: str) -> bool:
        """Verifica la contraseña ingresada contra el hash almacenado"""
        try:
            salt = bytes.fromhex(stored_salt)
            key = scrypt(password.encode(), salt, key_len=32, N=2**14, r=8, p=1)
            return key.hex() == stored_hash
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Contacta con el administrador: {str(e)}")

    def update_user(self, user_id: int, admin_update: bool = False, **kwargs):
        """Actualiza los detalles de un usuario y, si admin_update es True, envía una notificación."""
        try:
            db_user = self.db.query(User).filter(User.id == user_id).first()
            if not db_user:
                raise HTTPException(status_code=404, detail="Usuario no encontrado")
            for key, value in kwargs.items():
                setattr(db_user, key, value)
            self.db.commit()
            self.db.refresh(db_user)
            
            if admin_update:
                # Registro para ver que se dispara la notificación
                print(f"[DEBUG] Creando notificación para el usuario {user_id}.")
                notification_data = schemas.NotificationCreate(
                    user_id=user_id,
                    title="Información actualizada",
                    message="Su información ha sido actualizada por un administrador.",
                    type="admin_edit"  # Puedes modificar según tu convención
                )
                notification_res = self.create_notification(notification_data)
                print(f"[DEBUG] Resultado de la notificación: {notification_res}")
                
            return {"success": True, "data": "Usuario actualizado correctamente"}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail={"success": False, "data": {
                "title": "Contacta con el administrador",
                "message": str(e),
            }})


    def list_users(self):
        try:
            users = (
                self.db.query(
                    User.id,
                    User.email,
                    User.name,
                    User.first_last_name,
                    User.second_last_name,
                    User.address,
                    User.profile_picture,
                    User.phone,
                    User.document_number,
                    User.date_issuance_document,
                    User.type_document_id,
                    User.birthday,
                    TypeDocument.name.label("type_document_name"),
                    User.status_id,
                    Status.name.label("status_name"),
                    Status.description.label("status_description"),
                    User.gender_id,
                    Gender.name.label("gender_name"),
                    User.country,
                    User.department,
                    User.city,
                    User.first_login_complete
                )
                .outerjoin(User.type_document)
                .outerjoin(User.status_user)
                .outerjoin(User.gender)
                .all()
            )

            if not users:
                raise HTTPException(status_code=404, detail="No se encontraron usuarios.")

            users_list = []
            for user in users:
                user_dict = {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "first_last_name": user.first_last_name,
                    "second_last_name": user.second_last_name,
                    "address": user.address,
                    "profile_picture": user.profile_picture,
                    "phone": user.phone,
                    "date_issuance_document": user.date_issuance_document,
                    "document_number": user.document_number,
                    "status": user.status_id,
                    "birthday": user.birthday,
                    "status_name": user.status_name,
                    "status_description": user.status_description,
                    "type_document": user.type_document_id,
                    "type_document_name": user.type_document_name,
                    "gender": user.gender_id,
                    "gender_name": user.gender_name,
                    "country": user.country,
                    "department": user.department,
                    "city": user.city,
                    "first_login_complete": user.first_login_complete
                }

                user_obj = self.db.query(User).filter(User.id == user.id).first()
                user_roles = [{"id": role.id, "name": role.name} for role in user_obj.roles] if user_obj.roles else []
                user_dict["roles"] = user_roles

                users_list.append(user_dict)

            return jsonable_encoder({"success": True, "data": users_list})
        except Exception as e:
            raise HTTPException(status_code=500, detail={
                "success": False,
                "data": {
                    "title": "Error de servidor",
                    "message": str(e),
                }
            })

    def change_user_status(self, user_id: int, new_status: int):
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="Usuario no encontrado.")

            status_obj = self.db.query(Status).filter(Status.id == new_status).first()
            if not status_obj:
                raise HTTPException(status_code=400, detail="Estado no válido.")

            user.status_id = new_status
            self.db.commit()
            self.db.refresh(user)

            # Verificar si el nuevo estado representa una inhabilitación; en este ejemplo, usamos new_status == 0.
            if new_status == 0:
                notification_data = schemas.NotificationCreate(
                    user_id=user_id,
                    title="Cuenta inhabilitada",
                    message="Su cuenta ha sido inhabilitada por un administrador.",
                    type="admin_inactivation"
                )
                self.create_notification(notification_data)

            return {"success": True, "data": "Estado de usuario actualizado correctamente."}

        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Error al actualizar el estado del usuario: {str(e)}")


    def get_type_documents(self):
        """Obtiene todos los tipos de documentos"""
        try:
            type_documents = self.db.query(TypeDocument).all()
            if not type_documents:
                raise HTTPException(status_code=404, detail="No se encontraron tipos de documentos.")
            type_documents_data = jsonable_encoder(type_documents)
            return {"success": True, "data": type_documents_data}
        except Exception as e:
            raise HTTPException(status_code=500, detail={
                "success": False,
                "data": {
                    "title": "Error de servidor",
                    "message": str(e)
                }
            })

    def generate_reset_token(self, email: str) -> str:
        """
        Genera un token único para restablecer la contraseña y lo guarda en la BD.
        """
        previous_tokens = self.db.query(PasswordReset).filter(PasswordReset.email == email).all()
        for token_obj in previous_tokens:
            self.db.delete(token_obj)
        self.db.commit()

        token = str(uuid.uuid4())
        expiration_time = datetime.utcnow() + timedelta(hours=1)
        password_reset = PasswordReset(email=email, token=token, expiration=expiration_time)
        self.db.add(password_reset)
        self.db.commit()
        return token

    def update_password(self, token: str, new_password: str):
        """
        Actualiza la contraseña del usuario utilizando el token de restablecimiento y genera una notificación.
        """
        password_reset = self.db.query(PasswordReset).filter(PasswordReset.token == token).first()
        if not password_reset:
            raise HTTPException(status_code=404, detail="Token inválido o expirado")
        if password_reset.expiration < datetime.utcnow():
            raise HTTPException(status_code=400, detail="El token ha expirado")

        user = self.db.query(User).filter(User.email == password_reset.email).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Actualizar contraseña
        new_salt, new_hash = self.hash_password(new_password)
        user.password = new_hash
        user.password_salt = new_salt
        self.db.commit()
        
        # Eliminar el token usado
        self.db.delete(password_reset)
        self.db.commit()

        
        notification_data = schemas.NotificationCreate(
            user_id=user.id,
            title="Cambio de contraseña",
            message="Tu contraseña ha sido actualizada correctamente. Si no realizaste este cambio, contacta con soporte.",
            type="security"
        )
        self.create_notification(notification_data)

        return {"message": "Contraseña actualizada correctamente"}


    def change_user_password(self, user_id: int, password_data: ChangePasswordRequest):
        """
        Actualiza la contraseña de un usuario verificando la contraseña actual
        y genera una notificación de tipo 'security'.
        """
        try:
            # 1. Verificar existencia de usuario
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="Usuario no encontrado")

            # 2. Verificar que tenga contraseña configurada
            if user.password_salt is None:
                raise HTTPException(
                    status_code=400,
                    detail="El usuario no tiene una contraseña configurada. Usa recuperación de contraseña."
                )

            # 3. Verificar contraseña actual
            if not self.verify_password(user.password_salt, user.password, password_data.old_password):
                raise HTTPException(status_code=400, detail="La contraseña actual es incorrecta")

            # 4. Hashear y guardar nueva contraseña
            new_salt, new_hash = self.hash_password(password_data.new_password)
            user.password = new_hash
            user.password_salt = new_salt
            self.db.commit()

            # 5. Crear notificación
            notification_data = NotificationCreate(
                user_id=user.id,
                title="Cambio de contraseña",
                message="Has actualizado tu contraseña correctamente. Si no realizaste este cambio, contacta con soporte.",
                type="security"
            )
            notification_res = self.create_notification(notification_data)

            # 6. LOG de depuración
            print(f"[DEBUG] change_user_password → create_notification devolvió: {notification_res}")

            return {"success": True, "data": "Contraseña actualizada correctamente"}

        except HTTPException:
            # Propaga errores conocidos
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail={"success": False, "data": {
                    "title": "Error al actualizar la contraseña",
                    "message": str(e)
                }}
            )


    async def validate_for_pre_register(self, document_type_id: int, document_number: str, 
                                        date_issuance_document: datetime) -> PreRegisterResponse:
        try:
            doc_number_int = int(document_number)
            user = self.db.query(User).filter(
                User.document_number == doc_number_int,
                User.type_document_id == document_type_id
            ).first()
            if not user:
                raise HTTPException(status_code=404, detail="No existe un usuario con estos datos en el sistema.")
            if user.date_issuance_document.date() != date_issuance_document:
                raise HTTPException(status_code=400, detail="La fecha de expedición no coincide con nuestros registros.")
            if user.status_id == 1:
                raise HTTPException(status_code=400, detail="Este usuario ya ha realizado su pre-registro. Por favor inicie sesión o use la opción de recuperar contraseña.")
            if user.email:
                raise HTTPException(status_code=400, detail="Este usuario ya tiene un correo electrónico registrado. Por favor inicie sesión o use la opción de recuperar contraseña.")

            token = str(uuid.uuid4())
            expiration = datetime.utcnow() + timedelta(hours=24)
            pre_register_token = PreRegisterToken(
                token=token,
                user_id=user.id,
                expires_at=expiration,
                used=False
            )

            self.db.add(pre_register_token)
            self.db.commit()

            return PreRegisterResponse(
                success=True,
                message="Validación exitosa. Complete su registro con email y contraseña.",
                token=token
            )

        except ValueError as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=f"Error en la validación: {str(e)}")
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Error de base de datos: {str(e)}")
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")

    async def complete_pre_register(self, token: str, email: str, password: str) -> PreRegisterResponse:
        try:
            pre_register_token = self.db.query(PreRegisterToken).filter(
                PreRegisterToken.token == token,
                PreRegisterToken.used == False,
                PreRegisterToken.expires_at > datetime.utcnow()
            ).first()

            if not pre_register_token:
                raise HTTPException(status_code=400, detail="Token inválido o expirado. Por favor, reinicie el proceso.")

            user = self.db.query(User).filter(User.id == pre_register_token.user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="Usuario no encontrado. Por favor, contacte al administrador.")

            existing_email = self.db.query(User).filter(
                User.email == email,
                User.id != user.id
            ).first()

            if existing_email:
                raise HTTPException(status_code=400, detail="Este correo electrónico ya está registrado. Por favor utilice otro.")

            salt, hash_password = self.hash_password(password)
            user.email = email
            user.password = hash_password
            user.password_salt = salt
            user.status_id = 2  
            user.email_status = False
            pre_register_token.used = True

            activation_token = str(uuid.uuid4())
            expiration = datetime.utcnow() + timedelta(days=1)

            new_activation_token = ActivationToken(
                token=activation_token,
                user_id=user.id,
                expires_at=expiration,
                used=False
            )

            self.db.add(new_activation_token)
            self.db.commit()

            return PreRegisterResponse(
                success=True,
                message="Pre-registro completado con éxito. Se ha enviado un correo de activación a su dirección de email.",
                token=activation_token
            )

        except ValueError as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=f"Error en el pre-registro: {str(e)}")
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Error de base de datos: {str(e)}")
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")

    async def activate_account(self, activation_token: str) -> ActivateAccountResponse:
        try:
            token_obj = self.db.query(ActivationToken).filter(
                ActivationToken.token == activation_token,
                ActivationToken.used == False,
                ActivationToken.expires_at > datetime.utcnow()
            ).first()

            if not token_obj:
                raise HTTPException(status_code=400, detail="Token de activación inválido o expirado. Por favor, solicite uno nuevo.")

            user = self.db.query(User).filter(User.id == token_obj.user_id).first()

            if not user:
                raise HTTPException(status_code=404, detail="Usuario no encontrado. Por favor, contacte al administrador.")

            token_obj.used = True
            if user.status_id is None or user.status_id != 1 and user.email_status==False:
                user.status_id = 1
                user.email_status = True

            self.db.commit()

            return ActivateAccountResponse(
                success=True,
                message="¡Su cuenta ha sido activada con éxito! Ahora puede iniciar sesión en el sistema."
            )

        except ValueError as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=f"Error en la activación: {str(e)}")
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Error de base de datos: {str(e)}")
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")

    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

    def list_user(self, user_id: int):
        """
        Obtiene la información completa de un usuario, incluyendo relaciones.
        """
        try:
            user = (
                self.db.query(User)
                .options(
                    joinedload(User.type_document),
                    joinedload(User.status_user),
                    joinedload(User.gender),
                    joinedload(User.roles)
                )
                .filter(User.id == user_id)
                .first()
            )
            if not user:
                raise HTTPException(status_code=404, detail="Usuario no encontrado.")

            user_dict = {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "first_last_name": user.first_last_name,
                "second_last_name": user.second_last_name,
                "address": user.address,
                "profile_picture": user.profile_picture,
                "phone": user.phone,
                "document_number": user.document_number,
                "date_issuance_document": user.date_issuance_document,
                "type_document_id": user.type_document_id,
                "status_id": user.status_id,
                "gender_id": user.gender_id,
                "birthday": user.birthday,
                "type_document_name": user.type_document.name if user.type_document else None,
                "status_name": user.status_user.name if user.status_user else None,
                "status_description": user.status_user.description if user.status_user else None,
                "gender_name": user.gender.name if user.gender else None,
                "roles": [{"id": role.id, "name": role.name} for role in user.roles],
                "country": user.country,
                "department": user.department,
                "city": user.city,
                "first_login_complete": user.first_login_complete
            }

            return jsonable_encoder({"success": True, "data": [user_dict]})
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al obtener la información del usuario: {str(e)}")

    async def update_basic_profile(
        self,
        user_id: int,
        country: Optional[int] = None,
        department: Optional[int] = None,
        city: Optional[int] = None,
        address: Optional[str] = None,
        phone: Optional[str] = None,
        profile_picture: Optional[str] = None
    ) -> dict:
        """
        Actualiza la información básica del perfil del usuario.
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="Usuario no encontrado")

            if country is not None:
                user.country = country
            if department is not None:
                user.department = department
            if city is not None:
                user.city = city
            if address is not None:
                user.address = address
            if phone is not None:
                user.phone = phone
            if profile_picture is not None:
                user.profile_picture = profile_picture

            self.db.commit()
            self.db.refresh(user)

            return {
                "success": True,
                "data": {
                    "title": "Perfil actualizado",
                    "message": "Información del perfil actualizada correctamente"
                }
            }
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error al actualizar el perfil: {str(e)}"
            )

    def create_user_by_admin(self, name: str, first_last_name: str, second_last_name: str, 
                            type_document_id: int, document_number: str, date_issuance_document: datetime,
                            birthday: datetime, gender_id: int, roles: List[int], admin_id: int):
        try:
            # Se crea el usuario según los parámetros
            db_user = User(
                name=name,
                first_last_name=first_last_name,
                second_last_name=second_last_name,
                type_document_id=type_document_id,
                document_number=document_number,
                date_issuance_document=date_issuance_document,
                birthday=birthday,
                gender_id=gender_id,
                status_id=4  # Estado "Activo" para nuevos usuarios
            )

            if roles:
                roles_obj = self.db.query(Role).filter(Role.id.in_(roles)).all()
                db_user.roles = roles_obj

            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)

            
            notification_data = schemas.NotificationCreate(
                user_id=admin_id,  
                title="Nuevo usuario creado",
                message=f"Se ha creado un nuevo usuario: {db_user.name} {db_user.first_last_name}.",
                type="user_creation"
            )
            self.create_notification(notification_data)

            return {"success": True, "message": "Usuario creado correctamente", "user_id": db_user.id}

        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "data": {
                        "title": "Error al crear usuario",
                        "message": str(e),
                    }
                }
            )

    def get_genders(self):
        """Obtiene todos los géneros disponibles en el sistema"""
        try:
            genders = self.db.query(Gender).all()
            return {
                "success": True,
                "data": jsonable_encoder(genders)
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al obtener géneros: {str(e)}")

    def get_user_notifications(self, user_id: int):
        """
        Get all notifications for a specific user
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dictionary with success status and list of notifications
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "data": [], "unread_count": 0, "message": "Usuario no encontrado"}
            
            notifications = self.db.query(Notification).filter(
                Notification.user_id == user_id
            ).order_by(desc(Notification.created_at)).all()
            
            # Count unread notifications
            unread_count = self.db.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.read == False
            ).count()
            
            return {"success": True, "data": notifications, "unread_count": unread_count}
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail={"success": False, "data": {
                    "title": "Error al obtener notificaciones",
                    "message": str(e),
                }}
            )

    def create_notification(self, notification_data: schemas.NotificationCreate):
        """
        Create a new notification
        
        Args:
            notification_data: NotificationCreate schema with notification details
            
        Returns:
            Dictionary with success status and created notification ID
        """
        try:
            user = self.db.query(User).filter(User.id == notification_data.user_id).first()
            if not user:
                return {"success": False, "data": None, "message": "Usuario no encontrado"}
            
            new_notification = Notification(
                user_id=notification_data.user_id,
                title=notification_data.title,
                message=notification_data.message,
                type=notification_data.type,
                read=False,
                created_at=datetime.now()
            )
            
            self.db.add(new_notification)
            self.db.commit()
            self.db.refresh(new_notification)
            
            return {"success": True, "data": {"id": new_notification.id}}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500, 
                detail={"success": False, "data": {
                    "title": "Error al crear notificación",
                    "message": str(e),
                }}
            )

    def mark_notifications_as_read(self, user_id: int, notification_ids: List[int] = None, mark_all: bool = False):
        """
        Mark specific or all notifications as read for a user
        
        Args:
            user_id: ID of the user
            notification_ids: List of notification IDs to mark as read (optional)
            mark_all: Flag to mark all user's notifications as read
            
        Returns:
            Dictionary with success status and message
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "message": "Usuario no encontrado"}
            
            if mark_all:
                # Mark all notifications as read
                self.db.query(Notification).filter(
                    Notification.user_id == user_id
                ).update({"read": True})
            elif notification_ids:
                # Mark specific notifications as read
                self.db.query(Notification).filter(
                    Notification.id.in_(notification_ids),
                    Notification.user_id == user_id
                ).update({"read": True})
            
            self.db.commit()
            return {"success": True, "message": "Notificaciones marcadas como leídas"}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500, 
                detail={"success": False, "data": {
                    "title": "Error al marcar notificaciones como leídas",
                    "message": str(e),
                }}
            )

    def get_unread_notification_count(self, user_id: int):
        """
        Get count of unread notifications for a user
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dictionary with success status and count
        """
        try:
            count = self.db.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.read == False
            ).count()
            
            return {"success": True, "count": count}
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail={"success": False, "data": {
                    "title": "Error al obtener conteo de notificaciones",
                    "message": str(e),
                }}
            )