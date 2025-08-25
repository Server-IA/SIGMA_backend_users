from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.users import services  # Importa las funciones necesarias
from app.users.models import User
from datetime import datetime, timedelta
from jose import JWTError, jwt
import os
from typing import Optional, Dict

class AuthService:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
        self.secret_key = os.getenv("SECRET_KEY", "defaultsecretkey")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifica si la contraseña en texto plano coincide con la hasheada"""
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Genera el hash de una contraseña"""
        return self.pwd_context.hash(password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Crea un token JWT con fecha de expiración"""
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=self.access_token_expire_minutes))
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def get_user(self, db: Session, username: str) -> Optional[Dict]:
        """Obtiene un usuario de la base de datos y lo convierte en un diccionario JSON"""
        user = services.get_user_by_username(db, username)
        if user:
            return {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "first_last_name": user.first_last_name,
                "second_last_name": user.second_last_name
            }
        return None
