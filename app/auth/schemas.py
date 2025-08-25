from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional, Dict, Any

# Modelo para el login de usuario
class UserLogin(BaseModel):
    email: str
    password: str

# Modelo de respuesta con el token
class Token(BaseModel):
    access_token: str
    token_type: str

# Esquema para la solicitud de restablecimiento de contraseña
class ResetPasswordRequest(BaseModel):
    email: str

# Esquema para el restablecimiento de contraseña con token
class UpdatePasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=12, description="Nueva contraseña")
    confirm_password: str = Field(..., min_length=12, description="Confirmación de la nueva contraseña")

# Respuesta de restablecimiento de contraseña
class ResetPasswordResponse(BaseModel):
    message: str
    token: Optional[str] = None

# Esquema para la solicitud de cambio de contraseña
class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=12, description="Contraseña actual")
    new_password: str = Field(..., min_length=12, description="Nueva contraseña con mínimo 12 caracteres, incluyendo mayúsculas, minúsculas y números")
    confirm_password: str = Field(..., min_length=12, description="Confirmación de la nueva contraseña")

# Respuesta de cambio de contraseña
class ChangePasswordResponse(BaseModel):
    message: str

# Esquema para iniciar el proceso de login con OAuth
class OAuthLoginRequest(BaseModel):
    """Solicitud para iniciar el proceso de login con OAuth (Google/Microsoft)"""
    provider: str = Field(..., description="Proveedor de OAuth: 'google' o 'microsoft'")
    redirect_uri: str = Field(..., description="URI de redirección después de la autenticación")

# Esquema para el callback después de autenticación OAuth
class OAuthCallbackRequest(BaseModel):
    """Solicitud de callback después de autenticación OAuth"""
    provider: str = Field(..., description="Proveedor de OAuth: 'google' o 'microsoft'")
    code: str = Field(..., description="Código de autorización recibido")
    state: Optional[str] = None

# Información del usuario obtenida del proveedor OAuth
class OAuthUserInfo(BaseModel):
    """Información del usuario obtenida del proveedor OAuth"""
    provider: str
    provider_user_id: str
    email: EmailStr
    name: Optional[str] = None
    picture: Optional[str] = None

# Respuesta después de la autenticación con OAuth
class SocialLoginResponse(BaseModel):
    """Respuesta después de la autenticación con OAuth"""
    success: bool
    message: str
    access_token: Optional[str] = None
    token_type: Optional[str] = None
    user_info: Optional[Dict[str, Any]] = None
    is_new_user: Optional[bool] = None
