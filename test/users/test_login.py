import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal

client = TestClient(app)

@pytest.fixture(scope="function")
def setup_db():
    """Fixture para configurar la base de datos y hacer rollback después de cada prueba"""
    db = SessionLocal()
    db.begin()
    yield db
    db.rollback()
    db.close()

def test_login_success(setup_db):
    # Proporcionar credenciales correctas de usuario
    response = client.post("/users/login", json={"email": "juan.perez@example.com", "password": "Newpassword123."})
    
    # Verificar que la respuesta sea exitosa
    assert response.status_code == 200
    assert "access_token" in response.json()  # Verificar que el token esté presente

def test_login_failure(setup_db):
    # Proporcionar credenciales incorrectas
    response = client.post("/users/login", json={"email": "juan.perez@example.com", "password": "Secure123."})
    
    # Verificar que se reciba un error 401 de credenciales inválidas
    assert response.status_code == 401
    assert "Credenciales inválidas" in response.json()["detail"]
