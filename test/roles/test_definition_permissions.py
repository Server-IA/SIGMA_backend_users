import pytest
from fastapi.testclient import TestClient
from app.main import app  # Asegúrate de que este sea el nombre correcto de tu aplicación FastAPI

client = TestClient(app)

def test_create_permission():
    response = client.post("/roles/permissions/", json={
        "name": "edit_user", 
        "description": "Edit User Permissions", 
        "category": "User Management"
    })
    
    # Verificar que la respuesta sea exitosa
    assert response.status_code == 200
    data = response.json()
    
    # Verifica que la respuesta contiene el mensaje de éxito y la estructura correcta
    assert "success" in data
    assert data["success"] == True
    assert "data" in data
    assert data["data"] == "El permiso se ha creado correctamente"
    
    
def test_get_permissions():
    # Hacer una solicitud GET para obtener todos los permisos
    response = client.get("/roles/permissions/")
    
    # Verificar que la respuesta sea exitosa
    assert response.status_code == 200
    assert isinstance(response.json(), list)  # La respuesta debe ser una lista
    assert len(response.json()) > 0  # Verificar que haya al menos un permiso

