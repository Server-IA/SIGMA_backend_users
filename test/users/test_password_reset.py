import pytest
import re
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.users.models import User, PasswordReset
from app.users.services import UserService
from app.database import SessionLocal
from fastapi.exceptions import HTTPException



@pytest.fixture(scope="module")
def db():

    """Fixture para crear una nueva sesión de base de datos para las pruebas"""

    db = SessionLocal()
    db.begin()
    yield db
    db.rollback()
    db.close()


@pytest.fixture()
def user_service(db):
    """Crear una instancia del servicio para pruebas"""
    return UserService(db)


def cleanup_user(db, email):
    """Eliminar usuario si ya existe para evitar errores de clave única"""
    db.query(User).filter(User.email == email).delete()
    db.query(PasswordReset).filter(PasswordReset.email == email).delete()
    db.commit()


def test_generate_reset_token(user_service, db):
    """✅ Prueba para la generación del token de restablecimiento de contraseña"""
    email = "test@example.com"

    # Limpiar usuario antes de crearlo
    cleanup_user(db, email)

    user = User(email=email, password="hashedpassword", password_salt="somesalt")
    db.add(user)
    db.commit()

    token = user_service.generate_reset_token(email)

    stored_token = db.query(PasswordReset).filter(PasswordReset.email == email).first()
    assert stored_token is not None
    assert stored_token.token == token

    # Generar otro token para verificar que el anterior se elimina
    new_token = user_service.generate_reset_token(email)
    stored_token = db.query(PasswordReset).filter(PasswordReset.email == email).first()
    assert stored_token.token == new_token
    assert stored_token.token != token


def test_update_password_success(user_service, db):
    """✅ Prueba para actualizar la contraseña con un token válido"""

    email = "test@example.com"
    cleanup_user(db, email)

    user = User(email=email, password="hashedpassword", password_salt="somesalt")
    db.add(user)
    db.commit()

    token = user_service.generate_reset_token(email)
    new_password = "NewSecurePass123"

    assert len(new_password) >= 12
    assert re.search(r'[0-9]', new_password)
    assert re.search(r'[A-Z]', new_password)
    assert re.search(r'[a-z]', new_password)
    assert re.match(r'^[a-zA-Z0-9]+$', new_password)

    response = user_service.update_password(token, new_password)
    assert response["message"] == "Contraseña actualizada correctamente"

    db.refresh(user)
    assert user_service.verify_password(user.password_salt, user.password, new_password)


def test_update_password_invalid_token(user_service, db):
    """❌ Prueba para intentar cambiar contraseña con un token inválido"""
    with pytest.raises(HTTPException) as exc_info:
        user_service.update_password("invalid_token", "NewPassword123")

    assert exc_info.value.status_code == 404
    assert "Token inválido o expirado" in str(exc_info.value)


def test_update_password_expired_token(user_service, db):
    """❌ Prueba para intentar cambiar la contraseña con un token expirado"""

    email = "expired@example.com"
    cleanup_user(db, email)

    user = User(email=email, password="oldpassword", password_salt="oldsalt")
    db.add(user)
    db.commit()

    expired_token = PasswordReset(
        email=email,
        token="expired_token",
        expiration=datetime.now(timezone.utc) - timedelta(hours=1)  # Corregido el uso de datetime
    )
    db.add(expired_token)
    db.commit()

    with pytest.raises(HTTPException) as exc_info:
        user_service.update_password("expired_token", "NewPassword123")

    assert exc_info.value.status_code == 400
    assert "El token ha expirado" in str(exc_info.value)
