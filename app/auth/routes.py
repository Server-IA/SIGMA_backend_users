from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session , joinedload
from datetime import datetime
from jose import jwt, JWTError
from app.database import get_db
from app.auth.services import AuthService, SECRET_KEY, OAuthService
from app.auth.schemas import ResetPasswordRequest, ResetPasswordResponse, UpdatePasswordRequest, OAuthLoginRequest, OAuthCallbackRequest, SocialLoginResponse
from app.users.schemas import UserLogin, Token
from app.users.services import UserService
from app.roles.models import Role, Permission 
from app.users.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/swagger-login")
router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/swagger-login", response_model=Token)
def swagger_login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    auth_service = AuthService(db)
    
    user = auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    
    # Recargar el usuario con relaciones
    user = (
        db.query(User)
        .options(joinedload(User.roles).joinedload(Role.permissions))
        .filter(User.email == user.email)
        .first()
    )
    

    
    roles = []
    for role in user.roles:
        role_data = {"id": role.id, "name": role.name}
        permisos = [{"id": perm.id, "name": perm.name} for perm in role.permissions]
        role_data["permisos"] = permisos
        roles.append(role_data)
    
    token_data = {
        "sub": user.email,   
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "status_date": datetime.utcnow().isoformat(),
        "rol": roles,
        "birthday": user.birthday.isoformat() if user.birthday else None,
        "first_login_complete": user.first_login_complete
    }
    
    access_token = auth_service.create_access_token(data=token_data)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login/", response_model=Token)
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    

    user = auth_service.authenticate_user(user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    

    if not user.email_status:
        user_service = UserService(db)
        new_token = user_service.resend_activation_token(user)
        raise HTTPException(
            status_code=401, 
            detail={"status": "false", "message": "Cuenta no activada. Se ha reenviado el código de activación a su correo.", "token": new_token}
        )
    

    if user.status_id != 1:
        raise HTTPException(
            status_code=401, 
            detail="Cuenta inactiva o bloqueada. No se permite el acceso."
        )
    

    user = (
        db.query(User)
        .options(joinedload(User.roles).joinedload(Role.permissions))
        .filter(User.email == user.email)
        .first()
    )
    
    roles = []
    for role in user.roles:
        role_data = {"id": role.id, "name": role.name}
        permisos = [{"id": perm.id, "name": perm.name} for perm in role.permissions]
        role_data["permisos"] = permisos
        roles.append(role_data)
    
    token_data = {
        "sub": user.email,
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "status_date": datetime.utcnow().isoformat(),
        "rol": roles,
        "status": user.status_id,
        "birthday": user.birthday.isoformat() if user.birthday else None,
        "first_login_complete": user.first_login_complete
    }
    
    access_token = auth_service.create_access_token(data=token_data)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
def logout(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Cierra la sesión revocando el token.
    """
    auth_service = AuthService(db)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        expires_at = datetime.utcfromtimestamp(payload.get("exp"))
        auth_service.revoke_token(db, token, expires_at)
        return {"message": "Cierre de sesión exitoso"}
    except JWTError:
        raise HTTPException(status_code=400, detail="Token inválido")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al revocar el token: {str(e)}")

@router.post("/request-reset-password", response_model=ResetPasswordResponse)
def request_reset_password(reset_request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Solicita el restablecimiento de contraseña: valida el email, inhabilita tokens previos 
    y genera un token nuevo.
    """
    user_service = UserService(db)
    # Valida que el usuario exista (de lo contrario se lanza error)
    user_service.get_user_by_username(reset_request.email)
    token = user_service.generate_reset_token(reset_request.email)
    return ResetPasswordResponse(message="Enlace de restablecimiento generado", token=token)

@router.post("/reset-password/{token}", response_model=ResetPasswordResponse)
def update_password(token: str, update_request: UpdatePasswordRequest, db: Session = Depends(get_db)):
    """
    Actualiza la contraseña utilizando el token de restablecimiento.
    """
    user_service = UserService(db)
    user_service.update_password(token, update_request.new_password)
    return ResetPasswordResponse(message="Contraseña actualizada correctamente", token=token)

@router.post("/oauth/login", response_model=dict)
async def oauth_login(request: OAuthLoginRequest, db: Session = Depends(get_db)):
    """
    Inicia el proceso de inicio de sesión con OAuth (Google o Microsoft)
    
    Args:
        request: Solicitud con el proveedor y URI de redirección
        
    Returns:
        Dict con la URL de autenticación y estado
    """
    try:
        oauth_service = OAuthService(db)
        login_data = oauth_service.get_login_url(
            provider=request.provider,
            redirect_uri=request.redirect_uri
        )
        return {"success": True, "data": login_data}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al iniciar sesión con {request.provider}: {str(e)}"
        )

@router.post("/oauth/callback", response_model=SocialLoginResponse)
async def oauth_callback(request: OAuthCallbackRequest, db: Session = Depends(get_db)):
    """
    Procesa el callback de autenticación OAuth
    
    Args:
        request: Solicitud con el proveedor y código de autorización
        
    Returns:
        SocialLoginResponse con token JWT y datos del usuario
    """
    try:
        oauth_service = OAuthService(db)
        return await oauth_service.process_oauth_callback(
            provider=request.provider,
            code=request.code
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar callback de {request.provider}: {str(e)}"
        )
