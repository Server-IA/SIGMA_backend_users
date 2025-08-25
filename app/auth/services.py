from typing import Dict
from fastapi import Depends, HTTPException, requests, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from datetime import datetime, timedelta
from app.auth.schemas import OAuthUserInfo, SocialLoginResponse
from app.users.models import SocialAccount, User, RevokedToken
from sqlalchemy.orm import Session, joinedload
from app.roles.models import Role, Permission
from Crypto.Protocol.KDF import scrypt
import os

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

class AuthService:
    """Clase para la gestión de autenticación"""

    def __init__(self, db: Session):
        self.db = db

    def create_access_token(self, data: dict, expires_delta: timedelta = None) -> str:
        """
        Crear un token de acceso JWT con una fecha de expiración
        :param data: Información que se incluirá en el payload del JWT
        :param expires_delta: Tiempo de expiración del token
        :return: JWT firmado
        """
        try:
            to_encode = data.copy()
            expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
            to_encode.update({"exp": expire})
            encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
            return encoded_jwt
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al crear el token: {str(e)}")

    def revoke_token(self, db: Session, token: str, expires_at: datetime):
        """
        Revocar un token y guardarlo en la base de datos
        :param db: Sesión de la base de datos
        :param token: El token a revocar
        :param expires_at: Fecha de expiración del token
        :return: Mensaje de éxito
        """
        try:
            revoked = RevokedToken(token=token, expires_at=expires_at)
            db.add(revoked)
            db.commit()
            return {"success": True, "data": "Token revocado correctamente"}
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error al revocar el token: {str(e)}")

    def verify_password(self, stored_salt: str, stored_hash: str, password: str) -> bool:
        """
        Verificar si la contraseña proporcionada coincide con el hash almacenado
        :param stored_salt: El salt almacenado en la base de datos
        :param stored_hash: El hash de la contraseña almacenado en la base de datos
        :param password: La contraseña proporcionada por el usuario
        :return: True si la contraseña es válida, False en caso contrario
        """
        try:
            calculated_hash = self.hash_password(password, stored_salt)
            return calculated_hash == stored_hash
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al verificar la contraseña: {str(e)}")

    def hash_password(self, password: str, salt: str) -> str:
        """
        Generar el hash de la contraseña con salt utilizando el algoritmo scrypt
        :param password: Contraseña proporcionada por el usuario
        :param salt: El salt para el hash
        :return: El hash generado de la contraseña
        """
        try:
            salt_bytes = bytes.fromhex(salt)
            key = scrypt(password.encode(), salt=salt_bytes, key_len=32, N=2**14, r=8, p=1)
            return key.hex()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al generar el hash de la contraseña: {str(e)}")
    
    def get_user_by_username(self, username: str):
        try:
            user = (
                self.db.query(User)
                .options(joinedload(User.roles).joinedload(Role.permissions))
                .filter(User.email == username)
                .first()
            )
            if not user:
                raise HTTPException(status_code=404, detail="Usuario no encontrado.")
            return user
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al obtener el usuario: {str(e)}")

    def hash_password(self, password: str) -> tuple:
        try:
            salt = os.urandom(16)
            key = scrypt(password.encode(), salt, key_len=32, N=2**14, r=8, p=1)
            return salt.hex(), key.hex()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al generar el hash de la contraseña: {str(e)}")

    def verify_password(self, stored_salt: str, stored_hash: str, password: str) -> bool:
        try:
            bytes.fromhex(stored_salt)
        except ValueError:
            raise HTTPException(status_code=400, detail="El salt almacenado no es una cadena hexadecimal válida.")
        
        try:
            salt = bytes.fromhex(stored_salt)
            key = scrypt(password.encode(), salt, key_len=32, N=2**14, r=8, p=1)
            return key.hex() == stored_hash
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al verificar la contraseña: {str(e)}")

    def authenticate_user(self, email: str, password: str):
        try:
            user = self.get_user_by_username(email)
            if not user or not self.verify_password(user.password_salt, user.password, password):
                raise HTTPException(status_code=401, detail="Credenciales inválidas")
            return user
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Error al autenticar al usuario: {str(e)}")

    def create_access_token(self, data: dict, expires_delta: timedelta = None):
        try:
            to_encode = data.copy()
            expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
            to_encode.update({"exp": expire})
            encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
            return encoded_jwt
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al crear el token: {str(e)}")

    def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
        """
        Verifica el token JWT y retorna la información del usuario actual.
        Si el token es inválido, lanza una excepción.
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas",
                headers={"WWW-Authenticate": "Bearer"},
            )

class OAuthService:
    """Servicio para gestionar la autenticación con proveedores OAuth"""

    def __init__(self, db: Session):
        self.db = db
        # Credenciales para Google OAuth
        self.google_client_id = os.getenv("GOOGLE_CLIENT_ID", "")
        self.google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")
        self.google_redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "")

        # Credenciales para Microsoft OAuth
        self.microsoft_client_id = os.getenv("MICROSOFT_CLIENT_ID", "")
        self.microsoft_client_secret = os.getenv("MICROSOFT_CLIENT_SECRET", "")
        self.microsoft_redirect_uri = os.getenv("MICROSOFT_REDIRECT_URI", "")

    def get_login_url(self, provider: str, redirect_uri: str) -> Dict[str, str]:
        """
        Genera la URL para iniciar el flujo de OAuth con el proveedor seleccionado
        """
        if provider == "google":
            return self._get_google_login_url(redirect_uri)
        elif provider == "microsoft":
            return self._get_microsoft_login_url(redirect_uri)
        else:
            raise ValueError(f"Proveedor no soportado: {provider}")

    def _get_google_login_url(self, redirect_uri: str) -> Dict[str, str]:
        """Genera URL para autenticación con Google"""
        auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        scope = "openid email profile"
        state = "google_state_token"  # Generar un token aleatorio en producción

        auth_uri = (
            f"{auth_url}?client_id={self.google_client_id}&response_type=code&"
            f"scope={scope}&redirect_uri={redirect_uri}&state={state}&"
            f"access_type=offline&prompt=consent"
        )
        return {"auth_url": auth_uri, "state": state}

    def _get_microsoft_login_url(self, redirect_uri: str) -> Dict[str, str]:
        """Genera URL para autenticación con Microsoft"""
        auth_url = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
        scope = "openid email profile User.Read"
        state = "microsoft_state_token"  # Generar un token aleatorio en producción

        auth_uri = (
            f"{auth_url}?client_id={self.microsoft_client_id}&response_type=code&"
            f"scope={scope}&redirect_uri={redirect_uri}&state={state}&response_mode=query"
        )
        return {"auth_url": auth_uri, "state": state}

    async def process_oauth_callback(self, provider: str, code: str) -> SocialLoginResponse:
        """
        Procesa el callback de autenticación OAuth
        """
        try:
            if provider == "google":
                user_info = await self._get_google_user_info(code)
            elif provider == "microsoft":
                user_info = await self._get_microsoft_user_info(code)
            else:
                return SocialLoginResponse(success=False, message=f"Proveedor no soportado: {provider}")

            # Verificar si ya existe una cuenta social asociada
            social_account = self.db.query(SocialAccount).filter(
                SocialAccount.provider == provider,
                SocialAccount.provider_user_id == user_info.provider_user_id
            ).first()

            is_new_user = False

            if social_account:
                user = social_account.user
                social_account.email = user_info.email
                social_account.updated_at = datetime.utcnow()
            else:
                user = self.db.query(User).filter(User.email == user_info.email).first()
                if not user:
                    user = User(
                        email=user_info.email,
                        name=user_info.name or user_info.email.split('@')[0],
                        is_active=True,
                        status_id=1
                    )
                    self.db.add(user)
                    self.db.flush()
                    is_new_user = True

                social_account = SocialAccount(
                    user_id=user.id,
                    provider=provider,
                    provider_user_id=user_info.provider_user_id,
                    email=user_info.email
                )
                self.db.add(social_account)

            self.db.commit()

            # Generar token JWT
            token_data = {
                "sub": user.email,
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
            }
            access_token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

            return SocialLoginResponse(
                success=True,
                message="Inicio de sesión exitoso",
                access_token=access_token,
                token_type="bearer",
                user_info={"id": user.id, "email": user.email, "name": user.name},
                is_new_user=is_new_user
            )

        except Exception as e:
            self.db.rollback()
            return SocialLoginResponse(success=False, message=f"Error en la autenticación: {str(e)}")

    async def _get_google_user_info(self, code: str) -> OAuthUserInfo:
        """Obtiene información del usuario de Google"""
        token_url = "https://oauth2.googleapis.com/token"
        token_payload = {
            "code": code,
            "client_id": self.google_client_id,
            "client_secret": self.google_client_secret,
            "redirect_uri": self.google_redirect_uri,
            "grant_type": "authorization_code"
        }
        token_response = requests.post(token_url, data=token_payload)
        token_data = token_response.json()

        if "error" in token_data:
            raise ValueError(f"Error al obtener token de Google: {token_data['error']}")

        access_token = token_data["access_token"]
        userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        userinfo_response = requests.get(userinfo_url, headers=headers)
        userinfo = userinfo_response.json()

        return OAuthUserInfo(
            provider="google",
            provider_user_id=userinfo["sub"],
            email=userinfo["email"],
            name=userinfo.get("name"),
            picture=userinfo.get("picture")
        )

    async def _get_microsoft_user_info(self, code: str) -> OAuthUserInfo:
        """Obtiene información del usuario de Microsoft"""
        token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        token_payload = {
            "code": code,
            "client_id": self.microsoft_client_id,
            "client_secret": self.microsoft_client_secret,
            "redirect_uri": self.microsoft_redirect_uri,
            "grant_type": "authorization_code"
        }
        token_response = requests.post(token_url, data=token_payload)
        token_data = token_response.json()

        if "error" in token_data:
            raise ValueError(f"Error al obtener token de Microsoft: {token_data['error']}")

        access_token = token_data["access_token"]
        userinfo_url = "https://graph.microsoft.com/v1.0/me"
        headers = {"Authorization": f"Bearer {access_token}"}
        userinfo_response = requests.get(userinfo_url, headers=headers)
        userinfo = userinfo_response.json()

        return OAuthUserInfo(
            provider="microsoft",
            provider_user_id=userinfo["id"],
            email=userinfo["userPrincipalName"],
            name=userinfo.get("displayName"),
            picture=None
        )

