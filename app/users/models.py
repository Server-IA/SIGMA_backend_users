from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
from pydantic import BaseModel
from app.roles.models import Role, user_role_table

class ChangeUserStatusRequest(BaseModel):
    """Modelo para cambiar el estado de un usuario"""
    user_id: int
    new_status: int

class User(Base):
    """Modelo de Usuario"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    password = Column(String, nullable=True)
    password_salt = Column(String, nullable=True)
    name = Column(String)
    email_status = Column(Boolean, nullable=True)
    document_number = Column(Integer, nullable=True)
    date_issuance_document = Column(DateTime, nullable=True)
    type_person_id = Column(Integer, nullable=True)
    birthday = Column(DateTime, nullable=True)
    gender_id = Column(Integer, ForeignKey('gender.id'), nullable=True)
    first_last_name = Column(String, nullable=True)
    second_last_name = Column(String, nullable=True)
    address = Column(String, nullable=True)
    profile_picture = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    country = Column(String, nullable=True)
    department = Column(String, nullable=True)
    city = Column(Integer, nullable=True)
    first_login_complete = Column(Boolean, default=False)
    type_document_id = Column(Integer, ForeignKey('type_document.id'), nullable=True)
    status_id = Column(Integer, ForeignKey('status_user.id'), nullable=True)

    last_pre_register_attempt = Column(DateTime, nullable=True)
    pre_register_attempts = Column(Integer, default=0)


    roles = relationship("Role", secondary=user_role_table, back_populates="users")
    type_document = relationship("TypeDocument", back_populates="users")
    status_user = relationship("Status", back_populates="users")
    gender = relationship("Gender", back_populates="users")
    pre_register_tokens = relationship("PreRegisterToken", back_populates="user")
    activation_tokens = relationship("ActivationToken", back_populates="user")
    social_accounts = relationship("SocialAccount", back_populates="user", cascade="all, delete-orphan")
    __table_args__ = {'extend_existing': True}
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")

class RevokedToken(Base):
    """Modelo para almacenar tokens revocados (para cierre de sesión)"""
    __tablename__ = "revoked_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    def has_expired(self):
        return datetime.utcnow() > self.expires_at

class TypeDocument(Base):
    """Modelo para el Tipo de Documento"""
    __tablename__ = "type_document"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    users = relationship("User", back_populates="type_document")
    __table_args__ = {'extend_existing': True}

class Gender(Base):
    """Modelo para género"""
    __tablename__ = "gender"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    users = relationship("User", back_populates="gender")
    __table_args__ = {'extend_existing': True}
    
    def __repr__(self):
        return f"<Gender(id={self.id}, name={self.name})>"

def ensure_default_genders(db):
    default_genders = [
        {"id": 1, "name": "Hombre"},
        {"id": 2, "name": "Mujer"},
        {"id": 3, "name": "Otro"}
    ]
    for gender_data in default_genders:
        gender = db.query(Gender).filter(Gender.id == gender_data["id"]).first()
        if not gender:
            gender = Gender(**gender_data)
            db.add(gender)
    db.commit()

class Status(Base):
    """Modelo para los estados del usuario"""
    __tablename__ = "status_user"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    users = relationship("User", back_populates="status_user")
    __table_args__ = {'extend_existing': True}

class PasswordReset(Base):
    __tablename__ = "password_resets"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    token = Column(String, unique=True, index=True)
    expiration = Column(DateTime, default=datetime.utcnow)

class PreRegisterToken(Base):
    """Modelo para almacenar tokens de validación para el pre-registro."""
    __tablename__ = "pre_register_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    user = relationship("User", back_populates="pre_register_tokens")

class ActivationToken(Base):
    """Modelo para almacenar tokens de activación enviados por email."""
    __tablename__ = "activation_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    user = relationship("User", back_populates="activation_tokens")

class SocialAccount(Base):
    """Modelo para almacenar cuentas sociales vinculadas a usuarios"""
    __tablename__ = "social_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider = Column(String, nullable=False)
    provider_user_id = Column(String, nullable=False)
    email = Column(String, nullable=False)
    access_token = Column(String, nullable=True)
    refresh_token = Column(String, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = relationship("User", back_populates="social_accounts")
    __table_args__ = {'extend_existing': True}
    
    def __repr__(self):
        return f"<SocialAccount(id={self.id}, provider={self.provider}, email={self.email})>"


class Notification(Base):
    """Model for user notifications"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)  
    type = Column(String, nullable=False) 
    read = Column(Boolean, nullable=True) 
    created_at = Column(DateTime, nullable=True)  
    user = relationship("User", back_populates="notifications")