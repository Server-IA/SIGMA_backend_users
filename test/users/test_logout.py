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

def test_logout_success(setup_db):
    # Simular un login exitoso y obtener un token
    response = client.post("/users/login", json={"email": "juan.perez@example.com", "password": "Newpassword123."})
    token = response.json()["access_token"]
    
    # Hacer la solicitud de cierre de sesión
    response = client.post(
        "/users/logout",
        headers={"Authorization": f"Bearer {token}"}  # Pasamos el token en el encabezado
    )
    
    # Verificar que el cierre de sesión sea exitoso
    assert response.status_code == 200
    assert "Cierre de sesión exitoso" in response.json()["message"]

def test_logout_invalid_token(setup_db):
    # Intentar cerrar sesión con un token inválido
    invalid_token = "invalidtoken123"
    
    response = client.post(
        "/users/logout",
        headers={"Authorization": f"Bearer {invalid_token}"}  # Pasamos el token en el encabezado
    )
    
    # Verificar que se reciba un error por token inválido
    assert response.status_code == 400
    assert "Token inválido" in response.json()["detail"]
