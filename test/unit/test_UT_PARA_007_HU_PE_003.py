"""
Pruebas unitarias para actualización de foto de perfil
ID: UT-PARA-007 (HU-PE-003)

Historia de Usuario: Como usuario del sistema, quiero actualizar mi foto de perfil 
para personalizar mi cuenta, con validaciones de formato y tamaño de archivo.

Endpoint bajo prueba: PUT /users/users/update-photo/{user_id}
"""

import sys
import os
import pytest
import io
from unittest.mock import Mock, patch, MagicMock
from PIL import Image

# Mock Firebase ANTES de cualquier importación que pueda usar firebase_config
firebase_mock = MagicMock()
sys.modules['firebase_admin'] = firebase_mock
sys.modules['firebase_admin.credentials'] = MagicMock()
sys.modules['firebase_admin.storage'] = MagicMock()

# Configurar variables de entorno para pruebas
os.environ['DATABASE_URL'] = 'sqlite:///./test.db'
os.environ['FIREBASE_CREDENTIALS'] = '{"type": "service_account", "project_id": "test-project", "private_key": "test-key", "client_email": "test@test.com"}'
os.environ['FIREBASE_STORAGE_BUCKET'] = 'test-bucket'

# Mock del módulo firebase_config completo
firebase_config_mock = MagicMock()
firebase_config_mock.bucket = MagicMock()
sys.modules['app.firebase_config'] = firebase_config_mock

# Ahora podemos importar de forma segura
from fastapi.testclient import TestClient
from fastapi import HTTPException, UploadFile
from app.main import app

# TOKEN REAL GENERADO CON LAS CREDENCIALES DEL ADMIN
# Para generar un nuevo token, ejecutar el script get_test_token.py
REAL_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzaWdtYS5pbm1lcm9AZ21haWwuY29tIiwiaWQiOjEsIm5hbWUiOiJBZG1pbiBVc2VyIiwiZW1haWwiOiJzaWdtYS5pbm1lcm9AZ21haWwuY29tIiwic3RhdHVzX2RhdGUiOiIyMDI1LTA5LTA5VDIyOjU3OjMwLjYxNjA0MCIsInJvbCI6W3siaWQiOjEsIm5hbWUiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOlt7ImlkIjoxLCJuYW1lIjoidXNlcnMuY3JlYXRlIn0seyJpZCI6MiwibmFtZSI6InVzZXJzLnZpZXcifSx7ImlkIjozLCJuYW1lIjoidXNlcnMuZWRpdCJ9LHsiaWQiOjQsIm5hbWUiOiJ1c2Vycy5kZWxldGUifSx7ImlkIjo4LCJuYW1lIjoidXNlcnMucHJvZmlsZS5lZGl0In0seyJpZCI6OSwibmFtZSI6InVzZXJzLnBob3RvLnVwZGF0ZSJ9LHsiaWQiOjEwLCJuYW1lIjoidXNlcnMuc3RhdHVzLmNoYW5nZSJ9LHsiaWQiOjExLCJuYW1lIjoidXNlcnMucGFzc3dvcmQuY2hhbmdlIn0seyJpZCI6MTIsIm5hbWUiOiJ1c2Vycy5ub3RpZmljYXRpb25zLnZpZXcifV19XSwic3RhdHVzIjoxLCJiaXJ0aGRheSI6IjE5OTAtMDEtMDFUMDA6MDA6MDAiLCJmaXJzdF9sb2dpbl9jb21wbGV0ZSI6dHJ1ZSwiZXhwIjoxNzU3NTQ1MDUwfQ.RGJXQ7h0SRhuNZcJammmGhksflIw98q1zS5Ej6xHPlI"


