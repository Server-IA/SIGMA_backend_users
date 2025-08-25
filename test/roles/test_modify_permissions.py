import pytest
from fastapi.testclient import TestClient
from app.main import app  # Asegúrate de que este sea el nombre correcto de tu aplicación FastAPI

client = TestClient(app)

def test_update_role_permissions():
    role_id = 1  # Asegúrate de que este ID corresponda al rol existente en la base de datos
    new_permissions = [2, 3]  # Permisos que deseas asignar
    response = client.put(f"/roles/{role_id}/permissions", json={"permissions": new_permissions})
    assert response.status_code == 200
    assert "message" in response.json()
    assert "Permisos actualizados correctamente" in response.json()["message"]
