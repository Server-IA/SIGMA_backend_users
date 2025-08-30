from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import text , func
from fastapi import HTTPException
from app.roles import models, schemas
from app.users.models import User
from app.users.schemas import NotificationCreate
from app.users.services import UserService


class PermissionService:
    """Clase para gestionar los permisos"""

    def __init__(self, db: Session):
        self.db = db

    def create_permission(self, permission: schemas.PermissionBase):
        """Crear un permiso con manejo de errores"""
        try:
            db_permission = self.db.query(models.Permission).filter(models.Permission.name == permission.name).first()
            if db_permission:
                raise HTTPException(status_code=400, detail={
                    "success": False,
                    "data": "El permiso ya existe asignado a ese nombre"
                })

            db_permission = models.Permission(
                name=permission.name,
                description=permission.description,
                category=permission.category
            )
            self.db.add(db_permission)
            self.db.commit()
            self.db.refresh(db_permission)
            return schemas.SimpleResponse(success=True, data="El permiso se ha creado correctamente")
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=400, detail={"success": False, "data": "El permiso ya existe."})
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(status_code=500, detail={"success": False, "data": "Error interno al crear el permiso."})

    def get_permissions(self):
        """Obtener todos los permisos con manejo de errores"""
        try:
            return self.db.query(models.Permission).all()
            return {
                "detail": {
                    "success": True,
                    "data": permissions
                }
            }
        except SQLAlchemyError:
            # agrega el registro del error a los logs
            raise HTTPException(status_code=500, detail={"success": False, "data": "Error al obtener los permisos."})


