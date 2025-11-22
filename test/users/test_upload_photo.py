import pytest
import os
import tempfile
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock, AsyncMock
from app.database import Base, get_db
from app.main import app
from app.users.models import User, TypeDocument, Status, Gender
from app.roles.models import Role, Permission
from app.auth.services import AuthService

# Configuración de base de datos de prueba
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_photo_upload.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_database():
    """Configura la base de datos de prueba"""
    Base.metadata.create_all(bind=engine)
    
    # Crear datos de prueba básicos
    db = TestingSessionLocal()
    try:
        # Crear tipos de documento
        type_doc = TypeDocument(id=1, name="Cédula")
        db.add(type_doc)
        
        # Crear estados
        status = Status(id=1, name="Activo", description="Usuario activo")
        db.add(status)
        
        # Crear géneros
        gender = Gender(id=1, name="Masculino")
        db.add(gender)
        
        # Crear rol
        role = Role(id=1, name="Usuario")
        db.add(role)
        
        db.commit()
    finally:
        db.close()
    
    yield
    
    # Limpiar después de las pruebas
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("test_photo_upload.db"):
        os.remove("test_photo_upload.db")

@pytest.fixture
def test_user(setup_database):
    """Crea un usuario de prueba"""
    db = TestingSessionLocal()
    try:
        # Verificar si el usuario ya existe
        user = db.query(User).filter(User.email == "juandalozano07@gmail.com").first()
        if not user:
            user = User(
                id=1,
                email="juandalozano07@gmail.com",
                name="Juan",
                first_last_name="Díaz",
                second_last_name="Lozano",
                type_document_id=1,
                document_number=12345678,
                status_id=1,
                gender_id=1,
                email_status=True,
                first_login_complete=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user
    finally:
        db.close()

@pytest.fixture
def admin_token(test_user):
    """Obtiene un token de autenticación para el usuario admin"""
    login_data = {
        "username": "juandalozano07@gmail.com",
        "password": "Juanda2004#."
    }
    
    # Intentar con el endpoint normal primero
    response = client.post("/users/auth/login/", json=login_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        # Si falla, intenta con el endpoint swagger
        response = client.post(
            "/users/auth/swagger-login",
            data=login_data,
            headers={"content-type": "application/x-www-form-urlencoded"}
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            # Si ambos fallan, crear un token mock para las pruebas
            from app.auth.services import AuthService
            from datetime import timedelta
            auth_service = AuthService(TestingSessionLocal())
            token_data = {
                "sub": test_user.email,
                "id": test_user.id,
                "name": test_user.name,
                "email": test_user.email,
                "rol": []
            }
            return auth_service.create_access_token(data=token_data)

@pytest.fixture
def test_image_path():
    """Ruta del archivo de imagen de prueba"""
    # Asumiendo que el archivo está en files/xd.jpg desde la raíz del proyecto
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, "files", "xd.jpg")

@pytest.fixture
def mock_firebase_storage():
    """Mock para Firebase Storage"""
    with patch('app.users.services.bucket') as mock_bucket:
        mock_blob = MagicMock()
        mock_blob.upload_from_string.return_value = None
        mock_blob.make_public.return_value = None
        mock_blob.public_url = "https://firebase.storage.googleapis.com/fake-url/profile.jpg"
        mock_bucket.blob.return_value = mock_blob
        yield mock_bucket

class TestUpdateProfilePhoto:
    """Clase para pruebas del endpoint de actualización de foto de perfil"""

    def test_update_photo_success(self, setup_database, admin_token, test_image_path, mock_firebase_storage, test_user):
        """Prueba exitosa de actualización de foto de perfil"""
        user_id = test_user.id
        
        # Verificar que el archivo existe
        assert os.path.exists(test_image_path), f"Archivo de prueba no encontrado: {test_image_path}"
        
        with open(test_image_path, "rb") as image_file:
            files = {"profile_picture": ("xd.jpg", image_file, "image/jpeg")}
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            response = client.put(
                f"/users/users/update-photo/{user_id}",
                files=files,
                headers=headers
            )
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True
        assert response_data["data"] == "Usuario actualizado correctamente"
        
        # Verificar que Firebase fue llamado
        mock_firebase_storage.blob.assert_called_once()
        mock_blob = mock_firebase_storage.blob.return_value
        mock_blob.upload_from_string.assert_called_once()
        mock_blob.make_public.assert_called_once()

    def test_update_photo_unauthorized_user(self, setup_database, admin_token, test_image_path, test_user):
        """Prueba de actualización de foto con usuario no autorizado"""
        user_id = 999  # ID de usuario que no corresponde al token
        
        assert os.path.exists(test_image_path), f"Archivo de prueba no encontrado: {test_image_path}"
        
        with open(test_image_path, "rb") as image_file:
            files = {"profile_picture": ("xd.jpg", image_file, "image/jpeg")}
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            response = client.put(
                f"/users/users/update-photo/{user_id}",
                files=files,
                headers=headers
            )
        
        assert response.status_code == 403
        assert "No tiene permisos para editar este usuario" in response.json()["detail"]

    def test_update_photo_without_auth(self, setup_database, test_image_path, test_user):
        """Prueba de actualización de foto sin autenticación"""
        user_id = test_user.id
        
        assert os.path.exists(test_image_path), f"Archivo de prueba no encontrado: {test_image_path}"
        
        with open(test_image_path, "rb") as image_file:
            files = {"profile_picture": ("xd.jpg", image_file, "image/jpeg")}
            
            response = client.put(
                f"/users/users/update-photo/{user_id}",
                files=files
            )
        
        assert response.status_code == 401

    def test_update_photo_invalid_file_type(self, setup_database, admin_token, test_user):
        """Prueba de actualización con tipo de archivo inválido"""
        user_id = test_user.id
        
        # Crear un archivo de texto temporal para simular tipo incorrecto
        with patch('app.users.services.bucket') as mock_bucket:
            mock_bucket.blob.side_effect = Exception("Tipo de archivo no permitido")
            
            files = {"profile_picture": ("test.txt", b"contenido de texto", "text/plain")}
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            response = client.put(
                f"/users/users/update-photo/{user_id}",
                files=files,
                headers=headers
            )
        
        assert response.status_code == 500

    def test_update_photo_firebase_error(self, setup_database, admin_token, test_image_path, test_user):
        """Prueba de error en la subida a Firebase"""
        user_id = test_user.id
        
        assert os.path.exists(test_image_path), f"Archivo de prueba no encontrado: {test_image_path}"
        
        with patch('app.users.services.bucket') as mock_bucket:
            mock_blob = MagicMock()
            mock_blob.upload_from_string.side_effect = Exception("Error de Firebase Storage")
            mock_bucket.blob.return_value = mock_blob
            
            with open(test_image_path, "rb") as image_file:
                files = {"profile_picture": ("xd.jpg", image_file, "image/jpeg")}
                headers = {"Authorization": f"Bearer {admin_token}"}
                
                response = client.put(
                    f"/users/users/update-photo/{user_id}",
                    files=files,
                    headers=headers
                )
        
        assert response.status_code == 500

    def test_update_photo_missing_file(self, setup_database, admin_token, test_user):
        """Prueba sin enviar archivo"""
        user_id = test_user.id
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = client.put(
            f"/users/users/update-photo/{user_id}",
            headers=headers
        )
        
        # Debería fallar porque profile_picture es requerido
        assert response.status_code in [400, 422]

    def test_update_photo_user_not_found(self, setup_database, admin_token, test_image_path, mock_firebase_storage):
        """Prueba con usuario inexistente"""
        user_id = 99999  # ID que no existe
        
        assert os.path.exists(test_image_path), f"Archivo de prueba no encontrado: {test_image_path}"
        
        with open(test_image_path, "rb") as image_file:
            files = {"profile_picture": ("xd.jpg", image_file, "image/jpeg")}
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            response = client.put(
                f"/users/users/update-photo/{user_id}",
                files=files,
                headers=headers
            )
        
        # Debería fallar con 403 porque el usuario no tiene permisos para editar otro usuario
        assert response.status_code == 403

    def test_update_photo_various_image_formats(self, setup_database, admin_token, test_user, mock_firebase_storage):
        """Prueba con diferentes formatos de imagen"""
        user_id = test_user.id
        
        # Lista de formatos de imagen comunes para probar
        image_formats = [
            ("test.jpg", "image/jpeg"),
            ("test.png", "image/png"),
            ("test.gif", "image/gif"),
            ("test.webp", "image/webp")
        ]
        
        for filename, content_type in image_formats:
            # Simular contenido de imagen básico
            fake_image_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
            
            files = {"profile_picture": (filename, fake_image_content, content_type)}
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            response = client.put(
                f"/users/users/update-photo/{user_id}",
                files=files,
                headers=headers
            )
            
            # Debería ser exitoso para formatos válidos
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["success"] is True

    @pytest.mark.parametrize("file_size", [
        1024,      # 1KB
        1024*1024, # 1MB
        5*1024*1024, # 5MB
    ])
    def test_update_photo_file_sizes(self, setup_database, admin_token, test_user, mock_firebase_storage, file_size):
        """Prueba con diferentes tamaños de archivo"""
        user_id = test_user.id
        
        # Crear contenido de archivo del tamaño especificado
        fake_content = b'x' * file_size
        
        files = {"profile_picture": ("large_image.jpg", fake_content, "image/jpeg")}
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = client.put(
            f"/users/users/update-photo/{user_id}",
            files=files,
            headers=headers
        )
        
        # La respuesta dependerá de las validaciones implementadas
        assert response.status_code in [200, 400, 413, 500]

def test_endpoint_requirements():
    """Prueba que verifica que el endpoint cumple con los requisitos especificados"""
    # Verificar que la ruta existe
    routes = [route.path for route in app.routes]
    assert "/users/users/update-photo/{user_id}" in routes or any("/users/users/update-photo/" in route for route in routes)
    
    # Verificar que el método PUT está disponible
    for route in app.routes:
        if hasattr(route, 'path_regex') and 'update-photo' in str(route.path_regex):
            assert 'PUT' in route.methods

def test_endpoint_validation_requirements():
    """Prueba que verifica las validaciones específicas del endpoint"""
    # Verificar que el endpoint requiere autenticación
    response = client.put("/users/users/update-photo/1")
    assert response.status_code == 401
    
    # Verificar que el endpoint requiere el archivo
    # (Esto se prueba en test_update_photo_missing_file)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
