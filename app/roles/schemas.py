from pydantic import BaseModel, Field, field_validator
from typing import List, Any
# Respuesta simplificada con éxito y datos
class SimpleResponse(BaseModel):
    success: bool
    data: Any  # Aquí se puede incluir el mensaje de éxito o los datos relevantes


class PermissionBase(BaseModel):
    name: str
    description: str
    category: str

class PermissionResponse(PermissionBase):
    id: int
    class Config:
        orm_mode = True



class RoleBase(BaseModel):
    name: str = Field(..., max_length=20, min_length=3, description="Nombre del rol")
    description: str = Field(..., max_length=255, min_length=3, description="Descripción del rol")
    
    # Normalizar entrada: quitar espacios y forzar lowercase
    @field_validator("name")
    def normalize_name(cls, v: str) -> str:
        return v.strip().casefold()   
    
class RoleCreate(RoleBase):
    permissions: List[int] = []

class RoleResponse(RoleBase):
    id: int
    permissions: List[PermissionResponse] = []
    class Config:
        orm_mode = True

class EditRoleResponse(BaseModel):
    success: bool
    message: str 
    data: RoleResponse
    
    

class AssignRoleRequest(BaseModel):
    user_id: int
    role_id: int

class UpdateRolePermissions(BaseModel):
    permissions: List[int]  # Lista de IDs de permisos a asignar

class UpdateUserRoles(BaseModel):
    roles: List[int]  # Lista de IDs de los roles que el usuario debe tener


class GenericResponse(BaseModel):
    success: bool
    message: str
    