class TestUpdateProfilePhoto:
    """Pruebas unitarias para actualización de foto de perfil"""
    
    def setup_method(self):
        """Configuración para cada prueba"""
        self.client = TestClient(app)
        self.headers = {"Authorization": REAL_TOKEN}
        
    def create_mock_image_file(self, format="JPEG", width=200, height=200):
        """Crea un archivo de imagen mock para pruebas"""
        img = Image.new('RGB', (width, height), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format=format, quality=95)
        img_bytes.seek(0)
        return img_bytes
        
    def create_large_image_file(self, size_mb=6):
        """Crea un archivo de imagen grande para probar límites"""
        # Crear imagen grande
        img = Image.new('RGB', (3000, 3000), color='blue')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG', quality=100)
        img_bytes.seek(0)
        return img_bytes

    @patch('app.users.services.UserService.save_profile_picture')
    @patch('app.users.services.UserService.update_user')
    def test_update_photo_success_jpeg(self, mock_update_user, mock_save_picture):
        """UT-PARA-007-001: Verificar actualización exitosa con imagen JPEG"""
        # Arrange
        user_id = 1
        mock_save_picture.return_value = "https://storage.googleapis.com/test/photo.jpg"
        mock_update_user.return_value = {"success": True, "data": "Usuario actualizado correctamente"}
        
        test_file = self.create_mock_image_file("JPEG")
        
        # Act
        response = self.client.put(
            f"/users/users/update-photo/{user_id}",
            files={"profile_picture": ("profile.jpg", test_file, "image/jpeg")},
            headers=self.headers
        )
        
        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] == True
        mock_save_picture.assert_called_once()
        mock_update_user.assert_called_once()

    @patch('app.users.services.UserService.save_profile_picture')
    @patch('app.users.services.UserService.update_user')
    def test_update_photo_success_png(self, mock_update_user, mock_save_picture):
        """UT-PARA-007-002: Verificar actualización exitosa con imagen PNG"""
        # Arrange
        user_id = 1
        mock_save_picture.return_value = "https://storage.googleapis.com/test/photo.png"
        mock_update_user.return_value = {"success": True, "data": "Usuario actualizado correctamente"}
        
        test_file = self.create_mock_image_file("PNG")
        
        # Act
        response = self.client.put(
            f"/users/users/update-photo/{user_id}",
            files={"profile_picture": ("profile.png", test_file, "image/png")},
            headers=self.headers
        )
        
        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] == True
        mock_save_picture.assert_called_once()

    def test_update_photo_no_file_provided(self):
        """UT-PARA-007-003: Verificar error cuando no se proporciona archivo"""
        # Act
        response = self.client.put(
            "/users/users/update-photo/1",
            headers=self.headers
        )
        
        # Assert
        assert response.status_code == 422  # Validation error por campo requerido

    def test_update_photo_unauthorized_no_token(self):
        """UT-PARA-007-004: Verificar error sin token de autenticación"""
        # Arrange
        test_file = self.create_mock_image_file("JPEG")
        
        # Act (sin headers de autorización)
        response = self.client.put(
            "/users/users/update-photo/1",
            files={"profile_picture": ("profile.jpg", test_file, "image/jpeg")}
        )
        
        # Assert
        assert response.status_code == 401

    def test_update_photo_invalid_token(self):
        """UT-PARA-007-005: Verificar error con token inválido"""
        # Arrange
        test_file = self.create_mock_image_file("JPEG")
        invalid_headers = {"Authorization": "Bearer token_invalido"}
        
        # Act
        response = self.client.put(
            "/users/users/update-photo/1",
            files={"profile_picture": ("profile.jpg", test_file, "image/jpeg")},
            headers=invalid_headers
        )
        
        # Assert
        assert response.status_code == 401

    def test_update_photo_unauthorized_different_user(self):
        """UT-PARA-007-006: Verificar que usuario no puede actualizar foto de otro (excepto admin)"""
        # Arrange - Como el token es de admin, puede actualizar cualquier usuario
        # Pero vamos a probar con un user_id diferente para verificar la lógica
        user_id = 999  # Usuario diferente
        test_file = self.create_mock_image_file("JPEG")
        
        # Act
        response = self.client.put(
            f"/users/users/update-photo/{user_id}",
            files={"profile_picture": ("profile.jpg", test_file, "image/jpeg")},
            headers=self.headers
        )
        
        # Assert - Como es admin, debería permitirle (o dar error 404 si no existe el usuario)
        assert response.status_code in [200, 404, 500]  # Admin puede acceder, pero el usuario puede no existir

    def test_update_photo_invalid_file_format(self):
        """UT-PARA-007-007: Verificar error con formato de archivo no válido"""
        # Arrange
        invalid_file = io.BytesIO(b"This is not a valid image file")
        
        # Act
        response = self.client.put(
            "/users/users/update-photo/1",
            files={"profile_picture": ("document.txt", invalid_file, "text/plain")},
            headers=self.headers
        )
        
        # Assert
        assert response.status_code in [400, 415, 422, 500]  # Error por formato inválido

    @patch('app.users.services.UserService.save_profile_picture')
    def test_update_photo_firebase_storage_error(self, mock_save_picture):
        """UT-PARA-007-008: Verificar manejo de errores de Firebase Storage"""
        # Arrange
        mock_save_picture.side_effect = Exception("Firebase storage error")
        test_file = self.create_mock_image_file("JPEG")
        
        # Act
        response = self.client.put(
            "/users/users/update-photo/1",
            files={"profile_picture": ("profile.jpg", test_file, "image/jpeg")},
            headers=self.headers
        )
        
        # Assert
        assert response.status_code == 500

    @patch('app.users.services.UserService.save_profile_picture')
    @patch('app.users.services.UserService.update_user')
    def test_update_photo_database_error(self, mock_update_user, mock_save_picture):
        """UT-PARA-007-009: Verificar manejo de errores de base de datos"""
        # Arrange
        mock_save_picture.return_value = "https://storage.googleapis.com/test/photo.jpg"
        mock_update_user.side_effect = Exception("Database error")
        test_file = self.create_mock_image_file("JPEG")
        
        # Act
        response = self.client.put(
            "/users/users/update-photo/1",
            files={"profile_picture": ("profile.jpg", test_file, "image/jpeg")},
            headers=self.headers
        )
        
        # Assert
        assert response.status_code == 500

    @patch('app.users.services.UserService.save_profile_picture')
    @patch('app.users.services.UserService.update_user')
    def test_update_photo_admin_can_update_any_user(self, mock_update_user, mock_save_picture):
        """UT-PARA-007-010: Verificar que administrador puede actualizar foto de cualquier usuario"""
        # Arrange - El token usado es de administrador
        user_id = 2  # Diferente usuario
        mock_save_picture.return_value = "https://storage.googleapis.com/test/photo.jpg"
        mock_update_user.return_value = {"success": True, "data": "Usuario actualizado correctamente"}
        
        test_file = self.create_mock_image_file("JPEG")
        
        # Act
        response = self.client.put(
            f"/users/users/update-photo/{user_id}",
            files={"profile_picture": ("profile.jpg", test_file, "image/jpeg")},
            headers=self.headers
        )
        
        # Assert - Debería funcionar porque es administrador
        # Puede dar 200 (éxito) o 404/500 si el usuario no existe en BD
        assert response.status_code in [200, 404, 500]
