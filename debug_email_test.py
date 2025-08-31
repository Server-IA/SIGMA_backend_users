#!/usr/bin/env python3
"""
Script de prueba para verificar el sistema de correos electrónicos con debugging
"""

import os
import sys
from dotenv import load_dotenv

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_email_debug():
    """Prueba el sistema de correos con debugging detallado"""
    
    print("=" * 60)
    print("🔍 PRUEBA DE SISTEMA DE CORREOS ELECTRÓNICOS")
    print("=" * 60)
    
    # Cargar variables de entorno
    load_dotenv()
    
    # Verificar variables de entorno
    email_sender = os.getenv("EMAIL_SENDER")
    email_password = os.getenv("EMAIL_PASSWORD")
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    print(f"📧 EMAIL_SENDER: {email_sender}")
    print(f"🔑 EMAIL_PASSWORD: {'*' * len(email_password) if email_password else 'NO CONFIGURADO'}")
    print(f"🌐 FRONTEND_URL: {frontend_url}")
    print()
    
    if not email_sender or not email_password:
        print("❌ ERROR: EMAIL_SENDER y EMAIL_PASSWORD deben estar configurados")
        return False
    
    try:
        # Importar el servicio de email
        from app.email_service import EmailService
        
        print("✅ Servicio de email importado correctamente")
        
        # Crear instancia del servicio
        email_service = EmailService()
        print("✅ Instancia del servicio creada")
        
        # Datos de prueba
        test_email = "u20212201817@usco.edu.co"  # Tu email de prueba
        test_token = "test-token-12345"
        test_user_name = "Usuario de Prueba"
        
        print(f"📨 Email de prueba: {test_email}")
        print(f"🔑 Token de prueba: {test_token}")
        print(f"👤 Nombre de usuario: {test_user_name}")
        print()
        
        # Probar envío de correo de reseteo de contraseña
        print("🔄 Probando envío de correo de reseteo de contraseña...")
        result = email_service.send_password_reset_email(
            to_email=test_email,
            reset_token=test_token,
            user_name=test_user_name
        )
        
        if result:
            print("✅ Correo de reseteo enviado exitosamente")
        else:
            print("❌ FALLA en envío de correo de reseteo")
            return False
        
        print()
        
        # Probar envío de correo de activación
        print("🔄 Probando envío de correo de activación...")
        result = email_service.send_account_activation_email(
            to_email=test_email,
            activation_token=test_token,
            user_name=test_user_name
        )
        
        if result:
            print("✅ Correo de activación enviado exitosamente")
        else:
            print("❌ FALLA en envío de correo de activación")
            return False
        
        print()
        
        # Probar envío de correo de bienvenida
        print("🔄 Probando envío de correo de bienvenida...")
        result = email_service.send_welcome_email(
            to_email=test_email,
            user_name=test_user_name
        )
        
        if result:
            print("✅ Correo de bienvenida enviado exitosamente")
        else:
            print("❌ FALLA en envío de correo de bienvenida")
            return False
        
        print()
        print("🎉 ¡TODAS LAS PRUEBAS EXITOSAS!")
        print("📧 Verifica tu bandeja de entrada para confirmar la recepción")
        
        return True
        
    except ImportError as e:
        print(f"❌ Error al importar módulos: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_email_debug()
    if success:
        print("\n✅ Sistema de correos funcionando correctamente")
        sys.exit(0)
    else:
        print("\n❌ Problemas detectados en el sistema de correos")
        sys.exit(1)
