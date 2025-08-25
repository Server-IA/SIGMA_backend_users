from app.database import SessionLocal
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.fixture(scope="function")
def setup_db():
    """Fixture para configurar la base de datos y hacer rollback después de cada prueba"""
    db = SessionLocal()
    db.begin()
    yield db
    db.rollback()
    db.close()

def test_update_user_success(setup_db):
    # Datos de usuario a actualizar
    user_data = {
        "user_id": 3,
        "new_address": "New Address",
        "new_profile_picture": "new_image.jpg",
        "new_phone": "123456789"
    }
    
    response = client.post("/users/update", json=user_data)
    
    # Verificar que la actualización fue exitosa
    assert response.status_code == 200
    assert response.json()["data"] == "Usuario actualizado correctamente"

def test_update_user_not_found(setup_db):
    # Intentar actualizar un usuario que no existe
    user_data = {
        "user_id": 9999,  # ID de usuario no existente
        "new_address": "New Address"
    }
    
    response = client.post("/users/update", json=user_data)
    
    # Verificar que se recibe un error por usuario no encontrado
    assert response.status_code == 404
    assert "Usuario no encontrado" in response.json()["detail"]["data"]


