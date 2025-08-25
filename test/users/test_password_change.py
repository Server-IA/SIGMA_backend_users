import pytest
import re
from sqlalchemy.orm import Session
from app.users.models import User
from app.users.services import UserService
from app.users.schemas import ChangePasswordRequest
from app.database import SessionLocal
from fastapi.exceptions import HTTPException
from pydantic import ValidationError


@pytest.fixture(scope="module")
def db():
    """Fixture para manejar una sesión de base de datos en pruebas"""
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
    db.commit()


def create_test_user(db, email="test@example.com", password="CorrectPassword123"):
    """Crea un usuario de prueba con contraseña hasheada correctamente"""
    cleanup_user(db, email)

    user_service = UserService(db)
    salt, hashed_password = user_service.hash_password(password)
    
    user = User(email=email, password=hashed_password, password_salt=salt)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_change_password_success(user_service, db):
    """✅ Cambio de contraseña exitoso"""
    email = "test@example.com"
    user = create_test_user(db, email)

    request = ChangePasswordRequest(
        old_password="CorrectPassword123",
        new_password="NewSecurePass123",
        confirm_password="NewSecurePass123"
    )

    response = user_service.change_user_password(user.id, request)
    assert response["success"] is True
    assert response["data"] == "Contraseña actualizada correctamente"


def test_change_password_wrong_old_password(user_service, db):
    """❌ Error si la contraseña actual es incorrecta"""
    email = "test@example.com"
    user = create_test_user(db, email)

    request = ChangePasswordRequest(
        old_password="WrongPassword123",
        new_password="NewSecurePass123",
        confirm_password="NewSecurePass123"
    )

    with pytest.raises(HTTPException) as exc_info:
        user_service.change_user_password(user.id, request)

    assert exc_info.value.status_code == 500
    assert "La contraseña actual es incorrecta" in str(exc_info.value)


@pytest.mark.parametrize("invalid_password,expected_error", [
    ("Short1", "String should have at least 12 characters"),
    ("NoNumberPassword", "La contraseña debe incluir al menos un número"),
    ("nouppercase123", "La contraseña debe incluir al menos una letra mayúscula"),
    ("NOLOWERCASE123", "La contraseña debe incluir al menos una letra minúscula"),
])
def test_change_password_invalid_new_password(user_service, db, invalid_password, expected_error):
    """❌ Error si la nueva contraseña no cumple con los requisitos"""
    email = "test@example.com"
    user = create_test_user(db, email)

    with pytest.raises(ValidationError) as exc_info:  # Capturar validación antes de FastAPI
        ChangePasswordRequest(
            old_password="CorrectPassword123",
            new_password=invalid_password,
            confirm_password=invalid_password
        )

    assert expected_error in str(exc_info.value)  # ✅ Ahora compara con el mensaje real de Pydantic


def test_change_password_mismatched_confirmation(user_service, db):
    """❌ Error si la confirmación de la nueva contraseña no coincide"""
    email = "test@example.com"
    user = create_test_user(db, email)

    with pytest.raises(ValidationError) as exc_info:
        ChangePasswordRequest(
            old_password="CorrectPassword123",
            new_password="NewSecurePass123",
            confirm_password="DifferentPassword123"
        )

    assert "La nueva contraseña y la confirmación no coinciden" in str(exc_info.value)