class RoleService:
    """Clase para gestionar los roles"""

    def __init__(self, db: Session):
        self.db = db

    def create_role(self, role_data: schemas.RoleCreate):
        """Crear un rol verificando que el nombre sea único (ignorando mayúsculas)"""
        try:
            # Verificar si existe un rol con el mismo nombre (case-insensitive)
            existing_role = self.db.query(models.Role).filter(
                func.lower(models.Role.name) == role_data.name.lower()
            ).first()
            if existing_role:
                raise HTTPException(
                    status_code=400,
                    detail={"success": False, "data": "El rol ya existe."}
                )
            if len(role_data.permissions) == 0:
                raise HTTPException(
                    status_code=400,
                    detail={"success": False, "data": "El rol debe tener al menos un permiso asignado."}
                )

            permissions = self.db.query(models.Permission).filter(
                models.Permission.id.in_(role_data.permissions)
            ).all()
            found_permission_ids = {perm.id for perm in permissions}
            missing_permissions = set(role_data.permissions) - found_permission_ids
            if missing_permissions:
                raise HTTPException(
                    status_code=400,
                    detail={"success": False, "data": f"Los siguientes permisos no existen: {list(missing_permissions)}"}
                )

            db_role = models.Role(name=role_data.name, description=role_data.description, status=1)
            db_role.permissions = permissions
            self.db.add(db_role)
            self.db.commit()
            self.db.refresh(db_role)


            admins = self.db.query(User).join(models.user_role_table).join(models.Role).filter(
                models.Role.name == "Administrador"
            ).all()
        
            user_service = UserService(self.db)
            for admin in admins:
                notification_data = NotificationCreate(
                    user_id=admin.id,
                    title="Nuevo rol creado",
                    message=f"Se ha creado un nuevo rol: {db_role.name}",
                    type="role_creation"
                )
                user_service.create_notification(notification_data)

            return db_role
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=401, detail="El rol ya existe.")
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Error al crear el rol.")
        
    def edit_role(self, role_id: int, role_data: schemas.RoleCreate):
        """Editar un rol verificando que el nombre nuevo sea único (ignorando mayúsculas)"""
        try:
            db_role = self.db.query(models.Role).filter(models.Role.id == role_id).first()
            if not db_role:
                raise HTTPException(
                    status_code=404,
                    detail={"success": False, "data": "El rol no existe."}
                )
            # Verificar si ya existe otro rol con el mismo nombre
            existing_role = self.db.query(models.Role).filter(
                func.lower(models.Role.name) == role_data.name.lower(),
                models.Role.id != role_id
            ).first()
            if existing_role:
                raise HTTPException(
                    status_code=400,
                    detail={"success": False, "data": "El rol ya existe."}
                )
            db_role.name = role_data.name
            db_role.description = role_data.description

            if len(role_data.permissions) == 0:
                raise HTTPException(
                    status_code=400,
                    detail={"success": False, "data": "El rol debe tener al menos un permiso asignado."}
                )
            permissions = self.db.query(models.Permission).filter(
                models.Permission.id.in_(role_data.permissions)
            ).all()
            found_permission_ids = {perm.id for perm in permissions}
            missing_permissions = set(role_data.permissions) - found_permission_ids
            if missing_permissions:
                raise HTTPException(
                    status_code=400,
                    detail={"success": False, "data": f"Los siguientes permisos no existen: {list(missing_permissions)}"}
                )
            db_role.permissions = permissions
            self.db.commit()
            self.db.refresh(db_role)

            admins = self.db.query(User).join(models.user_role_table).join(models.Role).filter(
                models.Role.name == "Administrador"
            ).all()
        
            user_service = UserService(self.db)
            for admin in admins:
                notification_data = NotificationCreate(
                    user_id=admin.id,
                    title="Rol actualizado",
                    message=f"El rol '{db_role.name}' ha sido actualizado",
                    type="role_update"
                )
                user_service.create_notification(notification_data)

                return {
                    "success": True,
                    "message": "Rol editado correctamente",
                    "data": db_role
                }
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=400, detail="El rol ya existe.")
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Error al editar el rol.")
            
    def get_roles(self):
        """Obtener todos los roles con manejo de errores"""
        try:
            # Consulta modificada: se usa DISTINCT en el string_agg para evitar duplicados
            query = """
                SELECT
                    r.id AS role_id,
                    r.name AS role_name,
                    r.description AS role_description,
                    v.name AS status_name,
                    r.status,
                    COUNT(DISTINCT ur.user_id) AS quantity_users,
                    COALESCE(string_agg(DISTINCT CONCAT(p.id, ':::::', p.name, ':::::', p.description), ','), '') AS permissions
                FROM
                    rol r
                    LEFT JOIN user_rol ur ON ur.rol_id = r.id
                    LEFT JOIN vars v ON r.status = v.id
                    LEFT JOIN rol_permission rp ON rp.rol_id = r.id
                    LEFT JOIN permission p ON p.id = rp.permission_id
                GROUP BY
                    r.id,
                    r.name,
                    r.description,
                    v.name,
                    r.status
            """
            roles = self.db.execute(text(query)).fetchall()

            roles_data = []
            for role in roles:
                permissions = []
                if role.permissions:
                    for permission_str in role.permissions.split(','):
                        if ':::::' not in permission_str:
                            continue
                        parts = permission_str.split(':::::')
                        if len(parts) != 3:
                            continue
                        perm_id, perm_name, perm_description = parts
                        permissions.append({
                            "id": int(perm_id),
                            "name": perm_name,
                            "description": perm_description
                        })

                role_data = {
                    "role_id": role.role_id,
                    "role_name": role.role_name,
                    "role_description": role.role_description,
                    "status_name": role.status_name,
                    "status": role.status,
                    "quantity_users": role.quantity_users,
                    "permissions": permissions
                }
                roles_data.append(role_data)

            return {"success": True, "data": roles_data}
        except Exception as e:
            raise HTTPException(status_code=500, detail={"success": False, "data": "Error al obtener los roles." + str(e)})


        
    def get_rol(self, role_id):
        """Obtener detalles de un rol con manejo de errores, incluyendo status_name"""
        try:
            # Traer rol junto con el nombre del estado (status_name)
            role = (
                self.db.query(models.Role)
                .join(models.Vars, models.Role.status == models.Vars.id)
                .filter(models.Role.id == role_id)
                .first()
            )

            if not role:
                raise HTTPException(status_code=404, detail="El rol no fue encontrado")

            # Preparar permisos
            permissions_list = []
            if hasattr(role, "permissions") and role.permissions:
                for perm in role.permissions:
                    permissions_list.append({
                        "id": perm.id,
                        "name": perm.name,
                        "description": getattr(perm, "description", ""),
                        "category": getattr(perm, "category", "")
                    })

            # Construir objeto final
            role_data = {
                "id": role.id,
                "name": role.name,
                "description": role.description,
                "status": role.status,                 
                "status_name": role.vars.name,   
                "permissions": permissions_list
            }

            return {"success": True, "data": [role_data]}

        except Exception as e:
            raise HTTPException(status_code=500, detail={
                "success": False,
                "data": {
                    "title": "Contacta con el administrador",
                    "message": str(e)
                }
            })

    def change_role_status(self, role_id: int, new_status: int):
        """Cambiar el estado de un rol con validación para inhabilitarlo solo si no tiene usuarios asignados"""
        try:
            role = self.db.query(models.Role).filter(models.Role.id == role_id).first()
            if not role:
                raise HTTPException(status_code=404, detail="Rol no encontrado.")
            
            # Si se desea inhabilitar el rol (por ejemplo, new_status == 0 o cualquier valor que defina "inactivo")
            # Se asume que el estado activo es 1 y el inactivo es otro valor (por ejemplo, 0).
            # Ajusta estos valores según tu modelo.
            if new_status != 1:
                # Validar que no existan usuarios asignados a este rol
                if role.users and len(role.users) > 0:
                    raise HTTPException(
                        status_code=400,
                        detail="No se puede inhabilitar el rol porque hay usuarios asignados."
                    )
            
            role.status = new_status
            self.db.commit()
            self.db.refresh(role)

            # Determinar el texto del estado para el mensaje
            status_text = "habilitado" if new_status == 1 else "inhabilitado"
        
            # Notificar a los administradores
            admins = self.db.query(User).join(models.user_role_table).join(models.Role).filter(
                models.Role.name == "Administrador"
            ).all()
        
            user_service = UserService(self.db)
            for admin in admins:
                notification_data = NotificationCreate(
                    user_id=admin.id,
                    title="Estado de rol modificado",
                    message=f"El rol '{role.name}' ha sido {status_text}",
                    type="role_status_change"
            )
            user_service.create_notification(notification_data)

            return {"success": True, "data": "Estado del rol actualizado correctamente."}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Error al actualizar el estado del rol: {str(e)}")
        

        

    def update_role_permissions(self, role_id: int, permission_ids: list[int]):
        """Actualizar permisos de un rol"""
        try:
            role = self.db.query(models.Role).filter(models.Role.id == role_id).first()
            if not role:
                raise HTTPException(status_code=404, detail={"success": False, "data": "Rol no encontrado."})

            permissions = self.db.query(models.Permission).filter(models.Permission.id.in_(permission_ids)).all()
            found_permission_ids = {perm.id for perm in permissions}
            missing_permissions = set(permission_ids) - found_permission_ids

            if missing_permissions:
                raise HTTPException(status_code=400, detail={
                    "success": False,
                    "data": f"Los siguientes permisos no existen: {list(missing_permissions)}"
                })

            role.permissions = permissions
            self.db.commit()
            self.db.refresh(role)

            return {
                "success": True,
                "message": "Permisos actualizados correctamente",
                "data": {
                    "role_id": role.id,
                    "permissions": [{"id": p.id, "name": p.name} for p in role.permissions]
                }
            }
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(status_code=500, detail={"success": False, "data": "Error al actualizar permisos."})

    def delete_role(self, role_id: int):
        """Eliminar un rol si no está en uso y no es 'Administrador'"""
        try:
            role = self.db.query(models.Role).filter(models.Role.id == role_id).first()
            if not role:
                raise HTTPException(status_code=404, detail={"success": False, "data": "Rol no encontrado"})

            if role.name.lower() == "administrador":
                raise HTTPException(status_code=400, detail={"success": False, "data": "No se puede eliminar el rol 'Administrador'"})

            if role.users and len(role.users) > 0:
                raise HTTPException(status_code=400, detail={"success": False, "data": "No se puede eliminar el rol porque está asignado a usuarios"})

            self.db.delete(role)
            self.db.commit()

            return {"success": True, "message": "Rol eliminado correctamente"}

        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(status_code=500, detail={"success": False, "data": "Error al eliminar el rol"})

