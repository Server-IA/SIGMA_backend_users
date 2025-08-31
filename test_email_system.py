#!/usr/bin/env python3
"""
Script de prueba para verificar el sistema de correos electrónicos
"""

import os
import sys
from dotenv import load_dotenv

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.email_service import EmailService

def test_email_system():
    """Prueba el sistema de correos electrónicos"""
    
    # Cargar variables de entorno
    load_dotenv()
    
    # Verificar que las variables de entorno estén configuradas
    email_sender = os.getenv("EMAIL_SENDER")
    email_password = os.getenv("EMAIL_PASSWORD")
    
    if not email_sender or not email_password:
        print("❌ Error: EMAIL_SENDER y EMAIL_PASSWORD deben estar configurados en el archivo .env")
        print("\nEjemplo de configuración:")
        print("EMAIL_SENDER=tu_email@gmail.com")
        print("EMAIL_PASSWORD=tu_app_password")
        return False
    
    try:
        # Crear instancia del servicio de email
        email_service = EmailService()
        print("✅ Servicio de email inicializado correctamente")
        
        # Email de prueba
        test_email = input("Ingresa un email de prueba para enviar el correo: ")
        if not test_email:
            print("❌ No se proporcionó un email de prueba")
            return False
        
        print(f"\n📧 Enviando correo de prueba a: {test_email}")
        
        # Probar envío de correo de reseteo de contraseña
        print("\n1. Probando correo de reseteo de contraseña...")
        reset_success = email_service.send_password_reset_email(
            to_email=test_email,
            reset_token="test_token_123",
            user_name="Usuario de Prueba"
        )
        
        if reset_success:
            print("✅ Correo de reseteo enviado exitosamente")
        else:
            print("❌ Error al enviar correo de reseteo")
            return False
        
        # Probar envío de correo de activación de cuenta
        print("\n2. Probando correo de activación de cuenta...")
        activation_success = email_service.send_account_activation_email(
            to_email=test_email,
            activation_token="test_activation_token_123",
            user_name="Usuario de Prueba"
        )
        
        if activation_success:
            print("✅ Correo de activación enviado exitosamente")
        else:
            print("❌ Error al enviar correo de activación")
            return False
        
        # Probar envío de correo de bienvenida
        print("\n3. Probando correo de bienvenida...")
        welcome_success = email_service.send_welcome_email(
            to_email=test_email,
            user_name="Usuario de Prueba"
        )
        
        if welcome_success:
            print("✅ Correo de bienvenida enviado exitosamente")
        else:
            print("❌ Error al enviar correo de bienvenida")
            return False
        
        print("\n🎉 ¡Todos los correos fueron enviados exitosamente!")
        print("Revisa tu bandeja de entrada para verificar los correos.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la prueba: {str(e)}")
        return False

def main():
    """Función principal"""
    print("🧪 Prueba del Sistema de Correos Electrónicos")
    print("=" * 50)
    
    success = test_email_system()
    
    if success:
        print("\n✅ Sistema de correos funcionando correctamente")
        sys.exit(0)
    else:
        print("\n❌ Sistema de correos con problemas")
        sys.exit(1)

if __name__ == "__main__":
    main()
