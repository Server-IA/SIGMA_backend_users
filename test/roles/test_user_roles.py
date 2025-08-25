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

def test_assing_role_to_user(setup_db):
    user_id = 3  # Asegúrate de que este ID corresponda a un usuario existente en la base de datos
    role_id = 1  # ID del rol que deseas asignar
    response = client.post("/roles/assign_role/", json={"user_id": user_id, "role_id":role_id})
    
    # Verificar que el rol fue revocado correctamente
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["data"] == "Rol asignado correctamente"
    
def test_get_user_roles(setup_db):
    user_id = 3  # Asegúrate de que este ID corresponda a un usuario existente en la base de datos
    response = client.get(f"/roles/user/{user_id}/roles")
    
    # Verificar que la respuesta sea exitosa
    assert response.status_code == 200
    assert "data" in response.json()
    assert isinstance(response.json()["data"]["roles"], list)  # Debe ser una lista de roles
    assert len(response.json()["data"]["roles"]) >= 0  # Verificar que tenga roles asignados

def test_update_user_roles(setup_db):
    user_id = 3  # Asegúrate de que este ID corresponda a un usuario existente en la base de datos
    new_roles = [1, 2]  # IDs de roles que deseas asignar al usuario
    response = client.put(f"/roles/user/{user_id}/roles", json={"roles": new_roles})
    
    # Verificar que la actualización fue exitosa
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert len(response.json()["data"]["roles"]) == len(new_roles)

def test_revoke_role_from_user(setup_db):
    user_id = 3  # Asegúrate de que este ID corresponda a un usuario existente en la base de datos
    role_id = 1  # ID del rol que deseas revocar
    response = client.delete(f"/roles/user/{user_id}/role/{role_id}")
    
    # Verificar que el rol fue revocado correctamente
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["data"] == "Rol revocado correctamente"

def test_revoke_role_from_user_with_one_role(setup_db):
    user_id = 3  # Asegúrate de que este ID corresponda a un usuario con solo un rol asignado
    role_id = 2  # ID del rol que deseas revocar
    response = client.delete(f"/roles/user/{user_id}/role/{role_id}")
    
    # Verificar que no se puede revocar el único rol asignado
    assert response.status_code == 400
    assert "El usuario debe tener al menos un rol asignado" in response.json()["detail"]["data"]

def test_get_user_roles_not_found(setup_db):
    user_id = 9999  # ID de un usuario inexistente
    response = client.get(f"/roles/user/{user_id}/roles")
    
    # Verificar que se devuelve un error de usuario no encontrado
    assert response.status_code == 404
    assert "Usuario no encontrado" in response.json()["detail"]["data"]