class UserRoleService:
    """Clase para gestionar la asignación de roles a usuarios"""

    def __init__(self, db: Session):
        self.db = db

    def assign_role_to_user(self, user_id: int, role_id: int):
        """Asignar un rol a un usuario con validaciones"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail={"success": False, "data": "Usuario no encontrado."})

            role = self.db.query(models.Role).filter(models.Role.id == role_id).first()
            if not role:
                raise HTTPException(status_code=404, detail={"success": False, "data": "Rol no encontrado."})

            if role in user.roles:
                raise HTTPException(status_code=400, detail={"success": False, "data": "El usuario ya tiene este rol asignado."})

            user.roles.append(role)
            self.db.commit()
            self.db.refresh(user)

            
            return {"success": True, "data": "Rol asignado correctamente"}
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(status_code=500, detail={"success": False, "data": "Error al asignar el rol al usuario."})
    
    def revoke_role_from_user(self, user_id: int, role_id: int):
        """Revocar un rol de un usuario, asegurando que al menos tenga 1 rol asignado"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail={"success": False, "data": "Usuario no encontrado."})

            role = self.db.query(models.Role).filter(models.Role.id == role_id).first()
            if not role:
                raise HTTPException(status_code=404, detail={"success": False, "data": "Rol no encontrado."})

            if role not in user.roles:
                raise HTTPException(status_code=400, detail={"success": False, "data": "El usuario no tiene este rol asignado."})

            if len(user.roles) == 1:
                raise HTTPException(status_code=400, detail={"success": False, "data": "El usuario debe tener al menos un rol asignado."})

            user.roles.remove(role)
            self.db.commit()
            self.db.refresh(user)

            return {"success": True, "data": "Rol revocado correctamente"}
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(status_code=500, detail={"success": False, "data": "Error al revocar el rol del usuario."})
      
    def update_user_roles(self, user_id: int, new_role_ids: list[int]):
      """Actualizar los roles de un usuario asegurando que al menos tenga 1 rol"""
      try:
          user = self.db.query(User).filter(User.id == user_id).first()
          if not user:
              raise HTTPException(status_code=404, detail={"success": False, "data": "Usuario no encontrado."})

          # Obtener los roles existentes en la BD
          roles = self.db.query(models.Role).filter(models.Role.id.in_(new_role_ids)).all()

          # Validar que existen todos los roles enviados
          found_role_ids = {role.id for role in roles}
          missing_roles = set(new_role_ids) - found_role_ids

          if missing_roles:
              raise HTTPException(status_code=400, detail={
                  "success": False,
                  "data": f"Los siguientes roles no existen: {list(missing_roles)}"
              })

          # Validar que el usuario tenga al menos 1 rol
          if len(roles) < 1:
              raise HTTPException(status_code=400, detail={
                  "success": False,
                  "data": "El usuario debe tener al menos un rol asignado."
              })

          # Asignar los nuevos roles
          user.roles = roles
          self.db.commit()
          self.db.refresh(user)

          return {
              "success": True,
              "message": "Roles actualizados correctamente",
              "data": {
                  "user_id": user.id,
                  "roles": [{"id": r.id, "name": r.name} for r in user.roles]
              }
          }
      except SQLAlchemyError:
          self.db.rollback()
          raise HTTPException(status_code=500, detail={"success": False, "data": "Error al actualizar los roles del usuario."})

    def get_user_with_roles(self, user_id: int):
      """Obtener la información de un usuario y sus roles asignados"""
      try:
          user = self.db.query(User).filter(User.id == user_id).first()
          if not user:
              raise HTTPException(status_code=404, detail={"success": False, "data": "Usuario no encontrado."})

          # Obtener roles del usuario
          user_roles = [{"id": role.id, "name": role.name} for role in user.roles]

          return {
              "success": True,
              "data": {
                  "id": user.id,
                  "email": user.email,
                  "name": user.name,
                  "roles": user_roles
              }
          }
      except SQLAlchemyError:
          raise HTTPException(status_code=500, detail={"success": False, "data": "Error al obtener la información del usuario."})
