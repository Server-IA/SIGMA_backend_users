
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.database import Base

class RevokedToken(Base):
    """Modelo para almacenar tokens revocados (para cierre de sesión)"""
    __tablename__ = "revoked_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    def has_expired(self):
        """Método para verificar si el token ha expirado"""
        return datetime.utcnow() > self.expires_at

