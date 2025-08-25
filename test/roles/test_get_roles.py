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

def test_get_roles(setup_db):
    response = client.get("/roles/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)  # La respuesta debe ser una lista de roles
    assert len(response.json()) > 0  # Verificar que haya al menos un rol

def test_get_permissions(setup_db):
    response = client.get("/roles/permissions/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)  # La respuesta debe ser una lista de permisos
    assert len(response.json()) > 0  # Verificar que haya al menos un permiso
